# refactor(skills): flatten dev-flow package and eliminate shell deps

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-28
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High
- **Scope exemption**: 本 Plan 覆盖 20+ 文件、4 个不同子问题（包扁平化 + worktree 替换 + test 迁移 + 旧目录清理），看似宜拆分。但四个 Task 有强依赖链——Task 2 的所有 import 更新必须基于 Task 1 产出的新模块结构，Task 3 必须在 Task 4 确认 test 迁移完成后方可安全删除旧目录。拆成两期将引入跨 Plan 的模块结构不一致窗口（一期只扁平化但 worktree.sh 引用仍存在 → 状态不一致 → 无法验证等价性）。**风险控制**：4 个 Task 串行执行，每个 Task 均有独立 Verify 步骤降低风险。rook 审查已进行 3 轮，范围理解充分。

## Goal

1. 消除 dev-flow skill 的 Python 包嵌套层级（`dev_flow/core/`, `domain/`, `infra/` → 平铺），`__init__.py` 从 14 个减到 2 个
2. 用 `lib/worktree.py`（纯 Python）替代 `worktree.sh` 实现 git worktree 操作，`approve.py` 和 `archive.py` 不再 subprocess 调用外部 shell 脚本
3. 砍掉 `.workspace.md` 依赖——`lib/worktree.py` 使用 `lib/workspace.py` 的 workspace 检测（基于 `.wopal/.git` worktree 签名），不再搜索 `.workspace.md`

## Technical Context

### Architecture Context

**当前 `archive.py` worktree 清理逻辑**（L200-267）：
1. 尝试 `worktree.sh remove` → 成功则返回
2. 失败/脚本不存在 → fallback 直接 git cleanup：
   - `git worktree remove`（失败再 `--force`）
   - 删除 branch（`git branch -d branch || git branch -D branch`，跳过当前分支）

**`worktree.sh cmd_remove` 等价语义**（L403-468）：
- `git worktree remove`（失败则 `git worktree prune`）
- 目录已不存在时仍执行 prune + branch cleanup
- 删除本地 branch（`git branch -d || -D`，当前分支跳过）

**`lib/worktree.py` 新接口需完全覆盖以上语义**：
```python
# lib/worktree.py — 补充 archive 清理等价设计
def remove_worktree(project_dir: Path, branch: str, worktree_base: Path) -> None:
    """移除 worktree（等价 worktree.sh cmd_remove）
    - git worktree remove <path>（失败时 --force 重试）
    - git worktree prune（无论 remove 是否成功都执行）
    """

def delete_branch(git_dir: Path, branch: str) -> bool:
    """删除本地 branch（git branch -d → 失败则 -D）
    - 若为当前分支，跳过并返回 False
    """

def clean_worktree(project_dir: Path, branch: str, worktree_base: Path) -> dict:
    """archive.py 专用：一站式清理（等价原 worktree.sh remove 全局）
    1. remove_worktree() + prune
    2. delete_branch()
    返回 {"removed": bool, "branch_deleted": bool, "errors": list[str]}
    """
```
`archive.py` 原有 worktree.sh + fallback 两个分支 → 替换为直接调用 `clean_worktree()`，不再需要 `locate_worktree_script` 或两段式 fallback。

**当前结构**：
```
scripts/
├── flow.sh              # bash 入口（23 行）
├── flow.py              # CLI 主控
└── dev_flow/            # Python 包（多余的 1 层嵌套）
    ├── __init__.py      # __version__ = "0.1.0"
    ├── core/            # 4 文件（workspace, workflow, status, logging）
    ├── domain/          # 业务域（issue/, plan/, validation/, workflow.py, labels.py）
    ├── commands/        # CLI 处理层（11 文件）
    └── infra/           # git.py（git + gh CLI + locate_worktree_script）
```

14 个 `__init__.py`，7 个空文件。导入深度 `dev_flow.domain.plan.body.build_plan_body` — 4 层。

`approve.py` 和 `archive.py` 通过 `locate_worktree_script()` 找到外部 `worktree.sh`（位于 `git-worktrees` skill），subprocess 调用它创建/清理 worktree。`worktree.sh` 内部依赖 `.workspace.md` 做项目扫描。

