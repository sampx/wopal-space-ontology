# 86-refactor-wopal-task

## Metadata

- **Issue**: #86
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-13
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

重新设计 wopal-task 状态管理：task 是永续对话通道，去除终态概念，并发槽位根据 running/idle 状态动态占用/释放。

## Technical Context

### OpenCode abort 机制研究结论（源码验证）

**源码路径分析**：
1. `session.abort` API → `SessionPrompt.cancel()` → `SessionRunState.cancel()`
2. `cancel()` 调用 `runner.cancel` → `Fiber.interrupt` 打断当前 fiber
3. `Runner.cancel` 后状态变成 `{ _tag: "Idle" }` + 触发 `onIdle` callback
4. `onIdle` → `runners.delete(sessionID)` 删除 runner + `status.set(sessionID, { type: "idle" })`
5. 后续 `promptAsync` → `runner(sessionID)` 发现 map 中不存在 → **创建新的 runner**
6. 新 runner 的 `ensureRunning` 从 Idle 状态 → **启动新的 run**

**核心发现**：
- **abort 只是打断 running loop，不改 session 生命周期**
- **session 永续存在，只有物理删除才真正终止**
- **abort 后可以继续 prompt 对话**

### 当前设计问题

**问题 1：complete 后 reply 失效**
- `complete()` 设置 `status = 'completed'` + 释放槽位
- 但**没调用 `session.abort`**，子 session 还活着
- `reply()` 只允许 `waiting/running` 状态，`completed` 被拒绝
- 结果：子 session 存活但无法操作

**问题 2：cancel 设置终态**
- `cancel()` 设置 `status = 'cancelled'` + abort session
- 但根据 OpenCode 设计，abort 后 session 还能继续
- 被标记 `cancelled` 的 task 无法恢复，违背永续对话设计

**问题 3：reply 唤醒不重新占用槽位**
- reply 成功后设置 `status = "running"`，但没有重新 acquire 槽位
- 可能导致超过并发限制

### 正确设计理念（已验证）

**核心洞察**：
- **Task = 永续对话通道**：没有终态，可反复使用
- **并发槽位 = 资源管理**：running 占用，idle 释放
- **abort = 打断执行**：不是终止，只是暂停 running loop（后续可继续）
- **reply = 唤醒对话**：让 idle 的 task 继续
- **物理删除会话 → task 消失**：唯一的"终态"

**状态流转**：
```
launch → running (占用槽位)
running → idle (释放槽位，等待 reply)
idle → running (reply 唤醒，重新占用槽位)
running → idle (abort 打断当前 loop，后续可继续)

物理删除会话 → task 消失（唯一终态）
```

### 全局性风险

- 状态机重构影响所有 task 操作，需要全面测试
- 与现有工具（wopal-task-cancel、wopal-task-output）的交互需重新设计

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| Task Manager | `src/simple-task-manager.ts` | 核心状态管理，槽位管理逻辑 |
| Cancel Tool | `src/tools/wopal-task-cancel.ts` | 重命名为 interrupt，去掉终态设置 |
| Output Tool | `src/tools/wopal-task-output.ts` | 去掉 complete action，更新状态显示 |
| Reply Tool | `src/tools/wopal-task-reply.ts` | 允许任何状态，添加唤醒时槽位占用 |
| Tool Registry | `src/index.ts` | 重命名 cancel → interrupt |
| Tests | `src/*.test.ts` | 更新测试用例适配新状态机 |

## In Scope

- [ ] 去掉 complete 工具（wopal_task_output 的 action="complete"）
- [ ] 重命名 cancel → interrupt，只做 abort 不改状态
- [ ] reply 允许任何非 running 状态（只要 task 存在）
- [ ] reply 唤醒时重新占用并发槽位
- [ ] 状态简化：只有 running/idle，去掉 completed/cancelled/error/interrupt 终态
- [ ] 更新所有相关测试

## Out of Scope

