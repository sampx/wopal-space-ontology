# 121-refactor-dev-flow-clean-up-issue-scripts

## Metadata

- **Issue**: #121
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-21
- **Updated**: 2026-04-22
- **Status**: done

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

用 Python 重写 dev-flow，但采用**可执行的渐进式 TDD 迁移**，而不是一次性大爆炸替换：

- 先冻结当前 Bash 行为，作为回归基线
- 再按行为切片逐步迁移到 Python
- 每个切片都遵循 `先写新测试（红）→ 实现（绿）→ 跑旧回归（绿）`
- `scripts/flow.sh` 名称保持不变，`SKILL.md` 尽量不改
- 旧 Bash `flow.sh` 改名为 `flow-legacy.sh` 暂时保留，作为参考实现和兜底回退

**核心价值**：
- 消除 6344 行 Bash 的维护上限，但不牺牲现有稳定流程
- 不引入 skill 运行时不支持的外部 Python 依赖
- 用 legacy Bash 作为行为 oracle，降低迁移风险
- 用 hybrid wrapper 保持命令面稳定，让迁移可以分阶段落地

## Technical Context

### 当前行为基线

当前 dev-flow 已有 Bash 测试体系，覆盖核心行为：

| Test Group | Current Coverage |
|---|---|
| 标题/命名/标签 | `test-issue-title.sh`, `test-plan-naming.sh`, `test-type-labels.sh` |
| Plan 校验 | `test-check-doc.sh`, `test-user-validation.sh` |
| git / push / plan link | `test-approve-push.sh`, `test-plan-link-contract.sh` |
| issue renderer / issue command | `test-issue-contract.sh`, `test-issue-create-command.sh`, `test-issue-update-command.sh`, `test-issue-update.sh` |
| command surface / workflow gates | `test-command-surface.sh`, `test-approve-confirm-clean.sh`, `test-verify-gate.sh`, `test-no-issue-pr.sh` |
| archive / resources | `test-archive-plan-link.sh`, `test-related-resources-links.sh` |

这些 Bash 测试是**旧实现的回归基线**，但它们本身不能直接证明 Python 实现正确，因为很多测试会直接 `source lib/*.sh`。因此迁移必须新增 Python 测试，并建立 Bash 测试 → Python 测试的覆盖映射。

### Skill 运行约束

本计划按当前 skill 约束设计：

1. skill 规范只要求目录结构，不提供 Python 包管理能力
2. 当前 ontology skill 体系中没有 `requirements.txt` / `pyproject.toml` / venv 约定
3. 不能假设 skill 运行时可安装 `pytest` / `typer` / `rich` / `pyyaml` 等外部包

**因此本方案使用 Python 标准库实现**：

- CLI：`argparse`
- 测试：`unittest`
- mock：`unittest.mock`
- fixture / temp dir：`tempfile`, `pathlib`, `shutil`
- subprocess 封装：`subprocess`

### 渐进式迁移架构

目标态不是直接删除 Bash，而是先形成 hybrid 架构：

```text
scripts/
├── flow.sh              # 对外稳定入口（wrapper / hybrid router）
├── flow-legacy.sh       # 旧 Bash 入口，临时保留作参考与回退
├── flow.py              # Python CLI 入口（argparse）
└── dev_flow/            # Python 实现
    ├── commands/
    ├── domain/
    └── infra/
```

迁移期间：

- `flow.sh` 始终是唯一公共入口
- 已迁移命令 → 路由到 Python
- 未迁移命令 → 回退到 `flow-legacy.sh`
- 旧 `lib/` 和 `scripts/cmd/` 暂时保留，不在本期删除

### TDD 纠偏

正确的 TDD 落地方式应为：

1. **先把旧 Bash 回归跑绿**，冻结现状
2. **为某个行为切片写新的 Python 测试**
3. **先验证新测试对 Python 实现是红的**（因为还没实现）
4. 实现该切片，直到新 Python 测试转绿
5. 再跑旧 Bash 回归，确认没有破坏 legacy / fallback 行为

所以，Phase 0 不应该写成“Python 新测试全部通过”，那是不成立的。

## In Scope

