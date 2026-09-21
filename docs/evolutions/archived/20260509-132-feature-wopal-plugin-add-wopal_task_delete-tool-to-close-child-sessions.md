# 132-feature-wopal-plugin-add-wopal_task_delete-tool-to-close-child-sessions

## Metadata

- **Issue**: #132
- **Type**: feature
- **Target Project**: ontology
- **Created**: 2026-04-25
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

新增 `wopal_task_delete` 工具，允许用户在确认任务验证完成后手动删除子会话，释放孤儿资源。

## Technical Context

当前 `wopal_task` 创建的子会话在插件内存清理（`cleanup()` / `shutdownManager()`）时只移除 Map 记录，不调用 OpenCode `session.delete` API，子会话成为孤儿资源。

**API 可用性验证**：
- OpenCode v1 SDK (`OpencodeClient`) 已提供 `session.delete` API
- 方法签名：`client.session.delete({ path: { id: string } })` — 与 `session.abort` 参数格式一致
- 返回类型：`{ data: boolean }` 表示删除成功，或 `{ error: ... }` 表示失败
- Plugin v1 client (`pluginInput.client`) 即 `OpencodeClient` 实例，无需额外依赖

**全局风险**：无。新增独立工具，不修改现有工具行为。

## In Scope

- 新增 `wopal_task_delete` 工具（`.wopal/wopal-plugin/src/tools/wopal-task-delete.ts`）
- `SimpleTaskManager` 添加 `closeTask(taskId, parentSessionID)` 方法
- `TaskLifecycleDeps` 扩展 `session.delete` 类型
- 工具注册到 `.wopal/wopal-plugin/src/tools/index.ts`
- 工具描述中明确删除时机指引

## Out of Scope

- 批量删除功能（防误操作，Issue 明确排除）
- `cleanup()` / `shutdownManager()` 中自动调用 `session.delete`（生命周期不同步，需另行考虑）
- 修改现有 `wopal_task_reply` 等工具行为
- 自动 abort running 任务后删除（用户应显式验证后再删除）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 工具定义 | `.wopal/wopal-plugin/src/tools/wopal-task-delete.ts` | 创建 | 新工具实现 |
| 工具注册 | `.wopal/wopal-plugin/src/tools/index.ts` | 修改 | 注册新工具 |
| 任务管理器 | `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts` | 修改 | 添加 `closeTask` 方法 |
| 生命周期类型 | `.wopal/wopal-plugin/src/tasks/task-lifecycle.ts` | 修改 | 扩展 `TaskLifecycleDeps` 类型 |
| 插件文档 | `.wopal/wopal-plugin/AGENTS.md` | 修改 | 更新工具清单 |

## Implementation

### Task 1: 扩展 TaskLifecycleDeps 类型

**Files**: `.wopal/wopal-plugin/src/tasks/task-lifecycle.ts`

**Changes**:

- [x] Step 1: 在 `TaskLifecycleDeps.client.session` 类型中添加 `delete` 方法签名：
  ```typescript
  delete?: (args: { path: { id: string } }) => Promise<{ data?: boolean; error?: unknown }>
  ```

**Verification**:

- [x] Step 1: 类型检查通过（`bun run build`）

### Task 2: 添加 `closeTask` 方法到 SimpleTaskManager

**Files**: `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts`

**Changes**:

- [x] Step 1: 添加 `closeTask` 方法签名：
  ```typescript
  async closeTask(taskId: string, parentSessionID: string): Promise<{ ok: boolean; message: string }>
  ```
- [x] Step 2: 实现 `getTaskForParent(taskId, parentSessionID)` 校验所有权，失败返回 `{ ok: false, message: "Task not found or not owned by this session" }`
- [x] Step 3: 检查 task.status === 'running'，若是则返回警告 `{ ok: false, message: "Task is still running. Please verify completion before deleting (use wopal_task_output to check status)." }`
- [x] Step 4: 调用 `client.session.delete({ path: { id: task.sessionID } })` 删除子会话
- [x] Step 5: 检查返回结果：若有 `error` 则返回 `{ ok: false, message: "Failed to delete session: ..." }`
- [x] Step 6: 从 `tasks` Map 移除记录
- [x] Step 7: 从 `sessionToTask` Map 移除映射
- [x] Step 8: 调用 `releaseConcurrencySlot(task)`（若 task 有 concurrencyKey）
- [x] Step 9: 返回 `{ ok: true, message: "Task deleted successfully. Session removed from OpenCode." }`

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 现有测试通过

### Task 3: 实现 `wopal_task_delete` 工具

**Files**: `.wopal/wopal-plugin/src/tools/wopal-task-delete.ts`

**Changes**:

- [x] Step 1: 创建工具文件，遵循现有工具结构（如 `wopal-task.ts`）
- [x] Step 2: 工具参数：`task_id: string`（必填）
- [x] Step 3: 工具描述：
  ```
  Delete a completed task and its child session from OpenCode. ⚠️ Only use after verifying task completion via wopal_task_output. Running tasks cannot be deleted — use wopal_task_reply(interrupt=true) to stop first if needed.
  ```
