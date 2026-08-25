/**
 * dsh-tool-adapter — experiment 2.
 *
 * Projects tools from the in-process dsh container into ellamaka's
 * ToolRegistry through the plugin.tool path. The container is exposed by
 * serve.ts (ELLAMAKA_DSH=1) on globalThis.__ellamakaDshContainer.
 *
 * The container is mounted with `session-checkpoint-policy` disabled
 * (ellamaka-tools profile patch layer): that plugin flushes the calling
 * agent's live dsh session before every tools/execute — an agent-loop
 * durability semantic. Without it, a lightweight per-call agent carrying
 * the tool's actual consumption surface is enough:
 *
 *   - session.header.cwd — resolved workdir for spawns
 *   - session.header.id  — spill ownership label
 *
 * No dsh session is ever created in the container, so the container state
 * stays free of per-ellamaka-session records.
 *
 * Mappings come from plugin options:
 *
 *   "plugin": [["./.wopal/plugins/dsh-adapter/index.ts", {
 *     "tools": [
 *       { "source": "grep", "target": "grep", "enable": true },
 *       { "source": "glob", "target": "glob", "enable": true }
 *     ]
 *   }]]
 *
 * A mapping with enable:false is skipped. `source` is the container tool
 * name; `target` is the ellamaka slot it lands on — same-name shadows the
 * builtin (custom registers after builtin; same-name assignment wins), a
 * renamed target produces a new tool id.
 */
import type { Hooks, PluginInput, PluginOptions } from "@opencode-ai/plugin"
import { z } from "zod"

type Container = {
  get(name: "tools"): {
    schemas(): { name: string; description: string; parameters: unknown }[]
    execute(exec: unknown): Promise<{
      isError: boolean
      content?: { type: string; text?: string }[]
      error?: { message?: string }
    }>
  } | undefined
  logger(name: string): {
    info(message: string, extra?: unknown): void
    warn(message: string, extra?: unknown): void
    error(message: string, extra?: unknown): void
  }
}

export type DshAdapterOptions = {
  tools?: { source: string; target: string; enable: boolean }[]
}

// A projected container tool. args are a ZodRawShape (the plugin SDK
// contract): the registry's fromPlugin path detects Zod types and generates
// the correct flat JSON Schema. Passing the dsh JSON Schema document as-is
// would make the registry treat its top-level keys (type/properties/required)
// as property definitions, producing a nested schema the model cannot call.
type ProjectedTool = {
  description: string
  args: Record<string, z.ZodType>
  execute: (args: unknown, ctx: Record<string, unknown>) => Promise<{ output: string; title: string; metadata: Record<string, unknown> }>
}

type ToolContext = {
  abort?: AbortSignal
  sessionID: string
  directory: string
  callID?: string
}

type JsonSchemaNode = {
  type?: string
  description?: string
  properties?: Record<string, JsonSchemaNode>
  required?: string[]
  items?: JsonSchemaNode
  enum?: unknown[]
}

/**
 * Convert a dsh JSON Schema document into a ZodRawShape.
 *
 * The dsh tool registry exposes each tool's parameters as a full JSON Schema
 * document (`{ type: "object", properties: {...}, required: [...] }`). The
 * plugin SDK contract is a ZodRawShape — a map of property name to Zod type —
 * so the document is unwrapped into its property definitions, each converted
 * to the matching Zod type. Unsupported nodes degrade to `z.unknown()` so a
 * future dsh schema extension can never break the projection.
 */
function jsonSchemaToZodShape(schema: unknown): Record<string, z.ZodType> {
  const node = schema as JsonSchemaNode
  const properties = node?.properties ?? {}
  const required = new Set(node?.required ?? [])
  const shape: Record<string, z.ZodType> = {}
  for (const [name, property] of Object.entries(properties)) {
    let type = jsonSchemaNodeToZod(property)
    if (!required.has(name)) type = type.optional()
    shape[name] = type
  }
  return shape
}

function jsonSchemaNodeToZod(node: JsonSchemaNode | undefined): z.ZodType {
  if (!node || typeof node !== "object") return z.unknown()
  switch (node.type) {
    case "string":
      return z.string()
    case "number":
      return z.number()
    case "integer":
      return z.number().int()
    case "boolean":
      return z.boolean()
    case "array":
      return z.array(node.items ? jsonSchemaNodeToZod(node.items) : z.unknown())
    case "object":
      return z.record(z.string(), z.unknown())
    default:
      return z.unknown()
  }
}

function contentText(content: { type: string; text?: string }[] | undefined): string {
  return (content ?? [])
    .map((block) => (block.type === "text" ? (block.text ?? "") : ""))
    .join("\n")
}

export async function dshAdapter(_input: PluginInput, rawOptions?: PluginOptions): Promise<Hooks> {
  const options = (rawOptions ?? {}) as DshAdapterOptions
  const mappings = (options.tools ?? []).filter((m) => m.enable && m.source && m.target)
  if (mappings.length === 0) return {}

  const container = (globalThis as Record<string, unknown>).__ellamakaDshContainer as Container | undefined
  if (!container) return {}
  const tools = container.get("tools")
  if (!tools) return {}
  const log = container.logger("dsh-adapter")

  const available = new Map(tools.schemas().map((s) => [s.name, s]))
  const projected: Record<string, ProjectedTool> = {}

  for (const { source, target } of mappings) {
    const schema = available.get(source)
    if (!schema) continue
    projected[target] = {
      description: schema.description,
      args: jsonSchemaToZodShape(schema.parameters),
      execute: async (args, ctx) => {
        const toolCtx = ctx as ToolContext
        // Per-call agent carrying only the surface the tools consume: header.cwd
        // (spawn workdir) and header.id (spill owner). With
        // session-checkpoint-policy disabled, the pipeline never demands a
        // live dsh session, and no container state is created.
        const agent = {
          session: {
            header: { id: toolCtx.sessionID, cwd: toolCtx.directory },
          },
        }
        const result = await tools.execute({
          callId: toolCtx.callID ?? `dsh-${source}-${Date.now()}`,
          name: source,
          arguments: args,
          signal: toolCtx.abort ?? new AbortController().signal,
          agent,
        })
        const output = contentText(result.content)
        if (result.isError) {
          const message = output || result.error?.message || `dsh tool "${source}" failed`
          log.error("tool call failed", { tool: source, sessionID: toolCtx.sessionID, callID: toolCtx.callID, error: message })
          throw new Error(message)
        }
        log.info("tool call", { tool: source, sessionID: toolCtx.sessionID, callID: toolCtx.callID })
        return {
          output,
          title: source,
          metadata: { source: "dsh-container", containerTool: source },
        }
      },
    }
  }

  const toolRecord = Object.keys(projected).length === 0 ? undefined : (projected as Hooks["tool"])
  return toolRecord ? { tool: toolRecord } : {}
}

export default { id: "dsh-adapter", server: dshAdapter }