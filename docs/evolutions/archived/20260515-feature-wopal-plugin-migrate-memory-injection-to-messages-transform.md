# feature-wopal-plugin-migrate-memory-injection-to-messages-transform

## Metadata

- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-14
- **Status**: done
- **Worktree**: plugin-migrate-memory-injection-to-messages-transform | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-plugin-migrate-memory-injection-to-messages-transform
- **Prerequisite**: Plan #139（Rules 注入迁移）已完成

## Scope Assessment

- **Complexity**: Medium — 多文件改动（4 文件修改 + 1 新建），逻辑清晰但 Memory 注入有子会话检测/timeout/enriched query 等复杂路径
- **Confidence**: High — #139 已验证相同模式，enriched query 数据来源切换已有 precedent

## Goal

将 Memory 注入从 system.transform 移到 messages.transform，使 system prompt 仅保留 OpenCode 原始内容（agent.prompt + system + user.system），实现近 100% cache hit。

## Technical Context

### 为什么需要迁移

#139 把 Rules 注入移到 messages.transform 后，system prompt Part 2 只剩 Memory。Memory 每次触发会改变 Part 2 内容 → cache miss。将 Memory 也移到 messages.transform 后，system prompt 完全稳定不变。

### 前置依赖

#139 已完成，产出了 `rule-message-injector.ts` 和 messages.transform 薄壳调度模式。本次复用该模式，第三个注入器遵循相同结构。

### 架构变迁

**Before（#139 完成后，当前状态）**：

```
system.transform（system-transform.ts）
  ├─ Memory 注入   → output.system.push(memoryText)      ← 唯一动态内容，破坏 cache
  └─ snapshot/dump + isChildSession（auto-dump 前缀）

messages.transform（message-hooks.ts）
  ├─ seed context
  ├─ injectSkillReload(...)       → skill-reload-injector.ts
  ├─ injectRulesToMessage(...)    → rule-message-injector.ts
  └─ store transformedMessagesMap
```

**After（本次完成后）**：

```
system.transform（system-transform.ts）
  └─ snapshot/dump + isChildSession（auto-dump 前缀）    ← 纯基础设施

messages.transform（message-hooks.ts）
  ├─ seed context
  ├─ injectSkillReload(...)       → skill-reload-injector.ts
  ├─ injectRulesToMessage(...)    → rule-message-injector.ts
  ├─ injectMemoryToMessage(...)   → memory-message-injector.ts   ← 新增
  └─ store transformedMessagesMap
```

### 与 Rule 注入的对比

| 维度 | Rules 注入 | Memory 注入 |
|------|-----------|------------|
| 触发时机 | 每个 LLM step | `needsMemoryInjection` 标志触发，消费后不再注入 |
| 复杂度 | 查询+匹配+格式化 | 子会话检测 + enriched query + 语义检索 + timeout guard |
| 数据来源 | `injectRules()` 实时查询 | `MemoryInjector.retrieveAndFormat()` |
| enriched query | 不需要 | 需要（对话上下文 + session summary） |
| debugLog 模块 | `[rules]` | `[memory]` |

### enriched query 数据来源

当前 `injectMemoriesIntoSystem()` 通过 `client.session.messages()` API 获取消息来构建 enriched query。迁移到 messages.transform 后，消息就在 `output.messages` 参数中，直接传入 `buildEnrichedQuery()`，无需额外 API 调用。这更高效也更可靠。

## In Scope

- 新建 `memory-message-injector.ts`，实现 `injectMemoryToMessage()` 函数
- 重构 `MemoryInjector`：方法改名 `formatForSystem()` → `retrieveAndFormat()`，去掉 `wrapLines()` 硬编码 `<system-reminder>` 标签（只输出纯内容），标签由调用方决定
- 瘦身 `system-transform.ts`：移除 Memory 注入代码、shouldSkipInjection 检查，简化 SystemTransformHookContext
- 更新 `message-hooks.ts` 调度：新增 `memoryMessageCtx` 和 `injectMemoryToMessage()` 调用
- 更新 `index.ts` 组装：构建 Memory 依赖，简化 SystemTransform 参数
- 创建 worktree 隔离开发，完成后提交 PR

