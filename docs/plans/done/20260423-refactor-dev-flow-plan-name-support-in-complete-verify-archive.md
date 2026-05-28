# refactor-dev-flow-plan-name-support-in-complete-verify-archive

## Metadata

- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-23
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

修复 dev-flow Python 重构后 `complete`、`verify`、`archive` 三个命令不支持 plan-name 参数的 bug，统一所有工作流命令的输入为 Issue number 或 Plan name 双模式。

## Technical Context

dev-flow 从 Bash 重构为 Python 后，`approve`、`sync`、`reset` 三个命令正确使用了字符串参数 + `find_plan()` 智能查找（数字 → Issue 查找，字符串 → Plan 名查找）。但 `complete`、`verify`、`archive` 三个命令的 argparse 参数定义为 `type=int`，强制要求整数输入，导致无 Issue 模式下无法使用 plan-name。

SKILL.md 明确规定无 Issue 模式下后续统一用 plan-name，因此这三个命令必须支持双模式输入。

**根因**：argparse 参数定义 `type=int` 阻止了字符串输入，且函数内部直接用 `find_plan_by_issue()` 而非通用的 `find_plan()`。

## In Scope

- `complete` 命令支持 plan-name 输入
- `verify` 命令支持 plan-name 输入
- `archive` 命令支持 plan-name 输入
- `plan --check` 命令支持 plan-name 输入（定位已有 Plan 进行校验）
- 四个命令的无 Issue 模式路径正确处理（跳过 Issue sync / close）
- 四个命令的输出提示使用正确的 ref（plan-name 而非 issue number）

## Out of Scope

- 不修改 `approve`、`sync`、`reset`（已正确支持双模式）
- 不修改 `issue create`、`decompose-prd`、`query`（不涉及此问题）
- 不修改 `plan` 创建模式（创建新 Plan 时仍需 `--title` 等参数，只是 `--check` 校验模式需支持 plan-name）
- 不重构公共代码（如 log 函数重复定义），那是另一个任务

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| commands | `scripts/dev_flow/commands/complete.py` | 修改 | argparse + find_plan + 无 Issue 路径 |
| commands | `scripts/dev_flow/commands/verify.py` | 修改 | argparse + find_plan + 无 Issue 路径 |
| commands | `scripts/dev_flow/commands/archive.py` | 修改 | argparse + find_plan + 无 Issue 路径 |
| commands | `scripts/dev_flow/commands/plan.py` | 修改 | `--check` 模式支持 plan-name 定位 |

## Implementation

### Task 1: complete 命令支持 plan-name

**Files**: `scripts/dev_flow/commands/complete.py`

**Changes**:

- [x] Step 1: argparse 参数从 `"issue", type=int` 改为 `"target", nargs="?"`（去掉 type=int）
- [x] Step 2: `cmd_complete` 函数入口：`issue_number = args.issue` → `input_ref = args.target`
- [x] Step 3: Plan 查找：`find_plan_by_issue(issue_number, ...)` → `find_plan(input_ref, str(workspace_root))`
- [x] Step 4: 导入：添加 `from dev_flow.domain.plan.find import find_plan`（替换 `find_plan_by_issue`）
- [x] Step 5: 错误提示：`"No plan found for issue #..."` → `"No plan found for: {input_ref}"`
- [x] Step 6: 无 Issue 路径（PR 模式）：`effective_issue = plan_issue or issue_number` → 从 Plan metadata 获取 issue_number，若无 Issue 则走 plan-name 路径
- [x] Step 7: 无 Issue 路径（非 PR 模式）：Issue sync 条件 `if effective_issue and repo` 已正确处理（plan_issue 为 None 时跳过）
- [x] Step 8: 输出提示中的 next_ref：`plan_issue or issue_number` → 若有 Issue 用 Issue number，否则用 plan_name
- [x] Step 9: 状态错误提示中的 `<issue>` 占位符：改为 `<issue-or-plan>`

**Verification**:

- [x] Step 1: 执行 `cd .agents/skills/dev-flow && python3 -c "from dev_flow.commands.complete import register_complete_parser; import argparse; p = argparse.ArgumentParser(); sp = p.add_subparsers(); register_complete_parser(sp); print(p.parse_args(['my-plan-name']))"`
- [x] Step 2: 确认 parse 不报错，target='my-plan-name'