- 用 Python 标准库重写 dev-flow
- 保持公共入口仍为 `scripts/flow.sh`
- 将旧 Bash 入口改名为 `scripts/flow-legacy.sh` 并临时保留
- 建立 Bash 行为覆盖矩阵
- 逐切片建立 Python `unittest` 测试并实现迁移
- 用 hybrid wrapper 分阶段切换命令到 Python
- 新增 archive 前项目 repo dirty gate，并按 TDD 先写失败测试

## Out of Scope

- 引入第三方 Python 依赖（`pytest`, `typer`, `rich`, `pyyaml` 等）
- 在本期删除全部 legacy Bash 源码
- 修改 `SKILL.md` 的命令名称或主流程文案
- 改变 #120 已确定的用户命令面与字段契约
- 把 dev-flow 并入 wopal-cli

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| Public entry | `scripts/flow.sh` | 重写 | 稳定 wrapper / hybrid router |
| Legacy entry | `scripts/flow-legacy.sh` | 新增（由旧文件改名） | 参考实现 / fallback |
| Python CLI | `scripts/flow.py` | 新增 | argparse 入口 |
| Python modules | `scripts/dev_flow/commands/*.py`, `scripts/dev_flow/domain/**/*.py`, `scripts/dev_flow/infra/*.py` | 新增 | 新实现 |
| Legacy Bash source | `lib/*.sh`, `scripts/cmd/*.sh` | 保留 | 迁移期参考与 fallback 依赖 |
| Templates | `templates/` → `assets/templates/` | 移动 | 符合 skill 规范 |
| Legacy tests | `tests/run-tests.sh`, `tests/unit/*.sh`, `tests/integration/*.sh`, `tests/lib/*`, `tests/fixtures/*` | 保留 | 旧实现回归基线 |
| Python tests | `tests/python/unit/*.py`, `tests/python/integration/*.py`, `tests/python/support/*.py` | 新增 | 新实现 TDD 契约 |
| Legacy mapping | `tests/python/COVERAGE.md` | 新增 | Bash 测试到 Python 测试的映射矩阵 |

## Implementation

### TDD 原则

1. **旧回归先绿**：先确认 `bash tests/run-tests.sh` 通过，冻结现状
2. **新测试先红**：每个 Python 行为切片，先补 `unittest`，先看到红
3. **单切片转绿**：只实现当前切片所需最小代码
4. **双保险**：每个切片结束后同时跑 Python 新测试 + Bash 旧回归
5. **不删 legacy**：本期只 cutover，不删除 Bash 参考实现

---

### Phase 0：冻结 legacy 基线并搭好 hybrid 骨架

**Goal**：先让迁移起点可控，而不是直接写一套无法执行的 Python 测试大网。

---

### Task 0-1: 重命名旧入口并建立稳定 wrapper

**Files**: `scripts/flow.sh`, `scripts/flow-legacy.sh`

**Changes**:
- [x] Step 1: 将当前 Bash `scripts/flow.sh` 改名为 `scripts/flow-legacy.sh`
- [x] Step 2: 新建兼容 `scripts/flow.sh`，初始阶段 100% 转发到 `flow-legacy.sh`
- [x] Step 3: 保持现有 `SKILL.md` 中所有 `flow.sh` 用法不变

**Verification**:
- [x] Step 1: `bash scripts/flow.sh help` 输出与改名前一致
- [x] Step 2: `bash scripts/flow-legacy.sh help` 可独立执行

---

### Task 0-2: 跑绿 legacy Bash 回归并冻结基线

**Files**: `tests/run-tests.sh`, `tests/unit/*.sh`, `tests/integration/*.sh`

**Changes**:
- [x] Step 1: 执行当前 Bash 回归，确认现状可作为迁移基线
- [x] Step 2: 若存在非预期失败，先修正基线或明确记录已知失败原因
- [x] Step 3: 记录当前通过的测试集合与关键覆盖点

**Verification**:
- [x] Step 1: `bash tests/run-tests.sh` 通过
- [x] Step 2: 基线结果已记录，可作为后续回归 oracle

---

### Task 0-3: 建立 stdlib-only Python 骨架

**Files**: `scripts/flow.py`, `scripts/dev_flow/**`, `tests/python/support/**`

**Changes**:
- [x] Step 1: 创建 `scripts/flow.py`（基于 `argparse`）
- [x] Step 2: 创建 `scripts/dev_flow/commands/`, `domain/`, `infra/` 目录骨架
- [x] Step 3: 创建 `tests/python/support/` 公共测试辅助模块
- [x] Step 4: 明确不创建 `requirements.txt`、`pyproject.toml`、venv 相关文件

