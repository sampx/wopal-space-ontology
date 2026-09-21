# feature-dev-flow-support-existing-worktree-evolution-mode-without-merge

## Metadata

- **Type**: feat
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Status**: done
- **Base Commit**: f30a63da57665b6f8c868a1ade2e872f415afc57
- **Final Commit**: 548c4470230453366543b007d9979d5d0a92fb59
- **Worktree**: (--no-worktree 模式，直接在集成分支实施)

## Goal

为 dev-flow 引入「独立分支演进模式」，支持在 POC 探索与阶段性开发中复用已有 worktree 持续演进多个 Plan，跳过强制合并 main 与强制清理 worktree。同时新增 `issue list` 命令，自动定位空间仓库列出未完成 issue 并显示 repo URL，消除 Agent 手动 `gh issue` 查错仓库的问题。

## Technical Context

### Architecture Context
- `scripts/commands/approve.py`：负责解析审批参数、创建或绑定 worktree、写入元数据和记录 Base Commit。
- `scripts/commands/verify.py`：负责检查分支合并状态、用户验证确认、记录 Final Commit 并推进到 done。
- `scripts/commands/archive.py`：负责清理工作树与分支、归档 Plan 文件并关闭 Issue。
- `SKILL.md`：核心技能规范与决策指令指南。

## Overview

在 POC 探索、多阶段实验或长周期架构重构场景中，功能尚未稳定不能合入 `main`，需要保留 worktree 供后续多个连续 Plan 堆叠演进。
目前 dev-flow 强制每个 Plan 必须从 `main` 新建工作树，并在 `verify` 强制检查合入 `main`、在 `archive` 强制清理工作树与分支。这导致后续 Plan 无法复用已有环境，甚至误导 Agent 到 `main` 分支修改代码。

本 Plan 为 dev-flow 新增「独立分支演进模式」：
1. `approve` 支持 `--existing-worktree <path>`：复用已有工作树目录与分支，`Base Commit` 正确记录该分支当前 HEAD。
2. `verify` 支持 `--keep-worktree`：跳过合入检测，`Final Commit` 记录该特性分支当前 HEAD。
3. `archive` 支持 `--keep-worktree`：跳过工作树与分支清理，仅归档 Plan 并关闭 Issue。
4. 在 `SKILL.md` 与参考文档中明确规范 Agent 依据用户评审指令判定模式的决策逻辑。

## Verification Intent

- 验证 `--existing-worktree` 能够正确解析已有 worktree 路径与分支，写入 Plan 元数据并记录正确的 Base Commit。
- 验证 `--keep-worktree` 在 `verify` 阶段跳过合并检测并记录特性分支 HEAD 为 Final Commit。
- 验证 `--keep-worktree` 在 `archive` 阶段保留 worktree 目录与分支，仅归档 Plan。
- 验证 `SKILL.md` 场景规则清晰，防止 Agent 误用 `--no-worktree` 在 `main` 分支开发。
- 验证 `issue list` 自动定位空间仓库，列出未完成 issue 并显示 repo URL。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 审批命令 | `.wopal/skills/dev-flow/scripts/commands/approve.py` | 修改 | 支持 `--existing-worktree`，绑定已有分支并记录 HEAD 为 Base Commit |
| 验证命令 | `.wopal/skills/dev-flow/scripts/commands/verify.py` | 修改 | 支持 `--keep-worktree`，跳过 merge 检查并记录特性分支 Final Commit |
| 归档命令 | `.wopal/skills/dev-flow/scripts/commands/archive.py` | 修改 | 支持 `--keep-worktree`，跳过 worktree 和分支删除 |
| Issue 命令 | `.wopal/skills/dev-flow/scripts/commands/issue.py` | 修改 | 新增 `issue list` 子命令，列出未完成 issue 并显示 repo URL |
| 帮助文本 | `.wopal/skills/dev-flow/scripts/flow.py` | 修改 | help 文本新增 `issue list` |
| 技能规范 | `.wopal/skills/dev-flow/SKILL.md` | 修改 | 新增「Approve 模式选择」与「独立分支演进模式」规范；`issue list` 命令速查 |
| 参考文档 | `.wopal/skills/dev-flow/references/commands.md` | 修改 | 更新各命令参数说明与使用示例；新增 `issue list` |
| Issue 指南 | `.wopal/skills/dev-flow/references/issue-guide.md` | 修改 | 新增 `issue list` 用途说明 |
| 单元测试 | `.wopal/skills/dev-flow/tests/python/unit/test_approve.py` | 修改 | 新增 `--existing-worktree` 单元测试 |
| 单元测试 | `.wopal/skills/dev-flow/tests/python/unit/test_verify.py` | 修改 | 新增 `--keep-worktree` 单元测试 |
| 单元测试 | `.wopal/skills/dev-flow/tests/python/unit/test_archive.py` | 修改 | 新增 `--keep-worktree` 单元测试 |
| 单元测试 | `.wopal/skills/dev-flow/tests/python/unit/test_issue_list.py` | 新增 | `issue list` 单元测试 |

