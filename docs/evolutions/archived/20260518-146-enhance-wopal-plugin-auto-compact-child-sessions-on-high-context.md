# 146-enhance-wopal-plugin-auto-compact-child-sessions-on-high-context

## Metadata

- **Issue**: #146
- **Type**: enhance
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-18
- **Status**: done
- **Worktree**: issue-146-plugin-auto-compact-child-sessions-on-high-context | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-issue-146-plugin-auto-compact-child-sessions-on-high-context

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

关闭 ellamaka 自动压缩，通过 Plugin 提供上下文压缩能力（工具 + 恢复机制），由主 Agent 通过 skill 策略统一控制主会话和子会话的压缩时机与恢复流程。

## Technical Context

### Architecture Context

**当前架构**：

```
ellamaka (OpenCode)
├── 自动压缩 (compaction.auto=true)
│   ├── overflow 检测 → 自动 compact → autocontinue message
│   └── 不可控、恢复指令固定、metadata 标记不稳定
└── 手动压缩 (/compact API)
    ├── 不创建 autocontinue message
    ├── session 压缩后自然 IDLE
    └── 需要在 Plugin 层补充恢复机制

wopal-plugin (现有)
├── hooks/compaction.ts — compacting hook (已实现)
├── hooks/event-router.ts — session.compacted 事件处理 (已实现)
├── session-store.ts — compactingSince / needsSkillReload 状态 (已实现)
├── hooks/skill-reload-injector.ts — 压缩后注入技能重载提醒 (已实现，但需用户发消息触发)
├── tasks/task-monitor.ts — fetchContextPercent 上下文监控 (已实现)
├── tasks/task-notifier.ts — sendNotification/promptAsync (已实现)
└── tools/context-manage.ts — context_manage 工具 (已实现，需扩展 compact action)
```

**为什么需要变更**：
1. ellamaka 自动压缩不可控 — autocontinue 恢复指令固定，无法执行 WopalSpace 的恢复协议
2. 当前 skill reload 机制依赖用户发送消息才能触发 — 压缩后任务中断
3. 子会话上下文超标会导致 fae 质量下降或执行失败 — 需要主 Agent 可主动干预
4. 需要统一的上下文压缩策略 — 由主 Agent 通过 skill 决策，不依赖 ellamaka 内部逻辑

**变更影响范围**：
- Plugin 层：event-router（事件处理）、context-manage（工具）、hooks/index.ts（注册）
- 配置层：`.wopal/config/settings.jsonc`（关闭 ellamaka 自动压缩）
- Skill 层：space-master（添加压缩策略）
- 不涉及修改 ellamaka 源码

### Research Findings

**1. Compact API 调用路径**：

SDK 中 `session.summarize()` → `POST /session/{id}/summarize` → `compactSvc.create({ sessionID, model, auto: false })` → 手动压缩（不创建 autocontinue message）。

**SDK 类型** (`SessionSummarizeData`)：
```typescript
{
  body?: { providerID: string; modelID: string }
  path: { id: string }
  query?: { directory?: string }
}
```

`auto` 字段不在 SDK 类型中，服务端默认 `false`。

**2. `session.compacted` 事件触发时机**：

```typescript
// compaction.ts:561-576
if (result === "continue") {
  EventV2.run(SessionEvent.Compaction.Ended.Sync, {...})
  yield* bus.publish(Event.Compacted, { sessionID })
}
```

`Bus.publish(Event.Compacted)` 在 autocontinue 块之后触发，不受 `auto` 参数影响。**手动压缩和自动压缩都会触发此事件**（已通过现有代码验证）。

**3. `promptAsync` 能力**：

已在 task-notifier.ts、task-reply.ts、question-relay.ts 中大量使用，可向任意 session 发送消息并触发 LLM 处理：

```typescript
await client.session.promptAsync({
  path: { id: targetSessionID },
  body: {
    parts: [{ type: "text", text: message, synthetic: true }],
  },
})
```

**4. ellamaka 自动压缩关闭方式**：

```typescript
// overflow.ts:20
if (input.cfg.compaction?.auto === false) return false
```

