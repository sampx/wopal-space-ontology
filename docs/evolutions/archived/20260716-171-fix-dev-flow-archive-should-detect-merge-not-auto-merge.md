# 171-fix-dev-flow-archive-should-detect-merge-not-auto-merge

## Metadata

- **Issue**: #171
- **Type**: fix
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-07-16
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

修复 `archive` 命令三个 bug，并优化 dev-flow 技能文档中的流程规则。

## Technical Context

### Architecture Context

`archive` 命令位于 `scripts/commands/archive.py`，负责 Plan 归档流程的最后一步。当前存在三个代码 bug 和若干文档不一致问题。

**Bug 1 — archive 自动 merge**：`archive.py:618` 在检测到 worktree 存在且非 PR 路径时，调用 `_merge_worktree_branch` → `merge_branch(..., target='main', no_ff=True)` 执行自动 merge。这与 SKILL.md 铁律"脚本永远不碰代码"矛盾——merge 是 agent 的职责，archive 只应检测合并状态。`verify.py:166` 已有 `_check_feature_branch_merged` 函数实现合并检测逻辑，可提取复用。

**Bug 2 — worktree 删除失败无诊断**：`remove_worktree`（`lib/worktree.py:505`）在 `--force` 失败时抛出 `RuntimeError`，但 `clean_worktree` 以泛型 `Exception` 捕获，stderr 信息丢失，用户得不到可操作指引。

**Bug 3 — `_is_pr_path` 缺少 `--repo`**：`archive.py:219-228` 的 `_is_pr_path` 函数调用 `gh issue view` 时未传 `--repo`。`gh` CLI 不带 `--repo` 时用当前工作目录的 git remote 确定仓库，若 agent 在非 workspace 根目录执行 archive，会解析到错误仓库。dev-flow 其他 13 处 `gh issue` 调用都带了 `--repo`，唯独此处遗漏。

**文档优化**：
1. SKILL.md 铁律"脚本永远不碰代码"需要细化——区分"项目代码操作"（merge、commit 实施代码）与"基础设施操作"（worktree 创建/清理、分支创建/删除）。worktree 和分支是 dev-flow 创建的基础设施，理应由 dev-flow 管理生命周期。
2. fix 类型 Plan 通常方案简单明确，强制 rook plan review 增加流程摩擦。应允许跳过，复杂方案征求用户同意后再审。
3. `reviewing` 状态应允许修订 Plan，无需先 reset 到 `planning`。

### Key Decisions

- D-01: 将 `_check_feature_branch_merged` 从 `verify.py` 提取到 `lib/git.py` 作为公共函数 `check_branch_merged`，供 `archive.py` 和 `verify.py` 共用
- D-02: archive 中 worktree 存在 + 非 PR 路径时，调用 `check_branch_merged` 检测合并状态，未合并报错退出，已合并跳过 merge 直接进入清理
- D-03: `remove_worktree` `--force` 失败时，在 `RuntimeError` 消息中包含 stderr 输出 + 可操作指引
- D-04: SKILL.md 铁律从"脚本永远不碰代码"细化为"脚本不操作项目代码（merge、commit 实施代码），但管理自身创建的基础设施（worktree、feature 分支）"
- D-05: fix 类型 Plan 默认跳过 rook plan review；复杂方案提交前征求用户同意
- D-06: `reviewing` 状态允许直接修订 Plan，无需 reset

## In Scope

- Bug 1: 将 `archive.py` 的 `_merge_worktree_branch` 调用替换为合并检测，删除死代码
- Bug 2: 增强 `remove_worktree` 的错误信息，输出诊断和指引
- Bug 3: `_is_pr_path` 补上 `--repo` 参数
- 提取 `_check_feature_branch_merged` 到 `lib/git.py` 作为公共函数
- SKILL.md 文档更新：细化铁律、fix 类型跳过 rook review、reviewing 状态可修订

## Out of Scope

