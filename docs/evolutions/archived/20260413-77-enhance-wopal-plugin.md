# 77-enhance-wopal-plugin

## Metadata

- **Issue**: #77
- **Type**: enhance
- **Target Project**: ontology
- **Created**: 2026-04-11
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

优化任务监控与通知机制：消息拉取效率、progress 通知触发主 agent、tick 日志增强、上下文使用率显示。

## Technical Context

**现状问题**：

1. **消息拉取效率**：`diagnoseIdleSession` 拉取子会话全部消息，但诊断只需要最后一条 assistant。SDK 已支持 `query.limit` 参数。

2. **progress 通知静默**：`sendProgressNotification` 使用 `noReply: true`，只静默注入 `<system-reminder>`，不触发主 agent 响应。与 idle/stuck 通知行为不一致。

3. **tick 无日志**：每 30 秒执行 `checkProgressNotifications`，但没有任何日志输出，用户无法感知系统运行状态。

4. **上下文使用率缺失**：Wopal 无法感知 fae 的 token 消耗，不知道是否接近上下文窗口上限。`AssistantMessage.tokens` 已有完整数据。

**技术基础**：

- SDK `SessionMessagesData.query.limit` 参数支持（见 `types.gen.ts:3607`）
- `AssistantMessage.tokens` 结构：`{ input, output, reasoning, cache.read, cache.write }`
- Model 限制可通过 `client.config.providers()` → `model.limit.context` 获取
- `notifyParent` 已有正确实现（`noReply: false`），可作为 progress 通知的参考模板

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| task manager | `src/simple-task-manager.ts:88-93, 454-512` | tick 日志 + progress 通知改造 |
| runtime | `src/runtime.ts:941-958` | diagnoseIdleSession 消息拉取优化 |
| task output | `src/tools/wopal-task-output.ts:168-218` | summary 模式增加上下文使用率 |

## In Scope

- [x] Task 1：diagnoseIdleSession 使用 `query.limit: 10` 优化消息拉取
- [x] Task 2：progress 通知改为触发主 agent（与 idle/stuck 一致）
- [x] Task 3：tick 执行时输出状态日志（running tasks、检查结果）
- [x] Task 4：wopal_output summary 模式显示上下文使用率（>45% 警告）

## Out of Scope

- Task Store 持久化（Issue 明确排除）
- 其他 session.messages 调用点优化（wopal_output section 模式等）
- stuck 检测逻辑修改
- progress 通知阈值调整（保持 20 条消息 / 3 分钟）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/simple-task-manager.ts` | 修改 | tick 日志 + progress 通知改用 notifyParent 模式 |
| `src/runtime.ts` | 修改 | diagnoseIdleSession 增加 `query.limit: 10` |
| `src/tools/wopal-task-output.ts` | 修改 | summary 模式增加上下文使用率 |

## Implementation

### Task 1: diagnoseIdleSession 消息拉取优化

**Files**: `src/runtime.ts:941-958`

**Changes**:
1. `client.session.messages` 调用增加 `query: { limit: 10 }` 参数
2. 添加日志输出消息数量和结果

**Verification**: `bun run test:run`

### Task 2: progress 通知改为触发主 agent

**Files**: `src/simple-task-manager.ts:490-512`

**Changes**:
1. 删除 `sendProgressNotification` 方法中的 `<system-reminder>` 包装和 `synthetic: true`
2. 改用 `noReply: false`（与 `notifyParent` 一致）
3. 通知格式改为 `[WOPAL TASK PROGRESS]`（与其他通知风格统一）
4. 添加日志：发送成功时打印 taskId 和 messages 数量

**对比**：
```typescript
// 当前（静默）
parts: [{ type: "text", text: notification, synthetic: true }]
noReply: true

// 改为（触发主 agent）
parts: [{ type: "text", text: notification }]
noReply: false
```

**Verification**: `bun run test:run` + E2E 验证 progress 通知触发主 agent

### Task 3: tick 执行时输出状态日志

**Files**: `src/simple-task-manager.ts:88-93`

**Changes**:
1. ticker 执行时汇总所有 running 任务的状态，输出一条日志
2. 每个 running 任务显示：ID（缩写）、description、消息增量、耗时、是否触发通知
3. 无 running 任务时不输出（避免噪音）

**日志格式**：
```
[tick] 3 tasks:
  [1] wopal-task-abc "defer fae task": +15 msgs, 0m15s ✓notified
  [2] wopal-task-def "analyze codebase": 12 msgs, 1m15s
  [3] wopal-task-ghi "write tests": +18 msgs, 5m08s
```

**字段说明**：
- `+15 msgs`：距上次通知的新增消息数（从未通知过则显示总量，不带 `+`）
- `0m15s`：距上次通知的耗时（从未通知过则从 `startedAt` 算起）
- `✓notified`：本次 tick 触发了 progress 通知（仅通知时显示）

**Verification**: 设置 `WOPAL_PLUGIN_DEBUG=task`，观察日志输出

### Task 4: wopal_output summary 模式增加上下文使用率

**Files**: `src/tools/wopal-task-output.ts`

**Changes**:
1. 在 `running` 状态的 progress 输出中，获取最后一条 assistant 消息的 tokens
2. 通过 `client.config.providers()` 获取 model 的 `limit.context`
3. 计算使用率 `usage = (input + cache.read) / limit.context`
4. 显示格式：`Context: 35% used (70K/200K)`
5. usage > 45% 时添加 `⚠️` 警告标记

**Verification**: `bun run test:run` + E2E 验证使用率显示

## Delegation Strategy

N/A — 4 个任务均为简单修改（<50 行），改动量小，Wopal 直接执行效率更高。

## Test Plan

### Test Case Design

- Task 1：单元测试验证 `query.limit` 参数传递
  - mock `client.session.messages` 调用，检查参数包含 `query: { limit: 10 }`

- Task 2：单元测试验证 `noReply: false` + 日志输出
  - mock `client.session.promptAsync` 调用，检查 `noReply: false`
  - mock debugLog，验证日志输出包含 taskId 和 messages 数量

- Task 3：单元测试验证 tick 日志输出
  - mock debugLog 函数，验证有 running 任务时输出 `[tick] N tasks:` 格式
  - 验证每个任务显示：ID、description、消息增量（`+N` 或总量）、耗时、`✓notified` 标记
  - 验证无 running 任务时不输出

- Task 4：单元测试验证上下文使用率计算
  - mock tokens 和 model.limit，验证 usage = (input + cache.read) / limit.context
  - 验证 >45% 时返回警告标记

### Regression Testing

- 现有测试全部通过：`bun run test:run`
- runtime.events.test.ts 验证 idle 通知不受影响
- stuck 检测逻辑不受影响

### Adjustment Strategy

- providers API 不可用 → 降级处理，不显示上下文使用率
- tokens 字段不存在 → 降级处理，跳过使用率计算

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 构建通过
- [x] `bun run test:run` 单元测试通过
- [x] TypeScript 类型检查通过

### User Validation

- E2E 验证：progress 通知触发主 agent 响应（非静默注入）
- E2E 验证：tick 日志可见（设置 `WOPAL_PLUGIN_DEBUG=task`）
- E2E 验证：上下文使用率正确显示（>45% 有警告）