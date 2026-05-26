import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import {
  extractTitleFromCompaction,
  handleSessionCompacted,
  type IdleCompactHandlerContext,
} from "./idle-compact-handler.js"
import { SessionStore } from "../../session-store.js"
import type { LoggerInstance } from "../../logger.js"
import type { SimpleTaskManager } from "../../tasks/simple-task-manager.js"
import type { WopalTask } from "../../types.js"
import {
  loadSessionContext,
  clearSessionContext,
} from "../../memory/session-context.js"
import { join } from "path"
import { existsSync, mkdirSync, rmSync } from "fs"
import { homedir } from "os"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
  updateSessionTitle?: ReturnType<typeof vi.fn>
}): {
  ctx: IdleCompactHandlerContext
  sessionStore: SessionStore
  promptAsync: ReturnType<typeof vi.fn>
  updateSessionTitle: ReturnType<typeof vi.fn>
} {
  const sessionStore = overrides?.sessionStore ?? new SessionStore({ max: 100 })
  const promptAsync = overrides?.promptAsync ?? vi.fn().mockResolvedValue(undefined)
  const updateSessionTitle = overrides?.updateSessionTitle ?? vi.fn().mockResolvedValue(undefined)

  const ctx: IdleCompactHandlerContext = {
    client: {
      session: {
        promptAsync,
        update: updateSessionTitle,
      },
    } as unknown as IdleCompactHandlerContext["client"],
    sessionStore,
    taskManager: overrides?.taskManager as SimpleTaskManager | undefined,
    contextLogger: createMockLogger(),
    taskLogger: createMockLogger(),
  }

  return { ctx, sessionStore, promptAsync, updateSessionTitle }
}

// ---------------------------------------------------------------------------
// extractTitleFromCompaction — 6 boundary unit tests
// ---------------------------------------------------------------------------

describe("extractTitleFromCompaction", () => {
  it("extracts title from normal ## Goal section", () => {
    const text = "## Goal\nImplement auto-session title feature\n## Instructions\nSome details"
    expect(extractTitleFromCompaction(text)).toBe("Implement auto-session title feature")
  })

  it("extracts title when ## Goal is followed by blank line then content", () => {
    const text = "## Goal\n\nThis is the core intent\n\n## Instructions\nDetails"
    expect(extractTitleFromCompaction(text)).toBe("This is the core intent")
  })

  it("falls back to first valid line when no ## Goal section", () => {
    const text = "## Instructions\nDo something useful\n## Accomplished\nNothing yet"
    expect(extractTitleFromCompaction(text)).toBe("Do something useful")
  })

  it("skips heading lines and --- separators, picks first valid line", () => {
    const text = "## Instructions\n---\n### Sub-heading\nActual content here"
    expect(extractTitleFromCompaction(text)).toBe("Actual content here")
  })

  it("falls back to first 50 characters when all lines are invalid", () => {
    const text = "# Heading Only\n## Another Heading\n---"
    // All lines are headings or separators; fallback to first 50 chars
    expect(extractTitleFromCompaction(text)).toBe("# Heading Only\n## Another Heading\n---".slice(0, 50))
  })

  it("truncates long title to 80 characters", () => {
    const longTitle = "A".repeat(120)
    const text = `## Goal\n${longTitle}`
    const result = extractTitleFromCompaction(text)
    expect(result).toBe(longTitle.slice(0, 80))
    expect(result.length).toBe(80)
  })

  it("returns empty string for empty input", () => {
    expect(extractTitleFromCompaction("")).toBe("")
    expect(extractTitleFromCompaction("   ")).toBe("")
  })
})

// ---------------------------------------------------------------------------
// Consumption chain integration tests
// ---------------------------------------------------------------------------

