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
}

type ToolCtx = {
  sessionID: string
  directory: string
  callID?: string
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

  test("execute passes a per-call agent with header id and cwd only", async () => {
    let captured: unknown
    ;(globalThis as Record<string, unknown>).__ellamakaDshContainer = fakeContainer({
      execute: async (exec: unknown) => {
        captured = exec
        return { isError: false, content: [{ type: "text", text: "ok" }] }
      },
    })
    const out = await mod.dshAdapter({}, { tools: [{ source: "grep", target: "grep", enable: true }] })
    const tool = (out as { tool: Record<string, unknown> }).tool.grep as Projected
    await tool.execute({}, { sessionID: "ses-abc", directory: "/ellamaka/ws" })
    const exec = captured as {
      agent?: { session?: { header?: { id?: string; cwd?: string } } }
    }
    expect(exec.agent?.session?.header?.id).toBe("ses-abc")
    expect(exec.agent?.session?.header?.cwd).toBe("/ellamaka/ws")
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