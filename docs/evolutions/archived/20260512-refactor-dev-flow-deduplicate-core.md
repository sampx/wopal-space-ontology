# refactor-dev-flow-deduplicate-core

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space
- **Created**: 2026-05-12
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

去重 dev-flow 核心基础设施：workspace root 检测、space repo 检测、logging、Plan 状态更新。消除跨 command/domain 文件的重复基础函数，统一异常处理和错误信息风格。

## Technical Context

**现状问题**：

1. **重复函数**：`_get_space_repo()` / `get_space_repo()` / `_resolve_repo()` / `_update_plan_status()` / `_find_workspace_root()` 分散在 command 与 domain 层，后续修复容易漏改
2. **logging 重复**：多个 command 文件各自定义 `log_info` / `log_success` / `log_error` / `log_warn` / `log_step`
3. **repo 检测缺陷**：repo 检测依赖 `gh repo view`，在 fork worktree（`.wopal/`）中可能返回当前 worktree repo，而不是空间主仓库 `sampx/wopal-space`
4. **workspace root 检测不稳固**：现有逻辑用 `os.getcwd()` + `.wopal/` / `.git` 向上查找，`projects/gesp/.wopal` 会造成误判
5. **异常处理不一致**：有的 raise `RuntimeError`，有的 return `""`，有的 `log_error` 后 return `1`

**已有基础设施**：`infra/git.py` 已有 `get_remote_url(repo_path)`，可复用为 `detect_space_repo()` 的底层 Git 调用。

## In Scope

- 新建 `core/` 模块：`workspace.py`、`logging.py`、`status.py`
- `find_workspace_root()` 使用空间 `.wopal` worktree 特征定位 workspace root
- `detect_space_repo()` 使用 workspace root 的 `git remote get-url origin` 解析 `owner/repo`
- 删除 command 层重复 logging / repo / status / workspace 函数，改为 core 导入
- 删除 domain 层重复 workspace / repo 解析函数，改为 core 或显式参数
- `domain/issue/sync.py` 的 public sync 函数改为要求调用方显式传入 repo
- 修复 archive 幂等性：已在 `done/` 下的 Plan 不再移动到 `done/done/`
- 为 core 函数和 archive 幂等性补充 focused unit tests

## Out of Scope

- 命令行为变更（不改变任何命令的输入/输出/流程）
- domain 层业务重构（find、metadata、naming、issue body 生成等保持现有结构）
- GitHub Issue body/label 同步语义调整
- archive 自动提交/推送策略调整

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| core workspace | `.wopal/skills/dev-flow/scripts/dev_flow/core/workspace.py` | 新建 | workspace root + space repo 检测 |
| core logging | `.wopal/skills/dev-flow/scripts/dev_flow/core/logging.py` | 新建 | 统一日志函数 |
| core status | `.wopal/skills/dev-flow/scripts/dev_flow/core/status.py` | 新建 | Plan 状态更新 |
| core init | `.wopal/skills/dev-flow/scripts/dev_flow/core/__init__.py` | 新建 | core 模块导出 |
| plan find | `.wopal/skills/dev-flow/scripts/dev_flow/domain/plan/find.py` | 修改 | 删除 `_find_workspace_root`，改为从 core 导入 |
| plan link | `.wopal/skills/dev-flow/scripts/dev_flow/domain/plan/link.py` | 修改 | 删除重复 workspace/repo 解析，复用 core 或显式参数 |
| issue sync | `.wopal/skills/dev-flow/scripts/dev_flow/domain/issue/sync.py` | 修改 | 删除 `_resolve_repo`，repo 改为必选参数 |
| approve | `.wopal/skills/dev-flow/scripts/dev_flow/commands/approve.py` | 修改 | 删除重复基础函数 |
| archive | `.wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py` | 修改 | 删除重复基础函数 + 幂等修复 |
| complete | `.wopal/skills/dev-flow/scripts/dev_flow/commands/complete.py` | 修改 | 删除重复基础函数 |
| decompose | `.wopal/skills/dev-flow/scripts/dev_flow/commands/decompose.py` | 修改 | 删除重复基础函数 |
| issue | `.wopal/skills/dev-flow/scripts/dev_flow/commands/issue.py` | 修改 | 删除重复基础函数 |
| plan | `.wopal/skills/dev-flow/scripts/dev_flow/commands/plan.py` | 修改 | 删除重复基础函数 |
| query | `.wopal/skills/dev-flow/scripts/dev_flow/commands/query.py` | 修改 | 删除重复基础函数 |
| reset | `.wopal/skills/dev-flow/scripts/dev_flow/commands/reset.py` | 修改 | 删除重复基础函数 |
| sync | `.wopal/skills/dev-flow/scripts/dev_flow/commands/sync.py` | 修改 | 删除重复基础函数 |
| verify | `.wopal/skills/dev-flow/scripts/dev_flow/commands/verify.py` | 修改 | 删除重复基础函数 |
| unit tests | `.wopal/skills/dev-flow/tests/python/unit/test_core_workspace.py`, `.wopal/skills/dev-flow/tests/python/unit/test_core_status.py` | 新建 | core 行为测试 |
| integration tests | `.wopal/skills/dev-flow/tests/python/integration/test_archive_idempotent.py` | 新建 | archive 幂等性测试 |

