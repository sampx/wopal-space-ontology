# 149-refactor-wopal-plugin-simplify-sessionstore-to-single-main-session

## Metadata

- **Issue**: #149
- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-20
- **Status**: done
- **Worktree**: issue-149-plugin-simplify-sessionstore-to-single-main-session | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-issue-149-plugin-simplify-sessionstore-to-single-main-session

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 SessionStore 从 `Map<sessionID, SessionState>` 多 session 混存重构为单例 MainSessionState（存 main 状态） + WopalTask 扩展字段定义（本次仅定义类型接口，数据填充为 P2），消除 `isTask` 标记不一致和日志级别混乱。

## Technical Context

### Architecture Context

**当前架构问题**：

插件进程内只有一个 main session + 多个 task session（通过 wopal_task 创建）。当前 SessionStore 设计为 `Map<sessionID, SessionState>`，混存不同类型 session 的状态，导致三个问题：

1. **类型属性当状态存储**：`SessionState.isTask` 记录 session 类型（main/task），但类型是创建时确定的不可变属性，不应存在运行时状态容器中。多个事件源（message-hooks:60、message-token-handler:122）每次都重新计算 `isTask = !!taskManager.findBySession()`，而 `findBySession` 可能因 task 已结束返回 undefined → 同一 sessionID 在不同时刻被标记为不同角色（日志中出现 `ses_xxx(task)` → `ses_xxx(main)` 的混乱）。

2. **字段职责不分**：SessionState 混存 main 专用字段（isCompacting、needsSkillReload、seededFromHistory 等压缩/注入状态）和通用字段（agent、lastTokens、providerID），task session 也存在 SessionStore 中但实际这些字段对 task 无意义。

3. **日志级别混乱**：`session-runtime-info.ts` 中大量诊断信息（providersConfig fetched、tokens stale、fallback path）使用 debug 级别打印，每当 WOPAL_PLUGIN_DEBUG=task 时每 30s tick 都输出，污染日志。

**目标架构**：

```
MainSessionState (单例，非 Map)
  ├─ 压缩状态: isCompacting, needsAutoContinue, needsSkillReload, loadedSkills
  ├─ 注入状态: needsMemoryInjection, lastUserPrompt, lastRulesPrompt, injectedRawText
  ├─ 消息状态: seededFromHistory, recentMessages
  └─ 模型信息: agent, lastTokens, providerID, modelID, contextLimit

WopalTask（扩展字段）
  ├─ 原有字段
  └─ 新增: agent, lastTokens, providerID, modelID, contextLimit

SimpleTaskManager
  ├─ taskSessions: Set<sessionID> （session 类型注册表）
  └─ isTaskSession(sessionID): boolean （权威 isTask 来源）
```

**涉及模块**：

| 模块 | 影响 |
|------|------|
| session-store.ts | **删除** isTask 字段，接口不变（保持兼容） |
| simple-task-manager.ts | 新增 `isTaskSession()` + taskSessions 注册表 |
| task-launcher.ts | task 创建时注册 session 到 taskSessions |
| event-router.ts | 首次收到 event 时注册 main session |
| message-hooks.ts | 移除 `state.isTask = isTask` 设置 |
| message-token-handler.ts | 同上，移除 isTask 设置 |
| session-runtime-info.ts | 诊断日志降级为 trace |
| types.ts | WopalTask 新增 agent/lastTokens/providerID/modelID/contextLimit |

### Research Findings

**日志分析**（用户提供）：

```
2026-05-20 09:42:42 [context] [tokens] ses_1bcf8eb17ffe(task) agent=fae ...
2026-05-20 09:42:52 [task] [ctxFromStore] ses_1bcf8eb17ffe(main) 57238/202752 = 28%
2026-05-20 09:42:52 [task] [ctxUsage] ses_1bcf8eb17ffe(main) from store: 28%
```

