# refactor-dev-flow-decouple-issue-title-from-plan-and-branch-naming

## Metadata

- **Issue**: #
- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-08-12
- **Status**: done
- **Verification Commit**: 887e7be7aa8df88a22bfa6febe3f981e803ac6bb
- **Worktree**:
  - branch: flow-decouple-issue-title-from-plan-and-branch-naming
  - path: (removed)
- **Verification Dir**: /Volumes/U500G/coding/wopal-workspace/.wopal
- **Base Commit**: f379bd528d6205ef4080e519461db85863e386fa
- **Final Commit**: 25c20031082d459c5a04b690f9e3f28244010bd1

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

解耦 Issue title、Plan name、Branch name 三者的命名链：Issue title 自由化（不再强制 `type(scope): description` 格式），Plan name 成为权威标识（type/scope/slug 由 Wopal 显式指定，不从 Issue title 派生），Branch name 从最终确定的 Plan name 派生（`<project>-<plan-name>`），并清理命名链中的实现不一致 bug 与技术债。

## Technical Context

### Architecture Context

dev-flow 当前存在一条强耦合的命名派生链：

```
Issue title (type(scope): description)
  → _title_to_slug → Plan slug
  → _extract_slug → Branch slug
```

三个产物各自为政，存在以下问题：

1. **Issue title 被强制格式约束**：`validate_issue_title` 强制 `type(scope): description` 且 scope 必填。但 Issue 是需求讨论载体，内容经常变化，标题随讨论演化。一旦 Plan 与 Issue 严格对应，调整 Issue 内容后标题就不合适了。
2. **type 词汇表两套**：`issue.py` 的 `VALID_TYPES` 用 `feat/fix/perf/...`，`plan.py` 的 `_PLAN_VALID_TYPES` 用 `feature/fix/refactor/...`。同一 type 在两处命名不同。
3. **两个 `_extract_slug` 实现不一致（真实 bug）**：
   - `approve.py:58` 用 `split('-')` 按位置跳过 issue/type/scope → 返回 `add-skills-remove-command`（**去掉 scope**）
   - `plan.py:595` 用正则只去 issue 和 type → 返回 `cli-add-skills-remove-command`（**保留 scope**）
   - 对同一 plan `42-feature-cli-add-skills-remove-command`，approve 生成 branch `issue-42-add-skills-remove-command`，plan status legacy fallback 生成 `issue-42-cli-add-skills-remove-command`，两者不一致。
4. **Branch 丢失 type+scope**：`issue-42-add-skills-remove-command` 无法映射回 Plan `42-feature-cli-add-skills-remove-command`。
5. **scope 含连字符时 approve.py 的 split 逻辑会错**：`validate_plan_name` 约束 scope 为 `[a-z0-9]+`（无连字符），approve.py 的 `split('-')` 按位置跳过是安全的，但这是隐式依赖。一旦 scope 允许连字符（如 `dev-flow`），split 会把 `dev-flow` 拆成 `dev` 和 `flow`，slug 提取就错了。plan.py 的正则版本则不受影响。
6. **no-Issue Plan 的 worktree 定位依赖 Issue number**：`archive.py` 的 `_detect_worktree` fallback 以 `get_plan_issue()` 为前提（`<project>-issue-<N>-*` glob）。无 Issue Plan 没有 Issue number，fallback 无法定位其 worktree，导致 archive 无法清理 feature branch。

### Key Decisions

- D-01: **Issue title 自由化**。保留宽松 type 前缀（用于 label 推断），去掉强制 scope。Issue 是需求讨论载体，标题不应被格式绑架。
- D-02: **Plan name 是权威标识**。保留 `<N>-<type>-<scope>-<slug>` 结构（issue number 前缀保留，作为 Issue↔Plan 关联锚点）。type/scope/slug 由 Wopal 在创建 Plan 时显式指定，**不再从 Issue title 派生**。approve 前可自由改名/改范围。
- D-03: **Branch 从 Plan name 派生**。`branch = <project>-<plan-name>`，如 `ellamaka-42-feature-cli-add-skills-remove-command`。approve 时从最终确定的 plan name 生成，严格对应。
- D-04: **worktree 目录直接 = branch**。branch 已含 project 前缀，worktree 目录不再重复 project 前缀（当前是 `<project>-<branch>`，会变成 `<project>-<project>-<plan-name>` 重复）。
- D-05: **统一 type 词汇表**。以 `labels.py` 的 `_TYPE_NORMALIZE_MAP` 为唯一权威，`issue.py` 的 `VALID_TYPES` 与 `plan.py` 的 `_PLAN_VALID_TYPES` 对齐到 canonical 值。
- D-06: **消除重复的 `_extract_slug`**。删除 `approve.py` 与 `plan.py` 中两份 `_extract_slug`，统一为一个从 plan name 派生 branch 的权威函数。由于 branch 直接 = `<project>-<plan-name>`（完整 plan name），不再需要提取 slug 再拼 branch。
- D-07: **worktree 定位不依赖 Issue number**。worktree 路径由完整 Plan name 派生，Issue 模式与 no-Issue 模式统一，archive fallback 不再以 `get_plan_issue()` 为前提。

