# feat(dev-flow): support ontology-worktree project type

## Metadata

- **Type**: feat
- **Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-13
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

使 dev-flow 全生命周期支持 `ontology-worktree` 项目类型（`.wopal/` worktree），包括 Issue 创建自动注入类型信息、Plan 模板预填元数据、approve worktree 隔离创建、archive ontology 变更提交。

## Technical Context

### 现状问题

`.wopal/` 是 ontology fork 的 worktree（`sampx/wopal-space-ontology`，分支 `space/main`），负责空间能力（skills、agents、rules、plugin）的开发。它不在 `projects/` 下，不遵循标准项目的 git 工作流。

当前 dev-flow 的所有环节（issue 创建、plan 编制、approve、archive）都基于"项目在 `projects/<name>/` 下，分支最终合并到 `main`"的假设，导致 `.wopal/` 的开发过程中：

1. **Issue 创建**：Agent 不知道目标项目是 ontology worktree，无法在 Plan 中正确描述开发路径
2. **Plan 编制**：Plan metadata 缺少 `Project Path` 和 `Project Type` 字段
3. **Archive**：`resolve_project_path` 无法找到 `.wopal/`，跳过项目变更处理；即使找到，`_commit_project_changes` 会尝试 push 到 `main` 而非 `space/main`
4. **Worktree 隔离**：`approve --confirm --worktree` 无法为 `.wopal/` 创建隔离 worktree

### 架构约束

- `.wopal/` 本身是一个 worktree（指向 `~/.wopal/ontologies/wopal-space-ontology/`）
- `.wopal/` 的分支是 `space/main`，提交后 push 到 fork（`sampx/wopal-space-ontology`）
- `.wopal/` 的变更直接影响运行时（无需安装步骤）
- 标准项目在 `projects/<name>/` 下，是独立 git repo

### 风险

- 修改 `archive.py` 的提交流程可能影响现有标准项目的归档行为
- `approve --confirm --worktree` 为 ontology 创建 worktree 需要正确解析主仓库路径
- 文档变更需要与代码变更保持同步

## In Scope

- `.workspace.md` 和 `AGENTS.md` 增加项目类型说明
- `project.py` 增加项目类型注册表和识别逻辑
- Issue 创建时自动注入项目类型和路径信息
- Plan 模板增加 `Project Path` 和 `Project Type` 字段
- `archive.py` 增加 ontology worktree 专用提交流程
- `approve.py` 支持 ontology worktree 的 `--worktree` 模式

## Out of Scope

- `wopal space save` 命令的修改（保持现有 active space 设计）
- 上游 PR 工作流（fork → upstream PR，单独设计）
- `complete --pr` 的 ontology 适配
- `MEMORY.md` 更新

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 空间文档 | `.workspace.md` | 修改 | 增加项目类型列和说明 |
| 空间宪法 | `AGENTS.md` | 修改 | 扩展 ontology-worktree 的 dev-flow 规则 |
| dev-flow 项目适配 | `scripts/dev_flow/domain/plan/project.py` | 修改 | 增加 ProjectType 和注册表 |
| dev-flow Issue 创建 | Issue 创建逻辑（`issue create` 命令） | 修改 | 自动注入类型/路径字段 |
| dev-flow 模板 | `templates/plan.md` | 修改 | 增加可选 metadata 字段 |
| dev-flow 归档 | `scripts/dev_flow/commands/archive.py` | 修改 | 增加 ontology 提交 handler |
| dev-flow 审批 | `scripts/dev_flow/commands/approve.py` | 修改 | 支持 ontology worktree 隔离创建 |

## Implementation

### Task 1: 文档层 — `.workspace.md` 和 `AGENTS.md` 更新

**Files**: `.workspace.md`, `AGENTS.md`

**Changes**:

