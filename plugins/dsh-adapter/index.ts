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
 *   - session.events     — sandbox-mode policy fold + turn/approval audit
 *   - session.append     — audit-pair sink (approval/asked, approval/decided)
 *
 * Every tools.execute() dispatch is wrapped in a reference-counted turn
 * boundary (`turn/start` → dispatch → `turn/end`, finally-closed) so the dsh
 * approval plugin's open-turn precondition (`hasOpenTurn`) holds during
 * escalation audit.
 *
 * Escalation approval (Plan D-03/D-04/D-05): the adapter registers an
 * `approval/request` answerer on the container's cordis ctx. It routes each
 * dsh ask by session id to the calling turn's `ToolContext.ask` closure
 * (held in a per-session registry), asks ellamaka's Permission under
 * `sandbox_escalation` (patterns = the escalation target mode parsed from
 * the dsh reason, metadata = tool/callID/justification), and maps the
 * outcome — resolve → `allowed-once`, RejectedError/CorrectedError →
 * `rejected`, registry miss → `next()` (waterfall fail-closed). The
 * `escalation: "never"` option seeds an `approval/policy` event into every
 * facade so dsh's ApprovalService rejects deterministically before any
 * answerer dispatch.
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
  /**
   * The cordis event surface. The adapter registers its `approval/request`
   * answerer through it so dsh's ApprovalService waterfall can reach the
   * ellamaka Permission ask closure for the requesting session.
   */
  on(event: "approval/request", handler: (req: DshApprovalRequest, next: () => unknown) => unknown): unknown
}

/**
 * The dsh `approval/request` waterfall payload (structural subset: the
 * adapter only consumes the routing id and the prompt-text fields).
 */
type DshApprovalRequest = {
  agent?: { session?: { header?: { id?: string } } }
  toolName?: string
  callId?: string
  reason?: string
}

/**
 * The SDK ToolContext.ask input shape the escalation answerer builds
 * (Omit<Permission.Request, "id" | "sessionID" | "tool">).
 */
type AskInput = {
  permission: string
  patterns: string[]
  always: string[]
  metadata: Record<string, unknown>
}

type AskFn = (input: AskInput) => Promise<void>

/**
 * Extract the escalation target mode from a dsh approval reason. The dsh
 * escalation choreography (`approveEscalation`) formats every ask reason as
 * `escalate sandbox to ${mode}: ${justification}` — the mode is parsed back
 * out so the ellamaka ask advertises the exact target pattern.
 */
