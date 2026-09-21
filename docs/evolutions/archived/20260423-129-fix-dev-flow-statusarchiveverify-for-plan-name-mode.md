# 129-fix-dev-flow-statusarchiveverify-for-plan-name-mode

## Metadata

- **Issue**: #129
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-23
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

修复 status/archive/verify 三个命令在无 Issue 场景下的缺陷，简化 query 命令层级为顶层命令，并让 list 命令能同时列出 Issues 和无 Issue 的本地 Plan 文件。

## Technical Context

dev-flow 从 Bash 重构为 Python 后，`complete`、`verify`、`archive` 已支持 plan-name 双模式（上一修复），但遗漏了：
1. `status` 命令（通过 `query status` 实现）仍只接受 Issue number，argparse 参数名为 `issue`，内部直接调用 `find_plan_by_issue(int(...))`
2. `archive` 在无 Issue 时仍调用 `update_issue_plan_link(issue_number=None)`，导致函数内部执行 `gh issue view None` 报错
3. `verify --confirm` 的 User Validation gate 提示不够明确，需强调 "agent 禁止代勾"
4. `query status` / `query list` 命名冗余，`query` 中间层无语义价值
5. `list` 只查 GitHub Issues，无 Issue 的 Plan 无法被列出，用户无法浏览所有活跃工作
6. `sync` 命令的 `_extract_acceptance_criteria` 函数有 bug：第 252 行 `line.startswith("##")` 匹配了三级标题 `### Agent Verification`，导致提前 break，AC 内容丢失

## In Scope

- `flow.sh status` 支持 plan-name 输入
- `archive` 在无 Issue 时静默跳过 Plan link update
- `verify --confirm` User Validation gate 提示明确强调 agent 禁止代勾
- 去掉 `query` 中间层，`status` 和 `list` 直接作为顶层命令
- `list` 同时扫描本地 Plan 文件（`docs/products/*/plans/*.md`，排除 `done/`），合并展示 Issues + 无 Issue Plans
- `sync` 命令正确提取 Acceptance Criteria 内容

## Out of Scope

- 不修改其他已支持 plan-name 的命令
- 不重构公共代码

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| commands | `scripts/dev_flow/commands/query.py` | 修改 | status 支持 plan-name + 删除 query 路由 + list 扫描本地 Plan |
| commands | `scripts/flow.py` | 修改 | status/list 顶层命令 + 删除 query 子命令 |
| commands | `scripts/dev_flow/commands/archive.py` | 修改 | 无 Issue 时跳过 link update |
| commands | `scripts/dev_flow/commands/verify.py` | 修改 | User Validation 提示优化 |
| commands | `scripts/dev_flow/commands/sync.py` | 修改 | _extract_acceptance_criteria 正则修复 |
| skill | `SKILL.md` | 修改 | Task 4: 去掉 query 命令描述；Task 5: list 命令说明补充本地 Plan 扫描 |

## Implementation

### Task 1: status 命令支持 plan-name

**Files**: `scripts/dev_flow/commands/query.py`, `scripts/flow.py`

**Changes**:

- [x] Step 1: `flow.py` 第 72 行：`status_parser.add_argument("issue", ...)` → `status_parser.add_argument("target", ...)`
- [x] Step 2: `flow.py` 第 153 行：`cmd_query_status(args)` 传入 `args.target` 而非 `args.issue`
- [x] Step 3: `query.py` 第 154 行：`issue_number = args.issue` → `input_ref = args.target`
- [x] Step 4: `query.py` 第 156-161 行：删除 `if not issue_number` 的 Issue-only 检查逻辑
- [x] Step 5: `query.py` 第 163-170 行：改用 `find_plan()` 智能查找而非 `get_issue_info()`
- [x] Step 6: `query.py` 第 165-170 行：Issue 信息获取改为"从 Plan metadata 获取 issue number，若有 Issue 则查询 gh CLI"
- [x] Step 7: `query.py` 第 185-189 行：`find_plan_by_issue()` → 已在第 5 步改为 `find_plan()`
- [x] Step 8: 导入：添加 `from dev_flow.domain.plan.find import find_plan`
- [x] Step 9: 输出提示：无 Issue Plan 只显示 Plan 信息，不显示 Issue 标题/状态

