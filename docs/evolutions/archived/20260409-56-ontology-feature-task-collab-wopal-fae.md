# ontology-feature-task-collab-wopal-fae

## Metadata

- **Issue**: #56
- **Type**: feature
- **Target Project**: ontology
- **Created**: 2026-04-07
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 Wopal-Fae 任务委派的异常检测从"三层冗余机制"简化为"统一 ticker 心跳 + 异常检测"，并将 idle 判断权从程序交给 Wopal，消除正则猜测，让有推理能力的 agent 做最终判断。

## Technical Context

### Phase 1 已完成

已将 timeout/stale 从硬杀改为通知，cancel 放宽，reply 全状态支持。具体：
- cancel 放宽到所有非终态（running/waiting/pending/completed/error）
- reply 仅拒绝 cancelled/interrupt，completed/error 可回复并 revert to running
- 并发槽优化（waiting 释放，reply 重获取）
- wopal_task 移除 timeout/staleTimeout 参数

### Phase 2 已完成

移除 timeout timer + stale detector，将 loop 检测集成到 ticker，通知从 9 种简化到 7 种。

### Phase 3 待实施：IDLE 通知 — 判断权交给 Wopal

**问题**：Issue #69 移除了 `detectQuestionPattern`（文本提问正则检测），导致 `diagnoseIdle` 只返回 `completed | error`，永远不返回 `waiting`。`runtime.ts:851` 的 `verdict === 'waiting'` 分支是死代码。WAITING 通知的唯一触发路径是 fae 主动使用 question tool（`question.asked` 事件），但 fae 是否使用 question tool 取决于大模型当时的选择，不确定。

**设计原则**：无论 fae 以什么方式结束（完成、提问、卡住、死循环），程序只负责通知，Wopal 负责判断。不依赖正则猜测。

**目标架构**：

```
session.idle
  → diagnoseIdle（只检测 error）
  → verdict=error → markTaskErrorBySession + ERROR 通知
  → verdict=completed → 设 idleNotified 标记 + IDLE 通知
                        任务保持 running，不自动 completed

Wopal 收到 IDLE 通知
  → wopal_output 查看 fae 最后的 reasoning/text
  → 自行判断：
     ├─ 正常完成 → wopal_cancel 关闭任务
     ├─ 提问了   → wopal_reply 回答，fae 继续
     ├─ 出错了   → wopal_cancel 关闭
     └─ 不确定   → 继续等待

question.asked 事件（fae 使用 question tool）
  → question-relay.ts → WAITING 通知（保留，不变）

ticker (30s interval)
  ├── 跳过 idleNotified 任务（不检查 stuck/progress）
  ├── checkStuckTasks → [WOPAL TASK STUCK]
  ├── clearStuckState
  └── checkProgressNotifications → [WOPAL TASK PROGRESS]
```

**通知体系最终形态**：

| 通知 | 触发 | 性质 |
|------|------|------|
| `[WOPAL TASK IDLE]` | 子会话 idle（新增） | 等待 Wopal 判断 |
| `[WOPAL TASK ERROR]` | session.error / diagnoseIdle=error | 状态变更 |
| `[WOPAL TASK WAITING]` | question tool 事件 | 事件中继 |
| `[WOPAL TASK QUESTION]` | question tool 事件 | 事件中继 |
| `[WOPAL TASK PERMISSION]` | permission.asked 事件 | 事件中继 |
| `[WOPAL TASK PROGRESS]` | ticker 心跳 | 心跳 |
| `[WOPAL TASK STUCK]` | ticker 检测（跳过 idle 任务） | 异常 |

共 7 种通知。`[WOPAL TASK COMPLETED]` 不再由程序自动发出（Wopal 通过 wopal_cancel 关闭完成的任务）。