## Acceptance Criteria

### Agent Verification

1. [x] `pytest tests/python/unit/test_approve.py` 全部 pass（包含 `--existing-worktree` 校验、元数据写入、Base Commit 读取）
2. [x] `pytest tests/python/unit/test_verify.py` 全部 pass（包含 `--keep-worktree` 跳过 merge 检查、Final Commit 正确记录）
3. [x] `pytest tests/python/unit/test_archive.py` 全部 pass（包含 `--keep-worktree` 保留工作树与分支）
4. [x] `pytest tests/python/` 全量测试套件 100% pass 零回归
5. [x] `bash scripts/flow.sh plan check feature-dev-flow-support-existing-worktree-evolution-mode-without-merge` 校验通过
6. [x] `bash scripts/flow.sh issue list` 输出未完成 issue 列表且含 repo URL（对应 `test_issue_list.py`）

### User Validation

#### Scenario 1: 演进模式收尾当前 Ellamaka Plan
- Goal: 使用新增的 `--keep-worktree` 选项平滑收尾卡在 `verifying` 状态的 Ellamaka Plan，且保留现有 worktree
- User Actions:
  1. 运行 `bash .wopal/skills/dev-flow/scripts/flow.sh verify feature-ellamaka-cordis-container-hosts-loop-with-spill-plugins --confirm --keep-worktree`
  2. 运行 `bash .wopal/skills/dev-flow/scripts/flow.sh archive feature-ellamaka-cordis-container-hosts-loop-with-spill-plugins --keep-worktree`
- Expected Result: Plan 成功归档为 done，`.worktrees/ellamaka-feature-ellamaka-cordis-container-hosts-loop-with-spill-plugins` 目录和分支均完整保留

- [x] 用户已完成上述功能验证并确认结果符合预期

---

## Implementation

### Task 1: 单元测试扩展 (TDD - RED)

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**:
- `test_approve.py`: 传入 `--existing-worktree <path>` 时，解析已有分支、写入 Plan `Worktree` 元数据、`Base Commit` 读取该 worktree 当前 HEAD。
- `test_verify.py`: 传入 `--keep-worktree` 时，即使 feature 分支未合并至 `main`，也允许 transition 到 `done`，并将 `Final Commit` 记录为 feature 分支 HEAD。
- `test_archive.py`: 传入 `--keep-worktree` 时，跳过 `clean_worktree`，不删除目录也不删除分支，Plan 文件移入 `done/`。

**Files**:
- `.wopal/skills/dev-flow/tests/python/unit/test_approve.py`
- `.wopal/skills/dev-flow/tests/python/unit/test_verify.py`
- `.wopal/skills/dev-flow/tests/python/unit/test_archive.py`

**Pre-read**: `.wopal/skills/dev-flow/AGENTS.md` §5 (TDD 规则)

**Design**:
编写精准的 input → output pytest 测试用例，断言参数解析、元数据写入以及函数调用分支，运行测试确认在当前未实现代码下失败 (RED)。

**TDD**: true

