# 70-refactor-dev-flow

## Metadata

- **Issue**: #70
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-07
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

提升 dev-flow Plan 方案质量与工作流精确度：文件名以 issue 编号开头便于追踪，模板强化测试用例设计与并行委派策略，验收流程按执行主体分层，归档文件添加日期前缀。

## Technical Context

dev-flow 技能的 Plan 生成链路：`cmd_start` → `title_to_slug` → `plan_name` 拼接 → `create_plan` → `validate_plan_name`。文件名正则校验在 `plan.sh:140`，check-doc 校验在 `lib/check-doc.sh:111`，AC 校验在 `plan.sh:520` 的 `check_acceptance_criteria`。

优化点：
1. 文件名无 issue 编号开头，不直观
2. Plan 模板 Test Plan 仅 3 行占位
3. AC 不区分 agent/用户
4. 归档文件无日期前缀，done/ 目录按时间排列不便

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| 文件名生成 | `scripts/cmd/create.sh:61` | plan_name 拼接逻辑 |
| 文件名校验 | `lib/plan.sh:140` `validate_plan_name` 正则 | 校验新命名规范 |
| Plan 模板 | `templates/plan.md` | Test Plan / AC / 委派策略章节 |
| check-doc | `lib/check-doc.sh:111` | 文件名格式校验 + Test Plan 内容检查 |
| AC 校验 | `lib/plan.sh:520` `check_acceptance_criteria` | 区分 agent/user AC |
| 归档 | `lib/plan.sh:404` `archive_plan` | 归档文件名添加日期前缀 |
| complete 流程 | `scripts/cmd/execution.sh:132` | 只校验 agent AC |
| validate 流程 | `scripts/cmd/closing.sh:61` | 校验 user AC |
| SKILL.md | `SKILL.md` | 流程引导 / Plan 模板同步 |
| slug 提取 | `scripts/flow.sh:145-148` | extract_slug 从新格式提取 slug |
| type 提取 | `lib/plan.sh:274-276` | 从 plan_name 提取 type（第二段） |
| user AC 校验 | `lib/plan.sh:603-640` | check_user_validation 提取 User Validation 子章节 |

## In Scope

- [x] Plan 文件名格式改为 `<issue_number>-<type>-<slug>`
- [x] Plan 模板 Test Plan 章节强化（三个子标题）
- [x] Plan 模板增加并行委派策略章节
- [x] Acceptance Criteria 分层（agent AC + 用户 AC）
- [x] check-doc 校验适配新命名规范
- [x] 归档文件添加日期前缀
- [x] SKILL.md 强化实施后强制流程引导

## Out of Scope

- 已有 plan 文件的重命名（手动处理）
- state-machine 状态变更

## Out of Scope

| 文件 | 操作 | 说明 |
|------|------|------|
| `agents/wopal/skills/dev-flow/scripts/cmd/create.sh` | 修改 | plan_name 格式改为 `${issue_number}-${plan_type}-${slug}` |
| `agents/wopal/skills/dev-flow/scripts/flow.sh` | 修改 | `extract_slug` 正则适配新格式 |
| `agents/wopal/skills/dev-flow/lib/plan.sh` | 修改 | `validate_plan_name` 正则 + type 提取 + 归档日期前缀 + AC 分层校验 |
| `agents/wopal/skills/dev-flow/lib/check-doc.sh` | 修改 | 文件名校验正则 + Test Plan 内容检查 |
| `agents/wopal/skills/dev-flow/templates/plan.md` | 修改 | Test Plan 强化 + AC 分层 + 委派策略章节 |
| `agents/wopal/skills/dev-flow/scripts/cmd/execution.sh` | 修改 | `cmd_dev` 增加验证提醒输出 |
| `agents/wopal/skills/dev-flow/SKILL.md` | 修改 | Plan 模板格式同步 |

## Implementation

### Task 1: Plan 文件名格式改为 issue 编号开头

**Files**: `agents/wopal/skills/dev-flow/scripts/cmd/create.sh`, `agents/wopal/skills/dev-flow/lib/plan.sh`, `agents/wopal/skills/dev-flow/scripts/flow.sh`

**Changes**:
1. `create.sh:61` — plan_name 改为 `${issue_number}-${plan_type}-${slug}`
2. `plan.sh:140-165` — `validate_plan_name` 正则改为 `^([0-9]+)-(feature|enhance|fix|refactor|docs|chore|test)-([a-z0-9-]+)$`
3. `flow.sh:147` — `extract_slug` 正则改为从第三段提取 slug
4. `plan.sh:274-276` — type 提取改为取第二段

**Verification**: 新命名格式生成与校验

- [x] Step 1: `validate_plan_name` 正则匹配新格式
- [x] Step 2: `extract_slug` 从新格式正确提取 slug

### Task 2: Plan 模板 Test Plan 章节强化

**Files**: `agents/wopal/skills/dev-flow/templates/plan.md`

**Changes**:
1. Test Plan 章节扩展为三个子标题：Test Case Design / Regression Testing / Adjustment Strategy
2. 每个子项有填写指引，引导 agent 思考而非填占位符

**Verification**: 模板渲染正确性

- [x] Step 1: `flow.sh start` 创建新 plan，确认 Test Plan 章节包含新结构
- [x] Step 2: `flow.sh plan --check` 确认 check-doc 通过

### Task 3: Plan 模板增加并行委派策略章节

**Files**: `agents/wopal/skills/dev-flow/templates/plan.md`

