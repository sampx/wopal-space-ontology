# perf-wopal-plugin-reduce-token-usage-in-wopal_task_output-tool

## Metadata

- **Type**: perf
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-19
- **Status**: done
- **Worktree**: plugin-reduce-token-usage-in-wopal_task_output-tool | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-plugin-reduce-token-usage-in-wopal_task_output-tool

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

大幅降低 `wopal_task_output` 工具的 token 耗费：`tools` section 仅输出工具名+状态（成功/失败），`text`/`reasoning` 默认返回最后一条消息，清理历史遗留死代码。

## Technical Context

### Architecture Context

`wopal_task_output` 工具用于检查子会话任务状态和输出内容，当前存在严重的 token 浪费问题：

1. **`tools` section 输出完整内容**：`tool_result` 输出可达数万 chars（文件读取、bash 输出），用户无法快速定位失败工具
2. **无状态判断机制**：EllaMaka 数据结构中 `part.state.status`（`"completed"` | `"error"`）未被利用，无法区分成功/失败
3. **`text`/`reasoning` 截断策略不合理**：所有 section 强制 `maxLength=2000`，未区分内容类型需求差异
4. **历史遗留死代码**：`extractFullHistory` 函数定义未调用，`truncateOutput` + `MAX_RECENT_OUTPUT` 仅被一处使用

**涉及模块**：
- `wopal-plugin/src/tools/wopal-task-output.ts` — 工具定义层（调用方）
- `wopal-plugin/src/tasks/session-messages.ts` — 内容提取核心逻辑
- `wopal-plugin/src/tools/output-helpers.ts` — 辅助截断函数
- `wopal-plugin/src/types.ts` — 类型定义（需补充 `state` 字段）

**变更影响范围**：仅影响 `wopal_task_output` 工具输出格式，不影响任务执行逻辑或其他工具。

### Research Findings

**EllaMaka 数据结构调研**：

1. **`tool_result` 状态字段**：`part.state.status` 包含 `"pending"` | `"running"` | `"completed"` | `"error"`，可判断工具执行状态
2. **bash 工具退出码**：`part.state.metadata.exit` 包含进程退出码（`0` = 成功，非 0 = 失败）
3. **错误信息位置**：`part.state.error` 或 `part.state.output`（MCP `isError=true` 时）
4. **OpenCode Issue #16969**：确认 MCP 工具 `isError=true` 时状态映射错误（修复后状态字段可用）

**参考资料**：
- `.wopal/wopal-plugin/src/types.ts:78-86` — `SessionMessage.parts` 类型定义
- `.wopal/wopal-plugin/src/tasks/session-messages.ts:225-269` — `extractBySection` 当前实现
- `https://github.com/anomalyco/opencode/issues/16969` — MCP 工具状态字段修复

### Key Decisions

- D-01: `tools` section 仅输出工具名 + 状态（`(completed)` 或 `(error, exit:1)`），不输出完整结果内容 — 用户目标是"快速定位失败工具"，而非"查看完整输出"，完整内容可在需要时通过其他方式获取
- D-02: `text`/`reasoning` section 默认返回最后一条 assistant 消息内容 — 大多数场景仅需最新回答，历史内容通过 `last_n` 参数显式请求
- D-03: 删除 `extractFullHistory` 死代码 — 定义未调用，维护成本高于价值
- D-04: 保留 `truncateOutput` + `MAX_RECENT_OUTPUT` — 仅用于 `formatProgressOutput` 的 `recentOutput`，running 状态进度摘要需要截断。经分析 `formatProgressOutput` 的 `recentOutput` 来自 `extractAssistantContent(newMessages)`，不涉及 Task 3 重构的 `extractBySection`，故保留截断逻辑
- D-05: 补充 `types.ts` 中 `state` 字段类型定义 — 确保类型安全，避免 `as any` 逃逸
- D-06: MCP 工具状态 fallback 逻辑 — 针对 OpenCode Issue #16969（MCP 工具 `isError=true` 时 `status="completed"` 映射错误），Task 2 实现需增加 fallback：若 `state.status` 缺失或不可靠（如 `completed` 但内容含 `error` 关键词），降级为内容分析判断失败状态

### Key Interfaces

**补充类型定义** (`types.ts`)：

