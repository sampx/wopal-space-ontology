# refactor-dev-flow-adapt-to-project-level-docs-migration

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-28
- **Status**: planning

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

将 dev-flow 技能从“空间级 docs/projects 管 Plan、项目仓库管代码”的双轨模型，重构为“项目文档与项目代码同仓同生命周期”的规范模型，并修正技能内部的 Plan 路径解析、Git 提交/推送、Issue 链接与归档流程。

## Technical Context

### Architecture Context

项目文档已从 `docs/projects/<project>/` 迁移到 `projects/<project>/docs/`，空间级 `docs/projects/<project>` 仅作为过渡软链接。dev-flow 当前仍以旧结构为事实源：

- Plan 创建和查找硬编码 `docs/projects/<project>/plans/`。
- approve/complete/verify/archive 的 Plan 状态变更和归档 Git 操作默认在空间仓库执行。
- Issue 中的 Plan 链接默认指向空间仓库路径。
- implementation commit 与 Plan commit 被分开处理，导致文档状态、Done checkbox、代码变更可能落在不同提交甚至不同仓库。

新结构下，标准项目的 Plan 属于项目仓库：`projects/<project>/docs/plans/`。Plan 文件、项目文档和项目代码应作为同一个项目仓库的工作产物被查找、提交、推送和链接。空间仓库只保留空间级文档；`.wopal/` ontology worktree 作为 `wopal-space-ontology` 项目的 runtime source，仍需特殊处理。

### Research Findings

- 当前 `scripts/commands/plan.py::_resolve_plan_dir()` 是 Plan 创建入口，仍写入旧路径。
- 当前 `scripts/plan.py::find_plan_by_name()` 与 `find_plan_by_issue()` 依赖旧路径 glob，且不应长期依赖软链接。
- 当前 `scripts/commands/approve.py::_commit_and_push_plan()` 总是在 `workspace_root` 提交/推送 Plan 状态变更。
- 当前 `scripts/commands/complete.py` 先提交项目代码，再更新 Plan 状态为 verifying；新模型下若 Plan 与代码同仓，会导致 Plan 状态变更落在提交之外。
- 当前 `scripts/commands/verify.py` 更新 Plan 状态为 done 后不提交，实际归档前存在未提交状态。
- 当前 `scripts/commands/archive.py::archive_plan_file()` 使用 `workspace_root` 执行 `git ls-files`、`git mv`、`git add`、commit、push；标准项目 Plan 在项目仓库时该逻辑不成立。
- 当前 `scripts/plan.py::update_issue_plan_link()` 假设归档文件相对 `docs/`，并将链接拼成空间仓库 URL。

**参考资料**：
- `projects/wopal-space-ontology/docs/AGENTS.md`
- `.wopal/skills/dev-flow/SKILL.md`
- `.wopal/skills/dev-flow/scripts/commands/approve.py`
- `.wopal/skills/dev-flow/scripts/commands/complete.py`
- `.wopal/skills/dev-flow/scripts/commands/verify.py`
- `.wopal/skills/dev-flow/scripts/commands/archive.py`
- `.wopal/skills/dev-flow/scripts/plan.py`

### Key Decisions

- D-01: 标准项目 Plan 的规范路径为 `projects/<project>/docs/plans/`，归档路径为 `projects/<project>/docs/plans/done/`。理由：文档与代码同仓，Plan 生命周期随项目仓库演进。
- D-02: 空间级综合 Plan 的规范路径为 `docs/plans/`，不再放入 `docs/projects/wopal-space/plans/`。理由：`wopal-space` 不是标准项目仓库，不能伪装为 project。
- D-03: 在 dev-flow 技能脚本内引入公共解析层，统一解析 Plan 位置、Plan 所属仓库、Target Project 路径、Issue 链接仓库。理由：禁止命令脚本各自拼路径，避免旧结构残留。
- D-04: complete 阶段若 Plan 文件与项目代码在同一仓库，代码变更、Done checkbox、Agent Verification、Plan status=verifying 必须进入同一个提交。理由：实现“文档和代码一体”的提交语义。
- D-05: approve --confirm 阶段允许产生 Plan-only 状态提交。理由：planning → executing 是实施授权边界，发生在代码实现之前。
- D-06: verify --confirm 阶段只更新用户验证状态和 Plan status=done，提交到 Plan 所属仓库；archive 阶段只移动 Plan 到 done/ 并提交归档。理由：用户验证和归档是不同生命周期事件。
- D-07: Issue 仍归属空间仓库；Plan 链接必须指向 Plan 所属项目仓库。理由：Issue 是协调入口，Plan 文件是项目资产。
- D-08: `.wopal/` ontology-worktree 保持特殊项目类型，但 Plan 存放在 `projects/wopal-space-ontology/docs/plans/`；runtime source 仍在 `.wopal/`。理由：产品文档仓库与运行时 worktree 已分离，但同属 wopal-space-ontology 项目。

