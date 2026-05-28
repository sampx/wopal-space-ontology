# feature-wopal-plugin-migrate-skill-reload-to-messages-transform

## Metadata

- **Parent Plan**: #139 (Rules 注入迁移)
- **Type**: feature
- **Target Project**: wopal-plugin
- **Created**: 2026-05-12
- **Status**: done

## Scope Assessment

- **Complexity**: Low-Medium（迁移点单一，但涉及 hook 顺序、一次性消费语义、dump 类型兼容）
- **Confidence**: Medium-High（OpenCode 调用顺序已验证；需避免现有 message hook 早退导致漏注入）

## Goal

将 Compact 后的 Skill Reload Reminder 从 `system.transform` 移到 `messages.transform`，以 `<system-reminder>` synthetic part 注入到 user message，稳定 system prompt。

**Scope**：
- 仅迁移 Skill Reload Reminder，不涉及 Rules
- 不改动 session-store.ts（复用现有 `consumeSkillReload`）
- 不改动 Memory 注入
- 新增 transformedMessagesMap 支持 auto dump

**收益**：
- Compact 后首轮 system prompt 保持稳定（不因 Skill Reminder 变化）
- 为后续 Rules 迁移验证流程
- Auto dump 可完整展示 Skill Reload 注入内容

## Technical Context

### Skill Reload 当前实现

```
1. 技能加载 → sessionStore.recordSkillLoaded(sessionID, name) → loadedSkills: Set<string>
2. Compact 完成 → session.compacted 事件 → sessionStore.markCompacted() → needsSkillReload = true
3. system.transform → consumeSkillReload() → output.system.push("[系统提醒]...")
   → 一次性消费：消费后 needsSkillReload 被清除
```

**当前注入位置**：`system-transform.ts:100-108`，注入到 `output.system`

**问题**：Compact 后首轮 system prompt 变化 → cache miss

### messages.transform 机制

- **调用时机**：每个 LLM step 都触发（prompt.ts:1566）
- **数据来源**：每次从 DB 加载 → hook 临时修改 → 修改不写回
- **Multi-step 场景**：step 1 注入后 `consumeSkillReload` 返回 null → step 2+ 不注入
- **Synthetic part**：`{ type: "text", text: "...", synthetic: true }` 传递给模型，不写 DB

### 现有代码约束（实施必须遵守）

- `message-hooks.ts` 当前在 `seededFromHistory` 已存在时会提前 `return output`。迁移时必须拆分为：
  - seeding/rescan 可跳过
  - Skill Reload 注入和 transformed messages 存储必须继续执行
- `tsconfig.json` 使用 `lib: ["ES2022"]`，不能使用 `Array.prototype.findLast()`；用反向 `for` 循环查找最后一条 user message。
- `consumeSkillReload()` 是破坏性一次性消费。必须先找到可注入的 user message，再调用 `consumeSkillReload()`，避免“无 user message 时提醒被消费但未注入”。
- `transformedMessagesMap` 类型必须统一。建议以 `MessageWithInfo[]` 作为共享 Map 类型，并让 dump formatter 接受 `SessionMessage | MessageWithInfo` 的兼容消息结构。
- `context_manage dump` 当前仍从 DB 读取 messages。本计划只要求 auto dump 展示 synthetic part；手动 dump 是否使用 transformed map 作为后续增强，不作为本次验收门槛。

### Hook 调用顺序

```
prompt.ts:1566  → messages.transform（先执行）
                   ↓ 注入 synthetic part 到 user message
prompt.ts:1577  → handle.process({ system, messages })
                   ↓
llm.ts:118      → system.transform（后执行）
                   ↓ auto dump 触发
```

### 迁移目标

```
User Message（in-memory synthetic part）:
  ├─ <system-reminder> Skill Reload 提醒（compact 后首轮 step 1 出现，一次性消费）
  └─ 用户输入
```

### Auto Dump 机制

当前 auto dump 调用 `client.session.messages()` 从 DB 加载 messages，无法看到 synthetic part。

**解决方案**：messages-transform 将处理后的 messages 存入共享 Map → auto dump 优先从 Map 读取。

## In Scope

