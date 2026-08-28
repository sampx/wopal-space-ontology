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
 * Sandbox semantics (DESIGN §4.10): `enabled: true` selects the sandbox
 * backend and injects a `sandbox/mode` event (`read-only` or
 * `workspace-write`, default `workspace-write`) into each session facade.
 * `enabled: false` (or absent) DISABLES the sandbox by injecting
 * `danger-full-access` — dsh's one-shot full-access mode. It does NOT switch
 * the local fs/bash backend; tools always run through the same dsh container
 * and sandbox backend, only the effective mode is loosened.
 */
import type { Hooks, PluginInput, PluginOptions, ToolContext as PluginToolContext, ToolDefinition, ToolResult } from "@opencode-ai/plugin"
import path from "node:path"
import { z } from "zod"

type Container = {
  get(name: "tools"): {
    schemas(): { name: string; description: string; parameters: unknown }[]
    execute(exec: unknown): Promise<{
      isError: boolean
      content?: { type: string; text?: string }[]
      error?: { message?: string }
      meta?: unknown
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

// A projected container tool, shaped as an SDK `ToolDefinition`. args are a
// ZodRawShape (the plugin SDK contract): the registry's fromPlugin path
// detects Zod types and generates the correct flat JSON Schema. Passing the
// dsh JSON Schema document as-is would make the registry treat its top-level
// keys (type/properties/required) as property definitions, producing a nested
// schema the model cannot call.
type ProjectedTool = ToolDefinition

// The SDK ToolContext surface this adapter consumes, plus the optional
// callID the host Tool.Context carries at runtime.
type ToolContext = PluginToolContext & { callID?: string }

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
 * dsh tools use snake_case argument names; ellamaka's Workbench render layer
 * reads camelCase. The adapter maps the model-facing schema to camelCase so
 * the projected tool looks like a builtin, then maps back to snake_case
 * before dispatching into the dsh container.
 */
const ARG_NAME_MAP: Record<string, string> = {
  file_path: "filePath",
  old_string: "oldString",
  new_string: "newString",
}

function toCamelCase(name: string): string {
  return ARG_NAME_MAP[name] ?? name
}

function toSnakeCase(name: string): string {
  for (const [snake, camel] of Object.entries(ARG_NAME_MAP)) {
    if (camel === name) return snake
  }
  return name
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
    shape[toCamelCase(name)] = type
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

type DshDiff = { path: string; oldText: string | null; newText: string }

/**
 * Count added/removed lines between two texts using an order-sensitive,
 * duplicate-preserving LCS diff. A line present on both sides is not a change;
 * only lines unique to one side count toward the `+N/-N` badge, matching the
 * builtin edit tool's per-change statistics. Repeated lines are handled
 * correctly (e.g. `"same\nsame"` → `"same"` is `+0/-1`, not `+0/-0`).
 *
 * Uses a rolling LCS-length table (O(m) memory) instead of a full O(n*m) table,
 * so large hunks cannot exhaust memory. Retained lines equal the LCS length,
 * so deletions = n - LCS and additions = m - LCS. For very large hunks the
 * O(n*m) comparison is bounded by a threshold: beyond it the function returns
 * `null` so the caller omits the structured `filediff` entirely rather than
 * showing a misleading badge.
 */
function countLineChanges(before: string, after: string): { additions: number; deletions: number } | null {
  const beforeLines = before.split("\n")
  const afterLines = after.split("\n")
  const n = beforeLines.length
  const m = afterLines.length
  // Bound the O(n*m) LCS comparison. Beyond this, signal "too large to count
  // precisely" so the caller drops the filediff instead of emitting a wrong
  // badge.
  const MAX_LCS_CELLS = 1_000_000
  if (n * m > MAX_LCS_CELLS) {
    return null
  }
  let prev = new Array<number>(m + 1).fill(0)
  let curr = new Array<number>(m + 1).fill(0)
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      curr[j] = beforeLines[i] === afterLines[j]
        ? prev[j + 1] + 1
        : Math.max(prev[j], curr[j + 1])
    }
    ;[prev, curr] = [curr, prev]
  }
  const lcs = prev[0]
  return { additions: m - lcs, deletions: n - lcs }
}

/**
 * Extract an ellamaka `filediff` from dsh result `meta.diffs`.
 *
 * dsh's edit/write tools project `meta.diffs` (an array of `{path, oldText,
 * newText}` hunks, one per applied change) via their `presentationMeta`. The
 * Workbench render layer (`message-part.tsx`) consumes `filediff` with
 * `file`/`before`/`after` and derives the diff itself when `patch` is absent.
 *
 * The adapter merges every hunk into a single `filediff`: `before`/`after`
 * concatenate each hunk's old/new text, and the `+N/-N` badge sums the
 * per-hunk line changes. This mirrors dsh's own DiffBlock, which draws each
 * hunk's old side red and new side green without line numbers. Malformed or
 * absent meta yields `undefined` so the projected tool degrades to plain text.
 */
function filediffFromMeta(meta: unknown): { file: string; before: string; after: string; additions: number; deletions: number } | undefined {
  if (typeof meta !== "object" || meta === null || Array.isArray(meta)) return undefined
  const diffs = (meta as Record<string, unknown>).diffs
  if (!Array.isArray(diffs) || diffs.length === 0) return undefined
  const file = (diffs[0] as Partial<DshDiff> | undefined)?.path
  if (typeof file !== "string" || file.length === 0) return undefined
  const beforeParts: string[] = []
  const afterParts: string[] = []
  let additions = 0
  let deletions = 0
  for (const raw of diffs) {
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return undefined
    const diff = raw as Partial<DshDiff>
    if (typeof diff.path !== "string" || typeof diff.newText !== "string") return undefined
    if (diff.oldText !== null && typeof diff.oldText !== "string") return undefined
    const before = diff.oldText ?? ""
    const after = diff.newText
    beforeParts.push(before)
    afterParts.push(after)
    const counts = countLineChanges(before, after)
    // A null count means the hunk is too large to count precisely; omit the
    // structured filediff rather than show a misleading badge.
    if (counts === null) return undefined
    additions += counts.additions
    deletions += counts.deletions
  }
  return {
    file,
    before: beforeParts.join("\n"),
    after: afterParts.join("\n"),
    additions,
    deletions,
  }
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
      execute: async (args: Record<string, unknown>, ctx: ToolContext): Promise<ToolResult> => {
        // Map the model-facing camelCase args back to dsh snake_case before
        // permission checks and dispatch, so both read the same snake_case
        // surface the container expects.
        const dispatchArgs: Record<string, unknown> = {}
        for (const [key, value] of Object.entries(args)) {
          dispatchArgs[toSnakeCase(key)] = value
        }
        await askToolPermission(source, dispatchArgs, ctx)
        let session = sessions.get(ctx.sessionID)
        if (!session) {
          session = {
            header: { id: ctx.sessionID, cwd: ctx.directory },
            events: sandboxEvents,
          }
          sessions.set(ctx.sessionID, session)
        }
        const agent = {
          session,
        }
        const result = await tools.execute({
          callId: ctx.callID ?? `dsh-${source}-${Date.now()}`,
          name: source,
          arguments: dispatchArgs,
          signal: ctx.abort ?? new AbortController().signal,
          agent,
        })
        const output = contentText(result.content)
        if (result.isError) {
          const message = output || result.error?.message || `dsh tool "${source}" failed`
          log.error("tool call failed", { tool: source, sessionID: ctx.sessionID, callID: ctx.callID, error: message })
          throw new Error(message)
        }
        log.info("tool call", { tool: source, sessionID: ctx.sessionID, callID: ctx.callID })
        const metadata: Record<string, unknown> = { source: "dsh-container", containerTool: source }
        const filediff = filediffFromMeta(result.meta)
        if (filediff) metadata.filediff = filediff
        return {
          output,
          title: source,
          metadata,
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
        output.tools[target] = project(source, target, schema)
      }
    },
  }
}

export default { id: "dsh-adapter", server: dshAdapter }