在 `.wopal/config/settings.jsonc` 中配置：
```jsonc
{
  "ellamaka.compaction.auto": false
}
```

关闭后 `input.auto` 始终为 `false`，ellamaka 不再自动创建 continue 消息。

**5. 压缩后状态流转**：

| 压缩类型 | `input.auto` | autocontinue | session 状态 |
|---------|-------------|-------------|-------------|
| 自动压缩 | `true` | 创建 continue message | 自动继续 |
| 手动压缩 | `false` | 不创建 | 自然 IDLE |

**参考资料**：
- `projects/ellamaka/packages/opencode/src/session/compaction.ts:479-558` — autocontinue 逻辑
- `projects/ellamaka/packages/opencode/src/session/compaction.ts:561-576` — Event.Compacted 发布
- `projects/ellamaka/packages/opencode/src/session/overflow.ts:20` — auto 配置读取
- `projects/ellamaka/packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts:226-246` — summarize API handler
- `projects/ellamaka/packages/sdk/js/src/gen/types.gen.ts:2506` — SessionSummarizeData SDK 类型
- `.wopal/wopal-plugin/src/tasks/task-notifier.ts:61-83` — sendNotification / promptAsync 示例
- `.wopal/wopal-plugin/src/hooks/event-router.ts:157-162` — session.compacted 事件处理
- `.wopal/wopal-plugin/src/session-store.ts:105-119` — markCompacting / markCompacted
- `.wopal/wopal-plugin/src/hooks/skill-reload-injector.ts` — skill reload 注入

### Key Decisions

- D-01: **关闭 ellamaka 自动压缩，完全由主 Agent 策略驱动** — ellamaka autocontinue 机制不成熟（metadata 标记不稳定、恢复指令固定、无法自定义），Plugin 自建恢复机制更可控
- D-02: **子会话压缩后不自动发送恢复消息，由主 Agent 通过 wopal_task_reply 控制** — 主 Agent 了解任务状态，可发送更精准的恢复指令；避免 Plugin 盲目恢复
- D-03: **主会话压缩后由 Plugin 自动发送恢复消息** — 主会话 IDLE 后无人可通知，必须由 Plugin 主动发送恢复指令才能继续
- D-04: **使用 SDK `session.summarize()` API（v1）而非 v2 compact** — v2 compact 当前为 no-op stub，v1 summarize 功能完整
- D-05: **压缩策略合并到 space-master skill，不新建独立 skill** — 避免 skill 碎片化，提升触发准确性
- D-06: **context_manage 工具新增 compact action，不新增独立工具** — 上下文管理职责集中，减少 tool 数量

### Key Interfaces

**context_manage 工具扩展**：

```typescript
// tools/context-manage.ts — 新增 compact action
action: "compact"  // 新增
session_id?: string  // 可选，压缩指定 session（wopal-task-xxx 格式压缩子会话）
// 无 threshold 参数 — 工具仅如实汇报上下文占用，压缩决策由主 Agent 根据 skill 策略判断
```

**sessionStore 扩展**：

```typescript
// session-store.ts — SessionState 新增字段
interface SessionState {
  // ...existing...
  needsAutoContinue?: boolean  // 压缩后需要 Plugin 发送恢复消息
}
```

**event-router 扩展**：

```typescript
// hooks/event-router.ts — session.compacted 事件处理扩展
if (eventType === "session.compacted") {
  sessionStore.markCompacted(sessionID)
  const task = taskManager?.findBySession(sessionID)
  if (task) {
    // 子会话：通知主 Agent
    sendCompactedNotification(task)
  } else {
    // 主会话：自动发送恢复消息
    sendAutoContinueForMain(sessionID)
  }
}
```

**OpenCodeSession 类型扩展**：

```typescript
// types.ts — 新增 summarize 方法类型
export interface OpenCodeSession {
  // ...existing...
  summarize?(args: {
    path: { id: string }
    body: { providerID: string; modelID: string }
    query?: { directory: string }
  }): Promise<unknown>
}
```

## In Scope