- 移除 `system-transform.ts` 中的 Skill Reload 注入
- 新增 `message-hooks.ts` 中的 Skill Reload 注入（`<system-reminder>` 格式）
- 新增 `transformedMessagesMap` 共享机制
- 修改 `dump-formatter.ts` 优先使用 transformedMessagesMap
- 更新相关测试

## Out of Scope

- Rules 注入迁移（Parent Plan #139）
- Memory 注入
- session-store.ts 新方法（复用现有 `consumeSkillReload`）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| hooks | `src/hooks/index.ts` | 修改 | 新增 transformedMessagesMap，传递给子 hooks |
| hooks | `src/hooks/system-transform.ts` | 修改 | 移除 Skill Reload 注入，传递 transformedMessagesMap 给 auto dump |
| hooks | `src/hooks/message-hooks.ts` | 修改 | 新增 Skill Reload 注入，存储 messages 到 Map |
| tools | `src/tools/dump-formatter.ts` | 修改 | 优先使用 transformedMessagesMap |
| tests | `src/hooks/message-hooks.test.ts` | 修改 | 新增 Skill Reload 测试用例 |
| tests | `src/hooks/integration.test.ts` / `src/hooks/system-transform.test.ts` | 修改/新增 | 验证 system.transform 不再注入 Skill Reload |
| tests | `src/tools/context-manage.test.ts` / `src/tools/dump-formatter.test.ts` | 修改/新增 | 验证 dump fallback 与 transformed map 优先级 |

## Implementation

### Execution Strategy

#### Repository Strategy

- 目标实现仓库：`.wopal/wopal-plugin/`
- 方案文档仓库：workspace 根仓库 `docs/**`
- 实施前必须分别检查：
  - 根仓库：确认 Plan 变更不混入其他无关文档
  - `.wopal/` 仓库：确认 wopal-plugin 当前工作区状态
- 若 `.wopal/` 已有无关未提交变更，优先使用 dev-flow worktree 隔离执行；不要在当前工作区混写。

#### Delegation Strategy

本任务可以委派，但不建议把核心代码修改拆成多个并行写任务。原因：
- `message-hooks.ts`、`system-transform.ts`、`dump-formatter.ts` 的类型和调用链彼此耦合
- `transformedMessagesMap` 需要在 hook 组装入口、system transform、dump formatter 之间一次性贯通
- 并行写同一 hook 层容易产生重复类型定义或测试互相覆盖

推荐采用“两阶段、最多两名 Fae”的策略：

##### Batch 1: Implementation Worker（串行主线）

**Owner**: Fae Worker A  
**Write Scope**:
- `.wopal/wopal-plugin/src/hooks/index.ts`
- `.wopal/wopal-plugin/src/hooks/message-hooks.ts`
- `.wopal/wopal-plugin/src/hooks/system-transform.ts`
- `.wopal/wopal-plugin/src/tools/dump-formatter.ts`
- 相关测试文件

**Prompt Strategy**:
- 只给本 Plan 路径作为单一事实源
- 明确目标项目路径是 `.wopal/wopal-plugin/`
- 明确不得编辑 `projects/ontology/wopal-plugin/`
- 明确不得修改 workspace 根仓库其他 Plan

**Completion Criteria**:
- 完成 Task 1-5
- `bun run build` 通过
- `bun run test:run` 通过
- 输出 changed files + verification evidence

##### Batch 2: Review / Verification Worker（并行只读）

**Owner**: Fae Worker B  
**Read Scope Only**:
- `.wopal/wopal-plugin/src/hooks/**`
- `.wopal/wopal-plugin/src/tools/dump-formatter.ts`
- `.wopal/wopal-plugin/src/session-store.ts`
- 本 Plan 文件

**Task**:
- 审查 Batch 1 产出是否满足：
  - `seededFromHistory` 不再阻断 Skill Reload 注入
  - `consumeSkillReload` 不会在无 user message 时提前消费
  - system prompt 不再含 Skill Reload
  - auto dump 能看到 synthetic part
  - TypeScript strict + ES2022 兼容

**Restriction**:
- 不写文件，仅输出 findings
- 不运行破坏性命令

#### Main Agent Responsibilities