### Key Interfaces

新增公共路径/仓库解析层，建议位置：`.wopal/skills/dev-flow/scripts/lib/project.py` 或 `.wopal/skills/dev-flow/scripts/lib/plan_location.py`。

核心数据结构：

- `ProjectContext`
  - `name`: Target Project 名称
  - `type`: `standard | ontology-worktree | space`
  - `project_path`: 项目代码仓库路径；标准项目为 `projects/<name>`，ontology runtime 为 `.wopal`
  - `docs_path`: 项目文档路径；标准项目为 `projects/<name>/docs`，ontology docs 为 `projects/wopal-space-ontology/docs`
  - `docs_repo_path`: 文档所属 git repo root
  - `code_repo_path`: 代码所属 git repo root
  - `repo_slug`: GitHub owner/repo
  - `default_branch`: 默认分支

- `PlanLocation`
  - `path`: Plan 绝对路径
  - `repo_root`: Plan 所属 git repo root
  - `repo_relative_path`: Plan 在所属 repo 内的相对路径
  - `github_repo`: Plan 所属 GitHub repo
  - `branch`: blob URL 使用的分支
  - `is_archived`: 是否在 `plans/done/`

公共函数：

- `resolve_project_context(plan_path | project_name, workspace_root) -> ProjectContext`
- `resolve_plan_dir(project_name, workspace_root) -> Path`
- `find_plan(input_ref, workspace_root) -> PlanLocation`
- `resolve_plan_location(plan_path, workspace_root) -> PlanLocation`
- `build_plan_blob_url(plan_location) -> str`
- `commit_paths(repo_root, paths, message) -> bool`
- `push_repo(repo_root, branch=None) -> bool`

## In Scope

- 将 Plan 创建/查找路径迁移到 `projects/<project>/docs/plans/` 与 `docs/plans/`。
- 引入公共解析函数，替代各脚本中的硬编码路径拼接。
- 重构 approve/complete/verify/archive 的 Git 操作，使 Plan 文件在其所属仓库提交和推送。
- 调整 complete 提交流程，使同仓项目的代码变更与 Plan 状态变更同 commit。
- 调整 Issue 相关 Plan 链接，指向项目仓库中的 Plan 文件。
- 更新 dev-flow 文档、模板和测试断言。
- 保留旧 `docs/projects/*` 软链接作为短期兼容读路径，但新写入不再使用旧路径。

## Out of Scope

- 不移除 `docs/projects/*` 软链接；软链接移除属于后续迁移收尾。
- 不重写历史 Plan 链接；只保证新同步和归档后的链接正确。
- 不改变 GitHub Issue 归属；Issue 仍在空间仓库中承载协调状态。
- 不改变 wsf 系列工作流；本 Plan 仅覆盖 dev-flow 技能。
- 不修改 `.wopal/AGENTS.md`、`.wopal/rules/`、`.wopal/commands/`、`.wopal/plugins/` 等 dev-flow 技能外文件；这些路径引用由独立小改动处理。

## Business Rules Impact

N/A — 无业务规则变更。本次为 dev-flow 工程工作流重构，不引入业务约束。