- ontology-worktree 类型的 archive 流程（走 `line 577-579` 分支，不受影响）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| archive 命令 | `scripts/commands/archive.py` | 修改 | Bug 1+3：替换 merge 为检测，补 --repo |
| verify 命令 | `scripts/commands/verify.py` | 修改 | 改用 lib/git.py 的公共函数 |
| git 库 | `scripts/lib/git.py` | 修改 | 新增 `check_branch_merged` 公共函数 |
| worktree 库 | `scripts/lib/worktree.py` | 修改 | Bug 2：增强错误信息 |
| 技能文档 | `SKILL.md` | 修改 | 细化铁律、优化流程规则 |
| 单元测试 | `tests/python/unit/test_archive.py` | 修改 | 新增合并检测场景测试 |
| 单元测试 | `tests/python/unit/test_worktree_context.py` | 修改 | 新增 force 失败诊断测试 |

## Acceptance Criteria

### Agent Verification

1. [x] `python -m pytest tests/python/unit/test_archive.py -v` 全部 pass
2. [x] `python -m pytest tests/python/unit/test_worktree_context.py -v` 全部 pass
3. [x] `python -m pytest tests/python/ -v` 全部 pass（无回归）
4. [x] `rg 'from lib.git import merge_branch' .wopal/skills/dev-flow/scripts/commands/archive.py` 无匹配
5. [x] `rg 'def check_branch_merged' .wopal/skills/dev-flow/scripts/lib/git.py` 有匹配
6. [x] `rg '\-\-repo' .wopal/skills/dev-flow/scripts/commands/archive.py` 匹配数 = 2（`_is_pr_path` 已有 `--repo`，Bug 3 预先已修复）

### User Validation

#### Scenario 1: archive 在未合并时报错退出
- Goal: 确认 archive 不再自动 merge，未合并时给出明确错误
- Precondition: 一个 Plan 处于 `done` 状态，feature 分支存在但未合并到 main
- User Actions:
  1. 执行 `flow.sh archive <issue>`
  2. 观察输出
- Expected Result: 脚本报错退出，提示"feature branch not yet merged"，不执行 merge

#### Scenario 2: archive 在已合并时正常归档
- Goal: 确认 archive 在已合并时正常完成归档
- Precondition: 一个 Plan 处于 `done` 状态，feature 分支已合并到 main
- User Actions:
  1. 执行 `flow.sh archive <issue>`
  2. 观察输出
- Expected Result: 脚本正常完成归档，清理 worktree 和分支

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 提取 check_branch_merged 到 lib/git.py

**Verification Intent**: AC#3, AC#5

**Behavior**: `lib/git.py` 新增 `check_branch_merged` 公共函数，接受 workspace_root、plan_path 参数，返回 0（已合并）或 1（未合并）。逻辑与 `verify.py:_check_feature_branch_merged` 完全一致：SHA 祖先检测 → branch ref 检测 → git log fallback。

**Files**: `scripts/lib/git.py`, `scripts/commands/verify.py`

**Pre-read**: `scripts/commands/verify.py:166-291`, `scripts/lib/git.py:1-50`

**Design**:
1. 在 `lib/git.py` 新增 `check_branch_merged(workspace_root: Path, plan_path: str) -> int` 函数
2. 将 `verify.py:_check_feature_branch_merged` 的完整逻辑迁移到新函数
3. `verify.py` 的 `_check_feature_branch_merged` 改为调用 `lib/git.py` 的 `check_branch_merged`

**TDD**: true

**Changes**:
1. `lib/git.py`：新增 `check_branch_merged` 函数，包含完整合并检测逻辑
2. `verify.py`：`_check_feature_branch_merged` 改为委托给 `lib/git.py:check_branch_merged`

**Verify**:
`rg 'def check_branch_merged' scripts/lib/git.py` ≥ 1 && `python -m pytest tests/python/ -v` 全部 pass

**Done**:
任务产出：`lib/git.py` 新增 `check_branch_merged` 公共函数，`verify.py` 改用公共函数
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: archive 替换 merge 为合并检测 + 补 --repo（Bug 1 + Bug 3）

**Verification Intent**: AC#1, AC#4, AC#6

**Behavior**: `archive.py` 在 worktree 存在 + 非 PR 路径时，调用 `check_branch_merged` 检测合并状态。四种场景：(1) worktree 存在+已合并 → 跳过 merge，直接清理；(2) worktree 存在+未合并 → 报错退出；(3) worktree 不存在 → 跳过 merge，清理分支；(4) PR 路径 → 跳过 merge，清理 worktree。删除 `_merge_worktree_branch` 函数定义。`_is_pr_path` 补上 `--repo` 参数。

**Files**: `scripts/commands/archive.py`

