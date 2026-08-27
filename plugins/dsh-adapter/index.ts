/**
 * dsh-tool-adapter — experiment 2 (P3.5 dynamic provider).
 *
 * Projects tools from the in-process dsh container into ellamaka's
 * ToolRegistry through the dynamic `tool.provider` plugin hook. The container
 * is exposed by serve.ts (ELLAMAKA_DSH=1) on globalThis.__ellamakaDshContainer.
 *
 * Unlike the earlier static `tool` table (snapshotted at mount time), the
 * provider re-reads the container's live `tools.schemas()` on EVERY model
 * request — so tools mounted/unmounted inside the dsh container take effect
 * on the next request without a restart.
 *
 * The container is mounted with `session-checkpoint-policy` disabled
 * (ellamaka-tools profile patch layer): that plugin flushes the calling
 * agent's live dsh session before every tools/execute — an agent-loop
 * durability semantic. Without it, a cached session facade carrying the
 * tool's actual consumption surface is enough:
 *
 *   - session.header.cwd — resolved workdir for spawns
 *   - session.header.id  — spill ownership label
 *   - session.events     — sandbox-mode policy fold
 *
 * No dsh session is created in the container, so the container state stays
 * free of per-ellamaka-session records.
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
 * builtin (dynamic providers win on id collision), a renamed target produces
 * a new tool id.
 *
 * Sandbox semantics (DESIGN §4.10): `enabled: true` (or mode set) selects the
 * sandbox backend and injects a `sandbox/mode` event (`read-only` or
 * `workspace-write`, default `workspace-write`) into each session facade.
 * `enabled: false` (or absent) DISABLES the sandbox by injecting
 * `danger-full-access` — dsh's one-shot full-access mode. It does NOT switch
 * the local fs/bash backend; tools always run through the same dsh container
 * and sandbox backend, only the effective mode is loosened.
 */
import type { Hooks, PluginInput, PluginOptions, ToolDefinition } from "@opencode-ai/plugin"
import path from "node:path"
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
  /**
   * Space-level sandbox policy for the dsh tool container
   * (`ellamaka.dsh.sandbox`). `enabled: true` selects the sandbox backend and
   * injects a `sandbox/mode` event into each session facade; `mode` is
   * `read-only` or `workspace-write` (default `workspace-write`). `enabled:
   * false` (or absent) DISABLES the sandbox by injecting
   * `danger-full-access` — the dsh one-shot full-access mode. It never
   * switches the local fs/bash backend.
   */
  sandbox?: { enabled: boolean; mode?: "read-only" | "workspace-write" }
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
  worktree: string
  callID?: string
  ask(input: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }): Promise<void>
}

type DshSession = {
  header: { id: string; cwd: string }
  events: unknown[]
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

function isInside(root: string, target: string): boolean {
  const relative = path.relative(root, target)
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative))
}

async function askToolPermission(source: string, args: unknown, ctx: ToolContext): Promise<void> {
  if (source === "bash") {
    const command = (args as { command?: unknown }).command
    if (typeof command !== "string") return
    await ctx.ask({
      permission: "bash",
      patterns: [command],
      always: [command],
      metadata: {},
    })
    return
  }

  const input = args as { file_path?: unknown; path?: unknown; command?: unknown }
  const filePath = source === "str_replace_editor" ? input.path : input.file_path
  if (typeof filePath !== "string") return
  const permission = source === "read" || (source === "str_replace_editor" && input.command === "view")
    ? "read"
    : source === "write" || source === "edit" || source === "str_replace_editor"
      ? "edit"
      : undefined
  if (!permission) return

  const filepath = path.isAbsolute(filePath) ? path.normalize(filePath) : path.resolve(ctx.directory, filePath)
  const isProjectPath = isInside(ctx.directory, filepath) || (ctx.worktree !== "/" && isInside(ctx.worktree, filepath))
  if (!isProjectPath) {
    const parentDir = path.dirname(filepath)
    const pattern = path.join(parentDir, "*").replaceAll("\\", "/")
    await ctx.ask({
      permission: "external_directory",
      patterns: [pattern],
      always: [pattern],
      metadata: { filepath, parentDir },
    })
  }

  await ctx.ask({
    permission,
    patterns: [path.relative(ctx.worktree, filepath).replaceAll("\\", "/")],
    always: ["*"],
    metadata: {},
  })
}

export async function dshAdapter(_input: PluginInput, rawOptions?: PluginOptions): Promise<Hooks> {
  const options = (rawOptions ?? {}) as DshAdapterOptions
  const mappings = (options.tools ?? []).filter((m) => m.enable && m.source && m.target)
  if (mappings.length === 0) return {}

  const container = (globalThis as Record<string, unknown>).__ellamakaDshContainer as Container | undefined
  // Container missing -> the provider silently returns no tools (degraded).
  if (!container) return { "tool.provider": async (_input, _output) => {} }
  const tools = container.get("tools")
  if (!tools) return { "tool.provider": async (_input, _output) => {} }

  const log = container.logger("dsh-adapter")
  const sessions = new Map<string, DshSession>()

  // Resolve the space-level sandbox policy once at mount. `enabled: true`
  // selects the sandbox backend and injects a `sandbox/mode` event into every
  // session facade; `enabled: false` (or absent) DISABLES the sandbox by
  // injecting `danger-full-access` — dsh's one-shot full-access mode. The
  // container's sandbox backend is never switched; only the effective mode is
  // loosened. `mode` defaults to `workspace-write` (the dsh base profile
  // default) when the sandbox is enabled.
  const sandboxEnabled = options.sandbox?.enabled === true
  const sandboxMode = sandboxEnabled ? (options.sandbox?.mode ?? "workspace-write") : "danger-full-access"
  const sandboxEvents = [{ type: "sandbox/mode", data: { mode: sandboxMode } }]

  // Project a single container tool onto its target slot. The execute closure
  // is rebuilt per provider call but reuses the shared facade cache, logger,
  // and permission-ask logic declared once at adapter scope (memory-level cost).
  function project(source: string, target: string, schema: { description: string; parameters: unknown }): ProjectedTool {
    return {
      description: schema.description,
      args: jsonSchemaToZodShape(schema.parameters),
      execute: async (args, ctx) => {
        const toolCtx = ctx as ToolContext
        await askToolPermission(source, args, toolCtx)
        let session = sessions.get(toolCtx.sessionID)
        if (!session) {
          session = {
            header: { id: toolCtx.sessionID, cwd: toolCtx.directory },
            events: sandboxEvents,
          }
          sessions.set(toolCtx.sessionID, session)
        }
        const agent = {
          session,
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

  // Dynamic provider: re-reads the container's live schemas on every model
  // request so mounts/unmounts take effect immediately.
  return {
    "tool.provider": async (_input, output) => {
      const available = new Map(tools.schemas().map((s) => [s.name, s]))
      for (const { source, target } of mappings) {
        const schema = available.get(source)
        if (!schema) continue
        output.tools[target] = project(source, target, schema) as unknown as ToolDefinition
      }
    },
  }
}

export default { id: "dsh-adapter", server: dshAdapter }