### Key Interfaces

**命名契约（目标态）**：

| 产物 | 格式 | 示例 | 来源 |
|------|------|------|------|
| Issue title | 宽松 type 前缀（可选） | `feat: add skills remove command` | Wopal 自由编写 |
| Plan name | `<N>-<type>-<scope>-<slug>` | `42-feature-cli-add-skills-remove-command` | Wopal 显式指定 |
| Branch | `<project>-<plan-name>` | `ellamaka-42-feature-cli-add-skills-remove-command` | approve 时从 plan name 派生 |
| Worktree 目录 | `<branch>` | `.worktrees/ellamaka-42-feature-cli-add-skills-remove-command` | approve 时从 branch 派生 |

**type 词汇表（canonical）**：`feature, enhance, fix, perf, refactor, docs, test, chore`（来自 `labels.py`）。

**CLI 契约（Issue 模式创建 Plan）**：
```
flow.sh plan new <issue> --type <type> --scope <scope> --slug <slug>
```
三项必填，全部由 Wopal 显式指定，不从 Issue title 派生。

## In Scope

- Issue title 自由化：`validate_issue_title` 去掉强制 scope，保留宽松 type 前缀校验
- `issue create` 不再从 title 强制提取 scope，type 由 `--type` 显式指定
- Plan name 由 Wopal 显式指定：`_cmd_plan_new` 不再从 Issue title 派生 slug/type/scope，新增 `--slug` 参数
- Branch 命名统一：`<project>-<plan-name>`，删除两份 `_extract_slug`
- worktree 目录命名调整：直接 = branch，不依赖 Issue number
- 统一 type 词汇表
- 文档更新：`SKILL.md`、`references/issue-guide.md`、`references/plan-guide.md`、`templates/plan.md`
- 测试更新与新增（含 no-Issue 生命周期）

## Out of Scope

- 已归档 Plan 的历史命名迁移（历史文档不追溯）
- 状态机 `planning → reviewing → executing → verifying → done` 的调整
- `plan check` 脚本校验逻辑的调整（保留）
- 实施审查（complete 前 rook）流程的调整

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Issue 校验 | `scripts/issue.py` | 修改 | `validate_issue_title` 放宽，去掉强制 scope；`VALID_TYPES` 对齐 canonical |
| Issue 命令 | `scripts/commands/issue.py` | 修改 | `cmd_issue_create` 不再强制 scope，type 由 `--type` 指定 |
| Plan 命令 | `scripts/commands/plan.py` | 修改 | `_cmd_plan_new` 不再从 Issue title 派生；新增 `--slug`；删除 `_extract_slug` |
| Plan 命名 | `scripts/plan.py` | 修改 | `validate_plan_name`/`make_plan_name` 保持结构，`_PLAN_VALID_TYPES` 对齐 |
| Approve | `scripts/commands/approve.py` | 修改 | 删除 `_extract_slug`，branch 派生 `<project>-<plan-name>` |
| Worktree | `scripts/lib/worktree.py` | 修改 | worktree 目录直接 = branch |
| Archive | `scripts/commands/archive.py` | 修改 | `_detect_worktree` 由完整 Plan name 派生，不依赖 Issue number |
| 文档 | `SKILL.md`、`references/issue-guide.md`、`references/plan-guide.md`、`templates/plan.md` | 修改 | 命名契约更新 |
| 测试 | `tests/python/unit/test_issue_title.py`、`test_plan_naming.py`、`test_approve.py`、`test_worktree_context.py`、`test_archive.py`、`test_plan_cmd.py`、`tests/python/integration/test_no_issue_lifecycle.py` | 修改 | 适配新命名契约，新增 no-Issue 生命周期测试 |