- [x] Step 1: `.workspace.md` 项目表增加"类型"列，标明每个项目的类型（`standard` / `ontology-worktree`）
- [x] Step 2: `.workspace.md` 新增"项目类型说明"章节，描述两种类型的路径、分支策略、dev-flow 行为差异
- [x] Step 3: `AGENTS.md` "项目归属"节扩展 ontology-worktree 的 dev-flow 各阶段特殊行为说明
- [x] Step 4: 两端文档交叉验证：确保 `standard` / `ontology-worktree` 类型标识一致，行为描述无矛盾

**Verification**:

- [x] Step 1: 人工阅读 `.workspace.md` 和 `AGENTS.md`，确认 Agent 能从文档中理解 ontology-worktree 类型的所有行为差异
- [x] Step 2: 确认两个文档对同一类型的描述一致

### Task 2: 代码层 — `project.py` 增加项目类型注册表

**Files**: `scripts/dev_flow/domain/plan/project.py`

**Changes**:

- [x] Step 1: 新增 `ProjectType` 枚举：`STANDARD`、`ONTOLOGY_WORKTREE`
- [x] Step 2: 新增 `PROJECT_TYPE_REGISTRY` 字典，映射 project_name → `{type, path}`
- [x] Step 3: 新增 `resolve_project_type(project_name)` 函数，查 registry 返回类型信息
- [x] Step 4: 新增 `get_current_branch(repo_path)` 函数，返回当前 HEAD 分支名
- [x] Step 5: 新增 `get_ontology_main_repo(workspace_root)` 函数，从 `.wopal/.git` 文件解析 ontology 主仓库路径

**Verification**:

- [x] Step 1: 单元测试 — `resolve_project_type("wopal-space-ontology")` 返回 `ONTOLOGY_WORKTREE`
- [x] Step 2: 单元测试 — `resolve_project_type("wopal-cli")` 返回 `STANDARD`
- [x] Step 3: 手动验证 — `get_current_branch(workspace_root / ".wopal")` 返回 `space/main`
- [x] Step 4: 手动验证 — `get_ontology_main_repo(workspace_root)` 返回正确的 ontology 主仓库路径

### Task 3: 流程层 — Issue 创建自动注入

**Files**: Issue 创建逻辑（`issue create` 命令相关模块）

**Changes**:

- [x] Step 1: 在 `issue create` 时查询 `resolve_project_type(project_name)`
- [x] Step 2: 如果匹配 registry 中的类型，自动在 Issue body 中注入：
  - `- **Project Type**: {type}`
  - `- **Project Path**: {path}`（如果 registry 有 path）
- [x] Step 3: 如果 registry 中没有该 project_name，不注入额外字段（保持向后兼容，不影响标准项目）

**Verification**:

- [x] Step 1: 模拟 `issue create --project wopal-space-ontology` → body 包含 `Project Type: ontology-worktree` 和 `Project Path: .wopal`
- [x] Step 2: 模拟 `issue create --project wopal-cli` → body **不**包含 `Project Type` 和 `Project Path` 字段

### Task 4: 模板层 — Plan 模板增加字段

**Files**: `templates/plan.md`

**Changes**:

- [x] Step 1: Metadata 段增加两个可选字段（标注为可选，仅 ontology-worktree 类型 Plan 需要）：
  ```markdown
  {project_path_line}
  {project_type_line}
  ```
- [x] Step 2: `plan` 命令创建 Plan 时，如果 Issue body 有这两个字段，自动填入 Plan metadata

**Verification**:

- [x] Step 1: 为 ontology-worktree 项目创建 Plan → metadata 包含完整的 type/path 字段
- [x] Step 2: 为标准项目创建 Plan → metadata 不包含这两个字段（不中断流程）

### Task 5: 归档层 — `archive.py` ontology 提交 handler

**Files**: `scripts/dev_flow/commands/archive.py`

**Changes**:

- [x] Step 1: 新增 `_commit_ontology_worktree(workspace_root, plan_type, issue_number)` 函数：
  - 检测 `.wopal/` 是否有未提交变更（`has_uncommitted_changes`）
  - 获取当前分支（`get_current_branch`）
  - 生成 commit message（格式：`{type}: implement plan changes (#{issue})`）
  - 执行 `git add -A` → `git commit` → `git push origin {branch}`
- [x] Step 2: 在 `cmd_archive` 的 Step 3（项目变更检测）中增加类型判断分支：
  - 读 `Project Type` 字段
  - 如果为 `ontology-worktree` → 调用 `_commit_ontology_worktree`，**跳过** worktree 合并/清理逻辑
  - 否则走现有逻辑
- [x] Step 3: Step 2 中跳过 worktree 检测/合并/清理的所有逻辑（`.wopal/` 本身就是 worktree，不需要这些）

**Verification**:

- [x] Step 1: 模拟 scenario — `.wopal/` 有未提交变更，执行 archive → 变更被 commit + push 到 `origin/space/main`
- [x] Step 2: 模拟 scenario — `.wopal/` 无未提交变更，执行 archive → 正常完成，无错误
- [x] Step 3: 回归验证 — 标准项目（如 wopal-cli）的 archive 流程不受影响

### Task 6: 审批层 — `approve.py` worktree 隔离支持

**Files**: `scripts/dev_flow/commands/approve.py`

**Changes**:

- [x] Step 1: 在 `approve --confirm --worktree` 路径中增加 ontology-worktree 处理分支：
  - 解析 ontology 主仓库路径（通过 `get_ontology_main_repo`）
  - 从 `space/main` 创建 feature 分支 `issue-{N}-{slug}`
  - 在 `.worktrees/ontology-issue-{N}-{slug}` 创建 worktree
  - Plan metadata 写入 Worktree 字段
- [x] Step 2: 处理边缘情况：ontology 主仓库路径解析失败 → 阻断并提示

**Verification**:

- [x] Step 1: 模拟 — `flow.sh approve <issue> --confirm --worktree`（ontology-worktree 项目）→ 在 `.worktrees/` 下创建 ontology feature worktree
- [x] Step 2: 验证 — worktree 内容与 `.wopal/` 一致（分支 `space/main` 的副本）
- [x] Step 3: 验证 — Plan 中 Worktree 字段正确记录分支和路径

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 (文档) | fae | 无 |
| 2 | Task 2 (project.py) | fae | Task 1 完成（需了解文档约定的类型名） |
| 2 | Task 3 (Issue 注入) | fae | Task 2 完成（依赖 resolve_project_type） |
| 2 | Task 4 (模板) | fae | 无 |
| 3 | Task 5 (archive) | fae | Task 2 完成（依赖 get_current_branch） |
| 3 | Task 6 (approve) | fae | Task 2 完成（依赖 get_ontology_main_repo） |

## Test Plan

### Unit Tests

N/A — 脚本流程无独立单元测试框架，验证以手动执行为主。

### Integration Tests

##### Case I1: Project type registry 解析

- Goal: 验证 `resolve_project_type` 正确识别 ontology-worktree 和 standard 项目
- Fixture: `project.py` 中的 `PROJECT_TYPE_REGISTRY`
- Execution:
  - [x] Step 1: 编写临时 Python 脚本调用 `resolve_project_type("wopal-space-ontology")`，断言返回 `ONTOLOGY_WORKTREE`
  - [x] Step 2: 调用 `resolve_project_type("wopal-cli")`，断言返回 `None`（standard 类型）
  - [x] Step 3: 调用 `resolve_project_type("nonexistent-project")`，断言返回 `None`
- Expected Evidence: 三次调用均返回预期结果

##### Case I2: ontology archive 提交流程

