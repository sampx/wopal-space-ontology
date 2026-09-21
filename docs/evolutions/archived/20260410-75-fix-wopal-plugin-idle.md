# 75-fix-wopal-plugin-idle

## Metadata

- **Issue**: #75
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-10
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

补充任务终态路径（completed 不走 cancel）、新增 reply interrupt 能力、新增 diff 工具、统一工具命名为 `wopal_task_*` 前缀。

## Technical Context

Phase 3 实现了 IDLE 通知机制（`runtime.ts:834-856`），子会话 idle 时设置 `task.idleNotified=true` 但保持 `status='running'`，判断权交给 Wopal。这带来三个功能缺口：

1. **终态路径缺失**：Wopal 确认任务正常完成后，只能用 `wopal_cancel` 关闭任务，导致 `completed` 变成 `cancelled`。需要一个显式完成路径。
2. **无法中断纠偏**：fae 走偏时，Wopal 只能等它 idle 后 reply 或直接 cancel。没有"打断当前执行 + 发送纠正指令"的能力。
3. **验证成本高**：验证 fae 代码变更需 `wopal_output` 读整个输出，token 开销大。需要只看变更的 diff 视图。

此外，当前工具命名不一致：`wopal_task` 用 `wopal_task` 前缀，而 `wopal_output`、`wopal_reply`、`wopal_cancel` 没有 task 前缀。统一为 `wopal_task_*` 命名空间，语义更清晰，与 `wopal_task` 工具族对齐。

**关于 idle 状态显示**：原 Issue 中提到的"Status 显示矛盾"，经深入分析后发现：
- `notifyParent`（line 400）已正确显示 `[WOPAL TASK IDLE]`，通知语义正确
- `stuck-detector.ts:26` 已排除 idle 任务，不会误触发 stuck 检测
- `checkProgressNotifications`（line 431）已排除 idle 任务，不会发多余进度通知
- 唯一不一致的是 `wopal_output` 的 `Status: running` 行（line 85），但这只是**显示层美化**，不影响功能
- `idleNotified` 作为 `status='running'` 的附加标记，现有状态机已完整适配，不需要引入新状态值

**结论**：idle 显示修正降级为纯 UI 优化（在 Task 1 中附带处理），不作为独立改造目标。

**架构约束**：`SimpleTaskManager` 是任务状态的核心管理者，所有状态变更应通过它。工具层（`tools/`）只负责参数解析和调用 manager。

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| 任务管理器 | `src/simple-task-manager.ts` | 新增 `completeTask` 方法 |
| 输出工具 | `src/tools/wopal-task-output.ts` | idle 显示美化 + complete action（重命名自 wopal-output） |
| 回复工具 | `src/tools/wopal-task-reply.ts` | 新增 interrupt 参数（重命名自 wopal-reply） |
| Diff 工具 | `src/tools/wopal-task-diff.ts`（新建） | 基于 OpenCode session_diff 的文件变更视图 |
| 工具注册 | `src/tools/index.ts` | 注册重命名 + 新增 |
| 通知模板 | `src/simple-task-manager.ts`, `src/tools/wopal-task-output.ts` | 工具名引用更新 |

## In Scope

- [ ] wopal_task_output idle 状态显示美化（Status 行显示 "idle" 而非 "running"，纯 UI 层）
- [ ] wopal_task_output 新增 `action="complete"` 参数，支持显式完成任务
- [ ] SimpleTaskManager 新增 `completeTask` 方法
- [ ] wopal_task_reply 新增 `interrupt` 参数，支持中断后纠偏
- [ ] 新增 wopal_task_diff 工具，基于 OpenCode `session.diff` API 显示文件变更
- [ ] 工具重命名：`wopal_output` → `wopal_task_output`、`wopal_reply` → `wopal_task_reply`、`wopal_cancel` → `wopal_task_cancel`
- [ ] 更新现有测试 + 新增测试覆盖
- [ ] 更新插件 AGENTS.md、README.md 中的工具名引用

## Out of Scope