- `context_manage` 工具新增 `compact` action（支持主会话和子会话）
- `session.compacted` 事件扩展：主会话自动恢复 + 子会话通知主 Agent
- `sessionStore` 扩展 `needsAutoContinue` 标记
- `OpenCodeSession` 类型扩展 `summarize` 方法
- space-master skill 添加上下文压缩策略
- `context_manage` 和相关 hook 新增测试覆盖
- 更新 wopal-plugin 项目规范（AGENTS.md）：补充上下文压缩能力说明
- 更新空间宪法（AGENTS.md）：补充 ellamaka 自动压缩已关闭、压缩由 context_manage 控制
- 沉淀关键决策到长期记忆（LanceDB）：压缩架构决策、使用模式

## Out of Scope

- ellamaka 源码修改 — 不修改 OpenCode 内部逻辑
- 子会话 Plugin 自动触发压缩 — 由主 Agent 策略驱动，不在 Plugin 层自动触发
- 主会话 Plugin 自动触发压缩 — 主 Agent 通过 skill 策略主动调用工具
- 专用 compact 模型配置 — 使用 session 当前模型，不引入额外配置
- 压缩阈值自动检测和通知 — 复用 task-monitor 已有 progress notification 中的上下文信息

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Plugin Tool | `.wopal/wopal-plugin/src/tools/context-manage.ts` | 修改 | 新增 compact action |
| Plugin Types | `.wopal/wopal-plugin/src/types.ts` | 修改 | 新增 summarize 类型 |
| Plugin Hook | `.wopal/wopal-plugin/src/hooks/event-router.ts` | 修改 | session.compacted 事件扩展 |
| Plugin State | `.wopal/wopal-plugin/src/session-store.ts` | 修改 | 新增 needsAutoContinue 字段 |
| Plugin Test | `.wopal/wopal-plugin/src/tools/context-manage.test.ts` | 修改 | compact action 测试 |
| Plugin Test | `.wopal/wopal-plugin/src/hooks/event-router.test.ts` | 修改 | session.compacted 事件测试 |
| Plugin Test | `.wopal/wopal-plugin/src/session-store.test.ts` | 修改 | needsAutoContinue 测试 |
| Skill | `.wopal/skills/space-master/SKILL.md` | 修改 | 添加上下文压缩策略 |
| Project Spec | `.wopal/wopal-plugin/AGENTS.md` | 修改 | 补充上下文压缩能力说明 |
| Space Constitution | `AGENTS.md` | 修改 | 补充上下文压缩机制说明 |
| Memory | LanceDB (memory_manage) | 新增 | 压缩架构关键决策沉淀 |

## Acceptance Criteria

### Agent Verification

1. [x] `rg -c 'action.*compact' .wopal/wopal-plugin/src/tools/context-manage.ts` ≥ 1 — compact action 已定义
2. [x] `rg -c 'summarize' .wopal/wopal-plugin/src/types.ts` ≥ 1 — OpenCodeSession 含 summarize 类型
3. [x] `rg -c 'sendAutoContinueForMain\|sendCompactedNotification' .wopal/wopal-plugin/src/hooks/event-router.ts` ≥ 1 — 事件扩展已实现
4. [x] `rg -c 'needsAutoContinue' .wopal/wopal-plugin/src/session-store.ts` ≥ 1 — sessionStore 含新字段
5. [x] `rg -c 'needsAutoContinue' .wopal/wopal-plugin/src/session-store.test.ts` ≥ 1 — 新字段有测试
6. [x] `cd .wopal/wopal-plugin && bun run test:run` 全部 pass — 所有测试通过
7. [x] `rg -c '上下文压缩' .wopal/skills/space-master/SKILL.md` ≥ 1 — space-master 含压缩策略
8. [x] `rg -c 'context_manage.*compact\|compact action' .wopal/wopal-plugin/AGENTS.md` ≥ 1 — wopal-plugin 规范含 compact 能力描述
9. [x] `rg -c 'space-master.*上下文\|context.*space-master' AGENTS.md` ≥ 1 — 空间宪法引用 space-master skill 控制上下文压缩
10. [x] Agent 执行 `memory_manage command=search query="compact compression context"` 并逐条审查，确认无与新机制冲突/过时的记忆条目 — 过时记忆已清理

### User Validation