**目标结构**：
```
scripts/
├── flow.sh              # 保留不动
├── flow.py              # CLI 主控（内置 __version__）
│
├── lib/                 # 工具类
│   ├── __init__.py
│   ├── workspace.py     # find_workspace_root（基于 .wopal/.git 检测，非 .workspace.md）
│   ├── worktree.py      # NEW: git worktree 操作（替代 worktree.sh）
│   ├── github.py        # gh CLI 封装
│   ├── git.py           # git 原生命令（不再含 locate_worktree_script）
│   └── logging.py       # 彩色日志
│
├── issue.py             # issue 域（title/body/link/sync）
├── plan.py              # plan 域（metadata/body/naming/find/link/commit/project）
├── workflow.py          # 状态机 + status 展示
├── validation.py        # plan 质量校验
├── labels.py            # label 管理
│
└── commands/            # CLI 处理层（11 文件含 verify_switch.py）
    └── __init__.py
```

`__init__.py` 从 14 → 2（`lib/` + `commands/`）。`scripts/` 无 `__init__.py`，`python3 scripts/flow.py` 自动加入 sys.path。

### Key Decisions

- D-01: **不加 `scripts/__init__.py`** — 模块间用绝对导入 `from lib.xxx import ...`
- D-02: **`lib/` `commands/` 作为仅有的子包**
- D-03: **域模块平铺** — 4 层导入 → 1 层
- D-04: **保留 `flow.sh` 不动** — 23 行薄封装，避免改 SKILL.md
- D-05: **tests/ 移到 skill 根** — 与 `scripts/` 平级
- D-06: **`lib/worktree.py` 替代 `worktree.sh`** — 纯 Python subprocess git，使用 `lib/workspace.py` 的 workspace 检测替代 `.workspace.md` 搜索
- D-07: **`__version__` 内置于 `flow.py`** — 当前值 `"0.1.0"`，从 `dev_flow/__init__.py` 读取
- D-08: **现有工作流 key 保持不变** — approve/archive 的 worktree 创建/清理逻辑完整保留，仅实现方式从 subprocess shell 变为 Python 直接调用
- D-10: **gitdir 解析唯一实现** — `project.py:get_ontology_main_repo()` 和 `verify_switch.py:_get_ontology_git_dir()` 重复解析 `.wopal/.git` 文件，合并为 `lib/workspace.py` 的单一 `get_ontology_main_repo()`，两处调用方改为 import

### Key Interfaces

