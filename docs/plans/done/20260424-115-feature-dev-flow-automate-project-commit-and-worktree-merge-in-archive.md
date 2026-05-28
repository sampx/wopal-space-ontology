# 115-feature-dev-flow-automate-project-commit-and-worktree-merge-in-archive

## Metadata

- **Issue**: #115
- **Type**: feature
- **Target Project**: ontology
- **Created**: 2026-04-24
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

archive 归档时自动提交项目仓库变更，无 PR 路径下自动合并 worktree 分支到 main 并清理 worktree，同时删除已完成 Python 迁移的历史遗留 Bash 脚本。

## Technical Context

### 当前架构

dev-flow 技能已完成 Python 迁移（Phase 5）：`flow.sh` 路由到 `flow.py`，Python 实现在 `scripts/dev_flow/` 下。但存在两类遗留问题：

1. **功能缺陷**：`archive.py` 只检测项目仓库未提交变更并打印提示，不自动提交；完全不感知 worktree。
2. **代码冗余**：`scripts/cmd/*.sh`（10 个 Bash 命令脚本）、`scripts/flow-legacy.sh`、`lib/*.sh`（8 个 Bash 库）仍保留在源码中，但 Python 层已完全独立运行，不依赖任何 Bash 代码。`flow.sh` 引用 `flow-legacy.sh` 仅作为 fallback（实际永远不会走到）。

### 遗留脚本依赖关系

`flow.sh` 当前逻辑：
```
if CMD in PYTHON_COMMANDS: exec python3 flow.py
else: exec flow-legacy.sh
```
所有正式命令（issue/plan/approve/complete/verify/archive/sync/query/status/list/reset/decompose-prd）都在 `PYTHON_COMMANDS` 中，`flow-legacy.sh` 只处理未知命令——而未知命令本就该报错。

Bash 测试（`tests/integration/*.sh`、`tests/unit/*.sh`、`tests/lib/*.sh`）依赖 `lib/*.sh`，需一并清理。

## In Scope

- `commands/archive.py`：增加 worktree 感知 + 项目仓库自动提交 + 分支合并逻辑
- `commands/approve.py`：`--confirm --worktree` 时写入 Plan `Worktree` 字段（分支名+路径）
- `domain/plan/metadata.py`：新增 Worktree 字段存取 helper
- `infra/git.py`：新增 `merge_branch`、`branch_exists`、`delete_branch` 等 git 操作
- 删除所有遗留 Bash 脚本：`scripts/cmd/*.sh`（10 个）、`scripts/flow-legacy.sh`、`lib/*.sh`（8 个）
- 删除遗留 Bash 测试：`tests/integration/*.sh`、`tests/unit/*.sh`、`tests/lib/*.sh`、`tests/run-tests.sh`
- 简化 `flow.sh` 入口：移除 `flow-legacy.sh` 引用，未知命令直接报错
- 更新 SKILL.md 中遗留的 Bash 脚本执行方式说明

## Out of Scope

- PR 路径合并逻辑（已由 PR mechanism 处理）
- Worktree 创建逻辑（已有 git-worktrees 技能）
- 合并冲突自动解决（冲突时阻断 + 提示手动处理）
- `lib/check-doc.sh` 的 Python 迁移（已有 `domain/validation/check_doc.py`，Bash 版仅被遗留测试引用）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| archive 命令 | `scripts/dev_flow/commands/archive.py` | 修改 | 核心变更：worktree 感知 + 自动提交 + 合并 |
| approve 命令 | `scripts/dev_flow/commands/approve.py` | 修改 | 写入 Worktree 字段到 Plan |
| Plan 元数据 | `scripts/dev_flow/domain/plan/metadata.py` | 修改 | 新增 get/set Worktree helper |
| Git 操作 | `scripts/dev_flow/infra/git.py` | 修改 | 新增 merge/branch 操作函数 |
| 入口脚本 | `scripts/flow.sh` | 修改 | 移除 legacy fallback，简化路由 |
| 技能文档 | `SKILL.md` | 修改 | 移除 Bash 脚本执行说明 |
| 遗留命令 | `scripts/cmd/*.sh`（10 文件） | 删除 | Bash 命令实现，Python 已完全替代 |
| 遗留入口 | `scripts/flow-legacy.sh` | 删除 | Bash fallback，不再需要 |
| 遗留库 | `lib/*.sh`（8 文件） | 删除 | Bash 库，Python 层独立 |
| 遗留测试 | `tests/integration/*.sh`、`tests/unit/*.sh`、`tests/lib/*.sh`、`tests/run-tests.sh` | 删除 | 依赖 Bash lib 的遗留测试 |
| Python 缓存 | `scripts/dev_flow/**/__pycache__/` | 删除 | 清理编译缓存 |

