# 110-feature-improve-plan-naming-and-validation-strategy

## Metadata

- **Issue**: #110
- **Type**: feature
- **Target Project**: ontology
- **Created**: 2026-04-16
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

优化 dev-flow 技能的 Plan 文件命名、用户验证筛选、委派策略规范、approve 自动 push、Agent 禁止代勾选规则强化等 5 个缺陷。

> **注**：缺陷 6（archive 后 Issue label 未更新）经调研已不存在，`close_issue` 函数已实现 `clear_all_flow_labels + ensure_issue_label "status/done"`，Issue #106 归档后 label 正确为 `status/done`。

## Technical Context

dev-flow 技能当前存在以下缺陷需要修复：

### 1. Plan 文件名缺少 scope 标识

**现状**：`plan.sh` 生成的文件名格式为 `<issue_number>-<type>-<slug>.md`，如 `96-chore-reorganize-root-scripts.md`。

**问题**：多模块空间中无法一眼识别方案针对哪个模块（如 wopal-plugin）。

**改进**：从 Issue title 的 `<scope>` 部分提取 scope 标识，嵌入文件名。同时强制要求 Issue title 必须包含 scope。

**目标格式**：
- Issue 格式：`<issue_number>-<type>-<scope>-<slug>.md`（scope 从 Issue title 提取）
- 无 Issue 格式：`<type>-<scope>-<slug>.md`（scope 从 `--title` 提取）

**示例**：
- Issue 标题 `feat(cli): add skills remove` → `42-feature-cli-add-skills-remove.md`
- 无 Issue 标题 `feat(cli): standalone feature` → `feature-cli-standalone-feature.md`

**强制约束**：
- Issue title 和 `--title` 格式必须遵循 `<type>(<scope>): <description>` 规范
- **scope 为必填项**，禁止 `type: description` 格式（无 scope）
- Agent 创建 Issue 时必须生成合理的 scope（对应项目模块名）

### 2. 用户验证用例设计不合理

**现状**：`templates/plan.md` 和 `SKILL.md` 中 User Validation 设计原则未明确排除自动化测试可验证项。

**问题**：Agent 会将"构建通过"、"单元测试通过"等自动化验证项写入 User Validation，浪费用户验证精力。

**改进**：
- 在 SKILL.md 中明确 User Validation 只聚焦必须人机协作的场景（最终 E2E 功能验证）
- 在 templates/plan.md 模板中强化排除原则

### 3. 委派策略缺失强制规范

**现状**：`templates/plan.md` 中 Delegation Strategy 为可选章节，质量参差不齐。

**问题**：复杂任务缺少委派策略会导致主 agent 上下文浪费、委派混乱。

**改进**：
- 在 SKILL.md 中添加强制要求：复杂任务必须按 fae-collab 技能规范编制委派策略
- 在 `check-doc.sh` 中添加检查：Task 数量 > 2 或 Complexity = High 时强制检查委派策略章节存在且非 N/A

### 4. approve --confirm 缺少自动 push

**现状**：`approve.sh` 只检查 Plan 文件是否已 push（第 113-133 行），不执行 push。

**问题**：审批通过后 Plan 文件可能未 push，Issue 链接无法打开。

**改进**：在 `approve --confirm` 状态推进成功后，检查 Plan 是否未 push，若未 push 则自动 push。

### 5. Agent 擅自代用户勾选 User Validation 最终确认 checkbox

**现状**：SKILL.md 和模板有"Agent 禁止代为勾选"规则，但不够醒目，Agent 仍会违反。

**问题**：Agent 代勾选 final confirmation checkbox = 严重失职，绕过用户验证门。

**改进**：
- 在 SKILL.md 的人类授权门章节使用 `<CRITICAL_RULE>` 级别强化禁令
- 在 `templates/plan.md` 的 User Validation 注释中使用 `<CRITICAL_RULE>` 强化
- 明确：Agent 代勾选属于严重失职，必须明确告知用户由用户勾选