## Out of Scope

- 不改动 `memory-injector.ts`（`src/hooks/memory-injector.ts`）中的 `isChildSession()`、`clearInjectedMemory()`、`MemoryInjectorContext` — 保留为共享工具，新文件调用它们
- 不改动 `conversation-context.ts`（`buildEnrichedQuery` 接口不变，只改传入参数来源）
- 不改动 `session-store.ts`（`needsMemoryInjection` 标志逻辑不变）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| memory-injector | `src/hooks/memory-message-injector.ts` | 创建 | Memory 注入到 user message 的核心实现，决定 `<memory-context>` 标签 |
| memory-core | `src/memory/injector.ts` | 修改 | 方法改名 + 去掉 wrapLines 标签，只输出纯记忆内容 |
| system-transform | `src/hooks/system-transform.ts` | 修改 | 瘦身：移除 Memory 注入、shouldSkipInjection，简化 HookContext |
| message-hooks | `src/hooks/message-hooks.ts` | 修改 | 调度新增 Memory 注入，共享 lastUserMsg |
| index | `src/hooks/index.ts` | 修改 | 组装新增 Memory 依赖，简化 SystemTransform 参数 |

## Implementation

### Task 0: 重构 MemoryInjector

**Files**: `src/memory/injector.ts`

**Changes**:

- [x] Step 1: 方法改名 — `formatForSystem()` → `retrieveAndFormat()`（语义更准确：检索并格式化记忆内容，不暗示注入目标）
- [x] Step 2: 去掉 `wrapLines()` 硬编码 `<system-reminder>` 标签 — 改为只返回纯内容（lines joined），标签由调用方决定
- [x] Step 3: 更新文件顶部注释 — 删除 "Context Injection via system.transform Hook"，改为 "Memory retrieval and formatting for injection"
- [x] Step 4: 更新 `formatMemories()` 内部注释 — 删除 "Format memories for system prompt injection"，改为 "Format memories for injection"

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `grep -rn "formatForSystem" src/memory/injector.ts` → 无结果
- [x] Step 3: `grep -rn "retrieveAndFormat" src/memory/injector.ts` → 有结果
- [x] Step 4: `grep -rn "<system-reminder>" src/memory/injector.ts` → 无结果

### Task 1: 新建 memory-message-injector.ts

**Files**: `src/hooks/memory-message-injector.ts`

**Changes**:

- [x] Step 1: 创建 `MemoryMessageInjectorContext` 接口，包含 `memoryInjectorCtx`（共享上下文）、`memoryInjector`、`sessionStore`、`memoryDebugLog`、`memoryInjectionEnabled`
- [x] Step 2: 实现 `injectMemoryToMessage()` 函数，按序检查触发条件：`memoryInjectionEnabled` → `memoryInjector` 存在 → `needsMemoryInjection` flag → 消费 flag → 子会话检测 → store 空检查 → userQuery 检查
- [x] Step 3: 实现子会话检测 — 调用 `isChildSession()`，子会话时调用 `clearInjectedMemory()` 并跳过
- [x] Step 4: 实现 enriched query 构建 — 从 `messages` 参数（非 API）调用 `buildEnrichedQuery()`
- [x] Step 5: 实现 timeout guard — `Promise.race` 8 秒超时，超时时 `clearInjectedMemory()` 并跳过
- [x] Step 6: 实现 `doInject()` 辅助函数 — 调用 `retrieveAndFormat()`（纯内容）→ 包装 `<memory-context>` 标签 → synthetic part → push 到 `lastUserMsg.parts` → 更新 `injectedRawText`

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `grep -rn "injectMemoryToMessage" src/hooks/memory-message-injector.ts` → 有结果

