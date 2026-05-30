# feature-wopal-plugin-add-main-session-health-monitor

## Metadata

- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project-Path**: `.wopal/plugins/wopal-plugin/`
- **Project-Type**: ontology-component
- **Created**: 2026-05-21
- **Status**: done

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

把当前内嵌在 `SimpleTaskManager` 中的 30 秒 tick loop 提炼为通用 `MonitorEngine`，通过可注册的 monitor strategy 同时承载 task session 监控与 main session 监控。

首期目标：

1. `MonitorEngine` 统一负责 tick 调度、防重入、生命周期清理和 strategy 错误隔离
2. 现有 task 监控语义保持不变，只从 `SimpleTaskManager` 内部 tick 中抽出为 `TaskMonitorStrategy`
3. 新增 `MainSessionMonitorStrategy`，在主会话上下文达到阈值时记录待提醒状态，并在下一次 `step-finish` 后注入 `[CONTEXT HEALTH]` 压缩提醒

硬约束：不得改动子任务会话监控通知的现有逻辑，包括触发条件、通知内容、日志打印、阈值、去重字段和执行顺序。

## Technical Context

### Architecture Context

当前 `SimpleTaskManager` 同时负责两类职责：

1. task 管理职责：launch、状态存储、并发控制、reply/abort/finish、session recovery
2. tick 调度职责：在构造函数里创建 30 秒 `setInterval`，依次执行 `checkProgressNotifications()`、`clearStuckState()`、`checkStuckTasksAndNotify()`、`logTickStatus()`

这导致新监控需求自然会被追加进 `SimpleTaskManager`，形成“task manager 上继续叠加主会话监控”的技术债。正确演进方向是把 tick loop 提成通用引擎：

```text
MonitorEngine
  ├─ TaskMonitorStrategy        // 原 task progress/stuck/progress report/stuck alert/tick log 逻辑
  └─ MainSessionMonitorStrategy // 新 main session context health 逻辑
```

`TaskMonitorStrategy` 只包装当前 tick body，不修改以下现有函数的内部逻辑：

- `checkProgressNotifications()`
- `clearStuckState()`
- `checkStuckTasksAndNotify()`
- `logTickStatus()`
- `sendProgressNotification()`
- `notifyParentStuck()`

新增主会话监控不直接发送 prompt，而是沿用两段式模式：

1. monitor tick 只检查上下文占用并记录 pending warning
2. `message.part.updated` 的 `step-finish` 自然边界消费 pending warning
3. 发送前进入 sending 状态，失败回滚，避免 `promptAsync(noReply: false)` 触发二次 `step-finish` 时重复注入

### Code Findings

- `src/tasks/simple-task-manager.ts:72-87` 内嵌当前 tick loop，是需要抽出的调度引擎职责
- `src/tasks/task-monitor.ts` 是 task monitor assembly layer，已把 stuck/progress 核心逻辑拆出，适合被 strategy 复用
- `src/tasks/progress-notify.ts` 保存 task progress/context milestone 触发条件，必须保持语义不变
- `src/tasks/task-notifier.ts` 保存 `[WOPAL TASK PROGRESS]` / `[WOPAL TASK STUCK]` / `[WOPAL TASK IDLE]` 通知内容与 debug 日志，必须保持内容不变
- `src/session-runtime-info.ts` 已提供 `fetchContextPercent()`，可被 `MainSessionMonitorStrategy` 复用
- `src/hooks/events/message-token-handler.ts` 已在 `step-finish + tokens` 时写入 `SessionStore.lastTokens`，但 warning 消费必须提升到 `step-finish` 外层，不得被可选 `tokens` 门控
- `src/tasks/process-cleanup.ts` 实际是通用 cleanup registry，但位于 `tasks/`，MonitorEngine 若直接依赖它会造成新模块反向依赖 task 模块

### Key Decisions