### 同步确认
- [ ] N/A — 无业务规则变更，无需同步 `BUSINESS_RULES.md`

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Path model | `.wopal/skills/dev-flow/scripts/lib/project.py` 或 `lib/plan_location.py` | 创建 | 统一解析项目、文档、Plan、repo、blob URL |
| Plan core | `.wopal/skills/dev-flow/scripts/plan.py` | 修改 | Plan 查找、链接、commit message 入口适配新位置 |
| plan command | `.wopal/skills/dev-flow/scripts/commands/plan.py` | 修改 | 新 Plan 写入项目 docs 仓库 |
| approve command | `.wopal/skills/dev-flow/scripts/commands/approve.py` | 修改 | Plan 状态提交到 Plan 所属 repo |
| complete command | `.wopal/skills/dev-flow/scripts/commands/complete.py` | 修改 | 同仓合并提交代码与 Plan 状态 |
| verify command | `.wopal/skills/dev-flow/scripts/commands/verify.py` | 修改 | done 状态提交到 Plan 所属 repo |
| archive command | `.wopal/skills/dev-flow/scripts/commands/archive.py` | 修改 | 在 Plan 所属 repo 中 git mv/add/commit/push |
| query/sync | `.wopal/skills/dev-flow/scripts/commands/query.py`, `sync.py` | 修改 | 列表与同步查找新路径 |
| docs | `.wopal/skills/dev-flow/SKILL.md`, `.wopal/skills/dev-flow/references/*.md`, `.wopal/skills/dev-flow/templates/plan.md` | 修改 | 更新技能内部路径规则与工作流说明 |
| tests | `.wopal/skills/dev-flow/tests/**` | 修改/新增 | 覆盖新路径、Git repo 归属和链接生成 |

## Acceptance Criteria

### Agent Verification

1. [ ] `cd .wopal/skills/dev-flow && python -m pytest tests/python/unit -q` 全部 pass
2. [ ] `cd .wopal/skills/dev-flow && python -m pytest tests/python/integration -q` 全部 pass 或记录需外部 gh/git 环境的跳过项
3. [ ] `rg -n 'docs/projects/.*/plans|docs/projects/plans' .wopal/skills/dev-flow -g '*.py' -g '*.md'` 仅剩兼容说明或测试 fixture 中明确标注的 legacy case
4. [ ] `cd .wopal/skills/dev-flow && bash scripts/flow.sh plan --title "test(dev-flow): path smoke" --project wopal-space-ontology --type test --scope dev-flow` 在 `projects/wopal-space-ontology/docs/plans/` 创建/定位 Plan
5. [ ] 对一个临时 fixture repo 验证：complete 阶段在 Plan 与代码同仓时产生单一提交，且提交同时包含代码文件与 Plan status=verifying
6. [ ] 对一个临时 fixture repo 验证：archive 阶段在 Plan 所属 repo 内完成 `plans/<name>.md` → `plans/done/<date>-<name>.md` 的 git move/commit
7. [ ] Issue body 中 Plan URL 指向项目仓库路径 `projects/<project>/docs/plans/...` 所属 repo，而不是空间仓库软链接路径

### User Validation

#### Scenario 1: 使用 dev-flow 创建项目 Plan
- Goal: 用户能感知到新 Plan 不再写入空间级 `docs/projects/`，而是写入项目仓库 docs。
- Precondition: dev-flow 修改完成并重启 ellamaka。
- User Actions:
  1. 对任一标准项目执行 `flow.sh plan --title ... --project <project> --type ...`。
  2. 查看输出 Plan 路径。
- Expected Result: 输出路径为 `projects/<project>/docs/plans/<plan>.md`。

#### Scenario 2: 完成一个项目任务后查看 git 提交
- Goal: 用户能确认代码变更与 Plan 状态记录同仓、同生命周期。
- Precondition: 有一个小型 dev-flow Plan 处于 executing。
- User Actions:
  1. 完成实现并运行 `flow.sh complete <plan>`。
  2. 查看项目仓库最新 commit。
- Expected Result: 最新 commit 同时包含项目代码变更和 Plan 中 Done/status=verifying 的变更。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: Build shared project and Plan location resolver

**Verification Intent**: AC#1, AC#3

**Behavior**: dev-flow 所有命令通过公共解析层获取项目路径、文档路径、Plan repo、代码 repo 和 GitHub blob URL，不再自行拼接 `docs/projects/*`。

**Files**: `.wopal/skills/dev-flow/scripts/lib/project.py` 或 `.wopal/skills/dev-flow/scripts/lib/plan_location.py`, `.wopal/skills/dev-flow/scripts/plan.py`

**Pre-read**: `.wopal/skills/dev-flow/scripts/lib/workspace.py`, `.wopal/skills/dev-flow/scripts/plan.py`