## Acceptance Criteria

### Agent Verification

1. [x] `python -m pytest tests/python/ -v` 全部 pass
2. [x] `rg -c 'scope is mandatory|Scope is mandatory' scripts/issue.py` = 0（强制 scope 校验已移除）
3. [x] `rg -c 'issue-.*-.*-.*' scripts/commands/approve.py` = 0（旧 branch 格式已移除）
4. [x] `rg -c '_extract_slug' scripts/commands/approve.py scripts/commands/plan.py` = 0（两份 `_extract_slug` 已删除）
5. [x] `rg -c 'f"\{project_name\}-\{branch_slug\}"' scripts/lib/worktree.py` = 0（worktree 目录不再重复 project 前缀）
6. [x] `rg -c 'VALID_TYPES' scripts/issue.py` 存在且与 `labels.py` canonical 对齐
7. [x] `rg -c 'issue-<N>-<slug>|issue-\{issue_number\}-\{slug\}' scripts/` = 0（旧 branch 格式已移除）
8. [x] `rg -c 'get_plan_issue' scripts/commands/archive.py` = 0（archive fallback 不再依赖 Issue number）
9. [x] `rg -c '--slug' scripts/commands/plan.py` ≥ 1（`--slug` 参数已新增）

### User Validation

#### Scenario 1: 创建自由标题的 Issue
- Goal: 确认 Issue title 不再强制 `type(scope): description` 格式
- Precondition: dev-flow 脚本已更新
- User Actions:
  1. 运行 `flow.sh issue create --title "add skills remove command" --project ellamaka --type feat`
  2. 观察是否成功创建
- Expected Result: 创建成功，type label 正确设置，不要求 scope

#### Scenario 2: 创建 Plan 时显式指定命名
- Goal: 确认 Plan name 由 Wopal 显式指定，不从 Issue title 派生
- Precondition: 已创建自由标题的 Issue
- User Actions:
  1. 运行 `flow.sh plan new <issue> --type feature --scope cli --slug add-skills-remove-command`
  2. 观察 Plan name 是否使用显式指定的 type/scope/slug
- Expected Result: Plan name 为 `<N>-feature-cli-add-skills-remove-command`，slug 由 Wopal 指定

#### Scenario 3: approve 生成对应 branch
- Goal: 确认 branch 从 Plan name 派生为 `<project>-<plan-name>`
- Precondition: Plan 已创建并 submit
- User Actions:
  1. 运行 `flow.sh approve <plan> --confirm`
  2. 观察创建的 branch 名称
- Expected Result: branch 为 `<project>-<plan-name>`，如 `ellamaka-42-feature-cli-add-skills-remove-command`

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 统一 type 词汇表 + Issue title 自由化

**Verification Intent**: AC#1, AC#2, AC#6

**Behavior**: `issue.py` 的 `VALID_TYPES` 与 `plan.py` 的 `_PLAN_VALID_TYPES` 对齐到 `labels.py` 的 canonical 值。`validate_issue_title` 不再强制 `type(scope): description` 格式，保留宽松 type 前缀校验（可选，用于 label 推断），去掉强制 scope。`issue create` 不再从 title 强制提取 scope，type 由 `--type` 显式指定。

**Files**: `scripts/issue.py`, `scripts/commands/issue.py`, `scripts/plan.py`

**Pre-read**: `scripts/labels.py`, `scripts/issue.py`, `scripts/commands/issue.py`, `scripts/plan.py`

**Design**:
`labels.py` 的 `_TYPE_NORMALIZE_MAP` 是唯一权威 type 映射。统一后：
- `issue.py` 的 `VALID_TYPES` 改为 canonical 值（`feature, enhance, fix, perf, refactor, docs, test, chore`），与 `plan.py` 一致
- `validate_issue_title` 的 type 校验使用 canonical 值；`extract_type` 保留宽松解析（从 title 前缀提取原始 type），但校验时 normalize 到 canonical
- `validate_issue_title` 去掉强制 scope：title 可以是自由文本（如 `add skills remove command`）；如果 title 以 `type:` 或 `type(scope):` 开头，校验 type 合法，否则不强制
- 保留长度约束（description ≤ 50，总长 ≤ 72）和 ASCII 约束
- `cmd_issue_create` 中，type 由 `--type` 显式指定（已支持），不再从 title 强制推断 scope；scope 不再从 title 提取
- `plan.py` 的 `_PLAN_VALID_TYPES` 确认与 canonical 一致

