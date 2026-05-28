# refactor-wopal-plugin-deduplicate-and-consolidate-task-module

## Metadata

- **Type**: refactor
- **Target Project**: wopal-plugin
- **Created**: 2026-05-12
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

消除 task 模块中 4 处关键代码重复和 5 个碎片文件，将 ~3,040 行精简约 28% 至 ~2,200 行，不改变任何外部行为。

## Technical Context

task 模块（`src/tasks/` + `src/tools/wopal-task*.ts`）共 25 个文件、~3,040 行。经过逐文件审查，发现以下技术债务：

1. **toErrorMessage 重复 4 次**（task-launcher / question-relay / permission-proxy / error-classifier），~70 行
2. **getContextUsagePercent / getContextUsage 重复**（task-monitor / output-helpers），~130 行，核心逻辑 90% 相同
3. **消息分析函数散布**（getMessageTime ×2、tool call 提取 ×3、getFinishReason ×2、getLastAssistantMessage ×1），~80 行
4. **通知发送模式重复 5 次**（notifyParent / notifyParentStuck / sendProgressNotification / notifyParentQuestion / notifyParentPermission），~80 行
5. **5 个文件 < 60 行**过度碎片化（progress-tracker 22行、task-completion-notify 23行、stuck-detector 50行、session-cursor 50行、task-notifier-internals 56行）
6. **ErrorCategory 类型**在 types.ts 和 error-classifier.ts 各定义一份
7. **wopal-task-reply.ts** 三种 resume 模式的状态重置代码分散在 3 个 try/catch 中

全局性风险：纯重构，所有变更均为内部重组，外部接口（6 个工具的 args 和返回值）不变。风险可控。

## In Scope

- 提取共享 `toErrorMessage` 到 `tasks/utils.ts`
- 统一 `getContextUsage` 为单一核心函数
- 增强session-messages.ts 为消息分析中心（getMessageTime、提取tool calls、getLastAssistantMessage、getFinishReason）
- 提取通用 `sendNotification` 函数
- 合并碎片文件：stuck-detector → task-monitor、progress-tracker + progress-analyzer → progress、task-notifier-internals → task-notifier
- 删除 error-classifier.ts 中重复的 ErrorCategory 类型，统一使用 types.ts
- 提取 `resetTaskForResume` 统一状态重置

## Out of Scope

- WopalTask 接口拆分（影响面太大，需单独 issue）
- any 类型治理（依赖 OpenCode SDK 类型升级）
- question-relay / permission-proxy 外部接口变更
- 新增功能或行为变更

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 共享工具 | `tasks/utils.ts` | 创建 | 统一 toErrorMessage 等工具函数 |
| 消息分析 | `tasks/session-messages.ts` | 修改 | 增强为消息分析中心 |
| 上下文用量 | `tasks/task-monitor.ts`, `tools/output-helpers.ts` | 修改 | 统一 getContextUsage |
| 通知 | `tasks/task-notifier.ts` | 修改 | 合并 internals + 提取 sendNotification |
| 通知 | `tasks/task-notifier-internals.ts` | 删除 | 合并到 task-notifier.ts |
| 进度 | `tasks/progress.ts` | 创建 | 合并 tracker + analyzer |
| 进度 | `tasks/progress-tracker.ts`, `tasks/progress-analyzer.ts` | 删除 | 合并到 progress.ts |
| Stuck 检测 | `tasks/task-monitor.ts` | 修改 | 合并 stuck-detector |
| Stuck 检测 | `tasks/stuck-detector.ts` | 删除 | 合并到 task-monitor.ts |
| 错误分类 | `tasks/error-classifier.ts` | 修改 | 删除重复 ErrorCategory，引用 types.ts |
| Reply 状态 | `tools/wopal-task-reply.ts` | 修改 | 提取 resetTaskForResume |
| 通知消费者 | `tasks/question-relay.ts`, `tasks/permission-proxy.ts` | 修改 | 改用共享 toErrorMessage + sendNotification |
| 管理器 | `tasks/simple-task-manager.ts` | 修改 | 更新 import 路径 |
| Output 工具 | `tools/wopal-task-output.ts` | 修改 | 使用统一 getContextUsage |
| Delete 工具 | `tools/wopal-task-delete.ts` | 不变 | 无需修改 |
| Diff 工具 | `tools/wopal-task-diff.ts` | 不变 | 无需修改 |