**Design**:
1. 新增 `ProjectContext` 与 `PlanLocation` 数据结构。
2. 标准项目解析为 `projects/<project>` 与 `projects/<project>/docs`。
3. ontology-worktree 的代码路径解析为 `.wopal`，文档路径解析为 `projects/wopal-space-ontology/docs`。
4. 空间级 Plan 解析为 `docs/plans`，repo 为 workspace root。
5. 提供统一 blob URL 构造函数，基于 Plan 所属 repo root 和 repo-relative path。

**TDD**: true

**Changes**:
1. 为标准项目、ontology-worktree、space Plan 编写 resolver 单元测试。
2. 实现 resolver。
3. 将 `build_plan_link_for_issue()`、`update_issue_plan_link()` 改为使用 `PlanLocation`。

**Verify**:
`cd .wopal/skills/dev-flow && python -m pytest tests/python/unit -q`

**Done**:
任务产出：公共解析层可稳定解析新文档结构和 Plan 所属仓库。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: Migrate Plan creation, lookup, query and sync to the new paths

**Verification Intent**: AC#1, AC#3, AC#4

**Behavior**: 新 Plan 写入 `projects/<project>/docs/plans/`；Plan 查找、列表、同步优先使用新路径，仅保留 legacy 读兼容。

**Files**: `.wopal/skills/dev-flow/scripts/commands/plan.py`, `.wopal/skills/dev-flow/scripts/plan.py`, `.wopal/skills/dev-flow/scripts/commands/query.py`, `.wopal/skills/dev-flow/scripts/commands/sync.py`

**Pre-read**: Task 1 产出的 resolver 文件

**Design**:
1. `_resolve_plan_dir()` 改为调用公共 resolver。
2. `find_plan_by_name()` 和 `find_plan_by_issue()` 搜索新路径：`projects/*/docs/plans`、`projects/*/docs/plans/done`、`docs/plans`、`docs/plans/done`。
3. 旧路径仅作为 fallback read path，并在代码注释中标注 legacy compatibility。
4. query/sync 共享同一 Plan discovery 函数，避免重复 glob。

**TDD**: true

**Changes**:
1. 增加新路径查找测试。
2. 修改创建和查找实现。
3. 修改 query/sync 调用统一 discovery。

**Verify**:
`cd .wopal/skills/dev-flow && python -m pytest tests/python/unit -q && bash scripts/flow.sh plan --title "test(dev-flow): path smoke" --project wopal-space-ontology --type test --scope dev-flow`

**Done**:
任务产出：Plan 创建、查找、列表和同步均使用新项目文档路径。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: Redesign Git commit/push semantics around Plan ownership

**Verification Intent**: AC#1, AC#5, AC#6

**Behavior**: Plan 文件在其所属 repo 中提交；同仓项目 complete 时，代码变更和 Plan 状态变更进入同一个提交；archive 在 Plan 所属 repo 内执行 git mv/commit/push。

**Files**: `.wopal/skills/dev-flow/scripts/commands/approve.py`, `.wopal/skills/dev-flow/scripts/commands/complete.py`, `.wopal/skills/dev-flow/scripts/commands/verify.py`, `.wopal/skills/dev-flow/scripts/commands/archive.py`, `.wopal/skills/dev-flow/scripts/lib/git.py`, `.wopal/skills/dev-flow/scripts/plan.py`

**Pre-read**: `.wopal/skills/dev-flow/scripts/lib/git.py`, Task 1 resolver

**Design**:
1. approve --confirm:
   - 更新 Plan status=executing。
   - 提交 Plan 文件到 `PlanLocation.repo_root`。
   - 如需 push，推送 Plan 所属 repo 当前分支。
2. complete:
   - 先完成 gate 校验。
   - 更新 Plan status=verifying。
   - 若 `PlanLocation.repo_root == code_repo_path`，一次提交包含代码变更和 Plan 变更。
   - 若不同仓，分别提交代码 repo 与 Plan repo，并在日志中清晰说明两个提交。
3. verify --confirm:
   - 校验用户 validation checkbox。
   - 更新 Plan status=done。
   - 提交 Plan 文件到 Plan 所属 repo，不在 archive 阶段才补提交。
4. archive:
   - 使用 Plan 所属 repo 的相对路径执行 `git mv`。
   - 归档提交发生在 Plan 所属 repo。
   - push 目标为 Plan 所属 repo 当前分支或默认分支。
5. 保持 ontology runtime 变更提交到 `.wopal`，但 Plan 变更提交到 `projects/wopal-space-ontology`；当同一次 complete 同时涉及 `.wopal` 和 docs repo，必须显式产生两个提交并在输出中说明。