- D-01: 新建通用 `MonitorEngine`，它是唯一拥有 `setInterval`、`tickRunning`、`unref()` 和 monitor lifecycle 的模块
- D-02: `SimpleTaskManager` 不再创建 tick loop；它只保留 task 管理职责，并提供 task monitor strategy 所需依赖
- D-03: 当前 task tick body 原样迁移到 `TaskMonitorStrategy`，执行顺序必须保持：`checkProgressNotifications` → `clearStuckState` → `checkStuckTasksAndNotify` → `logTickStatus`
- D-04: 不修改 task monitor / notifier 的触发条件、通知模板、日志消息、阈值、去重字段；只改变调度归属
- D-05: `MainSessionMonitorStrategy` 只设置 pending warning，不直接调用 `promptAsync`，避免 tick 中打断活跃执行
- D-06: context warning 状态机集中沉淀到 `SessionStore` helper，禁止在多个调用点重复堆 upsert 状态变更逻辑
- D-07: `message-token-handler` 的 `step-finish` 处理拆两层：外层消费 warning，内层 `part.tokens` 只负责 token 写入
- D-08: 把通用 cleanup registry 提到 `src/lifecycle/process-cleanup.ts`，`src/tasks/process-cleanup.ts` 保留 re-export 兼容旧导入
- D-09: strategy 级异常由 engine 隔离并记录 generic monitor 日志，单个 strategy 失败不得阻塞其它 strategy；task strategy 内部日志和通知语义不变
- D-10: 未来新增监控策略只注册 strategy，不再向 `SimpleTaskManager` 堆叠逻辑

### Key Interfaces

```ts
// src/monitor/monitor-engine.ts
export interface MonitorStrategy {
  name: string
  tick(): Promise<void>
}

export class MonitorEngine {
  constructor(args: {
    intervalMs?: number
    strategies: MonitorStrategy[]
    logger: LoggerInstance
  })
  start(): void
  stop(): void
  shutdown(): void
  runOnceForTesting(): Promise<void>
}

// src/tasks/task-monitor-strategy.ts
export function createTaskMonitorStrategy(args: {
  getDeps: () => TaskMonitorRuntimeDeps
}): MonitorStrategy

export async function runTaskMonitorTick(deps: TaskMonitorRuntimeDeps): Promise<void>

// src/monitor/main-session-monitor.ts
export function createMainSessionMonitorStrategy(args: {
  sessionStore: SessionStore
  client: OpenCodeClient
  directory: string
  taskManager?: TaskSessionInspector
  logger: LoggerInstance
}): MonitorStrategy
```

`SessionStore` 新增 context warning helper，统一管理状态机：

- `queueContextWarning(sessionID, pct, nowMs): boolean`
- `beginContextWarningSend(sessionID): number | null`
- `commitContextWarningSend(sessionID, nowMs): void`
- `rollbackContextWarningSend(sessionID, pct): void`
- `clearContextWarningState(sessionID, options?: { resetCount?: boolean }): void`

## In Scope

- 提取通用 MonitorEngine，统一管理 tick loop、防重入、strategy 调度、生命周期清理
- 把现有 task tick body 包装为 TaskMonitorStrategy，保持 task monitor/notifier 语义不变
- 新增 MainSessionMonitorStrategy，基于 `fetchContextPercent()` 记录主会话 context warning pending 状态
- 在 `step-finish` 后消费 pending warning 并注入 `[CONTEXT HEALTH]` system reminder
- 抽出通用 cleanup registry，避免 monitor 模块依赖 tasks 模块
- 补齐 monitor engine、task strategy、main strategy、warning 状态机和事件注入测试
- 更新 `wopal-plugin/AGENTS.md` 的模块结构说明，记录 Monitor 模块边界

## Out of Scope

- 改动 task progress/stuck 触发条件
- 改动 `[WOPAL TASK PROGRESS]` / `[WOPAL TASK STUCK]` / `[WOPAL TASK IDLE]` 通知内容
- 改动 task monitor 日志内容、日志级别或日志触发时机
- 自动直接 compact（本次只提醒，由主 Agent 自主决定）
- 模型/agent 状态变化通知
- 主会话 stuck 检测或定期 heartbeat 报告
- 阈值配置化或多级主会话预警策略
- 子会话 context warning 新策略（本次只确保 task 现有 strategy 可插拔，未来另行添加）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| monitor engine | `src/monitor/monitor-engine.ts`, `src/monitor/monitor-engine.test.ts` | 创建 | 通用 tick 调度、防重入、strategy 编排、生命周期 |
| lifecycle cleanup | `src/lifecycle/process-cleanup.ts`, `src/tasks/process-cleanup.ts` | 创建/修改 | 通用 cleanup registry + task 旧路径 re-export |
| task monitor strategy | `src/tasks/task-monitor-strategy.ts`, `src/tasks/task-monitor-strategy.test.ts` | 创建 | 原 task tick body strategy 化 |
| task manager | `src/tasks/simple-task-manager.ts`, `src/tasks/simple-task-manager.test.ts` | 修改 | 移除内嵌 tick，保留 task 管理 API，提供 strategy 依赖 |
| plugin wiring | `src/index.ts` | 修改 | 创建 MonitorEngine，注册 TaskMonitorStrategy 与 MainSessionMonitorStrategy |
| main monitor strategy | `src/monitor/main-session-monitor.ts`, `src/monitor/main-session-monitor.test.ts` | 创建 | 主会话 context health pending 策略 |
| session state | `src/session-store.ts`, `src/session-store.test.ts` | 修改 | context warning 状态字段与 helper 方法，compact 生命周期清理 |
| delayed injection | `src/hooks/events/message-token-handler.ts`, `src/hooks/events/message-token-handler.test.ts`, `src/hooks/event-router.test.ts` | 修改/创建 | step-finish 后消费 pending warning 并注入提醒 |
| project docs | `.wopal/plugins/wopal-plugin/AGENTS.md` | 修改 | 记录新增 Monitor 模块边界和禁止 task 逻辑堆叠规则 |

