# refactor-git-worktrees-derive-project-list-from-filesystem

## Metadata

- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-26
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

优化 git-worktrees 与 dev-flow 的协作边界：git-worktrees 改为从文件系统发现项目；dev-flow 仅改进其内部对 worktree.sh 的调用与清理复用，不新增对外 worktree 命令面。

## Technical Context

**git-worktrees 问题**：
`worktree.sh` 的 `get_available_projects()` 通过 grep `.workspace.md` 中的 markdown 表格提取项目名。`.workspace.md` 是文档，不是稳定接口，格式随时可能调整，将其作为数据源不可靠。实际可操作项目应以 `projects/` 下存在 `.git` 的子目录为准。

**dev-flow 问题**：
1. `approve.py` 的 `_create_worktree()` 硬编码路径查找 `worktree.sh`，脆弱且难以适配不同部署位置
2. `archive.py` 的 `_cleanup_worktree()` 直接使用 git 命令，绕过 `worktree.sh`，导致逻辑重复

**边界原则**：
- 保持技能分离：`git-worktrees` 继续作为独立的通用 worktree 管理技能
- `dev-flow` 仅在 `approve --confirm --worktree` 与 `archive` 等生命周期命令内部调用 `git-worktrees`
- 不新增 `flow.sh worktree` 之类的包装命令，避免重复接口和不必要耦合

## In Scope

- 重写 `get_available_projects()` 改为扫描 `projects/*/` 下的 git 仓库
- 改进 approve.py 中 `worktree.sh` 的内部查找逻辑
- archive.py 清理 worktree 时优先复用 `worktree.sh remove --force`
- 更新 git-worktrees 技能文档，去除对 `.workspace.md` 项目表格的依赖描述

## Out of Scope

- 不新增 `flow.sh worktree` 或其他 dev-flow 对外 worktree 子命令
- 不合并两个技能，不移动脚本归属
- 不改 `find_workspace_root()`（仍依赖 `.workspace.md` 定位空间根，合理）
- 不改 dev-flow 的状态机或 Plan 生命周期

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| git-worktrees | `projects/ontology/agents/wopal/skills/git-worktrees/scripts/worktree.sh` | 修改 | 项目发现逻辑重构 |
| git-worktrees | `projects/ontology/agents/wopal/skills/git-worktrees/SKILL.md` | 修改 | 文档更新 |
| dev-flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/commands/approve.py` | 修改 | 改进内部 worktree 脚本查找 |
| dev-flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py` | 修改 | 复用 worktree.sh 清理 |
| dev-flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/infra/git.py` | 修改 | 提供共享的 worktree 脚本定位辅助函数 |

## Implementation

### Task 1: 重写 worktree.sh 项目发现逻辑

**Files**: `projects/ontology/agents/wopal/skills/git-worktrees/scripts/worktree.sh`

**Changes**:

- [x] Step 1: 重写 `get_available_projects()` 函数，从 `projects/` 目录扫描含 `.git` 的子目录
- [x] Step 2: 更新 `validate_project()` 的数据来源，确保使用扫描结果校验项目名
- [x] Step 3: 保持 `create`、`list`、`remove`、`prune` 命令的参数接口不变

**Verification**:

- [x] Step 1: 执行 `bash scripts/worktree.sh help` 确认脚本无语法错误
- [x] Step 2: 执行 `bash scripts/worktree.sh list` 验证能正确列出项目

### Task 2: 更新 git-worktrees SKILL.md

**Files**: `projects/ontology/agents/wopal/skills/git-worktrees/SKILL.md`

**Changes**:

- [x] Step 1: 删除“项目列表”章节中“从 `.workspace.md` 动态读取”的描述
- [x] Step 2: 改为说明“自动扫描 `projects/` 目录下包含 `.git` 的子目录”

**Verification**:

- [x] Step 1: 读取更新后的 SKILL.md 确认描述准确

### Task 3: 提取并复用 worktree.sh 查找逻辑

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/infra/git.py`, `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/commands/approve.py`

**Changes**:

- [x] Step 1: 在 `infra/git.py` 中新增共享辅助函数，统一查找 `git-worktrees/scripts/worktree.sh`
- [x] Step 2: 查找顺序覆盖运行时部署层和源码层，避免硬编码单一路径
- [x] Step 3: 更新 `approve.py` 的 `_create_worktree()` 改为使用共享辅助函数

**Verification**:

- [x] Step 1: 执行相关 Python 导入检查，确认辅助函数可被 `approve.py` 正常调用
- [x] Step 2: 检查缺少脚本时仍能返回明确错误或降级提示

