import { describe, expect, it, vi } from "vitest"
import { createWopalReplyTool } from "./wopal-task-reply.js"
import type { WopalTask } from "../types.js"

function getExecute(toolDefinition: unknown) {
  return (toolDefinition as { execute: (...args: unknown[]) => Promise<unknown> }).execute
}

function createMockClient() {
  return {
    session: {
      promptAsync: vi.fn().mockResolvedValue(undefined),
      abort: vi.fn().mockResolvedValue(undefined),
    },
    question: {
      reply: vi.fn().mockResolvedValue(undefined),
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
  v2Client?: { question?: { reply?: ReturnType<typeof vi.fn> } },
  serverUrl?: URL,
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
    getV2Client: vi.fn(() => v2Client),
    getServerUrl: vi.fn(() => serverUrl),
    releaseConcurrencySlot: vi.fn(),
    reacquireSlotOnWakeUp: vi.fn(() => true),
  }
}

describe("wopal_task_reply", () => {
  const parentSessionID = "parent-session-123"

  function createWaitingTask(overrides?: Partial<WopalTask>): WopalTask {
    return {
      id: "wopal-task-456",
      sessionID: "child-session-789",
      status: "waiting",
      description: "Test task",
      agent: "fae",
      prompt: "Do something",
      parentSessionID,
      createdAt: new Date(),
      ...overrides,
    }
  }

  it("fails when context session id is missing", async () => {
    const mockManager = createMockTaskManager()
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute({ task_id: "wopal-task-456", message: "test" }, {})

    expect(result).toBe("Error: Current session ID is unavailable; cannot reply to task.")
  })

  it("task_id not found: returns error", async () => {
    const mockManager = createMockTaskManager(undefined)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: "nonexistent", message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("Error: Task not found")
    expect(result).toContain("No active tasks in the current session")
  })

  it("ambiguous reference: returns candidate list without replying", async () => {
    const taskA = createWaitingTask({ id: "wopal-task-dup-aaa", description: "Task A" })
    const taskB = createWaitingTask({ id: "wopal-task-dup-bbb", description: "Task B" })
    const mockClient = createMockClient()
    const mockManager = createMockTaskManager(taskA, mockClient)
    mockManager.tasks.push(taskB)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: "wopal-task-dup", message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("Error: Ambiguous task reference")
    expect(result).toContain("wopal-task-dup-aaa")
    expect(result).toContain("wopal-task-dup-bbb")
    expect(mockClient.session.promptAsync).not.toHaveBeenCalled()
  })

  it("unique prefix reference: replies to the resolved task with canonical ID echo", async () => {
    const mockClient = createMockClient()
    const task = createWaitingTask()
    const mockManager = createMockTaskManager(task, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id.slice(0, 12), message: "continue" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Reply sent to task ${task.id}. The background task will continue execution.`)
    expect(mockClient.session.promptAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { id: task.sessionID },
      }),
    )
  })

  it("task status is stuck (not waiting): reply works and re-acquires slot", async () => {
    const stuckTask = createWaitingTask({ status: "stuck" })
    const mockManager = createMockTaskManager(stuckTask)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const _result = await execute(
      { task_id: stuckTask.id, message: "test" },
      { sessionID: parentSessionID },
    )

    // stuck is resumable, reply works
    expect(mockManager.reacquireSlotOnWakeUp).toHaveBeenCalled()
  })

  it("task status is error: reply is rejected and does not re-acquire slot", async () => {
    const errorTask = createWaitingTask({ status: "error" })
    const mockManager = createMockTaskManager(errorTask)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: errorTask.id, message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("error state")
    expect(result).toContain("cannot be resumed")
    expect(mockManager.reacquireSlotOnWakeUp).not.toHaveBeenCalled()
  })

  

  it("idle task: reply works without interrupt", async () => {
    const mockClient = createMockClient()
    const idleTask = createWaitingTask({ status: "idle" as WopalTask["status"], waitingConcurrencyKey: "default" } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(idleTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    // Without interrupt, reply works (idle task can be resumed without abort)
    const resultWithoutInterrupt = await execute(
      { task_id: idleTask.id, message: "继续完善" },
      { sessionID: parentSessionID },
    )

    expect(resultWithoutInterrupt).toBe(`Reply sent to task ${idleTask.id}. The background task will continue execution.`)
    expect(mockManager.reacquireSlotOnWakeUp).toHaveBeenCalled()
    expect(mockClient.session.promptAsync).toHaveBeenCalled()
    expect(idleTask.status).toBe("running")
    // abort should NOT be called for idle task without interrupt
    expect(mockClient.session.abort).not.toHaveBeenCalled()
  })

  it("idle task with interrupt=true returns error (not running)", async () => {
    const mockClient = createMockClient()
    const idleTask = createWaitingTask({ status: "idle" as WopalTask["status"] } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(idleTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: idleTask.id, message: "test", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("interrupt only works on running tasks")
    expect(result).toContain("Task is idle")
  })

  it("task status is waiting with valid message: calls promptAsync, status becomes running, re-acquires slot", async () => {
    const mockClient = createMockClient()
    const task = createWaitingTask()
    const mockManager = createMockTaskManager(task, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id, message: "Continue with option A" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Reply sent to task ${task.id}. The background task will continue execution.`)
    expect(mockManager.reacquireSlotOnWakeUp).toHaveBeenCalled()
    expect(mockClient.session.promptAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { id: task.sessionID },
      }),
    )
    expect(task.status).toBe("running")
  })

  it("task with pendingQuestionID: calls question.reply to resolve Deferred", async () => {
    const mockClient = createMockClient()
    const mockV2Client = {
      question: {
        reply: vi.fn().mockResolvedValue(undefined),
      },
    }
    const task = createWaitingTask({ pendingQuestionID: "question-req-123" })
    const mockManager = createMockTaskManager(task, mockClient, mockV2Client)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id, message: "ok" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Reply sent to task ${task.id}. The background task will continue execution.`)
    expect(mockV2Client.question.reply).toHaveBeenCalledWith({
      requestID: "question-req-123",
      answers: [["ok"]],
    })
    expect(mockClient.question.reply).not.toHaveBeenCalled()
    expect(mockClient.session.promptAsync).not.toHaveBeenCalled()
    expect(task.status).toBe("running")
    expect(task.pendingQuestionID).toBeUndefined()
  })

  it("task with pendingQuestionID but no v2 client: returns error", async () => {
    const mockClient = createMockClient()
    mockClient.question = {} as never
    const task = createWaitingTask({ pendingQuestionID: "question-req-456" })
    const mockManager = createMockTaskManager(task, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id, message: "ok" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Failed to send reply: question.reply is unavailable")
    expect(task.status).toBe("waiting")
    expect(task.pendingQuestionID).toBe("question-req-456")
  })

  it("task with pendingQuestionID but no SDK or serverUrl: returns error", async () => {
    const mockClient = createMockClient()
    mockClient.question = {} as never
    const task = createWaitingTask({ pendingQuestionID: "question-req-789" })
    const mockManager = createMockTaskManager(task, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id, message: "ok" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Failed to send reply: question.reply is unavailable")
    expect(task.status).toBe("waiting")
    expect(task.pendingQuestionID).toBe("question-req-789")
  })

  it("task without sessionID: returns error", async () => {
    const taskWithoutSession = createWaitingTask({ sessionID: undefined })
    const mockManager = createMockTaskManager(taskWithoutSession)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: taskWithoutSession.id, message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Error: Task has no active session")
  })

  it("promptAsync fails: returns error message, status remains waiting", async () => {
    const mockClient = createMockClient()
    mockClient.session.promptAsync.mockRejectedValueOnce(new Error("Network error"))
    const task = createWaitingTask()
    const mockManager = createMockTaskManager(task, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id, message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Failed to send reply: Network error")
    expect(task.status).toBe("waiting")
  })

  it("promptAsync unavailable: returns error", async () => {
    const mockClient = {
      session: {},
    }
    const task = createWaitingTask()
    const mockManager = createMockTaskManager(task, mockClient as never)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: task.id, message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Error: session.promptAsync is unavailable")
  })

  it("reply does not wake task when concurrency slot is unavailable", async () => {
    const mockClient = createMockClient()
    const waitingTask = createWaitingTask({ waitingConcurrencyKey: "default" })
    const mockManager = createMockTaskManager(waitingTask, mockClient)
    mockManager.reacquireSlotOnWakeUp.mockReturnValueOnce(false)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: waitingTask.id, message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Error: Concurrency limit reached; task remains waiting. Try again after running tasks finish.")
    expect(mockClient.session.promptAsync).not.toHaveBeenCalled()
    expect(waitingTask.status).toBe("waiting")
    expect(waitingTask.waitingConcurrencyKey).toBe("default")
  })

  it("interrupt=true calls abort + promptAsync on running task", async () => {
    const mockClient = createMockClient()
    const runningTask = createWaitingTask({ status: "running" as WopalTask["status"] })
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id, message: "Change direction", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Interrupt sent to task ${runningTask.id}. Previous execution aborted, new message injected. Task will continue with new direction.`)
    expect(mockClient.session.abort).toHaveBeenCalledWith({ path: { id: runningTask.sessionID } })
    expect(mockClient.session.promptAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { id: runningTask.sessionID },
        body: { agent: runningTask.agent, parts: [{ type: "text", text: "Change direction" }] },
      }),
    )
    expect(runningTask.status).toBe("running")
    expect(runningTask.stopNotificationSuppressions?.[0]?.reason).toBe("interrupt")
  })

  it("interrupt=true returns error for non-running task", async () => {
    const waitingTask = createWaitingTask()
    const mockManager = createMockTaskManager(waitingTask)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: waitingTask.id, message: "test", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toContain("interrupt only works on running tasks")
    expect(result).toContain("Task is waiting")
  })

  it("interrupt=true abort fails but still sends message", async () => {
    const mockClient = createMockClient()
    mockClient.session.abort.mockRejectedValueOnce(new Error("Session already idle"))
    const runningTask = createWaitingTask({ status: "running" as WopalTask["status"] })
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id, message: "new direction", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Interrupt sent to task ${runningTask.id}. Previous execution aborted, new message injected. Task will continue with new direction.`)
    expect(mockClient.session.abort).toHaveBeenCalled()
    expect(mockClient.session.promptAsync).toHaveBeenCalled()
  })

  it("interrupt=true does not wake task when concurrency slot is unavailable", async () => {
    const mockClient = createMockClient()
    const runningTask = createWaitingTask({
      status: "running" as WopalTask["status"],
      concurrencyKey: "default",
    })
    const mockManager = createMockTaskManager(runningTask, mockClient)
    mockManager.reacquireSlotOnWakeUp.mockReturnValueOnce(false)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id, message: "new direction", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Error: Concurrency limit reached; task remains idle. Try again after running tasks finish.")
    expect(mockClient.session.abort).toHaveBeenCalled()
    expect(mockClient.session.promptAsync).not.toHaveBeenCalled()
    expect(runningTask.status).toBe("idle")
    expect(runningTask.waitingConcurrencyKey).toBe("default")
  })

it("interrupt=true reacquireSlotOnWakeUp clears waitingConcurrencyKey and acquires concurrency slot", async () => {
    const mockClient = createMockClient()
    const runningTask = createWaitingTask({
      status: "running" as WopalTask["status"],
      concurrencyKey: undefined,
      waitingConcurrencyKey: "default",
    } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id, message: "continue with new direction", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Interrupt sent to task ${runningTask.id}. Previous execution aborted, new message injected. Task will continue with new direction.`)
    
    // Verify abort was called
    expect(mockClient.session.abort).toHaveBeenCalled()
    expect(mockClient.session.promptAsync).toHaveBeenCalled()
    
    // Verify concurrency slot management via reacquireSlotOnWakeUp
    expect(mockManager.reacquireSlotOnWakeUp).toHaveBeenCalledWith(runningTask)
    
    // After successful promptAsync, resetTaskForResume sets status to running
    expect(runningTask.status).toBe("running")
  })

  it("interrupt=true rollback releases slot when promptAsync fails", async () => {
    const mockClient = createMockClient()
    mockClient.session.promptAsync.mockRejectedValueOnce(new Error("Network error"))
    const runningTask = createWaitingTask({
      status: "running" as WopalTask["status"],
      concurrencyKey: undefined,
      waitingConcurrencyKey: "default",
    } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: runningTask.id, message: "continue", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Failed to send interrupt: Network error")
    
    // Verify rollback: reacquireSlotOnWakeUp acquired slot, promptAsync failed, releaseConcurrencySlot called
    expect(mockManager.reacquireSlotOnWakeUp).toHaveBeenCalledWith(runningTask)
    expect(mockManager.releaseConcurrencySlot).toHaveBeenCalledWith(runningTask)
    
    expect(runningTask.status).toBe("idle")
  })

  it("non-interrupt reply rollback releases slot when promptAsync fails", async () => {
    const mockClient = createMockClient()
    mockClient.session.promptAsync.mockRejectedValueOnce(new Error("Network error"))
    const waitingTask = createWaitingTask({
      concurrencyKey: undefined,
      waitingConcurrencyKey: "default",
    } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(waitingTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const result = await execute(
      { task_id: waitingTask.id, message: "test" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe("Failed to send reply: Network error")
    
    // Verify rollback: reacquireSlotOnWakeUp acquired slot, promptAsync failed, releaseConcurrencySlot called
    expect(mockManager.reacquireSlotOnWakeUp).toHaveBeenCalledWith(waitingTask)
    expect(mockManager.releaseConcurrencySlot).toHaveBeenCalledWith(waitingTask)
    
    // Task state should NOT be reset (failed before resetTaskForResume)
    expect(waitingTask.status).toBe("waiting")
  })

  it("reply resets progressNotifyTimeBaseline and lastNotifyTimeQuota for time trigger restart", async () => {
    const mockClient = createMockClient()
    const waitingTask = createWaitingTask({
      // Simulate a task that had old progress state before going idle
      progressNotifyTimeBaseline: new Date(Date.now() - 300_000), // 5 min ago baseline
      lastNotifyTimeQuota: 5, // multiple notifications already sent
    } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(waitingTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const beforeReply = Date.now()
    const result = await execute(
      { task_id: waitingTask.id, message: "continue" },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Reply sent to task ${waitingTask.id}. The background task will continue execution.`)
    
    // Verify progress time baseline reset
    expect(waitingTask.progressNotifyTimeBaseline).toBeDefined()
    const newBaseline = waitingTask.progressNotifyTimeBaseline!.getTime()
    // Baseline should be recent (within 1 second of reply)
    expect(newBaseline).toBeGreaterThanOrEqual(beforeReply - 1000)
    expect(newBaseline).toBeLessThanOrEqual(Date.now() + 1000)
    
    // Time quota reset to 0 (restart 3-minute counter)
    expect(waitingTask.lastNotifyTimeQuota).toBe(0)
    
    // Total runtime (startedAt) is NOT affected — this test doesn't set startedAt
    // but in real tasks, startedAt would remain unchanged
  })

  it("interrupt resets progressNotifyTimeBaseline and lastNotifyTimeQuota", async () => {
    const mockClient = createMockClient()
    const runningTask = createWaitingTask({
      status: "running" as WopalTask["status"],
      progressNotifyTimeBaseline: new Date(Date.now() - 180_000), // 3 min ago
      lastNotifyTimeQuota: 1,
    } as Partial<WopalTask>)
    const mockManager = createMockTaskManager(runningTask, mockClient)
    const execute = getExecute(createWopalReplyTool(mockManager as never))

    const beforeInterrupt = Date.now()
    const result = await execute(
      { task_id: runningTask.id, message: "new direction", interrupt: true },
      { sessionID: parentSessionID },
    )

    expect(result).toBe(`Interrupt sent to task ${runningTask.id}. Previous execution aborted, new message injected. Task will continue with new direction.`)
    
    // Verify progress time baseline reset
    expect(runningTask.progressNotifyTimeBaseline).toBeDefined()
    const newBaseline = runningTask.progressNotifyTimeBaseline!.getTime()
    expect(newBaseline).toBeGreaterThanOrEqual(beforeInterrupt - 1000)
    
    // Time quota reset
    expect(runningTask.lastNotifyTimeQuota).toBe(0)
  })
})
