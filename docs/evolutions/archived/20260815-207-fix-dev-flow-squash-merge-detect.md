# 207-fix-dev-flow-squash-merge-detect

## Metadata

- **Issue**: #207
- **Type**: fix
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-08-15
- **Status**: done
- **Verification Commit**: c7f23e3771bc0febe84744a98731ab21554bc78b
- **Worktree**:
  - branch: wopal-space-ontology-207-fix-dev-flow-squash-merge-detect
  - path: /Volumes/U500G/coding/wopal-workspace/.worktrees/wopal-space-ontology-207-fix-dev-flow-squash-merge-detect
- **Base Commit**: 25c20031082d459c5a04b690f9e3f28244010bd1
- **Final Commit**: c7f23e3771bc0febe84744a98731ab21554bc78b

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

修复 `flow.sh verify --confirm` 的 feature 分支合并检测（`scripts/lib/git.py` 的 `check_branch_merged`）无法识别「squash 合并后 main 又独立演进」场景的问题，使已合并的 Plan 能正确推进到 `done`；同时澄清 dev-flow SKILL.md 中 merge 授权门，避免 agent 把"agent 操作"误读为"agent 可自主执行"。

## Technical Context

### Architecture Context

`check_branch_merged`（`scripts/lib/git.py:521`）在 `verify --confirm` 时判断 feature 分支是否已合入集成分支，四级判定：

| 判据 | 失败原因（squash 合并后 main 又演进） |
|------|------|
| L1 Verification Commit 祖先检测 | squash 合并后 feature tip 永远不会成为 main 祖先 |
| L2 tree 相等判据 | main 合并后又演进，tree 与 feature 不等 |
| L3 changeset 字节一致判据 | feature 改动的文件在 main 上被后续修复修改，字节不一致 |
| L4 branch --merged | squash 无 merge commit，message 无分支名 |

设计假设是「merge 后 main 不再有 feature 涉及文件的新提交」，但「squash 合并 → 用户在 main 验证 → 修复直接提交 main」是正常合理流程。L3 的 `git diff --quiet integration feature -- path` 要求字节级一致，main 演进后必然失败。

SKILL.md 中"谁执行动作"与"谁授权动作"两个维度混在同一表述里（如"Agent 唯一的分支操作是 merge"），导致 agent 把"agent 操作"误读为"agent 可自主执行"，2026-08-14 曾发生用户说"提交吧"后 agent 擅自 `merge --squash` 的事件。

### Key Decisions

- D-01: 增强 L3 changeset 判据——当 feature 改动的文件在 main 上被后续修改时，不要求字节级一致，改为检查 **feature 相对 base 的改动 blob 是否已包含在 main 历史中**（main 是 feature 的超集）。用 `git log <integration> --find-object=<feature_blob>` 检测 feature 的 blob 是否进入过 integration 历史。
- D-02: 合并 #206 的 4 点文档修改到本 Plan，关闭 #206 并注明内容已合并。以 #207 为主 Issue。

### Key Interfaces

`check_branch_merged(workspace_root: Path, plan_path: str) -> int`：返回 0 表示已合并，1 表示未合并或出错。增强仅作用于 L3 内部，接口签名不变。

## In Scope

- 增强 `check_branch_merged` 的 L3 changeset 判据，识别「squash 合并后 main 又演进」场景
- 未合并的 feature 分支仍被正确拒绝（不误放行）
- 现有 dev-flow 测试全部通过
- SKILL.md 提交序列表第 7 步 merge 行加授权门前置
- 修正"Agent 唯一的分支操作是 merge"表述
- 场景 3 加归属声明
- "不要这样做"补一条 merge 授权相关条目

## Out of Scope

- 不引入"用户指令边界"映射表（#206 备注明确不采纳）
- 不改变 `check_branch_merged` 的接口签名与返回语义
- 不修改其他 dev-flow 命令逻辑

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dev-flow 脚本 | `.wopal/skills/dev-flow/scripts/lib/git.py` | 修改 | 增强 L3 changeset 判据 |
| dev-flow 测试 | `.wopal/skills/dev-flow/tests/python/unit/test_git_semantics.py` | 修改 | 新增/调整 check_branch_merged 测试 |
| dev-flow 技能 | `.wopal/skills/dev-flow/SKILL.md` | 修改 | merge 授权门文档澄清 |