同一 sessionID `ses_1bcf8eb17ffe` 在 `[tokens]` 中标记 `(task)`，在 `[ctxFromStore]` 和 `[ctxUsage]` 中标记 `(main)`。根源：`[tokens]` 路径通过 `message-token-handler.ts:79` 调用 `taskManager.findBySession()` 判断；`[ctxFromStore]` 路径通过 `session-runtime-info.ts:171` 读取 `sessionStore.get(sessionID)?.isTask`。两种判断源不一致。

**诊断日志冗余**（用户提供，每 30s tick 中）：

```
[task] [providersConfig] fetched 8 providers           ← trace-level: API call detail
[task] [ctxFromStore] ses_xxx tokens stale (65s ago)    ← trace-level: stale check
[task] [ctxUsage] ses_xxx fetched 43 messages (fallback) ← trace-level: fallback path
[task] [tick] 1 tasks: ...                              ← trace-level: periodic status
```

**参考资料**：
- `.wopal/wopal-plugin/src/session-store.ts` — 当前 SessionStore 实现
- `.wopal/wopal-plugin/src/session-runtime-info.ts` — 日志问题载体
- `.wopal/wopal-plugin/src/hooks/events/message-token-handler.ts` — isTask 设置点 1
- `.wopal/wopal-plugin/src/hooks/message-hooks.ts` — isTask 设置点 2
- `.wopal/wopal-plugin/src/hooks/event-router.ts` — 首次 event 处理
- `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts` — TaskManager 主类
- `.wopal/wopal-plugin/src/tasks/task-launcher.ts` — task 创建流程
- `.wopal/wopal-plugin/src/tasks/progress-notify.ts` — 进度通知（调用 fetchContextPercent）
- `.wopal/wopal-plugin/src/tasks/task-monitor.ts` — logTickStatus
- `.wopal/wopal-plugin/src/debug.ts` — createTraceLog 已存在

### Key Decisions

- **D-01**: 保留 SessionStore 的 Map 接口（`get(sessionID)`, `upsert(sessionID, mutator)`）不变，仅在内部按 session 类型路由。理由：避免修改 25+ 处调用点，降低回归风险。路由规则：`sessionID === mainSessionID` → 返回 MainSessionState；否则 → 返回 undefined（task session 不由 SessionStore 管理）。
- **D-02**: isTask 判断源改为 `taskManager.isTaskSession(sessionID)`，不再从 SessionState 读取。理由：session 类型是不可变属性，由 session 创建事件确定（task session 有 parentID），taskManager 作为 session 生命周期管理器是权威来源。
- **D-03**: WopalTask 新增 agent/lastTokens/providerID/modelID/contextLimit 字段，替代 SessionStore 中存储的 task session 状态。理由：这些字段对 task 的 progress notification 有用（计算 context usage、显示 model 信息），应由 TaskManager 管理。
- **D-04**: 诊断日志改用 `createTraceLog`（需要 `WOPAL_PLUGIN_TRACE=task` 才输出）。涉及：providersConfig fetched、ctxFromStore stale/fallback、tick 状态列表。理由：这些是高频诊断信息，污染正常 debug 日志。debug 级别只保留关键结果（如 context usage percentage、stuck detection）。
- **D-05**: task-launcher 中 session 创建成功后立即 `taskManager.registerTaskSession(sessionID)`，其他事件源不再设置/覆盖 isTask。理由：避免竞态和不一致的重新计算。

### Key Interfaces

```typescript
// types.ts — WopalTask 扩展
export interface WopalTask {
  // ... 原有字段
  agent?: string
  lastTokens?: {
    input: number; output: number;
    reasoning?: number;
    cache?: { read?: number; write?: number };
    updatedAt: number;
  }
  providerID?: string
  modelID?: string
  contextLimit?: number
}

// simple-task-manager.ts — 新增方法
export class SimpleTaskManager {
  private taskSessions = new Set<string>()

  registerTaskSession(sessionID: string): void {
    this.taskSessions.add(sessionID)
  }

  isTaskSession(sessionID: string): boolean {
    return this.taskSessions.has(sessionID)
  }
}

// session-store.ts — 移除 isTask 字段
export interface SessionState {
  // ❌ 删除: isTask?: boolean
  // ... 其余字段不变
}
```

