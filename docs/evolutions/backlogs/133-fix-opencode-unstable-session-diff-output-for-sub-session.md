# 133-fix-opencode-unstable-session-diff-output-for-sub-session

## Metadata

- **Issue**: #133
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-26
- **Updated**: 2026-04-28
- **Status**: planning

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

Fix `wopal_task_diff` to reliably return file changes for sub-sessions, using a hybrid approach that combines tool metadata (session-scoped, authoritative) with snapshot diff (worktree-scoped, supplementary).

## Technical Context

### 问题根因

OpenCode `session.diff` 依赖 snapshot 系统的 `step-start`/`step-finish` parts 中的 hash 来计算 diff。存在两个已确认的缺陷：

1. **Race Condition Bug**（官方已知，`snapshot-tool-race.test.ts` + `processor.ts:109-111` 注释）：AI SDK 可能在 emit `start-step` 事件前内部执行 tool，导致 before/after snapshot hash 相同 → diff 为空。
2. **Worktree-Global Scope Bug**（Issue #11802，OPEN）：snapshot diff 基于 `Instance.worktree` 全局状态，并发 session 互相污染 → 跨 session 文件变更归因错误。

### 混合方案：tool metadata + snapshot diff

**数据源分析**：

| 数据源 | edit | write | apply_patch | bash | scope | diff 统计 |
|--------|------|-------|-------------|------|-------|-----------|
| tool metadata | `filediff: {file, patch, additions, deletions}` ✓ | `filepath` ✓ | `files: [{relativePath, patch, additions, deletions, type}]` ✓✓ | ❌ | session-scoped | edit/apply_patch 精确 |
| snapshot diff | ✓ | ✓ | ✓ | ✓ | worktree-global | ✓ 精确 |

**合并策略**：

```
tool metadata → session-scoped（权威，不受并发污染）
snapshot diff → worktree-global（补充，覆盖 bash 等盲区）

合并规则：
  - 同文件 → 取 tool metadata 版本（session-scoped 更权威）
  - snapshot diff 中 metadata 未覆盖的文件 → 补充纳入（主要是 bash 产生的）
  - snapshot diff 为空 → 仅靠 metadata（大多数情况已足够）
```

**关键收益**：即使 snapshot diff 完全为空（当前 bug），edit/write/apply_patch 的变更仍能正确返回。bash 盲区在 sub-agent 场景下影响很小（sub-agent 绝大多数文件修改通过 edit/write 完成）。

### 全局风险

无。方案是纯 plugin 侧改动，不触及 ellamaka。

## Risks

### 已识别风险

| # | 风险 | 严重度 | 缓解策略 |
|---|------|--------|----------|
| **R1** | 同一文件多次操作的去重策略未定义 | 🔴 高 | **策略：取最后一次操作**。遍历 messages 时按时间顺序处理，Map 中同路径直接覆盖。理由：最后一次操作最接近子会话结束时的状态。统计显示最后一次的 `additions`/`deletions`，不累加（累加会夸大实际变更） |
| **R2** | write 工具无 diff 统计 | 🟡 中 | **策略：显示 `(+?/-?)` 占位符**。write 的 metadata 仅有 `filepath` + `exists`，无统计。当 `exists=true` 显示 `(modified)`，`exists=false` 显示 `(added)`，不显示具体行数。用户理解这是 write 操作的特性 |
| **R3** | plugin 能否访问子会话 messages 未验证 | 🔴 高 | **阻断项**。wopal-task-diff 在父会话的 plugin 上下文中运行，需确认 SDK 能否通过 `sessionID` 访问子会话 messages。验证方法：在 plugin 代码中调用 `client.messages({ sessionID: childSessionID, directory })`，检查返回结果。如果 API 限制只能访问当前 session，回退方案：改为纯 git diff（记录 HEAD commit） |
| **R4** | metadata 反映"操作意图"而非"最终状态" | 🟡 中 | **已知限制，可接受**。子会话可能 edit fileA 后又 revert edit，metadata 会记录两次操作。显示差异是"子会话做过的文件操作"而非"git diff 最终状态"。对用户有参考价值（知道子会话触碰了哪些文件）。snapshot diff 作为补充会反映最终状态，合并时可选择 snapshot 版本（如果两者不一致） |
| **R5** | 上游 metadata 格式耦合 | 🟡 中 | **缓解：添加类型防御**。提取 metadata 时做字段存在性检查，缺失时降级处理（跳过该工具，不报错）。未来上游重构时，只需更新字段名映射，不影响整体架构 |
| **R6** | error 状态工具的 metadata | 🟢 低 | **已规避**。方案明确只处理 `status === "completed"` 的工具，`ToolStateError` 不纳入。代码中显式过滤 |

### 关键阻断项验证计划

**R3 验证**：实施前必须先验证 SDK 跨 session 访问能力。

验证步骤：
1. 在 `wopal-task-diff.ts` 添加临时调试代码
2. 调用 `client.messages({ sessionID: childSessionID, directory: task.directory })`
3. 检查返回结果是否包含子会话的 messages
4. 如成功 → 继续 hybrid 方案；如失败 → 回退到 git diff 方案

**R3 回退方案**：如果 SDK 无法跨 session 访问 messages，采用纯 git diff：