**Changes**:
1. 在 Implementation 和 Test Plan 之间新增 `## Delegation Strategy` 章节
2. 包含批次划分、执行者分配、串行依赖说明
3. 可选章节（简单任务可填 N/A）

**Verification**: 模板渲染正确性

- [x] Step 1: 确认新章节出现在模板正确位置

### Task 4: Acceptance Criteria 分层

**Files**: `agents/wopal/skills/dev-flow/templates/plan.md`, `agents/wopal/skills/dev-flow/lib/plan.sh`, `agents/wopal/skills/dev-flow/scripts/cmd/execution.sh`, `agents/wopal/skills/dev-flow/scripts/cmd/closing.sh`

**Changes**:
1. 模板 AC 章节拆分为 `### Agent Verification` 和 `### User Validation`
2. `check_acceptance_criteria` 只检查 Agent Verification 下的 checkbox
3. `cmd_validate` 校验 User Validation 下的 checkbox
4. User Validation 无 checkbox 格式时跳过检查（纯提示用）

**Verification**: AC 分层校验

- [x] Step 1: Agent Verification 全勾选，`flow.sh complete` 通过
- [x] Step 2: User Validation 无 checkbox 时 `validate --confirm` 通过

### Task 5: check-doc 适配新命名规范

**Files**: `agents/wopal/skills/dev-flow/lib/check-doc.sh`

**Changes**:
1. 文件名校验正则改为 `^([0-9]+)-(type)-(slug)$`
2. 校验文件名中的 issue 编号与 Plan metadata 一致
3. Test Plan 检查升级为 mandatory + 内容深度检查

**Verification**: check-doc 校验逻辑

- [x] Step 1: 用新格式文件名运行 check-doc，确认通过
- [x] Step 2: 用旧格式运行 check-doc，确认报错

### Task 6: 归档文件添加日期前缀

**Files**: `agents/wopal/skills/dev-flow/lib/plan.sh`

**Changes**:
1. `archive_plan` 中归档文件名前添加 `$(date '+%Y%m%d')-` 前缀
2. 归档后文件名示例：`done/20260408-70-refactor-dev-flow-plan.md`

**Verification**: 归档文件名

- [x] Step 1: 确认归档文件名包含日期前缀

### Task 7: SKILL.md 流程引导强化 + 部署验证

**Files**: `agents/wopal/skills/dev-flow/SKILL.md`

**Changes**:
1. Plan 模板示例更新为新命名格式 + 分层 AC + Delegation Strategy
2. 实施后强制流程：Step checkbox → Agent AC 打勾 → complete → 等用户

**Verification**: 端到端流程

- [x] Step 1: 部署后 `flow.sh plan 70 --check` 通过
- [x] Step 2: SKILL.md 中 Plan 模板示例与 templates/plan.md 一致

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 (文件名) | Wopal | 无 |
| 1 | Task 2 (Test Plan 模板) | Wopal | 无 |
| 1 | Task 3 (委派策略章节) | Wopal | 无 |
| 2 | Task 4 (AC 分层) | Wopal | Task 2, 3（模板结构确定后） |
| 2 | Task 5 (check-doc) | Wopal | Task 1（命名格式确定后） |
| 2 | Task 6 (归档日期) | Wopal | 无 |
| 3 | Task 7 (SKILL.md + 部署) | Wopal | Task 1-6 全部完成 |

## Test Plan

### Test Case Design

- `validate_plan_name` 正则匹配新格式 `70-refactor-dev-flow-plan` ✓ / 拒绝旧格式 `ontology-refactor-dev-flow-plan` ✓
- `check_acceptance_criteria` 只检查 `### Agent Verification` 下 checkbox ✓
- `check_user_validation` 无 checkbox 时跳过 ✓
- `extract_slug` 从新格式 `70-refactor-dev-flow-plan` 正确提取 `dev-flow-plan` ✓
- `archive_plan` 归档文件名包含日期前缀 ✓

### Regression Testing

- `flow.sh start` 生成新格式文件名 ✓
- `flow.sh plan --check` 文件名格式校验 + Test Plan 内容检查 ✓
- `flow.sh complete` 只校验 Agent Verification AC ✓
- `flow.sh validate --confirm` User Validation 无 checkbox 时通过 ✓

### Adjustment Strategy

- N/A — 改动范围明确，无阻塞风险

## Acceptance Criteria

### Agent Verification

- [x] `flow.sh start` 生成的 plan 文件名格式为 `<issue_number>-<type>-<slug>`（如 `70-refactor-dev-flow-plan`）
- [x] Plan 模板 Test Plan 包含 Test Case Design / Regression Testing / Adjustment Strategy 三个子标题
- [x] Plan 模板包含 Delegation Strategy 章节（可选 N/A）
- [x] `check_acceptance_criteria` 只检查 Agent Verification 子章节，无子章节时退化
- [x] `check_user_validation` 无 checkbox 时跳过检查
- [x] check-doc 文件名格式校验 `^([0-9]+)-(type)-(slug)$` + issue 编号一致性校验
- [x] check-doc Test Plan 检查从 warning 升级为 mandatory + 内容深度检查
- [x] 归档文件名添加日期前缀（如 `done/20260408-70-refactor-dev-flow-plan.md`）
- [x] SKILL.md 包含更新后的 Plan 模板示例
- [x] 部署后 `flow.sh plan 70 --check` 通过

### User Validation

- 用户确认新 Plan 模板结构符合实际使用需求
- 用户确认 SKILL.md 流程引导清晰可用