## In Scope

- 从 SessionState 删除 `isTask?: boolean` 字段
- SimpleTaskManager 新增 `isTaskSession(sessionID)` 方法和 `taskSessions` 注册表
- task-launcher.ts 在 session 创建成功后调用 `taskManager.registerTaskSession(sessionID)`
- event-router.ts 首次收到 event 时通过 parentID 判断并注册 main session
- 所有 caller 的 isTask 判断改为 `taskManager.isTaskSession(sessionID)`（替代 `sessionStore.get().isTask`）
- message-hooks.ts 和 message-token-handler.ts 移除 `state.isTask = isTask` 设置
- session-runtime-info.ts 诊断日志降级为 `createTraceLog`
- task-monitor.ts tick 状态日志降级为 trace
- types.ts WopalTask 新增 agent/lastTokens/providerID/modelID/contextLimit
- `bun run test:run` 全部通过

## Out of Scope

- 删除 SessionStore 的 Map 结构（改为纯单例）— 风险太大，保留接口兼容
- 将 task session 的模型信息从 SessionStore 迁移到 WopalTask — 本次不在 SessionStore 存 task 状态即可，迁移为 P2
- 修改 formatSessionID 签名 — 保持当前 `(sessionID, isTask)` 签名，只修正调用点传入的 isTask 值

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| SessionStore | `session-store.ts` | 修改 | 删除 `isTask` 字段 |
| Types | `types.ts` | 修改 | WopalTask 扩展新字段 |
| TaskManager | `simple-task-manager.ts` | 修改 | 新增 `isTaskSession()` + taskSessions |
| Task Launcher | `task-launcher.ts` | 修改 | 创建时注册 task session |
| Event Router | `event-router.ts` | 修改 | 首次 event 注册 main session |
| Message Hooks | `message-hooks.ts` | 修改 | 移除 `state.isTask = isTask` |
| Token Handler | `message-token-handler.ts` | 修改 | 移除 `state.isTask = isTask` |
| Runtime Info | `session-runtime-info.ts` | 修改 | 诊断日志降级 trace |
| Task Monitor | `task-monitor.ts` | 修改 | `logTickStatus` 降级 trace |
| Tests | `*.test.ts` | 修改 | 更新测试中 SessionState 构造（移除 isTask） |

## Acceptance Criteria

### Agent Verification

1. [x] `rg 'isTask\b' .wopal/wopal-plugin/src/session-store.ts` = 0（isTask 已从 SessionState 移除）
2. [x] `rg 'state\.isTask\s*=' .wopal/wopal-plugin/src/ -g '!*.test.ts'` = 0（无代码在 SessionState 上设置 isTask）
3. [x] `rg '\.isTask\s*\?\s*false' .wopal/wopal-plugin/src/ -g '!*.test.ts'` = 0（无 sessionStore.get().isTask 读取）
4. [x] `rg 'isTaskSession' .wopal/wopal-plugin/src/simple-task-manager.ts` ≥ 2（方法定义 + 导出/使用）
5. [x] `rg 'registerTaskSession' .wopal/wopal-plugin/src/task-launcher.ts` ≥ 1（task 创建时注册）
6. [x] `rg 'createTraceLog' .wopal/wopal-plugin/src/session-runtime-info.ts` ≥ 1（引入 trace 日志）
7. [x] `rg '\[providersConfig\]' .wopal/wopal-plugin/src/session-runtime-info.ts` 所在行包含 `traceLog`（providersConfig 日志使用 trace 级别）
8. [x] `cd .wopal/wopal-plugin && bun run test:run` 全部 pass（无回归）

### User Validation

