# enhance-compaction-reuse-compaction-summary-for-auto-session-title

## Metadata

- **Type**: enhance
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal/
- **Project Type**: ontology-worktree
- **Created**: 2026-05-26
- **Status**: done
- **Worktree**: reuse-compaction-summary-for-auto-session-title | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-reuse-compaction-summary-for-auto-session-title

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

压缩（compaction）完成后，复用 ellamaka 内部 compaction agent 已生成的结构化摘要文本，自动提取 session title（≤80字符）并注入恢复消息，消除手动 `context_manage(summary)` 所需的独立 LLM 调用。

## Technical Context

### Architecture Context

当前 compaction 和 summary 是两个独立流程：

1. **compaction**：Agent 调用 `context_manage(compact)` → ellamaka 内部 compaction agent 生成结构化摘要（Goal/Instructions/Discoveries/Accomplished）→ `session.compacted` 事件 → 插件发送恢复消息。整个过程中，compaction agent 的输出被 ellamaka 存入消息流，但插件完全忽略。

2. **summary**：Agent 手动调用 `context_manage(summary)` → 插件获取消息 → 截断 → 独立 LLM 调用（distillLLM.complete）→ 生成 ≤50 字摘要 → 更新 session title + 保存 SessionContext.summary。这产生了一次额外的 LLM 请求。

关键发现：ellamaka 在 compaction 过程中发出 `session.next.compaction.ended` 事件，其 `properties.text` 包含完整的 compaction summary 文本。该事件在 `session.compacted` 之前触发。

### Research Findings

1. ellamaka 内部 compaction agent 输出固定结构：`## Goal` → `## Instructions` → `## Discoveries` → `## Accomplished` → `## Relevant files / directories`
2. `session.next.compaction.ended` 事件携带 `{ sessionID, text, include?, timestamp }` — `text` 是完整摘要
3. `session.compacted` 事件仅携带 `{ sessionID }`，不含摘要内容
4. 两个事件时序：`session.next.compaction.ended` → `session.compacted`
5. v2 SDK 定义了 `SessionMessageCompaction` 类型，包含 `summary: string` 字段，可通过 `client.session.messages()` 在压缩后读取

**参考资料**：
- `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`
- `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts`
- `.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts`
- `.wopal/plugins/wopal-plugin/src/session-store.ts`
- `.wopal/plugins/wopal-plugin/src/memory/session-context.ts`
- SDK 类型：`~/.wopal/ellamaka/config/node_modules/@opencode-ai/sdk/dist/v2/gen/types.gen.d.ts`

### Key Decisions

- D-01: 通过捕获 `session.next.compaction.ended` 事件获取 compaction 摘要，而非调用 `client.session.messages()` 再解析。理由：事件驱动零延迟，不依赖消息 API 的分页/格式变化。
- D-02: 从 `## Goal` 段落首行提取 title（纯字符串解析），不需要 LLM。理由：compaction agent 的 Goal 段天然就是一句话核心意图概括，质量等同于 LLM 生成的 50 字摘要。
- D-03: 保留 `handleSummary()` 手动调用路径，但标记为 fallback。理由：向后兼容，且在无 compaction 场景下用户仍可手动生成摘要。
- D-04: compaction 全文注入恢复消息，截断至 1500 字符。理由：恢复消息不需要完整摘要，1500 字符足以覆盖 Goal + Accomplished + key files。

### Key Interfaces

```typescript
// session-store.ts — SessionState 新增字段
interface SessionState {
  // ... existing fields ...
  compactionSummaryText?: string;  // 暂存 compaction agent 产出的完整摘要
}

// session-store.ts — 新增方法
class SessionStore {
  setCompactionSummary(sessionID: string, text: string): void;
  consumeCompactionSummary(sessionID: string): string | null;
}

// idle-compact-handler.ts — 新增辅助函数
function extractTitleFromCompaction(text: string): string;

// idle-compact-handler.ts — handleSessionCompacted 签名不变，内部流程变更
// sendAutoContinueForMain / sendCompactedNotification 新增可选 compactionText 参数
```