**退出安全**：`process-cleanup.ts` 已实现 SIGINT/beforeExit 信号处理，自动调用 `SimpleTaskManager.shutdown()` 清理活跃任务，不阻塞 OpenCode 退出。

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| 类型定义 | `plugins/rules-plugin/src/types.ts` | Phase 2: 删除 timeout/stale 字段; Phase 3: 新增 idleNotified |
| 任务管理器 | `plugins/rules-plugin/src/simple-task-manager.ts` | Phase 2: 删 timeout/stale, 集成 loop; Phase 3: idle 跳过 stuck/progress |
| 运行时 | `plugins/rules-plugin/src/runtime.ts:834-865` | Phase 3: session.idle 改为发 IDLE 通知，移除 WAITING 死代码分支 |
| Idle 诊断 | `plugins/rules-plugin/src/idle-diagnostic.ts` | 无变更（verdict 语义不变，handler 层改变行为） |
| 问题中继 | `plugins/rules-plugin/src/question-relay.ts` | 不变（question tool → WAITING 路径保留） |
| Stuck 检测 | `plugins/rules-plugin/src/stuck-detector.ts` | 保持（Phase 3: 跳过 idle 任务） |
| Loop 检测 | `plugins/rules-plugin/src/loop-detector.ts` | 保持（Phase 3: 跳过 idle 任务） |
| 回复工具 | `plugins/rules-plugin/src/tools/wopal-reply.ts` | Phase 2: 移除 rescheduleTimeout; Phase 3: 清除 idleNotified |
| 输出工具 | `plugins/rules-plugin/src/tools/wopal-output.ts` | Phase 2: 移除 detectLoop; Phase 3: 显示 idle 状态 |
| 协作技能 | `agents/wopal/skills/fae-collab/SKILL.md` | 通知表更新 |
| Stale 检测 | `plugins/rules-plugin/src/stale-detector.ts` | **Phase 2 已删除** |
| Runtime 删除 | `plugins/rules-plugin/src/runtime.ts:851-856` | `verdict === 'waiting'` 分支 — 死代码，已删除 |
| Runtime 删除 | `plugins/rules-plugin/src/runtime.ts:968-995` | `notifyParentWaiting` 方法 — 已删除 |
| Runtime 新增 | `plugins/rules-plugin/src/runtime.ts` | 新增 `notifyParentIdle` 方法 — 发送 IDLE 通知 |

## In Scope

### Phase 2（已完成）
- [x] 删除 stale-detector.ts 及相关测试
- [x] 删除 timeout timer 机制（scheduleTimeoutCheck, clearTimeoutTimer, timeoutTimers map）
- [x] 删除 notifyParentTimeout, notifyParentStale, rescheduleTimeout 方法
- [x] 清理 types.ts 中 timeout/stale 字段
- [x] 将 detectLoop 集成到 ticker（checkStuckTasks 中调用）
- [x] 从 wopal-output.ts 移除 detectLoop 调用
- [x] 从 wopal-reply.ts 移除 rescheduleTimeout 调用
- [x] 简化 ticker：合并 stale check + stuck check + loop check + progress
- [x] 更新 SKILL.md 通知表
- [x] 更新/删除相关测试

### Phase 3（待实施）
- [ ] types.ts 新增 `idleNotified` 字段
- [ ] runtime.ts session.idle handler：verdict=completed → 设 idleNotified + 发 IDLE 通知
- [ ] runtime.ts 移除 `verdict === 'waiting'` 死代码分支和 `notifyParentWaiting` 方法
- [ ] simple-task-manager.ts ticker：跳过 idleNotified 任务的 stuck/progress 检测
- [ ] wopal-reply.ts：reply 时清除 idleNotified
- [ ] wopal-output.ts：显示 idle 状态
- [ ] 更新测试
- [ ] 更新 SKILL.md 和 AGENTS.md

## Out of Scope

- SimpleTaskManager 拆分重构（独立 Issue）
- 兜底 TTL 配置化（当前 cleanup 已有 TTL 逻辑）
- progress-analyzer / progress-tracker 重构

## Files

### Phase 2（已完成）