describe("handleSessionCompacted — consumption chain", () => {
  const testSessionID = "test-compaction-chain-session-id"
  const stateDir = join(homedir(), ".wopal", "memory", "state")

  beforeEach(() => {
    // Clean up any test session context file
    clearSessionContext(testSessionID)
  })

  afterEach(() => {
    clearSessionContext(testSessionID)
  })

  it("consumes compaction summary, extracts title, saves SessionContext, and injects into recovery message", async () => {
    const compactionText = "## Goal\nRefactor compaction handler for auto title\n## Instructions\nSome details"
    const { ctx, sessionStore, promptAsync } = createMockContext()

    // Simulate session.next.compaction.ended → setCompactionSummary
    sessionStore.setCompactionSummary(testSessionID, compactionText)

    // Set up Plugin-initiated compact state
    sessionStore.upsert(testSessionID, (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    // Simulate session.compacted → handleSessionCompacted
    await handleSessionCompacted(ctx, testSessionID)

    // Verify: compaction summary was consumed
    expect(sessionStore.consumeCompactionSummary(testSessionID)).toBeNull()

    // Verify: SessionContext.summary saved
    const savedCtx = loadSessionContext(testSessionID)
    expect(savedCtx).not.toBeNull()
    expect(savedCtx!.summary?.text).toBe("Refactor compaction handler for auto title")

    // Verify: session title update API was called
    expect(ctx.client.session!.update).toHaveBeenCalledWith({
      path: { id: testSessionID },
      body: { title: "Refactor compaction handler for auto title" },
    })

    // Verify: recovery message was sent and contains compaction summary
    expect(promptAsync).toHaveBeenCalled()
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.body.parts[0].text).toContain("## Compaction Summary")
    expect(callArgs.body.parts[0].text).toContain("Refactor compaction handler for auto title")
  })

  it("correctly handles event timing: ended before compacted", async () => {
    const compactionText = "## Goal\nTest timing order"
    const { ctx, sessionStore, promptAsync } = createMockContext()

    // Step 1: session.next.compaction.ended → cache summary
    sessionStore.setCompactionSummary(testSessionID, compactionText)

    // Step 2: session.compacted arrives → consume + handle
    sessionStore.upsert(testSessionID, (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    await handleSessionCompacted(ctx, testSessionID)

    // Summary consumed and used
    expect(sessionStore.consumeCompactionSummary(testSessionID)).toBeNull()
    const savedCtx = loadSessionContext(testSessionID)
    expect(savedCtx?.summary?.text).toBe("Test timing order")
  })

  it("handles compacted event when no compaction summary was cached (no ended event)", async () => {
    const { ctx, sessionStore, promptAsync } = createMockContext()

    // No setCompactionSummary call — simulates missing ended event
    sessionStore.upsert(testSessionID, (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    await handleSessionCompacted(ctx, testSessionID)

    // Recovery message still sent (without compaction summary section)
    expect(promptAsync).toHaveBeenCalled()
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.body.parts[0].text).not.toContain("## Compaction Summary")
  })

  it("passes compactionText to child session notification", async () => {
    const compactionText = "## Goal\nChild task work"
    const task: WopalTask = {
      id: "task-1",
      sessionID: "child-session-id",
      parentSessionID: "parent-session-id",
      status: "running",
      description: "Test task",
      agent: "test-agent",
      prompt: "test",
      createdAt: new Date(),
    }
    const taskManager = {
      isTaskSession: vi.fn().mockReturnValue(true),
      findBySession: vi.fn().mockReturnValue(task),
    } as unknown as Partial<SimpleTaskManager>

    const { ctx, sessionStore, promptAsync } = createMockContext({ taskManager })

    sessionStore.setCompactionSummary("child-session-id", compactionText)
    sessionStore.upsert("child-session-id", (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    await handleSessionCompacted(ctx, "child-session-id")

    expect(promptAsync).toHaveBeenCalled()
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.path.id).toBe("parent-session-id")
    expect(callArgs.body.parts[0].text).toContain("Compaction Summary:")
    expect(callArgs.body.parts[0].text).toContain("Child task work")
  })
})

// ---------------------------------------------------------------------------
// API failure degradation test
// ---------------------------------------------------------------------------

describe("handleSessionCompacted — API failure degradation", () => {
  const testSessionID = "test-api-failure-session-id"

  beforeEach(() => {
    clearSessionContext(testSessionID)
  })

  afterEach(() => {
    clearSessionContext(testSessionID)
  })

  it("continues saving SessionContext and sending recovery when updateSessionTitle rejects", async () => {
    const compactionText = "## Goal\nTest API failure handling"
    const updateSessionTitle = vi.fn().mockRejectedValue(new Error("API timeout"))
    const { ctx, sessionStore, promptAsync } = createMockContext({ updateSessionTitle })

    sessionStore.setCompactionSummary(testSessionID, compactionText)
    sessionStore.upsert(testSessionID, (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    await handleSessionCompacted(ctx, testSessionID)

    // API was attempted
    expect(updateSessionTitle).toHaveBeenCalled()

    // SessionContext.summary is still saved
    const savedCtx = loadSessionContext(testSessionID)
    expect(savedCtx).not.toBeNull()
    expect(savedCtx!.summary?.text).toBe("Test API failure handling")

    // Recovery message was still sent
    expect(promptAsync).toHaveBeenCalled()

    // Debug log was recorded for the API failure
    expect(ctx.contextLogger.debug).toHaveBeenCalledWith(
      expect.objectContaining({
        err: expect.any(Error),
      }),
      "Failed to update session title from compaction summary",
    )
  })

  it("handles missing session.update API gracefully", async () => {
    const compactionText = "## Goal\nNo update API"
    const { ctx, sessionStore, promptAsync } = createMockContext()

    // Remove update method
    delete (ctx.client.session as Record<string, unknown>).update

    sessionStore.setCompactionSummary(testSessionID, compactionText)
    sessionStore.upsert(testSessionID, (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    await handleSessionCompacted(ctx, testSessionID)

    // SessionContext.summary is still saved
    const savedCtx = loadSessionContext(testSessionID)
    expect(savedCtx?.summary?.text).toBe("No update API")

    // Recovery message was still sent
    expect(promptAsync).toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// Negative timing: compacted arrives before ended
// ---------------------------------------------------------------------------

describe("handleSessionCompacted — negative timing (ended arrives after compacted)", () => {
  const testSessionID = "test-negative-timing-session-id"

  beforeEach(() => {
    clearSessionContext(testSessionID)
  })

  afterEach(() => {
    clearSessionContext(testSessionID)
  })

  it("skips summary/title when no cache, then late write leaves cache for next consumption", async () => {
    const compactionText = "## Goal\nLate arriving summary"
    const { ctx, sessionStore, promptAsync, updateSessionTitle } = createMockContext()

    // Step 1: handleSessionCompacted WITHOUT prior setCompactionSummary
    sessionStore.upsert(testSessionID, (s) => {
      s.compactingTrigger = "plugin"
      s.needsAutoContinue = true
    })

    await handleSessionCompacted(ctx, testSessionID)

    // Assert: no summary written to SessionContext
    const savedCtx = loadSessionContext(testSessionID)
    expect(savedCtx).toBeNull()

    // Assert: title update API not called (no title extracted)
    expect(updateSessionTitle).not.toHaveBeenCalled()

    // Assert: recovery message sent but without compaction summary section
    expect(promptAsync).toHaveBeenCalled()
    const callArgs = promptAsync.mock.calls[0][0]
    expect(callArgs.body.parts[0].text).not.toContain("## Compaction Summary")

    // Step 2: Late-arriving ended event writes compaction summary to cache
    sessionStore.setCompactionSummary(testSessionID, compactionText)

    // Assert: cache still exists, pending next consumption
    const state = sessionStore.get(testSessionID)
    expect(state?.compactionSummaryText).toBe(compactionText)
  })
})
