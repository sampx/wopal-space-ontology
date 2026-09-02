/**
 * dsh-tool-adapter — experiment 2 tests (P3.5 dynamic provider).
 *
 * The adapter now registers a `tool.provider` hook instead of a static
 * `tool` table, so the tool set is read from the container's live schemas on
 * every model request. Verifies:
 *  - `enable:false` suppresses a mapping (no tool registered for that slot)
 *  - `source->target` name mapping (rename) is honored
 *  - the provider reads the current container schemas per call, so adding or
 *    removing container tools shows up on the next provider invocation
 *  - absent container degrades to a provider that silently returns no tools
 *  - an `enable:true` mapping for a container tool that does not exist is skipped
 *  - `sandbox.enabled:false` (or absent) injects a `danger-full-access`
 *    `sandbox/mode` event; `sandbox.enabled:true` injects the configured mode
 *  - execute passes a per-call agent with header.id/header.cwd only (no
 *    container session is created)
 *  - the session facade owns a private events array (deep-copied sandbox
 *    seed) and exposes `append(type, data)` for audit pairs
 *  - every tools.execute() is wrapped in a turn boundary: `turn/start` before
 *    dispatch, `turn/end` in a finally (closed even when the tool throws),
 *    reference-counted so concurrent calls on the same session emit exactly
 *    one start/end pair at the outermost nesting level
 */
import { describe, expect, test, beforeEach, afterEach } from "bun:test"

type ContainerLogger = {
  info(message: string, extra?: unknown): void
  warn(message: string, extra?: unknown): void
  error(message: string, extra?: unknown): void
}

// An approval/request waterfall listener: dsh dispatches (req, next); the
// listener either answers with an ApprovalOutcome or delegates via next().
type ApprovalAnswerer = (req: unknown, next: () => unknown) => unknown

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
  logger(name: string): ContainerLogger
  /** Optional: the real cordis ctx exposes on(); fakes may capture listeners. */
  on?(event: string, handler: ApprovalAnswerer): unknown
}

type AdapterOptions = {
  tools?: { source: string; target: string; enable: boolean }[]
  sandbox?: { enabled: boolean; mode?: string }
  escalation?: "ask" | "never"
}

type ToolCtx = {
  sessionID: string
  directory: string
  worktree: string
  callID?: string
  ask(input: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }): Promise<void>
}

type Projected = {
  execute: (args: unknown, ctx: ToolCtx) => Promise<{ output: string; metadata: Record<string, unknown> }>
}

type ToolsService = {
  schemas(): { name: string; description: string; parameters: unknown }[]
  execute(exec: unknown): Promise<{
    isError: boolean
    content?: { type: string; text?: string }[]
    error?: { message?: string }
    meta?: unknown
  }>
}

function fakeContainer(
  tools?: Partial<ToolsService>,
  overrides?: Partial<Pick<Container, "get">>,
): Container {
  const loggers = new Map<string, ContainerLogger>()
  return {
    get(name) {
      if (name !== "tools") return undefined
      return {
        schemas: () => [
          { name: "grep", description: "dsh grep (ripgrep-backed)", parameters: {} },
          { name: "glob", description: "dsh glob", parameters: {} },
        ],
        execute: async () => ({
          isError: false,
          content: [{ type: "text", text: "NEEDLE-here" }],
        }),
        ...tools,
      }
    },
    logger(name) {
      let logger = loggers.get(name)
      if (!logger) {
        logger = { info: () => {}, warn: () => {}, error: () => {} }
        loggers.set(name, logger)
      }
      return logger
    },
    ...overrides,
  }
}

/**
 * A fake cordis container ctx that records `on` listeners and can dispatch
 * the `approval/request` waterfall, while still serving `tools`/`logger`
 * like the real container. Used in answerer tests: the adapter registers its
 * answerer via `container.on`, so tests exercise the mapping by dispatching
 * a captured listener.
 */
function fakeContainerCtx(
  tools?: Partial<ToolsService>,
): {
  get(name: "tools"): ToolsService | undefined
  logger(name: string): ContainerLogger
  on(event: string, handler: ApprovalAnswerer): unknown
  dispatchApprovalRequest(req: unknown): unknown
} {
  const inner = fakeContainer(tools)
  const listeners = new Map<string, ApprovalAnswerer[]>()
  return {
    get: (name) => inner.get(name),
    logger: (name) => inner.logger(name),
    on(event, handler) {
      const list = listeners.get(event) ?? []
      list.push(handler)
      listeners.set(event, list)
    },
    dispatchApprovalRequest(req: unknown) {
      // Mirror cordis waterfall: outermost listener composes around next().
      let chain: ApprovalAnswerer = () => "unavailable"
      for (const handler of [...(listeners.get("approval/request") ?? [])].reverse()) {
        const innerNext = chain
        chain = (req2: unknown) => handler(req2, () => innerNext(req2))
      }
      return chain(req)
    },
  }
}