- session 物理 deletion 机制（OpenCode 原生功能，暂不实现）
- TTL cleanup 逻辑调整（保留，用于清理长期未活跃的 task）
- shutdown 逻辑调整（暂时保留 interrupt 状态用于优雅关闭）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/simple-task-manager.ts` | 修改 | 去掉 complete/cancel 状态设置，添加 reply 唤醒槽位占用逻辑 |
| `src/tools/wopal-task-cancel.ts` | 重命名+修改 | → `wopal-task-interrupt.ts`，只做 abort 不改状态 |
| `src/tools/wopal-task-output.ts` | 修改 | 去掉 action="complete" 参数，更新状态显示逻辑 |
| `src/tools/wopal-task-reply.ts` | 修改 | 允许任何状态，唤醒时重新 acquire 槽位 |
| `src/index.ts` | 修改 | 重命名 cancel → interrupt |
| `src/simple-task-manager.test.ts` | 修改 | 去掉 complete/cancel 终态测试，添加 interrupt 测试 |
| `src/tools/wopal-task-output.test.ts` | 修改 | 去掉 complete action 测试 |
| `src/tools/wopal-task-reply.test.ts` | 修改 | 添加唤醒槽位占用测试 |

## Implementation

### Task 1: 状态机重构 - simple-task-manager.ts

**Files**: `src/simple-task-manager.ts`

**Changes**:
1. 去掉 `complete()` 方法（第 408-430 行）
2. 修改 `cancel()` → 只做 abort，不改状态为 cancelled
3. 添加 `interrupt()` 方法：abort session，status 保持 running → 等待下一个 idle
4. 修改槽位管理：reply 唤醒时重新 acquire（需要新增方法 `reacquireSlotOnWakeUp`）
5. 去掉 `failTask()` 中的终态检查（第 671 行）

**Verification**: `bun run test:run` 通过

- [x] Step 1: 删除 complete() 方法
- [x] Step 2: 修改 cancel() → 只 abort 不改状态（重命名为 interrupt）
- [x] Step 3: 添加 reacquireSlotOnWakeUp() 方法
- [x] Step 4: 单元测试通过

### Task 2: 工具重构 - cancel → interrupt

**Files**: `src/tools/wopal-task-cancel.ts`, `src/tools/wopal-task-output.ts`, `src/tools/wopal-task-reply.ts`

**Changes**:
1. 重命名 `wopal-task-cancel.ts` → `wopal-task-interrupt.ts`
2. 更新 description："打断当前执行循环，不改状态"
3. `wopal-task-output.ts`: 去掉 action="complete" 参数，去掉 idle 提示中的 complete
4. `wopal-task-reply.ts`: 
   - 修改条件：`task.status !== "running"` 时允许 reply（原条件是 waiting/running）
   - 添加 `reacquireSlotOnWakeUp()` 调用

**Verification**: `bun run test:run` 通过

- [x] Step 1: 重命名 cancel → interrupt
- [x] Step 2: 去掉 output 的 complete action
- [x] Step 3: reply 允许任何状态（非 running）
- [x] Step 4: reply 唤醒时重新占用槽位
- [x] Step 5: 单元测试通过

### Task 3: 更新工具注册和类型定义

**Files**: `src/index.ts`, `src/types.ts`

**Changes**:
1. `index.ts`: 重命名 createWopalCancelTool → createWopalInterruptTool
2. `types.ts`: 去掉 WopalTaskStatus 中的 'completed', 'cancelled', 'error', 'interrupt'

**Verification**: `bun run test:run` 通过

- [x] Step 1: 更新工具注册
- [x] Step 2: 更新类型定义（只保留 pending, running, waiting, error）
- [x] Step 3: 单元测试通过

### Task 4: 测试用例更新

**Files**: `src/simple-task-manager.test.ts`, `src/tools/*.test.ts`

**Changes**:
1. 去掉 complete/cancel 终态相关测试
2. 添加 interrupt 测试：abort 后状态仍为 running
3. 添加 reply 唤醒槽位占用测试
4. 添加永续对话测试：idle → reply → idle → reply 循环

**Verification**: `bun run test:run` 通过

- [x] Step 1: 去掉终态测试
- [x] Step 2: 添加 interrupt 测试（abort 后状态仍为 running）
- [x] Step 3: 添加槽位占用测试
- [x] Step 4: 全部测试通过

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | Wopal | 无 |
| 1 | Task 2 | Wopal | 无 |
| 2 | Task 3 | Wopal | Task 1, Task 2 |
| 2 | Task 4 | Wopal | Task 3 |

## Post-Review Fixes

评审发现 4 个问题，委派 Fae 修复（wopal-task-1776075142165-mzobpg）：

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| 1 | idleNotified 任务 reply 被阻断 | 添加 `!task.idleNotified` 条件 | `wopal-task-reply.ts:88` |
| 2 | markTaskCompletedBySession 与 runtime.ts 重复 | 简化为纯查找方法 | `simple-task-manager.ts:336` |
| 3 | getTaskModelInfo 全量拉取消息 | 添加 `query: { limit: 1 }` | `wopal-task-output.ts:39` |
| 4 | ErrorCategory 含已删除状态 | 添加兼容性注释 | `types.ts:3` |

验证：`bun run build` + `bun run test:run` (396 tests) ✅

### Test Case Design

- **TC1: interrupt 只打断不改状态** — 单元测试 — interrupt 后 status 仍为 running，等待下一个 idle
- **TC2: reply 允许任何状态** — 单元测试 — idle、interrupted、stuck 状态都能 reply
- **TC3: reply 唤醒重新占用槽位** — 单元测试 — 唤醒后 concurrencyKey 被正确设置
- **TC4: 永续对话循环** — 单元测试 — idle → reply → idle → reply 多次循环正常
- **TC5: 去掉 complete action** — 单元测试 — output 不再接受 action="complete"
- **TC6: 并发槽位边界** — 集成测试 — 多个 task idle 时都能释放槽位，唤醒时不超过限制

### Regression Testing

- 现有 reply 功能：正常唤醒 task
- 现有 output 功能：正常显示状态
- 现有 cancel 功能（改为 interrupt）：正常打断执行
- 现有 launch 功能：正常启动 task

### Adjustment Strategy

- 如测试发现槽位边界问题：先实现最简单版本（唤醒时不检查槽位限制），后续迭代优化
- 如 interrupt 后状态管理有问题：保留一个 "interrupted" 状态作为过渡态

## Acceptance Criteria

### Agent Verification

- [x] 代码构建通过：`bun run build` 成功
- [x] 单元测试通过：`bun run test:run` 396 tests 全部通过
- [x] interrupt 后状态检查：不变成终态，保持 running
- [x] reply 唤醒槽位占用：正确 acquire
- [x] output 无 complete action：参数被去掉

### User Validation

- 重启 OpenCode 后 wopal_task 功能正常
- 创建 task → interrupt → reply 循环正常
- 并发槽位管理正常（idle 释放，唤醒占用）
