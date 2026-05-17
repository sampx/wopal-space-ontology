import type { SessionMessage, WopalTask } from "../types.js"
import type { DebugLog } from "../debug.js"
import { formatSessionID } from "../debug.js"

// --- merged from stuck-detector.ts ---

export const DEFAULT_STUCK_TIMEOUT_MS = 120_000 // 2 minutes

export interface StuckCheckConfig {
  stuckTimeoutMs: number
}

export interface StuckResult {
  task: WopalTask
  durationMs: number
}

export function checkStuckTasks(args: {
  tasks: Iterable<WopalTask>
  config: StuckCheckConfig
}): StuckResult[] {
  const { tasks, config } = args
  const now = Date.now()
  const results: StuckResult[] = []

  for (const task of tasks) {
    if (task.status !== "running" && task.status !== "waiting") continue
    if (!task.startedAt || !task.sessionID) continue
    if (task.stuckNotified) continue
    if (task.idleNotified) continue

    const meaningfulActivity = task.progress?.lastMeaningfulActivity ?? task.startedAt
    const elapsed = now - meaningfulActivity.getTime()

    if (elapsed > config.stuckTimeoutMs) {
      results.push({ task, durationMs: elapsed })
    }
  }

  return results
}

export function clearStuckState(tasks: Iterable<WopalTask>): void {
  for (const task of tasks) {
    if (task.status !== "running") continue
    if (!task.stuckNotified || !task.stuckNotifiedAt) continue

    const meaningfulActivity = task.progress?.lastMeaningfulActivity
    if (meaningfulActivity && meaningfulActivity > task.stuckNotifiedAt) {
      task.stuckNotified = false
      delete task.stuckNotifiedAt
    }
  }
}

// --- original task-monitor.ts ---

// Progress notification thresholds
export const PROGRESS_NOTIFY_MESSAGE_MODULO = 20
export const PROGRESS_NOTIFY_TIME_THRESHOLD_MS = 180_000 // 3 minutes
export const CONTEXT_WARN_THRESHOLD = 45
export const CONTEXT_NOTIFY_MODULO = 10
export const CONTEXT_WARN_NOTIFY_MODULO = 5

export interface ProgressTaskInfo {
  taskId: string
  messageCount: number
  wasNotified: boolean
  contextUsage: number | null
}

export interface TaskMonitorDeps {
  tasks: Map<string, WopalTask>
  client: {
    session?: {
      messages?: (args: { path: { id: string } }) => Promise<{
        data?: SessionMessage[]
      }>
      promptAsync?: (args: unknown) => Promise<void>
    }
    config?: {
      providers?: (args: { query: { directory: string } }) => Promise<{
        data?: {
          providers?: Array<{
            id: string
            models?: Record<string, { limit?: { context?: number } }>
          }>
        }
      }>
    }
  }
  debugLog: DebugLog
  directory: string
  notifyParentStuckFn: (task: WopalTask, durationText: string) => Promise<void>
  sendProgressNotificationFn: (task: WopalTask, messageCount: number, contextUsage: number | null) => Promise<void>
}

/**
 * Core context usage calculation — single source of truth for fetching
 * messages, extracting token counts, and computing the usage percentage.
 * Returns rich info (percentage + raw values) or null if unavailable.
 */
export interface ContextUsageInfo {
  pct: number
  used: number
  contextLimit: number
}

export async function fetchContextPercent(
  client: TaskMonitorDeps["client"],
  directory: string,
  sessionID: string,
  debugLog: DebugLog,
): Promise<ContextUsageInfo | null> {
  try {
    if (typeof client.session?.messages !== "function") {
      return null
    }
    const messagesResult = await client.session.messages({
      path: { id: sessionID },
    })
    const messages = messagesResult?.data ?? []
    const lastAssistant = [...messages].reverse().find((m) =>
      m?.info?.role === "assistant" && m?.info?.tokens
    )
    if (!lastAssistant?.info?.tokens) {
      return null
    }

    const tokens = lastAssistant.info.tokens
    const used = (tokens.input ?? 0) + (tokens.cache?.read ?? 0)
    if (used === 0) {
      return null
    }

    if (typeof client.config?.providers !== "function") {
      return null
    }
    const providersResult = await client.config.providers({
      query: { directory },
    })
    const providers = providersResult?.data?.providers ?? []
    const providerID = lastAssistant.info.providerID ?? lastAssistant.info.model?.providerID
    const modelID = lastAssistant.info.modelID ?? lastAssistant.info.model?.modelID
    if (!providerID || !modelID) {
      return null
    }

    const provider = providers.find((p: { id: string }) => p.id === providerID)
    const contextLimit = provider?.models?.[modelID]?.limit?.context
    if (!contextLimit) {
      return null
    }

    const pct = Math.round((used / contextLimit) * 100)
    return { pct, used, contextLimit }
  } catch (err) {
    debugLog(`[ctxUsage] ${formatSessionID(sessionID, true)} error: ${err instanceof Error ? err.message : String(err)}`)
    return null
  }
}