> **缺陷 6 已不存在**：`close_issue` 函数（issue.sh:618-623）已实现 `clear_all_flow_labels + ensure_issue_label "status/done"`，归档后 Issue label 正确更新为 `status/done`。

## In Scope

- Plan 文件命名格式调整（加入 scope）
- User Validation 篮选原则强化
- 委派策略强制规范
- approve --confirm 自动 push
- Agent 禁止代勾选规则强化

> **已验证不存在**：archive 归档后 Issue label 更新（`close_issue` 已正确实现）

## Out of Scope

- 现有 Plan 文件批量迁移（可选后续任务）
- verify --confirm 脚本校验 checkbox 修改者（技术上难以实现，Git blame 不适用 Issue body）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Skill Doc | `projects/ontology/agents/wopal/skills/dev-flow/SKILL.md` | 修改 | 强化 User Validation 筛选原则、委派策略强制要求、Agent 禁止代勾选 `<CRITICAL_RULE>` |
| Plan Template | `projects/ontology/agents/wopal/skills/dev-flow/templates/plan.md` | 修改 | 强化 User Validation 注释、委派策略模板格式（引用 fae-collab） |
| Plan Command | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/plan.sh` | 修改 | 提取 scope 加入文件名，处理无 scope 边缘场景 |
| Approve Command | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/approve.sh` | 修改 | 移除阻断逻辑，改为自动 push |
| Check Doc Lib | `projects/ontology/agents/wopal/skills/dev-flow/lib/check-doc.sh` | 修改 | 添加委派策略强制检查、文件名验证支持 scope |
| Plan Lib | `projects/ontology/agents/wopal/skills/dev-flow/lib/plan.sh` | 修改 | 更新命名验证逻辑（支持 scope，兼容无 scope） |
| Issue Lib | `projects/ontology/agents/wopal/skills/dev-flow/lib/issue.sh` | 修改 | 添加 `extract_scope` helper |

## Implementation

### Task 1: 强化 User Validation 筛选原则和 Agent 禁止代勾选规则

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/SKILL.md`, `templates/plan.md`

**Changes**:
- [x] Step 1: 在 SKILL.md 的人类授权门章节添加 `<CRITICAL_RULE>` 块，强化 Agent 禁止代勾选 final confirmation checkbox
- [x] Step 2: 在 SKILL.md 的 Acceptance Criteria 分层章节 User Validation 设计原则中添加排除自动化测试可验证项的规则
- [x] Step 3: 在 SKILL.md 中添加委派策略强制要求章节（复杂任务必须按 fae-collab 规范编制）
- [x] Step 4: 在 `templates/plan.md` 的 User Validation 注释中使用 `<CRITICAL_RULE>` 强化禁令
- [x] Step 5: 在 `templates/plan.md` 的 Delegation Strategy 注释中引用 fae-collab 技能规范

**Verification**: 
- [x] Step 1: grep SKILL.md 确认 `<CRITICAL_RULE>` 块存在
- [x] Step 2: grep SKILL.md 确认 User Validation 排除自动化测试规则存在
- [x] Step 3: grep templates/plan.md 确认 `<CRITICAL_RULE>` 禁令存在

### Task 2: Plan 文件命名加入 scope 标识 + Issue title scope 强制

**Files**: `scripts/cmd/plan.sh`, `lib/plan.sh`, `lib/issue.sh`, `lib/check-doc.sh`, `SKILL.md`

**Changes**:
- [x] Step 1: 在 `lib/issue.sh` 中添加 `extract_scope` helper：从 title 提取 scope（正则 `^[a-z]+\(([^)]+)\):`）
- [x] Step 2: 在 `lib/issue.sh` 的 `validate_issue_title` 中将 scope 校验从可选改为必填：
  - 修改正则 `^[a-z]+(\([^)]+\))?:\s*.+$` 为 `^[a-z]+\([^)]+\):\s*.+$`（scope 括号不再可选）
  - 更新错误提示明确 scope 为必填
- [x] Step 3: 在 `cmd_plan` 函数中调用 `extract_scope`：
  - Issue 模式：`plan_name="${issue_number}-${plan_type}-${scope}-${slug}`
  - 无 Issue 模式：`plan_name="${plan_type}-${scope}-${slug}`（从 `--title` 提取 scope）