### Task 2: 瘦身 system-transform.ts

**Files**: `src/hooks/system-transform.ts`

**Changes**:

- [x] Step 1: 删除 `injectMemoriesIntoSystem` 调用（第 111-113 行）及相关 import
- [x] Step 2: 删除 `MemoryInjectorContext` 构建代码（第 74-81 行），保留 `isChildSession` import（auto-dump 仍需要）
- [x] Step 3: 删除 `shouldSkipInjection` 检查（第 91-98 行）— Memory 是唯一需要 compaction 保护的注入，移除后 system.transform 在 compaction 期间仍执行 snapshot/dump
- [x] Step 4: 从 `SystemTransformHookContext` 移除 `memoryInjector`、`memoryInjectionEnabled`。保留 `client`、`memoryDebugLog`、`childSessionCache`、`taskManager` — auto-dump 仍需 `isChildSession()`，其底层依赖这些字段
- [x] Step 5: 重构 `memoryInjectorCtx` 构建 — 仅用于 auto-dump 的 `isChildSession` 调用，`memoryInjector` 传 `undefined`

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `grep -rn "injectMemoriesIntoSystem" src/hooks/system-transform.ts` → 无结果
- [x] Step 3: `grep -rn "shouldSkipInjection" src/hooks/system-transform.ts` → 无结果
- [x] Step 4: `grep -rn "memoryInjectionEnabled" src/hooks/system-transform.ts` → 无结果

### Task 3: 更新调度和组装

**Files**: `src/hooks/message-hooks.ts`, `src/hooks/index.ts`

**Changes**:

- [x] Step 1: `MessageHookContext` 新增 `memoryMessageCtx: MemoryMessageInjectorContext` 字段
- [x] Step 2: `onMessagesTransform` 中新增 `await injectMemoryToMessage(ctx.memoryMessageCtx, sessionID, output.messages, lastUserMsg)` 调用，接在 `injectRulesToMessage` 之后
- [x] Step 3: `index.ts` 在 `createAllHooks` 内构建 `memoryInjectorCtx`（与 #139 的 `ruleInjectorCtx` 模式一致：内嵌 `satisfies MemoryInjectorContext`）
- [x] Step 4: `index.ts` 传递 `memoryMessageCtx` 给 `createMessageHooks`
- [x] Step 5: `index.ts` 从 `createSystemTransformHooks` 参数中移除 `memoryInjectionEnabled`。保留 `memoryInjector`、`memoryDebugLog`、`childSessionCache`、`taskManager`（auto-dump 的 `isChildSession` 依赖）

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 通过

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 0 | Task 0 | Wopal | 无（方法改名 + 去标签，简单重构）|
| 1 | Task 1 | fae | Task 0（需调用 `retrieveAndFormat()`）|
| 1 | Task 2 | fae | 无 |
| 2 | Task 3 | fae | Task 1 + Task 2 |

Task 0（重构 MemoryInjector）由 Wopal 直接执行（方法改名 + 去标签，简单且关键）。Task 1 和 Task 2 无依赖可并行（但 Task 1 依赖 Task 0 完成）。Task 3（调度+组装）依赖前两者。

开发在 worktree 中进行，完成后提交 PR 到 fork。

## Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| Memory 在 user message 中没有 cache | 每轮全量传输（但只触发一次） | `needsMemoryInjection` 标志在首次注入时消费，后续轮次直接跳过，无额外 token |
| 模型混淆记忆和用户输入 | Memory 注入到 user message 可能被模型误读为用户输入 | `<memory-context>` XML 标签 + `synthetic: true` 明确标识 |
| `needsMemoryInjection` 在 compaction 期间被意外消费 | compaction 调用 messages.transform 时消费了 clone 上的 flag | flag 是 sessionStore 状态而非 message 属性。compaction 的 `structuredClone` 只克隆 messages，不克隆 sessionStore |
| enriched query 数据来源切换 | 从 `client.session.messages()` API 改为直接取 `output.messages` | 数据更完整更及时，`buildEnrichedQuery()` 接口不变，只改传入参数来源 |
| auto-dump 的 `isChildSession` 依赖 | system-transform 仍需 `isChildSession` 确定 auto-dump 前缀 | 保留 `MemoryInjectorContext` 构建和 `isChildSession` import，`memoryInjector` 传 `undefined` |

