# 74-refactor-rules-plugin

## Metadata

- **Issue**: #74
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-08
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

降低 rules-plugin 调试日志噪音（~85%），并为所有注入日志添加会话来源标记（main / task / child），使日志可用于区分主会话与子会话行为。

## Technical Context

### 问题

每次 LLM turn 触发 `onSystemTransform`，产生 ~12 行无意义日志（222 行日志中 ~70% 是噪音），且完全无法区分日志来自主会话还是 wopal-task / 内置 task tool 创建的子会话。

### 会话来源的三种类型

| 来源 | 创建方式 | 识别特征 |
|------|---------|----------|
| **主会话** | 用户直接对话 | `taskManager.findBySession(id)` = undefined 且 session API 无 `parentID` |
| **wopal-task 子会话** | `SimpleTaskManager.launch()` | `taskManager.findBySession(id)` 找到 task（ID 格式 `wopal-task-*`） |
| **内置 task tool 子会话** | OpenCode 内置 task 工具 | `taskManager.findBySession(id)` = undefined 但 session API 返回有 `parentID` |

### 现有基础

`runtime.ts:249-283` 的 `isChildSession()` 已实现两级检测（wopal-task + parentID），但仅在记忆注入时使用。规则注入链路完全无会话标记。

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| 日志基础设施 | `debug.ts` | 无需改动，现有 `createDebugLog` 已满足 |
| 规则注入链路 | `utils.ts` | 删除噪音日志（cache hit/miss、skip conditional） |
| 运行时钩子 | `runtime.ts` | 新增 `getSessionTag()`，为注入日志添加会话标记 |
| 任务管理 ticker | `simple-task-manager.ts` | 无任务时静默 health check 日志 |

## In Scope

- [ ] 删除 `utils.ts` 中的纯噪音日志（Cache hit/miss、Skipping conditional rule）
- [ ] 删除 `runtime.ts` 中的 `Built-in tools` 日志
- [ ] `No applicable rules` 改为每 session 首次才输出
- [ ] 新增 `getSessionTag()` 方法，区分 `[main]` / `[task:xxxxx]` / `[child]`
- [ ] `onSystemTransform` 入口获取 tag，后续日志统一携带
- [ ] `readAndFormatRules` 的 `Including conditional rule` 日志携带 tag
- [ ] `Updated lastUserPrompt` 日志携带 tag
- [ ] `[ticker] health check` 仅在有任务时输出（无任务时静默）

## Out of Scope

- 不新增日志级别（verbose/debug/info）机制 — 环境变量过滤已够用
- 不重构 debug.ts — 现有能力满足需求
- 不改动 memory 模块的日志 — 专属 `[wopal-memory]` prefix 已区分

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `projects/ontology/agents/wopal/plugins/rules-plugin/src/runtime.ts` | 修改 | 新增 `getSessionTag()`，调整日志输出 |
| `projects/ontology/agents/wopal/plugins/rules-plugin/src/utils.ts` | 修改 | 删除噪音日志，`readAndFormatRules` 增加 `logTag` 参数 |
| `projects/ontology/agents/wopal/plugins/rules-plugin/src/simple-task-manager.ts` | 修改 | ticker 日志条件化（无任务时静默） |

## Implementation

### Task 1: 新增 `getSessionTag()` 会话标记

**Files**: `runtime.ts`

**Changes**:
1. 新增 `sessionTypeCache` (Map<string, string>)，复用 `isChildSession` 的缓存思路
2. 新增 `getSessionTag(sessionID: string): Promise<string>` 方法：
   - `taskManager.findBySession(sessionID)` 命中 → 返回 `[task:xxxxx]`（task ID 末 6 位）
   - session API 返回 `parentID` → 返回 `[child]`
   - 都不命中 → 返回 `[main]`
3. 与 `childSessionCache` 合并为一个统一缓存，避免重复 session API 调用

**Verification**: 构建通过

- [x] Step 1: 实现 `getSessionTag()` + 统一缓存
- [x] Step 2: `bun run build` 通过

