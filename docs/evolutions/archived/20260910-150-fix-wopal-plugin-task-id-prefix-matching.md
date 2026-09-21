# 150-fix-wopal-plugin-task-id-prefix-matching

## Metadata

- **Issue**: #150
- **Type**: fix
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-09-10
- **Status**: done
- **Verification Commit**: f56778b43205ee26b33282653d6eae7e525a7dac
- **Worktree**:
  - branch: wopal-space-ontology-150-fix-wopal-plugin-task-id-prefix-matching
  - path: (removed)
- **Verification Dir**: /Volumes/U500G/coding/wopal-workspace/.wopal
- **Base Commit**: dc0be66efc365a1c527240d55d6866b588d7e635
- **Final Commit**: 473d6e44125adad94e987765e48e2f650d4fe6ed

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

为 `SimpleTaskManager` 及 `wopal_task_*` 系列工具引入基于“唯一性约束 + 歧义硬拦截”的灵活任务 ID 解析机制，支持全名、前缀、后缀及无前缀纯哈希匹配，彻底解决因上下文压缩（Compaction）摘要截断或日志后缀截断导致的任务 not found 误判及失联问题。

## Technical Context

### Architecture Context

在主会话触发上下文压缩（Compaction）后，大模型生成的记忆摘要往往将 `wopal-task-1bcbb6eacffeD6Mr5eedcZH1hZ` 这样的超长 ID 截短为前缀（如 `wopal-task-1bcbb6eacffe`）；而在运行时调试日志（`formatSessionID`）中，系统通常打印的是后 10 位后缀（如 `D6Mr5eedcZH1hZ(task)`）。
目前 `SimpleTaskManager.getTaskForParent` 仅在内存 Map 中执行 `this.tasks.get(id)` 精确查找，截断的 ID 会直接导致 `Task not found` 报错。此时 Agent 会误判子任务已崩溃或丢失，引发重复拉起任务导致代码冲突踩踏，或因无法叫停/回复而导致任务失控、并发槽位泄漏。同时在 `finishTask` 中存在以传入 query 字符串而非真实 `task.id` 进行 `tasks.delete` 的潜在清理残留问题。

### Key Decisions

- **D-01（纯函数解耦）**：将任务查找与多模式匹配逻辑抽离为独立的纯函数模块 `src/tasks/task-resolver.ts`，接受任务集合与查询字符串，返回结构化判决结果（`exact`、`unique`、`ambiguous`、`not_found`）。
- **D-02（匹配策略与唯一性裁决）**：
  1. 精确匹配优先（`exact`）；
  2. 多模式模糊匹配（前缀 `startsWith`、后缀 `endsWith`、去除 `wopal-task-`/`ses_` 的主体匹配）；
  3. **铁律：仅当匹配结果严格等于 1 个时判定为 `unique` 并放行；当结果 ≥2 个时一律判定为 `ambiguous` 拒绝猜测，并返回冲突清单**。
  4. 最小查询长度限制：查询字符少于 3 个字符时不进行模糊匹配，避免误撞。
- **D-03（向后兼容与精准删除）**：
  `SimpleTaskManager.getTaskForParent` 保持签名不变，内部委托 `resolveTaskForParent`；`finishTask` 必须基于解析得到的 `task.id` 执行 `tasks.delete(task.id)`，杜绝内存泄漏。
- **D-04（诊断友好性回显）**：各 `wopal_task_*` 工具遇到 `ambiguous` 时明确提示冲突选项，遇到 `not_found` 且当前会话有任务时输出活跃候选清单，遇到 `unique` 命中时在输出头部标注实际完整 ID。

### Key Interfaces

```typescript
export type TaskResolveResult<T extends { id: string }> =
  | { type: "exact"; task: T }
  | { type: "unique"; task: T; matchedBy: "prefix" | "suffix" | "normalized" }
  | { type: "ambiguous"; query: string; candidates: T[] }
  | { type: "not_found"; query: string; availableTasks: T[] }
```

## In Scope

- 新建 `src/tasks/task-resolver.ts` 纯函数模块及完整单元测试。
- 修改 `src/tasks/simple-task-manager.ts`：
  - 新增 `resolveTaskForParent` 方法；
  - 升级 `getTaskForParent` 方法；
  - 修复 `finishTask` 中删除 key 的缺陷。