## Acceptance Criteria

### Agent Verification

1. [x] `python -m pytest tests/python/unit/test_git_semantics.py -v` 全部 pass
2. [x] `python -m pytest tests/python/ -v` 全部 pass（无回归）
3. [x] `rg -n "前置：用户已明确确认验证通过" .wopal/skills/dev-flow/SKILL.md` 命中 ≥ 1
4. [x] `rg -n "Agent 唯一的分支操作是 merge，且必须在用户明确授权之后执行" .wopal/skills/dev-flow/SKILL.md` 命中 ≥ 1
5. [x] `rg -n "agent 不得自行决定走场景 3" .wopal/skills/dev-flow/SKILL.md` 命中 ≥ 1
6. [x] `rg -n "每个状态机推进动作（merge/verify/archive）都需要独立明确指令" .wopal/skills/dev-flow/SKILL.md` 命中 ≥ 1

### User Validation

#### Scenario 1: squash 合并后 main 演进，verify 能推进到 done
- Goal: 确认复现场景下 `flow.sh verify --confirm` 能识别已合并并推进到 done
- Precondition: 一个 Plan 处于 verifying 状态，feature 分支已 squash 合入 main，且 main 在 feature 涉及文件上又有后续提交
- User Actions:
  1. 构造上述 git 场景（或使用测试覆盖）
  2. 执行 `flow.sh verify --confirm`
  3. 观察是否报错 `Feature branch not yet merged to main`
- Expected Result: verify 正确识别已合并，Plan 推进到 done，不报错

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 增强 L3 changeset 判据识别 squash 合并后 main 演进

**Verification Intent**: AC#1, AC#2

**Behavior**: 当 feature 改动的文件在 integration 上被后续修改（字节不一致）时，`check_branch_merged` 应检查 feature 相对 base 的改动 blob 是否已进入 integration 历史；若每个改动路径的 feature blob 都存在于 integration 历史中，则判定已合并返回 0；否则返回 1。

**Files**: `.wopal/skills/dev-flow/scripts/lib/git.py`, `.wopal/skills/dev-flow/tests/python/unit/test_git_semantics.py`

**Pre-read**: `.wopal/skills/dev-flow/scripts/lib/git.py:521-716`, `.wopal/skills/dev-flow/tests/python/unit/test_git_semantics.py:1281-1375`

**Design**:
现有 L3 对每个 feature 改动路径执行 `git diff --quiet integration feature -- path`，要求字节级一致。main 演进后该命令返回非 0，导致误判未合并。

增强方案：对每个改动路径，先尝试字节一致判据；失败时回退到 blob 存在性判据——检查 feature 在该路径的 blob 是否进入过 integration 历史：

```
feature_blob = git rev-parse <feature>:<path>          # feature 版本 blob SHA
git log <integration> --find-object=<feature_blob> --oneline -- <path>   # 非空 = blob 在 integration 历史中
```

`git log --find-object=<object> -- <path>` 会列出 integration 历史中改变该 object 出现次数的提交。squash 合入时 feature 的 blob 被引入 main，即使 main 后续又修改该文件，feature 的 blob 仍存在于 integration 历史中，因此能正确识别已合并。未合并时 feature blob 从未进入 integration，`--find-object` 返回空，正确拒绝。pathspec 限定该路径，避免跨路径对象计数干扰，同时缩减遍历范围。

该判据经过真实 git 实验验证：squash 合并 + main 演进场景正确命中；未合并场景返回空正确拒绝；带 pathspec 与不带结果一致。

