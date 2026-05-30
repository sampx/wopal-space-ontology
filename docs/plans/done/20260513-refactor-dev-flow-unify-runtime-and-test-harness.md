# refactor-dev-flow-unify-runtime-and-test-harness

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space
- **Created**: 2026-05-12
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

收敛 dev-flow 的运行时守卫与 Python 测试入口：把状态机校验和 space-level repo 解析抽到共享 helper，并统一测试 bootstrap，使 no-issue 流程与 `unittest discover` 都稳定可用。

## Technical Context

- `refactor-dev-flow-deduplicate-core` 已完成（commit `4d9c861`），把 logging/workspace/status 抽到 `core/`。`refactor-dev-flow-unify-project-path` 也已完成（commit `5db5a6a`），把项目级 repo 解析统一到 `domain/plan/project.py` 的 `resolve_project_path`。
- 当前仍存在三类技术债：
  1. `complete.py`、`verify.py`、`archive.py` 各自维护 `suggestion_map` + 状态校验 if-else 块，跨文件同步成本高。
  2. `archive.py:555` 无条件调用 `detect_space_repo(workspace_root)` 无 try-except，在无 remote 场景直接 `RuntimeError`——这是 **真实 bug**。
  3. tests/python 下 10+ 文件沿用手写 `SCRIPTS_DIR` 路径 hack，导致 `python3 -m unittest discover` 与直接脚本执行行为不一致。
- Repo 解析已有明确两层边界：
  - **项目级**（`domain/plan/project.py`）：Plan 对应哪个 git repo → `resolve_project_path`（已实现）
  - **空间级**（`core/workspace.py`）：workspace root 对应哪个 GitHub repo → `detect_space_repo`（需容错封装）
  - 本次 helper 封装的是空间级 `detect_space_repo` 的 issue-aware 容错调用，不重建 repo 解析。
- `approve.py` 的状态守卫已在上轮重构中清理完毕（无 `suggestion_map`，仅保留 if-elif 提示链），本轮不涉及。

## In Scope

- 新建共享 workflow helper（`core/workflow.py`），统一状态校验、下一步提示和空间级 repo 容错解析。
- 将 `complete.py`、`verify.py`、`archive.py` 迁移到共享 workflow helper（`approve.py` 已足够干净，不纳入）。
- 修复 `archive.py` 无条件调用 `detect_space_repo` 导致无 remote 场景崩溃的 bug。
- 新建统一测试 bootstrap helper，替换 tests/python 中内联 `SCRIPTS_DIR` 路径 hack。
- 补 no-issue complete/verify 回归测试，以及 test discovery 可运行性验证。
- 验证 `./scripts/flow.sh list` / `./scripts/flow.sh status <plan>` smoke path 保持正常。

## Out of Scope

- 拆分超大 command 文件（如 `archive.py`、`sync.py`、`issue.py`）为多个子模块。
- 将所有 `subprocess.run` 全面替换为统一进程执行框架。
- 改变现有 state machine 语义、Issue body 内容结构或 label 规则。
- 修改 `refactor-dev-flow-deduplicate-core` 之外的其他 active Plan。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| core workflow | `.wopal/skills/dev-flow/scripts/dev_flow/core/workflow.py`, `.wopal/skills/dev-flow/scripts/dev_flow/core/__init__.py` | 创建/修改 | 统一状态机守卫与空间级 repo 容错解析 |
| command runtime | `.wopal/skills/dev-flow/scripts/dev_flow/commands/complete.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/verify.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py` | 修改 | 改用共享 runtime helper，去掉重复 guard；修复 archive 无条件 repo 调用 bug |
| test bootstrap | `.wopal/skills/dev-flow/tests/python/support/bootstrap.py` | 创建 | 为 tests/python 提供统一 scripts 路径注入 |
| migrated tests | `.wopal/skills/dev-flow/tests/python/unit/test_check_doc.py`, `.wopal/skills/dev-flow/tests/python/unit/test_issue_title.py`, `.wopal/skills/dev-flow/tests/python/unit/test_plan_link_contract.py`, `.wopal/skills/dev-flow/tests/python/unit/test_plan_naming.py`, `.wopal/skills/dev-flow/tests/python/unit/test_step_completion.py`, `.wopal/skills/dev-flow/tests/python/unit/test_type_labels.py`, `.wopal/skills/dev-flow/tests/python/unit/test_user_validation.py`, `.wopal/skills/dev-flow/tests/python/unit/test_core_workspace.py`, `.wopal/skills/dev-flow/tests/python/unit/test_core_status.py`, `.wopal/skills/dev-flow/tests/python/unit/test_archive_idempotent.py`, `.wopal/skills/dev-flow/tests/python/integration/test_issue_contract.py`, `.wopal/skills/dev-flow/tests/python/integration/test_archive_plan_link.py` | 修改 | 替换内联 `SCRIPTS_DIR` hack |
| new regressions | `.wopal/skills/dev-flow/tests/python/unit/test_core_workflow.py`, `.wopal/skills/dev-flow/tests/python/integration/test_no_issue_lifecycle.py` | 创建 | 固化 no-issue repo 解析与 shared workflow 行为 |