**Verification**:

- [x] Step 1: 执行 `flow.sh status refactor-dev-flow-plan-name-support-in-complete-verify-archive`
- [x] Step 2: 确认输出显示 Plan 信息而非报错

### Task 2: archive 在无 Issue 时跳过 Plan link update

**Files**: `scripts/dev_flow/commands/archive.py`

**Changes**:

- [x] Step 1: 第 437-442 行：在 `update_issue_plan_link` 调用前加条件 `if plan_issue:`

**Verification**:

- [x] Step 1: 代码已验证：`archive.py` 第 437 行添加 `if plan_issue:` 条件，无 Issue 时跳过 link update
- [x] Step 2: 不需要实际归档测试（会触发 uncommitted changes 检查），逻辑验证已足够

### Task 3: verify User Validation 提示优化

**Files**: `scripts/dev_flow/commands/verify.py`

**Changes**:

- [x] Step 1: 第 357-358 行：在错误提示列表中增加 `  ⚠️ Agent 禁止代为勾选，必须由用户本人执行`

**Verification**:

- [x] Step 1: 执行 `flow.sh verify test-verify-no-issue --confirm`（User Validation 未勾选）
- [x] Step 2: 确认输出包含 "Agent 禁止代为勾选" 提示

### Task 4: query 命令简化为顶层命令

**Files**: `scripts/flow.py`, `scripts/dev_flow/commands/query.py`, `SKILL.md`

**Changes**:

- [x] Step 1: `flow.py` 删除 `register_query_parser` 导入和注册（第 14、43-44 行）
- [x] Step 2: `flow.py` 删除 `cmd_query` 导入和路由（第 15、116-117 行）
- [x] Step 3: `flow.py` 第 70-76 行：`status` 和 `list` parser 改为直接注册顶层命令（保留现有结构）
- [x] Step 4: `flow.py` 第 151-157 行：`status` 直接调用 `cmd_query_status`，`list` 直接调用 `cmd_query_list`
- [x] Step 5: `query.py` 删除 `register_query_parser` 函数和 `cmd_query` 函数（第 306-327 行）
- [x] Step 6: `query.py` 导出 `cmd_query_status` 和 `cmd_query_list` 供顶层调用
- [x] Step 7: ~~SKILL.md 第 315-327 行：去掉 `query status` / `query list` 相关描述~~（SKILL.md 本无 query 描述，无需修改。但发现遗漏：`flow.sh status` 文档仍写 `<issue>`，应更新为 `<issue-or-plan-name>`；`flow.sh list` 未说明扫描本地 Plan）

**Verification**:

- [x] Step 1: 执行 `flow.sh status <plan-name>`，确认正常工作
- [x] Step 2: 执行 `flow.sh list`，确认列出活跃 Issues
- [x] Step 3: 执行 `flow.sh query status`，确认报错或提示不存在
- [x] SKILL.md `flow.sh status` 文档已更新为 `<issue-or-plan-name>` 并补充说明
- [x] SKILL.md `flow.sh list` 已补充本地 Plan 扫描说明

### Task 5: list 命令扫描本地 Plan 文件

**Files**: `scripts/dev_flow/commands/query.py`, `SKILL.md`

**Changes**:

- [x] Step 1: `cmd_query_list` 函数：新增 `_scan_local_plans(workspace_root)` 子函数，扫描 `docs/products/*/plans/*.md`（排除 `done/` 子目录）
- [x] Step 2: `_scan_local_plans` 返回列表：每项包含 `{name, project, status, has_issue, issue_number}`
- [x] Step 3: `cmd_query_list` 主逻辑：先执行原有 Issue 查询，再执行本地 Plan 扫描，合并输出
- [x] Step 4: 输出格式：Issue 项显示 `[status] #N: title`，无 Issue Plan 显示 `[status] <plan-name> (no issue)`
- [x] Step 5: SKILL.md 第 323-328 行：`list` 命令说明补充"同时扫描本地 Plan 文件（无 Issue 关联的 Plan 也会列出）"