## Test Plan

#### Unit Tests

##### Case U1: Memory 注入到 user message
- Goal: 验证记忆内容被注入到 user message 的 synthetic part
- Fixture: mock MemoryInjector（retrieveAndFormat 返回文本）、sessionStore 标记 needsMemoryInjection=true、消息数组含 user 消息
- Execution:
  - [x] Step 1: 调用 `injectMemoryToMessage()`
  - [x] Step 2: 检查最后一条 user message 的 parts 包含 `<memory-context>` synthetic part
  - [x] Step 3: 确认 `synthetic: true` 已设置
  - [x] Step 4: 认 sessionStore 的 `needsMemoryInjection` 已被消费（值为 false）
- Expected Evidence: memory part 存在且格式正确，flag 已清除

##### Case U2: 无 user message 时跳过注入
- Goal: 验证消息数组仅含 assistant 消息时不崩溃
- Fixture: 消息数组仅含 assistant 消息，sessionStore 标记 needsMemoryInjection=true
- Execution:
  - [x] Step 1: 调用 `injectMemoryToMessage()`，`lastUserMsg` 传 `undefined`
  - [x] Step 2: 确认无异常抛出，无 parts 被添加
  - [x] Step 3: 确认 sessionStore 的 `injectedRawText` 已清除
- Expected Evidence: 正常返回，状态已清理

##### Case U3: Memory 注入禁用时跳过
- Goal: 验证 `memoryInjectionEnabled=false` 时完全不注入
- Fixture: memoryInjectionEnabled=false，其余条件满足
- Execution:
  - [x] Step 1: 调用 `injectMemoryToMessage()`
  - [x] Step 2: 确认无 synthetic part 添加，sessionStore 状态不变
- Expected Evidence: 正常返回，无注入

##### Case U4: 子会话跳过 Memory 注入
- Goal: 验证 wopal_task 子会话不注入 Memory
- Fixture: childSessionCache 标记 sessionID 为子会话，sessionStore 标记 needsMemoryInjection=true
- Execution:
  - [x] Step 1: 调用 `injectMemoryToMessage()`
  - [x] Step 2: 确认无 synthetic part 添加
  - [x] Step 3: 确认 `clearInjectedMemory` 已被调用
- Expected Evidence: 正常返回，子会话检测生效

##### Case U5: Memory 注入只触发一次
- Goal: 验证 `needsMemoryInjection` 标志消费后不重复注入
- Fixture: 第一次调用后 flag 已消费（needsMemoryInjection=false），第二次调用
- Execution:
  - [x] Step 1: 第一次调用 `injectMemoryToMessage()` → 确认注入成功
  - [x] Step 2: 第二次调用 `injectMemoryToMessage()` → 确认跳过（无额外 part）
- Expected Evidence: 仅首次注入，第二次直接跳过

##### Case U6: enriched query 使用 messages 参数而非 API
- Goal: 验证 `buildEnrichedQuery` 接收的 messages 来自 `output.messages` 而非 `client.session.messages()` API
- Fixture: messages 参数含完整消息数组，mock `buildEnrichedQuery` 记录传入参数
- Execution:
  - [x] Step 1: 调用 `injectMemoryToMessage()`，传入 messages 数组
  - [x] Step 2: 确认 `buildEnrichedQuery` 收到的 messages 与传入参数一致
  - [x] Step 3: 确认无 `client.session.messages()` API 调用