## Implementation

### Task 1: 提取共享工具函数

**Files**: `tasks/utils.ts`（创建）, `tasks/task-launcher.ts`, `tasks/question-relay.ts`, `tasks/permission-proxy.ts`, `tasks/error-classifier.ts`, `types.ts`

**Changes**:

- [x] Step 1: 创建 `tasks/utils.ts`，从 `task-launcher.ts` 导出 `toErrorMessage` 和 `isPromiseLike`
- [x] Step 2: 删除 `task-launcher.ts` 中的 `toErrorMessage` 和 `isPromiseLike`，改为从 `utils.js` import
- [x] Step 3: 删除 `question-relay.ts` 中的本地 `toErrorMessage`，改为从 `utils.js` import
- [x] Step 4: 删除 `permission-proxy.ts` 中的本地 `toErrorMessage`，改为从 `utils.js` import
- [x] Step 5: 删除 `error-classifier.ts` 中重复的 `ErrorCategory` 类型定义和 `extractErrorMessage` 函数，改为从 `types.js` import `ErrorCategory`、从 `utils.js` import `toErrorMessage`；保留 `isRecord`、`isAbortedSessionError`、`classifyError`

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过
- [x] Step 3: grep 确认 `toErrorMessage` 仅在 `utils.ts` 和 `error-classifier.ts`（classifyError 内部调用）中定义，无其他重复定义

### Task 2: 统一消息分析函数

**Files**: `tasks/session-messages.ts`, `tasks/progress-analyzer.ts`, `tasks/loop-detector.ts`, `tasks/idle-diagnostic.ts`

**Changes**:

- [x] Step 1: 在 `session-messages.ts` 中新增 `getMessageTime(message: SessionMessage): number`（从 progress-analyzer 提取）
- [x] Step 2: 在 `session-messages.ts` 中新增 `getLastAssistantMessage(messages: SessionMessage[]): SessionMessage | undefined`（从 idle-diagnostic 提取）
- [x] Step 3: 在 `session-messages.ts` 中新增 `getFinishReason(messages: SessionMessage[]): string | undefined`（从 idle-diagnostic 提取，支持单条和数组两种签名）
- [x] Step 4: 在 `session-messages.ts` 中新增 `extractToolCallSequence(messages: SessionMessage[]): string[]`（从 loop-detector 提取）
- [x] Step 5: 更新 `progress-analyzer.ts`：删除本地 `getMessageTime`、`countToolCalls`（改用 extractToolCallSequence）、`hasAssistantTextContent`（移入 session-messages）、`getFinishReason`，改为从 session-messages import
- [x] Step 6: 更新 `loop-detector.ts`：删除本地 `getMessageTime`、`extractToolCallSequence`、`getAssistantTimestamps`（改为组合使用 getMessageTime），改为从 session-messages import
- [x] Step 7: 更新 `idle-diagnostic.ts`：删除本地 `extractAssistantText`（移入 session-messages）、`getLastAssistantMessage`、`getFinishReason`，改为从 session-messages import

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过

### Task 3: 合并碎片文件

**Files**: `tasks/progress.ts`（创建）, `tasks/progress-tracker.ts`（删除）, `tasks/progress-analyzer.ts`（删除）, `tasks/task-notifier.ts`（修改）, `tasks/task-notifier-internals.ts`（删除）, `tasks/task-monitor.ts`（修改）, `tasks/stuck-detector.ts`（删除）, `tasks/simple-task-manager.ts`

**Changes**:

- [x] Step 1: 创建 `tasks/progress.ts`，合并 `progress-tracker.ts`（isMeaningfulActivity、trackActivity）和 `progress-analyzer.ts`（analyzeProgress + ProgressInfo 接口 + 内部辅助函数），重新 export 所有公共 API
- [x] Step 2: 删除 `tasks/progress-tracker.ts` 和 `tasks/progress-analyzer.ts`
- [x] Step 3: 将 `tasks/task-notifier-internals.ts` 的内容（sendProgressNotification + SendProgressDeps）合并到 `tasks/task-notifier.ts`，删除 `task-notifier-internals.ts`
- [x] Step 4: 将 `tasks/stuck-detector.ts` 的内容（checkStuckTasks、clearStuckState、DEFAULT_STUCK_TIMEOUT_MS、StuckCheckConfig、StuckResult）合并到 `tasks/task-monitor.ts`，删除 `stuck-detector.ts`
- [x] Step 5: 更新 `simple-task-manager.ts` 的 import 路径：progress-tracker → progress、progress-analyzer → progress、stuck-detector → task-monitor、task-notifier-internals → task-notifier
- [x] Step 6: 更新 `tools/wopal-task-reply.ts` 的 import：progress-tracker → progress
- [x] Step 7: 更新 `tools/wopal-task-output.ts` 的 import：progress-analyzer → progress、loop-detector 不变
- [x] Step 8: 更新所有测试文件的 import 路径

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过
- [x] Step 3: 确认旧文件已被删除（progress-tracker.ts、progress-analyzer.ts、task-notifier-internals.ts、stuck-detector.ts 不存在）

### Task 4: 统一上下文用量获取

**Files**: `tasks/task-monitor.ts`, `tools/output-helpers.ts`, `tools/wopal-task-output.ts`

**Changes**:

- [x] Step 1: 将 `task-monitor.ts` 中的 `getContextUsagePercent` 提取为核心函数 `fetchContextPercent(client, directory, sessionID, debugLog): Promise<number | null>`
- [x] Step 2: 在 `output-helpers.ts` 中将 `getContextUsage` 改为调用 `fetchContextPercent`（从 task-monitor import），外层包装格式化逻辑（添加 formatTokenCount 和 warn 标记）
- [x] Step 3: 删除 `output-helpers.ts` 中重复的 messages/providers 获取逻辑，仅保留格式化包装
- [x] Step 4: 更新 `wopal-task-output.ts` 中对 `getContextUsage` 的调用（如有），确保使用 output-helpers 的格式化版本

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过
- [x] Step 3: grep 确认 `config.providers` 调用仅在 `task-monitor.ts` 中出现一次

### Task 5: 提取通知发送和状态重置

**Files**: `tasks/task-notifier.ts`, `tasks/question-relay.ts`, `tasks/permission-proxy.ts`, `tools/wopal-task-reply.ts`

**Changes**:

- [x] Step 1: 在 `task-notifier.ts` 中提取 `sendNotification(deps: TaskNotifierDeps, parentSessionID: string, text: string, noReply?: boolean): Promise<void>` 通用函数
- [x] Step 2: `notifyParent` 和 `notifyParentStuck` 改用 `sendNotification`（仅保留各自的文本构建逻辑）
- [x] Step 3: `sendProgressNotification` 改用 `sendNotification`
- [x] Step 4: `question-relay.ts` 的 `notifyParentQuestion` 改用 `sendNotification`（从 task-notifier import）
- [x] Step 5: `permission-proxy.ts` 的 `notifyParentPermission` 改用 `sendNotification`（从 task-notifier import）
- [x] Step 6: 在 `tools/wopal-task-reply.ts` 中提取 `resetTaskForResume(task: WopalTask): void` 函数，统一三种 resume 模式（interrupt / question reply / normal reply）的状态重置代码（`task.status = "running"`、`delete task.idleNotified`、`delete task.waitingReason`、`trackActivity`）
- [x] Step 7: 在 `wopal-task-reply.ts` 的三个 resume 分支中使用 `resetTaskForResume`

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1（共享工具函数） | fae | 无 |
| 1 | Task 2（消息分析统一） | fae | 无 |
| 2 | Task 3（合并碎片文件） | fae | Task 1, Task 2（import 路径受影响） |
| 2 | Task 4（上下文用量统一） | fae | 无（与 Task 3 无文件交叉） |
| 2 | Task 5（通知发送 + 状态重置） | fae | Task 1（依赖 utils.ts） |