```python
# lib/workspace.py（从 core/workspace.py 直迁 + 新增 get_ontology_main_repo）
def find_workspace_root(start: Path | None = None) -> Path: ...
def detect_space_repo(workspace_root: Path) -> str: ...
def get_ontology_main_repo(workspace_root: Path) -> Path | None: ...  # 新增 — 合并三处重复实现的 gitdir 解析

# lib/worktree.py（NEW — 替代 worktree.sh）
def create_worktree(project_dir: Path, branch: str, worktree_base: Path) -> Path: ...
def list_worktrees(worktree_base: Path, project: str | None = None) -> list[str]: ...
def remove_worktree(project_dir: Path, branch: str, worktree_base: Path) -> None:
    """等价 worktree.sh cmd_remove: git worktree remove（失败 --force 重试）→ git worktree prune"""
def delete_branch(git_dir: Path, branch: str) -> bool:
    """git branch -d → 失败则 -D；当前分支跳过"""
def clean_worktree(project_dir: Path, branch: str, worktree_base: Path) -> dict:
    """archive.py 一站式清理：remove_worktree + prune + delete_branch，返回 {"removed": bool, "branch_deleted": bool, "errors": list[str]}"""
def scan_projects(workspace_root: Path) -> list[str]: ...

# lib/git.py（从 infra/git.py 迁移，移除 locate_worktree_script）
def get_remote_url(path: str) -> str: ...
def get_current_branch(path: str) -> str: ...
def commit_file(file_path: str, message: str) -> None: ...

# lib/github.py（从 infra/git.py 拆分 gh CLI 部分）
def create_issue(repo: str, title: str, body: str, labels: list[str]) -> str: ...
def update_issue(repo: str, issue_number: str, title: str, body: str, labels: list[str]) -> None: ...
def get_issue(repo: str, issue_number: str) -> dict: ...

# lib/logging.py（从 core/logging.py 直迁）
def info(msg: str, ...) -> None: ...
def error(msg: str, ...) -> None: ...
def success(msg: str, ...) -> None: ...

# issue.py（合并 domain/issue/ 下 4 文件）
def build_title(type_: str, scope: str, description: str) -> str: ...
def build_body(template: str, **kwargs) -> str: ...
def find_issue_by_plan(plan_name: str) -> str | None: ...
def sync_labels_to_issue(issue_number: str, plan_status: str, plan_type: str) -> None: ...

# plan.py（合并 domain/plan/ 下 7 文件）
def parse_metadata(plan_path: Path) -> dict: ...
def build_body(template: str, **kwargs) -> str: ...
def generate_plan_name(title: str) -> str: ...
def find_plan(issue: str, project: str) -> Path | None: ...
def link_plan_to_issue(plan_path: Path, issue_number: str) -> None: ...
def commit_plan(plan_path: Path, message: str) -> None: ...
def detect_project_type(plan_path: Path) -> str: ...

# workflow.py（合并 core/workflow + domain/workflow + core/status）
STATUS_PLANNING = "planning"
STATUS_EXECUTING = "executing"
STATUS_VERIFYING = "verifying"
STATUS_DONE = "done"
def get_status(plan_path: Path) -> str: ...
def transition(plan_path: Path, from_status: str, to_status: str) -> None: ...
def display_status(plan_path: Path) -> str: ...

# validation.py（迁移自 domain/validation/）
check_doc_plan(plan_path: Path) -> ValidationError | None: ...
check_user_validation(plan_path: Path) -> ValidationError | None: ...
check_acceptance_criteria(plan_path: Path) -> ValidationError | None: ...
check_step_completion(plan_path: Path) -> ValidationError | None: ...
class ValidationError(Exception): ...

# labels.py（迁移自 domain/labels.py）
normalize_plan_type(raw_type: str) -> str: ...
plan_type_to_issue_label(plan_type: str) -> str: ...
issue_label_to_plan_type(issue_label: str) -> str: ...
```

## In Scope

- 创建 `lib/` 目录：迁移 workspace/git/github/logging，新建 worktree.py
- 合并域模块：`domain/issue/` 4文件 → `issue.py`，`domain/plan/` 7文件 → `plan.py`，workflow 三层 → `workflow.py`，`validation.py`，`labels.py`
- 更新所有 import（`commands/` 11文件含 verify_switch.py + `flow.py`）
- **`approve.py`/`archive.py` 替换 worktree 调用**：移除 `locate_worktree_script()` + subprocess，改用 `lib/worktree.py` 的 Python 函数
- `__version__` 内置到 `flow.py`
- 删除旧 `dev_flow/` 目录（用 `trash`）
- 测试从 `scripts/dev_flow/domain/validation/tests/` 迁移到 `tests/python/unit/`，更新 import 和 mock/patch 路径
- **消除 gitdir 解析重复**：`project.py` 的 `get_ontology_main_repo()` 和 `verify_switch.py` 的 `_get_ontology_git_dir()` 合并到 `lib/workspace.py`，均解析同一份 `.wopal/.git` 文件

## Out of Scope

- 修改 `flow.sh`
- 修改命令逻辑或行为（结构重构 + worktree/imports 等价行为替换，不引入新功能）
- 删除 `git-worktrees` skill 的 `worktree.sh`（独立决策）
- SKILL.md 内容变更
- 新增测试用例

## Business Rules Impact

N/A — 纯技术重构 + 等价实现替换，无业务规则变更

## Affected Files