- [x] Step 4: 在 `lib/plan.sh` 的 `validate_plan_name` 中更新验证正则（两种格式均含 scope 段）
- [x] Step 5: 在 `lib/check-doc.sh` 的文件名验证中更新正则（支持 scope 段）
- [x] Step 6: 在 `SKILL.md` Issue 标题规范中：
  - 将 scope 规则从"可选"改为"**必选**"
  - 删除无 scope 的示例 `refactor: unify plan status management`
  - 添加 `<CRITICAL_RULE>` 强调 Agent 创建 Issue 时必须生成合理 scope（对应项目模块名）

**边缘场景**：
- Issue 标题有 scope（如 `feat(cli): add skills remove`）→ `${issue_number}-${type}-${scope}-${slug}.md`
- 无 Issue 模式（如 `--title "feat(cli): standalone feature"`）→ `${type}-${scope}-${slug}.md`
- Issue 标题或 `--title` 缺少 scope → `validate_issue_title` 拦截报错，阻断创建

**Verification**:
- [x] Step 1: `validate_issue_title "refactor: no scope title"` → 报错（scope 缺失）
- [x] Step 2: `validate_issue_title "feat(cli): valid scope"` → 通过
- [x] Step 3: 创建测试 Issue `feat(cli): test scope naming` → Plan 文件名 `<issue>-feature-cli-test-scope-naming.md`
- [x] Step 4: 无 Issue 模式 `--title "feat(plugin): standalone test" --type feature` → Plan 文件名 `feature-plugin-standalone-test.md`
- [x] Step 5: `flow.sh plan --check` 验证新命名格式通过检查

### Task 3: approve --confirm 自动 push

**Files**: `scripts/cmd/approve.sh`

**Changes**:
- [x] Step 0: 移除 approve.sh L122-130 的阻断逻辑（Plan 未 push 时 `exit 1`）
- [x] Step 1: 在 approve --confirm 状态推进成功后（Issue label 更新为 `status/executing` 后），检查 Plan 文件最后修改 commit 是否已 push
- [x] Step 2: 若未 push，执行 `git -C "$ROOT_DIR" push`，push 失败时 warning 但不阻断（状态已推进）
- [x] Step 3: 保留 L118-121 的安全检查（Plan 有未 commit 变更时阻断，此逻辑保留）

**Verification**:
- [x] Step 1: 本地 commit Plan 后执行 approve --confirm（Plan 未 push），验证自动 push 且状态推进成功
- [x] Step 2: 检查远程仓库 Plan 文件存在
- [x] Step 3: Plan 已 push 时执行 approve --confirm，验证无多余 push 操作

### Task 4: 委派策略强制检查

**Files**: `lib/check-doc.sh`

**Changes**:
- [x] Step 1: 在 `check_doc_plan` 中添加委派策略检查：Task 数量 > 2 或 Complexity = High 时强制检查 Delegation Strategy 章节存在且非 N/A
- [x] Step 2: 若缺失或为 N/A，报错阻断
- [x] Step 3: Complexity = High + Task ≤ 2 也触发检查（单独覆盖）

**Verification**:
- [x] Step 1: 创建多 Task（3+）Plan 且无委派策略，验证 check-doc 报错
- [x] Step 2: Complexity = High + Task ≤ 2 无委派策略，验证 check-doc 报错
- [x] Step 3: 添加委派策略后验证 check-doc 通过

## Delegation Strategy

<CRITICAL_RULE>

复杂任务（Task 数量 > 2 或 Complexity = High）必须按 fae-collab 技能规范编制委派策略。简单任务可填 N/A。