- 委派前按 AGENTS.md 执行记忆搜索和路径检查
- 检查 Fae prompt 中所有路径必须是 `.wopal/wopal-plugin/...` 或绝对路径
- 集成 Batch 1 结果后亲自运行最终验证
- 对 Batch 2 findings 做取舍，必要时主控修正
- 只有用户明确审批后才进入实施；本 Plan 优化不等于开始开发

#### Suggested Fae Prompt

```markdown
## Plan
读取 Plan 文件，按 Implementation 执行：
docs/products/wopal-plugin/plans/feature-wopal-plugin-migrate-skill-reload-to-messages-transform.md

## 项目路径
目标项目是 .wopal/wopal-plugin/。
所有源码路径都相对该项目目录理解。
禁止编辑 projects/ontology/wopal-plugin/。
禁止编辑 workspace 根仓库其他 Plan 或无关文件。

## 特别注意
- message-hooks.ts 中 seededFromHistory 只能跳过 rescan，不能阻断 Skill Reload 注入和 transformedMessagesMap 存储。
- 先找到最后一条 user message，再调用 consumeSkillReload。
- 不使用 Array.prototype.findLast，保持 ES2022 兼容。
- transformedMessagesMap 类型以 MessageWithInfo[] 为准，dump formatter 做兼容。

## 完成标准
- bun run build 通过
- bun run test:run 通过
- system-transform.ts 中无 consumeSkillReload
- auto dump 路径可展示 synthetic Skill Reload part

## Task Report
完成时输出：Goal/Accomplished/Files/Verification/Status
```

### Risks & Mitigations

| Risk | Why It Matters | Mitigation |
|------|----------------|------------|
| `seededFromHistory` 早退导致 compact 后不注入提醒 | 大多数真实会话都会先完成 seeding，compact 后首轮会被早退挡掉 | 将 early return 改为 `shouldSeed` 分支，post-transform 逻辑始终执行 |
| 无 user message 时提前消费 Skill Reload | 一次性消费后无法重试，agent 收不到提醒 | 先找到 user message，再调用 `consumeSkillReload()` |
| `MessageWithInfo` 与 `SessionMessage` 类型不兼容 | strict TS 下 dump formatter 容易编译失败 | 定义 `DumpMessage` 兼容类型，并用 helper 读取 role/time |
| transformed map 保留较大 messages 数组 | debug dump 需要完整 prompt 视图，但内存占用会增加 | 每个 session 只保留最新一次 transformed messages；后续如有需要再做 session prune |
| 并行委派改同一 hook 层 | 容易产生冲突和重复修复 | 核心实现单 worker 串行，第二 worker 只读 review |

### Task 1: hooks/index.ts - 新增共享 Map

**Files**: `src/hooks/index.ts`

**Changes**:

- [x] Step 1: 导入 `MessageWithInfo` 类型并在 `createAllHooks` 内新增 `transformedMessagesMap`
  ```typescript
  import type { MessageWithInfo } from "./message-context.js";

  // createAllHooks 内，messageHooks/systemTransformHooks 创建前
  const transformedMessagesMap = new Map<string, MessageWithInfo[]>();
  ```

- [x] Step 2: 传递给 messageHooks 和 systemTransformHooks
  ```typescript
  const messageHooks = createMessageHooks({
    sessionStore: ctx.sessionStore,
    debugLog: ctx.debugLog,
    projectDirectory: ctx.projectDirectory,
    transformedMessagesMap,
  });

  const systemTransformHooks = createSystemTransformHooks({
    ...
    transformedMessagesMap,
  });
  ```

**Verification**:

- [x] Step 1: TypeScript 编译通过

### Task 2: message-hooks.ts - Skill Reload 注入 + 存储 messages

**Files**: `src/hooks/message-hooks.ts`

**Changes**:

- [x] Step 1: 扩展 MessageHookContext 接口
  ```typescript
  import type { MessageWithInfo } from "./message-context.js";

  export interface MessageHookContext {
    sessionStore: SessionStore;
    debugLog: DebugLog;
    projectDirectory: string;
    transformedMessagesMap: Map<string, MessageWithInfo[]>;  // 新增
  }
  ```

- [x] Step 2: 拆掉 `seededFromHistory` 的早退，只跳过 rescan，不跳过 post-transform 逻辑
  ```typescript
  const existingState = ctx.sessionStore.get(sessionID);
  const shouldSeed = !existingState?.seededFromHistory;

  if (shouldSeed) {
    // 现有 extract contextPaths / userPrompt / upsert / debugLog 逻辑
  } else {
    ctx.debugLog(`Session ${sessionID} already seeded, skipping rescan`);
  }
  ```