function targetModeFromReason(reason: string): string | undefined {
  const match = /^escalate sandbox to ([a-z-]+):/.exec(reason)
  return match?.[1]
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
  /**
   * Sandbox escalation approval policy (`ellamaka.dsh.sandbox.escalation`).
   * `ask` (the default) bridges dsh `approval/request` asks to ellamaka's
   * Permission (Workbench approval card); `never` seeds an `approval/policy`
   * event into every session facade so dsh's ApprovalService rejects every
   * escalation deterministically before any answerer dispatch (headless
   * stance, no UI prompt).
   */
  escalation?: "ask" | "never"
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

// Per-message sandbox mode selected in the composer. Carried on Tool.Context
// extra by the host; absent falls back to the space-level default.
type SandboxMode = "read-only" | "workspace-write" | "full-access"

// A session facade shaped for dsh consumers (approval plugin, sandbox fold).
// `events` is PRIVATE to this ellamaka session: seeded with a fresh copy of
// the sandbox-mode event so `append` (turn pairs, approval audit) can never
// leak into another session's log. `turnDepth` reference-counts concurrent
// tools.execute() calls so nested/concurrent dispatches emit exactly one
// turn/start — turn/end pair, closed only at the outermost level (the shape
// dsh's hasOpenTurn reverse-scan expects).
type FacadeSession = {
  header: { id: string; cwd: string }
  events: { type: string; data: unknown }[]
  append(type: string, data: unknown): void
  turnDepth: number
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
  const sessions = new Map<string, FacadeSession>()

  // Resolve the space-level escalation policy once at mount. `ask` (the
  // default) bridges dsh approval asks to ellamaka Permission; `never` seeds
  // an `approval/policy` override into every session facade so dsh's
  // ApprovalService rejects deterministically before any answerer dispatch.
  const escalation = options.escalation ?? "ask"
  const escalationPolicyEvents: { type: string; data: unknown }[] =
    escalation === "never" ? [{ type: "approval/policy", data: { policy: "never" } }] : []

  // Per-session ask closures for the escalation answerer. Registered on every
  // tools.execute() (the plugin SDK hands each call its own ToolContext.ask
  // bound to the live permission table); keyed by the ellamaka sessionID the
  // dsh request routes back through (req.agent.session.header.id).
  const askRegistry = new Map<string, AskFn>()

  // Escalation answerer bridge (Plan D-03/D-04): dsh's ApprovalService
  // waterfall asks THIS listener before falling through to fail-closed.
  // The ask closure is looked up by the requesting session's id; a hit asks
  // ellamaka Permission (`sandbox_escalation`) and maps the reply to the dsh
  // outcome vocabulary — resolve → `allowed-once`, RejectedError /
  // CorrectedError → `rejected`; a miss delegates via next() so the chain
  // ends at the service's own `unavailable` (fail closed). A container
  // without the cordis event surface (degraded container) skips the bridge:
  // asks then fall through to the service's own fail-closed `unavailable`.
  container.on?.("approval/request", (req, next) => {
    const sessionID = req.agent?.session?.header?.id
    const ask = sessionID !== undefined ? askRegistry.get(sessionID) : undefined
    if (!ask) return next()
    const targetMode = req.reason !== undefined ? targetModeFromReason(req.reason) : undefined
    return ask({
      permission: "sandbox_escalation",
      patterns: [targetMode ?? "escalation"],
      always: [targetMode ?? "escalation"],
      metadata: {
        tool: req.toolName,
        callID: req.callId,
        justification: req.reason,
        targetMode,
      },
    }).then(
      () => "allowed-once",
      (error: unknown) => {
        const name = (error as { name?: string } | undefined)?.name
        if (name === "PermissionRejectedError" || name === "PermissionCorrectedError") return "rejected"
        throw error
      },
    )
  })

  // Resolve the space-level sandbox policy once at mount. `enabled: true`
  // selects the sandbox backend and injects a `sandbox/mode` event into every
  // session facade; `enabled: false` (or absent) DISABLES the sandbox by
  // injecting `danger-full-access` — dsh's one-shot full-access mode. The
  // container's sandbox backend is never switched; only the effective mode is
  // loosened. `mode` defaults to `workspace-write` (the dsh base profile
  // default) when the sandbox is enabled.
  // Space-level default (mount-time fallback). The per-message mode from
  // Tool.Context.extra takes precedence; this only applies when the caller
  // did not select a mode (TUI sessions, queue follow-ups without a choice).
  const sandboxEnabled = options.sandbox?.enabled === true
  const defaultMode: SandboxMode = sandboxEnabled
    ? (options.sandbox?.mode === "read-only" ? "read-only" : "workspace-write")
    : "full-access"
  // Per-facade seed: the space-default sandbox mode fold + (never policy) the
  // approval policy override dsh's ApprovalService folds via
  // effectiveApprovalPolicy. Copied per session so appends never leak across
  // facades. Per-message overrides append at execute time (LAST-wins fold).
  // dsh event-log vocabulary: the composer's full-access preset folds to the
  // one-shot danger-full-access mode (never a space-level config value).
  const seedMode = defaultMode === "full-access" ? "danger-full-access" : defaultMode
  const sandboxEvents: { type: string; data: unknown }[] = [
    { type: "sandbox/mode", data: { mode: seedMode } },
    ...escalationPolicyEvents,
  ]

  // Per-session facade factory. Seeding copies `sandboxEvents` so each
  // session's log is independently appendable.
  function facadeFor(sessionID: string, directory: string): FacadeSession {
    let facade = sessions.get(sessionID)
    if (!facade) {
      facade = {
        header: { id: sessionID, cwd: directory },
        events: [...sandboxEvents],
        append(type, data) {
          this.events.push({ type, data })
        },
        turnDepth: 0,
      }
      sessions.set(sessionID, facade)
    }
    return facade
  }

  // dsh event-log vocabulary for the composer's full-access preset: the
  // one-shot danger-full-access fold. Never a space-level config value.
  function modeEventValue(mode: SandboxMode): string {
    return mode === "full-access" ? "danger-full-access" : mode
  }

  // Reference-counted turn boundary around one tools.execute() call. Concurrent
  // calls on the same session share a single open turn: the pair is emitted
  // only at the outermost nesting level, matching dsh's hasOpenTurn semantics.
  async function executeInTurn<T>(facade: FacadeSession, run: () => Promise<T>): Promise<T> {
    facade.turnDepth += 1
    if (facade.turnDepth === 1) facade.append("turn/start", {})
    try {
      return await run()
    } finally {
      facade.turnDepth -= 1
      if (facade.turnDepth === 0) facade.append("turn/end", {})
    }
  }

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
        const session = facadeFor(ctx.sessionID, ctx.directory)
        // Per-message sandbox override: the composer selector rides on
        // Tool.Context.extra. Appending a fresh sandbox/mode event (LAST-wins
        // fold) switches the effective mode mid-session. Every explicit
        // choice appends — including one equal to the space default — because
        // the facade may already carry an earlier per-message choice (e.g.
        // read-only from a previous turn); skipping same-as-default values
        // would leave that stale override in force. Absence keeps whatever
        // the facade currently folds to.
        const requestedMode = (ctx.extra as { sandboxMode?: SandboxMode } | undefined)?.sandboxMode
        if (requestedMode) {
          session.append("sandbox/mode", { mode: modeEventValue(requestedMode) })
        }
        // Register this call's ask closure for the escalation answerer: dsh
        // routes `approval/request` back through
        // `req.agent.session.header.id` (= ctx.sessionID), and the closure
        // carries the live ellamaka permission table of the calling turn.
        askRegistry.set(ctx.sessionID, ctx.ask)
        const agent = {
          session,
        }
        return executeInTurn(session, async () => {
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
        })
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