#### Scenario 1: 主会话上下文压缩与自动恢复
- Goal: 主 Agent 调用 context_manage(compact) 后，session 被压缩并自动收到恢复指令继续工作
- Precondition: 主会话有较长的对话历史（上下文占用 > 40%）
- User Actions:
  1. 在主会话中让 Agent 执行一个长任务
  2. 观察 Agent 在收到上下文提醒后主动调用 context_manage(compact)
  3. 观察压缩完成后 Agent 是否自动恢复并继续工作
- Expected Result: 压缩后 Agent 自动恢复（重载技能、读取文件、搜索记忆），无需用户手动输入消息

#### Scenario 2: 子会话上下文压缩
- Goal: 主 Agent 检测到子会话上下文超标后，调用 context_manage(compact, session_id="wopal-task-xxx") 压缩子会话
- Precondition: 有一个运行中的子会话（fae），上下文占用较高
- User Actions:
  1. 启动一个复杂 fae 任务
  2. 观察主 Agent 在 progress notification 中看到上下文占用后是否调用压缩
  3. 观察主 Agent 是否通过 wopal_task_reply 发送恢复指令
- Expected Result: 子会话被压缩后收到精准恢复指令，继续执行任务，无需人工干预

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 扩展 sessionStore 和类型定义（基础层）

**Verification Intent**: AC#4, AC#5, AC#2

**Behavior**: sessionStore 支持 `needsAutoContinue` 标记，OpenCodeSession 类型支持 `summarize` 方法。

**Files**: `.wopal/wopal-plugin/src/session-store.ts`, `.wopal/wopal-plugin/src/types.ts`

**Pre-read**: N/A

**Design**:

sessionStore 新增：
- `needsAutoContinue?: boolean` — 压缩完成后标记，供 event-router 判断是否需要发送恢复消息
- `markCompacted()` 方法扩展：设置 `needsAutoContinue = true`

OpenCodeSession 类型扩展：
- 新增 `summarize` 方法类型，参数与 SDK 的 `SessionSummarizeData` 对齐
- 标记为可选（`summarize?`），运行时检查可用性

**TDD**: true

**Changes**:
1. RED: 编写 `sessionStore.test.ts` 测试：验证 `markCompacted()` 后 `needsAutoContinue=true`
2. GREEN: `session-store.ts` 新增 `needsAutoContinue` 字段，`markCompacted()` 中设置
3. RED: 编写类型检查确保 `OpenCodeSession.summarize` 类型定义正确
4. GREEN: `types.ts` 新增 `summarize` 类型
5. REFACTOR: 确保现有测试全部 pass

**Verify**:
`cd .wopal/wopal-plugin && bun test src/session-store.test.ts src/types.test.ts 2>/dev/null || bun run test:run`

**Done**:
任务产出：sessionStore 新增 needsAutoContinue 字段、OpenCodeSession 类型新增 summarize 方法
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 扩展 context_manage 工具（compact action）

**Verification Intent**: AC#1

**Behavior**: `context_manage` 工具支持 `action="compact"`，如实汇报上下文占用并执行压缩，不做阈值判断——压缩决策权归主 Agent。

**Files**: `.wopal/wopal-plugin/src/tools/context-manage.ts`

**Pre-read**: `.wopal/wopal-plugin/src/hooks/event-router.ts`, `.wopal/wopal-plugin/src/tasks/task-monitor.ts`

**Design**:

新增 `compact` action：
- 参数：`session_id?`（默认当前会话，支持 `wopal-task-xxx` 格式）
- 执行流程：
  1. normalize sessionID（处理 `wopal-task-xxx` → `ses_xxx` 转换）
  2. 检查 `sessionStore.isCompacting`（防重触发）
  3. 调用 `fetchContextPercent` 获取当前上下文占用
  4. 获取 session 的 `providerID/modelID`（从 sessionStore）
  5. 调用 `client.session.summarize({ path: { id }, body: { providerID, modelID } })`
  6. 返回结果：当前上下文占用百分比 + 压缩状态
- 错误处理：summarize 不可用返回错误提示；session 不存在返回明确错误；正在压缩中返回状态提示
- 不做阈值判断：工具只负责获取上下文占用并触发压缩，由主 Agent 根据 skill 策略决定

