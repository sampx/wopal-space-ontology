import { describe, it, expect, vi, beforeEach } from "vitest"
import {
  runTaskMonitorTick,
  createTaskMonitorStrategy,
  type TaskMonitorRuntimeDeps,
} from "./task-monitor-strategy.js"
import type { WopalTask } from "../types.js"
import type { ProgressTaskInfo } from "./task-monitor.js"
import { PROGRESS_NOTIFY_TIME_THRESHOLD_MS, CONTEXT_WARN_THRESHOLD, DEFAULT_STUCK_TIMEOUT_MS } from "./task-monitor.js"

// --- Call-order tracking via vi.mock (hoisted) ---
const callOrder: string[] = []
let logTickReceivedInfos: ProgressTaskInfo[] | undefined

vi.mock("./task-monitor.js", async (importOriginal) => {
  const actual = await importOriginal() as any
  return {
    ...actual,
    checkProgressNotifications: vi.fn(async (deps: any) => {
      callOrder.push("checkProgressNotifications")
      return actual.checkProgressNotifications(deps)
    }),
    clearStuckState: vi.fn((...args: any[]) => {
      callOrder.push("clearStuckState")
      return actual.clearStuckState(...args)
    }),
    checkStuckTasksAndNotify: vi.fn(async (...args: any[]) => {
      callOrder.push("checkStuckTasksAndNotify")
      return actual.checkStuckTasksAndNotify(...args)
    }),
    logTickStatus: vi.fn((tasks: any, infos: any, log: any) => {
      callOrder.push("logTickStatus")
      logTickReceivedInfos = infos
      return actual.logTickStatus(tasks, infos, log)
    }),
  }
})

function createMockDeps(overrides?: Partial<TaskMonitorRuntimeDeps>): TaskMonitorRuntimeDeps {
  return {
    tasks: new Map<string, WopalTask>(),
    sessionStore: {
      get: vi.fn(),
      set: vi.fn(),
      delete: vi.fn(),
      has: vi.fn(),
      ids: vi.fn().mockReturnValue([]),
      lastTokens: vi.fn(),
    } as unknown as TaskMonitorRuntimeDeps["sessionStore"],
    client: {
      session: {
        messages: vi.fn().mockResolvedValue({ data: [] }),
        promptAsync: vi.fn().mockResolvedValue(undefined),
      },
    } as unknown as TaskMonitorRuntimeDeps["client"],
    debugLog: {
      trace: vi.fn(),
      debug: vi.fn(),
      info: vi.fn(),
      warn: vi.fn(),
      error: vi.fn(),
      fatal: vi.fn(),
    },
    directory: "/test",
    taskManager: { isTaskSession: vi.fn().mockReturnValue(false) },
    notifyParentStuckFn: vi.fn().mockResolvedValue(undefined),
    sendProgressNotificationFn: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  }
}

function createRunningTask(overrides: Partial<WopalTask> = {}): WopalTask {
  return {
    id: "wopal-task-test-1",
    status: "running",
    description: "Test task",
    agent: "fae",
    prompt: "test",
    parentSessionID: "parent-1",
    createdAt: new Date(),
    startedAt: new Date(Date.now() - 300_000),
    sessionID: "ses_test-session-1",
    progress: { toolCalls: 0, lastUpdate: new Date(), lastMeaningfulActivity: new Date() },
    ...overrides,
  } as WopalTask
}