- Goal: 验证 `_commit_ontology_worktree` 正确处理 `.wopal/` 变更
- Fixture: 在 `.wopal/` 中创建一个临时文件（如 `.tmp/test-archive.md`）
- Execution:
  - [x] Step 1: 执行 `flow.sh archive <plan-name>`（Plan 的 `Project Type` 为 `ontology-worktree`）
  - [x] Step 2: 检查 `.wopal/` git log 确认新增了 commit
  - [x] Step 3: 检查 `.wopal/` git status 确认工作区清洁
  - [x] Step 4: 清理临时文件，revert commit
- Expected Evidence: commit 存在，message 格式正确，push 到 `origin/space/main`

### E2E Tests

##### Case E1: ontology-worktree Plan 全生命周期

- Goal: 从 Issue 创建到归档，完整走通 ontology-worktree 项目流程
- Fixture: 创建一个测试 Issue（如 Issue #200），project 为 `wopal-space-ontology`
- Execution:
  - [x] Step 1: `flow.sh issue create --project wopal-space-ontology --type feat --goal "test"` → body 包含 Project Type 和 Path
  - [x] Step 2: `flow.sh plan <issue>` → Plan metadata 包含 type/path 字段
  - [x] Step 3: 在 `.wopal/` 中做一个简单代码变更
  - [x] Step 4: `flow.sh approve --confirm` → 不报错
  - [x] Step 5: `flow.sh complete` → 通过
  - [x] Step 6: `flow.sh verify --confirm` → 通过
  - [x] Step 7: `flow.sh archive` → `.wopal/` 变更被提交，Plan 归档到 done/
- Expected Evidence: 每个命令返回成功，最终 Plan 在 done/ 下，`.wopal/` 有对应 commit

### Regression Tests

##### Case R1: 标准项目流程不受影响

- Goal: 确认 ontology-worktree 改动不破坏标准项目的 dev-flow 流程
- Fixture: 使用任意标准项目（如 wopal-cli）的已有 Issue
- Execution:
  - [x] Step 1: `flow.sh plan <issue>` → 正常创建 Plan
  - [x] Step 2: 检查 Plan metadata 不包含 `Project Type` / `Project Path`
  - [x] Step 3: `flow.sh approve` → 正常执行
  - [x] Step 4: `flow.sh archive <issue>` → 确认 archive 流程不变
- Expected Evidence: 所有命令行为与改动前一致，无新增错误或 warning

## Acceptance Criteria

### Agent Verification

- [x] Task 1-6 全部完成，所有 Step checkbox 已勾选
- [x] `project.py` 中新增函数可 import 无语法错误
- [x] `archive.py` 修改后 Python 语法无错误
- [x] `approve.py` 修改后 Python 语法无错误

### User Validation

#### Scenario 1: 创建 ontology 相关 Issue 时 body 自动包含类型信息

- Goal: 确认 `flow.sh issue create --project wopal-space-ontology` 创建的 Issue body 中包含 `Project Type: ontology-worktree` 和 `Project Path: .wopal`
- Precondition: `PROJECT_TYPE_REGISTRY` 中已注册 `wopal-space-ontology`
- User Actions:
  1. 执行 `flow.sh issue create --project wopal-space-ontology --type feat --goal "test"`
  2. 查看生成的 Issue body
- Expected Result: body 的 Metadata 段包含 `Project Type: ontology-worktree` 和 `Project Path: .wopal`

#### Scenario 2: ontology Plan 归档时自动提交 .wopal/ 变更

- Goal: 确认 `flow.sh archive` 对 ontology-worktree 类型 Plan 能正确提交 `.wopal/` 的未提交变更
- Precondition: `.wopal/` 有未提交变更，Plan 状态为 `done`，`Project Type` 为 `ontology-worktree`
- User Actions:
  1. 执行 `flow.sh archive <plan-name>`
  2. 观察输出和 `.wopal/` 的 git 状态
- Expected Result: `.wopal/` 的变更被 commit + push 到 `origin/space/main`，Plan 归档到 done/

- [x] 用户已完成上述功能验证并确认结果符合预期