**TDD**: true

**Changes**:
1. RED: 编写 `context-manage.test.ts` 测试：验证 compact action 参数解析和 API 调用
2. GREEN: `context-manage.ts` 新增 compact action 处理分支
3. REFACTOR: 提取 normalizeSessionID 和 fetchContextPercent 为独立工具函数

**Verify**:
`cd .wopal/wopal-plugin && bun test src/tools/context-manage.test.ts`

**Done**:
任务产出：context_manage 工具支持 compact action
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 扩展 event-router（session.compacted 事件处理）

**Verification Intent**: AC#3

**Behavior**: `session.compacted` 事件触发后，根据会话类型自动处理恢复：主会话发送恢复消息，子会话通知主 Agent。

**Files**: `.wopal/wopal-plugin/src/hooks/event-router.ts`

**Pre-read**: `.wopal/wopal-plugin/src/tasks/task-notifier.ts`, `.wopal/wopal-plugin/src/session-store.ts`

**Design**:

扩展 `session.compacted` 事件处理：

```typescript
if (eventType === "session.compacted") {
  ctx.sessionStore.markCompacted(sessionID)
  
  const task = ctx.taskManager?.findBySession(sessionID)
  const state = ctx.sessionStore.get(sessionID)
  
  if (!state?.needsAutoContinue) return  // 非 Plugin 触发的压缩，跳过
  
  if (task) {
    // 子会话：通知主 Agent（通过 promptAsync 到 parentSessionID）
    await sendCompactedNotification(ctx, task, state)
  } else {
    // 主会话：发送恢复消息（通过 promptAsync 到自身）
    await sendAutoContinueForMain(ctx, sessionID, state)
  }
}
```

**sendCompactedNotification** 内容：
```typescript
const notification = `<system-reminder>
[WOPAL TASK COMPACTED]
Task ID: ${task.id}
Description: ${task.description}
Skills: ${skills.join(", ")}
The child session has been compacted and is now IDLE.
Use wopal_task_reply to send recovery instructions if the task should continue.
</system-reminder>`
```

**sendAutoContinueForMain** 内容：
```typescript
const recoverText = `<system-reminder>
The session context has been compacted. Execute recovery protocol immediately and continue working:
<CRITICAL_RULE>
1. Read key files from the compaction summary (plans, specs, etc. — max 3)
2. Search and load task-relevant memories (max 3)
3. Reload previously loaded skills: ${skills}
4. Briefly report what was recovered, then continue the previous work
</CRITICAL_RULE>
</system-reminder>`
```

**TDD**: true

**Changes**:
1. RED: 编写 `event-router.test.ts` 测试：验证主会话 compacted 事件触发 sendAutoContinueForMain
2. RED: 编写测试：验证子会话 compacted 事件触发 sendCompactedNotification
3. GREEN: `event-router.ts` 扩展 session.compacted 事件处理逻辑
4. REFACTOR: 提取消息构建函数，确保与 task-notifier 无重复代码

**Verify**:
`cd .wopal/wopal-plugin && bun test src/hooks/event-router.test.ts`

**Done**:
任务产出：event-router 支持 session.compacted 后自动恢复/通知
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: space-master 压缩策略（skill 文档）

**Verification Intent**: AC#7

**Behavior**: space-master skill 包含上下文压缩策略，指导主 Agent 决策何时及如何压缩。

**Files**: `.wopal/skills/space-master/SKILL.md`

**Pre-read**: `.wopal/skills/space-master/SKILL.md`

**Design**:

space-master SKILL.md 新增上下文压缩策略章节：

```markdown
## 上下文压缩策略

### 监控信号
收到 progress notification 包含上下文占用信息：`[WOPAL TASK PROGRESS] Context: 55% used ⚠️`

### 决策规则
| 上下文占用 | 建议 |
|----------|------|
| < 45% | 无需关注 |
| 45-55% | 评估任务复杂度 |
| ≥ 55% | 建议压缩（fae 质量下降风险） |
| ≥ 75% | 紧急压缩 |

### 安全检查
- 无关键未提交变更
- 无阻塞依赖
- 子会话非 stuck 状态

### 执行
主会话: `context_manage(action="compact")`
子会话: `context_manage(action="compact", session_id="wopal-task-xxx")`

### 恢复
主会话压缩后自动恢复。
子会话压缩后收到 [WOPAL TASK COMPACTED] 通知，主 Agent 用 wopal_task_reply 发送恢复指令。
```

