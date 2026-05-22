import { describe, it, expect, vi, beforeEach } from "vitest"
import {
  handleMessagePartUpdated,
  consumeContextWarning,
  type MessageTokenHandlerContext,
} from "./message-token-handler.js"
import { SessionStore } from "../../session-store.js"
import type { LoggerInstance } from "../../logger.js"
import type { SimpleTaskManager } from "../../tasks/simple-task-manager.js"

function createMockLogger(): LoggerInstance {
  return {
    trace: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    fatal: vi.fn(),
  }
}

function createMockContext(overrides?: {
  sessionStore?: SessionStore
  taskManager?: Partial<SimpleTaskManager>
  promptAsync?: ReturnType<typeof vi.fn>
}): {
  ctx: MessageTokenHandlerContext
  sessionStore: SessionStore
  promptAsync: ReturnType<typeof vi.fn>
} {
  const sessionStore = overrides?.sessionStore ?? new SessionStore({ max: 100 })
  const promptAsync = overrides?.promptAsync ?? vi.fn().mockResolvedValue(undefined)

  const ctx: MessageTokenHandlerContext = {
    client: {
      session: {
        messages: vi.fn().mockResolvedValue({
          data: [{
            info: {
              role: "assistant",
              providerID: "test-provider",
              modelID: "test-model",
            },
          }],
        }),
        promptAsync,
      },
      config: {
        providers: vi.fn().mockResolvedValue({
          data: {
            providers: [{
              id: "test-provider",
              models: { "test-model": { limit: { context: 100_000 } } },
            }],
          },
        }),
      },
    } as unknown as MessageTokenHandlerContext["client"],
    sessionStore,
    taskManager: overrides?.taskManager as SimpleTaskManager | undefined,
    contextLog: createMockLogger(),
  }

  return { ctx, sessionStore, promptAsync }
}

describe("consumeContextWarning", () => {
  let logger: LoggerInstance

  beforeEach(() => {
    logger = createMockLogger()
  })

  it("sends [CONTEXT HEALTH] reminder when pending warning exists", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()
    // Set pending warning
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 75
    })

    const result = await consumeContextWarning(ctx, "ses_main")

    expect(result).toBe(true)
    expect(promptAsync).toHaveBeenCalledWith({
      path: { id: "ses_main" },
      body: {
        noReply: false,
        parts: [{
          type: "text",
          text: expect.stringContaining("[CONTEXT HEALTH]"),
        }],
      },
    })
    // Verify the message contains the percentage
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.body.parts[0].text).toContain("Context usage: 75%")
    expect(callArgs.body.parts[0].text).toContain('context_manage(action="compact")')

    // Verify committed: sending cleared, count incremented
    const state = sessionStore.get("ses_main")
    expect(state?.contextWarningSending).toBeUndefined()
    expect(state?.pendingContextWarningPct).toBeUndefined()
    expect(state?.contextWarningsSent).toBe(1)
    expect(state?.lastContextWarningAt).toBeDefined()
  })

  it("skips task sessions", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext({
      taskManager: { isTaskSession: vi.fn().mockReturnValue(true) } as unknown as Partial<SimpleTaskManager>,
    })
    sessionStore.upsert("ses_task", (s) => {
      s.pendingContextWarningPct = 80
    })

    const result = await consumeContextWarning(ctx, "ses_task")

    expect(result).toBe(false)
    expect(promptAsync).not.toHaveBeenCalled()
    // Pending should remain untouched
    const state = sessionStore.get("ses_task")
    expect(state?.pendingContextWarningPct).toBe(80)
  })

  it("returns false when no pending warning", async () => {
    const { ctx, promptAsync } = createMockContext()
    // No pending warning set

    const result = await consumeContextWarning(ctx, "ses_main")

    expect(result).toBe(false)
    expect(promptAsync).not.toHaveBeenCalled()
  })

  it("rolls back on promptAsync failure", async () => {
    const promptAsync = vi.fn().mockRejectedValue(new Error("send failed"))
    const { ctx, sessionStore } = createMockContext({ promptAsync })

    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 75
    })

    const result = await consumeContextWarning(ctx, "ses_main")

    expect(result).toBe(false)
    // Verify rolled back: pending restored, sending cleared
    const state = sessionStore.get("ses_main")
    expect(state?.pendingContextWarningPct).toBe(75)
    expect(state?.contextWarningSending).toBeUndefined()
    expect(state?.contextWarningsSent).toBeUndefined()
  })

  it("prevents re-entrant send via beginContextWarningSend atomicity", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 75
    })

    // First call atomically enters sending and clears pending
    const pct = sessionStore.beginContextWarningSend("ses_main")
    expect(pct).toBe(75)

    // Second call returns null (no pending)
    const pct2 = sessionStore.beginContextWarningSend("ses_main")
    expect(pct2).toBeNull()

    // Even if consumeContextWarning is called again, it won't send
    const result = await consumeContextWarning(ctx, "ses_main")
    expect(result).toBe(false)

    // Clean up
    sessionStore.rollbackContextWarningSend("ses_main", pct!)
  })

  it("rolls back when promptAsync is unavailable", async () => {
    const sessionStore = new SessionStore({ max: 100 })
    const ctx: MessageTokenHandlerContext = {
      client: {} as MessageTokenHandlerContext["client"], // no promptAsync
      sessionStore,
      taskManager: undefined,
      contextLog: logger,
    }
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 75
    })

    const result = await consumeContextWarning(ctx, "ses_main")

    expect(result).toBe(false)
    // Pending should be rolled back
    const state = sessionStore.get("ses_main")
    expect(state?.pendingContextWarningPct).toBe(75)
    expect(state?.contextWarningSending).toBeUndefined()
  })
})