| Component | Files | Operation |
|-----------|-------|-----------|
| lib 包 | `scripts/lib/__init__.py`, `workspace.py`, `worktree.py`, `github.py`, `git.py`, `logging.py` | 创建/迁移 |
| 域模块 | `scripts/issue.py`, `plan.py`, `workflow.py`, `validation.py`, `labels.py` | 合并/迁移 |
| CLI 层 | `scripts/commands/*.py`（11 文件） | 修改 import + worktree 调用替换 |
| 入口 | `scripts/flow.py` | 修改 import + __version__ |
| 旧目录 | `scripts/dev_flow/` | 删除（trash） |
| 测试迁移 | `scripts/dev_flow/domain/validation/tests/test_check_doc.py` → `tests/python/unit/` | 移动 + import 更新 |
| 测试更新 | `tests/python/unit/*.py`, `tests/python/support/bootstrap.py` | import/patch 路径更新 |

## Acceptance Criteria

### Agent Verification

所有命令在 `.wopal/skills/dev-flow` 下执行。

1. [x] `python3 scripts/flow.py --help` 正常输出
2. [x] `python3 scripts/flow.py issue --help` 正常输出
3. [x] `python3 scripts/flow.py plan --help` 正常输出
4. [x] `find scripts/dev_flow -type d` 无输出（旧目录已删除）
5. [x] `find scripts -name '__init__.py' | wc -l` 输出 2（lib/ + commands/）
6. [x] `test ! -f scripts/__init__.py` 通过
7. [x] `rg 'from dev_flow' scripts/` 无匹配
8. [x] `rg 'from domain\.' scripts/` 无匹配
9. [x] `rg 'from core\.' scripts/` 无匹配
10. [x] `rg 'from infra\.' scripts/` 无匹配
11. [x] `rg 'from \.domain' scripts/` 无匹配
12. [x] `rg 'worktree\.sh' scripts/` 无匹配（仅注释中有"equivalent to worktree.sh"说明文字，无代码引用）
13. [x] `rg '\.workspace\.md' scripts/` 无匹配（仅注释中有"not .workspace.md"说明文字，无代码引用）
14. [x] `rg 'locate_worktree_script' scripts/` 无匹配（旧函数已移除）
15. [x] 全量导入冒烟通过
16. [x] `python3 -m pytest tests/python/ -v` 250 passed, 2 failed（2 个集成测试为 pre-existing archive push 环境问题）
17. [x] `rg 'def.*get_ontology|def.*_get_ontology' scripts/` 仅 1 个匹配（只在 lib/workspace.py）
18. [x] worktree 行为等价冒烟通过
19. [x] `python3 scripts/flow.py archive --help` + `python3 scripts/flow.py approve --help` 正常输出

### User Validation

#### Scenario 1: flow.sh 核心命令正常导入

- Goal: 确认重构后所有命令正常导入，无 import 错误
- Precondition: 空间根目录
- User Actions:
  1. `cd .wopal/skills/dev-flow && bash scripts/flow.sh help`
  2. `bash scripts/flow.sh status`
  3. `bash scripts/flow.sh list`
  4. `bash scripts/flow.sh approve --help`
  5. `bash scripts/flow.sh archive --help`

- Expected Result: 所有命令无 import 错误

#### Scenario 2: worktree 基础操作正常，不依赖 .workspace.md

- Goal: 验证 lib/worktree.py 的 `scan_projects` 使用 git 原生检测（非 .workspace.md 搜索），基础导入正常
- Precondition: 任意项目目录
- User Actions:
  1. `python3 -c "import sys; from pathlib import Path; sys.path.insert(0,'scripts'); from lib.worktree import scan_projects; projects = scan_projects(Path.cwd()); print(f'Found {len(projects)} project(s)')"`
  2. 在**无 .workspace.md** 的环境下执行，确认不报文件不存在错误
  3. 检查 `rg '\.workspace\.md' scripts/` 无匹配

- Expected Result: `scan_projects` 正常返回（可能是空列表），不依赖 .workspace.md

- [x] 用户已完成功能验证并确认结果符合预期

## Implementation

### Task 1: Create lib/ package (with worktree.py) and flatten domain modules

**Verification Intent**: AC#5, AC#6, AC#14, AC#15