**TDD**: true

**Changes**:
1. 增加 fixture 测试覆盖 Plan repo 与 code repo 相同/不同两种场景。
2. 改造 approve 的 `_commit_and_push_plan()` 为 repo-aware。
3. 改造 complete 的提交顺序，确保状态更新先于 commit。
4. 改造 verify 和 archive 的提交/移动逻辑。

**Verify**:
`cd .wopal/skills/dev-flow && python -m pytest tests/python/unit -q && python -m pytest tests/python/integration -q`

**Done**:
任务产出：dev-flow Git 操作以 Plan 所属仓库为核心，并支持文档代码同仓提交。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: Fix Issue links and GitHub repo resolution

**Verification Intent**: AC#1, AC#7

**Behavior**: Issue body 中的 Plan 链接指向 Plan 实际所属 GitHub repo 和 repo-relative path，不再默认指向空间仓库 `docs/projects/*`。

**Files**: `.wopal/skills/dev-flow/scripts/issue.py`, `.wopal/skills/dev-flow/scripts/plan.py`, `.wopal/skills/dev-flow/scripts/commands/sync.py`, `.wopal/skills/dev-flow/scripts/commands/archive.py`

**Pre-read**: Task 1 resolver

**Design**:
1. `build_repo_blob_url()` 支持传入 branch，默认从 repo resolver 获取。
2. Plan link 使用 `PlanLocation.github_repo` 和 `repo_relative_path`。
3. Issue status/labels 仍使用空间仓库 Issue repo；Plan blob URL 使用 Plan repo。两者不能混用。
4. archive 后更新 Issue 中 Plan URL 到 archived Plan 的项目仓库路径。

**TDD**: true

**Changes**:
1. 更新 Plan link contract 测试。
2. 改造 build/update link 函数。
3. 覆盖 active Plan 与 archived Plan 两种链接。

**Verify**:
`cd .wopal/skills/dev-flow && python -m pytest tests/python/unit/test_plan_link_contract.py tests/python/integration/test_related_resources_links.py -q`

**Done**:
任务产出：Issue 中 Plan 链接准确指向项目仓库中的 Plan 文件。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 5: Update dev-flow docs, templates and tests for the new model

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: dev-flow 技能内部文档说明新路径、新提交语义和同仓模型；模板不再引导 agent 读取旧路径。

**Files**: `.wopal/skills/dev-flow/SKILL.md`, `.wopal/skills/dev-flow/templates/plan.md`, `.wopal/skills/dev-flow/references/*.md`, `.wopal/skills/dev-flow/tests/**`

**Pre-read**: 本 Plan 的 Key Decisions

**Design**:
1. 将路径说明更新为 `projects/<project>/docs/...`。
2. 明确 `docs/projects/*` 是 legacy compatibility，不作为新写入目标。
3. 文档中补充 Git 语义：approve 可 Plan-only，complete 同仓合并提交，verify/ archive 分别提交状态与归档。
4. 更新测试 fixture 中旧路径断言；必要时保留 legacy fixture 并显式命名。

**TDD**: false — 文档与 fixture 更新，验证通过 rg 与现有测试完成。

**Changes**:
1. 更新 dev-flow 技能说明。
2. 更新模板中的 BUSINESS_RULES 路径。
3. 更新 commands/issue-format/troubleshooting references。
4. 更新测试断言。

**Verify**:
`rg -n 'docs/projects/.*/plans|docs/projects/\{project\}|docs/projects/<project>' .wopal/skills/dev-flow -g '*.md' -g '*.py'`

**Done**:
任务产出：dev-flow 技能内部文档、模板和测试均表达新项目文档结构。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 建立公共抽象，后续任务依赖 |
| 2 | Task 2 | fae | Task 1 | 路径迁移与发现逻辑集中改造 |
| 2 | Task 4 | fae | Task 1 | 链接生成可与路径迁移并行 |
| 3 | Task 3 | fae | Task 1, Task 2 | Git 语义风险最高，需在路径稳定后改造 |
| 4 | Task 5 | fae | Task 1-4 | 文档和测试应反映最终行为 |

每个 wave 完成后由 Wopal 运行对应 Verify 命令；Task 3 完成后必须委派 rook 做 implementation review，重点审查 Git 操作是否会误提交/误 push/跨仓错位。