describe("handleMessagePartUpdated", () => {
  it("sends warning on step-finish without tokens when pending exists", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 72
    })

    // step-finish WITHOUT tokens
    await handleMessagePartUpdated(ctx, "ses_main", { type: "step-finish" })

    expect(promptAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { id: "ses_main" },
      }),
    )
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.body.parts[0].text).toContain("[CONTEXT HEALTH]")
  })

  it("sends warning AND stores tokens on step-finish with tokens", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 70
      s.agent = "test-agent"
    })

    await handleMessagePartUpdated(ctx, "ses_main", {
      type: "step-finish",
      tokens: { input: 5000, output: 2000, cache: { read: 1000, write: 500 } },
    })

    // Warning should be sent
    expect(promptAsync).toHaveBeenCalled()
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.body.parts[0].text).toContain("[CONTEXT HEALTH]")

    // Tokens should be stored
    const state = sessionStore.get("ses_main")
    expect(state?.lastTokens).toMatchObject({
      input: 5000,
      output: 2000,
      cache: { read: 1000, write: 500 },
    })
    expect(state?.providerID).toBe("test-provider")
    expect(state?.modelID).toBe("test-model")
  })

  it("does not send warning for task sessions", async () => {
    const taskManager = {
      isTaskSession: vi.fn().mockReturnValue(true),
      findBySession: vi.fn().mockReturnValue(undefined),
    } as unknown as Partial<SimpleTaskManager>
    const { ctx, sessionStore, promptAsync } = createMockContext({
      taskManager,
    })
    sessionStore.upsert("ses_task", (s) => {
      s.pendingContextWarningPct = 80
    })

    await handleMessagePartUpdated(ctx, "ses_task", {
      type: "step-finish",
      tokens: { input: 5000, output: 2000 },
    })

    expect(promptAsync).not.toHaveBeenCalled()
    // Pending should remain
    const state = sessionStore.get("ses_task")
    expect(state?.pendingContextWarningPct).toBe(80)
  })

  it("does not send warning when no pending", async () => {
    const { ctx, promptAsync } = createMockContext()
    // No pending warning set

    await handleMessagePartUpdated(ctx, "ses_main", {
      type: "step-finish",
      tokens: { input: 5000, output: 2000 },
    })

    expect(promptAsync).not.toHaveBeenCalled()
  })

  it("rolls back pending on promptAsync failure", async () => {
    const promptAsync = vi.fn().mockRejectedValue(new Error("network error"))
    const { ctx, sessionStore } = createMockContext({ promptAsync })
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 70
    })

    await handleMessagePartUpdated(ctx, "ses_main", { type: "step-finish" })

    const state = sessionStore.get("ses_main")
    expect(state?.pendingContextWarningPct).toBe(70)
    expect(state?.contextWarningSending).toBeUndefined()
  })

  it("does not send old warning after compact cleared state", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 80
    })

    // Simulate compact — clears all warning state
    sessionStore.markCompacting("ses_main", Date.now())

    await handleMessagePartUpdated(ctx, "ses_main", { type: "step-finish" })

    expect(promptAsync).not.toHaveBeenCalled()
    const state = sessionStore.get("ses_main")
    expect(state?.pendingContextWarningPct).toBeUndefined()
  })

  it("no re-entrant send — second step-finish does not duplicate", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()
    sessionStore.upsert("ses_main", (s) => {
      s.pendingContextWarningPct = 70
    })

    // First step-finish sends warning
    await handleMessagePartUpdated(ctx, "ses_main", { type: "step-finish" })
    expect(promptAsync).toHaveBeenCalledTimes(1)

    // Second step-finish has no pending (already consumed)
    await handleMessagePartUpdated(ctx, "ses_main", { type: "step-finish" })
    expect(promptAsync).toHaveBeenCalledTimes(1) // still only 1 call
  })
})
