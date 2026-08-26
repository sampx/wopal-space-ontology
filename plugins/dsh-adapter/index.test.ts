/**
 * dsh-tool-adapter — experiment 2 tests.
 *
 * Verifies the adapter's projection logic:
 *  - `enable:false` suppresses a mapping (no tool registered for that slot)
 *  - `source->target` name mapping (rename) is honored
 *  - absent container (no dsh engine) degrades to registering zero tools
 *  - an `enable:true` mapping for a container tool that does not exist is skipped
 *  - execute passes a per-call agent with header.id/header.cwd only (no
 *    container session is created)
 */
import { describe, expect, test, beforeEach, afterEach } from "bun:test"

type ContainerLogger = {
  info(message: string, extra?: unknown): void
  warn(message: string, extra?: unknown): void
  error(message: string, extra?: unknown): void
}

type Container = {
  get(name: "tools"): {
    schemas(): { name: string; description: string; parameters: unknown }[]
    execute(exec: unknown): Promise<{
      isError: boolean
      content?: { type: string; text?: string }[]
      error?: { message?: string }
    }>
  } | undefined
  logger(name: string): ContainerLogger
}

type AdapterOptions = {
  tools?: { source: string; target: string; enable: boolean }[]
  sandbox?: { enabled: boolean; mode?: string }
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

function fakeContainer(
  overrides?: Partial<Container["get"] extends never ? never : ReturnType<Container["get"]>>,
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
        ...overrides,
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
  }
}

let mod: { dshAdapter: (input: unknown, options?: AdapterOptions) => Promise<Record<string, unknown>> }

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
    expect(Object.keys(out)).toEqual(["tool"])
    const tool = (out as { tool: Record<string, unknown> }).tool
    expect(Object.keys(tool)).toEqual(["grep"])
    expect(tool.grep.description).toContain("dsh")
  })

  test("source->target rename is honored", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep2", enable: true }],
    })
    const tool = (out as { tool: Record<string, unknown> }).tool
    expect(Object.keys(tool)).toEqual(["grep2"])
  })

  test("missing container degrades to zero tools", async () => {
    delete (globalThis as Record<string, unknown>).__ellamakaDshContainer
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    expect(out).toEqual({})
  })

  test("mapping for a missing source tool is skipped", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, {
      tools: [
        { source: "nope", target: "missing", enable: true },
        { source: "glob", target: "glob", enable: true },
      ],
    })
    const tool = (out as { tool: Record<string, unknown> }).tool
    expect(Object.keys(tool)).toEqual(["glob"])
  })

  test("execute closure propagates container output with dsh-container metadata", async () => {
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer()
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    const res = await tool.execute({}, { sessionID: "ses-meta", directory: "/w" })
    expect(res.output).toBe("NEEDLE-here")
    expect(res.metadata.source).toBe("dsh-container")
  })

  test("execute passes a reusable session facade with header id, cwd, and events", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    const ctx = {
      sessionID: "ses-abc",
      directory: "/ellamaka/ws",
      worktree: "/ellamaka",
      ask: async () => {},
    }
    await tool.execute({}, ctx)
    await tool.execute({}, ctx)
    const exec = captured[0] as {
      agent?: { session?: { header?: { id?: string; cwd?: string }; events?: unknown[] } }
    }
    const repeated = captured[1] as { agent?: { session?: object } }
    expect(exec.agent?.session?.header?.id).toBe("ses-abc")
    expect(exec.agent?.session?.header?.cwd).toBe("/ellamaka/ws")
    expect(exec.agent?.session?.events).toEqual([])
    expect(repeated.agent?.session).toBe(exec.agent?.session)
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
    const tools = (out as { tool: Record<string, unknown> }).tool
    const ctx = {
      sessionID: "ses-permission",
      directory: "/workspace/app",
      worktree: "/workspace",
      ask: async (input: { permission: string; patterns: string[]; always: string[]; metadata: Record<string, unknown> }) => {
        asks.push(input)
      },
    }

    await (tools.read as Projected).execute({ file_path: "src/file.ts" }, ctx)
    await (tools.write as Projected).execute({ file_path: "/outside/file.ts", content: "next" }, ctx)
    await (tools.edit as Projected).execute({ file_path: "src/file.ts", old_string: "before", new_string: "after" }, ctx)

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
    const editor = (out as { tool: Record<string, unknown> }).tool.str_replace_editor as Projected
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
    const bash = (out as { tool: Record<string, unknown> }).tool.bash as Projected
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
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as {
      args: Record<string, unknown>
    }
    // The plugin SDK contract is a ZodRawShape: each property value is a Zod
    // type. The registry's fromPlugin path detects this and generates the
    // correct flat JSON Schema (not a nested document-as-properties schema).
    expect(Object.keys(tool.args)).toEqual(["pattern", "path"])
    expect("_zod" in (tool.args.pattern as object)).toBe(true)
    expect("_zod" in (tool.args.path as object)).toBe(true)
  })

  test("sandbox enabled injects sandbox/mode event into session facade", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: true, mode: "read-only" },
    })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    await tool.execute({}, { sessionID: "ses-sandbox", directory: "/w", worktree: "/w", ask: async () => {} })
    const exec = captured[0] as { agent?: { session?: { events?: unknown[] } } }
    expect(exec.agent?.session?.events).toEqual([{ type: "sandbox/mode", data: { mode: "read-only" } }])
  })

  test("sandbox enabled without mode defaults to workspace-write", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: true },
    })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    await tool.execute({}, { sessionID: "ses-default", directory: "/w", worktree: "/w", ask: async () => {} })
    const exec = captured[0] as { agent?: { session?: { events?: unknown[] } } }
    expect(exec.agent?.session?.events).toEqual([{ type: "sandbox/mode", data: { mode: "workspace-write" } }])
  })

  test("sandbox disabled leaves session facade events empty", async () => {
    const captured: unknown[] = []
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured.push(exec)
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, {
      tools: [{ source: "grep", target: "grep", enable: true }],
      sandbox: { enabled: false },
    })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    await tool.execute({}, { sessionID: "ses-nosandbox", directory: "/w", worktree: "/w", ask: async () => {} })
    const exec = captured[0] as { agent?: { session?: { events?: unknown[] } } }
    expect(exec.agent?.session?.events).toEqual([])
  })

  test("execute logs the tool call through the container logger", async () => {
    const logged: { level: string; message: string; extra?: unknown }[] = []
    const container = fakeContainer()
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = container
    const logger = container.logger("dsh-adapter")
    logger.info = (message, extra) => logged.push({ level: "info", message, extra })
    logger.error = (message, extra) => logged.push({ level: "error", message, extra })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
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
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    await expect(tool.execute({ pattern: "needle" }, { sessionID: "ses-log", directory: "/w" })).rejects.toThrow("boom")
    expect(logged.length).toBe(1)
    expect(logged[0].level).toBe("error")
    expect(logged[0].message).toBe("tool call failed")
    expect(logged[0].extra).toMatchObject({ tool: "grep", sessionID: "ses-log" })
  })
})