#### Scenario 1: 日志中同一 sessionID 标记一致
- Goal: 确认同一 sessionID 在 debug 日志中始终显示相同的 (main) 或 (task) 标记
- Precondition: `WOPAL_PLUGIN_DEBUG=task` 启用，有活跃的 wopal_task 运行
- User Actions:
  1. 启动 wopal，触发 wopal_task
  2. 观察 `logs/wopal-plugins-debug.log` 中同一 sessionID 的所有日志行
- Expected Result: 同一 sessionID 的所有行后缀标记一致（要么全部 `(main)`，要么全部 `(task)`），不再出现交替变化

#### Scenario 2: trace 日志仅在显式启用时输出
- Goal: 确认诊断细节（providersConfig、stale、tick）不在默认 debug 日志中出现
- Precondition: 无 `WOPAL_PLUGIN_TRACE` 环境变量，仅 `WOPAL_PLUGIN_DEBUG=task`
- User Actions:
  1. 启动 wopal
  2. 检查 `logs/wopal-plugins-debug.log`
- Expected Result: 日志中无 `[providersConfig]`、`tokens stale`、`[tick]` 等诊断细节；仅保留关键结果（如 `[ctxUsage] X%`、`[stuck] detected`）。设置 `WOPAL_PLUGIN_TRACE=task` 后这些细节重新出现

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: Remove isTask from SessionState + add isTaskSession to SimpleTaskManager

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**: SessionState 不再包含 `isTask` 字段；SimpleTaskManager 提供 `isTaskSession(sessionID)` 方法作为 isTask 判断的权威来源；taskSessions 集合在 task 创建时注册，永不删除（session 类型不可变）。

**Files**: `types.ts`, `session-store.ts`, `simple-task-manager.ts`

**Pre-read**: N/A

**Design**:

1. `types.ts`：WopalTask 新增字段 `agent?`, `lastTokens?`, `providerID?`, `modelID?`, `contextLimit?`
2. `session-store.ts`：SessionState 接口删除第 28 行 `isTask?: boolean | undefined`
3. `simple-task-manager.ts`：
   - 新增 `private taskSessions = new Set<string>()`
   - 新增 `registerTaskSession(sessionID: string): void`
   - 新增 `isTaskSession(sessionID: string): boolean`
   - 在构造函数或适当位置暴露这些方法

**TDD**: false（纯类型和接口重构，无业务逻辑变更）

**Changes**:
1. `types.ts`: WopalTask 接口新增 agent/lastTokens/providerID/modelID/contextLimit 可选字段
2. `session-store.ts`: 删除 SessionState 中的 `isTask?: boolean | undefined` 字段及注释
3. `simple-task-manager.ts`: 新增 `private taskSessions = new Set<string>()`
4. `simple-task-manager.ts`: 新增 `registerTaskSession(sessionID)` 方法
5. `simple-task-manager.ts`: 新增 `isTaskSession(sessionID)` 方法

**Verify**:
```bash
rg 'isTask\b' .wopal/wopal-plugin/src/session-store.ts && exit 1 || exit 0
rg 'isTaskSession' .wopal/wopal-plugin/src/simple-task-manager.ts
```

**Done**:
任务产出：SessionState 已删除 isTask 字段，SimpleTaskManager 已新增 isTaskSession() 方法
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: Downgrade diagnostic logs to trace level

**Verification Intent**: AC#6, AC#7

**Behavior**: session-runtime-info.ts、task-monitor.ts 中的诊断细节日志改用 `createTraceLog`，仅在 `WOPAL_PLUGIN_TRACE=task` 时输出。debug 级别仅保留关键结果。

**Files**: `session-runtime-info.ts`, `task-monitor.ts`

**Pre-read**: `debug.ts`（确认 `createTraceLog` 函数签名）

**Design**:

1. `session-runtime-info.ts`：
   - 在文件顶部新增 `import { createTraceLog } from "../debug.js"`
   - 创建 `const traceLog = createTraceLog("[task]", "task")`
   - `fetchProvidersConfig` 中 debugLog 调用改为 traceLog（第 41, 48, 51 行）
   - `extractContextFromStore` 中 stale check 日志改为 traceLog（第 181 行）
   - `fetchContextPercent` 中 fallback 路径日志改为 traceLog（第 254 行）
   - 保留关键结果在 debugLog（如 `ctxLog` 中的最终 pct 输出）
2. `task-monitor.ts`：
   - `logTickStatus` 中 debugLog 改为 traceLog（第 148 行）
   - 注：`progress-notify.ts` 无需直接修改——其日志均为关键结果（progressNotify sent/error），且其调用的 `fetchContextPercent` 已在 session-runtime-info.ts 中覆盖

**TDD**: false（日志级别调整，无业务逻辑变更）

**Changes**:
1. `session-runtime-info.ts`: 引入 `createTraceLog`，创建 `traceLog` 实例
2. `session-runtime-info.ts`: `fetchProvidersConfig` 三条日志改用 `traceLog`
3. `session-runtime-info.ts`: `extractContextFromStore` stale 日志改用 `traceLog`
4. `session-runtime-info.ts`: `fetchContextPercent` fallback 日志改用 `traceLog`
5. `task-monitor.ts`: `logTickStatus` 改用 `traceLog`

**Verify**:
```bash
rg 'createTraceLog' .wopal/wopal-plugin/src/session-runtime-info.ts
rg 'providersConfig.*traceLog|traceLog.*providersConfig' .wopal/wopal-plugin/src/session-runtime-info.ts
```

**Done**:
任务产出：诊断日志已降级为 trace 级别，debug 级别只保留关键结果
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: Fix all caller sites — mark isTask at source + use isTaskSession

**Verification Intent**: AC#2, AC#3, AC#5

**Behavior**: task 创建时立即注册到 taskSessions；event-router 首次收到 main session event 时注册 main；所有原 `sessionStore.get(sessionID)?.isTask` 的调用点改为 `taskManager.isTaskSession(sessionID)`；message-hooks 和 message-token-handler 移除 `state.isTask = isTask` 设置。

**Files**: `task-launcher.ts`, `event-router.ts`, `message-hooks.ts`, `message-token-handler.ts`, `session-runtime-info.ts`

**Pre-read**: `task-launcher.ts`（session 创建流程），`event-router.ts`（首次 event 处理），`message-hooks.ts`（isTask 设置点），`simple-task-manager.ts`（确认 Task 1 产出：taskSessions、registerTaskSession、isTaskSession 已就绪）

**Design**:

1. `task-launcher.ts`（在 launchTask 函数中）：
   - session 创建成功后（第 86-91 行之后），调用 `deps.taskManager.registerTaskSession(sessionID)`
   - 需要通过 deps 传入 taskManager 引用（或扩展 TaskLauncherDeps）
   - 同时可设置 WopalTask 的 agent 字段
2. `event-router.ts`（onEvent 函数中）：
   - 首次收到 event 且 `!session.parentID` 时，注册为 main session：
     `ctx.taskManager.registerMainSession(sessionID)`
   - 需要 SimpleTaskManager 新增 `mainSessionID` 字段和 `setMainSession()` 方法
3. `session-runtime-info.ts`（三处）：
   - `extractContextFromStore`（第 171-172 行）：`state?.isTask ?? false` → 通过传入的 taskManager 参数调用 `isTaskSession(sessionID)`
   - `fetchContextPercent`（第 226 行）：同上
   - 需要在这两个函数的参数中新增 `taskManager?: { isTaskSession: (id: string) => boolean }`
4. `message-hooks.ts`（两处）：
   - 第 55 行：删除 `state.isTask = isTask`
   - 第 60 行：删除 `state.isTask = isTask`
   - 保留第 39 行 `const isTask` 变量（用于 formatSessionID 等其他用途）