**TDD**: true

**Changes**:
1. 修改 `scripts/issue.py` 的 `VALID_TYPES` 为 canonical 值
2. 修改 `validate_issue_title`：type 校验用 canonical 值，去掉强制 scope，保留宽松 type 前缀校验
3. 修改 `cmd_issue_create`：type 由 `--type` 指定，不再强制从 title 提取 scope
4. 确认 `scripts/plan.py` 的 `_PLAN_VALID_TYPES` 与 canonical 一致
5. 更新 `test_issue_title.py`：去掉强制 scope 的测试，新增自由标题测试，type 相关测试用 canonical 值

**Verify**:
`python -m pytest tests/python/unit/test_issue_title.py tests/python/unit/test_plan_naming.py tests/python/unit/test_issue_body_file.py -v` 全部 pass

**Done**:
任务产出：type 词汇表统一到 canonical 值，Issue title 自由化
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: Plan name 由 Wopal 显式指定

**Verification Intent**: AC#1, AC#7, AC#9

**Behavior**: `_cmd_plan_new` 不再从 Issue title 派生 slug/type/scope。Issue 模式下，type/scope/slug 由 Wopal 通过 `--type`、`--scope`、`--slug` 三项必填显式指定。无 Issue 模式保持现有逻辑（`--title --project --type --scope`）。

**Files**: `scripts/commands/plan.py`

**Pre-read**: `scripts/commands/plan.py`, `scripts/plan.py`

**Design**:
`_cmd_plan_new` 当前在 Issue 模式下从 title 提取 type/scope，并用 `_title_to_slug` 从 title 派生 slug。改为：
- Issue 模式下，`--type`、`--scope`、`--slug` 三项必填，全部由 Wopal 显式指定
- 新增 `--slug` 参数（Issue 模式必填）
- 不再强制 title 格式，不再从 title 提取 type/scope/slug
- `_title_to_slug` 保留（用于无 Issue 模式的宽松 slug 派生），但 Issue 模式下 slug 由 Wopal 指定
- 无 Issue 模式保持现有逻辑（`--title --project --type --scope`，slug 从 title 宽松派生）

**TDD**: true

**Changes**:
1. 修改 `_cmd_plan_new`：Issue 模式下 type/scope/slug 由 Wopal 显式指定，三项必填
2. 新增 `--slug` 参数支持（parser 注册 + help）
3. 更新 `test_plan_cmd.py` 中 Issue 模式创建 Plan 的测试，新增 `--slug` 必填校验测试

**Verify**:
`python -m pytest tests/python/unit/test_plan_cmd.py tests/python/unit/test_plan_naming.py -v` 全部 pass

**Done**:
任务产出：Plan name 由 Wopal 显式指定，不从 Issue title 派生
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: Branch 命名统一

**Verification Intent**: AC#1, AC#3, AC#4, AC#7

**Behavior**: Branch 从 Plan name 派生为 `<project>-<plan-name>`。删除 `approve.py` 与 `plan.py` 两份 `_extract_slug`，统一为一个从 plan name 派生 branch 的权威函数。旧格式 `issue-<N>-<slug>` 完全移除。

**Files**: `scripts/commands/approve.py`, `scripts/commands/plan.py`

**Pre-read**: `scripts/commands/approve.py`, `scripts/commands/plan.py`

**Design**:
- 删除 `approve.py` 与 `plan.py` 中两份 `_extract_slug`
- `approve.py` 的 branch 生成：`branch = f"{project}-{plan_name}"`（plan_name 为完整 plan name，含 issue number/type/scope/slug）
- `plan.py` legacy fallback：同样用 `f"{project}-{plan_name}"`，与 approve 一致
- 移除 `issue-<N>-<slug>` 旧格式
- 由于 branch 直接用完整 plan name，`_extract_slug` 的 split 逻辑问题（scope 含连字符）自然消除
- 新增参数化单元测试：断言 issue/no-Issue、含连字符 scope 的 Plan 都派生出唯一预期 branch

**TDD**: true