```typescript
// SessionMessage.parts 扩展 state 字段
parts?: Array<{
  type?: string
  tool?: string
  callID?: string
  // 新增 state 字段（用于 tool type）
  state?: {
    status?: "pending" | "running" | "completed" | "error"
    metadata?: { exit?: number }
    error?: string
    input?: unknown
    output?: string
  }
  content?: string | Array<{ type: string; text?: string }>
  // ... 其他字段
}>
```

**核心函数签名变更** (`session-messages.ts`)：

```typescript
// extractBySection 行为变更（不修改签名）
export function extractBySection(
  messages: SessionMessage[],
  section: OutputSection,
  options?: { lastN?: number; maxLength?: number }
): string

// tools section: 仅输出工具名 + 状态
// text/reasoning section: 默认最后一条，多消息时 4000 截断
```

## In Scope

- 补充 `types.ts` 中 `SessionMessage.parts[].state` 类型定义
- 重构 `session-messages.ts` 的 `extractBySection` 函数：
  - `tools` section：仅输出工具名 + 状态（成功/失败/退出码）
  - `text`/`reasoning` section：默认最后一条消息，多消息时聚合截断（maxLength=4000）
- 删除 `extractFullHistory` 死代码
- 评估并保留/删除 `truncateOutput` + `MAX_RECENT_OUTPUT`
- 更新测试用例覆盖新行为

## Out of Scope

- 其他 `wopal_task_*` 工具优化（如 `wopal_task_reply`）
- `wopal-task-output.ts` 工具层参数暴露（如 `maxLength` 参数）
- 子会话压缩策略调整
- MCP 工具状态映射修复（属 EllaMaka 上游问题）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| types | `.wopal/wopal-plugin/src/types.ts` | 修改 | 补充 `state` 字段类型定义 |
| core logic | `.wopal/wopal-plugin/src/tasks/session-messages.ts` | 修改 | 重构 `extractBySection`，删除 `extractFullHistory` |
| helper | `.wopal/wopal-plugin/src/tools/output-helpers.ts` | 修改 | 评估保留/删除 `truncateOutput` |
| test | `.wopal/wopal-plugin/src/tasks/session-messages.test.ts` | 修改 | 更新测试用例覆盖新行为 |

## Acceptance Criteria

### Agent Verification

1. [x] `bun run test:run` 在 `.wopal/wopal-plugin` 执行全部 pass (466 passed)
2. [x] `rg -c 'extractFullHistory' .wopal/wopal-plugin/src` = 0（死代码已删除）
3. [x] `rg 'state\?:' .wopal/wopal-plugin/src/types.ts` ≥ 1（类型定义已补充）
4. [x] `rg '\[tool:' .wopal/wopal-plugin/src/tasks/session-messages.ts` ≥ 1（工具状态输出格式已实现）
5. [x] `rg 'fallback.*error' .wopal/wopal-plugin/src/tasks/session-messages.ts` ≥ 1（MCP 状态 fallback 逻辑已实现）
6. [x] 测试用例覆盖 MCP 工具 `status=completed` 但内容含 `error` 关键词的边界情况（3 个测试用例验证）

### User Validation

#### Scenario 1: tools section 输出精简验证
- Goal: 确认 `wopal_task_output(section="tools")` 仅输出工具名+状态，不再输出完整结果内容
- Precondition: 存在已完成子会话（含多个工具调用，包括成功和失败）
- User Actions:
  1. 执行 `wopal_task_output(task_id="<id>", section="tools")`
  2. 观察输出格式是否为 `[tool: read] (completed)` 或 `[tool: bash] (error, exit:1)`
  3. 确认无完整文件内容或 bash 输出
- Expected Result: 每个工具一行，仅显示工具名和状态，token 显著降低

#### Scenario 2: text/reasoning 默认最后一条验证
- Goal: 确认不指定 `last_n` 时仅返回最后一条 assistant 消息
- Precondition: 子会话有多轮对话（≥3 条 assistant 消息）
- User Actions:
  1. 执行 `wopal_task_output(task_id="<id>", section="text")` 不传 `last_n`
  2. 观察输出是否仅为最后一条消息
  3. 执行 `wopal_task_output(task_id="<id>", section="text", last_n=5)`
  4. 观察输出是否聚合多条并截断（≤4000 chars）