let mod: { dshAdapter: (input: unknown, options?: AdapterOptions) => Promise<Record<string, unknown>> }

type ProviderOutput = { tools: Record<string, unknown> }

async function invokeProvider(out: Record<string, unknown>): Promise<Record<string, unknown>> {
  const provider = out["tool.provider"] as (
    input: unknown,
    output: ProviderOutput,
  ) => Promise<void>
  const output: ProviderOutput = { tools: {} }
  await provider({}, output)
  return output.tools
}

beforeEach(async () => {
  mod = await import("./index")
})

afterEach(() => {
  delete globalThis.__ellamakaDshContainer
})

describe("dsh-adapter projection", () => {
  test("enable:false suppresses a mapping entirely", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: false }],
    })
    expect(out).toEqual({})
  })

  test("enable:true projects container tool onto target slot (same-name)", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
    })
    expect(Object.keys(out)).toEqual(["tool.provider"])
    const tools = await invokeProvider(out)
    expect(Object.keys(tools)).toEqual(["grep"])
    expect((tools.grep as { description: string }).description).toContain("dsh")
  })

  test("source->target rename is honored", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep2", enable: true }],
    })
    const tools = await invokeProvider(out)
    expect(Object.keys(tools)).toEqual(["grep2"])
  })

  test("missing container degrades to a provider that returns no tools", async () => {
    delete (globalThis as Record<string, unknown>).__ellamakaDshContainer
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    expect(Object.keys(out)).toEqual(["tool.provider"])
    const tools = await invokeProvider(out)
    expect(Object.keys(tools)).toEqual([])
  })

  test("mapping for a missing source tool is skipped", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, {
      tools: [
        { source: "nope", target: "missing", enable: true },
        { source: "glob", target: "glob", enable: true },
      ],
    })
    const tools = await invokeProvider(out)
    expect(Object.keys(tools)).toEqual(["glob"])
  })

  test("provider reflects container schema additions across invocations", async () => {
    const schemas: { name: string; description: string; parameters: unknown }[] = [
      { name: "grep", description: "dsh grep", parameters: {} },
      { name: "glob", description: "dsh glob", parameters: {} },
    ]
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => schemas,
    })
    const out = await mod.dshAdapter({}, {
      tools: [
        { source: "grep", target: "grep", enable: true },
        { source: "glob", target: "glob", enable: true },
        { source: "bash", target: "bash", enable: true },
      ],
    })
    expect(Object.keys(await invokeProvider(out))).toEqual(["grep", "glob"])

    schemas.push({ name: "bash", description: "dsh bash", parameters: {} })
    expect(Object.keys(await invokeProvider(out))).toEqual(["grep", "glob", "bash"])

    schemas.splice(0, 1)
    expect(Object.keys(await invokeProvider(out))).toEqual(["glob", "bash"])
  })

  test("execute closure propagates container output with dsh-container metadata", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const res = await tool.execute({}, { sessionID: "ses-meta", directory: "/w" })
    expect(res.output).toBe("NEEDLE-here")
    expect(res.metadata.source).toBe("dsh-container")
  })

  test("execute passes a reusable session facade with header id, cwd, and events", async () => {
    const captured: { exec: unknown; eventsAtDispatch: unknown[] }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        const events = (exec as { agent?: { session?: { events?: unknown[] } } }).agent?.session?.events ?? []
        captured.push({ exec, eventsAtDispatch: [...events] })
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const ctx = {
      sessionID: "ses-abc",
      directory: "/ellamaka/ws",
      worktree: "/ellamaka",
      ask: async () => {},
    }
    await tool.execute({}, ctx)
    await tool.execute({}, ctx)
    const first = captured[0]
    const repeated = captured[1] as { exec: { agent?: { session?: object } } }
    const exec = first.exec as {
      agent?: { session?: { header?: { id?: string; cwd?: string }; events?: unknown[] } }
    }
    expect(exec.agent?.session?.header?.id).toBe("ses-abc")
    expect(exec.agent?.session?.header?.cwd).toBe("/ellamaka/ws")
    // Sandbox option absent -> adapter injects danger-full-access (P3.5); the
    // dispatch happens inside an open turn (snapshot taken before the
    // finally-closed turn/end is appended).
    expect(first.eventsAtDispatch).toEqual([
      { type: "sandbox/mode", data: { mode: "danger-full-access" } },
      { type: "turn/start", data: {} },
    ])
    expect(repeated.exec.agent?.session).toBe(exec.agent?.session)
  })

  test("session facade owns a private events array per session", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const ctxA = { sessionID: "ses-a", directory: "/w", worktree: "/w", ask: async () => {} }
    const ctxB = { sessionID: "ses-b", directory: "/w", worktree: "/w", ask: async () => {} }
    await tool.execute({}, ctxA)
    await tool.execute({}, ctxB)
    const execA = captured[0] as { agent?: { session?: { events?: unknown[] } } }
    const execB = captured[1] as { agent?: { session?: { events?: unknown[] } } }
    const eventsA = execA.agent?.session?.events
    const eventsB = execB.agent?.session?.events
    // Per-session arrays: appending turn events for session A must not leak
    // into session B's log (the shared sandboxEvents array would break this).
    expect(eventsA).not.toBe(eventsB)
    expect(eventsB).toEqual([
      { type: "sandbox/mode", data: { mode: "danger-full-access" } },
      { type: "turn/start", data: {} },
      { type: "turn/end", data: {} },
    ])
  })

  test("facade append pushes typed events onto the session events array", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const ctx = { sessionID: "ses-append", directory: "/w", worktree: "/w", ask: async () => {} }
    await tool.execute({}, ctx)
    await tool.execute({}, ctx)
    // Both dispatches run inside the SAME session facade (cached by
    // sessionID). The live events array ends with two closed turn pairs —
    // the append surface approval/asked will use between them.
    const exec = captured[1] as { agent?: { session?: { events?: { type: string; data: unknown }[] } } }
    expect(exec.agent?.session?.events).toEqual([
      { type: "sandbox/mode", data: { mode: "danger-full-access" } },
      { type: "turn/start", data: {} },
      { type: "turn/end", data: {} },
      { type: "turn/start", data: {} },
      { type: "turn/end", data: {} },
    ])
  })

  test("execute closes the turn when the tool throws", async () => {
    const captured: { events?: { type: string; data: unknown }[] }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        // Capture the live events array reference: the facade's finally block
        // appends to this same array after the tool throws.
        captured.push({
          events: (exec as { agent?: { session?: { events?: { type: string; data: unknown }[] } } }).agent?.session?.events,
        })
        throw new Error("boom")
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await expect(
      tool.execute({}, { sessionID: "ses-throw", directory: "/w", worktree: "/w", ask: async () => {} }),
    ).rejects.toThrow("boom")
    // finally-closed: hasOpenTurn's reverse scan must see turn/end after the
    // matching turn/start, or the approval precondition breaks on the next call.
    const events = captured[0]?.events ?? []
    expect(events[events.length - 1].type).toBe("turn/end")
  })

  test("concurrent executes share one outermost turn pair (reference counting)", async () => {
    const captured: { events?: { type: string; data: unknown }[] }[] = []
    let release!: () => void
    const gate = new Promise<void>((resolve) => {
      release = resolve
    })
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push({
          events: (exec as { agent?: { session?: { events?: { type: string; data: unknown }[] } } }).agent?.session?.events,
        })
        await gate
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const ctx = { sessionID: "ses-concurrent", directory: "/w", worktree: "/w", ask: async () => {} }
    // Two calls dispatched in parallel on the same session; both block inside
    // the container until `release`.
    const first = tool.execute({}, ctx)
    const second = tool.execute({}, ctx)
    release()
    await Promise.all([first, second])
    const events = captured[0]?.events ?? []
    const types = events.map((event) => event.type)
    expect(types.filter((type) => type === "turn/start")).toHaveLength(1)
    expect(types.filter((type) => type === "turn/end")).toHaveLength(1)
    expect(types[0]).toBe("sandbox/mode")
    expect(types[1]).toBe("turn/start")
    expect(types[types.length - 1]).toBe("turn/end")
  })

  test("execute preserves ellamaka file and external-directory permission gates", async () => {
    const asks: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        { name: "read", description: "dsh read", parameters: { properties: { file_path: { type: "string" } } } },
        {
          name: "write",
          description: "dsh write",
          parameters: { properties: { file_path: { type: "string" }, content: { type: "string" } } },
        },
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" }, old_string: { type: "string" }, new_string: { type: "string" } } },
        },
      ],
    })
    const out = await mod.dshAdapter({}, {
      tools: [
        { source: "read", target: "read", enable: true },
        { source: "write", target: "write", enable: true },
        { source: "edit", target: "edit", enable: true },
      ],
    })
    const tools = await invokeProvider(out)
    const ctx = {
      sessionID: "ses-permission",
      directory: "/workspace/app",
      worktree: "/workspace",
      ask: async (input: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }) => {
        asks.push(input)
      },
    }

    await (tools.read as Projected).execute({ filePath: "src/file.ts" }, ctx)
    await (tools.write as Projected).execute({ filePath: "/outside/file.ts", content: "next" }, ctx)
    await (tools.edit as Projected).execute({ filePath: "src/file.ts", oldString: "before", newString: "after" }, ctx)

    expect(asks).toEqual([
      { permission: "read", patterns: ["app/src/file.ts"], always: ["*"], metadata: {} },
      {
        permission: "external_directory",
        patterns: ["/outside/*"],
        always: ["/outside/*"],
        metadata: { filepath: "/outside/file.ts", parentDir: "/outside" },
      },
      { permission: "edit", patterns: ["../outside/file.ts"], always: ["*"], metadata: {} },
      { permission: "edit", patterns: ["app/src/file.ts"], always: ["*"], metadata: {} },
    ])
  })

  test("str_replace_editor preserves read, edit, and external-directory gates by command", async () => {
    const asks: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "str_replace_editor",
          description: "dsh editor",
          parameters: { properties: { command: { type: "string" }, path: { type: "string" } } },
        },
      ],
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "str_replace_editor", target: "str_replace_editor", enable: true }],
    })
    const tools = await invokeProvider(out)
    const editor = tools.str_replace_editor as Projected
    const ctx = {
      sessionID: "ses-editor-permission",
      directory: "/workspace/app",
      worktree: "/workspace",
      ask: async (input: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }) => {
        asks.push(input)
      },
    }

    await editor.execute({ command: "view", path: "/workspace/app/file.ts" }, ctx)
    await editor.execute({ command: "create", path: "/outside/new.ts", file_text: "created" }, ctx)

    expect(asks).toEqual([
      { permission: "read", patterns: ["app/file.ts"], always: ["*"], metadata: {} },
      {
        permission: "external_directory",
        patterns: ["/outside/*"],
        always: ["/outside/*"],
        metadata: { filepath: "/outside/new.ts", parentDir: "/outside" },
      },
      { permission: "edit", patterns: ["../outside/new.ts"], always: ["*"], metadata: {} },
    ])
  })

  test("bash preserves ellamaka's command permission gate", async () => {
    const asks: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "bash",
          description: "dsh bash",
          parameters: { properties: { command: { type: "string" }, description: { type: "string" } } },
        },
      ],
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "bash", target: "bash", enable: true }] })
    const tools = await invokeProvider(out)
    const bash = tools.bash as Projected
    const ctx = {
      sessionID: "ses-bash-permission",
      directory: "/workspace/app",
      worktree: "/workspace",
      ask: async (input: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }) => {
        asks.push(input)
      },
    }

    await bash.execute({ command: "printf adapter-ok", description: "Print adapter proof" }, ctx)

    expect(asks).toEqual([
      {
        permission: "bash",
        patterns: ["printf adapter-ok"],
        always: ["printf adapter-ok"],
        metadata: {},
      },
    ])
  })

  test("projects a dsh JSON Schema document into a ZodRawShape args map", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "grep",
          description: "dsh grep (ripgrep-backed)",
          parameters: {
            type: "object",
            properties: {
              pattern: { type: "string", required: true, description: "Regular expression" },
              path: { type: "string", description: "File or directory to search" },
            },
            required: ["pattern"],
          },
        },
      ],
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as { args: Record<string, unknown> }
    // The plugin SDK contract is a ZodRawShape: each property value is a Zod
    // type. The registry's fromPlugin path detects this and generates the
    // correct flat JSON Schema (not a nested document-as-properties schema).
    expect(Object.keys(tool.args)).toEqual(["pattern", "path"])
    expect("_zod" in (tool.args.pattern as object)).toBe(true)
    expect("_zod" in (tool.args.path as object)).toBe(true)
  })

  test("sandbox enabled injects sandbox/mode event into session facade", async () => {
    const captured: { eventsAtDispatch: unknown[] }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        const events = (exec as { agent?: { session?: { events?: unknown[] } } }).agent?.session?.events ?? []
        captured.push({ eventsAtDispatch: [...events] })
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: true, mode: "read-only" },
    })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, { sessionID: "ses-sandbox", directory: "/w", worktree: "/w", ask: async () => {} })
    expect(captured[0]?.eventsAtDispatch).toEqual([
      { type: "sandbox/mode", data: { mode: "read-only" } },
      { type: "turn/start", data: {} },
    ])
  })

  test("sandbox enabled without mode defaults to workspace-write", async () => {
    const captured: { eventsAtDispatch: unknown[] }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        const events = (exec as { agent?: { session?: { events?: unknown[] } } }).agent?.session?.events ?? []
        captured.push({ eventsAtDispatch: [...events] })
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: true },
    })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, { sessionID: "ses-default", directory: "/w", worktree: "/w", ask: async () => {} })
    expect(captured[0]?.eventsAtDispatch).toEqual([
      { type: "sandbox/mode", data: { mode: "workspace-write" } },
      { type: "turn/start", data: {} },
    ])
  })

  test("sandbox disabled injects danger-full-access mode event", async () => {
    const captured: { eventsAtDispatch: unknown[] }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        const events = (exec as { agent?: { session?: { events?: unknown[] } } }).agent?.session?.events ?? []
        captured.push({ eventsAtDispatch: [...events] })
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: false },
    })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, { sessionID: "ses-nosandbox", directory: "/w", worktree: "/w", ask: async () => {} })
    expect(captured[0]?.eventsAtDispatch).toEqual([
      { type: "sandbox/mode", data: { mode: "danger-full-access" } },
      { type: "turn/start", data: {} },
    ])
  })

  test("sandbox config absent injects danger-full-access mode event", async () => {
    const captured: { eventsAtDispatch: unknown[] }[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        const events = (exec as { agent?: { session?: { events?: unknown[] } } }).agent?.session?.events ?? []
        captured.push({ eventsAtDispatch: [...events] })
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, { sessionID: "ses-noopt", directory: "/w", worktree: "/w", ask: async () => {} })
    expect(captured[0]?.eventsAtDispatch).toEqual([
      { type: "sandbox/mode", data: { mode: "danger-full-access" } },
      { type: "turn/start", data: {} },
    ])
  })

  test("execute logs the tool call through the container logger", async () => {
    const logged: { level: string; message: string; extra?: unknown }[] = []
    const container = fakeContainer()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = container
    const logger = container.logger("dsh-adapter")
    logger.info = (message, extra) => logged.push({ level: "info", message, extra })
    logger.error = (message, extra) => logged.push({ level: "error", message, extra })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({ pattern: "needle" }, { sessionID: "ses-log", directory: "/w", callID: "call-1" })
    expect(logged.length).toBe(1)
    expect(logged[0].level).toBe("info")
    expect(logged[0].message).toBe("tool call")
    expect(logged[0].extra).toMatchObject({ tool: "grep", sessionID: "ses-log", callID: "call-1" })
  })

  test("execute logs tool errors through the container logger", async () => {
    const logged: { level: string; message: string; extra?: unknown }[] = []
    const container = fakeContainer({
      execute: async () => ({ isError: true, error: { message: "boom" } }),
    })
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = container
    const logger = container.logger("dsh-adapter")
    logger.error = (message, extra) => logged.push({ level: "error", message, extra })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await expect(tool.execute({ pattern: "needle" }, { sessionID: "ses-log", directory: "/w" })).rejects.toThrow("boom")
    expect(logged.length).toBe(1)
    expect(logged[0].level).toBe("error")
    expect(logged[0].message).toBe("tool call failed")
    expect(logged[0].extra).toMatchObject({ tool: "grep", sessionID: "ses-log" })
  })

  test("execute projects dsh meta.diffs into ellamaka filediff metadata", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" }, old_string: { type: "string" }, new_string: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "Edit applied successfully." }],
        meta: {
          diffs: [
            { path: "/workspace/app/src/file.ts", oldText: "unchanged\nold\n", newText: "unchanged\nnew\n" },
          ],
        },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "edit", target: "edit", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.edit as Projected
    const res = await tool.execute(
      { filePath: "/workspace/app/src/file.ts", oldString: "old", newString: "new" },
      { sessionID: "ses-diff", directory: "/workspace/app", worktree: "/workspace", ask: async () => {} },
    )
    const filediff = res.metadata.filediff as {
      file: string
      before: string
      after: string
      additions: number
      deletions: number
    }
    expect(filediff.file).toBe("/workspace/app/src/file.ts")
    expect(filediff.before).toBe("unchanged\nold\n")
    expect(filediff.after).toBe("unchanged\nnew\n")
    // Only the changed line counts; the shared context line is not a change.
    expect(filediff.additions).toBe(1)
    expect(filediff.deletions).toBe(1)
  })

  test("execute maps dsh snake_case args to ellamaka camelCase before dispatch", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" }, old_string: { type: "string" }, new_string: { type: "string" } } },
        },
      ],
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "edit", target: "edit", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.edit as Projected
    await tool.execute(
      { filePath: "/workspace/app/src/file.ts", oldString: "before", newString: "after" },
      { sessionID: "ses-map", directory: "/workspace/app", worktree: "/workspace", ask: async () => {} },
    )
    const exec = captured[0] as { arguments?: Record<string, unknown> }
    expect(exec.arguments).toEqual({
      file_path: "/workspace/app/src/file.ts",
      old_string: "before",
      new_string: "after",
    })
  })

  test("execute preserves unmapped args unchanged when dispatching", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "write",
          description: "dsh write",
          parameters: { properties: { file_path: { type: "string" }, content: { type: "string" } } },
        },
      ],
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "write", target: "write", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.write as Projected
    await tool.execute(
      { filePath: "/workspace/app/src/file.ts", content: "hello" },
      { sessionID: "ses-unmapped", directory: "/workspace/app", worktree: "/workspace", ask: async () => {} },
    )
    const exec = captured[0] as { arguments?: Record<string, unknown> }
    expect(exec.arguments).toEqual({
      file_path: "/workspace/app/src/file.ts",
      content: "hello",
    })
  })

  test("filediffFromMeta degrades to undefined on malformed meta", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "ok" }],
        meta: { diffs: [{ path: "x", newText: null }] },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "edit", target: "edit", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.edit as Projected
    const res = await tool.execute(
      { filePath: "/workspace/app/src/file.ts" },
      { sessionID: "ses-malformed", directory: "/workspace/app", worktree: "/workspace", ask: async () => {} },
    )
    expect(res.metadata.filediff).toBeUndefined()
  })

  test("filediffFromMeta counts repeated-line changes correctly", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "ok" }],
        meta: { diffs: [{ path: "/w/f.ts", oldText: "same\nsame\n", newText: "same\n" }] },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "edit", target: "edit", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.edit as Projected
    const res = await tool.execute(
      { filePath: "/w/f.ts" },
      { sessionID: "ses-repeat", directory: "/w", worktree: "/w", ask: async () => {} },
    )
    const filediff = res.metadata.filediff as { additions: number; deletions: number }
    // One repeated line removed; the surviving "same" line is not a change.
    expect(filediff.additions).toBe(0)
    expect(filediff.deletions).toBe(1)
  })

  test("filediffFromMeta counts pure insertion with no deletions", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "write",
          description: "dsh write",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "ok" }],
        meta: { diffs: [{ path: "/w/f.ts", oldText: null, newText: "new\nline\n" }] },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "write", target: "write", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.write as Projected
    const res = await tool.execute(
      { filePath: "/w/f.ts" },
      { sessionID: "ses-insert", directory: "/w", worktree: "/w", ask: async () => {} },
    )
    const filediff = res.metadata.filediff as { additions: number; deletions: number }
    expect(filediff.additions).toBe(2)
    expect(filediff.deletions).toBe(0)
  })

  test("filediffFromMeta merges multiple hunks into one filediff", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "ok" }],
        meta: {
          diffs: [
            { path: "/w/f.ts", oldText: "old1\n", newText: "new1\n" },
            { path: "/w/f.ts", oldText: "old2\n", newText: "new2\n" },
          ],
        },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "edit", target: "edit", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.edit as Projected
    const res = await tool.execute(
      { filePath: "/w/f.ts" },
      { sessionID: "ses-multi", directory: "/w", worktree: "/w", ask: async () => {} },
    )
    const filediff = res.metadata.filediff as { file: string; before: string; after: string; additions: number; deletions: number }
    expect(filediff.file).toBe("/w/f.ts")
    expect(filediff.before).toBe("old1\n\nold2\n")
    expect(filediff.after).toBe("new1\n\nnew2\n")
    expect(filediff.additions).toBe(2)
    expect(filediff.deletions).toBe(2)
  })

  test("filediffFromMeta degrades to undefined when a later hunk is null", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "edit",
          description: "dsh edit",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "ok" }],
        meta: {
          diffs: [
            { path: "/w/f.ts", oldText: "old\n", newText: "new\n" },
            null,
          ],
        },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "edit", target: "edit", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.edit as Projected
    const res = await tool.execute(
      { filePath: "/w/f.ts" },
      { sessionID: "ses-nullhunk", directory: "/w", worktree: "/w", ask: async () => {} },
    )
    expect(res.metadata.filediff).toBeUndefined()
  })

  test("filediffFromMeta omits filediff for oversized hunks", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "write",
          description: "dsh write",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
      execute: async () => ({
        isError: false,
        content: [{ type: "text", text: "ok" }],
        meta: {
          diffs: [
            { path: "/w/f.ts", oldText: "x\n".repeat(2000), newText: "y\n".repeat(2000) },
          ],
        },
      }),
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "write", target: "write", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.write as Projected
    const res = await tool.execute(
      { filePath: "/w/f.ts" },
      { sessionID: "ses-oversize", directory: "/w", worktree: "/w", ask: async () => {} },
    )
    // 2000*2000 = 4M cells > 1M threshold; the filediff is omitted rather than
    // showing a misleading badge.
    expect(res.metadata.filediff).toBeUndefined()
  })

  test("projected args expose camelCase filePath for read/edit/write", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      schemas: () => [
        {
          name: "read",
          description: "dsh read",
          parameters: { properties: { file_path: { type: "string" } } },
        },
      ],
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "read", target: "read", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.read as { args: Record<string, unknown> }
    expect(Object.keys(tool.args)).toEqual(["filePath"])
  })
})