| 文件 | 操作 | 说明 |
|------|------|------|
| `plugins/rules-plugin/src/stale-detector.ts` | 删除 | stale 检测与 stuck 重叠 |
| `plugins/rules-plugin/src/stale-detector.test.ts` | 删除 | 对应测试 |
| `plugins/rules-plugin/src/types.ts` | 修改 | 删 timeout/stale 字段和 LaunchInput 参数 |
| `plugins/rules-plugin/src/simple-task-manager.ts` | 修改 | 删 timeout/stale 逻辑，简化 ticker，集成 loop |
| `plugins/rules-plugin/src/tools/wopal-reply.ts` | 修改 | 移除 rescheduleTimeout 调用 |
| `plugins/rules-plugin/src/tools/wopal-output.ts` | 修改 | 移除 detectLoop 调用 |
| `agents/wopal/skills/fae-collab/SKILL.md` | 修改 | 通知表简化 |

### Phase 3（待实施）

| 文件 | 操作 | 说明 |
|------|------|------|
| `plugins/rules-plugin/src/types.ts` | 修改 | 新增 `idleNotified` 字段 |
| `plugins/rules-plugin/src/runtime.ts` | 修改 | session.idle 改发 IDLE 通知，删死代码 |
| `plugins/rules-plugin/src/simple-task-manager.ts` | 修改 | ticker 跳过 idle 任务 |
| `plugins/rules-plugin/src/tools/wopal-reply.ts` | 修改 | reply 清除 idleNotified |
| `plugins/rules-plugin/src/tools/wopal-output.ts` | 修改 | 显示 idle 状态 |
| `agents/wopal/skills/fae-collab/SKILL.md` | 修改 | IDLE 通知说明 |
| `plugins/rules-plugin/AGENTS.md` | 修改 | idle 机制描述 |

全局风险：
- ticker 中拉取消息检测 loop 增加开销（低）— 仅对 running 任务检测，复用已有 progress 通知消息拉取
- loop 检测在 ticker 中有 30s 延迟（低）— 30s 延迟可接受，Wopal 也可随时用 wopal_output 手动检查
- idle 任务占用并发槽（中）— Wopal 收到 IDLE 通知后应尽快处理（cancel 或 reply）
- Wopal 不响应 IDLE 通知时任务永远挂着（低）— process-cleanup 确保 OpenCode 退出时清理

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 10 (types.ts) | Wopal | 无 |
| 2 | Task 11 (runtime.ts) + Task 12 (ticker) + Task 13 (reply) + Task 14 (output) | fae | Task 10 |
| 3 | Task 15 (tests) | fae | Task 11-14 |
| 4 | Task 16 (docs) | Wopal | Task 15 |

## Acceptance Criteria

### Agent Verification

Phase 2:
- [x] `stale-detector.ts` 已删除，无残留引用
- [x] timeout timer 机制已删除（scheduleTimeoutCheck, timeoutTimers map）
- [x] types.ts 中无 timeout/stale 字段
- [x] ticker 中 loop 检测正常工作（自动检测 tool_loop / rapid_cycle）
- [x] wopal-output.ts 不再调用 detectLoop
- [x] wopal-reply.ts 不再调用 rescheduleTimeout
- [x] `bun run test:run` 全部通过（384/384）
- [x] fae-collab SKILL.md 已更新

Phase 3:
- [x] session.idle 不再自动 markTaskCompleted，改为发 IDLE 通知
- [x] `verdict === 'waiting'` 死代码和 `notifyParentWaiting` 已删除
- [x] types.ts 包含 `idleNotified` 字段
- [x] ticker 跳过 idleNotified 任务的 stuck/progress 检测
- [x] wopal-reply 清除 idleNotified
- [x] wopal-output 显示 idle 状态
- [x] `bun run test:run` 全部通过

### User Validation
- fae 正常完成 → 收到 IDLE 通知 → Wopal 检查后 cancel
- fae 文本提问 → 收到 IDLE 通知 → Wopal 检查后 reply
- fae question tool → WAITING/QUESTION 通知正常
- idle 任务不触发 STUCK 通知