```bash
# Task 启动时
git rev-parse HEAD → task.startCommit

# Task 完成时
git diff <startCommit> HEAD
```

回退方案的代价：受 worktree 全局 scope 污染（Issue #11802），但比空结果更可用。

## In Scope

- 在 `wopal-task-diff.ts` 添加 tool metadata 提取逻辑
- 合并 tool metadata 与 snapshot diff
- 保持现有 snapshot diff API 调用作为补充数据源
- 移除 snapshot 诊断代码（不再需要诊断空结果原因）

## Out of Scope

- 修改 ellamaka 源码
- bash tool 的 `metadata.files` 添加（Issue #11802 的上游修复方向）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| tools | `wopal-plugin/src/tools/wopal-task-diff.ts` | 重写 | 混合 diff 逻辑 |

## Implementation

### Task 1: Rewrite wopal-task-diff.ts with hybrid approach

**Files**: `wopal-plugin/src/tools/wopal-task-diff.ts`

**Changes**:

整体重写为混合机制，分三步：

- [ ] Step 1: 提取 tool metadata
  - 调用 `session.messages` API 获取子会话所有 messages
  - 遍历 parts，过滤 `type === "tool" && state.status === "completed"`
  - 按 tool 名提取文件变更：
    - `edit` → `metadata.filediff`（`{file, patch, additions, deletions}`）
    - `write` → `metadata.filepath`（路径，无 diff 统计 → 标记 `status: exists ? "modified" : "added"`，统计设 0）
    - `apply_patch` → `metadata.files`（`[{relativePath, patch, additions, deletions, type}]`）
    - 其他 tool → 跳过
  - 路径标准化：所有绝对路径转为相对于 worktree 的相对路径

- [ ] Step 2: 获取 snapshot diff（保持现有逻辑）
  - 调用 `session.diff` API
  - 空结果是预期内的，不作为错误

- [ ] Step 3: 合并去重
  - 以 `Map<normalizedPath, FileChange>` 为合并容器
  - metadata 先入（session-scoped 权威）
  - snapshot diff 补充 metadata 未覆盖的文件
  - 同文件冲突 → 取 metadata 版本
  - 格式化输出（与当前格式一致）

**Verification**:

- [ ] Step 1: `bun run test:run` 确认无回归
- [ ] Step 2: `bun run lint` 确认无 lint 错误

### Task 2: Add unit tests for hybrid diff

**Files**: `wopal-plugin/src/tools/wopal-task-diff.test.ts`（新建或修改）

**Changes**:

- [ ] Step 1: 测试仅 tool metadata 有数据时，正确返回变更（snapshot 为空）
- [ ] Step 2: 测试 tool metadata + snapshot diff 合并去重
- [ ] Step 3: 测试同文件冲突时取 metadata 版本
- [ ] Step 4: 测试 write tool 的 filepath 路径提取
- [ ] Step 5: 测试 apply_patch 的 files 数组提取
- [ ] Step 6: 测试路径标准化（绝对路径 → 相对路径）

**Verification**:

- [ ] Step 1: `bun run test:run` 全部通过

## Delegation Strategy

N/A — 单文件改动，Wopal 直接实施。

## Test Plan

#### Unit Tests

##### Case U1: Tool metadata only (snapshot empty)
- Goal: 验证 snapshot 为空时，纯 metadata 能返回正确变更
- Fixture: mock messages 包含 edit/write tool parts with metadata，mock session.diff 返回空数组
- Execution: 调用 `wopal_task_diff({ task_id })`
- Expected: 返回 edit/write 对应的文件变更列表

##### Case U2: Hybrid merge with dedup
- Goal: 验证 metadata + snapshot 合并，同文件取 metadata
- Fixture: mock messages 含 edit(fileA)，mock snapshot diff 含 fileA(不同统计) + fileB(bash)
- Execution: 调用 `wopal_task_diff({ task_id })`
- Expected: fileA 用 metadata 版本，fileB 补充纳入

##### Case U3: Path normalization
- Goal: 验证绝对路径正确转为相对路径
- Fixture: mock edit metadata.file = `/abs/path/to/file.ts`，worktree = `/abs/path/to`
- Expected: 输出中 file = `file.ts`

#### Regression Tests

##### Case R1: Existing tests still pass
- Goal: 确认修改不影响现有功能
- Execution: `bun run test:run`
- Expected: 所有现有测试 pass

## Acceptance Criteria

### Agent Verification

- [ ] wopal-plugin `bun run test:run` 全部通过
- [ ] wopal-plugin `bun run lint` 通过
- [ ] 新增 hybrid diff 测试全部通过

### User Validation

#### Scenario 1: wopal_task_diff returns file changes reliably with any provider
- Goal: 子会话完成后 wopal_task_diff 能稳定返回文件变更，不受 provider 影响
- Precondition: 启动一个 wopal_task 子任务（使用 GLM 或其他模型），任务中执行文件修改
- User Actions:
  1. 等待子任务完成
  2. 调用 `wopal_task_diff(task_id)` 查看文件变更
  3. 多次调用确认结果一致
- Expected Result: 每次调用都能返回正确的文件变更列表，不再出现空结果

- [ ] 用户已完成上述功能验证并确认结果符合预期