## Acceptance Criteria

### Agent Verification

1. [x] `rg -c 'class MonitorEngine' .wopal/plugins/wopal-plugin/src/monitor/monitor-engine.ts` ≥ 1
2. [x] `rg -c 'interface MonitorStrategy' .wopal/plugins/wopal-plugin/src/monitor/monitor-engine.ts` ≥ 1
3. [x] `rg -c 'setInterval' .wopal/plugins/wopal-plugin/src/monitor/monitor-engine.ts` = 1
4. [x] `rg -c 'setInterval' .wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts` = 0
5. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && ! rg "setInterval|setTimeout" src/tasks src/hooks src/index.ts src/monitor/main-session-monitor.ts'` exit 0（除 `MonitorEngine.start()` 外禁止新增独立周期性调度链）
6. [x] `rg -c 'new MonitorEngine' .wopal/plugins/wopal-plugin/src/index.ts` ≥ 1
7. [x] `rg -c 'taskManager\.createMonitorStrategy' .wopal/plugins/wopal-plugin/src/index.ts` ≥ 1
8. [x] `rg -c 'createMainSessionMonitorStrategy' .wopal/plugins/wopal-plugin/src/index.ts` ≥ 1
9. [x] `rg -c 'createTaskMonitorStrategy' .wopal/plugins/wopal-plugin/src/tasks/task-monitor-strategy.ts` ≥ 1
10. [x] `rg -c 'checkProgressNotifications\|clearStuckState\|checkStuckTasksAndNotify\|logTickStatus' .wopal/plugins/wopal-plugin/src/tasks/task-monitor-strategy.ts` ≥ 4
11. [x] `rg -c 'PROGRESS_NOTIFY_TIME_THRESHOLD_MS = 180_000' .wopal/plugins/wopal-plugin/src/tasks/progress-notify.ts` = 1
12. [x] `rg -c 'CONTEXT_WARN_THRESHOLD = 45' .wopal/plugins/wopal-plugin/src/tasks/progress-notify.ts` = 1
13. [x] `rg -c 'DEFAULT_STUCK_TIMEOUT_MS = 120_000' .wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts` = 1
14. [x] `rg -c 'lastNotifyTimeQuota\|lastNotifyContextPct' .wopal/plugins/wopal-plugin/src/tasks/progress-notify.ts` ≥ 4
15. [x] `rg -c '\[WOPAL TASK PROGRESS\]' .wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts` = 1
16. [x] `rg -c '\[WOPAL TASK STUCK\]' .wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts` = 1
17. [x] `rg -c "task\.idleNotified \? 'IDLE'" .wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts` = 1
18. [x] `rg -c '\[progressNotify\]|\[notifyParentStuck\]|\[tick\]|\[stuck\]' .wopal/plugins/wopal-plugin/src/tasks` ≥ 4
19. [x] `rg -c 'queueContextWarning\|beginContextWarningSend\|commitContextWarningSend\|rollbackContextWarningSend' .wopal/plugins/wopal-plugin/src/session-store.ts` ≥ 4
20. [x] `rg -c 'createMainSessionMonitorStrategy' .wopal/plugins/wopal-plugin/src/monitor/main-session-monitor.ts` ≥ 1
21. [x] `rg -c '\[CONTEXT HEALTH\]' .wopal/plugins/wopal-plugin/src/hooks/events/message-token-handler.ts` ≥ 1
22. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/monitor/monitor-engine.test.ts'` 全部 pass
23. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/task-monitor-strategy.test.ts'` 全部 pass
24. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/monitor/main-session-monitor.test.ts'` 全部 pass
25. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/simple-task-manager.test.ts'` 全部 pass
26. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/index.test.ts'` 全部 pass（若无现有 index 测试，则本任务创建）
27. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/hooks/events/message-token-handler.test.ts'` 全部 pass；若修改 `event-router` 路由行为，另需 `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/hooks/event-router.test.ts'` 全部 pass
28. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run typecheck:fix'` exit 0
29. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run typecheck'` exit 0
30. [x] `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run'` 全部 pass