5. `message-token-handler.ts`：
   - 第 122 行：删除 `state.isTask = isTask`
   - 保留第 79 行 `const isTask` 变量（用于 formatSessionID）

**TDD**: false（类型驱动的调用点修正）

**Changes**:
1. `simple-task-manager.ts`: 新增 `mainSessionID: string | null` 和 `setMainSession(sessionID)` 方法
2. `task-launcher.ts`: 扩展 `TaskLauncherDeps` 加入 taskManager，session 创建成功后调用 `registerTaskSession`
3. `event-router.ts`: 首次 event 无 parentID → 调用 `setMainSession`
4. `session-runtime-info.ts`: `extractContextFromStore` 和 `fetchContextPercent` 参数新增 taskManager，isTask 改用 `taskManager.isTaskSession(sessionID)`
5. `message-hooks.ts`: 删除两处 `state.isTask = isTask` 设置
6. `message-token-handler.ts`: 删除 `state.isTask = isTask` 设置

**Verify**:
```bash
rg 'state\.isTask\s*=' .wopal/wopal-plugin/src/ -g '!*.test.ts'  # AC#2: 应为 0
rg 'sessionStore\.get.*\.isTask' .wopal/wopal-plugin/src/ -g '!*.test.ts'  # 应为 0
rg '\.isTask\s*\?\s*false' .wopal/wopal-plugin/src/ -g '!*.test.ts'  # AC#3: 应为 0
```

**Done**:
任务产出：所有 isTask 设置已移除，调用点已改用 taskManager.isTaskSession()
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: Run full test suite and verify consistency

**Verification Intent**: AC#8

**Behavior**: 重构后所有现有测试通过，无回归；新增的 session 类型判断逻辑被测试覆盖。

**Files**: `*.test.ts`（更新受影响的测试），`test-helpers.ts`（可能需要更新）

**Pre-read**: 所有受影响的测试文件

**Design**:

1. 更新所有使用 `sessionStore.upsert(sessionID, (state) => { state.isTask = ... })` 的测试：
   - `task-monitor.test.ts:290`
   - `event-router.test.ts:202`
   - `test-helpers.ts:25`
   - `memory.test.ts` 多处
   - `session-runtime-info.test.ts` 多处
2. 移除这些测试中的 `state.isTask = ...` 设置
3. 在 `simple-task-manager.test.ts` 中新增 `isTaskSession` 和 `registerTaskSession` 的测试
4. 运行 `bun run test:run` 确保全部通过

**TDD**: false（测试修正 + 补充覆盖）

**Changes**:
1. 各测试文件：删除 `state.isTask = true/false` 设置
2. `simple-task-manager.test.ts`：新增 isTaskSession 和 registerTaskSession 测试
3. 运行 `bun run test:run` 确认全部 pass

**Verify**:
```bash
cd .wopal/wopal-plugin && bun run test:run
```

**Done**:
任务产出：所有测试通过，无回归，新增 session 类型判断测试覆盖
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

> **Note**: 4 Tasks 处于 warning 阈值（rubric: 2-3 为 target，4 为 warning）。不拆分原因：Task 1/2 均为纯修改（类型定义 + 日志级别），Total 文件数可控；Task 3 文件交集多（simple-task-manager.ts 跨 Wave 修改），拆分会增加上下文切换成本。Task 3 Pre-read 已明确提醒确认 Task 1 产出。

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1, Task 2 | fae | 无 | Task 1（类型/接口改动）和 Task 2（日志级别调整）互不依赖，可并行；Files 不交集 |
| 2 | Task 3 | fae | Task 1, Task 2 | 依赖 Task 1 产出的 `isTaskSession()` 方法和 Task 2 产出的 traceLog 实例；Files 交集多（6 个文件），整组委派 |
| 3 | Task 4 | fae | Task 3 | 依赖所有代码变更完成；需运行全量测试验证无回归 |