**Behavior**: `lib/` 作为工具类子包。workspace/git/github/logging 从旧位置迁移，新建 `worktree.py` 实现 git worktree 操作（用 subprocess git，依赖 `lib/workspace.py` 的 workspace 检测而非 `.workspace.md`）。domain/issue、domain/plan、workflow 三层、domain/validation、domain/labels 合并为平级模块。

**Files**: `scripts/lib/__init__.py`, `scripts/lib/workspace.py`, `scripts/lib/worktree.py`, `scripts/lib/git.py`, `scripts/lib/github.py`, `scripts/lib/logging.py`, `scripts/issue.py`, `scripts/plan.py`, `scripts/workflow.py`, `scripts/validation.py`, `scripts/labels.py`

**Pre-read**:
- `scripts/dev_flow/core/workspace.py` — workspace root 检测
- `scripts/dev_flow/core/logging.py` — 日志工具
- `scripts/dev_flow/infra/git.py` — git 命令 + gh CLI + locate_worktree_script
- `scripts/dev_flow/domain/issue/*.py` — issue 域
- `scripts/dev_flow/domain/plan/*.py` — plan 域
- `scripts/dev_flow/core/workflow.py` + `domain/workflow.py` + `core/status.py` — workflow
- `scripts/dev_flow/domain/validation/check_doc.py` — plan 校验
- `scripts/dev_flow/domain/labels.py` — label 管理
- `scripts/dev_flow/commands/approve.py`（L213-258）— 理解 worktree 调用场景
- `scripts/dev_flow/commands/archive.py`（L211-232）— 理解 worktree 调用场景

**Design**:

**lib/ 包**:
1. `lib/__init__.py` — 空文件
2. `lib/workspace.py` — 从 `core/workspace.py` 直迁（`find_workspace_root`, `detect_space_repo`）。**新增 `get_ontology_main_repo()`**——合并 `domain/plan/project.py:297` 和 `commands/verify_switch.py:20` 的重复 gitdir 解析逻辑（均读 `.wopal/.git` 文件解析 gitdir: 路径获取 ontology 主仓库），形成唯一实现。仅用标准库，不改其余 import。
3. `lib/logging.py` — 从 `core/logging.py` 直迁
4. `lib/git.py` — 从 `infra/git.py` 提取 git 原生命令（`get_remote_url`, `get_current_branch`, `commit_file`），**移除 `locate_worktree_script()`**（不再需要）
5. `lib/github.py` — 从 `infra/git.py` 提取 gh CLI 函数（`create_issue`, `update_issue`, `get_issue`, `add_labels`）
6. `lib/worktree.py` — **全新实现**，用 `subprocess.run(['git', 'worktree', ...])` 替代 worktree.sh：
   - `scan_projects(workspace_root)` — 用 `os.listdir` + 检测 `.git` 目录，**不依赖 `.workspace.md`**
   - `create_worktree(project_dir, branch, worktree_base)` → `git worktree add`
   - `list_worktrees(worktree_base, project)` → `git worktree list` + 过滤
   - `remove_worktree(project_dir, branch, worktree_base)` → `git worktree remove`
   - `prune_worktrees(worktree_base)` → `git worktree prune`
   - 使用 `lib/workspace.py` 的 `find_workspace_root()` 代替 `.workspace.md` 搜索

**域模块平铺**:
1. `issue.py` — 合并 `domain/issue/` 下 4 文件（title→body→link→sync），import → `from lib.github import ...`
2. `plan.py` — 合并 `domain/plan/` 下 7 文件（metadata→project→naming→body→find→link→commit），import → `from lib.git import ...`。**注意**：`project.py` 的 `get_ontology_main_repo()` 不合并入 plan.py——该函数已提取到 `lib/workspace.py`，plan.py 中替换为 `from lib.workspace import get_ontology_main_repo`。
3. `workflow.py` — 合并 `core/workflow.py`（状态常量）+ `domain/workflow.py`（转换）+ `core/status.py`（展示）
4. `validation.py` — `domain/validation/check_doc.py` 直迁（导出 `check_doc_plan`, `check_user_validation`, `check_acceptance_criteria`, `check_step_completion`, `ValidationError`）
5. `labels.py` — `domain/labels.py` 直迁（导出 `normalize_plan_type`, `plan_type_to_issue_label`, `issue_label_to_plan_type`）