## Implementation

### Task 1: 新建 shared workflow runtime helper

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/core/workflow.py`, `.wopal/skills/dev-flow/scripts/dev_flow/core/__init__.py`, `.wopal/skills/dev-flow/tests/python/unit/test_core_workflow.py`

**Changes**:

- [x] Step 1: 新建 `core/workflow.py`，封装 expected status 校验与下一步提示生成逻辑（`guard_status` + `format_suggestion`）。
- [x] Step 2: 在 helper 中封装空间级 repo 容错解析（`resolve_space_repo`）：封装 `detect_space_repo` 的 issue-aware 调用——无 Issue 时直接返回空字符串；有 Issue 但 repo 不可解析时 try-except 并 log warning，不阻断本地 no-issue 流程。注意：此处不重建 repo 解析逻辑，仅容错包装 `core/workspace.py` 的 `detect_space_repo`。
- [x] Step 3: 将 workflow helper 导出到 `core/__init__.py`，保持 command 层导入路径清晰。
- [x] Step 4: 新增 `test_core_workflow.py`，覆盖状态校验、提示文案与 repo 解析分支。

**Verification**:

- [x] Step 1: 执行 `python3 tests/python/unit/test_core_workflow.py -v`
- [x] Step 2: 确认 helper 单元测试全部通过且返回码为 0

### Task 2: command 层迁移到 shared runtime helper（含 archive bug fix）

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/commands/complete.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/verify.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py`, `.wopal/skills/dev-flow/tests/python/integration/test_no_issue_lifecycle.py`

**Changes**:

- [x] Step 1: `complete.py` 改用 `guard_status` + `format_suggestion`，删除本地 `suggestion_map`；改用 `resolve_space_repo` 替换手写 try-except `detect_space_repo` 块。
- [x] Step 2: `verify.py` 改用 `guard_status` + `format_suggestion`，删除本地 `suggestion_map`；改用 `resolve_space_repo` 替换手写 try-except `detect_space_repo` 块。
- [x] Step 3: **[bug fix]** `archive.py` 改用 `guard_status` + `format_suggestion`，删除本地 `suggestion_map`；将第 555 行无条件 `detect_space_repo(workspace_root)` 替换为 `resolve_space_repo(issue, workspace_root)`，修复无 remote 场景直接崩溃。
- [x] Step 4: 新增 `test_no_issue_lifecycle.py`，回归验证 no-issue `complete` / `verify` 路径不会因 repo 解析失败而中断。

**Verification**:

- [x] Step 1: 执行 `python3 tests/python/integration/test_no_issue_lifecycle.py -v`
- [x] Step 2: 执行 `python3 -m compileall scripts/dev_flow/commands/complete.py scripts/dev_flow/commands/verify.py scripts/dev_flow/commands/archive.py`

### Task 3a: 引入统一 test bootstrap 并迁移 core tests

**Files**: `.wopal/skills/dev-flow/tests/python/support/bootstrap.py`, `.wopal/skills/dev-flow/tests/python/unit/test_core_workspace.py`, `.wopal/skills/dev-flow/tests/python/unit/test_core_status.py`, `.wopal/skills/dev-flow/tests/python/unit/test_archive_idempotent.py`