- [x] Step 3: 在 `onMessagesTransform` 的统一出口前添加 Skill Reload 注入，且先找 user message 再消费
  ```typescript
  let lastUserMsg: MessageWithInfo | undefined;
  for (let i = output.messages.length - 1; i >= 0; i--) {
    const message = output.messages[i];
    const role = message.info?.role ?? message.role;
    if (role === "user") {
      lastUserMsg = message;
      break;
    }
  }

  if (lastUserMsg) {
    const skillsToReload = ctx.sessionStore.consumeSkillReload(sessionID);
    if (skillsToReload && skillsToReload.length > 0) {
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

      ctx.debugLog(
        `Injected Skill Reload for session ${sessionID}: ${skillsToReload.join(", ")}`,
      );
    }
  }
  ```

- [x] Step 4: 无论是否注入，都在统一出口前存储 transformed messages，供 auto dump 使用
  ```typescript
  ctx.transformedMessagesMap.set(sessionID, output.messages);

  return output;
  ```

**Verification**:

- [x] Step 1: `bun run test:run` 通过

### Task 3: system-transform.ts - 移除 Skill Reload + 传递 transformedMessagesMap

**Files**: `src/hooks/system-transform.ts`

**Changes**:

- [x] Step 1: 扩展 SystemTransformHookContext 接口
  ```typescript
  import type { MessageWithInfo } from "./message-context.js";

  export interface SystemTransformHookContext {
    ...
    transformedMessagesMap: Map<string, MessageWithInfo[]>;  // 新增
  }
  ```

- [x] Step 2: 删除 `onSystemTransform` 中的 Skill Reload 逻辑（line 100-108）
  ```typescript
  // DELETE THIS BLOCK:
  const skillsToReload = sessionID
    ? ctx.sessionStore.consumeSkillReload(sessionID)
    : null;
  if (skillsToReload) {
    output.system.push(
      `[系统提醒] 上下文已被压缩，之前加载的技能 [${skillsToReload.join(", ")}] 内容已丢失。` +
        `请重新加载这些技能以恢复完整的指令和工具链。`,
    );
  }
  ```

- [x] Step 3: 在 auto dump 调用时传递 transformedMessagesMap
  ```typescript
  void writeContextDump({
    sessionID,
    baseDir: ctx.directory,
    filenamePrefix: "AUTO-CTXDUMP",
    systemSnapshots: ctx.systemSnapshots ?? new Map(),
    systemMetadataMap: ctx.systemMetadataMap ?? new Map(),
    systemInjectionsMap: ctx.systemInjectionsMap,
    transformedMessagesMap: ctx.transformedMessagesMap,  // 新增
    client: ctx.client,
    detail: false,
  }).catch(err => ctx.debugLog(`[auto-dump] error: ${err}`));
  ```

**Verification**:

- [x] Step 1: `grep -n "consumeSkillReload" src/hooks/system-transform.ts` → 无结果
- [x] Step 2: `bun run build` 通过
- [x] Step 3: `bun run test:run` 通过

### Task 4: dump-formatter.ts - 优先使用 transformedMessagesMap

**Files**: `src/tools/dump-formatter.ts`

**Changes**:

- [x] Step 1: 扩展 ContextDumpOptions 接口，Map 类型使用 `MessageWithInfo[]`
  ```typescript
  import type { MessageWithInfo } from "../hooks/message-context.js";

  export interface ContextDumpOptions {
    sessionID: string;
    baseDir: string;
    filenamePrefix: string;
    systemSnapshots: Map<string, string[]>;
    systemMetadataMap: Map<string, SystemPromptMetadata>;
    systemInjectionsMap?: Map<string, string[]>;
    transformedMessagesMap?: Map<string, MessageWithInfo[]>;  // 新增
    client: any;
    detail: boolean;
    title?: string | null;
  }
  ```

