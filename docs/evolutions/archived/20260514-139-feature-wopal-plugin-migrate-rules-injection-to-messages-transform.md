# 139 — Rules 注入迁移：从 system.transform 到 messages.transform

## Metadata

- **Issue**: #139
- **Type**: feature
- **Target Project**: wopal-space-ontology（`.wopal/wopal-plugin/`）
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-11
- **Status**: done
- **Worktree**: issue-139-plugin-migrate-rules-injection-to-messages-transform | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-issue-139-plugin-migrate-rules-injection-to-messages-transform
- **Prerequisite**: Plan #140（Skill Reload 迁移）已完成

## 为什么做这件事

Rules 注入当前在 `system.transform` hook 中执行，注入内容拼进 system prompt 的 Part 2。因为 Rules 每轮 LLM 调用都重新计算（用户输入、文件路径、工具列表都可能变化），这导致 Part 2 每轮不同 → system prompt 整体 cache miss。

把 Rules 注入移到 `messages.transform`（作为 user message 的 synthetic part），system prompt 就只剩 Memory（Phase 2 再处理），cache 命中率显著提升。

## 改动范围

### 只做一件事

把 Rules 注入的**调用位置**从 `system-transform.ts` 移到新文件 `rule-message-injector.ts`。规则加载和匹配逻辑（`rule-injector.ts`、`formatter.ts`、`matcher.ts`、`discoverer.ts`）完全不动。

### 不做的事

- **不改动** `rule-injector.ts`（injectRules 函数签名和逻辑不变）
- **不改动** `formatter.ts`（输出格式不变，XML 包装在注入点加）
- **不改动** `matcher.ts`（匹配逻辑不变）
- **不改动** Memory 注入（留在 system.transform，Phase 2 再处理）
- **不改动** `skill-reload-injector.ts`（已在 #140 完成）

## 架构对比

### 当前（Before）

```
system.transform hook（system-transform.ts）
  ├─ Rules 注入    → output.system.push(formattedRules)  ← 每轮变化，破坏 cache
  ├─ Memory 注入   → output.system.push(memoryText)      ← 也会变化
  └─ snapshot/dump

messages.transform hook（message-hooks.ts，一个大函数）
  ├─ seed context
  ├─ Skill Reload 注入（内联代码）
  └─ store transformedMessagesMap
```

### 目标（After）

```
system.transform hook（system-transform.ts）
  ├─ Memory 注入   → output.system.push(memoryText)
  └─ snapshot/dump

messages.transform hook（message-hooks.ts，薄壳调度）
  ├─ seed context
  ├─ injectSkillReload(...)   → skill-reload-injector.ts   ← 从 message-hooks.ts 拆出
  ├─ injectRulesToMessage(...)→ rule-message-injector.ts   ← 新文件
  └─ store transformedMessagesMap
```

每个注入器是独立文件，有自己的 debugLog 归属：

| 文件 | debugLog 模块 | 调试开关 |
|------|-------------|---------|
| `skill-reload-injector.ts` | `[context]` | `WOPAL_PLUGIN_DEBUG=context` |
| `rule-message-injector.ts` | `[rules]` | `WOPAL_PLUGIN_DEBUG=rules` |
| `memory-message-injector.ts`（Phase 2） | `[memory]` | `WOPAL_PLUGIN_DEBUG=memory` |

## 文件结构

```
src/hooks/
  ├─ message-hooks.ts              ← 薄壳：seed + 找 lastUserMsg + 调度注入器 + store map
  ├─ skill-reload-injector.ts      ← Skill Reload 注入（从 message-hooks.ts 拆出）
  ├─ rule-message-injector.ts      ← Rules 注入（新增）
  ├─ rule-injector.ts              ← 不动：injectRules() 核心逻辑
  ├─ memory-injector.ts            ← 不动：Memory system prompt 注入
  ├─ memory-message-injector.ts    ← Phase 2 预留位置
  └─ system-transform.ts           ← 瘦身：只留 Memory 注入 + dump
```

## 具体改动

### 1. 新建 `skill-reload-injector.ts` — 从 message-hooks.ts 拆出 Skill Reload