- 升级 `src/tools/wopal-task-output.ts`、`wopal-task-reply.ts`、`wopal-task-abort.ts` 的解析调用与错误提示回显（`wopal_task_finish` 工具透传 `finishTask` 返回消息，工具文件本身无需改动）。
- 适配 `wopal-task-abort.test.ts`、`wopal-task-reply.test.ts`、`wopal-task-finish.test.ts`、`wopal-task-output.test.ts` 中 `getTaskForParent` 相关测试与 mock。
- 补充各层级单元测试，覆盖精确匹配、前缀匹配、后缀匹配、歧义拦截、跨 session 隔离与删除安全性。

## Out of Scope

- 不修改 OpenCode/Ellamaka 核心引擎中的 Compaction 算法或 Prompt 模板（保持消费端容错与韧性）。
- 不改变底层 `WopalTask` 数据结构。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| `tasks` | `.wopal/plugins/wopal-plugin/src/tasks/task-resolver.ts` | 创建 | 任务 ID 确定性多模式匹配与歧义仲裁核心算法 |
| `tasks` | `.wopal/plugins/wopal-plugin/src/tasks/task-resolver.test.ts` | 创建 | 解析器纯函数的完备单元测试 |
| `tasks` | `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts` | 修改 | 集成解析器、升级查找接口与修复删除缺陷 |
| `tasks` | `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.test.ts` | 修改 | Manager 层面集成测试与回退场景验证 |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.ts` | 修改 | 增强输出与错误回显 |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts` | 修改 | 增强歧义与未找到错误回显 |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-abort.ts` | 修改 | 增强歧义与未找到错误回显 |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.test.ts` | 修改 | 工具层前缀/后缀匹配测试 |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-abort.test.ts` | 修改 | 适配 `getTaskForParent` 解析结果 mock |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.test.ts` | 修改 | 适配 `getTaskForParent` 解析结果 mock |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-finish.test.ts` | 修改 | 适配 `finishTask` → `getTaskForParent` 解析结果 mock |
| `tools` | `.wopal/plugins/wopal-plugin/src/tools/pending-boundary.test.ts` | 修改 | 适配 abort/reply/finish 工具 mock（精确匹配行为不变） |

## Acceptance Criteria

### Agent Verification

1. [x] `cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run test:run src/tasks/task-resolver.test.ts` 全部通过（覆盖精确、前缀、后缀、纯哈希、歧义、空结果）。
2. [x] `cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run test:run src/tasks/simple-task-manager.test.ts` 全部通过（覆盖多 Session 隔离与前缀下 `finishTask` 安全清理）。
3. [x] `cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run test:run` 全套测试 100% 绿灯。
4. [x] `cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run typecheck` 零类型错误。

### User Validation

#### Scenario 1: 通过截断的前缀或日志后缀查询/控制后台任务
- Goal: 验证即使只提供前缀或后缀，工具也能正确定位任务；有多个任务冲突时明确提示歧义，不发生误操作。
- Precondition: 当前会话中启动了一个后台子任务（如 `wopal-task-1bcbb6eacffeD6Mr5eedcZH1hZ`）。
- User Actions:
  1. 调用 `wopal_task_output(task_id: "wopal-task-1bcbb6eacffe")` 传入前缀；
  2. 调用 `wopal_task_output(task_id: "D6Mr5eedcZH1hZ")` 传入日志后缀；
  3. 观察命令回显。
- Expected Result: 两次查询均成功返回该子任务详情，并在输出中注明匹配来源；输入短歧义字符串时返回冲突列表提示。

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 实现 task-resolver 纯函数解析模块与单元测试

**Verification Intent**: AC#1

**Behavior**:
在给定任务集合与查询字符串时：
- 精确匹配时返回 `{ type: "exact", task }`；
- 唯一前缀、唯一后缀或唯一无前缀主体匹配时返回 `{ type: "unique", task, matchedBy }`；
- 多个候选命中时返回 `{ type: "ambiguous", query, candidates }`；
- 零命中时返回 `{ type: "not_found", query, availableTasks }`；
- 查询过短（<3 字符）时拒绝模糊匹配。

**Files**:
- `.wopal/plugins/wopal-plugin/src/tasks/task-resolver.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-resolver.test.ts`

**Pre-read**:
- `.wopal/plugins/wopal-plugin/src/session-ref.ts`
- `.wopal/plugins/wopal-plugin/src/tools/dump-format-utils.ts`

**Design**:
独立纯函数 `resolveTask<T extends { id: string; sessionID?: string }>(tasks: Iterable<T>, query: string): TaskResolveResult<T>`。提供 `formatAmbiguousErrorMessage` 和 `formatNotFoundErrorMessage` 辅助格式化函数。

**TDD**: true

**Changes**:
1. 编写 `src/tasks/task-resolver.test.ts` 测试各种边界（红）。
2. 实现 `src/tasks/task-resolver.ts` 匹配算法（绿）。
3. 导出相关类型与格式化工具。

**Verify**:
`cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run test:run src/tasks/task-resolver.test.ts`

**Done**:
任务产出：完成解耦的任务 ID 解析器核心算法与测试
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: 升级 SimpleTaskManager 支持多模式解析并修复清理缺陷

**Verification Intent**: AC#2

**Behavior**:
- `SimpleTaskManager.resolveTaskForParent` 仅在当前 `parentSessionID` 的所属任务中解析；
- `SimpleTaskManager.getTaskForParent` 在唯一模糊匹配时也能返回目标任务；
- `finishTask` 传入前缀 ID 时，不仅能正常结束会话，还能准确通过 `tasks.delete(task.id)` 从内部 Map 中清除任务，释放槽位。

**Files**:
- `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.test.ts`

**Pre-read**:
- `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`

**Design**:
在 `SimpleTaskManager` 中引入 `resolveTaskForParent`，更新 `getTaskForParent` 和 `finishTask`。

**TDD**: true

**Changes**:
1. 在 `simple-task-manager.test.ts` 增加前缀查询、后缀查询、歧义阻断、多 session 隔离和 `finishTask` 前缀清理测试用例（红）。
2. 在 `simple-task-manager.ts` 引入并调用 `resolveTask`，将 `tasks.delete(taskId)` 改为 `tasks.delete(task.id)`（绿）。

**Verify**:
`cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run test:run src/tasks/simple-task-manager.test.ts`

**Done**:
任务产出：SimpleTaskManager 完成解析器集成与清理修复
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: 升级 wopal_task_* 工具交互提示并运行完整回归验证

**Verification Intent**: AC#3, AC#4

**Behavior**:
`wopal_task_output`、`wopal_task_reply`、`wopal_task_abort` 遇到前缀/后缀能正常执行，遇到歧义时给出候选清单，遇到 not_found 时给出可用任务列表。相关测试文件 mock 适配后，全套测试与类型检查全部通过。

**Files**:
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-abort.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.test.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-abort.test.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.test.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-finish.test.ts`
- `.wopal/plugins/wopal-plugin/src/tools/pending-boundary.test.ts`