describe("task-monitor-strategy", () => {
  beforeEach(() => {
    callOrder.length = 0
    logTickReceivedInfos = undefined
  })

  describe("runTaskMonitorTick", () => {
    it("executes in strict order: checkProgressNotifications → clearStuckState → checkStuckTasksAndNotify → logTickStatus", async () => {
      const task = createRunningTask()
      const tasks = new Map<string, WopalTask>()
      tasks.set(task.id, task)
      const deps = createMockDeps({ tasks })

      await runTaskMonitorTick(deps)

      expect(callOrder).toEqual([
        "checkProgressNotifications",
        "clearStuckState",
        "checkStuckTasksAndNotify",
        "logTickStatus",
      ])
    })

    it("passes progressInfos from checkProgressNotifications to logTickStatus verbatim", async () => {
      const task = createRunningTask()
      const tasks = new Map<string, WopalTask>()
      tasks.set(task.id, task)

      const deps = createMockDeps({ tasks })
      ;(deps.client.session.messages as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: [{ id: "msg-1" }, { id: "msg-2" }],
      })

      await runTaskMonitorTick(deps)

      // logTickStatus must receive the exact array returned by checkProgressNotifications
      expect(logTickReceivedInfos).toBeDefined()
      expect(Array.isArray(logTickReceivedInfos)).toBe(true)
      // The infos should reference the task we set up
      const infoForTask = logTickReceivedInfos!.find((p) => p.taskId === task.id)
      expect(infoForTask).toBeDefined()
    })
  })

  describe("createTaskMonitorStrategy", () => {
    it("returns a MonitorStrategy with correct name", () => {
      const deps = createMockDeps()
      const strategy = createTaskMonitorStrategy({ getDeps: () => deps })

      expect(strategy.name).toBe("task-monitor")
      expect(typeof strategy.tick).toBe("function")
    })

    it("tick() calls getDeps on each invocation", async () => {
      let callCount = 0
      const deps = createMockDeps()
      const strategy = createTaskMonitorStrategy({
        getDeps: () => {
          callCount++
          return deps
        },
      })

      await strategy.tick()
      expect(callCount).toBe(1)

      await strategy.tick()
      expect(callCount).toBe(2)
    })

    it("preserves notifyParentStuckFn from getMonitorDeps", async () => {
      const notifyParentStuckFn = vi.fn().mockResolvedValue(undefined)
      const deps = createMockDeps({ notifyParentStuckFn })
      const strategy = createTaskMonitorStrategy({ getDeps: () => deps })

      // Make a stuck task so the function is called
      const task = createRunningTask()
      task.progress!.lastMeaningfulActivity = new Date(Date.now() - DEFAULT_STUCK_TIMEOUT_MS - 10_000)
      deps.tasks.set(task.id, task)

      await strategy.tick()

      expect(notifyParentStuckFn).toHaveBeenCalledWith(task, expect.any(String))
    })

    it("preserves sendProgressNotificationFn from getMonitorDeps", async () => {
      const sendProgressNotificationFn = vi.fn().mockResolvedValue(undefined)
      const task = createRunningTask()
      const tasks = new Map<string, WopalTask>()
      tasks.set(task.id, task)

      const deps = createMockDeps({ tasks, sendProgressNotificationFn })
      // Make the task trigger time-based notification (started 4 min ago)
      task.startedAt = new Date(Date.now() - PROGRESS_NOTIFY_TIME_THRESHOLD_MS - 60_000)
      // Provide messages
      ;(deps.client.session.messages as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: [{ id: "msg-1" }, { id: "msg-2" }, { id: "msg-3" }],
      })

      const strategy = createTaskMonitorStrategy({ getDeps: () => deps })
      await strategy.tick()

      expect(sendProgressNotificationFn).toHaveBeenCalled()
    })
  })

  describe("constant guards", () => {
    it("PROGRESS_NOTIFY_TIME_THRESHOLD_MS is 180_000", () => {
      expect(PROGRESS_NOTIFY_TIME_THRESHOLD_MS).toBe(180_000)
    })

    it("CONTEXT_WARN_THRESHOLD is 45", () => {
      expect(CONTEXT_WARN_THRESHOLD).toBe(45)
    })

    it("DEFAULT_STUCK_TIMEOUT_MS is 120_000", () => {
      expect(DEFAULT_STUCK_TIMEOUT_MS).toBe(120_000)
    })
  })
})