**Pre-read**: `scripts/commands/archive.py:208-270, 577-640`，Task 1 完成后的 `lib/git.py`

**Design**:
1. 在 `archive.py` 中 import `check_branch_merged` from `lib.git`，移除 `merge_branch` import
2. 将 `line 612-629` 的 merge 逻辑替换为 `check_branch_merged` 检测
3. 删除 `_merge_worktree_branch` 函数定义（无其他调用方）
4. `_is_pr_path`（line 219-228）补上 `--repo` 参数

**TDD**: true

**Changes**:
1. `archive.py`：import `check_branch_merged`，移除 `merge_branch` import
2. `archive.py:612-629`：替换 merge 调用为 `check_branch_merged` 检测
3. `archive.py`：删除 `_merge_worktree_branch` 函数定义
4. `archive.py:219-228`：`_is_pr_path` 补上 `--repo` 参数

**Verify**:
`python -m pytest tests/python/unit/test_archive.py -v` 全部 pass

**Done**:
任务产出：archive 不再执行自动 merge，改为合并检测；`_is_pr_path` 补上 `--repo`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: 增强 remove_worktree 错误诊断（Bug 2）

**Verification Intent**: AC#2

**Behavior**: `remove_worktree` 在 `--force` 失败时，`RuntimeError` 消息包含：stderr 原文 + 诊断提示（检查占用进程、手动 trash 路径）+ 可操作命令。

**Files**: `scripts/lib/worktree.py`

**Pre-read**: `scripts/lib/worktree.py:505-551`

**Design**:
1. 在 `remove_worktree` 的 `--force` 失败分支（line 540-543），增强 `RuntimeError` 消息：
   - 包含 `result.stderr.strip()` 原文
   - 追加诊断提示：常见原因（进程占用、大量未跟踪文件）+ 建议操作（`lsof +D <path>` 检查占用、`trash <path>` 手动删除）

**TDD**: true

**Changes**:
1. `worktree.py:540-543`：增强 `RuntimeError` 消息，包含 stderr + 诊断指引

**Verify**:
`python -m pytest tests/python/unit/test_worktree_context.py -v` 全部 pass

**Done**:
任务产出：`remove_worktree` 失败时输出可操作的诊断信息
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: SKILL.md 文档更新

**Verification Intent**: 文档一致性

**Behavior**: 更新 SKILL.md 三处规则，使其与代码行为一致并优化流程。

**Files**: `SKILL.md`

**Pre-read**: `SKILL.md:1-372`

**Design**:
1. **细化铁律**（"脚本永远不碰代码"章节）：区分"项目代码操作"与"基础设施操作"。worktree 创建/清理、feature 分支创建/删除是 dev-flow 管理的基础设施，由脚本负责。merge、commit 实施代码是 agent 职责。删除 `_merge_worktree_branch` 后，archive 不再执行任何项目代码操作。
2. **fix 类型跳过 rook plan review**（"Plan 审查与提交"章节）：fix 类型 Plan 默认跳过 rook plan review。若方案复杂需审查，提交前征求用户同意。Plan 处于 `reviewing` 状态时可直接修订，无需先 reset 到 `planning`。
3. **reviewing 状态可修订**（"状态机"或"不要这样做"章节）：`reviewing` 状态的 Plan 可直接修订内容，无需 `flow.sh reset` 回退到 `planning`。修订后重新 `submit` 即可。

**TDD**: false（文档变更，无代码逻辑）

**Changes**:
1. SKILL.md 铁律章节：细化"脚本不碰代码"为"脚本不操作项目代码，但管理自身基础设施"
2. SKILL.md Plan 审查章节：fix 类型跳过 rook review，复杂方案征求用户同意
3. SKILL.md 状态机/禁止事项章节：reviewing 状态可修订 Plan

**Verify**:
人工审阅 SKILL.md 变更内容

**Done**:
任务产出：SKILL.md 三处规则更新，与代码行为一致
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 提取公共函数，Task 2 的前置依赖 |
| 2 | Task 2 | fae | Task 1 | 依赖 Task 1 的 `check_branch_merged` |
| 2 | Task 3 | fae | 无 | 独立修改 worktree 错误处理，可与 Task 2 并行 |
| 3 | Task 4 | Wopal | Task 1-3 | 文档更新需等代码变更确定后编写，确保一致性 |
