# 107-fix-wopal-plugin-progress-notification-context-messageabortederror-

## Metadata

- **Issue**: #107
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-16
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

修复 wopal-plugin 中两个遗留 bug：PROGRESS 通知缺失 Context 行 + session.error 未过滤 MessageAbortedError。

## Technical Context

### Bug 1: PROGRESS 通知缺失 Context

**根因分析**：

`task-monitor.ts:72` 守卫 `if (used === 0) return null` — 当 step 正在 streaming 时 `tokens.input=0`，跳过返回。

这是**设计行为**（避免返回不准确的 0%），但 ticker 每 30s 检查时可能正好赶上 streaming 状态。

**改进方案**：使用 `cacheContextUsage` 缓存机制 — `event-router.ts:47-49` 已在 `step-finish` 时调用 `cacheContextUsage`。PROGRESS 通知应优先读取 `task.lastContextUsage` 缓存值，仅在缓存缺失时才调用 `getContextUsagePercent`。

### Bug 2: MessageAbortedError 未过滤

**根因分析**：

`event-router.ts:92-105` 处理 `session.error` 事件时未过滤 `MessageAbortedError`。OpenCode TUI 在 `app.tsx:825` 有过滤：`if (error.name === "MessageAbortedError") return`。

当 `session.error` 先于 `session.idle` 到达（`idleNotified=false`）时，`markTaskErrorBySession` 会调用 `failTask` → `status='error'`。

**附加问题**：`markTaskErrorBySession` skip 时返回 `task`（而非 `undefined`），导致 `event-router.ts:98` 的 `if (task)` 成立 → 重复发送通知。

**修复方案**：
1. `event-router.ts` 添加 `MessageAbortedError` 过滤
2. `task-lifecycle.ts:markTaskErrorBySession` skip 时返回 `undefined` 而非 `task`

## In Scope

- Bug 1：PROGRESS 通知优先使用缓存值
- Bug 2：过滤 MessageAbortedError + 修复 skip 返回值

## Out of Scope

- Bug 1 的"完全消除时序窗口"（streaming 期间返回 null 是正确行为）
- 其他 wopal-plugin bug

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| task-monitor | `src/tasks/task-monitor.ts` | 修改 | Bug 1: 优先读缓存 |
| task-notifier-internals | `src/tasks/task-notifier-internals.ts` | 修改 | Bug 1: 传缓存值给通知 |
| event-router | `src/hooks/event-router.ts` | 修改 | Bug 2: 过滤 MessageAbortedError |
| task-lifecycle | `src/tasks/task-lifecycle.ts` | 修改 | Bug 2: skip 返回 undefined |
| simple-task-manager | `src/tasks/simple-task-manager.ts` | 修改 | Bug 2: 调用 markErrorBySession 时处理返回值 |

## Implementation

### Task 1: Bug 1 — PROGRESS 通知优先使用缓存值

**Files**: `src/tasks/task-monitor.ts`, `src/tasks/task-notifier-internals.ts`

**Changes**:

- [x] Step 1: `task-monitor.ts:checkProgressNotifications` — 优先使用 `task.lastContextUsage` 缓存，仅在缓存缺失时调用 `getContextUsagePercent`
- [x] Step 2: `task-notifier-internals.ts:sendProgressNotification` — 接收 `contextUsage` 参数不变（已有缓存值时传缓存值，无缓存时传 null）

**Verification**:

- [x] Step 1: `bun run test:run` 验证单测通过
- [x] Step 2: 检查 `logTickStatus` 输出正确显示缓存值

### Task 2: Bug 2 — 过滤 MessageAbortedError + 修复返回值

**Files**: `src/hooks/event-router.ts`, `src/tasks/task-lifecycle.ts`, `src/tasks/simple-task-manager.ts`

**Changes**:

- [x] Step 1: `event-router.ts:92-105` — 在 `session.error` 处理开头添加 `MessageAbortedError` 过滤（检查 `props?.error?.name === "MessageAbortedError"`）
- [x] Step 2: `task-lifecycle.ts:markTaskErrorBySession` — L81-84 和 L86-89 的 skip 路径改为返回 `undefined` 而非 `task`
- [x] Step 3: `simple-task-manager.ts:markTaskErrorBySession` — 调用方已有 `if (task)` 检查，返回值语义修正后逻辑不变

**Verification**:

- [x] Step 1: `bun run test:run` 验证单测通过
- [x] Step 2: `event-router.test.ts` 添加 MessageAbortedError 过滤测试 case

## Delegation Strategy

N/A — 两个 Task 独立且简单，Wopal 直接执行。

## Test Plan

#### Unit Tests

##### Case U1: MessageAbortedError 过滤
- Goal: 验证 session.error 事件过滤 MessageAbortedError
- Fixture: `event-router.test.ts` 中添加测试 case
- Execution:
  - [x] Step 1: 添加 test case 模拟 `session.error` 事件传入 `{ name: "MessageAbortedError" }`
  - [x] Step 2: 验证 `markTaskErrorBySession` 未被调用
- Expected Evidence: task status 保持原状态，无 error 标记

##### Case U2: PROGRESS 通知缓存优先
- Goal: 验证 checkProgressNotifications 优先使用缓存值
- Fixture: 代码逻辑验证（无独立测试文件，缓存优先逻辑简单明确）
- Execution:
  - [x] Step 1: 代码审查 `task-monitor.ts:139` 优先读 `task.lastContextUsage ?? null`
  - [x] Step 2: 验证仅在缓存为 null 时调用 `getContextUsagePercent`
- Expected Evidence: 代码逻辑正确，现有测试覆盖不阻断

#### Integration Tests

N/A — Bug 修复范围小，单测覆盖充分。

#### Regression Tests

##### Case R1: 现有 session.error 处理不受影响
- Goal: 验证其他错误类型仍正常处理
- Fixture: 现有 `event-router.test.ts` 测试
- Execution:
  - [x] Step 1: `bun run test:run` 验证现有测试通过
- Expected Evidence: 所有 event-router.test.ts 测试通过（6 tests passed）

### Rollback Strategy

N/A — 低风险修复，出问题直接 revert commit。

## Acceptance Criteria

### Agent Verification

- [x] `bun run test:run` 全部通过
- [x] `bun run lint` 无新增 error

### User Validation

#### Scenario 1: MessageAbortedError 不污染任务状态
- Goal: 确认子会话 abort 后任务不会被标记为 error
- Precondition: 启动一个 wopal_task 子会话
- User Actions:
  1. 使用 `wopal_task_interrupt(task_id)` 中断任务
  2. 观察 `[WOPAL TASK IDLE]` 通知而非 `[WOPAL TASK ERROR]`
- Expected Result: 任务状态为 IDLE/running，无 error 标记

#### Scenario 2: PROGRESS 通知稳定显示 Context
- Goal: 确认 PROGRESS 通知在 streaming 期间仍能显示 Context 用量
- Precondition: 启动一个长时间运行的 wopal_task
- User Actions:
  1. 等待至少一次 PROGRESS 通知触发
  2. 检查通知是否包含 `Context: xx% used` 行
- Expected Result: 通知包含 Context 行（使用缓存值）

- [x] 用户已完成上述功能验证并确认结果符合预期