把 message-hooks.ts 中第 72-104 行的 Skill Reload 注入逻辑提取到独立文件：

```typescript
// skill-reload-injector.ts
import type { SessionStore } from "../session-store.js";
import type { DebugLog } from "../debug.js";
import type { MessageWithInfo } from "./message-context.js";

export interface SkillReloadInjectorContext {
  sessionStore: SessionStore;
  contextDebugLog: DebugLog;
}

export async function injectSkillReload(
  ctx: SkillReloadInjectorContext,
  sessionID: string,
  lastUserMsg: MessageWithInfo | undefined,
): Promise<void> {
  if (!lastUserMsg) return;

  const skillsToReload = ctx.sessionStore.consumeSkillReload(sessionID);
  if (!skillsToReload || skillsToReload.length === 0) return;

  const reminderText = [
    "<system-reminder>",
    `上下文已被压缩，之前加载的技能 [${skillsToReload.join(", ")}] 内容已丢失。`,
    "请重新加载这些技能以恢复完整的指令和工具链。",
    "</system-reminder>",
  ].join("\n");

  lastUserMsg.parts ??= [];
  lastUserMsg.parts.push({
    type: "text",
    text: reminderText,
    synthetic: true,
  });

  ctx.contextDebugLog(
    `Injected Skill Reload for session ${sessionID}: ${skillsToReload.join(", ")}`,
  );
}
```

### 2. 新建 `rule-message-injector.ts` — Rules 注入到 user message

```typescript
// rule-message-injector.ts
import type { SessionStore } from "../session-store.js";
import type { DebugLog } from "../debug.js";
import type { MessageWithInfo } from "./message-context.js";
import type { RuleInjectorContext } from "./rule-injector.js";
import { injectRules } from "./rule-injector.js";
import { extractLatestUserPrompt } from "./message-context.js";

export interface RuleMessageInjectorContext {
  sessionStore: SessionStore;
  ruleInjectorCtx: RuleInjectorContext;
  rulesDebugLog: DebugLog;
  rulesInjectionEnabled: boolean;
}

export async function injectRulesToMessage(
  ctx: RuleMessageInjectorContext,
  sessionID: string,
  messages: MessageWithInfo[],
  lastUserMsg: MessageWithInfo | undefined,
): Promise<void> {
  if (!ctx.rulesInjectionEnabled) return;
  if (!lastUserMsg) return;

  const sessionState = ctx.sessionStore.get(sessionID);
  const contextPaths = sessionState
    ? Array.from(sessionState.contextPaths).sort()
    : [];
  const userPrompt = extractLatestUserPrompt(messages);

  const formattedRules = await injectRules(
    ctx.ruleInjectorCtx,
    contextPaths,
    userPrompt,
  );

  if (!formattedRules) return;

  lastUserMsg.parts ??= [];
  lastUserMsg.parts.push({
    type: "text",
    text: `<rules-context>\n${formattedRules}\n</rules-context>`,
    synthetic: true,
  });

  ctx.rulesDebugLog(`Injected rules for session ${sessionID}`);
}
```

### 3. 瘦身 `message-hooks.ts` — 只做调度