- Expected Evidence: enriched query 数据来自 transform 参数，无额外 API 调用

#### Integration Tests

##### Case I1: system-transform 不再注入 Memory
- Goal: 确认 system.transform 输出中不含 Memory 内容
- Fixture: sessionStore 标记 needsMemoryInjection=true，mock MemoryInjector
- Execution:
  - [x] Step 1: 调用 `onSystemTransform()`
  - [x] Step 2: 检查 `output.system` 不包含记忆文本
- Expected Evidence: system[] 中无 Memory

#### Regression Tests

##### Case R1: Rules 注入不受影响
- Goal: 确认 Rules 注入仍正常工作（#139 产出）
- Fixture: 规则文件存在 + sessionStore 有 contextPaths
- Execution:
  - [x] Step 1: 调用 `injectRulesToMessage()`
  - [x] Step 2: 确认 user message 含 `<rules-context>` synthetic part
- Expected Evidence: Rules 注入正常

##### Case R2: Skill Reload 注入不受影响
- Goal: 确认 Skill Reload 仍正常注入（#140 产出）
- Fixture: sessionStore 标记 needsSkillReload=true
- Execution:
  - [x] Step 1: 调用 `injectSkillReload()`
  - [x] Step 2: 确认 user message 含 `<system-reminder>` synthetic part
- Expected Evidence: Skill Reload 注入正常

##### Case R3: system-transform 的 auto-dump 仍正常工作
- Goal: 确认移除 Memory 注入后，auto-dump（含 `isChildSession` 前缀判断）不受影响
- Fixture: `WOPAL_PLUGIN_DEBUG=context`，有完整会话
- Execution:
  - [x] Step 1: 触发 auto-dump
  - [x] Step 2: 确认 dump 文件生成，前缀正确（主会话 vs 子会话）
- Expected Evidence: auto-dump 输出格式与迁移前一致

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 通过
- [x] `grep -rn "formatForSystem" src/memory/injector.ts` → 无结果
- [x] `grep -rn "retrieveAndFormat" src/memory/injector.ts` → 有结果
- [x] `grep -rn "<system-reminder>" src/memory/injector.ts` → 无结果
- [x] `grep -rn "injectMemoriesIntoSystem" src/hooks/system-transform.ts` → 无结果
- [x] `grep -rn "injectMemoryToMessage" src/hooks/memory-message-injector.ts` → 有结果
- [x] `grep -rn "shouldSkipInjection" src/hooks/system-transform.ts` → 无结果
- [x] `grep -rn "memoryInjectionEnabled" src/hooks/system-transform.ts` → 无结果
- [x] PR 已提交到 fork `space/main` 分支

### User Validation

#### Scenario 1: 记忆仍被正确注入
- Goal: Memory 注入位置变更后模型仍能引用记忆内容
- Precondition: Memory store 有相关记录
- User Actions:
  1. 开启新会话
  2. 发送需要记忆检索的消息
  3. 观察模型回复是否引用记忆内容
- Expected Result: 模型正确引用记忆

#### Scenario 2: System prompt 完全稳定
- Goal: Memory 注入已从 system prompt 移除，多轮对话后 system blocks 不变
- Precondition: `WOPAL_PLUGIN_DEBUG=context`
- User Actions:
  1. 发送消息 → 查看 auto-dump 中 system blocks
  2. 多轮对话后再次查看 auto-dump
  3. 对比两轮的 system blocks 内容
- Expected Result: system blocks 内容完全一致（无 Memory 动态内容）

#### Scenario 3: Memory 注入只触发一次
- Goal: Memory 注入后不再重复注入
- Precondition: Memory store 有相关记录
- User Actions:
  1. 发送触发 Memory 注入的消息
  2. 继续多轮对话
  3. 观察 auto-dump 中后续轮次的 user message
- Expected Result: 仅首轮 user message 包含 `<memory-context>`

- [x] 用户已完成上述功能验证并确认结果符合预期