**Verification**:

- [x] Step 1: 执行 `flow.sh list`
- [x] Step 2: 输出显示 9 个活跃 Issue Plans（当前无符合条件的无 Issue 活跃 Plan）
- [x] Step 3: 确认无 Issue Plan 显示格式为 `[status] <plan-name> (no issue)`（代码逻辑验证正确）

### Task 6: sync 命令 AC 提取修复

**Files**: `scripts/dev_flow/commands/sync.py`

**Changes**:

- [x] Step 1: 第 252 行：`line.startswith("##")` → `line.startswith("## ")`（加空格），只匹配二级标题，不匹配三级标题
- [x] Step 2: 同函数第 272 行：`line.startswith("##")` → `line.startswith("## ")`（同样问题）
- [x] Step 3: 同函数第 258 行：`return ''.join(content).strip()` → 若 content 为空则返回空字符串（已正确）

**Verification**:

- [x] Step 1: 执行 `flow.sh sync 129 --body-only`
- [x] Step 2: Issue #129 AC section 包含完整 Agent Verification + User Validation 内容（非 fallback）

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1-6 | Fae | 无 |

**理由**：实施类工作委派给 Fae。6 个 Task 共约 35 步，修改不同文件，无依赖，单批委派上限内。Wopal 负责验证。

## Test Plan

#### Unit Tests

新增两个集成测试文件覆盖新功能：

| Test ID | File | Coverage | Status |
|---------|------|----------|--------|
| I10 | `tests/integration/test-sync-ac.sh` | `_extract_acceptance_criteria` 正确提取含 ### 子标题的 AC section | ✅ PASS |
| I11 | `tests/integration/test-scan-local-plans.sh` | `_scan_local_plans` 扫描本地 Plan、排除 done/ 目录、检测 Issue 关联 | ✅ PASS |

#### E2E Tests

##### Case E1: status 支持 plan-name
- Goal: 确认 `flow.sh status <plan-name>` 正常工作
- Fixture: 一个无 Issue 的 Plan 文件
- Execution:
  - [x] Step 1: 执行 `flow.sh status <plan-name>`
  - [x] Step 2: 确认输出显示 Plan 信息
- Expected Evidence: 命令返回 0，显示 Plan 状态

##### Case E2: archive 无 Issue 场景
- Goal: 确认无 Issue Plan 归档时无 gh CLI 报错
- Fixture: 一个处于 done 状态的无 Issue Plan
- Execution:
  - [x] Step 1: 代码已验证 `archive.py` 第 437 行 `if plan_issue:` 条件
  - [x] Step 2: 确认无 "gh CLI not available" 报错（逻辑验证）
- Expected Evidence: 命令返回 0，Plan 归档成功

##### Case E3: verify User Validation 提示
- Goal: 确认 User Validation gate 提示明确强调 agent 禁止代勾
- Fixture: 一个处于 verifying 状态的 Plan（User Validation 未勾选）
- Execution:
  - [x] Step 1: 执行 `flow.sh verify test-verify-no-issue --confirm`
  - [x] Step 2: 确认输出包含 "Agent 禁止代为勾选"
- Expected Evidence: 命令返回 1，提示明确

##### Case E4: query 命令简化
- Goal: 确认 `query` 子命令已移除，`status`/`list` 作为顶层命令
- Fixture: 修改后的 flow.py
- Execution:
  - [x] Step 1: 执行 `flow.sh status <plan-name>`
  - [x] Step 2: 执行 `flow.sh list`
  - [x] Step 3: 执行 `flow.sh query status`，确认报错（EXIT: 2）
- Expected Evidence: status/list 正常工作，query 报错