## Implementation

### Task 1: 增加基础设施 — infra/git.py + domain/plan/metadata.py

**Files**: `scripts/dev_flow/infra/git.py`, `scripts/dev_flow/domain/plan/metadata.py`

**Changes**:

- [x] Step 1: 在 `infra/git.py` 新增 `merge_branch(repo_path, branch, target, no_ff=True)` — 合并指定分支到 target，返回 (success, conflict_files)
- [x] Step 2: 在 `infra/git.py` 新增 `branch_exists(repo_path, branch)` — 检查分支是否存在
- [x] Step 3: 在 `infra/git.py` 新增 `delete_branch(repo_path, branch, force=False)` — 删除本地分支
- [x] Step 4: 在 `infra/git.py` 新增 `push_branch(repo_path, branch='main')` — 推送指定分支
- [x] Step 5: 在 `infra/git.py` 新增 `has_uncommitted_changes(repo_path)` — 别名方法，复用 `is_repo_dirty`
- [x] Step 6: 在 `domain/plan/metadata.py` 新增 `get_plan_worktree(plan_path)` — 提取 Plan `Worktree` 字段（返回 dict: `{branch, path}` 或 None）
- [x] Step 7: 在 `domain/plan/metadata.py` 新增 `set_plan_worktree(plan_path, branch, path)` — 写入 Plan `Worktree` 字段

**Verification**:

- [x] Step 1: 在 Python REPL 中 import `dev_flow.infra.git` 确认新增函数可用
- [x] Step 2: 确认 `get_plan_worktree` 能正确解析 Worktree 字段格式（`branch_name | absolute_path`）

### Task 2: approve --confirm --worktree 写入 Worktree 字段

**Files**: `scripts/dev_flow/commands/approve.py`

**Changes**:

- [x] Step 1: 在 `cmd_approve` 中 worktree 创建成功后，调用 `set_plan_worktree` 写入分支名和路径到 Plan 元数据
- [x] Step 2: 写入格式：`- **Worktree**: <branch> | <absolute_path>`

**Verification**:

- [x] Step 1: 确认 approve --confirm --worktree 后 Plan 文件中出现 Worktree 字段
- [x] Step 2: 确认 `get_plan_worktree` 能正确读取写入的值

### Task 3: archive 命令增加 worktree 感知 + 自动提交 + 合并逻辑

**Files**: `scripts/dev_flow/commands/archive.py`

**Changes**:

- [x] Step 1: 新增 `_detect_worktree(plan_path, project, workspace_root)` — 从 Plan Worktree 字段读取，fallback 到 `.worktrees/<project>-issue-<N>-*` glob 匹配
- [x] Step 2: 新增 `_is_pr_path(plan_path, issue_number, repo)` — 检测是否有 pr/opened 标签或 Plan PR 字段
- [x] Step 3: 新增 `_commit_project_changes(project_path, plan_type, issue_number)` — 自动 git add -A + commit + push，commit message 从 Plan 元数据生成
- [x] Step 4: 新增 `_merge_worktree_branch(project_path, branch, worktree_path)` — 合并 worktree 分支到 main（--no-ff），处理冲突检测
- [x] Step 5: 新增 `_cleanup_worktree(project_path, branch, worktree_path, workspace_root)` — 调用 git-worktrees remove 清理 worktree 和分支
- [x] Step 6: 重写 `cmd_archive` 核心流程，替换原有 `print_post_archive_commit_guide` 为自动执行逻辑：
  ```
  archive 执行时：
    ├─ 1. 现有逻辑（sync + archive file + commit + close issue）
    ├─ 2. 检测 worktree
    │   ├─ 有 worktree + PR 路径 → 清理 worktree
    │   ├─ 有 worktree + 无 PR 路径 →
    │   │   ├─ 检查 worktree 未提交变更 → 有则阻断
    │   │   ├─ 合并分支到 main (--no-ff)
    │   │   ├─ 冲突 → 阻断 + 提示
    │   │   ├─ push main
    │   │   └─ 清理 worktree + 删除分支
    │   └─ 无 worktree →
    │       ├─ 检测 projects/$project/ 未提交变更
    │       └─ 有则 auto commit + push
    └─ 3. 输出完成摘要
  ```
