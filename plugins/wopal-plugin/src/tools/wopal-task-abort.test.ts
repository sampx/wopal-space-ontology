import { describe, expect, it, vi } from "vitest"
import { createWopalTaskAbortTool } from "./wopal-task-abort.js"
import type { WopalTask } from "../types.js"

function getExecute(toolDefinition: unknown) {
  return (toolDefinition as { execute: (...args: unknown[]) => Promise<unknown> }).execute
}

function createMockClient() {
  return {
    session: {
      abort: vi.fn().mockResolvedValue(undefined),
    },
  }
}

/**
 * Mock the manager with a resolver-backed in-memory task store so both exact
 * and fuzzy (prefix/suffix) lookups behave like the real SimpleTaskManager.
 */
function createMockTaskManager(
  task?: WopalTask,
  client?: ReturnType<typeof createMockClient>,
) {
  const mockClient = client ?? createMockClient()
  const tasks: WopalTask[] = task ? [task] : []
  return {
    tasks,
    resolveTaskForParent: vi.fn((query: string, parentID: string) => {
      const owned = tasks.filter((t) => t.parentSessionID === parentID)
      const exact = owned.find((t) => t.id === query)
      if (exact) return { type: "exact" as const, task: exact }
      const fuzzy = owned.filter((t) => t.id.startsWith(query))
      if (fuzzy.length === 1) return { type: "unique" as const, task: fuzzy[0], matchedBy: "prefix" as const }
      if (fuzzy.length >= 2) return { type: "ambiguous" as const, query, candidates: fuzzy }
      return { type: "not_found" as const, query, availableTasks: owned }
    }),
    formatResolveErrorMessage: vi.fn((query: string, parentID: string) => {
      const owned = tasks.filter((t) => t.parentSessionID === parentID)
      const fuzzy = owned.filter((t) => t.id.startsWith(query))
      if (fuzzy.length >= 2) {
        return `Ambiguous task reference (ambiguous): "${query}" matches ${fuzzy.length} tasks. Task IDs are ambiguous; use one of the full task IDs:\n${fuzzy.map((t) => `- ${t.id}`).join("\n")}`
      }
      return owned.length > 0
        ? `Task not found: "${query}". Active tasks in the current session:\n${owned.map((t) => `- ${t.id} [${t.status}] ${t.description}`).join("\n")}`
        : `Task not found: "${query}". No active tasks in the current session.`
    }),
    getClient: vi.fn(() => mockClient),
    releaseConcurrencySlot: vi.fn(),
  }
}

