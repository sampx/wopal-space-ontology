/**
 * dsh-tool-adapter — experiment 2 (research §17, guesses S1–S6).
 *
 * An ellamaka server plugin that projects tools from the in-process dsh
 * container into ellamaka's ToolRegistry through the plugin.tool path. The
 * container is exposed by serve.ts (ELLAMAKA_DSH=1) on
 * globalThis.__ellamakaDshContainer after mounting fs-search on the
 * container's global layer.
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

type Container = {
  get(name: "tools"): {
    schemas(): { name: string; description: string; parameters: unknown }[]
    execute(exec: unknown): Promise<{
      isError: boolean
      content?: { type: string; text?: string }[]
      error?: { message?: string }
    }>
  } | undefined
}

export type DshAdapterOptions = {
  tools?: { source: string; target: string; enable: boolean }[]
}

// A projected container tool. args are a JSON Schema object (dsh ToolSchema.parameters);
// the registry consumes them through the legacyJsonSchema path, so the zod-shape
// ToolDefinition typing does not apply here. Cast to Hooks["tool"] at the boundary.
type ProjectedTool = {
  description: string
  args: Record<string, unknown>
  execute: (args: unknown, ctx: Record<string, unknown>) => Promise<{ output: string; title: string; metadata: Record<string, unknown> }>
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

  const available = new Map(tools.schemas().map((s) => [s.name, s]))
  const projected: Record<string, ProjectedTool> = {}

  for (const { source, target } of mappings) {
    const schema = available.get(source)
    if (!schema) continue
    projected[target] = {
      description: schema.description,
      args: schema.parameters as Record<string, unknown>,
      execute: async (args, ctx) => {
        const toolCtx = ctx as { abort?: AbortSignal; sessionID: string; callID?: string }
        const result = await tools.execute({
          callId: toolCtx.callID ?? `dsh-${source}-${Date.now()}`,
          name: source,
          arguments: args,
          signal: toolCtx.abort ?? new AbortController().signal,
        })
        const output = contentText(result.content)
        if (result.isError) {
          throw new Error(output || result.error?.message || `dsh tool "${source}" failed`)
        }
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
