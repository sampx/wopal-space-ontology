# 103-fix-memory-manage-search

## Metadata

- **Issue**: #103
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-21
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

区分 memory_manage 各子命令的展示义务，让 search 不再强制向用户回显内部检索结果。

## Technical Context

memory_manage 工具的 description 和 ECHO_REMINDER 对所有子命令统一要求"逐字展示给用户"。但 search 有两种使用场景：
1. 用户通过 `/memory search` 主动搜索 → 需要展示（命令层控制）
2. Agent 自主调用检索长期记忆 → 不需要展示，仅供内部参考

当前 `ECHO_REMINDER` 在 `formatters.ts:10-14` 定义，被追加到所有 CRUD 命令返回值（`index.ts:78-103`），包括 `search`。这导致 Agent 即使只想内部检索记忆也被迫向用户回显。

命令层 `/memory`（`commands/memory.md`）有独立的输出规则，不依赖工具层的 ECHO_REMINDER，因此移除 search 的 ECHO_REMINDER 不影响用户主动搜索时的展示。

同样，`stats` 和 `injected` 也可能被 Agent 内部使用，一并移除 ECHO_REMINDER。`list`、`add`、`update`、`delete` 始终需要用户可见，保留 ECHO_REMINDER。

## In Scope

- 移除 `search`、`stats`、`injected` 的 `ECHO_REMINDER`
- 修改工具 description，区分需要展示和不需要展示的子命令
- 更新 `/memory` 命令文档，明确 search 的展示由命令层控制

## Out of Scope

- 修改其他工具的返回协议
- 重构 ECHO_REMINDER 机制本身（如参数化控制）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 工具定义 | `projects/ontology/wopal-plugin/src/tools/memory-manage/index.ts` | 修改 | 移除 search/stats/injected 的 ECHO_REMINDER，修改 description |
| 格式化常量 | `projects/ontology/wopal-plugin/src/tools/memory-manage/formatters.ts` | 修改 | ECHO_REMINDER 不变（list/add/update/delete 仍需） |
| 命令文档 | `projects/ontology/agents/wopal/commands/memory.md` | 修改 | 明确 search 展示规则 |

## Implementation

### Task 1: 修改工具定义和 description

**Files**: `projects/ontology/wopal-plugin/src/tools/memory-manage/index.ts`

**Changes**:
- [ ] Step 1: 修改工具 description，明确区分"需要展示给用户"和"仅供内部使用"的子命令
- [ ] Step 2: `search` case 中移除 `+ ECHO_REMINDER`
- [ ] Step 3: `stats` case 中移除 `+ ECHO_REMINDER`
- [ ] Step 4: `injected` case 中移除 `+ ECHO_REMINDER`

**Verification**: 构建通过 + 单测通过

### Task 2: 更新 /memory 命令文档

**Files**: `projects/ontology/agents/wopal/commands/memory.md`

**Changes**:
- [ ] Step 1: 在输出要求中补充说明：search 结果在 `/memory` 命令下仍需展示给用户（因为用户主动发起）
- [ ] Step 2: 说明展示义务仅由 `/memory` 命令触发，Agent 自主调用 search 无需展示

**Verification**: 文档内容清晰，无歧义

## Delegation Strategy

N/A — 单一任务，Complexity = Low，无需并行委派

## Test Plan

#### Unit Tests

##### Case U1: search 不包含 ECHO_REMINDER
- Goal: 验证 search 返回值不包含"逐字展示给用户"的提示
- Fixture: mock MemoryStore，searchByQuery 返回至少一条记录
- Execution:
  - [ ] Step 1: 调用 createMemoryManageTool 的 execute，command="search", query="test"
  - [ ] Step 2: 检查返回字符串不包含 ECHO_REMINDER 关键文字
- Expected Evidence: 返回值包含搜索结果但不包含"逐字展示"提示

##### Case U2: stats 和 injected 不包含 ECHO_REMINDER
- Goal: 验证 stats/injected 返回值不含强制展示提示
- Fixture: mock Store
- Execution:
  - [ ] Step 1: 分别调用 command="stats" 和 command="injected"
  - [ ] Step 2: 检查返回值不含 ECHO_REMINDER 关键文字
- Expected Evidence: 返回值不含"逐字展示"提示

##### Case R1: list/add/update/delete 仍包含 ECHO_REMINDER
- Goal: 确认需要展示的命令未受影响
- Fixture: mock Store + Embedder
- Execution:
  - [ ] Step 1: 分别调用 list、add、update 命令
  - [ ] Step 2: 检查返回值包含 ECHO_REMINDER
- Expected Evidence: 返回值末尾包含"逐字展示"提示

## Acceptance Criteria

### Agent Verification
- [x] TypeScript 构建通过（`cd projects/ontology/wopal-plugin && npx tsc --noEmit`）
- [x] 单元测试通过（`cd projects/ontology/wopal-plugin && npx vitest run src/tools/memory-manage/`）

### User Validation

#### Scenario 1: Agent 内部检索不再强制回显
- Goal: 确认 Agent 自主调用 memory_manage search 时不再被强制向用户回显结果
- Precondition: Agent 在开发流程中需要回忆之前的经验
- User Actions:
  1. 进行一项需要 Agent 检索记忆的开发任务（如 issue 驱动开发）
  2. 观察 Agent 是否在主线任务中插入不必要的记忆回显
- Expected Result: Agent 检索记忆后直接使用结果继续主线任务，不向用户展示检索内容

- [x] 用户已完成上述功能验证并确认结果符合预期