- Task Store 持久化
- 消息拉取性能优化
- 管道延时度量
- 上下文使用率显示
- memory 模块参数修正（已拆分至 #78）
- idleNotified 状态机改造（现有机制已完备，见 Technical Context 分析）
- 历史文档（`docs/projects/plans/done/`）不追溯修改
- 空间级文档（`AGENTS.md`、系统提示词）的工具名引用 — 由 `/evolve` 单独处理

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/simple-task-manager.ts` | 修改 | 新增 `completeTask` + 通知模板中工具名更新 |
| `src/tools/wopal-output.ts` | 重命名为 `wopal-task-output.ts` + 修改 | idle 显示美化 + complete action |
| `src/tools/wopal-reply.ts` | 重命名为 `wopal-task-reply.ts` + 修改 | 新增 interrupt 参数 |
| `src/tools/wopal-task-diff.ts` | 创建 | 文件变更 diff 工具（基于 v2 SDK） |
| `src/tools/index.ts` | 修改 | 注册键重命名 + 新增 wopal_task_diff |
| `src/tools/wopal-task.ts` | 修改 | 返回消息中工具名更新 |
| `src/tools/wopal-output.test.ts` | 重命名为 `wopal-task-output.test.ts` + 修改 | 新增测试用例 |
| `src/tools/wopal-reply.test.ts` | 重命名为 `wopal-task-reply.test.ts` + 修改 | 新增 interrupt 测试 |
| `src/tools/wopal-task-diff.test.ts` | 创建 | diff 工具测试 |
| `src/tools/wopal-tools.test.ts` | 修改 | describe 名称和工具键名更新 |
| `src/tools/wopal-cancel.ts` | 重命名为 `wopal-task-cancel.ts` | 纯重命名 |
| `src/question-relay.ts` | 修改 | 注释中工具名更新 |
| `src/idle-diagnostic.ts` | 修改 | 注释中工具名更新 |
| `src/runtime.ts` | 修改 | 注释中工具名更新 |
| `src/index.ts` | 修改 | 日志中工具名更新 |
| `AGENTS.md` | 修改 | 工具名引用更新 |
| `README.md` | 修改 | 工具名引用更新 |

## Implementation

### Task 1: complete action + idle 显示美化

**Files**: `src/simple-task-manager.ts`, `src/tools/wopal-task-output.ts`

**背景分析**：当前状态机对 `idleNotified` 的处理已完备（见下表），本次改动**不触及状态机逻辑**，仅在显示层和终态路径上补缺。

| 现有逻辑 | 文件:行 | idleNotified 处理 | 影响 |
|----------|---------|-------------------|------|
| stuck 检测 | `stuck-detector.ts:26` | `if (task.idleNotified) continue` | idle 不触发 stuck ✅ |
| 进度通知 | `simple-task-manager.ts:431` | `!t.idleNotified` 过滤 | idle 不发进度 ✅ |
| 父通知 | `simple-task-manager.ts:400` | `idleNotified ? 'IDLE' : status` | 通知显示 IDLE ✅ |
| reply 恢复 | `wopal-task-reply.ts:103,123` | `delete task.idleNotified` | reply 清除 idle ✅ |
| activity 追踪 | `runtime.ts:819,828` | `task.status === "running"` | idle 后无新消息，自然停 ✅ |

**Changes**:

1. `simple-task-manager.ts` — 新增 `completeTask` 方法：
   - 校验 task 存在 + 父会话匹配 + 状态为 `running`（含 idleNotified）
   - 设置 `status = 'completed'`，`completedAt = new Date()`
   - 释放 concurrency slot（检查 `waitingConcurrencyKey`，因为 idle 时 slot 已移到该字段）
   - 返回 `'completed' | 'not_found' | 'not_running'`

2. `wopal-task-output.ts` — idle 显示美化（纯 UI，不改变 status 值）：
   - 当 `task.idleNotified` 时，`Status` 行显示 `idle (awaiting judgment)` 而非 `running`
   - 注意：这是显示层替换，`task.status` 仍为 `running`，不影响任何状态机判断

3. `wopal-task-output.ts` — 新增 `action` 参数：
   - `action: tool.schema.enum(["complete"]).optional()`
   - 当 `action="complete"` 时：调用 `manager.completeTask(task_id, context.sessionID)`
   - 完成后继续显示输出内容（从子会话拉取消息）
   - 非 idle 状态调用 `action="complete"` 返回错误提示

4. `wopal-task-output.ts` — 更新 idle 提示文案：
   - 当前：`Use wopal_output to check, then wopal_cancel or wopal_reply.`
   - 改为：`Use wopal_task_output(action="complete") to accept, wopal_task_reply to redirect, or wopal_task_cancel to terminate.`

**Verification**: `bun run test:run` — 验证现有测试不被破坏

- [ ] Step 1: 实现完成
- [ ] Step 2: 测试通过

### Task 2: wopal_task_reply interrupt 参数

**Files**: `src/tools/wopal-task-reply.ts`

**Changes**:

1. 新增 `interrupt` 布尔参数：
   - `interrupt: tool.schema.boolean().optional().default(false).describe("Abort current execution and send correction")`

2. 当 `interrupt=true` 时的执行逻辑：
   - 先调用 `client.session.abort({ path: { id: task.sessionID } })` 中断当前推理
   - 再调用 `client.session.promptAsync` 发送纠正消息
   - 重置状态：`task.status = 'running'`，删除 `idleNotified`、`waitingReason`、`waitingConcurrencyKey`
   - 如果任务之前 idle 且有 `waitingConcurrencyKey`，需要重新获取并发槽（任务恢复执行）
   - 调用 `trackActivity(task, "text")` 更新活动时间

3. 状态校验：
   - `interrupt=true` 仅允许 `running`（含 idleNotified）状态的任务
   - `waiting` 状态的任务不需要 interrupt（已经停了），直接 reply 即可
   - 其他状态返回错误

4. 错误处理：
   - `abort` 失败不阻断（任务可能已经 idle）
   - `promptAsync` 失败返回错误信息

**Verification**: `bun run test:run`

- [ ] Step 1: 实现完成
- [ ] Step 2: 测试通过

### Task 3: 新增 wopal_task_diff 工具

**Files**: `src/tools/wopal-task-diff.ts`（新建）, `src/tools/index.ts`

**技术方案**：利用 OpenCode 内置的 `session_diff` 机制，而非手动解析消息。

OpenCode 在每次 assistant 消息完成后自动计算文件 diff（`Snapshot.FileDiff[]`），存入 `session_diff` 存储。v2 SDK 提供 `client.session.diff({ sessionID, messageID? })` 直接查询。

**返回类型**（已有，无需定义）：
```typescript
type FileDiff = {
  file: string        // 文件路径
  before: string      // 变更前内容
  after: string       // 变更后内容
  additions: number   // 增加行数
  deletions: number   // 删除行数
  status?: "added" | "deleted" | "modified"
}
```

**调用链路**：`SimpleTaskManager` 已持有 `v2Client` 并暴露 `getV2Client()`（line 121-123），直接使用。

**Changes**:

1. 新建 `wopal-task-diff.ts`：
   - 工具名：`wopal_task_diff`
   - 工具描述：`"Show file changes made by a background task. More token-efficient than wopal_task_output for verifying code changes."`
   - 参数：`task_id: string`（必填）
   - 执行逻辑：
     a. 获取 task，校验父会话匹配
     b. 调用 `manager.getV2Client().session.diff({ sessionID: task.sessionID })`
     c. 格式化 `FileDiff[]` 输出：
        - 每个文件一行：`[status] path (+additions/-deletions)`
        - 如果无变更，返回 "No file changes in this task."
     d. 底部显示统计：`Total: N files changed, +A/-L lines`

2. `index.ts` 注册：
   - 导入 `createWopalTaskDiffTool`
   - 在 `createWopalTools` 中注册 `wopal_task_diff`

**优势**（对比原手动解析方案）：
- 实现量从 ~80 行降到 ~40 行
- 无需依赖 `session-cursor.ts`、`session-messages.ts`
- 数据来自 OpenCode 核心的 Snapshot 引擎，准确性有保障
- 天然支持增量查询（通过 `messageID` 参数可选查看单条消息的 diff）

**Verification**: `bun run test:run`

- [ ] Step 1: 实现完成
- [ ] Step 2: 测试通过

### Task 4: 工具重命名

**Scope**: 将 `wopal_output`、`wopal_reply`、`wopal_cancel` 重命名为 `wopal_task_output`、`wopal_task_reply`、`wopal_task_cancel`

**重命名映射**：

| 旧名 | 新名 | 文件名变更 |
|------|------|-----------|
| `wopal_output` | `wopal_task_output` | `wopal-output.ts` → `wopal-task-output.ts` |
| `wopal_reply` | `wopal_task_reply` | `wopal-reply.ts` → `wopal-task-reply.ts` |
| `wopal_cancel` | `wopal_task_cancel` | `wopal-cancel.ts` → `wopal-task-cancel.ts` |

**影响面**（仅限插件源码内）：

| 类别 | 文件 | 改动 |
|------|------|------|
| 工具注册 | `tools/index.ts` | 注册键名更新 |
| 通知模板 | `simple-task-manager.ts` | `notifyParent`、`sendProgressNotification`、`notifyParentStuck` 中的工具名引用 |
| 提示文案 | `tools/wopal-task-output.ts` | idle 提示文案中的工具名引用 |
| 返回消息 | `tools/wopal-task.ts` | launch 返回消息中的工具名引用 |
| 禁用列表 | `simple-task-manager.ts:266` | `"wopal_task": false` → 不变，已正确 |
| 日志 | `index.ts` | debugLog 中的工具列表字符串 |
| 注释 | `question-relay.ts`, `idle-diagnostic.ts`, `runtime.ts` | 注释中工具名引用 |
| describe | `wopal-tools.test.ts` | describe 块名称 |
| 导入路径 | 所有引用重命名文件的 `.ts` | `.js` 后缀的 import 路径更新 |

**不改的**：
- `wopal_task` 本身不改名（已有 task 前缀）
- `memory_manage`、`context_manage` 不改名（非任务工具）
- 历史文档（`docs/projects/plans/done/`）不追溯
- 空间级文档（`AGENTS.md`、系统提示词 `wopal.md`/`wopal-cn.md`）的工具名引用 — 这些由 `/evolve` 单独处理，避免本 Plan 膨胀

**执行策略**：先完成 Task 1-3（功能改动），再执行 Task 4（纯重命名），避免在功能开发期间频繁处理 import 路径冲突。

**Verification**: `bun run test:run` + `bun run build`

- [ ] Step 1: 文件重命名 + import 路径更新
- [ ] Step 2: 注册键名 + 通知模板 + 提示文案更新
- [ ] Step 3: 测试文件同步重命名 + describe 更新
- [ ] Step 4: 全部测试通过 + 构建通过

### Task 5: 测试更新

**Files**: `src/tools/wopal-task-output.test.ts`, `src/tools/wopal-task-reply.test.ts`, `src/tools/wopal-task-diff.test.ts`（新建）

**Changes**:

1. `wopal-task-output.test.ts` 新增用例：
   - idle task 显示 "idle" 而非 "running"
   - `action="complete"` 成功标记完成
   - `action="complete"` 非 idle 任务返回错误

2. `wopal-task-reply.test.ts` 新增用例：
   - `interrupt=true` 调用 abort + promptAsync
   - `interrupt=true` 非 running 状态返回错误
   - `interrupt=true` abort 失败仍发送消息

3. `wopal-task-diff.test.ts` 新建：
   - 无变更时返回 "No file changes"
   - 有文件变更时正确格式化 FileDiff[]
   - v2Client.session.diff 不可用时优雅降级

**Verification**: `bun run test:run`

- [ ] Step 1: 测试编写完成
- [ ] Step 2: 全部测试通过

### Task 6: 文档更新

**Files**: `AGENTS.md`, `README.md`

**Changes**:

1. `AGENTS.md`：
   - 所有 `wopal_output` → `wopal_task_output`
   - 所有 `wopal_reply` → `wopal_task_reply`
   - 所有 `wopal_cancel` → `wopal_task_cancel`
   - 数据流描述和状态流转图中的工具名

2. `README.md`：
   - 工具表格中的名称和示例
   - 流程图中的工具名

**Verification**: 人工审查

- [ ] Step 1: 更新完成

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 1 | Task 2 | fae | 无 |
| 1 | Task 3 | fae | 无 |
| 2 | Task 4 | fae | Task 1-3 |
| 2 | Task 5 | fae | Task 1-3 |
| 3 | Task 6 | fae | Task 4 |

## Test Plan

### Test Case Design

- complete action：单元测试验证 `action="complete"` 调用 completeTask 并显示输出 / 单元测试 / 断言状态变为 "completed"
- idle 显示美化：单元测试验证 `Status` 行在 `idleNotified=true` 时显示 "idle" / 单元测试 / 断言包含 "idle" 不包含 "running"
- interrupt reply：单元测试验证 `interrupt=true` 调用 abort + promptAsync / 单元测试 / 断言 abort 和 promptAsync 都被调用
- wopal_task_diff：单元测试验证 FileDiff 格式化 / 单元测试 / 断言正确调用 v2Client.session.diff 并格式化输出
- 工具重命名：`bun run build` 编译通过 + 现有测试 import 路径正确

### Regression Testing

- 现有 `wopal-task-output.test.ts` 用例不破坏（idleNotified=false 时 Status 仍显示 "running"）
- 现有 `wopal-task-reply.test.ts` 用例不破坏（interrupt=false 时行为不变）
- `bun run build` 编译通过

### Adjustment Strategy

- 如果 `session.abort` 后无法 `promptAsync`（session 已关闭），interrupt 退化为 cancel + 重新 launch
- 如果 `v2Client.session.diff` 不可用（SDK 版本不匹配），降级为提示用户使用 wopal_task_output

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 全部测试通过（400 tests）
- [x] idle task `wopal_task_output` Status 显示 "idle (awaiting judgment)"
- [x] `wopal_task_reply(interrupt=true)` 调用 abort + promptAsync
- [x] `wopal_task_diff` 正确调用 v2 SDK session.diff 并格式化输出
- [x] 工具注册键名全部更新为 `wopal_task_*` 前缀
- [x] `completed` 状态已从状态机移除，cancel 兼顾语义

### User Validation

- [x] 重启 OpenCode 后 wopal_plugin 加载正常
- [x] 实际委派 fae 任务，idle 后 wopal_task_output 显示 idle 状态
- [x] 用 wopal_task_cancel 确认任务完成（替代 complete action）
- [x] 用 wopal_task_reply(interrupt=true) 中断走偏的 fae 任务
- [x] 用 wopal_task_diff 查看文件变更摘要
- [x] 通知中的工具名引用正确（wopal_task_output / wopal_task_reply / wopal_task_cancel）