- [x] Step 4: 检查 `context.sessionID`，无则返回错误
- [x] Step 5: 调用 `manager.closeTask(task_id, context.sessionID)`
- [x] Step 6: 返回结果消息

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: 代码风格符合项目规范（无 console.log、使用 debugLog、ESM import）

### Task 4: 注册工具并更新文档

**Files**: `.wopal/wopal-plugin/src/tools/index.ts`, `.wopal/wopal-plugin/AGENTS.md`

**Changes**:

- [x] Step 1: 在 `index.ts` 中 import `createWopalTaskDeleteTool` 并注册：
  ```typescript
  import { createWopalTaskDeleteTool } from "./wopal-task-delete.js"
  // ...
  tools.wopal_task_delete = createWopalTaskDeleteTool(manager)
  ```
- [x] Step 2: 更新 `.wopal/wopal-plugin/AGENTS.md` 工具清单表格，新增：
  ```
  | wopal_task_delete | 删除已完成的任务及其子会话 | task_id |
  ```

**Verification**:

- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过

## Delegation Strategy

N/A — 单一任务，Complexity = Low，无需并行委派。

## Test Plan

#### Unit Tests

N/A — 核心逻辑是 API 调用 + Map 操作，无复杂算法需单独测试。依赖集成环境验证。

#### Integration Tests

##### Case I1: 正常删除 idle 状态的 task
- Goal: 验证工具能成功删除 idle/waiting/error 状态的 task 及其子会话
- Fixture: OpenCode 运行环境，已通过 `wopal_task` 创建并等待其 idle 的 task
- Execution:
  - [x] Step 1: 用 `wopal_task` 创建一个简单任务（如 `echo hello`），等待其完成到 idle
  - [x] Step 2: 调用 `wopal_task_delete(task_id="<id>")`
  - [x] Step 3: 验证返回成功消息
  - [x] Step 4: 调用 `wopal_task_output(task_id="<id>")` 认返回 "Task not found"
- Expected Evidence: delete 返回成功，后续 output 返回 not found

##### Case I2: 删除不存在的 task
- Goal: 验证工具对不存在的 task_id 返回明确错误
- Fixture: 无需特殊前置条件
- Execution:
  - [x] Step 1: 调用 `wopal_task_delete(task_id="nonexistent-id")`
  - [x] Step 2: 验证返回包含 "not found" 的错误信息
- Expected Evidence: 返回错误信息，不抛异常

##### Case I3: 删除属于其他会话的 task
- Goal: 验证权限校验，不能删除非本会话的 task
- Fixture: 两个不同会话各有一个 task
- Execution:
  - [x] Step 1: 会话 A 创建 task，获取 task_id
  - [x] Step 2: 在会话 B 中调用 `wopal_task_delete(task_id="<A的task>")`
  - [x] Step 3: 验证返回权限错误
- Expected Evidence: 返回 "not found or not owned by this session"

##### Case I4: 删除 running 状态的 task
- Goal: 验证工具拒绝删除 running 任务并返回警告
- Fixture: 一个正在运行的长时间任务（如复杂代码生成）
- Execution:
  - [x] Step 1: 创建任务后立即调用 `wopal_task_delete(task_id="<id>")`
  - [x] Step 2: 验证返回警告消息，建议先验证完成状态
- Expected Evidence: 返回 "Task is still running. Please verify completion before deleting"

#### E2E Tests

N/A — 无用户界面，集成测试已覆盖。

#### Regression Tests

##### Case R1: 现有工具不受影响
- Goal: 确认新增工具不影响 `wopal_task`、`wopal_task_output`、`wopal_task_reply` 的正常功能
- Fixture: 现有工具功能
- Execution:
  - [x] Step 1: 运行 `bun run test:run`，确认所有现有测试通过
  - [x] Step 2: 通过 `wopal_task` 创建任务 → `wopal_task_output` 查询 → `wopal_task_reply` 回复，流程正常
- Expected Evidence: 所有测试通过，工具链路无异常

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 全部通过
- [x] 新文件 `wopal-task-delete.ts` 符合项目代码规范（debugLog、ESM import、无 console.log）
- [x] 工具描述包含删除时机指引（验证后才能删除，running 任务警告）

### User Validation

#### Scenario 1: 删除已验证完成的 task
- Goal: 确认用户能通过工具删除已完成验证的 task 子会话
- Precondition: 已通过 `wopal_task` 创建任务并等待 idle，验证完成
- User Actions:
  1. 调用 `wopal_task_delete(task_id="xxx")`
  2. 观察返回信息
- Expected Result: 返回成功删除消息，后续查询该 task 返回 not found

#### Scenario 2: running 状态的 task 提示警告
- Goal: 确认工具对 running 状态的 task 给出明确警告
- Precondition: 有一个正在运行的 task
- User Actions:
  1. 调用 `wopal_task_delete(task_id="xxx")`
  2. 观察返回信息
- Expected Result: 返回警告提示，告知用户任务仍在执行中，建议先验证完成状态

- [x] 用户已完成上述功能验证并确认结果符合预期