```typescript
// message-hooks.ts（改造后）
import { extractSessionID, extractLatestUserPrompt, normalizeContextPath,
         toExtractableMessages, type MessageWithInfo } from "./message-context.js";
import type { SessionStore } from "../session-store.js";
import type { DebugLog } from "../debug.js";
import type { SkillReloadInjectorContext } from "./skill-reload-injector.js";
import type { RuleMessageInjectorContext } from "./rule-message-injector.js";

const MAX_RECENT_MESSAGES = 10;

interface MessagesTransformOutput {
  messages: MessageWithInfo[];
}

export interface MessageHookContext {
  sessionStore: SessionStore;
  contextDebugLog: DebugLog;
  projectDirectory: string;
  transformedMessagesMap: Map<string, MessageWithInfo[]>;
  skillReloadCtx: SkillReloadInjectorContext;
  ruleMessageCtx: RuleMessageInjectorContext;
}

export function createMessageHooks(ctx: MessageHookContext) {
  async function onMessagesTransform(
    _input: Record<string, never>,
    output: MessagesTransformOutput,
  ): Promise<MessagesTransformOutput> {
    const sessionID = extractSessionID(output.messages);
    if (!sessionID) {
      ctx.contextDebugLog("No sessionID found in messages");
      return output;
    }

    // 1. Seed context（仅首次）
    const existingState = ctx.sessionStore.get(sessionID);
    const shouldSeed = !existingState?.seededFromHistory;
    if (shouldSeed) {
      // ... 现有 seed 逻辑不变 ...
    }

    // 2. 找最后一条 user message（共享，只找一次）
    let lastUserMsg: MessageWithInfo | undefined;
    for (let i = output.messages.length - 1; i >= 0; i--) {
      const message = output.messages[i];
      const role = message.info?.role ?? message.role;
      if (role === "user") {
        lastUserMsg = message;
        break;
      }
    }

    // 3. 各注入器独立调用
    await injectSkillReload(ctx.skillReloadCtx, sessionID, lastUserMsg);
    await injectRulesToMessage(ctx.ruleMessageCtx, sessionID, output.messages, lastUserMsg);

    // 4. Store transformed messages for auto dump
    ctx.transformedMessagesMap.set(sessionID, output.messages);

    return output;
  }

  // onChatMessage 不变
  // ...

  return {
    "experimental.chat.messages.transform": onMessagesTransform,
    "chat.message": onChatMessage,
  };
}
```

### 4. 瘦身 `system-transform.ts` — 移除 Rules 注入

**删除**：
- `RuleInjectorContext` 构建（第 56-61 行）
- `injectRules` 调用及整个 `if (ctx.rulesInjectionEnabled)` 块（第 102-117 行）
- 相关 import（`injectRules`, `queryAvailableToolIDs`, `RuleInjectorContext`）

**从 SystemTransformHookContext 移除**：
- `ruleFiles` → 只服务于 Rules
- `rulesDebugLog` → 只服务于 Rules
- `rulesInjectionEnabled` → 只服务于 Rules

**保留**：`directory`（writeContextDump 用）、`projectDirectory`、Memory 相关字段、dump 逻辑。

### 5. 更新 `index.ts` — 组装依赖

```typescript
// index.ts createAllHooks 内

// Rules 注入器上下文（新增）
const ruleInjectorCtx: RuleInjectorContext = {
  client: ctx.client,
  directory: ctx.directory,
  ruleFiles: ctx.ruleFiles,
  rulesDebugLog: ctx.rulesDebugLog,
};

const messageHooks = createMessageHooks({
  sessionStore: ctx.sessionStore,
  contextDebugLog: ctx.contextDebugLog,
  projectDirectory: ctx.projectDirectory,
  transformedMessagesMap,
  skillReloadCtx: {
    sessionStore: ctx.sessionStore,
    contextDebugLog: ctx.contextDebugLog,
  },
  ruleMessageCtx: {
    sessionStore: ctx.sessionStore,
    ruleInjectorCtx,
    rulesDebugLog: ctx.rulesDebugLog,
    rulesInjectionEnabled: ctx.rulesInjectionEnabled,
  },
});

const systemTransformHooks = createSystemTransformHooks({
  client: ctx.client,
  directory: ctx.directory,
  // ruleFiles, rulesDebugLog, rulesInjectionEnabled → 已移除
  sessionStore: ctx.sessionStore,
  memoryDebugLog: ctx.memoryDebugLog,
  contextDebugLog: ctx.contextDebugLog,
  now: ctx.now,
  memoryInjector: ctx.memoryInjector,
  childSessionCache: ctx.childSessionCache,
  taskManager: ctx.taskManager,
  systemSnapshots: ctx.systemSnapshots,
  systemMetadataMap: ctx.systemMetadataMap,
  systemInjectionsMap: ctx.systemInjectionsMap,
  transformedMessagesMap,
  memoryInjectionEnabled: ctx.memoryInjectionEnabled,
});
```

### 6. 不改动的文件

| 文件 | 说明 |
|------|------|
| `rule-injector.ts` | `injectRules()` 函数签名和逻辑不变，只是调用者换了 |
| `formatter.ts` | 输出格式不变，XML 包装在 `rule-message-injector.ts` 中加 |
| `matcher.ts` | 匹配逻辑不变 |
| `discoverer.ts` | 规则发现不变 |
| `memory-injector.ts` | Memory 注入不变 |
| `session-store.ts` | 不变 |