- [x] Step 2: 让 formatter 接受兼容消息结构，role 读取同时支持 `info.role` 和 `role`
  ```typescript
  type DumpMessage = SessionMessage | MessageWithInfo;

  function getDumpMessageRole(msg: DumpMessage): string {
    const directRole = "role" in msg ? msg.role : undefined;
    return msg.info?.role ?? directRole ?? "unknown";
  }

  function getDumpMessageTime(msg: DumpMessage): SessionMessage["info"]["time"] | undefined {
    const info = msg.info;
    if (info && "time" in info) return info.time;
    return undefined;
  }

  export function formatMessagesForDump(messages: DumpMessage[], detail = false): string {
    ...
    const role = getDumpMessageRole(msg);
    const time = getDumpMessageTime(msg);
    ...
  }
  ```

- [x] Step 3: 修改 writeContextDump 中 messages 加载逻辑（line 614-623）
  ```typescript
  // Messages section
  lines.push("---", "");
  lines.push("## Messages");
  lines.push("");

  let messages: DumpMessage[] = [];
  
  // Priority: use transformedMessagesMap (contains synthetic parts)
  const transformed = transformedMessagesMap?.get(sessionID);
  if (transformed && transformed.length > 0) {
    messages = transformed;
  } else {
    // Fallback: load from DB
    try {
      if (client && typeof client?.session?.messages === "function") {
        const result = await client.session.messages({ path: { id: sessionID } });
        messages = result?.data ?? [];
      }
    } catch {
      // Graceful degradation
    }
  }

  if (messages.length > 0) {
    lines.push(`_(${messages.length} messages)_`);
    lines.push("");
    lines.push(formatMessagesForDump(messages, detail));
  } else {
    lines.push("(No messages)");
    lines.push("");
  }
  ```

**Verification**:

- [x] Step 1: Auto dump 文件包含 Skill Reload synthetic part（`> _[synthetic]_` 格式）
- [x] Step 2: Fallback 逻辑正常工作（无 transformedMessagesMap 时从 DB 加载）

### Task 5: 更新测试

**Files**: `src/hooks/message-hooks.test.ts`, `src/hooks/integration.test.ts`, `src/tools/context-manage.test.ts` 或新增 `src/tools/dump-formatter.test.ts`，必要时新增 `src/hooks/system-transform.test.ts`

**Changes**:

- [x] Step 1: 新增 `message-hooks.test.ts` 测试用例
  - Case U1: Skill Reload 注入到 user message（含 synthetic: true）
  - Case U2: Skill Reload 一次性消费（第二次调用不注入）
  - Case U3: 无 Skill Reload 时不注入
  - Case U4: 无 user message 时跳过
  - Case U5: transformedMessagesMap 存储 messages（含 synthetic part）

- [x] Step 2: 新增或调整 system transform 测试，确认 `system.transform` 不再消费/注入 Skill Reload
  - 当前仓库没有 `src/hooks/system-transform.test.ts`；如果新增该文件，只覆盖本计划相关行为
  - 若放入 `integration.test.ts`，测试名必须明确指向 Skill Reload 迁移

- [x] Step 3: 更新旧测试 `should not modify messages in messages.transform hook`
  - 当前断言消息完全不变；迁移后仅在 `needsSkillReload` 时允许新增 synthetic part
  - 无 Skill Reload 场景仍应保持不变

- [x] Step 4: 新增 dump formatter 测试
  - transformedMessagesMap 存在时优先使用 map，不调用或不依赖 DB messages
  - transformedMessagesMap 缺失时 fallback 到 `client.session.messages()`
  - synthetic text part 格式化为 `> _[synthetic]_`

- [x] Step 5: 确认 Memory 注入测试不受影响

**Verification**:

- [x] Step 1: `bun run test:run` → 全部通过
- [x] Step 2: `bun run build` → 编译通过

## Test Plan

### Unit Tests

#### Case U1: Skill Reload 注入到 user message
- Goal: 验证 Skill Reload 以 `<system-reminder>` synthetic part 注入
- Fixture:
  ```typescript
  const transformedMessagesMap = new Map<string, MessageWithInfo[]>();
  sessionStore.upsert(sessionID, (s) => {
    s.loadedSkills = new Set(["dev-flow", "fae-collab"]);
    s.needsSkillReload = true;
  });
  const messages = [
    { info: { role: "user" }, parts: [{ type: "text", text: "hello" }] },
    { info: { role: "assistant" }, parts: [{ type: "text", text: "response" }] },
  ];
  ```