**Changes**:

- [x] Step 1: 新建 `tests/python/support/bootstrap.py`，提供统一的 scripts path 注入 helper（基于 skill 根目录推导，支持直接执行和 `unittest discover` 两种模式）。
- [x] Step 2: 将 `test_core_workspace.py`、`test_core_status.py`、`test_archive_idempotent.py` 中的内联 `SCRIPTS_DIR` hack 替换为 `from support.bootstrap import ensure_scripts_path`。
- [x] Step 3: 验证迁移后这 3 个测试既可直接脚本执行，也可通过 `python3 -m unittest discover` 运行。

**Verification**:

- [x] Step 1: 执行 `python3 -m unittest discover -s tests/python/unit -p "test_core_*.py"`
- [x] Step 2: 确认命令无需额外 `PYTHONPATH` 且返回码为 0

### Task 3b: 迁移剩余 tests

**Files**: `.wopal/skills/dev-flow/tests/python/unit/test_check_doc.py`, `.wopal/skills/dev-flow/tests/python/unit/test_issue_title.py`, `.wopal/skills/dev-flow/tests/python/unit/test_plan_link_contract.py`, `.wopal/skills/dev-flow/tests/python/unit/test_plan_naming.py`, `.wopal/skills/dev-flow/tests/python/unit/test_step_completion.py`, `.wopal/skills/dev-flow/tests/python/unit/test_type_labels.py`, `.wopal/skills/dev-flow/tests/python/unit/test_user_validation.py`, `.wopal/skills/dev-flow/tests/python/integration/test_issue_contract.py`, `.wopal/skills/dev-flow/tests/python/integration/test_archive_plan_link.py`

**Changes**:

- [x] Step 1: 将上述 9 个测试文件的内联 `SCRIPTS_DIR` hack 替换为 `from support.bootstrap import ensure_scripts_path`。
- [x] Step 2: 确认迁移后全部测试可被 `python3 -m unittest discover` 发现并执行。

**Verification**:

- [x] Step 1: 执行 `python3 -m unittest discover -s tests/python/unit -p "test_*.py"` 确认全部 unit tests 通过
- [x] Step 2: 执行 `python3 -m unittest discover -s tests/python/integration -p "test_*.py"` 确认 integration tests 通过

### Task 4: 收口 smoke / regression 验证

**Files**: `.wopal/skills/dev-flow/scripts/flow.sh`, `.wopal/skills/dev-flow/references/plan-validation.md`（仅当测试/运行方式说明需要同步时修改）

**Changes**:

- [x] Step 1: 执行重复模式扫描，确认 `complete.py`、`verify.py`、`archive.py` 不再保留本地 `suggestion_map` / 同类 runtime guard 重复块。
- [x] Step 2: 执行 tests/python 下路径 hack 扫描，确认不再残留旧式 `SCRIPTS_DIR` 片段。
- [x] Step 3: 运行 `./scripts/flow.sh list` 与 `./scripts/flow.sh status refactor-dev-flow-unify-runtime-and-test-harness` smoke test。
- [x] Step 4: 如测试运行方式发生可见变化，补充最小必要文档说明。

**Verification**:

- [x] Step 1: 执行 `rg -n "SCRIPTS_DIR = os.path.dirname\(os.path.dirname\(os.path.dirname\(os.path.dirname\(os.path.dirname\(os.path.abspath\(__file__\)\)\)\)\)\)" tests/python`
- [x] Step 2: 执行 `python3 -m compileall scripts/dev_flow && ./scripts/flow.sh list && ./scripts/flow.sh status refactor-dev-flow-unify-runtime-and-test-harness`

## Delegation Strategy

使用小批次串行委派，避免再次出现“大任务整包给 fae 导致上下文过高”的情况。前置依赖已满足：`refactor-dev-flow-deduplicate-core`（commit `4d9c861`）和 `refactor-dev-flow-unify-project-path`（commit `5db5a6a`）均已完成。

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | Wopal | 前置依赖已完成 |
| 2 | Task 2 | fae | Task 1 |
| 3 | Task 3a | fae | Task 1 |
| 4 | Task 3b | fae | Task 3a |
| 5 | Task 4 + final review | Wopal | Task 2-3 |