- [x] Step 7: 删除 `print_post_archive_commit_guide` 函数和 `ProjectRepoCheckResult` dataclass（不再需要手动提示）

**Verification**:

- [x] Step 1: 运行 `python3 -c "from dev_flow.commands.archive import cmd_archive"` 确认无 import 错误
- [x] Step 2: 确认无 worktree + 无未提交变更时 archive 行为不变
- [x] Step 3: 确认 archive 输出包含 worktree 处理结果摘要

### Task 4: 删除遗留 Bash 脚本和测试

**Files**: `scripts/cmd/`, `scripts/flow-legacy.sh`, `lib/*.sh`, `tests/integration/*.sh`, `tests/unit/*.sh`, `tests/lib/*.sh`, `tests/run-tests.sh`

**Changes**:

- [x] Step 1: 删除 `scripts/cmd/` 目录全部内容（approve.sh, archive.sh, complete.sh, issue.sh, plan.sh, query.sh, sync.sh, utility.sh, verify.sh 共 9 个文件）
- [x] Step 2: 删除 `scripts/flow-legacy.sh`
- [x] Step 3: 删除 `lib/` 目录全部内容（check-doc.sh, common.sh, git.sh, issue.sh, labels.sh, plan-sync.sh, plan.sh, state-machine.sh 共 8 个文件）
- [x] Step 4: 删除 Bash 测试：`tests/integration/*.sh`（10 个文件）、`tests/unit/*.sh`（7 个文件）、`tests/lib/*.sh`（2 个文件）、`tests/run-tests.sh`
- [x] Step 5: 清理 Python `__pycache__` 目录

**Verification**:

- [x] Step 1: 确认 `scripts/cmd/`、`lib/`、`tests/integration/`、`tests/unit/`、`tests/lib/` 目录已清空
- [x] Step 2: 运行 `python3 -m pytest tests/python/ -x` 确认 Python 测试不受影响

### Task 5: 简化 flow.sh 入口 + 更新 SKILL.md

**Files**: `scripts/flow.sh`, `SKILL.md`

**Changes**:

- [x] Step 1: 简化 `flow.sh`：移除 `LEGACY_SCRIPT` 和 fallback 逻辑，未知命令直接报错退出
- [x] Step 2: 更新 SKILL.md 中关于 Bash 脚本执行的说明，移除所有 `scripts/cmd/*.sh` 和 `lib/*.sh` 引用

**Verification**:

- [x] Step 1: 运行 `flow.sh help` 确认入口正常
- [x] Step 2: 运行 `flow.sh unknown-cmd` 确认返回错误而非 fallback

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 2 | Task 2 | fae | Task 1 |
| 2 | Task 3 | fae | Task 1 |
| 3 | Task 4 | fae | 无 |
| 3 | Task 5 | fae | Task 4 |

## Risks

| 风险 | 影响 | 缓解 |
|------|------|------|
| 合并冲突导致 archive 中断 | 中 | 合并前检测 conflict，阻断并给出明确指引 |
| 删除 Bash 脚本后 flow.sh 行为变化 | 低 | 简化后逻辑更清晰，未知命令报错是正确行为 |
| Worktree 已被手动删除 | 低 | 降级为普通项目仓库提交流程 |
| 遗留 Bash 测试有 Python 版本未覆盖的 case | 低 | Python 测试已覆盖核心命令 surface、archive、approve、issue 等，遗留测试主要验证 Bash 实现 |

## Test Plan