委派策略必须包含：
1. **批次划分**：无依赖的 Task 放同一批次并行执行
2. **执行者标明**：每个批次标明执行者（Wopal / fae）及理由
3. **验证边界**：明确哪些验证由 fae 完成，哪些由 Wopal 完成

参考：`.agents/skills/fae-collab/SKILL.md`

</CRITICAL_RULE>

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1（SKILL.md + templates） | Wopal | 无 |
| 1 | Task 2（Plan 命名） | Wopal | 无 |
| 1 | Task 4（check-doc 委派检查） | Wopal | 无 |
| 2 | Task 3（approve push） | Wopal | 无 |

**理由**：Task 1/2/4 是文档和脚本修改，无依赖可并行；Task 3 是 approve.sh 单点修改，可并行执行。所有 Task 粒度适中，无跨 Task 依赖。

**验证边界**：全部由 Wopal 完成（涉及技能核心逻辑修改，需主 agent 审慎验证）。

## Test Plan

#### Unit Tests

N/A — Shell 脚本修改，单元测试需集成测试覆盖。

#### Integration Tests

##### Case I1: Plan 文件命名包含 scope（Issue 模式）
- Goal: 验证 Issue 驱动 Plan 文件名包含 scope 标识
- Fixture: 创建测试 Issue `feat(cli): test scope naming`
- Execution:
  - [x] Step 1: `flow.sh plan <issue> --project ontology`
  - [x] Step 2: 验证生成的 Plan 文件名包含 `-cli-`
- Expected Evidence: Plan 文件名格式为 `<issue>-feature-cli-test-scope-naming.md`

##### Case I1.1: Plan 文件命名包含 scope（无 Issue 模式）
- Goal: 验证无 Issue 模式 Plan 文件名从 `--title` 提取 scope
- Fixture: 无 Issue，`--title "feat(plugin): standalone feature"`
- Execution:
  - [x] Step 1: `flow.sh plan --title "feat(plugin): standalone feature" --project ontology --type feature`
  - [x] Step 2: 验证生成的 Plan 文件名包含 `-plugin-`
- Expected Evidence: Plan 文件名格式为 `feature-plugin-standalone-feature.md`

##### Case I2: approve --confirm 后 Plan 已 push
- Goal: 验证 approve --confirm 后 Issue 包含 Plan 链接且 Plan 文件已 push
- Fixture: 已创建的 Plan（未 approve），Plan 已 commit 但未 push
- Execution:
  - [x] Step 1: 编写完整 Plan 并 commit
  - [x] Step 2: `flow.sh approve <issue> --confirm`
  - [x] Step 3: 验证 Issue body 包含 Plan 链接
  - [x] Step 4: 验证远程仓库 Plan 文件存在
- Expected Evidence: Issue Plan 链接可点击，远程 Plan 文件存在

##### Case I3: check-doc 对复杂任务强制检查委派策略（Task > 2）
- Goal: 验证 check-doc 对 Task > 2 的 Plan 强制检查委派策略
- Fixture: 创建 4 Task 的 Plan，无委派策略章节
- Execution:
  - [x] Step 1: `flow.sh plan --check`
  - [x] Step 2: 验证报错提示缺少委派策略
  - [x] Step 3: 添加委派策略后重新 check
- Expected Evidence: 无委派策略时 check-doc 报错，添加后通过

##### Case I4: check-doc 对复杂任务强制检查委派策略（Complexity = High）
- Goal: 验证 Complexity = High + Task ≤ 2 也触发委派策略检查
- Fixture: 创建 2 Task 的 Plan，Complexity = High，无委派策略章节
- Execution:
  - [x] Step 1: `flow.sh plan --check`
  - [x] Step 2: 验证报错提示缺少委派策略
  - [x] Step 3: 添加委派策略后重新 check
- Expected Evidence: 无委派策略时 check-doc 报错，添加后通过