### User Validation

#### Scenario 1: 子任务现有通知语义保持不变
- Goal: 确认抽出 MonitorEngine 后，子任务 progress/stuck/idle 通知的触发与内容不变
- Precondition: 启动一个长时间运行的子任务，并让它达到现有 progress 或 stuck 通知条件
- User Actions:
  1. 启动一个子任务并等待其跨过现有 progress 或 stuck 触发条件
  2. 观察主会话收到的 `[WOPAL TASK PROGRESS]` 或 `[WOPAL TASK STUCK]` 通知
  3. 对照现有通知格式，确认标题、字段、提示语和日志语义没有变化
- Expected Result: task 通知内容和触发条件与当前版本一致；没有出现因主会话监控新增导致的额外 task 通知或漏通知

- [x] 用户已完成上述功能验证并确认结果符合预期

#### Scenario 2: 主会话在自然间隙收到上下文健康预警
- Goal: 确认主会话 context health 策略通过 MonitorEngine 运行，并在自然边界提醒 compact
- Precondition: 主会话上下文已达到 65% 以上，且本轮任务即将结束并产出一次 `step-finish`
- User Actions:
  1. 让主 Agent 完成一段可观察到结束边界的工作
  2. 观察该轮回复结束后，主会话是否收到 `[CONTEXT HEALTH]` system-reminder
  3. 观察提醒内容是否建议使用 `context_manage(action="compact")` 维持会话健康
- Expected Result: 预警出现在 reply 完成后的自然间隙，不打断处理中任务；主 Agent 收到提醒后可自主决定是否 compact

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 提取通用 MonitorEngine 与 lifecycle cleanup

**Verification Intent**: AC#1, AC#2, AC#3, AC#22

**Behavior**: 给定多个 monitor strategy，MonitorEngine 每 30 秒运行一次；同一轮 tick 未结束时跳过下一次 tick；单个 strategy 抛错时只记录 generic monitor 错误并继续执行后续 strategy；`stop()` / `shutdown()` 可清理 interval 且幂等。

**Files**: `.wopal/plugins/wopal-plugin/src/monitor/monitor-engine.ts`, `.wopal/plugins/wopal-plugin/src/monitor/monitor-engine.test.ts`, `.wopal/plugins/wopal-plugin/src/lifecycle/process-cleanup.ts`, `.wopal/plugins/wopal-plugin/src/tasks/process-cleanup.ts`, `.wopal/plugins/wopal-plugin/AGENTS.md`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tasks/process-cleanup.ts`, `.wopal/plugins/wopal-plugin/AGENTS.md`

**Design**:

1. 新建 `src/monitor/monitor-engine.ts`：
   - 定义 `MonitorStrategy { name: string; tick(): Promise<void> }`
   - 定义 `MonitorEngine`，默认 `intervalMs = 30_000`
   - 只允许 engine 内部使用 `setInterval` 和 `tickRunning`
   - `start()` 幂等，重复调用不创建第二个 interval
   - `stop()` / `shutdown()` 幂等，清理 interval
   - `runOnceForTesting()` 直接运行一轮 strategy，供单测验证顺序和异常隔离
   - 每个 strategy 独立 try/catch；strategy 失败日志只记录 strategy name 和 error，不改 strategy 内部日志

2. 抽出通用 cleanup registry：
   - 新建 `src/lifecycle/process-cleanup.ts`，迁移现有 cleanup registry 实现
   - `src/tasks/process-cleanup.ts` 保留 re-export，避免一次性改动所有旧导入
   - MonitorEngine 可以注册到通用 cleanup，不依赖 tasks 模块

3. 更新 `wopal-plugin/AGENTS.md`：
   - 在模块表中新增 Monitor 模块
   - 明确 `SimpleTaskManager` 禁止拥有 tick loop；新增策略必须注册到 MonitorEngine

**TDD**: true

**Changes**:
1. 创建 `monitor-engine.ts` 与 `monitor-engine.test.ts`
2. 抽出 `lifecycle/process-cleanup.ts`，旧 `tasks/process-cleanup.ts` re-export
3. 更新 AGENTS 模块边界说明

**Verify**:
`bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/monitor/monitor-engine.test.ts'` 全部 pass