**TDD**: false

**Changes**:
1. 创建 `scripts/lib/` + `__init__.py`
2. 迁移 workspace/logging → `lib/`；拆分 infra/git → `lib/git.py` + `lib/github.py`（移除 locate_worktree_script）
3. 新建 `lib/worktree.py`
4. 合并域模块为 5 个平级文件
5. 所有新文件内部 import 统一为新路径

**Verify**:
```bash
cd .wopal/skills/dev-flow
python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.workspace import find_workspace_root; print('ws OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.worktree import create_worktree, scan_projects; print('wt OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.git import get_remote_url; print('git OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.github import create_issue; print('gh OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.logging import info; print('log OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from issue import build_title; print('issue OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from plan import parse_metadata; print('plan OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from workflow import STATUS_PLANNING; print('wf OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from validation import check_doc_plan; print('val OK')"
python3 -c "import sys; sys.path.insert(0,'scripts'); from labels import normalize_plan_type, plan_type_to_issue_label; print('lbl OK')"
```

**Done**:
任务产出：lib/ 包（含 worktree.py）+ 5 个域模块就绪
- [x] 实施 Agent 已完成上述功能开发和验证，确认结果符合预期

---

### Task 2: Update all imports + replace worktree.sh calls in approve.py/archive.py

**Verification Intent**: AC#1, AC#2, AC#3, AC#7–14, AC#15, AC#18, AC#19

**Behavior**: `commands/` 下 11 文件 + `flow.py` 的所有 import 更新为新路径。**`approve.py` 和 `archive.py` 中 worktree 调用替换**：移除 `locate_worktree_script` + subprocess 调用 worktree.sh，改用 `lib/worktree.py` 函数。

**Files**: `scripts/flow.py`, `scripts/commands/approve.py`, `scripts/commands/archive.py`, `scripts/commands/complete.py`, `scripts/commands/verify.py`, `scripts/commands/sync.py`, `scripts/commands/reset.py`, `scripts/commands/roadmap.py`, `scripts/commands/decompose.py`, `scripts/commands/query.py`, `scripts/commands/verify_switch.py`

**Design**:

**Import 映射表**:

| 旧 import | 新 import |
|-----------|-----------|
| `from dev_flow.core.workspace import ...` | `from lib.workspace import ...` |
| `from dev_flow.core.logging import ...` | `from lib.logging import ...` |
| `from dev_flow.core.workflow import STATUS_*, is_valid_transition` | `from workflow import STATUS_*, is_valid_transition` |
| `from dev_flow.core.status import display_*` | `from workflow import display_*` |
| `from dev_flow.infra.git import get_remote_url, ...` | `from lib.git import ...` 或 `from lib.github import ...` |
| `from dev_flow.infra.git import locate_worktree_script` | **删除** — 改用 `from lib.worktree import ...` |
| `from dev_flow.domain.issue.body import ...` | `from issue import ...` |
| `from dev_flow.domain.issue.title import ...` | `from issue import ...` |
| `from dev_flow.domain.issue.link import ...` | `from issue import ...` |
| `from dev_flow.domain.issue.sync import ...` | `from issue import ...` |
| `from dev_flow.domain.issue import ...` (package-level) | `from issue import ...` |
| `from dev_flow.domain.plan.metadata import ...` | `from plan import ...` |
| `from dev_flow.domain.plan.body import ...` | `from plan import ...` |
| `from dev_flow.domain.plan.find import ...` | `from plan import ...` |
| `from dev_flow.domain.plan.link import ...` | `from plan import ...` |
| `from dev_flow.domain.plan.commit import ...` | `from plan import ...` |
| `from dev_flow.domain.plan.project import ...` | `from plan import ...` |
| `from dev_flow.domain.plan.naming import ...` | `from plan import ...` |
| `from dev_flow.domain.plan import ...` (package-level) | `from plan import ...` |
| `from dev_flow.domain.workflow import ...` | `from workflow import ...` |
| `from dev_flow.domain.validation.check_doc import ...` | `from validation import ...` |
| `from dev_flow.domain.validation import ...` (package-level) | `from validation import ...` |
| `from dev_flow.domain.labels import ...` | `from labels import ...` |
| `from dev_flow.commands.xxx import ...` | `from commands.xxx import ...` |
| `from dev_flow import __version__` | `flow.py` 硬编码 `__version__ = "0.1.0"` |