**Pre-read**:
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-lifecycle.ts`

**Design**:
工具层使用 `manager.resolveTaskForParent` 获得详细判决结果，提升对 Agent 和用户的可解释性。`wopal_task_reply` 的 `interrupt=true` 路径在工具层完成解析后继续使用已解析的规范 `task.id` 操作（与现状一致，`task-lifecycle.ts` 的 `interruptTask` 无需改动）。`wopal_task_finish` 工具仅透传 `finishTask` 返回消息，无需改动文件，但其测试 mock 需适配解析结果。

**TDD**: true

**Changes**:
1. 更新各工具针对 `ambiguous` 与 `not_found` 的报错结构。
2. 更新工具单元测试（含 `wopal-task-abort.test.ts`、`wopal-task-reply.test.ts`、`wopal-task-finish.test.ts` 中 `getTaskForParent`/`finishTask` mock 适配）。
3. 执行 `bun run typecheck` 与 `bun run test:run` 进行全面回归验证。

**Verify**:
`cd /Volumes/U500G/coding/wopal-workspace/.wopal/plugins/wopal-plugin && bun run test:run && bun run typecheck`

**Done**:
任务产出：工具层完成提示增强，全套测试绿灯
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 纯算法模块实现，零外部副作用 |
| 2 | Task 2 | fae | Task 1 | 核心管理器接入与缺陷修复 |
| 3 | Task 3 | fae | Task 2 | 工具层回显升级与全量测试回归 |