## Implementation

### Task 1: 新建 `core/logging.py`

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/core/logging.py`

**Changes**:

- [x] Step 1: 创建 `dev_flow/core/` package 和 `__init__.py`
- [x] Step 2: 将统一日志函数实现放入 `core/logging.py`
- [x] Step 3: 保持 `log_error(msg: str, file=None)` 兼容 complete/verify 现有调用

**Verification**:

- [x] Step 1: 执行 `python3 -c "from dev_flow.core.logging import log_info, log_success, log_error, log_warn, log_step"`
- [x] Step 2: 确认导入命令返回码为 0

### Task 2: 新建 `core/workspace.py`

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/core/workspace.py`

**Changes**:

- [x] Step 1: 实现 `find_workspace_root(start: Path | None = None) -> Path`
- [x] Step 2: 使用空间根目录下 `.wopal/.git` 是 `gitdir:` worktree 文件作为 workspace root 判定条件
- [x] Step 3: 实现 `detect_space_repo(workspace_root: Path) -> str`
- [x] Step 4: 复用 `infra.git.get_remote_url()` 获取 workspace root 的 origin URL
- [x] Step 5: 支持 `https://github.com/owner/repo(.git)` 与 `git@github.com:owner/repo(.git)` 两种 URL 解析
- [x] Step 6: repo 无法解析时抛出带上下文的 `RuntimeError`

**Verification**:

- [x] Step 1: 从 `.wopal/skills/dev-flow/scripts` 执行测试，`find_workspace_root()` 返回空间根
- [x] Step 2: 从 `projects/gesp/` 执行测试，`find_workspace_root()` 返回空间根，不误判 `projects/gesp/.wopal`
- [x] Step 3: `detect_space_repo(find_workspace_root())` 返回 `sampx/wopal-space`

### Task 3: 新建 `core/status.py`

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/core/status.py`

**Changes**:

- [x] Step 1: 实现 `update_plan_status(plan_path: str | Path, new_status: str) -> bool`
- [x] Step 2: 复用现有 Status 行替换语义，只更新首个 `- **Status**:` 行
- [x] Step 3: 文件不存在或 Status 行缺失时返回 `False`，不吞掉无关异常

**Verification**:

- [x] Step 1: 执行 `python3 -c "from dev_flow.core.status import update_plan_status"`
- [x] Step 2: 确认导入命令返回码为 0

### Task 4: 修改 plan domain

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/domain/plan/find.py`, `.wopal/skills/dev-flow/scripts/dev_flow/domain/plan/link.py`

**Changes**:

- [x] Step 1: `find.py` 删除本地 `_find_workspace_root()`，改为导入 `find_workspace_root`
- [x] Step 2: `find.py` 中所有 `_find_workspace_root()` 调用改为 `find_workspace_root()`

**Verification**:

- [x] Step 1: 执行 `python3 -c "from dev_flow.domain.plan.find import find_plan"`
- [x] Step 2: 执行 `python3 -c "from dev_flow.domain.plan.link import update_issue_plan_link"`
- [x] Step 3: 确认两个导入命令返回码均为 0

### Task 5: 修改 issue sync domain

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/domain/issue/sync.py`

**Changes**:

- [x] Step 1: 删除 `_resolve_repo()` 函数
- [x] Step 2: `sync_status_label()` 的 `repo` 参数改为必选
- [x] Step 3: `sync_plan_to_issue_body()` 的 `repo` 参数改为必选
- [x] Step 4: `ensure_issue_labels()` 的 `repo` 参数改为必选
- [x] Step 5: 保持 repo 为空时的失败行为清晰，不再静默 fallback 到 `gh repo view`

**Verification**:

- [x] Step 1: 执行 `python3 -c "from dev_flow.domain.issue.sync import sync_status_label, sync_plan_to_issue_body, ensure_issue_labels"`
- [x] Step 2: 确认三个 public sync 函数签名中 `repo` 无默认 `None`

### Task 6: 更新所有 command 文件

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/commands/approve.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/complete.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/decompose.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/issue.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/plan.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/query.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/reset.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/sync.py`, `.wopal/skills/dev-flow/scripts/dev_flow/commands/verify.py`

**Changes**:

- [x] Step 1: 删除 command 文件中的本地 `log_*` 函数定义
- [x] Step 2: 删除 command 文件中的本地 `_get_space_repo()` / `get_space_repo()` / `_resolve_repo()` 函数定义
- [x] Step 3: 删除 command 文件中的本地 `_update_plan_status()` 函数定义
- [x] Step 4: 将 workspace root 获取改为导入并调用 `find_workspace_root()`
- [x] Step 5: 将 space repo 获取改为导入并调用 `detect_space_repo(workspace_root)`
- [x] Step 6: 将 Plan 状态更新改为导入并调用 `update_plan_status()`
- [x] Step 7: 修正 `sync_status_label()` / `sync_plan_to_issue_body()` / `ensure_issue_labels()` 调用点，全部显式传入 repo

**Verification**:

- [x] Step 1: 执行重复定义扫描，确认 `commands/` 中无本地基础函数定义残留
- [x] Step 2: 执行 `python3 -m compileall scripts/dev_flow`，确认无语法错误和导入循环

### Task 7: 修复 archive 幂等性

**Files**: `.wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py`

**Changes**:

- [x] Step 1: 在 `archive_plan_file()` 开头检查 `plan_file.parent.name == "done"`
- [x] Step 2: 已归档 Plan 直接返回当前路径，不创建 `done/done/`
- [x] Step 3: 保持未归档 Plan 的 `git mv` / `Path.rename()` 行为不变

**Verification**:

- [x] Step 1: 对 `done/` 下的 Plan fixture 调用 `archive_plan_file()`
- [x] Step 2: 确认返回原路径且不存在 `done/done/`

## Delegation Strategy

使用异步 `wopal_task` 委派给 fae 小批次串行实施。每批只覆盖可独立验证的文件集合，Wopal 在每批完成后运行扫描/compile/import 验证，再决定下一批。

| 批次 | Task | 执行者 | 依赖 | 策略 |
|------|------|--------|------|------|
| 1 | Task 1-5 | fae + Wopal verification | 无 | 已完成 core/domain 基础设施，Wopal 已验证并勾选 |
| 2 | Task 6 command cleanup A | fae | Task 1-5 | 仅处理 `plan.py`、`query.py`、`reset.py`、`sync.py`、`issue.py`、`decompose.py` 的重复基础函数和调用点 |
| 3 | Task 6 command cleanup B + Task 7 | fae | 批次 2 | 仅处理 `complete.py`、`verify.py`、`archive.py` 剩余调用与 archive 幂等性 |
| 4 | Tests + final verification | Wopal / fae as needed | 批次 2-3 | 补测试，运行 compileall、重复定义扫描、flow.sh smoke tests |

**委派理由**：