#### Unit Tests

N/A — 新增函数为 subprocess 包装，逻辑简单，由集成测试覆盖。

#### Integration Tests

##### Case I1: archive 无 worktree 时自动提交项目变更
- Goal: 验证 archive 在项目仓库有未提交变更时自动 commit + push
- Fixture: 创建临时 Plan 文件（状态 done），在项目仓库中制造未提交变更
- Execution:
  - [x] Step 1: 准备测试环境（临时 Plan + 模拟项目仓库 dirty 状态）
  - [x] Step 2: 调用 `check_project_repo_state` 确认 `needs_commit=True`
  - [x] Step 3: 调用 archive 流程后确认项目仓库 clean
- Expected Evidence: 项目仓库 git status 为空，commit message 符合 `<type>: <desc> (#<issue>)` 格式

##### Case I2: archive 检测 worktree 并合并分支
- Goal: 验证 archive 正确检测 worktree 并执行合并流程
- Fixture: 模拟 Plan 含 Worktree 字段，模拟 worktree 目录存在
- Execution:
  - [x] Step 1: 创建含 Worktree 字段的 Plan 文件
  - [x] Step 2: 调用 `_detect_worktree` 确认返回正确的分支信息
  - [x] Step 3: 确认 `_is_pr_path` 在无 pr/opened 标签时返回 False
- Expected Evidence: `_detect_worktree` 返回 `{branch: '...', path: '...'}`，PR 路径检测正确

##### Case I3: flow.sh 入口简化后正常工作
- Goal: 确认删除 legacy fallback 后 flow.sh 路由正常
- Fixture: 清理后的 skill 目录
- Execution:
  - [x] Step 1: 运行 `flow.sh help` 确认返回帮助信息
  - [x] Step 2: 运行 `flow.sh status 115` 确认命令路由到 Python
  - [x] Step 3: 运行 `flow.sh nonexistent` 确认返回错误码非零
- Expected Evidence: help 和 status 正常输出，未知命令返回 exit code 1

#### E2E Tests

N/A — 完整 E2E 需要真实 worktree 和远程仓库交互，由用户验证覆盖。

#### Regression Tests

##### Case R1: 现有 archive 无项目变更时行为不变
- Goal: 确认项目仓库 clean 时 archive 行为与改动前一致
- Fixture: Plan 状态 done，项目仓库 clean
- Execution:
  - [x] Step 1: 调用 archive 流程
  - [x] Step 2: 确认不执行任何项目仓库操作
- Expected Evidence: archive 正常完成，无多余 commit/push

### Adjustment Strategy

N/A — 改动面可控，无复杂阻塞场景。

## Acceptance Criteria

### Agent Verification

- [x] 所有新增 Python 函数可正常 import，无语法错误
- [x] `python3 -m pytest tests/python/ -x` 全部通过
- [x] `flow.sh help`、`flow.sh status`、`flow.sh list` 命令正常执行
- [x] 遗留 Bash 脚本和测试文件已全部删除
- [x] `scripts/cmd/`、`lib/` 目录不存在或为空

### User Validation

#### Scenario 1: archive 自动提交项目变更
- Goal: 确认 archive 后项目仓库不再遗留未提交变更
- Precondition: 一个 Issue 开发完成，verify --confirm 通过，项目仓库有未提交的代码变更
- User Actions:
  1. 执行 `flow.sh archive <issue>`
  2. 进入项目目录执行 `git status` 和 `git log -1`
- Expected Result: git status 为 clean，git log 显示自动生成的 commit（格式 `<type>: <desc> (#<issue>)`）

#### Scenario 2: archive 自动合并 worktree 分支
- Goal: 确认使用 worktree 开发时 archive 自动合并并清理
- Precondition: 一个 Issue 通过 worktree 开发完成，verify --confirm 通过，代码在 feature 分支上
- User Actions:
  1. 执行 `flow.sh archive <issue>`
  2. 确认 main 分支包含 feature 分支的所有提交
  3. 确认 worktree 目录已清理
- Expected Result: main 分支包含合并提交，worktree 目录不存在，feature 分支已删除

- [x] 用户已完成上述功能验证并确认结果符合预期