**验证纪律**：

- 批次 1 完成后先跑 workflow helper 单测，再继续迁移 commands。
- 批次 2 完成后先做 compile + no-issue integration test，不达标不进入 Task 3。
- 批次 3-4 各自完成后先做 compile / unittest / grep 扫描，不达标不进入下一批。
- 批次 5 由 Wopal 运行 smoke / regression，读取 diff 后再勾选 Plan。

## Test Plan

#### Unit Tests

##### Case U1: workflow status guard 输出一致
- Goal: 确认 shared workflow helper 能根据当前状态给出正确 next-step 提示
- Fixture: `core/workflow.py` helper 和 mock status 输入
- Execution:
  - [x] Step 1: 执行 `python3 tests/python/unit/test_core_workflow.py -v`
  - [x] Step 2: 确认状态校验与提示文案断言全部通过
- Expected Evidence: `test_core_workflow.py` 返回码为 0，覆盖 planning/executing/verifying/done 分支

##### Case U2: issue-aware repo 解析
- Goal: 确认无 Issue 场景不会强制 repo 解析，有 Issue 时仍能返回 owner/repo 或 warning
- Fixture: `core/workflow.py` 中 repo helper 的 mocked workspace / issue 输入
- Execution:
  - [x] Step 1: 在 `test_core_workflow.py` 中执行 issue/no-issue 两类用例
  - [x] Step 2: 确认 no-issue 分支不抛异常，有 Issue 分支行为可预期
- Expected Evidence: helper 单测全部通过，no-issue 分支返回空 repo

##### Case U3: bootstrap helper 可独立注入 scripts path
- Goal: 确认 tests/python bootstrap helper 可替代各文件内联路径 hack
- Fixture: `tests/python/support/bootstrap.py`
- Execution:
  - [x] Step 1: 执行 `python3 -m unittest discover -s tests/python/unit -p "test_core_*.py"`
  - [x] Step 2: 确认测试导入成功，无需额外设置 `PYTHONPATH`
- Expected Evidence: discover 成功启动并执行目标 test modules

#### Integration Tests

##### Case I1: no-issue complete 路径不依赖 GitHub repo
- Goal: 确认 `complete` 在 no-issue Plan 上不会因为 repo 解析失败而中断
- Fixture: `test_no_issue_lifecycle.py` 中的 mocked no-issue plan
- Execution:
  - [x] Step 1: 执行 `python3 tests/python/integration/test_no_issue_lifecycle.py -v`
  - [x] Step 2: 确认 complete no-issue 分支返回成功或正确 guidance 输出
- Expected Evidence: 测试断言 `detect_space_repo` 失败不会阻断 no-issue `complete`

##### Case I2: no-issue verify 路径不依赖 GitHub repo
- Goal: 确认 `verify` 在 no-issue Plan 上不会因为 repo 解析失败而中断
- Fixture: 同上 integration fixture
- Execution:
  - [x] Step 1: 在 `test_no_issue_lifecycle.py` 中执行 verify no-issue 用例
  - [x] Step 2: 确认命令输出 guidance 或完成状态，不出现 repo 解析异常
- Expected Evidence: 测试断言 no-issue `verify` 分支返回码为 0 或符合预期

##### Case I3: migrated tests 可被 discover 驱动
- Goal: 确认迁移后的 tests/python 不再依赖每个文件自带路径 hack
- Fixture: 迁移后的 unit tests 集合
- Execution:
  - [x] Step 1: 执行 `python3 -m unittest discover -s tests/python/unit -p "test_*.py"`
  - [x] Step 2: 确认目标测试模块导入成功，至少 bootstrap 迁移范围内模块全部可运行
- Expected Evidence: discover 不再因 `ModuleNotFoundError: dev_flow` 失败

#### E2E Tests

##### Case E1: dev-flow 常用查询命令 smoke
- Goal: 确认 runtime/test harness 重构后常用查询命令仍正常工作
- Fixture: 当前空间已有 active plan
- Execution:
  - [x] Step 1: 执行 `./scripts/flow.sh list`
  - [x] Step 2: 执行 `./scripts/flow.sh status refactor-dev-flow-unify-runtime-and-test-harness`