## In Scope

- 捕获 `session.next.compaction.ended` 事件，缓存摘要文本
- 在 `handleSessionCompacted` 中消费缓存，提取 title 并保存 SessionContext
- 将 compaction 摘要注入恢复消息（主会话 + 子会话通知）
- 更新 session title via API
- SessionContext.summary 自动生成（复用 Goal 行）

## Out of Scope

- 修改 ellamaka 内部 compaction agent 的 prompt 模板（不在插件控制范围内）
- 移除 `handleSummary()` 的独立 LLM 路径（保留为 fallback）
- 修改 `buildEnrichedQuery()` 的消费逻辑（它已经能读 SessionContext.summary，无需改动）
- 新增环境变量开关（后续观察再决定）

## Business Rules Impact

N/A — 无业务规则变更

### 同步确认
- [x] 已将上述变更同步到 `BUSINESS_RULES.md`

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| session-store | `.wopal/plugins/wopal-plugin/src/session-store.ts` | 修改 | 新增 compactionSummaryText 字段和存取方法 |
| event-router | `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts` | 修改 | 新增 `session.next.compaction.ended` 事件监听 |
| compact-handler | `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts` | 修改 | 消费摘要、提取 title、注入恢复消息 |
| tests | `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts` 对应测试 | 修改 | 覆盖自动摘要的新测试用例 |

## Acceptance Criteria

### Agent Verification

1. [x] `rg -c 'compactionSummaryText' .wopal/plugins/wopal-plugin/src/session-store.ts` ≥ 1（SessionState 新字段存在）
2. [x] `rg -c 'setCompactionSummary' .wopal/plugins/wopal-plugin/src/session-store.ts` ≥ 1（缓存方法存在）
3. [x] `rg -c 'consumeCompactionSummary' .wopal/plugins/wopal-plugin/src/session-store.ts` ≥ 1（消费方法存在）
4. [x] `rg 'session\.next\.compaction\.ended' .wopal/plugins/wopal-plugin/src/hooks/event-router.ts` 匹配 ≥ 1（事件路由已添加）
5. [x] `rg -c 'extractTitleFromCompaction' .wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts` ≥ 1（title 提取函数存在）
6. [x] `cd .wopal/plugins/wopal-plugin && bun run typecheck` exit 0
7. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run` 全部 pass

### User Validation

#### Scenario 1: 压缩后自动生成 session title
- Goal: 压缩完成后 session title 自动更新为 compaction 摘要的 Goal 行，无需手动调用 summary
- Precondition: 活跃会话，上下文使用率较高，已触发过至少一轮对话
- User Actions:
  1. 让 Agent 调用 `context_manage(action="compact")` 触发压缩
  2. 等待压缩完成，观察恢复消息
  3. 检查 session title 是否自动更新
- Expected Result: session title 变为 compaction 摘要中的核心意图描述（≤80字符），恢复消息中包含 compaction summary 摘要段

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: SessionStore 新增 compaction summary 缓存

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: `SessionStore` 支持 `setCompactionSummary(sessionID, text)` 写入和 `consumeCompactionSummary(sessionID)` 原子读取并清除。consume 返回 text 后自动删除字段，防止重复消费。

**Files**: `.wopal/plugins/wopal-plugin/src/session-store.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/session-store.ts`

**Design**:

1. `SessionState` 接口新增 `compactionSummaryText?: string`
2. `setCompactionSummary(sessionID, text)` — 调用 `upsert` 写入
3. `consumeCompactionSummary(sessionID)` — 读取后通过 `upsert` 删除，返回 text 或 null

**TDD**: true

**Changes**:
1. 在 `SessionState` 接口的 `contextWarningsSent` 字段后新增 `compactionSummaryText?: string`
2. 在 `SessionStore` 类的 `consumeRecoveryInjection` 方法后新增 `setCompactionSummary` 方法
3. 在 `setCompactionSummary` 方法后新增 `consumeCompactionSummary` 方法

**Verify**: `rg -c 'compactionSummaryText\|setCompactionSummary\|consumeCompactionSummary' .wopal/plugins/wopal-plugin/src/session-store.ts` ≥ 3

**Done**:
任务产出：SessionStore 新增 compaction summary 缓存的存取方法
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 事件路由捕获 compaction summary

**Verification Intent**: AC#4

**Behavior**: `event-router.ts` 的 `onEvent` 函数新增 `session.next.compaction.ended` 事件分支，从 `properties.text` 提取摘要文本，调用 `sessionStore.setCompactionSummary(sessionID, text)` 缓存。

**Files**: `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts`

**Design**:

在 `session.compacted` 事件处理块之前添加新的事件分支。解析 `props.text` 和 `props.sessionID`，调用缓存方法。日志级别使用 debug。

**TDD**: true

**Changes**:
1. 在 `session.idle` 事件块和 `session.compacted` 事件块之间，新增 `session.next.compaction.ended` 事件处理块
2. 从 `props` 提取 `text` 和 `sessionID`，校验非空后调用 `ctx.sessionStore.setCompactionSummary(sessionID, text)`
3. 添加 debug 级别日志记录捕获行为

**Verify**: `rg 'session\.next\.compaction\.ended' .wopal/plugins/wopal-plugin/src/hooks/event-router.ts` 匹配 ≥ 1

**Done**:
任务产出：事件路由器新增 compaction summary 事件的捕获和缓存
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: idle-compact-handler 消费摘要并注入恢复消息

**Verification Intent**: AC#5, AC#6, AC#7

**Behavior**: `handleSessionCompacted` 在 `markCompacted` 之前消费缓存的 compaction summary：提取 title（≤80字符）→ 更新 session title → 保存 SessionContext.summary → 将全文注入恢复消息。恢复消息（主会话 + 子会话）新增 compaction summary 段落。

**Files**: `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`

**Pre-read**:
- `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`
- `.wopal/plugins/wopal-plugin/src/memory/session-context.ts`
- `.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts`（参考 handleSummary 的 SessionContext 保存逻辑）

**Design**:

1. **新增 `extractTitleFromCompaction(text: string): string`**
   - 尝试匹配 `## Goal\n\s*(.+)` 正则，取捕获组第一行
   - Fallback: 取第一个非空、非 `#` 开头、非 `---` 的行
   - 最终 fallback: 截取 text 前 50 字符
   - 结果 truncate 至 80 字符