- Execution:
  - [x] Step 1: 调用 `onMessagesTransform({}, { messages })`
  - [x] Step 2: 检查最后一条 user message 的 parts 包含 `<system-reminder>` synthetic part
  - [x] Step 3: 确认 `synthetic: true` 已设置
- Expected Evidence: Skill Reload part 存在且格式正确

#### Case U2: Skill Reload 一次性消费
- Goal: 验证第二次调用不注入（consumeSkillReload 已消费）
- Fixture: 同 U1
- Execution:
  - [x] Step 1: 第一次调用 → 确认 Skill Reload part 存在
  - [x] Step 2: 第二次调用 → 确认无 Skill Reload part
- Expected Evidence: 仅首次注入

#### Case U3: 无 Skill Reload 时不注入
- Goal: 验证正常会话不注入空 part
- Fixture:
  ```typescript
  sessionStore.upsert(sessionID, (s) => {
    s.loadedSkills = new Set();
    // 无 needsSkillReload
  });
  ```
- Execution:
  - [x] Step 1: 调用 `onMessagesTransform`
  - [x] Step 2: 确认无 synthetic part
- Expected Evidence: 无多余 part

#### Case U4: 无 user message 时跳过
- Goal: 验证不崩溃
- Fixture:
  ```typescript
  sessionStore.upsert(sessionID, (s) => {
    s.loadedSkills = new Set(["dev-flow"]);
    s.needsSkillReload = true;
  });
  const messages = [{ info: { role: "assistant" }, parts: [{ type: "text", text: "response" }] }];
  ```
- Execution:
  - [x] Step 1: 调用 `onMessagesTransform`
  - [x] Step 2: 确认无异常
- Expected Evidence: 正常返回

#### Case U5: transformedMessagesMap 存储
- Goal: 验证处理后的 messages（含 synthetic part）被存储
- Fixture: 同 U1
- Execution:
  - [x] Step 1: 调用 `onMessagesTransform`
  - [x] Step 2: 检查 `transformedMessagesMap.get(sessionID)` 返回的 messages 包含 synthetic part
- Expected Evidence: Map 内容正确

#### Case U6: seededFromHistory 不阻断 Skill Reload
- Goal: 验证已 seed 过的会话仍能在 compact 后收到 Skill Reload
- Fixture:
  ```typescript
  sessionStore.upsert(sessionID, (s) => {
    s.seededFromHistory = true;
    s.loadedSkills = new Set(["dev-flow"]);
    s.needsSkillReload = true;
  });
  const messages = [{ info: { role: "user", sessionID }, parts: [{ type: "text", text: "continue" }] }];
  ```
- Execution:
  - [x] Step 1: 调用 `onMessagesTransform`
  - [x] Step 2: 确认 user message 含 Skill Reload synthetic part
- Expected Evidence: 早退已移除，post-transform 逻辑仍执行

#### Case U7: 无 user message 时不消费 Skill Reload
- Goal: 验证没有可注入目标时保留一次性提醒
- Fixture:
  ```typescript
  sessionStore.upsert(sessionID, (s) => {
    s.loadedSkills = new Set(["dev-flow"]);
    s.needsSkillReload = true;
  });
  const messages = [{ info: { role: "assistant", sessionID }, parts: [{ type: "text", text: "response" }] }];
  ```
- Execution:
  - [x] Step 1: 调用 `onMessagesTransform`
  - [x] Step 2: 确认无异常、无 synthetic part
  - [x] Step 3: 再用含 user message 的 messages 调用 `onMessagesTransform`
  - [x] Step 4: 确认 Skill Reload 仍被注入
- Expected Evidence: 无 user message 时未提前消费

#### Case U8: dump formatter 优先使用 transformedMessagesMap
- Goal: 验证 auto dump 可展示 synthetic Skill Reload
- Fixture:
  ```typescript
  const transformedMessagesMap = new Map([
    [sessionID, [{ info: { role: "user", sessionID }, parts: [{ type: "text", text: "<system-reminder>reload</system-reminder>", synthetic: true }] }]],
  ]);
  ```