describe("dsh-adapter escalation answerer bridge", () => {
  /** The dsh escalation reason shape: `escalate sandbox to ${mode}: ${justification}`. */
  const escalationRequest = (overrides?: Partial<Record<string, unknown>>) => ({
    agent: { session: { header: { id: "ses-esc" } } },
    toolName: "bash",
    callId: "call-esc-1",
    reason: "escalate sandbox to danger-full-access: need to write outside the workspace",
    ...overrides,
  })

  test("registers an approval/request answerer on the container ctx", async () => {
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = containerCtx
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    expect(Object.keys(out)).toEqual(["tool.provider"])
    const tools = await invokeProvider(out)
    expect(Object.keys(tools)).toEqual(["grep"])
    // Run one execute so the ask closure registers for ses-esc...
    const tool = tools.grep as Projected
    await tool.execute({}, {
      sessionID: "ses-esc",
      directory: "/w",
      worktree: "/w",
      ask: async () => {},
    })
    // ...then the answerer must be present and route the request.
    const outcome = await containerCtx.dispatchApprovalRequest(escalationRequest())
    expect(outcome).toBe("allowed-once")
  })

  test("no container ctx.on (legacy fake) degrades: provider still works", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    expect(Object.keys(tools)).toEqual(["grep"])
  })

  test("ask resolve maps to allowed-once with sandbox_escalation ask params", async () => {
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = containerCtx
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const asks: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }[] = []
    const tool = tools.grep as Projected
    await tool.execute({}, {
      sessionID: "ses-esc",
      directory: "/w",
      worktree: "/w",
      ask: async (input) => {
        asks.push(input)
      },
    })
    const outcome = await containerCtx.dispatchApprovalRequest(escalationRequest())
    expect(outcome).toBe("allowed-once")
    expect(asks).toEqual([
      {
        permission: "sandbox_escalation",
        patterns: ["danger-full-access"],
        always: ["danger-full-access"],
        metadata: {
          tool: "bash",
          callID: "call-esc-1",
          justification: "escalate sandbox to danger-full-access: need to write outside the workspace",
          targetMode: "danger-full-access",
        },
      },
    ])
  })

  test("ask RejectedError maps to rejected", async () => {
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = containerCtx
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const rejected = Object.assign(new Error("The user rejected permission to use this specific tool call."), { name: "PermissionRejectedError" })
    await tool.execute({}, {
      sessionID: "ses-esc",
      directory: "/w",
      worktree: "/w",
      ask: async () => {
        throw rejected
      },
    })
    const outcome = await containerCtx.dispatchApprovalRequest(escalationRequest())
    expect(outcome).toBe("rejected")
  })

  test("ask CorrectedError maps to rejected", async () => {
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = containerCtx
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    const corrected = Object.assign(new Error("rejected with feedback: no"), { name: "PermissionCorrectedError", feedback: "no" })
    await tool.execute({}, {
      sessionID: "ses-esc",
      directory: "/w",
      worktree: "/w",
      ask: async () => {
        throw corrected
      },
    })
    const outcome = await containerCtx.dispatchApprovalRequest(escalationRequest())
    expect(outcome).toBe("rejected")
  })

  test("unknown session (askRegistry miss) delegates via next() and yields unavailable", async () => {
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = containerCtx
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, {
      sessionID: "ses-known",
      directory: "/w",
      worktree: "/w",
      ask: async () => {},
    })
    // The request routes to an unregistered session: fail-closed waterfall.
    const outcome = await containerCtx.dispatchApprovalRequest(escalationRequest({
      agent: { session: { header: { id: "ses-stranger" } } },
    }))
    expect(outcome).toBe("unavailable")
  })

  test("escalation: never seeds an approval/policy event into every session facade", async () => {
    const captured: { events?: { type: string; data: unknown }[] }[] = []
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = {
      ...containerCtx,
      get(name: "tools") {
        if (name !== "tools") return undefined
        return {
          schemas: () => [
            { name: "grep", description: "dsh grep (ripgrep-backed)", parameters: {} },
            { name: "glob", description: "dsh glob", parameters: {} },
          ],
          execute: async (exec: unknown) => {
            captured.push({
              events: (exec as { agent?: { session?: { events?: { type: string; data: unknown }[] } } }).agent?.session?.events,
            })
            return { isError: false, content: [{ type: "text", text: "ok" }] }
          },
        }
      },
    }
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: true, mode: "workspace-write" },
      escalation: "never",
    })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, { sessionID: "ses-never", directory: "/w", worktree: "/w", ask: async () => {} })
    // The policy fold rides the seeded log; dsh's ApprovalService decides
    // 'never' before any answerer dispatch (deterministic rejection).
    expect(captured[0]?.events?.[0]).toEqual({ type: "sandbox/mode", data: { mode: "workspace-write" } })
    expect(captured[0]?.events?.[1]).toEqual({ type: "approval/policy", data: { policy: "never" } })
    expect(captured[0]?.events?.[2]).toEqual({ type: "turn/start", data: {} })
  })

  test("escalation: never never invokes the ellamaka ask closure", async () => {
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = containerCtx
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      escalation: "never",
    })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    let asked = 0
    await tool.execute({}, {
      sessionID: "ses-never",
      directory: "/w",
      worktree: "/w",
      ask: async () => {
        asked += 1
      },
    })
    await containerCtx.dispatchApprovalRequest(escalationRequest())
    // dsh service-level short-circuit; the answerer must not reach ask() as a
    // live UI prompt. (The bridge itself never runs for 'never'.)
    expect(asked).toBe(0)
  })

  test("escalation: ask (default) registers no approval/policy override", async () => {
    const captured: { events?: { type: string; data: unknown }[] }[] = []
    const containerCtx = fakeContainerCtx()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = {
      ...containerCtx,
      get(name: "tools") {
        if (name !== "tools") return undefined
        return {
          schemas: () => [
            { name: "grep", description: "dsh grep (ripgrep-backed)", parameters: {} },
            { name: "glob", description: "dsh glob", parameters: {} },
          ],
          execute: async (exec: unknown) => {
            captured.push({
              events: (exec as { agent?: { session?: { events?: { type: string; data: unknown }[] } } }).agent?.session?.events,
            })
            return { isError: false, content: [{ type: "text", text: "ok" }] }
          },
        }
      },
    }
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: true, mode: "workspace-write" },
    })
    const tools = await invokeProvider(out)
    const tool = tools.grep as Projected
    await tool.execute({}, { sessionID: "ses-ask-default", directory: "/w", worktree: "/w", ask: async () => {} })
    const types = (captured[0]?.events ?? []).map((event) => event.type)
    expect(types).not.toContain("approval/policy")
  })
})