2. **改造 `handleSessionCompacted`**
    - 在函数开头（`markCompacted` 之前）调用 `consumeCompactionSummary`
    - 如果有 text：提取 title → 保存 SessionContext → 尝试更新 session title via API
    - **API 失败 fallback**：`updateSessionTitle` 调用包裹在 try/catch 中；失败时记录 debug 日志，但仍继续保存 `SessionContext.summary` 和注入恢复消息 — 这是最小成功保证（title 可由下次 compaction 或手动 summary 补偿）
    - 将 compactionText 传递给 `sendAutoContinueForMain` 和 `sendCompactedNotification`

3. **改造 `sendAutoContinueForMain`**
   - 新增可选参数 `compactionText?: string | null`
   - 在恢复消息 `<system-reminder>` 的 `<CRITICAL_RULE>` 前注入 compaction summary 段（截断 1500 字符）
   - 示例：`\n## Compaction Summary\n${compactionText.slice(0, 1500)}\n`

4. **改造 `sendCompactedNotification`**
   - 新增可选参数 `compactionText?: string | null`
   - 在通知消息中注入摘要信息

**TDD**: true

**Changes**:
1. 在文件顶部新增 import：`loadSessionContext`, `saveSessionContext`, `SessionContext` from `../../memory/session-context.js`
2. 新增 `extractTitleFromCompaction(text: string): string` 纯函数
3. 修改 `handleSessionCompacted`：在 `markCompacted` 前消费摘要、提取 title、保存 SessionContext、更新 session title（try/catch 包裹 API 调用，失败不阻塞后续流程）
4. 修改 `sendAutoContinueForMain` 签名新增 `compactionText` 参数，恢复消息中注入摘要
5. 修改 `sendCompactedNotification` 签名新增 `compactionText` 参数，通知中注入摘要