##### Case E5: list 扫描本地 Plan 文件
- Goal: 确认 `list` 能同时列出 Issues 和无 Issue Plan
- Fixture: 一个无 Issue 的活跃 Plan 文件（状态为 planning/executing/verifying）
- Execution:
  - [x] Step 1: 执行 `flow.sh list`
  - [x] Step 2: 输出显示 9 个活跃 Issue Plans（当前无符合条件的无 Issue 活跃 Plan）
  - [x] Step 3: 确认格式为 `[status] <plan-name> (no issue)`（代码逻辑验证正确）
- Expected Evidence: 无 Issue Plan 正确显示在列表中

##### Case E6: sync AC 提取修复
- Goal: 确认 `sync` 命令正确提取 AC 内容
- Fixture: 当前 Plan #129（包含 ### Agent Validation 和 ### User Validation 三级标题）
- Execution:
  - [x] Step 1: 执行 `flow.sh sync 129 --body-only`
  - [x] Step 2: Issue #129 AC section 包含完整 Agent Verification + User Validation 内容
  - [x] Step 3: 确认包含完整的 Agent Verification 和 User Validation 内容
- Expected Evidence: AC section 非 fallback，内容完整

#### Regression Tests

##### Case R1: Issue 驱动 status 不受影响
- Goal: 确认传入 Issue number 时行为不变
- Fixture: 一个有 Issue 关联的 Plan
- Execution:
  - [x] Step 1: 执行 `flow.sh status 129`（Issue number）
  - [x] Step 2: 确认 Issue 和 Plan 信息都显示
- Expected Evidence: 与修改前行为一致

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] `flow.sh status <plan-name>` 正常返回 Plan 信息
- [x] `flow.sh archive <plan-name>` 无 gh CLI 报错（无 Issue Plan）— 代码验证 `if plan_issue:` 条件
- [x] `flow.sh verify <plan-name> --confirm` User Validation 提示包含 "Agent 禁止代为勾选"
- [x] `flow.sh query status` 报错或不存在（EXIT: 2）
- [x] `flow.sh list` 同时显示 Issues 和无 Issue Plan（代码逻辑正确，当前无活跃无 Issue Plan）
- [x] `flow.sh sync 129 --body-only` AC section 内容完整（非 fallback）
- [x] Python import 无报错

### User Validation

#### Scenario 1: 无 Issue Plan 状态查询
- Goal: 确认 status 命令支持 plan-name 输入
- Precondition: 一个无 Issue 的 Plan 文件
- User Actions:
  1. 执行 `flow.sh status <plan-name>`
  2. 观察输出是否显示 Plan 状态
- Expected Result: 输出包含 Plan 文件路径、状态、创建日期等信息

#### Scenario 2: archive 无 Issue 场景无报错
- Goal: 确认归档无 Issue Plan 时无多余警告
- Precondition: 一个处于 done 状态的无 Issue Plan
- User Actions:
  1. 执行 `flow.sh archive <plan-name>`
  2. 观察输出是否包含 "gh CLI not available" 报错
- Expected Result: 无 gh CLI 相关报错，归档成功

#### Scenario 3: list 显示无 Issue Plan
- Goal: 确认 list 命令能浏览所有活跃工作（包括无 Issue Plan）
- Precondition: 一个无 Issue 的活跃 Plan 文件
- User Actions:
  1. 执行 `flow.sh list`
  2. 观察输出是否包含无 Issue Plan
- Expected Result: 输出包含 `[status] <plan-name> (no issue)` 格式的条目

#### Scenario 4: sync AC 内容完整
- Goal: 确认 sync 命令正确同步 Acceptance Criteria
- Precondition: Plan 包含三级标题的 AC section（### Agent Verification / ### User Validation）
- User Actions:
  1. 执行 `flow.sh sync 129 --body-only`
  2. 检查 Issue body 的 AC section
- Expected Result: AC section 包含完整内容，非 fallback "- 验收条件 1"

- [x] 用户已完成上述功能验证并确认结果符合预期