## 实施步骤

### Step 1: 拆出 skill-reload-injector.ts

1. [x] 从 `message-hooks.ts` 提取 Skill Reload 注入逻辑到 `skill-reload-injector.ts`
2. [x] `message-hooks.ts` 改为调用 `injectSkillReload()`
3. [x] `bun run build` + `bun run test:run` 验证行为不变

### Step 2: 移除 system-transform.ts 中的 Rules 注入

1. [x] 删除 `RuleInjectorContext` 构建和 `injectRules` 调用
2. [x] 删除相关 import
3. [x] 从 `SystemTransformHookContext` 移除 `ruleFiles`、`rulesDebugLog`、`rulesInjectionEnabled`
4. [x] 验证 Memory 注入路径完全不变

### Step 3: 新建 rule-message-injector.ts

1. [x] 创建新文件，实现 `injectRulesToMessage()`
2. [x] XML 包装 `<rules-context>` 在此处加

### Step 4: 更新 message-hooks.ts 调度逻辑

1. [x] `MessageHookContext` 新增 `skillReloadCtx` 和 `ruleMessageCtx`
2. [x] `onMessagesTransform` 改为调用各注入器

### Step 5: 更新 index.ts 组装

1. [x] 构建 `ruleInjectorCtx`
2. [x] 传递给 `createMessageHooks`
3. [x] 从 `createSystemTransformHooks` 参数中移除 Rules 相关字段

### Step 6: 验证

1. [x] `bun run build` 编译通过
2. [x] `bun run test:run` 全部通过

## 风险与应对

### 不需要担心的

- **compaction 场景**：`messages.transform` 修改不写回 DB（Plan #140 已验证），compaction 用 `structuredClone` 保护 DB
- **tool-use 重入**：工具结果不是独立 user message，`messages.transform` 始终看到原始 user message
- **synthetic part 处理**：`prompt.ts:1552` 跳过 synthetic parts 的 system-reminder 包装
- **Rules 每轮重新计算**：当前在 `system.transform` 也是每轮计算，延迟无变化

### 需要注意的

| 风险 | 说明 | 应对 |
|------|------|------|
| Rules 在 user message 中没有 cache | 每轮全量传输 | Rules 通常几十到几百 tokens，成本低。换来 system prompt 大块 cache 命中，净收益为正 |
| 模型混淆规则和用户输入 | Rules 注入到 user message | `<rules-context>` XML 标签 + `synthetic: true` |
| contextPaths 首轮为空 | 首次 seed 和注入在同一次 `onMessagesTransform` 调用 | 注入发生在 seed 之后，contextPaths 已存入 sessionStore。无 state 时传空数组（与当前行为一致） |

## 已验证的设计点

- ✅ `messages.transform` 允许添加 part（引用语义）
- ✅ 工具结果不是独立 user message
- ✅ `synthetic: true` 的 part 不被 prompt.ts 二次包装
- ✅ `messages.transform` 修改不持久化到 DB
- ✅ compaction 用 `structuredClone`，不影响 DB 数据

## Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| Rules 在 user message 中没有 cache | 每轮全量传输 | Rules 通常几十到几百 tokens，成本低。换来 system prompt 大块 cache 命中，净收益为正 |
| 模型混淆规则和用户输入 | Rules 注入到 user message | `<rules-context>` XML 标签 + `synthetic: true` |
| contextPaths 首轮为空 | 首次 seed 和注入在同一次 `onMessagesTransform` 调用 | 注入发生在 seed 之后，contextPaths 已存入 sessionStore。无 state 时传空数组（与当前行为一致） |

## Test Plan

#### Unit Tests

##### Case U1: Rules 注入到 user message
- Goal: 验证规则内容被注入到 user message 的 synthetic part
- Fixture: mock RuleInjectorContext、sessionStore、消息数组含 user + assistant 消息
- Execution:
  - [x] Step 1: 调用 `injectRulesToMessage()`
  - [x] Step 2: 检查最后一条 user message 的 parts 包含 `<rules-context>` synthetic part
  - [x] Step 3: 确认 `synthetic: true` 已设置