- Expected Result: 默认单条输出简洁，多条时聚合截断

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 补充类型定义

**Verification Intent**: AC#3

**Behavior**: `SessionMessage.parts` 类型定义包含 `state` 字段，支持工具状态判断（`status`、`metadata.exit`、`error`），避免代码中使用 `as any` 逃逸。

**Files**: `.wopal/wopal-plugin/src/types.ts`

**Pre-read**: `.wopal/wopal-plugin/src/types.ts:78-86`（现有 `parts` 类型定义）

**Design**:
在 `SessionMessage.parts` 数组元素类型中补充可选 `state` 字段，定义 `status`（`"pending" | "running" | "completed" | "error"`）、`metadata`（`{ exit?: number }`）、`error`（`string`）和 `input`/`output` 字段。确保类型守卫可用，避免后续代码使用 `as any` 访问状态信息。

**TDD**: true

**Changes**:
1. 在 `parts` 数组元素类型中添加 `state?: { status?: "pending" | "running" | "completed" | "error"; metadata?: { exit?: number }; error?: string; input?: unknown; output?: string }`
2. 添加类型守卫函数 `hasToolState(part: unknown): part is { state: { status?: string; metadata?: { exit?: number }; error?: string } }`

**Verify**: `rg 'state\?:' .wopal/wopal-plugin/src/types.ts` ≥ 1

**Done**:
任务产出：类型定义补充完成，支持工具状态判断
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 重构 tools section 输出逻辑

**Verification Intent**: AC#4

**Behavior**: `extractBySection(messages, "tools")` 仅输出工具名 + 状态（`(completed)` 或 `(error, exit:1)`），不输出完整结果内容。

**Files**: `.wopal/wopal-plugin/src/tasks/session-messages.ts`

**Pre-read**: `.wopal/wopal-plugin/src/tasks/session-messages.ts:240-249`（现有 `tools` section 提取逻辑）

**Design**:
重写 `extractBySection` 函数中 `section === "tools"` 分支：
- 遍历 `relevantMessages` 的 `parts`
- `part.type === "tool"` 时：提取 `part.tool` 和 `part.state?.status`，格式化为 `[tool: ${tool}] (${status})`，若 `state.metadata.exit` 存在则附加 `exit:${exit}`
- `part.type === "tool_result"` 时：提取 `part.state?.status`，格式化为 `[result]: (${status})`，不输出 `content`
- **MCP 状态 fallback 逻辑**（D-06）：若 `state.status` 缺失或为 `"completed"` 但 `content` 含 `"error"`/`"Error"`/`"validation error"` 关键词，降级判断为 `(error, detected-from-content)`
- 使用类型守卫 `hasToolState(part)` 确保类型安全
- 结果拼接为单行列表，无需截断（状态信息长度固定）

**Fallback 检测关键词**：`["error", "Error", "validation error", "isError", "failed", "exception"]`

**TDD**: true

**Changes**:
1. 修改 `extractBySection` 中 `section === "tools"` 分支逻辑
2. `tool` 类型：输出 `[tool: ${tool}] (${status}, exit:${exit})` 或 `[tool: ${tool}] (${status})`
3. `tool_result` 类型：输出 `[result]: (${status})`（不输出 content）
4. 删除原有 `content` 拼接逻辑
5. 增加 MCP 状态 fallback：检测 `content` 含错误关键词时判断为 `(error, detected-from-content)`
6. 添加测试用例验证工具状态输出格式和 MCP fallback 边界情况

**Verify**: `rg '\[tool:' .wopal/wopal-plugin/src/tasks/session-messages.ts` ≥ 1 && `rg 'fallback.*error' .wopal/wopal-plugin/src/tasks/session-messages.ts` ≥ 1

**Done**:
任务产出：`tools` section 输出精简为工具名+状态格式
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 重构 text/reasoning section 输出逻辑

**Verification Intent**: AC#1

**Behavior**: `extractBySection(messages, "text"|"reasoning")` 默认返回最后一条 assistant 消息内容；若指定 `last_n > 1` 则聚合多条消息，截断至 `maxLength=4000`。

**Files**: `.wopal/wopal-plugin/src/tasks/session-messages.ts`

**Pre-read**: `.wopal/wopal-plugin/src/tasks/session-messages.ts:254-258`（现有 `text`/`reasoning` section 提取逻辑）