- 前一次整包委派导致 Fae 上下文超过 55%，重定向响应变差；后续必须小批次推进
- command 文件替换具有重复性，适合 fae，但必须限制文件集合和完成标准
- Wopal 保留每批 diff 审查、重复定义扫描、compileall、真实空间命令 smoke test、Plan checkbox 核对职责

**推荐委派 prompt**：

```markdown
## Plan
读取 Plan 文件，按 Implementation 执行：docs/products/wopal-space/plans/refactor-dev-flow-deduplicate-core.md

## 特别注意
- 目标代码在 `.wopal/skills/dev-flow/scripts/dev_flow/` 和 `.wopal/skills/dev-flow/tests/python/`
- 所有路径必须使用空间根目录相对路径或绝对路径，不要使用裸 `.planning/` 等相对输出路径
- 不要修改 `external/`、`.agents/`、`.env`、`AGENTS.md`、`USER.md`、`MEMORY.md`
- 不要提交、不 push；只完成代码、测试和 Plan checkbox 更新
- 若发现 Plan 与代码现状冲突，先在任务报告中说明，不要扩大重构范围

## 完成标准
- Implementation 与 Test Plan 中已实际完成的 Step checkbox 已勾选
- Agent Verification 中可由 fae 验证的项目已勾选
- core workspace/status 单元测试通过
- archive 幂等性测试通过
- `python3 -m compileall scripts/dev_flow` 通过
- `flow.sh list` 和 `flow.sh status <plan>` smoke test 通过

## Task Report
完成时输出：Goal / Accomplished / Files / Verification / Risks
```

**Wopal 验证职责**：

- 检查 fae 修改的所有文件，确认没有把基础函数复制回 command/domain 层
- 复跑 Plan 中的关键验证命令
- 检查 `git status`，确认没有无关文件被改动
- 若产出不达标，通过 `wopal_reply` 要求 fae 继续修复，而不是另开新任务

## Test Plan

#### Unit Tests

##### Case U1: workspace root 检测
- Goal: 验证 `find_workspace_root()` 不被子项目 `.wopal/` 误导
- Fixture: 在 `.tmp/` 或临时目录构造 workspace root，其中根 `.wopal/.git` 为 `gitdir:` 文件，子项目包含普通 `.wopal/` 目录
- Execution:
  - [x] Step 1: 从 workspace root、`.wopal/skills/dev-flow/scripts`、`projects/gesp` 三个起点调用 `find_workspace_root(start=...)`
  - [x] Step 2: 确认三次返回同一个 workspace root
- Expected Evidence: 单元测试断言通过，返回路径均为 fixture workspace root

##### Case U2: space repo URL 解析
- Goal: 验证 `detect_space_repo()` 能解析常见 origin URL
- Fixture: mock `get_remote_url()` 返回 `https://github.com/sampx/wopal-space.git`、`git@github.com:sampx/wopal-space.git`、无效 URL
- Execution:
  - [x] Step 1: 对 https 和 ssh URL 分别调用 `detect_space_repo()`
  - [x] Step 2: 对无效 URL 调用 `detect_space_repo()` 并捕获异常
- Expected Evidence: 有效 URL 返回 `sampx/wopal-space`，无效 URL 抛出 `RuntimeError`

##### Case U3: Plan 状态更新
- Goal: 验证 `update_plan_status()` 只更新 Metadata 中首个 Status 行
- Fixture: 临时 Plan 文件，包含 `- **Status**: planning`
- Execution:
  - [x] Step 1: 调用 `update_plan_status(plan, "executing")`
  - [x] Step 2: 读取文件确认 Status 行变为 `executing`
- Expected Evidence: 函数返回 `True`，文件内容只发生预期替换

##### Case U4: archive 已归档 Plan 幂等
- Goal: 验证 `archive_plan_file()` 对 `done/` 下文件不会二次移动
- Fixture: 临时 workspace 中创建 `docs/products/wopal-space/plans/done/20260512-demo.md`
- Execution:
  - [x] Step 1: 调用 `archive_plan_file()` 并记录返回路径
  - [x] Step 2: 检查 filesystem 中没有 `done/done/`
