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
})