说明：Task 1 和 Task 2 无文件交叉，可并行。Task 3 合并文件时需要 Task 1/2 的新 import 路径已就位。Task 4 和 Task 5 互不依赖但都依赖 Task 1，与 Task 3 同批并行。

## Test Plan

#### Unit Tests

##### Case U1: toErrorMessage 去重验证
- Goal: 确认 toErrorMessage 从 utils.ts 正确导出且所有消费方行为不变
- Fixture: 现有测试用例（error-classifier.test.ts、task-launcher.test.ts）
- Execution:
  - [x] Step 1: `bun run test:run` 运行所有测试
  - [x] Step 2: 确认 error-classifier.test.ts、task-launcher.test.ts 相关测试通过
- Expected Evidence: 所有测试通过，无 regression

##### Case U2: 合并后 progress 模块功能不变
- Goal: 确认 progress-tracker + progress-analyzer 合并到 progress.ts 后功能一致
- Fixture: 现有 progress-tracker.test.ts、progress-analyzer.test.ts（迁移到 progress.test.ts）
- Execution:
  - [x] Step 1: 迁移测试文件到 progress.test.ts，更新 import
  - [x] Step 2: `bun run test:run` 全部通过
- Expected Evidence: 所有 progress 相关测试通过

##### Case U3: stuck-detector 合并后功能不变
- Goal: 确认 stuck-detector 合并到 task-monitor.ts 后功能一致
- Fixture: 现有 stuck-detector.test.ts（迁移到 task-monitor.test.ts 或更新 import）
- Execution:
  - [x] Step 1: 更新测试文件 import 路径
  - [x] Step 2: `bun run test:run` 全部通过
- Expected Evidence: stuck 检测测试通过

#### Integration Tests

N/A — 纯内部重构，无接口变更，单元测试覆盖足够

#### E2E Tests

N/A — 插件内部重构，无用户可触发的端到端行为变更

#### Regression Tests

##### Case R1: 任务完整生命周期回归
- Goal: 确认重构后任务启动 → 运行 → 通知 → 回复 → 完成 全链路正常
- Fixture: 插件正常加载的 OpenCode 环境
- Execution:
  - [x] Step 1: `bun run test:run` 运行全部测试套件
  - [x] Step 2: 确认 simple-task-manager.test.ts、wopal-task-reply.test.ts、wopal-task-output.test.ts、wopal-task-diff.test.ts 全部通过
- Expected Evidence: 所有 16 个测试文件通过，0 失败

### Adjustment Strategy

N/A — 纯重构，每步可独立验证，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过，0 错误
- [x] `bun run test:run` 全部通过，0 失败
- [x] `toErrorMessage` 仅在 `tasks/utils.ts` 定义（error-classifier 的 extractErrorMessage 为语义不同的包装，不算重复）
- [x] `config.providers` 调用仅在 `task-monitor.ts` 中出现一次
- [x] 以下 4 个文件已删除：progress-tracker.ts、progress-analyzer.ts、task-notifier-internals.ts、stuck-detector.ts
- [x] `tasks/utils.ts` 已创建并导出 toErrorMessage 和 isPromiseLike

### User Validation

#### Scenario 1: 任务委派功能正常
- Goal: 确认重构后 wopal_task 启动任务、wopal_task_output 查询输出、wopal_task_reply 恢复任务的行为与重构前一致
- Precondition: OpenCode 已重启加载新插件代码
- User Actions:
  1. 使用 wopal_task 启动一个简单的 explore 任务
  2. 使用 wopal_task_output 查看任务状态和输出
  3. 等待任务 idle 后使用 wopal_task_reply 恢复或结束
- Expected Result: 任务全生命周期行为与重构前无差异，通知格式正确

- [x] 用户已完成上述功能验证并确认结果符合预期