#### E2E Tests

##### Case E1: 完整工作流验证 Plan 命名新特性
- Goal: 验证 Plan 命名（Issue 模式和无 Issue 模式）全流程
- Fixture: 创建测试 Issue `fix(plugin): test e2e scope flow` + 无 Issue 命令 `--title "feat(cli): standalone test"`
- Execution:
  - [x] Step 1: `flow.sh plan <issue> --project ontology`（验证文件名包含 `-plugin-`）
  - [x] Step 2: `flow.sh plan --title "feat(cli): standalone test" --project ontology --type feature`（验证文件名包含 `-cli-`）
  - [x] Step 3: 对 Issue 模式的 Plan 完整执行 approve → complete → verify → archive（验证流程无误）
- Expected Evidence: Issue 和无 Issue 模式均正确命名，archive 流程无异常

#### Regression Tests

##### Case R1: 现有 Plan 文件兼容性（无 scope 格式）
- Goal: 确认变更后现有无 scope 格式的 Plan 文件 check-doc 验证行为
- Fixture: `docs/products/ontology/plans/96-chore-reorganize-root-scripts.md`（无 scope 的旧格式文件）
- Execution:
  - [x] Step 1: `flow.sh plan 96 --check`（或直接对文件 check-doc）
  - [x] Step 2: 验证 check-doc 报错提示文件名格式不符合新规范（scope 缺失）
- Expected Evidence: 旧格式文件 check-doc 报错，提示需符合新命名规范（后续可批量迁移）

## Acceptance Criteria

### Agent Verification

- [x] SKILL.md 中 `<CRITICAL_RULE>` 块存在（禁止代勾选、委派策略强制）
- [x] templates/plan.md 中 `<CRITICAL_RULE>` 禁令存在
- [x] `lib/issue.sh` 中 `validate_issue_title` 强制校验 scope 存在（正则不含 `?` 可选标记）
- [x] `lib/issue.sh` 中 `extract_scope` helper 存在并正确工作
- [x] Plan 文件命名验证正则支持 scope 段（Issue 模式和无 Issue 模式均含 scope）
- [x] SKILL.md Issue 标题规范中 scope 规则改为"必选"，删除无 scope 示例
- [x] approve.sh 中移除阻断逻辑，添加自动 push
- [x] check-doc.sh 中添加委派策略检查（覆盖 Task > 2 和 Complexity = High）
- [x] 所有 Integration Tests 通过（I1、I1.1、I2、I3、I4）

### User Validation

#### Scenario 1: Plan 文件命名包含 scope 标识（有 scope）
- Goal: 确认 Issue title 含 scope 时 Plan 文件名也包含 scope
- Precondition: Issue 标题为 `feat(cli): xxx` 格式
- User Actions:
  1. 查看新创建的 Plan 文件名
  2. 确认格式为 `<issue>-feature-cli-<slug>.md`
- Expected Result: Plan 文件名可一眼识别针对哪个模块

#### Scenario 2: Plan 文件命名包含 scope（无 Issue 模式）
- Goal: 确认无 Issue 模式 Plan 文件名从 `--title` 提取 scope
- Precondition: `--title` 格式为 `feat(cli): xxx`（含 scope）
- User Actions:
  1. 执行 `flow.sh plan --title "feat(cli): xxx" --project ontology --type feature`
  2. 查看生成的 Plan 文件名
  3. 确认格式为 `feature-cli-<slug>.md`
- Expected Result: 无 Issue 模式 Plan 文件名包含 scope 段

#### Scenario 3: approve 后 Issue 可点击 Plan 链接
- Goal: 确认 approve --confirm 后 Issue 中 Plan 链接可正常打开
- Precondition: Plan 已通过审批
- User Actions:
  1. 打开 GitHub Issue
  2. 点击 Related Resources 中的 Plan 链接
- Expected Result: Plan 文件正常打开，内容完整

- [x] 用户已完成上述功能验证并确认结果符合预期