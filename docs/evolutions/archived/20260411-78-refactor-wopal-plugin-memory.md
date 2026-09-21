# 78-refactor-wopal-plugin-memory

## Metadata

- **Issue**: #78
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-11
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 distill/confirm/cancel 子命令从 context_manage 迁移到 memory_manage，修正 memory_manage 参数描述歧义，使记忆相关操作统一入口。

## Technical Context

当前 distill 功能散落在 context_manage 工具中（distill/confirm/cancel 三个 action），但语义上属于记忆管理而非上下文管理。context_manage 应只保留 summary 和 status 两个子命令。

memory_manage 的 `query` 参数在不同子命令下语义不同：search 时是搜索内容，delete/update 时是 ID 前缀。当前描述 "search 的查询内容 / delete 和 update 的 ID 前缀" 含糊，且 Issue 提到 "update 需要提供 id（记忆 ID 前缀）" 但实际参数名是 `query`，导致认知负担。

### 当前架构

```
context_manage (5 actions): summary, status, distill, confirm, cancel
memory_manage (7 commands): list, stats, search, delete, add, update, injected

工具注册 (index.ts):
  tools = createWopalTools(...)        → wopal_task_*, memory_manage
  tools.context_manage = create...()   → context_manage (条件注册)
```

### 迁移后架构

```
context_manage (2 actions): summary, status
memory_manage (10 commands): list, stats, search, delete, add, update, injected, distill, confirm, cancel
```

### 数据流

distill 功能需要：
- `DistillEngine` 实例（preview + confirmCandidates）
- `client.session.messages()` API（获取消息）
- `client.session.update()` API（更新 title）
- `distill-formatters.ts`（格式化输出）
- `memory/distill.ts` 的状态管理函数（getPendingConfirmation 等）

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| context-manage tool | `src/tools/context-manage.ts` | 移除 distill/confirm/cancel handler，保留 summary/status |
| context-manage test | `src/tools/context-manage.test.ts` | 移除 distill 相关测试 |
| memory-manage tool | `src/tools/memory-manage.ts` | 新增 distill/confirm/cancel 子命令，修正 query 参数描述 |
| distill-formatters | `src/tools/distill-formatters.ts` | 更新 Next Steps 中的工具名引用 |
| tool index | `src/tools/index.ts` | createMemoryManageTool 签名变更（需 distillEngine, client, distillLLM） |
| plugin index | `src/index.ts` | context_manage 注册简化，memory_manage 注册增强 |
| distill command | `agents/wopal/commands/distill.md` | context_manage → memory_manage |

## In Scope

- [ ] memory_manage 新增 distill/confirm/cancel 子命令
- [ ] context_manage 移除 distill/confirm/cancel 子命令
- [ ] memory_manage query 参数描述修正（不同子命令语义清晰区分）
- [ ] 工具注册更新（index.ts, src/index.ts）
- [ ] distill-formatters.ts Next Steps 引用更新
- [ ] distill.md 命令文件引用更新
- [ ] 测试迁移和更新

## Out of Scope