- Expected Evidence: 返回路径等于输入路径，`done/done/` 不存在

#### Integration Tests

##### Case I1: workspace root 检测准确性
- Goal: 验证真实空间中 `find_workspace_root()` 从各目录执行均返回正确根目录
- Fixture: 当前空间目录结构，根 `.wopal/` 为 worktree，`projects/gesp/.wopal` 为子项目目录
- Execution:
  - [x] Step 1: 从空间根目录执行，返回 `/Users/sam/coding/wopal/wopal-workspace`
  - [x] Step 2: 从 `.wopal/skills/dev-flow/scripts/` 执行，返回相同路径
  - [x] Step 3: 从 `projects/gesp/` 执行，返回相同路径
- Expected Evidence: 三个输出路径一致

##### Case I2: space repo 检测准确性
- Goal: 验证真实空间中 `detect_space_repo()` 返回空间主仓库
- Fixture: workspace root 的 `origin` remote
- Execution:
  - [x] Step 1: 调用 `detect_space_repo(find_workspace_root())`
  - [x] Step 2: 确认返回值
- Expected Evidence: 返回 `sampx/wopal-space`

##### Case I3: command 端到端 smoke
- Goal: 确认重构后常用 `flow.sh` 命令正常运行
- Fixture: 当前空间已有 Plan 文件
- Execution:
  - [x] Step 1: 执行 `flow.sh list`
  - [x] Step 2: 执行 `flow.sh status <plan>`
- Expected Evidence: 两个命令返回码为 0，输出与重构前语义一致

#### Regression Tests

##### Case R1: 无重复基础函数定义
- Goal: 确认 command/domain 层重复基础函数已清除
- Fixture: dev-flow 代码库
- Execution:
  - [x] Step 1: 执行 `rg -n "def (_?get_space_repo|get_space_repo|_resolve_repo|_update_plan_status|_find_workspace_root|log_info|log_success|log_error|log_warn|log_step)" scripts/dev_flow`
  - [x] Step 2: 确认匹配仅出现在 `core/` 中，或属于非基础业务函数且有明确保留理由
- Expected Evidence: commands/ 与 domain/ 中无重复基础函数定义残留

##### Case R2: Python 模块可编译
- Goal: 确认 core 引入后没有语法错误和明显循环导入
- Fixture: dev-flow Python scripts
- Execution:
  - [x] Step 1: 执行 `python3 -m compileall scripts/dev_flow`
  - [x] Step 2: 确认命令返回码为 0
- Expected Evidence: compileall 通过

### Adjustment Strategy

若出现循环依赖，优先调整依赖方向：`core` 只依赖 stdlib 与 `infra/`，`domain/` 和 `commands/` 依赖 `core`。不得把 workspace/repo/status 基础函数重新复制回 command/domain 层。

## Acceptance Criteria

### Agent Verification

- [x] `core/` 模块包含 `workspace.py`、`logging.py`、`status.py`
- [x] command/domain 层无重复 workspace/repo/status/logging 基础函数定义
- [x] `find_workspace_root()` 从 `.wopal/`、`projects/` 子目录执行均返回空间根
- [x] `detect_space_repo()` 返回 `sampx/wopal-space`
- [x] `domain/issue/sync.py` public sync 函数要求显式 repo 参数
- [x] archive 幂等：已归档 Plan 不产生 `done/done/`
- [x] core workspace/status 单元测试通过
- [x] archive 幂等性测试通过
- [x] `python3 -m compileall scripts/dev_flow` 通过
- [x] `flow.sh list` 和 `flow.sh status` 正常运行

### User Validation

#### Scenario 1: 日常 dev-flow 流程稳定性
- Goal: 确认重构不影响常用 Plan 查询与归档流程
- Precondition: 有一个 status=done 的 Plan
- User Actions:
  1. 执行 `flow.sh list`
  2. 执行 `flow.sh status <plan>`
  3. 执行 `flow.sh archive <plan>`
- Expected Result: 所有命令输出正常，Issue 操作成功，已归档 Plan 不会再次产生 `done/done/`

- [x] 用户已完成上述功能验证并确认结果符合预期