**Changes**:
1. 删除 `approve.py` 的 `_extract_slug`，branch 生成改为 `f"{project}-{plan_name}"`
2. 删除 `plan.py` 的 `_extract_slug`，legacy fallback 的 branch 生成与 approve 一致
3. 移除 `issue-<N>-<slug>` 旧格式
4. 新增参数化测试：issue/no-Issue、含连字符 scope 的 Plan 派生唯一预期 branch
5. 更新 `test_approve.py`、`test_plan_cmd.py` 中 branch 相关测试

**Verify**:
`python -m pytest tests/python/unit/test_approve.py tests/python/unit/test_plan_cmd.py -v` 全部 pass

**Done**:
任务产出：Branch 命名统一为 `<project>-<plan-name>`，两份 `_extract_slug` 已删除
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: worktree 目录命名调整（不依赖 Issue number）

**Verification Intent**: AC#1, AC#5, AC#8

**Behavior**: worktree 目录直接 = branch（不再重复 project 前缀），且由完整 Plan name 派生，不依赖 Issue number。Issue 模式与 no-Issue 模式统一。archive fallback 不再以 `get_plan_issue()` 为前提。

**Files**: `scripts/lib/worktree.py`, `scripts/commands/approve.py`, `scripts/commands/archive.py`

**Pre-read**: `scripts/lib/worktree.py`, `scripts/commands/approve.py`, `scripts/commands/archive.py`

**Design**:
- `create_worktree`：worktree 目录 = branch（branch 已含 project 前缀），不再加 project 前缀
- `approve.py` 的 worktree_path 预测逻辑：同步改为 = branch
- `archive.py` 的 `_detect_worktree`：由完整 Plan name 派生 worktree 路径，不依赖 `get_plan_issue()`；Issue 模式与 no-Issue 模式统一
- 新增 no-Issue 生命周期测试：no-Issue Plan 创建 → status fallback → archive cleanup 全链路
- 更新 `test_worktree_context.py`、`test_archive.py` 中 worktree 路径相关测试

**TDD**: true

**Changes**:
1. 修改 `create_worktree`：worktree 目录 = branch
2. 修改 `approve.py` worktree_path 预测逻辑
3. 修改 `archive.py` `_detect_worktree`：由完整 Plan name 派生，不依赖 Issue number
4. 新增 no-Issue 生命周期测试（创建 → status fallback → archive cleanup）
5. 更新 `test_worktree_context.py`、`test_archive.py`、`test_no_issue_lifecycle.py`

**Verify**:
`python -m pytest tests/python/unit/test_worktree_context.py tests/python/unit/test_archive.py tests/python/integration/test_no_issue_lifecycle.py -v` 全部 pass

**Done**:
任务产出：worktree 目录命名与 branch 一致，不依赖 Issue number
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 5: 文档更新

**Verification Intent**: AC#1

**Behavior**: 文档中的命名契约更新为新的解耦方案。`SKILL.md`、`references/issue-guide.md`、`references/plan-guide.md`、`templates/plan.md` 中的 Issue title 格式、Plan 命名、Branch 命名描述同步更新。

**Files**: `SKILL.md`, `references/issue-guide.md`, `references/plan-guide.md`, `templates/plan.md`

**Pre-read**: `SKILL.md`, `references/issue-guide.md`, `references/plan-guide.md`, `templates/plan.md`

**Design**:
- `references/issue-guide.md`：Issue title 格式改为宽松 type 前缀（可选），去掉强制 scope 描述
- `references/plan-guide.md`：Plan 命名说明更新，明确 type/scope/slug 由 Wopal 显式指定
- `SKILL.md`：命名契约相关描述更新
- `templates/plan.md`：如有命名相关注释更新

**TDD**: false

**Changes**:
1. 更新 `references/issue-guide.md` 的 Issue title 格式
2. 更新 `references/plan-guide.md` 的 Plan 命名说明
3. 更新 `SKILL.md` 的命名契约描述
4. 更新 `templates/plan.md` 相关注释

**Verify**:
`rg -c 'scope is mandatory|Scope is mandatory' references/issue-guide.md` = 0

**Done**:
任务产出：文档命名契约更新
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | type 词汇表统一 + Issue title 自由化，独立基础 |
| 2 | Task 2 | fae | Task 1 | Plan name 显式指定依赖 type 词汇表统一 |
| 3 | Task 3 | fae | Task 2 | Branch 命名依赖 Plan name 显式指定 |
| 4 | Task 4 | fae | Task 3 | worktree 目录依赖 branch 命名 |
| 4 | Task 5 | fae | Task 1-4 | 文档更新依赖所有代码变更 |