- 记忆存储后端改造（LanceDB schema 不变）
- distill 核心逻辑改动（DistillEngine 不变）
- 新增子命令（只在已有命令集内重组）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/tools/memory-manage.ts` | 修改 | 新增 distill/confirm/cancel handler，修正参数描述 |
| `src/tools/context-manage.ts` | 修改 | 移除 distill/confirm/cancel，精简为 summary/status |
| `src/tools/distill-formatters.ts` | 修改 | Next Steps 中 context_manage → memory_manage |
| `src/tools/context-manage.test.ts` | 修改 | 移除 distill 相关测试 |
| `src/tools/index.ts` | 修改 | createMemoryManageTool 签名变更 |
| `src/index.ts` | 修改 | 工具注册逻辑调整 |
| `agents/wopal/commands/distill.md` | 修改 | context_manage → memory_manage |
| `memory/index.ts` | 不变 | 无需修改 |

## Implementation

### Task 1: memory_manage 新增 distill/confirm/cancel

**Files**: `src/tools/memory-manage.ts`

**Changes**:
1. 新增导入：DistillEngine, DistillLLMClient, SessionMessage, 相关 distill 状态函数, formatPreviewReport, formatConfirmReportWithDedup, session-context
2. createMemoryManageTool 签名扩展：新增 `distillEngine?: DistillEngine`, `distillLLM?: DistillLLMClient`, `client?: any`
3. command enum 新增 `"distill"`, `"confirm"`, `"cancel"`
4. 新增 args: `force`, `selectedIndices`（复用已有定义）
5. 修正 query 参数描述：
   - search: "搜索查询关键词"
   - delete/update: "记忆 ID 前缀"
6. 新增 handleDistill, handleConfirm, handleCancel handler（从 context-manage.ts 迁移，逻辑不变）
7. 新增 confirmingSessions Set 和 ECHO_REMINDER_DISTILL
8. switch 中添加三个新分支

**Verification**: `bun run test:run`

### Task 2: context_manage 精简

**Files**: `src/tools/context-manage.ts`

**Changes**:
1. 移除所有 distill 相关导入（DistillEngine, distill 状态函数, distill-formatters）
2. 移除 confirmingSessions, ECHO_REMINDER
3. ContextManageAction 缩减为 `"summary" | "status"`
4. 移除 handleDistill, handleConfirm, handleCancel 函数
5. 移除 force, selectedIndices 参数
6. 精简 description：移除 distill 相关描述
7. 精简 args：只保留 action（enum 缩减）和隐含的 sessionID
8. handleStatus 中保留 distill state 展示（只读展示，不需要 distill engine）

**Verification**: `bun run test:run`

### Task 3: 工具注册更新

**Files**: `src/tools/index.ts`, `src/index.ts`

**Changes**:

`src/tools/index.ts`:
- createMemoryManageTool 签名扩展：新增 `distillEngine?`, `distillLLM?`, `client?`
- 将这些参数传递给 createMemoryManageTool

`src/index.ts`:
- createWopalTools 传递 memory 的 distillEngine, llm, client
- context_manage 注册时不再传 distillEngine（只传 distillLLM 和 client）

**Verification**: `bun run test:run && bun run build`

### Task 4: 引用更新

**Files**: `src/tools/distill-formatters.ts`, `agents/wopal/commands/distill.md`

**Changes**:

`distill-formatters.ts`:
- formatPreviewReport 中 Next Steps: `context_manage action=confirm` → `memory_manage command=confirm`

`distill.md`:
- 所有 `context_manage(` → `memory_manage(`
- 参数格式调整：`context_manage({"action": "distill"})` → `memory_manage({"command": "distill"})`

**Verification**: grep 确认无残留引用

### Task 5: 测试更新

**Files**: `src/tools/context-manage.test.ts`

**Changes**:
1. 移除 "prevents duplicate concurrent confirm" 测试（该功能迁移到 memory-manage）
2. 保留 summary 相关测试不变
3. 如 memory-manage 没有测试文件，新建 `memory-manage.test.ts` 并迁移 distill 测试

**Verification**: `bun run test:run`

## Delegation Strategy

N/A — 任务之间有强依赖（Task 1 必须先于 Task 2），且涉及同一文件的连续修改，由 Wopal 直接执行。

## Test Plan

### Test Case Design

- memory_manage distill: 单元测试验证 preview → confirm → cancel 流程
- memory_manage query 参数: 验证 search/delete/update 参数描述清晰无歧义
- context_manage: 验证只剩 summary/status 两个 action，distill/confirm/cancel 报错
- 注册正确性: 验证工具注册后 context_manage 和 memory_manage 都能正常调用

### Regression Testing

- 现有 summary 测试不回归
- 现有 memory_manage CRUD 测试不回归
- 全量测试 `bun run test:run` 通过

### Adjustment Strategy

- 若 createMemoryManageTool 签名变更导致编译错误，检查所有调用点
- 若测试文件引用路径问题，按实际目录结构调整

## Acceptance Criteria

### Agent Verification

- [x] `bun run test:run` 全部通过
- [x] `bun run build` 编译成功
- [x] context_manage 只响应 summary 和 status action
- [x] memory_manage 响应 distill/confirm/cancel command
- [x] memory_manage query 参数描述明确区分 search 和 delete/update 用途
- [x] distill-formatters.ts 和 distill.md 中无 context_manage 残留引用

### User Validation

- 重启 OpenCode 后 `/distill` 命令正常触发记忆蒸馏
- `memory_manage command=list` 正常返回记忆列表
- `context_manage action=status` 正常展示会话状态（含 distill 状态）