**Changes**:
1. 在 `test_approve.py` 增加 `test_approve_existing_worktree`
2. 在 `test_verify.py` 增加 `test_verify_keep_worktree_skips_merge_check`
3. 在 `test_archive.py` 增加 `test_archive_keep_worktree_preserves_dir_and_branch`

**Verify**: `python -m pytest tests/python/unit/test_approve.py tests/python/unit/test_verify.py tests/python/unit/test_archive.py` 出现预期的失败 (RED)

**Done**: 单元测试用例已添加并成功捕获未实现特性
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: 脚本实现 (TDD - GREEN)

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**:
- `approve.py`: 增加 `--existing-worktree` CLI 参数解析；校验路径有效性并读取工作树分支；写入 Worktree 元数据并提取该分支 HEAD 为 Base Commit。
- `verify.py`: 增加 `--keep-worktree` CLI 参数解析；跳过 `_check_feature_branch_merged`；Final Commit 写入 feature 分支最新 HEAD。
- `archive.py`: 增加 `--keep-worktree` CLI 参数解析；跳过 `_cleanup_worktree`。

**Files**:
- `.wopal/skills/dev-flow/scripts/commands/approve.py`
- `.wopal/skills/dev-flow/scripts/commands/verify.py`
- `.wopal/skills/dev-flow/scripts/commands/archive.py`

**Pre-read**: `.wopal/skills/dev-flow/scripts/lib/worktree.py`

**Design**:
- `approve.py`: 当 `args.existing_worktree` 存在时，解析其对应分支与相对路径，写入 Plan 的 `Worktree` 字段。获取 `get_branch_head(wt_path, branch)` 写入 `Base Commit`。
- `verify.py`: 当 `args.keep_worktree` 为 True 时，跳过 `_check_feature_branch_merged`，`_record_final_commit` 改为获取 feature 分支的 HEAD。
- `archive.py`: 当 `args.keep_worktree` 为 True 时，跳过 `_cleanup_worktree`，保留分支与目录。

**TDD**: true

**Changes**:
1. 修改 `approve.py` 的参数注册与执行逻辑
2. 修改 `verify.py` 的参数注册与 merge 跳过逻辑
3. 修改 `archive.py` 的参数注册与清理跳过逻辑

**Verify**: `python -m pytest tests/python/unit/` 全量通过 (GREEN)

**Done**: 脚本逻辑实现完毕并通过全部单元测试
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: 技能文档与指令规范更新（遵循 skill-creator 规范）

**Verification Intent**: AC#5

**Behavior**:
严格遵循 `skill-creator` 技能的指令编写与文档优化规范，在技能文档中清晰规范三种 approve 模式（标准 / main直实施 / 独立分支演进模式）的判定条件与对应命令序列，给出防错铁律与场景化指引。

**Files**:
- `.wopal/skills/dev-flow/SKILL.md`
- `.wopal/skills/dev-flow/references/commands.md`

**Pre-read**: 
- `.wopal/skills/skill-creator/SKILL.md`（技能编写原则：渐进式披露、解释 Why、防错边界、避免无脑堆参数、理论心智模型）
- `.wopal/skills/dev-flow/SKILL.md`

**Design**:
根据 `skill-creator` 技能规范优化 `dev-flow` 技能定义：
1. **渐进式披露与结构控制**：保持 `SKILL.md` 主干精炼（不超过 500 行限制），将详尽命令参数和边缘场景下沉至 `references/commands.md`。
2. **场景驱动与 Theory of Mind**：在 `SKILL.md` 中新增「Approve 模式选择（用户评审指令判定）」章节，从 Agent 接收用户审批信号的心智模型出发，详细阐述用户触发词、模式区别、对应命令链和严禁项（解释背后的原因而非单纯的硬性禁令）。
3. **精准消除歧义**：明确区分 `--no-worktree`（main 直接实施）与 `--existing-worktree`（独立分支演进），防止 Agent 产生误操作。

**TDD**: false

**Changes**:
1. 依照 `skill-creator` 准则更新 `SKILL.md`：增加用户评审指令判定模式表、命令链和易错对照表。
2. 更新 `references/commands.md`：详细描述 `--existing-worktree` 与 `--keep-worktree` 参数、设计背景与使用示例。