describe("wopal_task_abort", () => {
  const parentSessionID = "parent-session-123"

  function createRunningTask(overrides?: Partial<WopalTask>): WopalTask {
    return {
      id: "wopal-task-456",
      sessionID: "child-session-789",
      status: "running",
      description: "Test task",
      agent: "fae",
      prompt: "Do something",
      parentSessionID,
      createdAt: new Date(),
      concurrencyKey: "default",
      ...overrides,
    }
  }

  it("fails when context session id is missing", async () => {
    const mockManager = createMockTaskManager()
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute({ task_id: "wopal-task-456" }, {})

    expect(result).toBe("Failed to abort task: current session ID is unavailable.")
  })

  it("task not found or not owned: returns error", async () => {
    const mockManager = createMockTaskManager(undefined)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: "nonexistent" },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("Failed to abort task: Task not found")
    expect(result).toContain("No active tasks in the current session")
  })

  it("ambiguous reference: returns candidate list without aborting", async () => {
    const taskA = createRunningTask({ id: "wopal-task-dup-aaa", description: "Task A" })
    const taskB = createRunningTask({ id: "wopal-task-dup-bbb", description: "Task B" })
    const mockClient = createMockClient()
    const mockManager = createMockTaskManager(taskA, mockClient)
    mockManager.tasks.push(taskB)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: "wopal-task-dup" },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("Failed to abort task: Ambiguous task reference")
    expect(result).toContain("wopal-task-dup-aaa")
    expect(result).toContain("wopal-task-dup-bbb")
    expect(mockClient.session.abort).not.toHaveBeenCalled()
  })

  it("unique prefix reference: aborts the resolved task", async () => {
    const runningTask = createRunningTask()
    const mockClient = createMockClient()
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id.slice(0, 12) },
      { sessionID: parentSessionID },
    )

    expect(result).toContain(`Task ${runningTask.id} aborted`)
    expect(mockClient.session.abort).toHaveBeenCalledWith({
      path: { id: runningTask.sessionID },
    })
  })

  it("non-running task: returns error with guidance", async () => {
    const waitingTask = createRunningTask({ status: "waiting" })
    const mockManager = createMockTaskManager(waitingTask)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: waitingTask.id },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("Failed to abort task: task is waiting")
    expect(result).toContain("abort only works on running tasks")
    expect(result).toContain("Use wopal_task_finish")
  })

  it("task without sessionID: returns error", async () => {
    const taskWithoutSession = createRunningTask({ sessionID: undefined })
    const mockManager = createMockTaskManager(taskWithoutSession)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: taskWithoutSession.id },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Failed to abort task: task has no active session.")
  })

  it("successfully aborts running task and sets status to idle", async () => {
    const mockClient = createMockClient()
    const runningTask = createRunningTask()
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id },
      { sessionID: parentSessionID },
    )

    expect(result).toContain(`Task ${runningTask.id} aborted`)
    expect(result).toContain("Execution stopped")
    expect(result).toContain("now idle")
    expect(result).toContain("wopal_task_finish")
    expect(result).toContain("wopal_task_reply")
    
    // Verify session.abort was called
    expect(mockClient.session.abort).toHaveBeenCalledWith({
      path: { id: runningTask.sessionID },
    })

    // Verify task state changes - status becomes idle
    expect(runningTask.status).toBe("idle")
    expect(runningTask.waitingConcurrencyKey).toBe("default")
    expect(runningTask.stopNotificationSuppressions?.[0]?.reason).toBe("abort")
    expect(mockManager.releaseConcurrencySlot).toHaveBeenCalledWith(runningTask)
  })

  it("abort handles abort API failure gracefully", async () => {
    const mockClient = createMockClient()
    mockClient.session.abort.mockRejectedValueOnce(new Error("Session already idle"))
    const runningTask = createRunningTask()
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id },
      { sessionID: parentSessionID },
    )

    // Should still succeed even if abort fails
    expect(result).toContain(`Task ${runningTask.id} aborted`)
    expect(runningTask.status).toBe("idle")
  })

  it("abort without concurrencyKey does not set waitingConcurrencyKey", async () => {
    const mockClient = createMockClient()
    const runningTask = createRunningTask({ concurrencyKey: undefined })
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id },
      { sessionID: parentSessionID },
    )

    expect(result).toContain(`Task ${runningTask.id} aborted`)
    expect(runningTask.status).toBe("idle")
    expect(runningTask.waitingConcurrencyKey).toBeUndefined()
    // releaseConcurrencySlot is called even when concurrencyKey is undefined (no-op in implementation)
    expect(mockManager.releaseConcurrencySlot).toHaveBeenCalledWith(runningTask)
  })

  it("stuck task cannot be aborted", async () => {
    const stuckTask = createRunningTask({ status: "stuck" })
    const mockManager = createMockTaskManager(stuckTask)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: stuckTask.id },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("Failed to abort task: task is stuck")
    expect(result).toContain("Use wopal_task_finish")
  })

  it("idle task cannot be aborted again", async () => {
    const idleTask = createRunningTask({ status: "idle" })
    const mockManager = createMockTaskManager(idleTask)
    const execute = getExecute(createWopalTaskAbortTool(mockManager as never))

    const result = await execute(
      { task_id: idleTask.id },
      { sessionID: parentSessionID },
    )

    // idle task should be rejected with guidance to use finish instead
    expect(result).toContain("Failed to abort task: task is idle")
    expect(result).toContain("Use wopal_task_finish")
  })
})