### Task 4: archive.py 复用 worktree.sh 清理

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/commands/archive.py`, `projects/ontology/agents/wopal/skills/dev-flow/scripts/dev_flow/infra/git.py`

**Changes**:

- [x] Step 1: 更新 `_cleanup_worktree()` 优先调用 `worktree.sh remove <project> <branch> --force`
- [x] Step 2: 保留 fallback：当脚本不可用或调用失败时，再降级为直接 git 清理
- [x] Step 3: 保持 archive 现有行为语义不变（清理 worktree 并删除分支）

**Verification**:

- [x] Step 1: 执行相关 Python 导入检查，确认 `archive.py` 可正常加载
- [x] Step 2: 检查清理逻辑在脚本存在和脚本缺失两种路径下都有明确处理

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 1 | Task 2 | fae | 无 |
| 1 | Task 3 | fae | 无 |
| 2 | Task 4 | fae | Task 3 |

## Test Plan

#### Unit Tests

N/A — shell 脚本与命令编排改动，以集成和回归测试覆盖

#### Integration Tests

##### Case I1: worktree.sh list 正确发现项目
- Goal: 验证项目发现逻辑改为文件系统扫描后仍能正确工作
- Fixture: 当前工作空间 `projects/` 目录
- Execution:
  - [x] Step 1: 在空间根目录执行 `bash .agents/skills/git-worktrees/scripts/worktree.sh list`
  - [x] Step 2: 确认输出包含 `ontology`、`wopal-cli` 等实际项目
- Expected Evidence: 输出包含实际存在的项目名

##### Case I2: validate_project 拒绝无效项目
- Goal: 验证传入不存在的项目名时能正确报错
- Fixture: 无
- Execution:
  - [x] Step 1: 执行 `bash .agents/skills/git-worktrees/scripts/worktree.sh create nonexistent-project test-branch 2>&1`
  - [x] Step 2: 确认输出包含“无效项目名”错误
- Expected Evidence: stderr 包含“无效项目名”且 exit code 非 0

#### E2E Tests

N/A — 不新增新的对外命令面，现有行为通过回归场景验证

#### Regression Tests

##### Case R1: worktree.sh create/remove 仍正常
- Goal: 确认项目发现重构后 create/remove 命令仍按原接口工作
- Fixture: ontology 项目存在且工作区干净
- Execution:
  - [x] Step 1: 执行 `bash .agents/skills/git-worktrees/scripts/worktree.sh create ontology test-regression-check --no-install --no-test`
  - [x] Step 2: 确认 worktree 创建成功
  - [x] Step 3: 执行 `bash .agents/skills/git-worktrees/scripts/worktree.sh remove ontology test-regression-check --force`
  - [x] Step 4: 确认清理成功
- Expected Evidence: create 成功创建 worktree，remove 成功清理 worktree 与分支

##### Case R2: dev-flow 的 approve/cleanup 内部集成不引入新命令耦合
- Goal: 确认 dev-flow 仅内部复用 git-worktrees，而不暴露新的 worktree 命令接口
- Fixture: 更新后的 dev-flow 源码
- Execution:
  - [x] Step 1: 读取 `flow.sh` 与 `flow.py`，确认未新增 `worktree` 子命令
  - [x] Step 2: 读取 `approve.py` 与 `archive.py`，确认仅内部调用共享辅助函数和 `worktree.sh`
- Expected Evidence: dev-flow 命令面无新增 worktree 命令，内部协作代码存在

### Adjustment Strategy

如果 `worktree.sh remove --force` 与 archive 当前清理语义不完全一致，优先保持 archive 行为正确，再决定调用参数或 fallback 策略，不强行追求“100% 复用”。

## Acceptance Criteria

### Agent Verification

- [x] `worktree.sh help` 无语法错误
- [x] `worktree.sh list` 能正确发现 `projects/` 下的项目
- [x] 传入无效项目名时 `worktree.sh create` 正确报错
- [x] `approve.py` 不再硬编码单一路径查找 `worktree.sh`
- [x] `archive.py` 优先复用 `worktree.sh` 清理，并保留可用 fallback
- [x] dev-flow 未新增 `flow.sh worktree` 等对外 worktree 命令
- [x] git-worktrees SKILL.md 中不再引用 `.workspace.md` 作为项目列表数据源

### User Validation

#### Scenario 1: 方案边界保持清晰
- Goal: 确认这次优化强化的是内部协作，而不是合并技能边界
- Precondition: 代码修改完成并可阅读
- User Actions:
  1. 查看 git-worktrees 技能入口与 dev-flow 命令面
  2. 检查 dev-flow 是否只在生命周期命令内部调用 worktree 能力
- Expected Result: git-worktrees 仍是独立技能；dev-flow 没有新增通用 worktree 管理入口

- [x] 用户已完成上述功能验证并确认结果符合预期