**Verification**:
- [x] Step 1: `python3 scripts/flow.py --help` 可执行
- [x] Step 2: `python3 -m unittest discover tests/python` 可执行（允许 0 tests）

---

### Task 0-4: 建立 Bash → Python 测试覆盖矩阵

**Files**: `tests/python/COVERAGE.md`

**Changes**:
- [x] Step 1: 为 17 个现有 Bash 测试建立行为映射
- [x] Step 2: 标注每个行为属于哪个 Python 迁移切片
- [x] Step 3: 标注哪些是 legacy-only 回归，哪些必须被 Python 新测试接管

**Verification**:
- [x] Step 1: 覆盖矩阵包含全部现有 Bash 测试
- [x] Step 2: 每个公开命令行为都能定位到后续 Python 测试归属

---

### Phase 1：迁移纯规则切片（title / naming / labels）

**Goal**：先迁移纯函数规则，建立第一批真正的 Python TDD 闭环。

---

### Task 1-1: 为 title / naming / labels 写 Python 红测试

**Files**: `tests/python/unit/test_issue_title.py`, `test_plan_naming.py`, `test_type_labels.py`

**Changes**:
- [x] Step 1: 依据现有 Bash fixture 与 case，编写 Python `unittest` 用例
- [x] Step 2: 先对未实现的 Python 模块运行测试，确认红灯
- [x] Step 3: 保留 Bash 同名测试不动，作为 legacy oracle

**Verification**:
- [x] Step 1: `python3 -m unittest tests.python.unit.test_issue_title` 初次运行失败
- [x] Step 2: `python3 -m unittest tests.python.unit.test_plan_naming` 初次运行失败
- [x] Step 3: `python3 -m unittest tests.python.unit.test_type_labels` 初次运行失败

---

### Task 1-2: 实现 title / naming / labels Python 模块

**Files**: `scripts/dev_flow/domain/issue/title.py`, `scripts/dev_flow/domain/plan/naming.py`, `scripts/dev_flow/domain/labels.py`

**Changes**:
- [x] Step 1: 实现 `extract_scope`, `extract_type`, `validate_issue_title`
- [x] Step 2: 实现 `validate_plan_name`, `make_plan_name`
- [x] Step 3: 实现 `normalize_plan_type`, `plan_type_to_issue_label`, `issue_label_to_plan_type`

**Verification**:
- [x] Step 1: `python3 -m unittest tests.python.unit.test_issue_title` 转绿
- [x] Step 2: `python3 -m unittest tests.python.unit.test_plan_naming` 转绿
- [x] Step 3: `python3 -m unittest tests.python.unit.test_type_labels` 转绿
- [x] Step 4: `bash tests/run-tests.sh` 仍通过

---

### Phase 2：迁移文档与渲染切片（validation / issue body / plan link）

**Goal**：接管 Plan 校验、Issue body 渲染、Plan link 等核心内容逻辑。

---

### Task 2-1: 为 validation / renderer / plan link 写 Python 红测试

**Files**: `tests/python/unit/test_check_doc.py`, `test_user_validation.py`, `test_plan_link_contract.py`, `tests/python/integration/test_issue_contract.py`, `test_archive_plan_link.py`

**Changes**:
- [x] Step 1: 迁移现有 Bash fixtures 到 Python `unittest` 场景
- [x] Step 2: 先运行新测试，确认 Python 侧仍为红灯
- [x] Step 3: 对命令级集成测试预留 `FLOW_BIN` 环境变量，后续可分别指向 `flow-legacy.sh` 与 `flow.sh`

**Verification**:
- [x] Step 1: `python3 -m unittest tests.python.unit.test_check_doc` 初次运行失败
- [x] Step 2: `python3 -m unittest tests.python.unit.test_user_validation` 初次运行失败
- [x] Step 3: `python3 -m unittest tests.python.integration.test_issue_contract` 初次运行失败

---

### Task 2-2: 实现 validation / renderer / plan link Python 模块

**Files**: `scripts/dev_flow/domain/validation.py`, `scripts/dev_flow/domain/issue/body.py`, `scripts/dev_flow/domain/issue/link.py`, `scripts/dev_flow/domain/plan/find.py`

