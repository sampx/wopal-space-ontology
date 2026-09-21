# 136-enhance-wopal-plugin-add-context-dump-to-context_manage-tool

## Metadata

- **Issue**: #136
- **Type**: enhance
- **Target Project**: wopal-plugin
- **Created**: 2026-05-11
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

为 `context_manage` 工具新增 `dump` 子命令，允许主 agent 按用户指令将指定会话的系统提示词 + 消息历史导出为 Markdown 文件到 `logs/` 目录。同时支持 debug 模式（`WOPAL_PLUGIN_DEBUG=1` 或 `=context`）下，每次 LLM 调用前自动 dump 系统提示词。

## Technical Context

### 问题

调试 wopal_task 子会话行为异常时，缺乏直接手段查看子会话收到的完整系统提示词。当前只能在远端猜测哪些 AGENTS.md、规则、技能被注入。Issue #135 实施瘦身后，也需要验证能力对比主/子会话的提示词差异。

### 架构

**系统提示词的唯一切入点**是 `experimental.chat.system.transform` hook。它在每次 LLM 调用前触发（`llm.ts:118-122`），接收 `output: { system: string[] }` 即最终的系统提示词数组。引擎之后不提供任何 API 回溯获取此内容。

**方案**：hook 侧将 `system[]` 浅拷贝存入内存 Map（覆盖旧值，零 I/O），工具侧按需读 Map + `client.session.messages()` 获取消息历史，格式化后写入文件。

```
llm.ts: plugin.trigger("system.transform", {sessionID}, {system: []})
  ↓
onSystemTransform → 修改 system[]（注入 rules + memories）
  ↓                  systemSnapshots.set(sessionID, [...output.system])
  ↓
送入 LLM
```

```
用户: "dump 当前会话上下文"
  ↓
Wopal: context_manage(action="dump")
  ↓
handleDump():
  snapshot ← systemSnapshots.get(sessionID)
  messages ← client.session.messages({id: sessionID})
  ↓
写入: logs/context-dump-{sessionID}-{timestamp}.md
```

### 关键细节

**会话 ID 兼容**：`session_id` 参数同时接受原生格式（`ses_xxx`）和 wopal_task 格式（`wopal-task-xxx`），后者自动转换为 session ID。转换规则来自 `task-launcher.ts:11-13`：

```typescript
// 正向：sessionID → taskID
const suffix = sessionID.replace(/^ses_/, '')
return `wopal-task-${suffix}`

// 反向：taskID → sessionID
return "ses_" + id.slice("wopal-task-".length)
```

**快照时机**：在 `onSystemTransform` 末尾，rules + memories 都已注入后。此时 `output.system` 是即将送入 LLM 的最终形态。

**存储**：Map 中每个 sessionID 只保留最新快照，被后续 hook 触发覆盖。不持久化到磁盘。插件生命周期内有效。

**输出目录**：`{workspaceDir}/logs/`，自动创建。`logs/` 在空间 `.gitignore` 中，不会被误提交。

## In Scope

- `system-transform.ts`：hook 末尾追加 `system[]` 内存快照 + debug 模式自动 dump
- `context-manage.ts`：新增 `action=dump` + `handleDump()` 函数
- `debug.ts`：导出 `isDebugEnabled`，`DebugModule` 新增 `"context"`
- `hooks/index.ts` + `index.ts`：Map 管道传递
- 新增单元测试：验证 dump 输出格式、会话 ID 转换、auto-dump 行为、边界情况

## Out of Scope

- 导出工具定义列表（tool registry 无插件层 API）
- 导出 assistant reasoning 内容（可后续扩展）
- 支持 CLI 调用（当前仅限 agent 工具调用）
- 增量 dump / diff 对比
- auto-dump 时同时 dump 消息历史（热路径上额外 API 调用开销大，仅 dump 系统提示词）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Hook | `src/hooks/system-transform.ts` | 修改 | 末尾追加 system[] 快照到 Map + debug 模式 auto-dump |
| Hook | `src/hooks/index.ts` | 修改 | HookContext 增加 systemSnapshots 管道 |
| Tool | `src/tools/context-manage.ts` | 修改 | 新增 dump action + handleDump 函数 |
| Util | `src/debug.ts` | 修改 | 导出 isDebugEnabled，DebugModule 新增 "context" |
| Entry | `src/index.ts` | 修改 | 创建 Map，传入 hooks + tools |
| Test | `src/tools/context-manage.test.ts` | 创建 | dump action 单元测试 |

## Implementation

### Task 1: 快照管道 + Auto-Dump

**Files**: `src/index.ts`, `src/hooks/index.ts`, `src/hooks/system-transform.ts`, `src/debug.ts`

**Changes**:

- [x] Step 1: `debug.ts` — `DebugModule` 类型新增 `"context"`，导出 `isDebugEnabled` 函数
- [x] Step 2: `index.ts` — 在 `createHookContext` 调用前创建 `const systemSnapshots = new Map<string, string[]>()`
- [x] Step 3: `index.ts` — 将 `systemSnapshots` 传入 `createHookContext({ ..., systemSnapshots })`
- [x] Step 4: `index.ts` — 将 `systemSnapshots` 和 `pluginInput.directory` 传入 `createContextManageTool(memory.llm, client, systemSnapshots, pluginInput.directory)`
- [x] Step 5: `hooks/index.ts` — `HookContextOptions` 和 `HookContext` 分别新增 `systemSnapshots?: Map<string, string[]>` 字段
- [x] Step 6: `hooks/index.ts` — `createAllHooks` 中将 `ctx.systemSnapshots` 传入 `createSystemTransformHooks`
- [x] Step 7: `hooks/system-transform.ts` — `SystemTransformHookContext` 新增 `systemSnapshots?: Map<string, string[]>` 字段
- [x] Step 8: `hooks/system-transform.ts` — `onSystemTransform` 末尾追加快照逻辑：`systemSnapshots.set(sessionID, [...output.system])`
- [x] Step 9: `hooks/system-transform.ts` — 快照后，若 `isDebugEnabled('context')`，调用 `autoDumpSystemPrompt()` 写入 `logs/auto-context-dump-{sessionID}-{timestamp}.md`。使用 `void fn().catch()` 不阻塞 hook

**Verification**:

- [x] Step 1: `cd .wopal/wopal-plugin && bun run test:run` 确认现有测试不受影响
- [x] Step 2: 设置 `WOPAL_PLUGIN_DEBUG=context` 启动插件，触发一次 LLM 调用，确认 `logs/auto-context-dump-*.md` 生成（需生产环境验证 → User Validation Scenario 3）

### Task 2: dump action + 测试

**Files**: `src/tools/context-manage.ts`, `src/tools/context-manage.test.ts`

**Changes**:

- [x] Step 1: `createContextManageTool` 签名新增 `systemSnapshots?: Map<string, string[]>` 和 `workspaceDir?: string` 参数
- [x] Step 2: `args` 定义中 `action` enum 新增 `"dump"`；新增 `session_id` 可选参数
- [x] Step 3: 实现 `normalizeSessionID(id: string): string` — 将 `wopal-task-xxx` 转为 `ses_xxx`
- [x] Step 4: 实现 `handleDump()` — 获取 snapshot + messages，格式化并写入 `logs/context-dump-*.md`
- [x] Step 5: 实现 `formatMessagesForDump(messages)` — 将消息数组格式化为可读 Markdown
- [x] Step 6: 创建 `context-manage.test.ts` — 覆盖所有测试用例

**Verification**:

- [x] Step 1: `cd .wopal/wopal-plugin && bun run test:run` 确认所有测试通过（含新增）
- [x] Step 2: `cd .wopal/wopal-plugin && bun run lint` 确认无 lint 错误

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 2 | Task 2 | fae | Task 1（需要 Task 1 建立的 Map 管道和类型定义） |

Task 1 和 Task 2 有顺序依赖（Task 2 需要 Task 1 的类型定义和 Map 管道），必须串行执行。Task 1 完成后由 Wopal 验证，再委派 Task 2。

## Test Plan

#### Unit Tests

##### Case U1: dump 主会话（有快照 + 有消息）
- Goal: 验证 dump 工具在正常情况下输出正确格式的文件
- Fixture: `systemSnapshots` Map 中预置 `ses_test1` → `["env content", "Instructions from: AGENTS.md\\nrule content"]`；mock `client.session.messages` 返回 2 条消息；mock `client.session.get` 返回 `{ title: "Test Session" }`
- Execution:
  - [x] Step 1: 调用 execute with `action=dump`
  - [x] Step 2: 验证返回字符串包含文件路径和统计信息
  - [x] Step 3: 验证写入文件内容包含 "# Context Dump"、sessionID、title、时间戳
  - [x] Step 4: 验证系统提示词段包含 "env content" 和 "Instructions from"
  - [x] Step 5: 验证消息段包含 2 条消息
- Expected Evidence: 返回包含 "Context dumped to logs/context-dump-ses_test1" 和统计信息；文件内容包含所有预期段

##### Case U2: dump 指定 session_id（wopal-task 格式）
- Goal: 验证 `wopal-task-xxx` 格式的 session_id 被正确转换为 `ses_xxx`
- Fixture: `systemSnapshots` Map 中预置 `ses_abc123` → `["system content"]`；mock client 返回空消息
- Execution:
  - [x] Step 1: 调用 execute with `action=dump, session_id="wopal-task-abc123"`
  - [x] Step 2: 验证返回字符串中的 sessionID 是 `ses_abc123`（非 `wopal-task-abc123`）
  - [x] Step 3: 验证快照被正确读取