export async function getContextUsagePercent(
  client: TaskMonitorDeps["client"],
  directory: string,
  sessionID: string,
  debugLog: DebugLog,
): Promise<number | null> {
  const info = await fetchContextPercent(client, directory, sessionID, debugLog)
  return info?.pct ?? null
}

export async function checkProgressNotifications(
  deps: TaskMonitorDeps,
): Promise<ProgressTaskInfo[]> {
  const { tasks, client, debugLog, directory, sendProgressNotificationFn } = deps
  const taskInfos: ProgressTaskInfo[] = []
  const runningTasks = Array.from(tasks.values()).filter(t => t.status === 'running' && !t.idleNotified)

  for (const task of runningTasks) {
    if (!task.sessionID) continue

    try {
      const messagesResult = await client.session?.messages?.({
        path: { id: task.sessionID },
      })

      if (!messagesResult?.data) continue

      const messageCount = messagesResult.data.length

      let shouldNotify = messageCount > 0 && messageCount % PROGRESS_NOTIFY_MESSAGE_MODULO === 0

      // Time-based fallback: notify once per time quota slot (3 min each)
      // This ensures stuck tasks (no message/context change) still get periodic notifications
      const now = new Date()
      const elapsedMs = now.getTime() - (task.startedAt?.getTime() ?? 0)
      const timeQuota = Math.floor(elapsedMs / PROGRESS_NOTIFY_TIME_THRESHOLD_MS)
      const lastQuota = task.lastNotifyTimeQuota ?? -1
      if (timeQuota > lastQuota) {
        task.lastNotifyTimeQuota = timeQuota
        shouldNotify = true
      }

      let contextUsage: number | null = null
      try {
        contextUsage = await getContextUsagePercent(client, directory, task.sessionID, debugLog)
      } catch {
        // Graceful degradation
      }

      if (contextUsage !== null) {
        const modulo = contextUsage >= CONTEXT_WARN_THRESHOLD
          ? CONTEXT_WARN_NOTIFY_MODULO
          : CONTEXT_NOTIFY_MODULO
        if (contextUsage > 0 && contextUsage % modulo === 0) {
          shouldNotify = true
        }
      }

      if (shouldNotify) {
        await sendProgressNotificationFn(task, messageCount, contextUsage)
      }

      taskInfos.push({
        taskId: task.id,
        messageCount,
        wasNotified: shouldNotify,
        contextUsage,
      })
    } catch (err) {
      debugLog(`[progressNotify] error for ${task.id}: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  return taskInfos
}

export async function checkStuckTasksAndNotify(
  deps: Pick<TaskMonitorDeps, "tasks" | "debugLog" | "notifyParentStuckFn">,
): Promise<void> {
  const { tasks, debugLog, notifyParentStuckFn } = deps

  const results = checkStuckTasks({
    tasks: tasks.values(),
    config: { stuckTimeoutMs: DEFAULT_STUCK_TIMEOUT_MS },
  })

  for (const { task, durationMs } of results) {
    const durationSeconds = Math.floor(durationMs / 1000)
    const durationMinutes = Math.floor(durationSeconds / 60)
    const durationText = durationMinutes >= 1
      ? `${durationMinutes}min ${durationSeconds % 60}s`
      : `${durationSeconds}s`

    task.stuckNotified = true
    task.stuckNotifiedAt = new Date()

    debugLog(`[stuck] detected: taskId=${task.id} duration=${durationText}`)
    await notifyParentStuckFn(task, durationText)
  }
}

export function logTickStatus(
  tasks: Map<string, WopalTask>,
  progressInfos: ProgressTaskInfo[],
  debugLog: DebugLog,
): void {
  const runningTasks = Array.from(tasks.values())
    .filter(t => t.status === 'running' && !t.idleNotified)

  if (runningTasks.length === 0) return

  const now = Date.now()
  const lines = runningTasks.map((task, i) => {
    const shortId = task.id.replace('wopal-task-', '').slice(0, 8)
    const wasChecked = progressInfos.find(p => p.taskId === task.id)

    const msgsText = wasChecked ? `${wasChecked.messageCount} msgs` : '—'

    const elapsedMs = now - (task.startedAt?.getTime() ?? 0)
    const totalSec = Math.floor(elapsedMs / 1000)
    const min = Math.floor(totalSec / 60)
    const sec = totalSec % 60
    const timeText = `${min}m${sec.toString().padStart(2, '0')}s`

    const ctxPct = wasChecked?.contextUsage
    const ctxText = ctxPct != null
      ? (ctxPct >= CONTEXT_WARN_THRESHOLD ? `, ctx:${ctxPct}% ⚠️` : `, ctx:${ctxPct}%`)
      : ''

    const notifiedMark = wasChecked?.wasNotified ? ' ✓notified' : ''

    return `  [${i + 1}] wopal-task-${shortId} "${task.description}": ${msgsText}, ${timeText}${ctxText}${notifiedMark}`
  })

  debugLog(`[tick] ${runningTasks.length} tasks:\n${lines.join('\n')}`)
}