**Design**:
重构 `extractBySection` 中 `text`/`reasoning` section 分支：
- 默认行为（未指定 `last_n` 或 `last_n=1`）：调用 `getLastAssistantMessage(messages)` 获取最后一条 assistant 消息，提取其 `text`/`reasoning` 部分
- 多消息行为（`last_n > 1`）：遍历 `relevantMessages.slice(-last_n)`，聚合所有 `text`/`reasoning` 内容，截断至 `maxLength=4000`（使用 `slice(-maxLength)` 保留尾部）
- 删除原有默认 `maxLength=2000` 截断逻辑（单条消息无需截断）
- 更新测试用例验证默认单条和多条聚合行为

**TDD**: true

**Changes**:
1. 重构 `section === "text" | "reasoning"` 分支逻辑
2. 默认：调用 `getLastAssistantMessage()` 提取最后一条消息内容
3. 多消息：聚合多条内容，截断至 `maxLength=4000`
4. 删除原有 `maxLength=2000` 默认截断
5. 添加测试用例验证默认单条输出和多条聚合截断

**Verify**: `bun run test:run` 全部 pass

**Done**:
任务产出：`text`/`reasoning` section 默认输出最后一条，多消息聚合截断
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: 清理死代码和更新测试

**Verification Intent**: AC#2, AC#1, AC#5

**Behavior**: 删除未调用的 `extractFullHistory` 函数，保留 `truncateOutput` + `MAX_RECENT_OUTPUT`（仅用于 `formatProgressOutput`，不影响 Task 3 重构），更新测试用例覆盖 Task 2/3 的新行为。

**Files**: `.wopal/wopal-plugin/src/tasks/session-messages.ts`, `.wopal/wopal-plugin/src/tools/output-helpers.ts`, `.wopal/wopal-plugin/src/tasks/session-messages.test.ts`

**Pre-read**: `.wopal/wopal-plugin/src/tasks/session-messages.ts:58-110`（`extractFullHistory` 定义），`.wopal/wopal-plugin/src/tools/output-helpers.ts:9-77`（`truncateOutput` 和 `formatProgressOutput` 实现）

**Design**:
- **删除 `extractFullHistory`**：函数定义从未被调用（grep 结果仅定义处），直接删除函数定义和相关注释
- **保留 `truncateOutput` + `MAX_RECENT_OUTPUT`**：
  - 分析：`truncateOutput` 仅被 `formatProgressOutput`（output-helpers.ts:73）调用，用于截断 running 状态的 `recentOutput`
  - `recentOutput` 来自 `extractAssistantContent(newMessages)`，不涉及 `extractBySection`（Task 3 重构目标）
  - 结论：保留截断逻辑，不受本优化影响
- **更新测试**：修改 `session-messages.test.ts` 中 `extractBySection` 测试用例，覆盖工具状态输出、默认单条输出、多条聚合截断、MCP fallback 四种场景

**TDD**: true

**Changes**:
1. 删除 `extractFullHistory` 函数定义（L58-110）
2. 保留 `truncateOutput` + `MAX_RECENT_OUTPUT`（已分析不影响本优化）
3. 更新 `extractBySection` 测试用例：
   - 添加 `tools` section 工具状态输出测试
   - 添加 MCP fallback 测试（`status=completed` 但内容含 `error` 关键词）
   - 添加 `text`/`reasoning` 默认单条输出测试
   - 添加多条聚合截断测试
4. 运行 `bun run test:run` 验证全部 pass

**Verify**: `rg -c 'extractFullHistory' .wopal/wopal-plugin/src` = 0

**Done**:
任务产出：死代码清理完成，测试覆盖新行为
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 类型定义补充，独立变更，无依赖 |
| 1 | Task 4 | fae | 无 | 死代码清理独立，测试更新依赖 Task 2/3，但可先清理 `extractFullHistory` 并准备测试骨架 |
| 2 | Task 2 | fae | Task 1 | 依赖 Task 1 的类型定义，重构核心逻辑 |
| 2 | Task 3 | fae | Task 1 | 依赖 Task 1 的类型定义，重构核心逻辑 |
| 3 | Task 4 测试部分 | fae | Task 2, Task 3 | 测试用例需验证 Task 2/3 的新行为，必须等待实现完成 |