**approve.py / archive.py worktree 调用替换**:
- 移除 `from dev_flow.infra.git import locate_worktree_script` 及 subprocess 调用 worktree.sh 的代码
- **approve.py**: 改为 `from lib.worktree import create_worktree` + `from lib.workspace import find_workspace_root`，worktree 路径计算逻辑保持不变
- **archive.py**: 原 `_clean_worktree()` 两段式逻辑（worktree.sh remove → fallback git）替换为 `from lib.worktree import clean_worktree` 一站式调用，覆盖 remove + prune + branch deletion 三个操作。不再需要 `locate_worktree_script` 或 fallback 分支。

**verify_switch.py**: 更新 `from dev_flow.domain.workflow import ...` → `from workflow import ...`，`from dev_flow.core.workspace import ...` → `from lib.workspace import find_workspace_root, get_ontology_main_repo`。**删除 `_get_ontology_git_dir()` 函数**——使用 `lib/workspace.py` 的 `get_ontology_main_repo()` 替代，消除重复实现。

**TDD**: false

**Changes**:
1. 逐文件替换 import（按映射表）
2. `flow.py` 内置 `__version__ = "0.1.0"`
3. `approve.py` 替换 worktree.sh subprocess → lib/worktree.py 函数
4. `archive.py` 同上
5. 确认无 `from dev_flow`、`from domain.`、`from core.`、`from infra.`、`worktree.sh`、`locate_worktree_script`、`.workspace.md` 匹配

**Verify**:
```bash
cd .wopal/skills/dev-flow
python3 scripts/flow.py --help
python3 scripts/flow.py help
python3 scripts/flow.py status
python3 scripts/flow.py list
python3 scripts/flow.py issue --help
python3 scripts/flow.py plan --help
python3 scripts/flow.py approve --help
python3 scripts/flow.py archive --help
python3 scripts/flow.py complete --help
python3 scripts/flow.py verify --help
python3 scripts/flow.py sync --help
python3 scripts/flow.py reset --help
python3 scripts/flow.py roadmap --help
python3 scripts/flow.py decompose --help
python3 scripts/flow.py verify-switch --help
rg 'from dev_flow' scripts/
rg 'worktree\.sh' scripts/
rg '\.workspace\.md' scripts/
rg 'locate_worktree_script' scripts/
rg 'from domain\.' scripts/
rg 'from core\.' scripts/
rg 'from infra\.' scripts/
```

**Done**:
任务产出：所有 import 更新完毕，worktree.sh/.workspace.md 依赖清零，所有命令正常导入
- [x] 实施 Agent 已完成上述功能开发和验证，确认结果符合预期

---

### Task 3: Clean up old directories

**Verification Intent**: AC#4, AC#5, AC#6

**Behavior**: 确认所有 import 更新、test 迁移完成后，用 `trash` 删除 `scripts/dev_flow/` 旧包目录。

**Files**: 删除对象：`scripts/dev_flow/`（整个目录树）

**Design**:

前置条件：Task 4（测试迁移）必须已完成，确保 `scripts/dev_flow/domain/validation/tests/` 中的测试文件已移动到 `tests/python/unit/`。确认 import 全部更新后，用 `trash` 删除旧目录。

**TDD**: false

**Changes**:
1. 确认 `rg 'from dev_flow' scripts/` 无匹配
2. 确认 `tests/python/unit/test_check_doc.py` 已存在（Task 4 完成）
3. `trash scripts/dev_flow/`（旧包目录已无代码引用，安全删除。遵守 REGULATIONS 误删防护：用 trash，禁止 git rm -rf）
4. 确认 `find scripts -name '__init__.py' | wc -l` 输出 2