**Changes**:
- [x] Step 1: 实现 `check_doc_plan` 与 `check_user_validation`
- [x] Step 2: 实现 `build_structured_issue_body`
- [x] Step 3: 实现 `build_repo_blob_url`, `update_issue_plan_link`, `find_plan_by_issue`

**Verification**:
- [x] Step 1: `python3 -m unittest tests.python.unit.test_check_doc` 转绿
- [x] Step 2: `python3 -m unittest tests.python.unit.test_user_validation` 转绿
- [x] Step 3: `python3 -m unittest tests.python.unit.test_plan_link_contract` 转绿
- [x] Step 4: `python3 -m unittest tests.python.integration.test_issue_contract` 转绿
- [x] Step 5: `python3 -m unittest tests.python.integration.test_archive_plan_link` 转绿
- [x] Step 6: `bash tests/run-tests.sh` 仍通过

---

### Phase 3：迁移命令面切片（help / issue create / issue update / query / sync）

**Goal**：开始让 `flow.sh` 对部分公开命令切到 Python，同时保留未迁移命令的 legacy fallback。

---

### Task 3-1: 为公开命令建立双入口兼容测试

**Files**: `tests/python/integration/test_command_surface.py`, `test_issue_create_command.py`, `test_issue_update_command.py`, `test_related_resources_links.py`

**Changes**:
- [x] Step 1: 让命令级 Python 集成测试支持 `FLOW_BIN` 环境变量
- [x] Step 2: 先用 `FLOW_BIN=scripts/flow-legacy.sh` 跑绿，确认测试正确表达 legacy 行为
- [x] Step 3: 再用 `FLOW_BIN=scripts/flow.sh` 跑，确认在切换前对 Python 路由是红灯或未实现

**Verification**:
- [x] Step 1: `FLOW_BIN=scripts/flow-legacy.sh python3 -m unittest tests.python.integration.test_command_surface` 通过
- [x] Step 2: `FLOW_BIN=scripts/flow-legacy.sh python3 -m unittest tests.python.integration.test_issue_create_command` 通过
- [x] Step 3: `FLOW_BIN=scripts/flow-legacy.sh python3 -m unittest tests.python.integration.test_issue_update_command` 通过

---

### Task 3-2: 实现 issue / query / sync Python 命令并接入 hybrid wrapper

**Files**: `scripts/dev_flow/commands/issue.py`, `query.py`, `sync.py`, `scripts/flow.py`, `scripts/flow.sh`

**Changes**:
- [x] Step 1: 实现 `issue create`, `issue update`
- [x] Step 2: 实现 `help`, `status`, `list`, `sync`
- [x] Step 3: 在 `scripts/flow.sh` 中将这些命令路由到 Python
- [x] Step 4: 未迁移命令仍回退到 `flow-legacy.sh`

**Verification**:
- [x] Step 1: `FLOW_BIN=scripts/flow.sh python3 -m unittest tests.python.integration.test_command_surface` 转绿
- [x] Step 2: `FLOW_BIN=scripts/flow.sh python3 -m unittest tests.python.integration.test_issue_create_command` 转绿
- [x] Step 3: `FLOW_BIN=scripts/flow.sh python3 -m unittest tests.python.integration.test_issue_update_command` 转绿
- [x] Step 4: `bash tests/run-tests.sh` 仍通过

---

### Phase 4：迁移 workflow 切片（plan / approve / complete / verify / archive）

**Goal**：接管状态机命令，并把新增 archive repo gate 作为新行为通过 TDD 落地。

---

### Task 4-1: 先为 archive 项目 repo gate 写失败测试

**Files**: `tests/python/integration/test_archive_project_repo_gate.py`

**Changes**:
- [x] Step 1: 为"Target Project repo 有未提交变更时 archive 必须阻断"编写新测试
- [x] Step 2: 先对当前 Python 实现运行，确认红灯
- [x] Step 3: 明确此测试是新增行为，不要求 legacy Bash 通过

**Verification**:
- [x] Step 1: `python3 -m unittest tests.python.integration.test_archive_project_repo_gate` 初次运行失败

---

### Task 4-2: 实现 plan / workflow / archive Python 命令

**Files**: `scripts/dev_flow/commands/plan.py`, `approve.py`, `complete.py`, `verify.py`, `archive.py`, `scripts/dev_flow/domain/workflow.py`, `scripts/dev_flow/infra/git.py`