**Verify**: `bash scripts/flow.sh plan check feature-dev-flow-support-existing-worktree-evolution-mode-without-merge` 校验通过

**Done**: 遵循 skill-creator 规范更新技能文档和命令参考完毕
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: `issue list` 命令 (TDD)

**Verification Intent**: AC#6

**Behavior**:
- `flow.sh issue list` 调用 `detect_space_repo` 自动定位空间仓库，列出未完成 issue。
- 支持 `--project <name>` 与 `--status <planning|executing|verifying|done>` 过滤（均可多次指定）：project 与 status 之间为 AND，同类型多个为 OR。
- 输出格式：每行显示 issue 号、标题、labels 和所在 repo URL（`https://github.com/<owner>/<repo>`）。
- 无法检测空间仓库或 `gh` 不可用时，输出清晰错误信息并返回 1。
- 通过 `lib/github.py` 的受控 wrapper 调用 gh，JSON 解析（不依赖管道分隔），gh 缺失时不 traceback。
- `plan list --issue` 行为保持不变。

**Files**:
- `.wopal/skills/dev-flow/scripts/commands/issue.py`
- `.wopal/skills/dev-flow/scripts/lib/github.py`
- `.wopal/skills/dev-flow/scripts/flow.py`
- `.wopal/skills/dev-flow/tests/python/unit/test_issue_list.py`
- `.wopal/skills/dev-flow/tests/fixtures/github/`（gh issue list JSON 样本）
- `.wopal/skills/dev-flow/SKILL.md`
- `.wopal/skills/dev-flow/references/commands.md`
- `.wopal/skills/dev-flow/references/issue-guide.md`

**Pre-read**:
- `.wopal/skills/dev-flow/scripts/lib/workspace.py`（`detect_space_repo`）
- `.wopal/skills/dev-flow/scripts/lib/github.py`（受控 wrapper 约定）
- `.wopal/skills/dev-flow/tests/python/unit/test_issue_body_file.py`（现有测试约定）
- `.wopal/skills/dev-flow/AGENTS.md` §5（TDD 六条硬规则 R1-R6）

**Design**:
- `github.py` 新增 `list_issues(repo, state, projects, statuses, limit) -> list[dict] | None`：受控 subprocess 调用 gh，捕获 `FileNotFoundError` 返回 None；用 `--search` 构建过滤查询（多 project 用 OR、多 status 用 OR，project 与 status 之间 AND）；`--json` 输出经 `json.loads` 解析为 dict list。
- `issue.py` 新增 `cmd_issue_list(args)`：调用 `find_workspace_root()` + `detect_space_repo()`；解析 `--project`（list）与 `--status`（list，映射到 status 标签）；调用 `list_issues` 并格式化打印；失败时 `log_error` 返回 1。
- status 标签映射：`planning→status/planning`、`executing|in-progress→status/in-progress`、`verifying→status/verifying`、`done→status/done`。
- 注册 `issue list` 子命令（`--project` append、`--status` append、`--limit` 默认 50）。
- `flow.py` help 文本新增 `issue list` 行。
- 文档更新：`SKILL.md` 命令速查、`commands.md` `issue list` 参数说明与示例、`issue-guide.md` 查询说明。

**TDD**: true

**Changes**:
1. 新增 `tests/fixtures/github/issue-list-*.json` 真实样本（成功/空/含分隔符）
2. 新增 `test_issue_list.py`：成功列出（默认/按 project/按 status 过滤）、空结果、gh 失败返回 1、repo 检测失败返回 1（用 `argparse.Namespace` 传参）
3. `github.py` 实现 `list_issues` wrapper
4. `issue.py` 实现 `cmd_issue_list` + 注册 `list` 子命令
5. `flow.py` help 文本更新
6. `SKILL.md` / `commands.md` / `issue-guide.md` 文档更新

**Verify**: `python -m pytest tests/python/unit/test_issue_list.py` 通过 (GREEN)；`python -m pytest tests/python/` 全量通过

**Done**: `issue list` 命令实现完毕（含过滤与 JSON 解析）并通过单元测试与文档更新
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.