- Execution:
  - [x] Step 1: 调用 `writeContextDump({ transformedMessagesMap, ... })`
  - [x] Step 2: 读取 dump 文件
  - [x] Step 3: 确认包含 `> _[synthetic]_` 与 `<system-reminder>`
- Expected Evidence: dump 使用 transformed messages 而非 DB fallback

### Integration Tests

#### Case I1: system-transform 不再注入 Skill Reload
- Goal: 确认 system.transform 不注入 Skill Reload
- Fixture:
  ```typescript
  sessionStore.upsert(sessionID, (s) => {
    s.loadedSkills = new Set(["dev-flow"]);
    s.needsSkillReload = true;
  });
  ```
- Execution:
  - [x] Step 1: 调用 `onSystemTransform`
  - [x] Step 2: 检查 output.system 不包含 `[系统提醒]`
- Expected Evidence: system[] 中无 Skill Reload

### Regression Tests

#### Case R1: compact 后 Skill Reload 完整流程
- Goal: 验证完整链路
- Fixture: 模拟 compact 流程
- Execution:
  - [x] Step 1: `recordSkillLoaded("dev-flow")` → `markCompacted()` → 确认 `needsSkillReload=true`
  - [x] Step 2: 调用 `onSystemTransform` → 确认 system[] 无 Skill Reload
  - [x] Step 3: 调用 `onMessagesTransform` → 确认 user message 含 `<system-reminder>`
  - [x] Step 4: 再次 `onMessagesTransform` → 确认不注入
- Expected Evidence: Skill Reload 仅在 messages.transform 出现一次

## Acceptance Criteria

### Agent Verification

- [x] `bun run test:run` 全部通过
- [x] `bun run build` 编译通过
- [x] system-transform.ts 不注入 Skill Reload
- [x] message-hooks.ts 注入 Skill Reload 到 user message（`<system-reminder>` synthetic part）
- [x] Skill Reload 一次性消费机制正常工作
- [x] transformedMessagesMap 存储处理后的 messages
- [x] Auto dump 优先使用 transformedMessagesMap，能展示 Skill Reload 注入内容

### User Validation

#### Scenario 1: Compact 后 Skill Reload 提醒
- Goal: 确认 compact 后 agent 仍收到技能重载提醒
- Precondition: 会话中已加载技能（如 `/dev-flow`），触发 compact
- User Actions:
  1. 在长会话中加载技能后持续对话触发 compact
  2. compact 完成后发送消息
  3. 观察 agent 是否主动重新加载技能
- Expected Result: agent 收到提醒并重新加载技能

- [ ] 用户已完成上述功能验证并确认结果符合预期

#### Scenario 2: Auto dump 包含 Skill Reload
- Goal: 确认 auto dump 文件能看到 Skill Reload synthetic part
- Precondition: 设置 `WOPAL_PLUGIN_DEBUG=context`，compact 后首轮对话
- User Actions:
  1. 触发 compact + Skill Reload 注入
  2. 查看 logs 目录下的 AUTO-CTXDUMP 文件
  3. 检查 Messages 部分的最后一条 user message
- Expected Result: 包含 `> _[synthetic]_` 和 `<system-reminder>` 内容

- [x] 用户已完成上述功能验证并确认结果符合预期

## References

### OpenCode 源码
- `labs/ref-repos/opencode/packages/opencode/src/session/prompt.ts:1566` — messages.transform 调用
- `labs/ref-repos/opencode/packages/opencode/src/session/prompt.ts:1548-1563` — synthetic parts 不被二次包装
- `labs/ref-repos/opencode/packages/opencode/src/session/message-v2.ts:801-806` — toModelMessagesEffect 不跳过 synthetic
- `labs/ref-repos/opencode/packages/opencode/src/session/llm.ts:118` — system.transform 调用

### 插件源码
- `.wopal/wopal-plugin/src/hooks/system-transform.ts:100-108` — 当前 Skill Reload 注入位置（待删除）
- `.wopal/wopal-plugin/src/hooks/message-hooks.ts` — 迁移目标
- `.wopal/wopal-plugin/src/hooks/index.ts` — hooks 组装入口
- `.wopal/wopal-plugin/src/session-store.ts:119-127` — consumeSkillReload 定义
- `.wopal/wopal-plugin/src/tools/dump-formatter.ts:614-623` — messages 加载逻辑