### Task 2: 规则注入链路添加会话标记 + 删噪音

**Files**: `runtime.ts`, `utils.ts`

**Changes**:
1. `runtime.ts` — `onSystemTransform()` 入口调用 `getSessionTag(sessionID)` 获取 tag
2. `runtime.ts` — `No applicable rules` 日志加 tag，且用 Set 记录已输出过的 sessionID（每 session 只打一次）
3. `runtime.ts` — 删除 `Built-in tools: ...` 日志（`queryAvailableToolIDs` 中的 `debugLog`）
4. `runtime.ts` — `Updated lastUserPrompt` 日志加 tag
5. `utils.ts` — 删除 `getCachedRule` 中的 `Cache hit` 和 `Cache miss` 日志
6. `utils.ts` — 删除 `readAndFormatRules` 中的 `Skipping conditional rule: ...` 日志
7. `utils.ts` — `readAndFormatRules` 新增可选参数 `logTag?: string`，`Including conditional rule` 日志携带 tag

**Verification**: 构建通过 + 单元测试通过

- [x] Step 1: `onSystemTransform` 入口获取 tag 并传递
- [x] Step 2: 删除 utils.ts 中 3 处噪音日志
- [x] Step 3: `Including conditional rule` 携带 tag
- [x] Step 4: `bun run test:run` 通过

### Task 3: Ticker 日志条件化

**Files**: `simple-task-manager.ts`

**Changes**:
1. `tickerInterval` 回调中，先检查 `this.tasks.size === 0`，无任务时跳过 `health check` 日志输出
2. 有任务时保持现有日志不变

**Verification**: 构建通过

- [x] Step 1: ticker 无任务时静默
- [x] Step 2: `bun run build` 通过
- [ ] Step 2: `bun run build` 通过

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 + Task 2 + Task 3 | fae | 无（同一文件组，顺序执行） |

## Test Plan

### Test Case Design

- 会话标记正确性：手动检查日志输出格式是否包含 `[main]` / `[task:xxxxx]` / `[child]` 标记
- 噪音消除：启用 `WOPAL_PLUGIN_DEBUG=rules` 后，一次对话只输出 1 条 `No applicable rules`（而非 7 条）
- 缓存行为：Cache hit/miss 日志消失不影响规则注入功能
- Ticker 静默：无任务时日志文件无 `[ticker]` 行

### Regression Testing

- 规则匹配成功时 `Including conditional rule` 仍正常输出（带 tag）
- 记忆注入日志不受影响（使用 `[wopal-memory]` prefix）
- `debug.test.ts` 现有测试通过（该测试不依赖被删除的日志内容）

### Adjustment Strategy

- 若 `getSessionTag` 的 session API 调用影响性能 → 缓存已在方案中，无需额外调整
- 若测试依赖被删除的日志字符串 → 更新测试断言

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 通过
- [x] `bun run test:run` 通过（396 tests passed）
- [x] 日志中不再出现 `Cache hit`、`Cache miss`、`Skipping conditional rule`、`Built-in tools` 行
- [x] `No applicable rules` 同一 session 只输出一次（`noRulesReportedSessions` Set 控制）
- [x] 所有 `[wopal-rules]` 日志携带会话来源标记 `[main]` / `[task:xxxxx]` / `[child]`

### User Validation

- [x] 启用调试日志，进行一次多轮对话 + 启动一个 wopal_task，确认日志格式正确、噪音显著降低
- [x] 确认规则匹配成功时 `Including conditional rule` 仍可见（带 tag）

**验证结果**（2026-04-08 16:02）：
- 主会话日志：`[main] Updated lastUserPrompt` / `[main] Including conditional rule` / `[main] Injecting rules`
- 子会话日志：`[task:p0kt2t] Updated lastUserPrompt` / `[task:p0kt2t] No applicable rules`
- 噪音日志已消除：无 `Cache hit/miss`、`Skipping conditional rule`、`Built-in tools`
- `No applicable rules` 每个 session 只输出一次
- 所有规则注入日志正确携带会话标记