**TDD**: false — Skill 文档变更，非代码逻辑

**Changes**:
1. `.wopal/skills/space-master/SKILL.md` 新增上下文压缩策略章节

**Verify**:
`rg '上下文压缩' .wopal/skills/space-master/SKILL.md` ≥ 1

**Done**:
任务产出：space-master skill 含上下文压缩策略
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 5: 项目规范和记忆同步

**Verification Intent**: AC#8, AC#9, AC#10

**Behavior**: 实施完成后，项目规范、空间宪法和长期记忆同步更新，描述与实现一致，清理过时信息避免误导后续 Agent。

**Files**: `.wopal/wopal-plugin/AGENTS.md`, `AGENTS.md`, LanceDB

**Pre-read**: `.wopal/wopal-plugin/AGENTS.md`, `AGENTS.md`

**Design**:

**wopal-plugin/AGENTS.md 更新**：
- tools 章节：补充 `context_manage` compact action 说明
- hooks 章节：补充 event-router 的 session.compacted 自动恢复行为
- context 模块归属：补充上下文压缩能力描述

**空间宪法 AGENTS.md 更新**：
- 简洁描述：上下文压缩由主 Agent 控制，Agent 必须主动加载 `space-master` 技能获取上下文压缩策略
- 不在此处展开具体策略细节（策略归属 skill）

**长期记忆清理**（重点）：
- 搜索现有记忆中与压缩/上下文相关的条目（`memory_manage command=search query="compact compression context 上下文 压缩"`）
- 逐条分析是否与新机制冲突：
  - 冲突/过时 → `memory_manage command=update` 修正或 `delete` 移除
  - 仍有效但与新机制无关 → 保留不动
- 目标：消除过时信息对后续 Agent 的误导，而非新增决策记录（决策已沉淀在 skill 和代码中）

**TDD**: false — 文档和记忆变更，非代码逻辑

**Changes**:
1. `.wopal/wopal-plugin/AGENTS.md` 更新 tools/hooks/context 章节，补充上下文压缩能力
2. `AGENTS.md` 更新，简洁说明上下文压缩由 space-master skill 控制
3. 搜索并清理 LanceDB 中与新压缩机制冲突/过时的记忆条目

**Verify**:
`rg 'compact action\|上下文压缩' .wopal/wopal-plugin/AGENTS.md` ≥ 1 & `rg 'space-master.*上下文\|context.*space-master' AGENTS.md` ≥ 1 & Agent 执行 `memory_manage command=search query="compact compression context"` 确认无冲突/过时条目

**Done**:
任务产出：项目规范、空间宪法已同步更新，过时记忆已清理
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1: sessionStore + 类型 | fae | 无 | 基础层变更，无依赖，可独立执行 |
| 1 | Task 4: space-master skill | Wopal | 无 | 纯 skill 文档变更，无代码逻辑 |
| 2 | Task 2: context_manage | fae | Task 1 | 依赖新类型定义和 sessionStore 字段 |
| 2 | Task 3: event-router | fae | Task 1 | 依赖 sessionStore.needsAutoContinue 字段 |
| 3 | Task 5: 文档和记忆同步 | Wopal | Task 2,3,4 | 依赖所有实现完成，确保描述与代码一致 |
| 3 | 全量测试 + verify | Wopal | Task 2,3 | 集成验证，确认各模块协作正确 |

**Wave 1**：Task 1 委派 fae（代码变更），Task 4 由 Wopal 直接执行（skill 文档，无代码逻辑）。两者 files 不交集，可并行。

**Wave 2**：Task 2 和 Task 3 依赖 Task 1 的产出。两者 files 不交集，可并行委派 fae。

**Wave 3**：Task 5 依赖所有实现完成（确保描述与代码一致），由 Wopal 执行文档更新和记忆沉淀。全量测试并行执行，验证集成效果。