**Changes**:
- [x] Step 1: 实现 `plan`（仅 issue 模式）, `approve`（仅 --confirm，缺 --worktree/check-doc/stash）, `complete`（仅状态转换，缺 --pr/acceptance gate/issue sync）, `verify`（仅状态转换，缺 --confirm gate/PR check/user_validation/issue sync）, `archive`（仅基础流程，缺 sync before archive/project warning）
- [x] Step 2: 实现 workflow 状态转换规则
- [x] Step 3: 实现 archive 前 Target Project repo dirty gate
- [x] Step 4: 补齐 `plan` no-issue 模式（--title/--project/--type/--scope）、--check/--deep/--prd
- [x] Step 5: 补齐 `approve` --worktree、check-doc 验证、stash 处理、Issue sync、Plan name lookup
- [x] Step 6: 补齐 `complete` --pr、acceptance_criteria gate、Issue sync（label + body）
- [x] Step 7: 补齐 `verify` --confirm gate、PR merged check、user_validation gate、Issue sync
- [x] Step 8: 补齐 `archive` sync before archive、project uncommitted changes warning
- [x] Step 9: 将剩余公开命令全部切到 Python（确认所有功能完整后）

**Verification**:
- [x] Step 1: `python3 -m unittest tests.python.integration.test_archive_project_repo_gate` 转绿
- [x] Step 2: `FLOW_BIN=scripts/flow.sh python3 -m unittest discover tests/python/integration` 通过
- [x] Step 3: `bash tests/run-tests.sh` 仍通过
- [x] Step 4: Bash vs Python 功能对比完整一致

---

### Phase 5：全量切换、保留 legacy 参考、完成回归

**Goal**：完成 cutover，但不删除 legacy Bash，实现“可运行的新实现 + 可参考的旧实现”。

---

### Task 5-1: 完成 full Python cutover 并保留 legacy 参考

**Files**: `scripts/flow.sh`, `scripts/flow-legacy.sh`, `lib/*.sh`, `scripts/cmd/*.sh`

**Changes**:
- [x] Step 1: 补齐 Phase 4 Task 4-2 所有遗漏功能（plan no-issue/approve --worktree/complete --pr/verify gates/archive sync）
- [x] Step 2: 确认 `scripts/flow.sh` 所有命令走 Python 且功能完整（不依赖 legacy fallback）
- [x] Step 3: 保留 `scripts/flow-legacy.sh` 作为参考实现
- [x] Step 4: 保留 `lib/*.sh` 与 `scripts/cmd/*.sh` 作为迁移参考，不在本期删除

**Verification**:
- [x] Step 1: Bash vs Python 功能对比完全一致（无遗漏）
- [x] Step 2: `bash scripts/flow.sh help` 走 Python 实现
- [x] Step 3: `bash scripts/flow-legacy.sh help` 仍可独立运行作参考

---

### Task 5-2: 执行最终双回归

**Changes**:
- [x] Step 1: 跑全量 Python `unittest` 回归
- [x] Step 2: 跑 legacy Bash 回归，确保参考实现未被迁移过程破坏
- [x] Step 3: 执行真实命令链路 smoke test

**Verification**:
- [x] Step 1: `python3 -m unittest discover tests/python` 全部通过（111 tests）
- [x] Step 2: `bash tests/run-tests.sh` 全部通过（6 tests）
- [x] Step 3: `bash scripts/flow.sh query status 121` 正常执行（worktree 环境限制 gh CLI）

## Delegation Strategy

| Phase | Task | 执行者 | 依赖 |
|---|---|---|---|
| Phase 0 | Task 0-1 / 0-2 / 0-4 | Wopal | 无 |
| Phase 0 | Task 0-3 | fae | Task 0-1 |
| Phase 1 | Task 1-1 / 1-2 | fae | Phase 0 |
| Phase 2 | Task 2-1 / 2-2 | fae | Phase 1 |
| Phase 3 | Task 3-1 / 3-2 | fae | Phase 2 |
| Phase 4 | Task 4-1 / 4-2 | fae | Phase 3 |
| Phase 5 | Task 5-1 | Wopal | Phase 4 |
| Phase 5 | Task 5-2 | Wopal | Task 5-1 |

**原则**：
- Wopal 负责定义 TDD 切片与验收门
- fae 执行具体迁移，但每次只做一个切片
- Wopal 必须亲自验证 wrapper 行为与最终回归