**Test Cases**（覆盖审查要求的边界）:

`extractTitleFromCompaction` 单测：
- 正常 `## Goal\n核心意图描述` → 返回 `核心意图描述`
- `## Goal` 后跟空行再跟内容 → 返回内容行
- 无 `## Goal` 段 → fallback 到首个非空、非 `#` 开头、非 `---` 的行
- 首行是 `#` 标题或 `---` 分隔线 → 跳过，取下一有效行
- 全部无效 → fallback 到 text 前 50 字符
- 超长文本 → truncate 至 80 字符

消费链集成测试：
- 模拟 `session.next.compaction.ended`（写入 summary）→ `session.compacted`（消费 summary）→ 验证 SessionContext.summary 已保存、恢复消息已注入
- 验证事件时序依赖：ended 先于 compacted 才能正确消费

API 失败降级测试：
- mock `updateSessionTitle` reject → 验证 SessionContext.summary 仍保存、恢复消息仍发送、debug 日志已记录

**Verify**: `cd .wopal/plugins/wopal-plugin && bun run typecheck && bun run test:run`

**Done**:
任务产出：压缩完成后自动提取 title、保存摘要、注入恢复消息的完整链路
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 纯数据结构改动，独立无依赖 |
| 1 | Task 2 | fae | 无 | 事件路由独立，不依赖 Task 1 的方法签名（仅依赖 import） |
| 2 | Task 3 | fae | Task 1, Task 2 | 依赖 Task 1 的 SessionStore 方法和 Task 2 的事件缓存 |

Task 1 和 Task 2 可并行。Task 3 依赖两者完成后才能正确编译。

## Supplementary Optimizations

以下为原 Plan 实施完成后追加的优化调整，不修改实施方案部分。

### 1. 移除 context_manage summary action

**原因**：后台 title 自动生成已覆盖原手动 summary 功能，不再需要独立 LLM 调用生成会话摘要。

**变更**：
- `context-manage.ts`：移除 enum 中的 `summary`、`distillLLM` 参数
- `context-manage-actions.ts`：删除 `handleSummary` 函数
- `index.ts`：`createContextManageTool` 不再传 `llm` 实例
- 记忆中删除 `context_manage summary` 相关记录，更新残留引用

### 2. LLM 客户端模块迁移与优化

**原因**：LLM 不再仅服务 memory 蒸馏，也用于 title 生成等场景，应从 memory 模块提升为共享基础设施。

**变更**：
- `DistillLLMClient` → `LLMClient`，文件从 `src/memory/llm-client.ts` 迁移至 `src/llm-client.ts`
- 日志从 `memoryLogger` 迁移至 `coreLogger`
- ready 日志新增 API URL 输出：`LLMClient ready: <model> @ <baseURL>`

### 3. 提示词文件独立化

**原因**：提示词移出 TS 源码，放入 `plugins/wopal-plugin/prompts/` 目录，支持热加载修改无需重启。

**变更**：
- `prompts/distill.md`：英文版记忆蒸馏提示词（含 Tags Specification 章节，对齐 `mem-rule.md` 标签设计规范）
- `prompts/dedup.md`：英文版记忆去重提示词
- `prompts/title.md`：引入 ellamaka 原生 title agent 提示词，适应性调整输入为 compaction summary
- `src/memory/prompts.ts`：重构为 `setPluginDirectory()` + `loadPromptFile()` 架构，env var 覆盖优先级高于 `prompts/` 目录
- 三份提示词均添加输出语言规则：从输入对话推断用户语言

### 4. 验证

`cd .wopal/plugins/wopal-plugin && bun run typecheck && bun run test:run` — typecheck 通过，742/742 tests pass。

---

完成后在 Plan 文件中编辑对应 Task 的 Done checkbox（- [ ] → - [x]），Plan 文件路径：/Users/sam/coding/wopal/wopal-workspace/docs/projects/wopal-space/plans/enhance-compaction-reuse-compaction-summary-for-auto-session-title.md
禁止修改 Plan Status