**Done**:
任务产出：通用 monitor engine 与通用 cleanup lifecycle 落地，具备可复用 strategy 调度能力
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 将现有 task tick body 迁移为 TaskMonitorStrategy

**Verification Intent**: AC#4, AC#5, AC#6, AC#7, AC#9-AC#18, AC#23, AC#25

**Behavior**: MonitorEngine 调度 `TaskMonitorStrategy` 后，task progress/stuck/tick log 行为与迁移前等价；`SimpleTaskManager` 不再直接创建 interval，但 task launch/reply/abort/finish/recover 等管理 API 不变。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-monitor-strategy.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-monitor-strategy.test.ts`, `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.test.ts`, `.wopal/plugins/wopal-plugin/src/index.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/plugins/wopal-plugin/src/tasks/progress-notify.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts`, `.wopal/plugins/wopal-plugin/src/index.ts`

**Design**:

1. 新建 `src/tasks/task-monitor-strategy.ts`：
   - `runTaskMonitorTick(deps)` 原样执行当前 tick body：
     1. `const taskInfos = await checkProgressNotifications(deps)`
     2. `clearStuckState(deps.tasks.values())`
     3. `await checkStuckTasksAndNotify(deps)`
     4. `logTickStatus(deps.tasks, taskInfos, deps.debugLog)`
   - `createTaskMonitorStrategy({ getDeps })` 返回 `MonitorStrategy`
   - 不复制 progress/stuck/notification 逻辑，只调用现有公共函数

2. 修改 `SimpleTaskManager`：
   - 删除 `tickerInterval`、`tickRunning` 字段和 constructor 内 `setInterval`
   - 保留 `dispose()` / `shutdown()` API，`dispose()` 不再管理 monitor interval
   - 新增 `createMonitorStrategy()` 或等价 public method，内部闭包调用现有 `getMonitorDeps()`，避免暴露 private tasks map
   - 保持 `getMonitorDeps()` 中 `notifyParentStuckFn` / `sendProgressNotificationFn` 的包装逻辑不变

3. 修改 `index.ts`：
   - 创建 `SimpleTaskManager`
   - 创建 `MonitorEngine`，先只注册 `taskManager.createMonitorStrategy()`
   - `monitorEngine.start()` 在 hooks/tools 返回前执行
   - 使用通用 cleanup 确保进程退出时 monitor stop

4. 测试要求：
   - `task-monitor-strategy.test.ts` 显式断言 tick 顺序仍是 `checkProgressNotifications -> clearStuckState -> checkStuckTasksAndNotify -> logTickStatus`
   - `task-monitor-strategy.test.ts` 断言 `progressInfos` 原样传入 `logTickStatus`
   - `task-monitor-strategy.test.ts` 断言 `notifyParentStuckFn` / `sendProgressNotificationFn` 仍由 `SimpleTaskManager.getMonitorDeps()` 等价包装，不改变 parent session 发送路径
   - `task-monitor-strategy.test.ts` 或 `task-monitor.test.ts` 保留/新增常量守卫：`180_000`、`45`、`120_000`
   - `task-notifier` 模板、`[progressNotify]` / `[notifyParentStuck]` / `[tick]` / `[stuck]` 日志语义由 AC#15-AC#18 守卫，禁止在本任务改动
   - `simple-task-manager.test.ts` 更新 dispose 测试：不再期望 manager 清理 ticker，而是验证 task 管理 API 不回归

**TDD**: true

**Changes**:
1. 创建 `task-monitor-strategy.ts` 与测试
2. 从 `SimpleTaskManager` 中移除内嵌 tick loop，新增 strategy factory
3. 在 `index.ts` 接入 MonitorEngine + TaskMonitorStrategy
4. 更新相关单测，证明 task 管理 API 与 task monitor 语义不回归

**Verify**:
`bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/task-monitor-strategy.test.ts src/tasks/simple-task-manager.test.ts'` 全部 pass