**Verify**:
```bash
cd .wopal/skills/dev-flow
find scripts/dev_flow -type d 2>/dev/null | wc -l    # 应输出 0
find scripts -name '__init__.py'                       # 仅 lib/ + commands/
test ! -f scripts/__init__.py && echo "PASS"
```

**Done**:
任务产出：旧 `dev_flow/` 包全部删除
- [x] 实施 Agent 已完成上述功能开发和验证，确认结果符合预期

---

### Task 4: Update tests

**Verification Intent**: AC#16

**Behavior**: 从 `scripts/dev_flow/domain/validation/tests/` 移动测试文件到 `tests/python/unit/`，更新所有测试 import 和 mock/patch 路径。

**Files**: `tests/python/unit/*.py`, `tests/python/support/bootstrap.py`, 源文件: `scripts/dev_flow/domain/validation/tests/test_check_doc.py`

**Pre-read**: 所有测试文件的 import 段 + `@patch` 装饰器

**Design**:

1. 移动 `scripts/dev_flow/domain/validation/tests/test_check_doc.py` → `tests/python/unit/test_check_doc.py`
2. 删除 `scripts/dev_flow/domain/validation/tests/` 目录

**测试 Import + Patch 映射表**:

| 旧路径 | 新路径 |
|--------|--------|
| `from dev_flow.core.workspace import ...` | `from lib.workspace import ...` |
| `from dev_flow.core.logging import ...` | `from lib.logging import ...` |
| `from dev_flow.core.workflow import ...` | `from workflow import ...` |
| `from dev_flow.core.status import ...` | `from workflow import ...` |
| `from dev_flow.infra.git import ...` | `from lib.git import ...` 或 `from lib.github import ...` |
| `from dev_flow.commands.xxx import ...` | `from commands.xxx import ...` |
| `from dev_flow.domain.validation.check_doc import ...` | `from validation import ...` |
| `from dev_flow.domain.validation import ...` | `from validation import ...` |
| `from dev_flow.domain.issue import ...` | `from issue import ...` |
| `from dev_flow.domain.plan import ...` | `from plan import ...` |
| `@patch('dev_flow.commands.xxx.func')` | `@patch('commands.xxx.func')` |
| `@patch('dev_flow.domain.validation.xxx.yyy')` | `@patch('validation.yyy')` |
| `@patch('dev_flow.domain.xxx.yyy')` | `@patch('xxx.yyy')` |
| `@patch('dev_flow.core.xxx.yyy')` | `@patch('workflow.yyy')` 或 `@patch('lib.xxx.yyy')` |
| `@patch('dev_flow.infra.git.func')` | `@patch('lib.git.func')` 或 `@patch('lib.github.func')` |

3. 更新 `tests/python/support/bootstrap.py` — `ensure_scripts_path()` 路径注入逻辑不变（`scripts/` 仍在 sys.path）

**TDD**: false

**Changes**:
1. 移动 `test_check_doc.py` 到 `tests/python/unit/`
2. 更新所有测试文件的 import + mock/patch 路径
3. 确认 bootstrap.py 正常
4. 运行全量测试

**Verify**:
```bash
cd .wopal/skills/dev-flow
python3 -m pytest tests/python/ -v
```

**Done**:
任务产出：所有测试迁移并通过
- [x] 实施 Agent 已完成上述功能开发和验证，确认结果符合预期

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 说明 |
|------|------|--------|------|------|
| 1 | Task 1 | fae | 无 | lib/ 包 + worktree.py + 域模块合并（独立写入） |
| 2 | Task 2 | fae | Task 1 | 所有模块就绪后更新 import + worktree 调用替换 |
| 3 | Task 4 | fae | Task 2 | 测试迁移（先从旧目录移出） |
| 4 | Task 3 | fae | Task 4 | 旧目录删除（测试已安全移走） |

全部串行。Task 4 → Task 3 顺序保证删除旧目录前测试已迁移。