### Task 2: verify 命令支持 plan-name

**Files**: `scripts/dev_flow/commands/verify.py`

**Changes**:

- [x] Step 1: argparse 参数从 `"issue", type=int` 改为 `"target", nargs="?"`
- [x] Step 2: `cmd_verify` 函数入口：`issue_number = args.issue` → `input_ref = args.target`
- [x] Step 3: Plan 查找：`find_plan_by_issue(issue_number, ...)` → `find_plan(input_ref, str(workspace_root))`
- [x] Step 4: 导入：添加 `from dev_flow.domain.plan.find import find_plan`
- [x] Step 5: 错误提示：`"No plan found for issue #..."` → `"No plan found for: {input_ref}"`
- [x] Step 6: `effective_issue = plan_issue or issue_number` → `plan_issue`（从 Plan metadata 获取，不再依赖 args 参数）
- [x] Step 7: Issue sync 条件：`if effective_issue and repo` 已正确处理无 Issue 路径
- [x] Step 8: 输出提示中的 next_ref：有 Issue 用 Issue number，否则用 plan_name
- [x] Step 9: PR 检查路径：`effective_issue` 用于 `_search_merged_pr_for_issue` 和 `_get_pr_url_from_issue`，无 Issue 时跳过

**Verification**:

- [x] Step 1: 执行 `cd .agents/skills/dev-flow && python3 -c "from dev_flow.commands.verify import register_verify_parser; import argparse; p = argparse.ArgumentParser(); sp = p.add_subparsers(); register_verify_parser(sp); print(p.parse_args(['my-plan-name', '--confirm']))"`
- [x] Step 2: 确认 parse 不报错

### Task 3: archive 命令支持 plan-name

**Files**: `scripts/dev_flow/commands/archive.py`

**Changes**:

- [x] Step 1: argparse 参数从 `"issue", type=int` 改为 `"target", nargs="?"`
- [x] Step 2: `cmd_archive` 函数入口：`issue_number = args.issue` → `input_ref = args.target`
- [x] Step 3: Plan 查找：`find_plan_by_issue(issue_number, ...)` → `find_plan(input_ref, str(workspace_root))`
- [x] Step 4: 导入：添加 `from dev_flow.domain.plan.find import find_plan`
- [x] Step 5: 错误提示：`"No plan found for issue #..."` → `"No plan found for: {input_ref}"`
- [x] Step 6: `plan_issue = get_plan_issue(plan_path) or issue_number` → `get_plan_issue(plan_path)`（不再回退到 args 参数）
- [x] Step 7: 无 Issue 路径：跳过 Issue sync（body + labels + close），只做 Plan 文件归档
- [x] Step 8: 输出提示：有 Issue 显示 `Issue: #N (closed)`，无 Issue 不显示 Issue 信息
- [x] Step 9: commit message：无 Issue 时用 plan_name（`commit_archived_plan` 已正确处理 issue_number=None）

**Verification**:

- [x] Step 1: 执行 `cd .agents/skills/dev-flow && python3 -c "from dev_flow.commands.archive import register_archive_parser; import argparse; p = argparse.ArgumentParser(); sp = p.add_subparsers(); register_archive_parser(sp); print(p.parse_args(['my-plan-name']))"`
- [x] Step 2: 确认 parse 不报错

### Task 4: plan --check 支持 plan-name 定位

**Files**: `scripts/dev_flow/commands/plan.py`

**Changes**:

- [x] Step 1: argparse 位置参数从 `"issue", type=int` 改为 `"target", nargs="?"`
- [x] Step 2: `cmd_plan` 函数入口：`issue_number = args.issue` → 判断 `args.target` 是数字还是字符串
- [x] Step 3: `--check` 模式：当 `args.target` 为字符串时，用 `find_plan_by_name()` 而非重构 plan name
- [x] Step 4: 导入：添加 `from dev_flow.domain.plan.find import find_plan, find_plan_by_name`
- [x] Step 5: Issue 模式（`args.target` 为数字）：行为不变，`int(args.target)` 获取 issue_number
- [x] Step 6: 创建模式（`--title`）：不受影响，因为 `args.target` 为 None
- [x] Step 7: 输出提示中的 next_ref 使用 plan_name 而非 issue_number