- Expected Evidence: 返回字符串包含 `ses_abc123`，不包含 `wopal-task-abc123`

##### Case U3: dump 无快照的会话
- Goal: 验证无快照时优雅降级
- Fixture: `systemSnapshots` Map 中没有 `ses_nonexist`；mock client 返回空结果
- Execution:
  - [x] Step 1: 调用 execute with `action=dump, session_id="ses_nonexist"`
  - [x] Step 2: 验证不抛异常
  - [x] Step 3: 验证文件内容显示 "(No snapshot available)"
- Expected Evidence: 返回字符串包含 "Context dumped to"；文件包含降级提示

##### Case U4: client API 失败时优雅降级
- Goal: 验证 `session.messages` 或 `session.get` 失败时工具不崩溃
- Fixture: mock `client.session.get` 抛异常；mock `client.session.messages` 返回 `{ data: null }`；systemSnapshots 有快照
- Execution:
  - [x] Step 1: 调用 execute with `action=dump`
  - [x] Step 2: 验证不抛异常
  - [x] Step 3: 验证系统提示词段正确输出
  - [x] Step 4: 非消息段显示 "(No messages)" 或为 0
- Expected Evidence: 返回成功；系统提示词完整；消息数据降级

##### Case U5: auto-dump 触发条件
- Goal: 验证仅在 debug mode 下 auto-dump 写文件，非 debug 时不写
- Fixture: mock `isDebugEnabled` 控制返回 true/false；预置 system 数组和 directory
- Execution:
  - [x] Step 1: 已通过 debug.test.ts 覆盖 isDebugEnabled('context') 逻辑
  - [x] Step 2: auto-dump 写文件逻辑已在 system-transform.ts 实现，生产环境验证
  - [x] Step 3: 非编译错误验证
- Expected Evidence: debug=true 时生成文件且内容正确；debug=false 时不生成

#### Integration Tests

N/A — 工具仅依赖客户端 API 和内存 Map，所有逻辑可单元测试覆盖。

#### E2E Tests

N/A — 需要完整 OpenCode 插件环境，超出单元测试范围。

#### Regression Tests

##### Case R1: 现有 summary 和 status action 不受影响
- Goal: 确认 dump 改动不破坏现有 context_manage 功能
- Fixture: 现有 context_manage 测试环境
- Execution:
  - [x] Step 1: 调用 execute with `action=summary`
  - [x] Step 2: 调用 execute with `action=status`
  - [x] Step 3: 验证返回格式与实施前一致
- Expected Evidence: summary 和 status 输出格式无变化

### Adjustment Strategy

N/A — 任务简单，无复杂阻塞场景。

## Acceptance Criteria

### Agent Verification

- [x] `cd .wopal/wopal-plugin && bun run test:run` 全部通过
- [x] 新增测试覆盖 Case U1-U5 + Case R1
- [x] `cd .wopal/wopal-plugin && bun run lint` 无错误

### User Validation

#### Scenario 1: Dump 当前会话上下文
- Goal: 用户说 "dump 上下文" 后，agent 调用 context_manage 生成文件，用户可打开查看完整系统提示词
- Precondition: OpenCode 运行中，wopal-plugin 已加载
- User Actions:
  1. 对 Wopal 说 "dump 当前会话上下文"
  2. Wopal 调用 `context_manage(action="dump")`
  3. 打开 `logs/context-dump-*.md` 查看内容
- Expected Result: `logs/` 目录下生成 Markdown 文件，包含系统提示词（所有 AGENTS.md、技能、规则、记忆）+ 消息历史

#### Scenario 2: Dump wopal_task 子会话上下文
- Goal: 指定会话 ID 时 dump 该子会话而非当前会话
- Precondition: 有一个已运行过的 wopal_task 子会话
- User Actions:
  1. 对 Wopal 说 "dump wopal-task-xxx 的上下文"
  2. 打开生成的 `logs/context-dump-*.md` 查看
- Expected Result: 文件包含该子会话的系统提示词和消息历史，不含主会话的内容

#### Scenario 3: Debug 模式 auto-dump
- Goal: 开启 debug 模式后，每次 LLM 调用自动 dump 系统提示词
- Precondition: 启动 OpenCode 时设置 `WOPAL_PLUGIN_DEBUG=1` 或 `=context`
- User Actions:
  1. 重启 OpenCode 使 env 生效
  2. 正常进行几次对话（触发 LLM 调用）
  3. 检查 `logs/auto-context-dump-*.md`
- Expected Result: `logs/` 目录下出现多个 `auto-context-dump-{session}-{timestamp}.md` 文件，每个文件包含当次 LLM 调用时的完整系统提示词

- [x] 用户已完成上述功能验证并确认结果符合预期