### Task 4-2 委派批次（当前 Phase）

根据功能差异矩阵和强依赖分析，分 5 批推进：

| Batch | Task | 内容 | 估计步骤 | 验证 |
|-------|------|------|----------|------|
| **Batch 1** | Step 4 | plan 命令补齐：no-issue 模式、--check、--deep/--prd | ~15 | Wopal 跑测试 |
| **Batch 2** | Step 5 | approve 命令补齐：--worktree、check-doc、stash、Issue sync | ~20 | Wopal 跑测试 |
| **Batch 3** | Step 6+7 | complete + verify 补齐：--pr、gates、Issue sync（强依赖） | ~25 | Wopal 跑测试 |
| **Batch 4** | Step 8 | archive 补齐：sync before archive、project warning | ~10 | Wopal 跑测试 |
| **Batch 5** | Step 9 | 全切到 Python | ~5 | Wopal 验证 |

**强依赖说明**：
- Batch 3 的 complete 和 verify 有强依赖：complete 的 PR path 与 verify 的 PR merged check 关联，必须整体委派
- 每批完成后 Wopal 验证，再发下一批

**当前状态**：准备启动 Batch 1

## Test Plan

##### Case P0-1：legacy 基线冻结
- Goal: 当前 Bash 行为被可靠冻结
- Fixture: 现有 Bash 测试套件
- Execution:
  - [x] Step 1: 执行 `bash tests/run-tests.sh`
  - [x] Step 2: 执行 `bash scripts/flow.sh help`
- Expected Evidence: 旧测试全绿，公共入口未变化 ✅

##### Case P1-1：纯规则切片遵循红 → 绿
- Goal: title / naming / labels 切片按 TDD 成功迁移
- Fixture: Python `unittest`
- Execution:
  - [x] Step 1: 先执行 `python3 -m unittest tests.python.unit.test_issue_title`
  - [x] Step 2: 实现后再次执行同命令
  - [x] Step 3: 执行 `bash tests/run-tests.sh`
- Expected Evidence: 先红后绿，且 legacy 回归仍绿 ✅

##### Case P2-1：命令兼容测试可同时验证 legacy 与新入口
- Goal: 同一命令测试可跑 `flow-legacy.sh` 与 `flow.sh`
- Fixture: `FLOW_BIN` 参数化集成测试
- Execution:
  - [x] Step 1: `FLOW_BIN=scripts/flow-legacy.sh python3 -m unittest tests.python.integration.test_command_surface`
  - [x] Step 2: `FLOW_BIN=scripts/flow.sh python3 -m unittest tests.python.integration.test_command_surface`
- Expected Evidence: legacy 先绿，切换完成后新入口也绿 ✅

##### Case P4-1：archive repo gate 遵循新行为 TDD
- Goal: 新增 archive repo dirty gate 通过失败测试先行落地
- Fixture: 目标项目 repo 脏状态 fixture
- Execution:
  - [x] Step 1: 先执行 `python3 -m unittest tests.python.integration.test_archive_project_repo_gate`
  - [x] Step 2: 实现 gate 后再次执行
- Expected Evidence: 先红后绿，且阻断信息明确 ✅

##### Case P4-2：plan no-issue 模式
- Goal: 无 Issue 也可创建 Plan
- Fixture: --title/--project/--type/--scope 参数组合
- Execution:
  - [x] Step 1: `python3 flow.py plan --title "test(scope): desc" --project ontology --type feature`
  - [x] Step 2: 验证 Plan 文件创建在正确目录
- Expected Evidence: Plan 创建成功，命名规范正确 ✅

##### Case P4-3：approve 完整功能
- Goal: approve 命令所有补齐功能正确工作
- Fixture: Plan 文件 + Issue mock
- Execution:
  - [x] Step 1: `python3 flow.py approve --help` 显示 --worktree 参数
  - [x] Step 2: check_doc 验证集成到 approve 流程
  - [x] Step 3: Plan name lookup（无 Issue 模式）正确路由
- Expected Evidence: 参数齐全，验证门正确阻断 ✅

##### Case P4-4：complete 完整功能
- Goal: complete 命令所有补齐功能正确工作
- Fixture: Plan 文件 + Issue mock
- Execution:
  - [x] Step 1: `python3 flow.py complete --help` 显示 --pr 参数
  - [x] Step 2: acceptance_criteria gate 检查 Agent Verification checkbox
  - [x] Step 3: Issue sync 状态转换后执行