**Done**:
任务产出：task 监控从 manager 内部 tick 解耦为可插拔 strategy，现有 task 通知语义保持不变
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 新增 MainSessionMonitorStrategy 与 context warning 状态机

**Verification Intent**: AC#19, AC#20, AC#24

**Behavior**: MainSessionMonitorStrategy 扫描 `SessionStore.ids()` 中的非 task session；当 `fetchContextPercent()` 返回 `pct >= 65` 且未处于 compact、cooldown、sending、pending、次数上限时，写入 pending warning。策略不调用 `promptAsync`。

**Files**: `.wopal/plugins/wopal-plugin/src/monitor/main-session-monitor.ts`, `.wopal/plugins/wopal-plugin/src/monitor/main-session-monitor.test.ts`, `.wopal/plugins/wopal-plugin/src/session-store.ts`, `.wopal/plugins/wopal-plugin/src/session-store.test.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/session-store.ts`, `.wopal/plugins/wopal-plugin/src/session-runtime-info.ts`, `.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`

**Design**:

1. `SessionState` 新增字段：
   - `pendingContextWarningPct?: number`
   - `contextWarningSending?: boolean`
   - `lastContextWarningAt?: number`
   - `contextWarningsSent?: number`

2. `SessionStore` 新增 helper，集中管理 warning 状态机：
   - `queueContextWarning(sessionID, pct, nowMs)`：检查 pending/sending/cooldown/max count 后写入 pending
   - `beginContextWarningSend(sessionID)`：发送前原子进入 sending 并清空 pending，返回 pct
   - `commitContextWarningSend(sessionID, nowMs)`：成功后清 sending、更新时间、递增次数
   - `rollbackContextWarningSend(sessionID, pct)`：失败后清 sending、恢复 pending
   - `clearContextWarningState(sessionID, { resetCount })`：compact 或显式清理使用

3. Compact 生命周期：
   - `markCompacting()` 调用 `clearContextWarningState(sessionID, { resetCount: true })`
   - compact 后上下文已重置，旧 pending 和发送计数均无意义

4. `createMainSessionMonitorStrategy()`：
   - 遍历 `sessionStore.ids()`
   - 每个 session 独立 `try/catch`；单个 session 检查失败只记录 debug 并 `continue`，不得提前终止整轮 main strategy
   - 跳过 `taskManager?.isTaskSession(sessionID) === true`
   - 跳过 `state.isCompacting`
   - 调用 `fetchContextPercent()` 获取上下文百分比
   - `pct >= 65` 时调用 `sessionStore.queueContextWarning()`
   - 只记 contextLogger debug，不发送 prompt

5. 测试覆盖：
   - 达阈值设置 pending
   - 低于阈值跳过
   - task session 跳过
   - compacting 跳过
   - cooldown 未过跳过
   - 已达提醒次数上限跳过
   - pending / sending 状态不覆盖
   - 单个 session 的 `fetchContextPercent()` 或 queue 操作抛错时，仅记录 debug 并继续扫描后续 session
   - compact 后清理 pending/sending/count

**TDD**: true

**Changes**:
1. 添加 context warning 状态字段和 SessionStore helper
2. 创建 `main-session-monitor.ts` 与测试
3. 更新 `session-store.test.ts` 覆盖状态机和 compact 清理

**Verify**:
`bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/monitor/main-session-monitor.test.ts src/session-store.test.ts'` 全部 pass

**Done**:
任务产出：主会话 context health monitor strategy 与去重/节流/发送中状态机落地
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: 注册 MainSessionMonitorStrategy 并在 step-finish 后注入提醒

**Verification Intent**: AC#6, AC#7, AC#8, AC#21, AC#26, AC#27, AC#28, AC#29, AC#30

**Behavior**: MonitorEngine 同时调度 TaskMonitorStrategy 与 MainSessionMonitorStrategy。主会话触发 pending warning 后，下一次 `step-finish` 即使没有 tokens 也会发送一次 `[CONTEXT HEALTH]` reminder；发送成功提交状态，发送失败回滚 pending；task session 的现有事件处理和通知不变。

**Files**: `.wopal/plugins/wopal-plugin/src/index.ts`, `.wopal/plugins/wopal-plugin/src/index.test.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/message-token-handler.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/message-token-handler.test.ts`, `.wopal/plugins/wopal-plugin/src/hooks/event-router.test.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/index.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/message-token-handler.ts`, `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`