- Expected Evidence: rules part 存在且格式正确

##### Case U2: 无 user message 时跳过注入
- Goal: 验证消息数组仅含 assistant 消息时不崩溃
- Fixture: 消息数组仅含 assistant 消息
- Execution:
  - [x] Step 1: 调用 `injectRulesToMessage()`
  - [x] Step 2: 确认无异常，无 parts 被添加
- Expected Evidence: 正常返回

##### Case U3: Rules 注入禁用时跳过
- Goal: 验证 `rulesInjectionEnabled=false` 时不注入
- Fixture: rulesInjectionEnabled=false
- Execution:
  - [x] Step 1: 调用 `injectRulesToMessage()`
  - [x] Step 2: 确认无 synthetic part 添加
- Expected Evidence: 正常返回，无注入

#### Integration Tests

##### Case I1: system-transform 不再注入 Rules
- Goal: 确认 system.transform 不注入 Rules
- Fixture: 完整 hook context + 规则文件 + mock MemoryInjector
- Execution:
  - [x] Step 1: 调用 `onSystemTransform()`
  - [x] Step 2: 检查 output.system 不包含 `# OpenCode Rules`
  - [x] Step 3: 确认 output.system 仍包含 memory 内容（若有）
- Expected Evidence: system[] 中无规则

#### Regression Tests

##### Case R1: Skill Reload 注入不受影响
- Goal: 确认 Skill Reload 仍正常注入（#140 产出）
- Fixture: sessionStore 标记 needsSkillReload=true
- Execution:
  - [x] Step 1: 调用 `injectSkillReload()`
  - [x] Step 2: 确认 user message 含 `<system-reminder>` synthetic part
- Expected Evidence: Skill Reload 注入正常

##### Case R2: Memory 注入不受影响
- Goal: 确认 Memory 注入路径完全不变
- Fixture: sessionStore 标记 needsMemoryInjection=true，mock MemoryInjector
- Execution:
  - [x] Step 1: 调用 `onSystemTransform()`
  - [x] Step 2: 确认 output.system 包含 memory 内容
- Expected Evidence: Memory 注入正常工作

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 通过
- [x] `grep -rn "injectRules" src/hooks/system-transform.ts` → 无结果
- [x] `grep -rn "injectRulesToMessage" src/hooks/rule-message-injector.ts` → 有结果
- [x] `grep -rn "consumeSkillReload" src/hooks/message-hooks.ts` → 无结果（已拆到 skill-reload-injector.ts）

### User Validation

#### Scenario 1: 规则仍被模型遵守
- Goal: 确认规则注入位置变更后模型仍遵守规则
- Precondition: 有关键词匹配的规则文件（如 TypeScript 规范）
- User Actions:
  1. 开启新会话
  2. 发送匹配规则的消息
  3. 观察模型回复是否遵守规则
- Expected Result: 模型遵守规则

#### Scenario 2: System prompt 不再包含规则
- Goal: 确认 Rules 注入已从 system prompt 移除
- Precondition: 开启 debug 日志（`WOPAL_PLUGIN_DEBUG=context`）
- User Actions:
  1. 发送消息 → 查看 `logs/` 下 auto-context-dump
  2. 对比 system blocks
- Expected Result: system blocks 中无 `# OpenCode Rules` 内容

#### Scenario 3: Rules 注入在 user message 中可见
- Goal: 确认 Rules 以 `<rules-context>` synthetic part 形式注入
- Precondition: `WOPAL_PLUGIN_DEBUG=rules`
- User Actions:
  1. 发送匹配规则的消息
  2. 查看 auto-dump 的 Messages 部分
- Expected Result: user message 的 synthetic parts 包含 `<rules-context>` 内容

- [x] 用户已完成上述功能验证并确认结果符合预期

## 后续方案

Memory 注入迁移已拆分为独立方案：`feature-wopal-plugin-migrate-memory-injection-to-messages-transform.md`。本方案完成后，可继续执行 Memory 迁移，最终实现 system prompt 完全稳定（近 100% cache hit）。