- Expected Evidence: 两条命令返回码为 0，输出包含 active plan 信息与正确状态

#### Regression Tests

##### Case R1: tests/python 不再残留旧式 SCRIPTS_DIR hack
- Goal: 确认路径注入逻辑已统一收敛到 bootstrap helper
- Fixture: tests/python 目录
- Execution:
  - [x] Step 1: 执行 `rg -n "SCRIPTS_DIR = os.path.dirname\(os.path.dirname\(os.path.dirname\(os.path.dirname\(os.path.dirname\(os.path.abspath\(__file__\)\)\)\)\)\)" tests/python`
  - [x] Step 2: 确认没有匹配结果
- Expected Evidence: `rg` 返回码为 1 或空输出

##### Case R2: command runtime guard 不再重复散落
- Goal: 确认目标 command 文件不再保留重复 suggestion map / 同类状态 guard 逻辑块
- Fixture: `complete.py`、`verify.py`、`archive.py`
- Execution:
  - [x] Step 1: 执行针对 `suggestion_map = {`、`current_status !=`、直接 repo lazy resolve 片段的 `rg` 扫描
  - [x] Step 2: 确认命中只剩 shared helper 的调用点或明确保留的单一入口
- Expected Evidence: 目标 command 文件不再各自维护重复的状态提示分支

##### Case R3: Python 脚本整体可编译
- Goal: 确认 helper 抽取与测试迁移后没有语法错误或明显循环导入
- Fixture: dev-flow Python scripts
- Execution:
  - [x] Step 1: 执行 `python3 -m compileall scripts/dev_flow`
  - [x] Step 2: 确认命令返回码为 0
- Expected Evidence: compileall 通过

### Adjustment Strategy

若 shared workflow helper 抽象过度，优先回到“两个最小 helper（`guard_status` + `resolve_space_repo`）”而不是继续扩展通用框架。

## Acceptance Criteria

### Agent Verification

- [x] `core/workflow.py` 已创建并被 `complete.py`、`verify.py`、`archive.py` 复用
- [x] `archive.py` 不再无条件调用 `detect_space_repo`，无 remote 场景不再崩溃
- [x] no-issue `complete` / `verify` 回归测试通过
- [x] tests/python 中不再残留旧式 `SCRIPTS_DIR` 路径 hack
- [x] `python3 -m unittest discover -s tests/python/unit -p "test_core_*.py"` 无需额外 `PYTHONPATH` 通过
- [x] `python3 -m compileall scripts/dev_flow` 通过
- [x] `./scripts/flow.sh list` 与 `./scripts/flow.sh status refactor-dev-flow-unify-runtime-and-test-harness` 通过

### User Validation

#### Scenario 1: no-issue Plan 生命周期不再绑定 GitHub repo
- Goal: 确认维护本地 no-issue Plan 时，`complete` / `verify` 不会再报 repo 解析或 remote 必需错误
- Precondition: 存在一个 no-issue Plan，且处于 `executing` 或 `verifying` 状态
- User Actions:
  1. 在 `.wopal/skills/dev-flow` 目录执行对应状态下的 `./scripts/flow.sh complete <plan-name>` 或 `./scripts/flow.sh verify <plan-name>`
  2. 观察命令输出中的下一步 guidance 或状态变更
- Expected Result: 命令不会因 GitHub repo 解析失败而中断，输出保持可理解的 next-step guidance

#### Scenario 2: 运行核心单测不再需要手工设置 PYTHONPATH
- Goal: 确认维护者可直接从 skill 根目录运行核心测试，而无需再手写路径注入
- Precondition: `.wopal/skills/dev-flow` 工作区可执行 Python 测试
- User Actions:
  1. 在 `.wopal/skills/dev-flow` 目录执行 `python3 -m unittest discover -s tests/python/unit -p "test_core_*.py"`
  2. 观察测试是否正常导入并运行
- Expected Result: 测试在不设置额外 `PYTHONPATH` 的情况下正常启动并通过

- [x] 用户已完成上述功能验证并确认结果符合预期