**Design**:

1. `index.ts` 创建唯一的 `MonitorEngine` 实例，并注册两个 strategy：
   - `taskManager.createMonitorStrategy()`
   - `createMainSessionMonitorStrategy({ sessionStore, client, directory, taskManager, logger: contextLogger })`

   禁止在 `index.ts`、`tasks/`、`hooks/` 或 main strategy 中另起 `setInterval` / 递归 `setTimeout` / 其他独立周期性调度链；所有周期性调度都必须经过同一个 engine。

2. `handleMessagePartUpdated()` 拆成两层：
   - 外层 `sessionID && part?.type === "step-finish"`：消费 main session context warning
   - 内层 `part.tokens`：保留现有 token/provider/model/contextLimit 写入逻辑

3. Warning 消费流程：
   - 如果 `taskManager?.isTaskSession(sessionID)` 为 true，跳过 context health reminder（不影响 task session）
   - 调用 `sessionStore.beginContextWarningSend(sessionID)`，返回 pct 时才发送
   - 发送文本：

     ```text
     <system-reminder>
     [CONTEXT HEALTH]
     Context usage: {pct}%. Consider compacting with context_manage(action="compact") to maintain session health.
     </system-reminder>
     ```

   - 成功：`commitContextWarningSend(sessionID, Date.now())`
   - 失败：`rollbackContextWarningSend(sessionID, pct)`

4. 防重入要求：发送前必须先进入 sending 并清空 pending，避免 `promptAsync(noReply: false)` 引发的二次 `step-finish` 重复发送。

5. 测试覆盖：
   - `index.test.ts` 验证 plugin wiring 只创建一个 `MonitorEngine`，并向同一个 engine 注册 task/main 两个 strategy
   - `index.test.ts` 验证同一轮 tick 同时调度 task strategy 与 main strategy，禁止另起 main-session 专用 timer 或递归 timeout 调度链
   - `step-finish` 无 tokens 但 pending 存在 → 仍发送提醒
   - `step-finish + tokens` → token 写入和 warning 发送均成立
   - task session → 不发送 `[CONTEXT HEALTH]`
   - 无 pending → 不发送
   - `promptAsync` 失败 → pending 回滚
   - re-entrant `step-finish` → 不重复发送
   - pending warning 后先 compact，再触发后续 `step-finish` → 不发送旧 `[CONTEXT HEALTH]`

**TDD**: true

**Changes**:
1. `index.ts` 创建唯一 MonitorEngine，并注册 TaskMonitorStrategy 与 MainSessionMonitorStrategy
2. `message-token-handler.ts` 拆分 step-finish 外层 warning 消费与内层 token 写入
3. 创建 `index.test.ts`，覆盖单一 engine 与双 strategy 接线
4. 创建或补充 `message-token-handler.test.ts`，直接覆盖成功、失败、无 tokens、防重入、task 跳过与 compact 后旧 warning 不残留
5. 运行项目级验证链

**Verify**:
`bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/index.test.ts src/hooks/events/message-token-handler.test.ts'` 全部 pass；若修改 `event-router` 路由行为，另需 `bash -lc 'cd .wopal/plugins/wopal-plugin && bun run test:run src/hooks/event-router.test.ts'` 全部 pass

**Done**:
任务产出：MonitorEngine 同时支持 task strategy 与 main session strategy，主会话自然边界 context health reminder 可用
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 先建立通用 monitor engine 与 cleanup 基础设施，避免后续继续堆在 task manager 上 |
| 2 | Task 2 | fae | Task 1 | 把现有 task tick body strategy 化，消除当前技术债并验证 task 语义不变 |
| 2 | Task 3 | fae | Task 1 | 主会话 monitor strategy 与状态机独立于 task strategy，可并行开发 |
| 3 | Task 4 | fae | Task 2, Task 3 | 最后注册 main strategy 并接入 step-finish 注入，避免与 Task 2 同时修改 `index.ts` 冲突 |

每次委派 fae 时，prompt 末尾必须附加：

完成后在 Plan 文件中编辑对应 Task 的 Done checkbox（- [ ] → - [x]），Plan 文件路径：/Users/sam/coding/wopal/wopal-workspace/docs/products/wopal-space-ontology/plans/feature-wopal-plugin-add-main-session-health-monitor.md
禁止修改 Plan Status