- Expected Evidence: 参数齐全，gate 正确阻断未完成 AC ✅

##### Case P4-5：verify 完整功能
- Goal: verify 命令所有补齐功能正确工作
- Fixture: Plan 文件 + Issue mock
- Execution:
  - [x] Step 1: `python3 flow.py verify --help` 显示 --confirm 参数
  - [x] Step 2: PR merged check 从 Plan metadata 或 Issue body 获取 PR URL
  - [x] Step 3: user_validation gate 检查最终 checkbox
  - [x] Step 4: Issue sync + 关闭 Issue
- Expected Evidence: 参数齐全，gate 正确阻断未验证状态 ✅

##### Case P4-6：archive 完整功能
- Goal: archive 命令所有补齐功能正确工作
- Fixture: Plan 文件 + Issue mock + project repo
- Execution:
  - [x] Step 1: sync before archive（body + labels）执行
  - [x] Step 2: project uncommitted changes 显示 WARNING（非阻断）
- Expected Evidence: sync 正确执行，warning 提示用户确认 ✅

##### Case P4-7：新增命令功能
- Goal: decompose-prd 和 reset 命令正确实现
- Fixture: PRD 文件 + Plan 文件
- Execution:
  - [x] Step 1: `python3 flow.py decompose-prd --help` 显示参数
  - [x] Step 2: `python3 flow.py reset --help` 显示参数
  - [x] Step 3: status/list 顶层别名路由正确
- Expected Evidence: 新命令可用，别名路由正确 ✅

##### Case P5-1：全量 Python 回归通过
- Goal: 新实现具备完整可运行性
- Fixture: Python 测试套件
- Execution:
  - [x] Step 1: 执行 `python3 -m unittest discover tests/python`
- Expected Evidence: 全部通过（111 tests）✅

##### Case P5-2：legacy 参考回归未被破坏
- Goal: 迁移过程中旧实现仍可以作为参考 oracle
- Fixture: 现有 Bash 测试套件
- Execution:
  - [x] Step 1: 执行 `bash tests/run-tests.sh`
- Expected Evidence: 全部通过 ✅

## Acceptance Criteria

### Agent Verification

- [x] `scripts/flow.sh` 保持稳定公共入口
- [x] 旧 Bash 入口已改名为 `scripts/flow-legacy.sh` 并保留
- [x] 未引入 `requirements.txt`、`pyproject.toml`、venv 或第三方 Python 包
- [x] 已建立 `tests/python/COVERAGE.md`，覆盖全部现有 Bash 测试行为映射
- [x] 每个 Python 迁移切片都按"红 → 绿 → 旧回归绿"完成
- [x] `python3 -m unittest discover tests/python` 通过（111 tests）
- [x] `bash tests/run-tests.sh` 通过（6 tests）
- [x] archive 项目 repo dirty gate 已通过失败测试先行落地

### User Validation

#### Scenario 1：命令名完全不变
- Goal: 用户仍只使用 `flow.sh`
- Precondition: wrapper 已切换为 Python 实现
- User Actions:
  1. 执行 `flow.sh help`
  2. 执行 `flow.sh status 121`
- Expected Result: 命令名与使用方式不变

#### Scenario 2：旧 Bash 入口保留作参考
- Goal: legacy 代码未被抹掉
- Precondition: 迁移已完成
- User Actions:
  1. 查看 `scripts/flow-legacy.sh`
  2. 确认其仍可作为参考实现存在
- Expected Result: 旧入口保留，便于对照与回退分析

#### Scenario 3：archive 新 gate 行为正确
- Goal: 项目 repo 未提交时归档被阻断
- Precondition: Target Project repo 存在未提交变更
- User Actions:
  1. 执行 `flow.sh archive <issue>`
  2. 提交项目 repo 后再次执行
- Expected Result: 第一次阻断，第二次放行

#### Scenario 4：完整流程可继续执行
- Goal: planning → executing → verifying → done 流程不被迁移破坏
- Precondition: 选择一个测试 Issue
- User Actions:
  1. 执行 `flow.sh plan <issue>`
  2. 执行 `flow.sh approve <issue>`
  3. 在授权后执行后续命令链
- Expected Result: 状态推进符合 dev-flow 既有约定

- [x] 用户已完成上述功能验证并确认结果符合预期
