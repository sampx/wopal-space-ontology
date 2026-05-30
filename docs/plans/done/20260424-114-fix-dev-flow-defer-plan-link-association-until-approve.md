# 114-fix-dev-flow-defer-plan-link-association-until-approve

## Metadata

- **Issue**: #114
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-23
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

修复 Plan 链接关联时机：创建时不写入，approve --confirm 后才写入。

## Technical Context

当前 `plan.py` 在创建 Plan 后立即调用 `_update_issue_plan_link` 写入 Issue，导致用户误以为 Plan 已就绪。

`approve.py` 的 `--confirm` 分支已有 `sync_plan_to_issue_body` 会整体覆盖 Issue body 并包含 Plan link，因此只需移除创建时的写入调用。

## In Scope

- 从 `plan.py` 移除 `_update_issue_plan_link` 调用及函数定义
- 移除 `_build_repo_blob_url` helper（仅被 `_update_issue_plan_link` 使用）

## Out Of Scope

- 其他命令修改
- sync/approve 流程调整

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| commands | `plan.py` | 修改 | 移除创建时的 Plan link 写入 |

## Implementation

### Task 1: 移除 plan.py 中创建时写入 Plan link 的逻辑

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/commands/plan.py`

**Changes**:

- [x] Step 1: 删除 `_update_issue_plan_link` 函数定义（L180-230）
- [x] Step 2: 删除 `_build_repo_blob_url` helper（L159-177）
- [x] Step 3: 移除 `cmd_plan` 中对 `_update_issue_plan_link` 的调用（L624）及相关 log（L625）

**Verification**:

- [x] Step 1: 运行 `flow.py plan <issue>` 创建新 Plan，Issue body 不包含 Plan link（Issue #131 验证）
- [x] Step 2: 运行 `flow.py approve <issue> --confirm`，Issue body 包含 Plan link（Issue #114 已验证）

## Delegation Strategy

N/A — 单一任务，无需并行委派

## Test Plan

#### Unit Tests

N/A — 无复杂逻辑变更，通过集成测试覆盖

#### Integration Tests

##### Case I1: Plan 创建后 Issue 无 Plan link
- Goal: 验证创建时不写入 Plan link
- Fixture: 新建 Issue #TEST（或使用现有 open issue）
- Execution:
  - [x] Step 1: 执行 `flow.py plan <issue>`（Issue #131）
  - [x] Step 2: 用 `gh issue view <issue>` 检查 body，确认无 Related Resources 表或无 Plan 行
- Expected Evidence: Issue body 缺少 Plan link

##### Case I2: Approve --confirm 后 Issue 有 Plan link
- Goal: 验证 approve 后写入 Plan link
- Fixture: 上一步创建的 Plan（状态 planning）
- Execution:
  - [x] Step 1: 填写 Plan 最小内容后执行 `flow.py approve <issue> --confirm`（Issue #114 已执行）
  - [x] Step 2: 用 `gh issue view <issue>` 检查 body，确认 Related Resources 表含 Plan 行
- Expected Evidence: Issue body 包含 `[plan-name](plan-url)`

#### E2E Tests

N/A — 集成测试已覆盖用户感知场景

#### Regression Tests

##### Case R1: 现有 Plan 不受影响
- Goal: 确认已有 Plan 的 Issue 不被错误修改
- Fixture: 任一已归档的 Issue（如 #110）
- Execution:
  - [x] Step 1: 检查 Issue body 仍包含 Plan link
  - [x] Step 2: 检查 Plan 文件未被修改
- Expected Evidence: Issue 和 Plan 状态无变化

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] `flow.py plan <issue>` 创建后 Issue 无 Plan link（Issue #131 验证）
- [x] `flow.py approve <issue> --confirm` 后 Issue 有 Plan link（Issue #114 已验证）
- [x] 现有归档 Issue 不受影响（Issue #110 验证）

### User Validation

#### Scenario 1: 创建 Plan 后 Issue 无 Plan link
- Goal: 确认创建时不误导用户"Plan 已就绪"
- Precondition: 有一个 open Issue
- User Actions:
  1. Agent 执行 `flow.sh plan <issue>`
  2. 用户查看 Issue body
- Expected Result: Issue 中不包含 Plan link，只有 Issue 原有内容

#### Scenario 2: Approve 后 Issue 有 Plan link
- Goal: 确认审批后才写入 Plan link
- Precondition: Plan 已创建并填写，用户确认审批
- User Actions:
  1. Agent 执行 `flow.sh approve <issue> --confirm`
  2. 用户查看 Issue body
- Expected Result: Issue Related Resources 表包含 Plan link

- [x] 用户已完成上述功能验证并确认结果符合预期
