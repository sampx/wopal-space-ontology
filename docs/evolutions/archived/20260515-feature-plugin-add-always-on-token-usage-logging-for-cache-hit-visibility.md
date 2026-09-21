# feature-plugin-add-always-on-token-usage-logging-for-cache-hit-visibility

## Metadata

- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-14
- **Status**: done
- **Worktree**: add-always-on-token-usage-logging-for-cache-hit-visibility | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-add-always-on-token-usage-logging-for-cache-hit-visibility

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

每次 LLM 调用完成后自动打印 token 用量信息（input/output/cache_read/cache_write），无需任何环境变量开关，让用户直观看到缓存命中情况。

## Technical Context

ellamaka 的 `processor.ts` 已完整计算 token usage（含 `cache.read`/`cache.write`），通过 `session.updatePart({ type: "step-finish", tokens: ... })` 写入消息流。插件通过 `message.part.updated` 事件可获取完整的 `StepFinishPart` 数据（含 `tokens.cache.read`）。

当前 wopal-plugin 的 debug 日志全部需要 `WOPAL_PLUGIN_DEBUG` 开关。`debug.ts` 仅有 `createDebugLog`（需开关）和 `createWarnLog`（始终输出但带 `[WARN]` 标记）。缺少一个"始终输出、无标记"的普通日志函数。

**设计决策**：新增 `createInfoLog` 函数，与 `createWarnLog` 同级但无 `[WARN]` 标记。token 日志通过 `createInfoLog("[tokens]")` 始终输出到日志文件。

## In Scope

- 在 `debug.ts` 新增 `createInfoLog` 函数（始终输出、无标记）
- 在 `event-router.ts` 的 `message.part.updated` 处理中对 `step-finish` part 打印 token 信息
- 配套单元测试

## Out of Scope

- TUI 状态栏显示缓存信息（需改 ellamaka 源码）
- 日志控制开关（本次目标就是无需开关）
- 历史 token 统计（已有 `ellamaka stats` 命令）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| debug | `.wopal/wopal-plugin/src/debug.ts` | 修改 | 新增 `createInfoLog` 函数 |
| hooks | `.wopal/wopal-plugin/src/hooks/event-router.ts` | 修改 | 在 `step-finish` 时调用 `infoLog` 打印 token |
| test | `.wopal/wopal-plugin/src/debug.test.ts` | 修改 | 新增 `createInfoLog` 的单元测试 |

## Implementation

### Task 1: Add `createInfoLog` to debug.ts

**Files**: `.wopal/wopal-plugin/src/debug.ts`

**Changes**:

- [x] Step 1: 在 `createWarnLog` 函数之后添加 `createInfoLog` 函数，参照 `createWarnLog` 实现但无 `[WARN]` 标记
- [x] Step 2: 验证 TypeScript 编译通过

**Verification**:

- [x] Step 1: 运行 `bun run build` 确认编译通过
- [x] Step 2: 运行 `bun run test:run` 确认全部测试通过

### Task 2: Add token usage logging to event-router.ts

**Files**: `.wopal/wopal-plugin/src/hooks/event-router.ts`

**Changes**:

- [x] Step 1: 在 `message.part.updated` 处理逻辑中，对所有 `part.type === "step-finish"` 事件提取 `part.tokens` 并通过 `infoLog("[tokens]")` 打印
- [x] Step 2: 日志格式：`<sessionID前8位> tokens: input=<N> output=<N> cache_read=<N> cache_write=<N>`

**Verification**:

- [x] Step 1: 运行 `bun run build` 确认编译通过
- [x] Step 2: 运行 `bun run test:run` 确认全部测试通过

## Delegation Strategy

N/A — 单一任务，无需并行委派

## Test Plan

#### Unit Tests

##### Case U1: createInfoLog always writes to log file
- Goal: 确认 `createInfoLog` 不需要 `WOPAL_PLUGIN_DEBUG` 也能写入日志
- Fixture: 未设置 `WOPAL_PLUGIN_DEBUG` 环境变量
- Execution:
  - [x] Step 1: 调用 `createInfoLog("[test]")("hello")`
  - [x] Step 2: 读取日志文件，确认包含 `[test] hello`
- Expected Evidence: 日志文件包含 `[test] hello`，且无 `[WARN]` 标记

##### Case U2: createInfoLog does not include [WARN] suffix
- Goal: 确认 `createInfoLog` 输出不含 `[WARN]` 标记
- Fixture: 同 U1
- Execution:
  - [x] Step 1: 对比 `createInfoLog` 和 `createWarnLog` 的输出
  - [x] Step 2: 确认前者无 `[WARN]`，后者有 `[WARN]`
- Expected Evidence: `createInfoLog` 输出格式为 `[prefix] message`，`createWarnLog` 为 `[prefix] [WARN] message`

#### Integration Tests

##### Case I1: step-finish event triggers token logging
- Goal: 确认 `message.part.updated` 事件携带 `step-finish` part 时产生 token 日志
- Fixture: 模拟 `message.part.updated` 事件，part 包含 `step-finish` 类型 + tokens 数据
- Execution:
  - [x] Step 1: 调用 `onEvent` 传入 `step-finish` part 事件
  - [x] Step 2: 读取日志文件，确认包含 token 信息
- Expected Evidence: 日志文件包含 `tokens: input=` 格式的输出

#### Regression Tests

##### Case R1: Existing debug/warn logging unchanged
- Goal: 确认 `createDebugLog` 和 `createWarnLog` 行为不变
- Fixture: 运行现有 debug.test.ts
- Execution:
  - [x] Step 1: 运行 `bun run test:run`
  - [x] Step 2: 确认全部测试通过（含已有的 debug test）
- Expected Evidence: 全部测试通过，无回归

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 全部测试通过
- [x] 新增 `createInfoLog` 在任何环境下都能写入日志（不依赖 `WOPAL_PLUGIN_DEBUG`）

### User Validation

#### Scenario 1: 启动 ellamaka 后发送请求，日志文件自动记录 token 信息
- Goal: 确认无需设置任何环境变量，每次 LLM 调用后日志文件都会记录 token 用量
- Precondition: 正常启动 ellamaka（不设 `WOPAL_PLUGIN_DEBUG`）
- User Actions:
  1. 启动 ellamaka，发送一条对话
  2. 打开 `logs/wopal-plugins-debug.log`
  3. 查看是否有 `[tokens]` 开头的日志行
- Expected Result: 日志文件中出现类似 `ses_1db872a8dffe(main) tokens: input=500 output=200 cache_read=4500 cache_write=0 model=wopal-ai/glm-5.1` 的行

- [x] 用户已完成上述功能验证并确认结果符合预期

## Actual Implementation Notes

实际实现超出原始 Scope，新增以下增强：

- **模型信息**：日志格式增加 `model=<provider>/<model>`，通过 `getSessionModelInfo` 从会话消息中获取真实模型
- **会话角色标识**：日志格式增加 `(main/task)` 标识，区分主会话和子任务
- **16 位 sessionID**：前缀从 8 位扩展到 16 位，避免短时间内创建的会话前缀碰撞
- **Task Recovery 修复**：`recoverFromSession` 方法已定义但从未被调用，已修复为首次主会话事件触发恢复