实现要点：
- 保持现有 L1/L2/L4 判据不变，仅增强 L3 内部
- L3 对每个改动路径：先 `git diff --quiet`，非 0 时再走 blob 存在性兜底
- 删除文件边界：`git rev-parse <feature>:<path>` 失败（feature 中该路径不存在）时，用 `git cat-file -e <integration>:<path>` 检查——integration 中也不存在 = 删除已被吸收，判该路径已合并；integration 中仍存在 = 判未合并
- 所有路径都判定已合并才返回 0
- 保持接口签名不变
- 注释说明固有假阳性边界：main 独立演化出与 feature 完全相同的 blob 时（内容相同 = 同一对象），git 内容寻址无法区分"合并引入"与"独立写出"，该巧合场景判已合并。此局限在实务中可接受（verify 前有用户验证门控，且概率极低）

**TDD**: true

**Changes**:
1. 在 `check_branch_merged` 的 L3 changeset 判据中，对每个改动路径增加 blob 存在性兜底：`git diff --quiet` 失败时，用 `git rev-parse <feature>:<path>` 取 feature blob，再用 `git log <integration> --find-object=<blob> --oneline -- <path>` 判断 blob 是否在 integration 历史中
2. 在 L3 中处理删除文件边界：`git rev-parse <feature>:<path>` 失败时，用 `git cat-file -e <integration>:<path>` 判断删除是否已被吸收
3. 在 `test_git_semantics.py` 新增测试：squash 合并后 main 演进（字节不一致但 feature blob 在 integration 历史）→ 返回 0
4. 在 `test_git_semantics.py` 新增测试：feature blob 不在 integration 历史 → 返回 1（不误放行）
5. 在 `test_git_semantics.py` 新增测试：feature 删除文件且 integration 也已删除 → 返回 0；feature 删除文件但 integration 仍存在 → 返回 1

**Verify**:
`python -m pytest tests/python/unit/test_git_semantics.py -v`

**Done**:
任务产出：L3 判据增强 + 对应 TDD 测试，全部通过。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: SKILL.md merge 授权门文档澄清

**Verification Intent**: AC#3, AC#4, AC#5, AC#6

**Behavior**: SKILL.md 中 merge 相关表述明确区分"谁执行动作"与"谁授权动作"，agent 不得把"agent 操作"误读为"agent 可自主执行"。

**Files**: `.wopal/skills/dev-flow/SKILL.md`

**Pre-read**: `.wopal/skills/dev-flow/SKILL.md:92-106, 237-256, 358-378`

**Design**:
按 #206 的 4 点最小修改方案执行：

1. **提交序列表加授权门前置**（第 103 行）：第 7 步 merge 行加 `⚠️ 前置：用户已明确确认验证通过（或用户选择场景 3）`；第 6 步验证行标为"用户操作+用户授权"。
2. **修正"Agent 唯一的分支操作是 merge"**（第 250 行）：改为"Agent 唯一的分支操作是 merge，且必须在用户明确授权之后执行"。
3. **场景 3 加归属声明**（第 237-240 行）："先合并后验证"是用户可选的验证方式，agent 不得自行决定走场景 3；用户未表态时默认等验证通过后再 merge。
4. **"不要这样做"补一条**（第 358 行区域）：把"提交吧"解读为"完成整个收尾流程"——每个状态机推进动作（merge/verify/archive）都需要独立明确指令。

**TDD**: false

**Changes**:
1. 提交序列表第 7 步 merge 行加 `⚠️ 前置：用户已明确确认验证通过（或用户选择场景 3）`；第 6 步验证行标注"用户操作+用户授权"
2. 分支生命周期铁律第 250 行改为"Agent 唯一的分支操作是 merge，且必须在用户明确授权之后执行"
3. 场景 3 加归属声明：agent 不得自行决定走场景 3，用户未表态时默认等验证通过后再 merge
4. "不要这样做"补一条：把"提交吧"解读为"完成整个收尾流程"，每个状态机推进动作（merge/verify/archive）都需要独立明确指令

**Verify**:
`rg -n "前置：用户已明确确认验证通过" .wopal/skills/dev-flow/SKILL.md` ≥ 1

**Done**:
任务产出：SKILL.md 4 点 merge 授权门文档修改完成。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 代码 + TDD 测试，需实施 |
| 1 | Task 2 | fae | 无 | 文档修改，与 Task 1 无依赖，可并行 |