**Verification**:

- [x] Step 1: 执行 `flow.sh plan <plan-name> --check`，确认不报错
- [x] Step 2: 确认对已有 Plan 正确执行 check_doc 校验

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | Wopal | 无 |
| 1 | Task 2 | Wopal | 无 |
| 1 | Task 3 | Wopal | 无 |
| 1 | Task 4 | Wopal | 无 |

四个 Task 修改不同文件，无依赖，可并行执行。Complexity = Low，Wopal 直接实施。

## Test Plan

#### Unit Tests

##### Case U1: argparse 不拒绝 plan-name 字符串输入
- Goal: 确认四个命令的 argparse 不再将 plan-name 当作非法参数
- Fixture: 修改后的 Python 模块
- Execution:
  - [x] Step 1: 对 complete/verify/archive/plan 分别传入字符串参数执行 parse_args
  - [x] Step 2: 确认均返回 target=plan-name，无报错
- Expected Evidence: parse_args 返回正确结果，无 ValueError

##### Case U2: find_plan 数字输入走 Issue 路径
- Goal: 确认传入数字时仍走 Issue 查找
- Fixture: 已有 Issue 关联的 Plan 文件
- Execution:
  - [x] Step 1: 传入纯数字字符串（如 "121"）
  - [x] Step 2: 确认 find_plan 调用 find_plan_by_issue
- Expected Evidence: 找到正确 Plan 文件

#### Integration Tests

N/A — 三个命令是 CLI 入口，需在真实工作空间验证

#### E2E Tests

##### Case E1: 无 Issue Plan 完整流程验证
- Goal: 确认无 Issue 模式下 complete → verify --confirm → archive 全链路畅通
- Fixture: 一个处于 done 状态的无 Issue Plan（如本次修复的 Plan 本身）
- Execution:
  - [x] Step 1: 创建测试 Plan 并推进到 verifying 状态
  - [x] Step 2: 执行 `flow.sh verify <plan-name> --confirm`
  - [x] Step 3: 确认状态变为 done
  - [x] Step 4: 执行 `flow.sh archive <plan-name>`
  - [x] Step 5: 确认 Plan 文件移到 done/ 目录
- Expected Evidence: 命令返回 0，Plan 文件在 done/ 中，无 Issue close 操作

#### Regression Tests

##### Case R1: Issue 驱动模式不受影响
- Goal: 确认修改后传入 Issue number 时行为不变
- Fixture: 已有 Issue 关联的 Plan
- Execution:
  - [x] Step 1: 对一个 Issue 驱动的 Plan 执行 `flow.sh complete <issue-number>`
  - [x] Step 2: 确认 Issue sync 正常执行
  - [x] Step 3: 执行 `flow.sh verify <issue-number> --confirm`
  - [x] Step 4: 确认 Issue close 正常
- Expected Evidence: 全链路通过，Issue labels 和 close 行为与修改前一致

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] complete.py argparse 接受 plan-name 字符串
- [x] verify.py argparse 接受 plan-name 字符串
- [x] archive.py argparse 接受 plan-name 字符串
- [x] plan.py argparse 接受 plan-name 字符串
- [x] 四个命令内部使用 `find_plan()` 智能查找
- [x] 无 Issue 模式下不执行 Issue sync/close
- [x] Python import 无报错

### User Validation

#### Scenario 1: 无 Issue Plan 驱动流程
- Goal: 确认无 Issue 的 Plan 可以用 plan-name 完成 complete/verify/archive 全流程
- Precondition: 一个处于 verifying 状态的无 Issue Plan
- User Actions:
  1. 执行 `flow.sh verify <plan-name> --confirm`
  2. 执行 `flow.sh archive <plan-name>`
- Expected Result: 命令正常执行，无报错，Plan 文件归档到 done/

#### Scenario 2: Issue 驱动模式无回归
- Goal: 确认传入 Issue number 时行为与修改前一致
- Precondition: 一个有 Issue 关联的 Plan
- User Actions:
  1. 执行 `flow.sh complete <issue-number>`
  2. 确认 Issue labels 同步正确
- Expected Result: 与修改前行为一致，Issue body 和 labels 正确更新

- [x] 用户已完成上述功能验证并确认结果符合预期
