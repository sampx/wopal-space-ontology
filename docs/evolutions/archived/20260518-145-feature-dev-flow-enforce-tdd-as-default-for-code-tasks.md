# 145-feature-dev-flow-enforce-tdd-as-default-for-code-tasks

## Metadata

- **Issue**: #145
- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-18
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

将 dev-flow 从 TDD opt-in（默认 false）反转为 opt-out（代码 Task 默认 true），使 Agent 编写 Plan 时自动为代码变更启用 RED-GREEN-REFACTOR 流程。

## Technical Context

### Architecture Context

dev-flow 的 TDD 引导机制分布在三层：

| 层级 | 文件 | 当前行为 |
|------|------|----------|
| Plan 模板 | `templates/plan.md` | `**TDD**: false`（硬编码默认值） |
| 主流程文档 | `SKILL.md` | 仅在"Plan 质量门"间接提及 TDD 字段校验，无显式规则 |
| 参考指南 | `references/tdd-guide.md` | 完整 TDD 指南，但按需加载（Agent 不主动查阅） |

问题链：模板默认 false → Agent 写 Plan 时跳过 TDD → check-doc 只校验 `TDD=true` 时 Behavior 必填 → 无强制触发点。

### Key Decisions

- D-01: 仅修改模板注释和 SKILL.md 文本，不改 check-doc 校验逻辑。模板注释翻转后，Agent 写 Plan 时会主动设置 `**TDD**: true`，现有 check-doc 的 Behavior 必填校验自然生效。
- D-02: 暂不增加"TDD=false 需附理由"的 check-doc 校验规则。模板注释中要求说明理由即可，后续按需加严。

### Key Interfaces

check-doc 现有校验接口（不改）：
- `TDD_PATTERN = r'\*\*TDD\*\*:\s*(true|false)'` — 匹配显式声明
- `if tdd_value == 'true':` → 强制 Behavior 必填
- `tdd_value = tdd_match.group(1).lower() if tdd_match else 'false'` — 缺省默认 false

## In Scope

- 修改 `templates/plan.md` 的 `**TDD**` 字段注释，从"默认 false"改为"代码 Task 默认 true；非代码 Task 设为 false 并说明理由"
- 更新 `SKILL.md` 的"Plan 质量门"章节，添加 TDD 默认规则
- 在 `SKILL.md` 的 Implementation Task 字段说明中强调 Behavior 对代码 Task 为必填

## Out of Scope

- check-doc 校验逻辑变更（D-01：模板注释翻转已足够）
- `references/tdd-guide.md` 内容更新（现有内容完整，无需改动）
- "TDD=false 需附理由"的自动校验（D-02：后续按需）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| plan template | `.wopal/skills/dev-flow/templates/plan.md` | 修改 | TDD 字段注释翻转 |
| skill doc | `.wopal/skills/dev-flow/SKILL.md` | 修改 | 添加 TDD 默认规则 |

## Acceptance Criteria

<!-- agent-verify-guard -->

### Agent Verification

1. [x] `rg -c '默认 true.*代码.*Task' .wopal/skills/dev-flow/templates/plan.md` ≥ 1 — TDD 字段注释已更新为代码 Task 默认 true
2. [x] `rg -c '代码.*Task.*默认.*TDD' .wopal/skills/dev-flow/SKILL.md` ≥ 1 — SKILL.md 已添加 TDD 默认规则
3. [x] `rg -c 'Behavior.*必填.*代码' .wopal/skills/dev-flow/SKILL.md` ≥ 1 — SKILL.md 已强调代码 Task Behavior 必填
4. [x] `cd /Users/sam/coding/wopal/wopal-workspace/.wopal/skills/dev-flow && python -m pytest scripts/dev_flow/domain/validation/tests/test_check_doc.py -v` — 现有 check-doc 测试不受影响，全部 pass

### User Validation

#### Scenario 1: 新 Plan 中代码 Task 自动启用 TDD
- Goal: 确认修改后的模板和规则引导 Agent 为代码 Task 默认设置 TDD=true
- Precondition: dev-flow 技能已更新
- User Actions:
  1. 让 Agent 为一个代码变更 Issue 创建 Plan
  2. 检查生成的 Plan 中代码 Task 的 `**TDD**` 字段值
- Expected Result: 代码 Task 的 `**TDD**` 字段为 `true`，`**Behavior**` 字段已填写输入/输出映射，`**Design**` 按 RED-GREEN-REFACTOR 组织

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: Flip TDD default annotation and add SKILL.md rule

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**: Plan 模板 TDD 字段注释从"默认 false"改为"代码 Task 默认 true"；SKILL.md 新增 TDD 默认规则和 Behavior 必填说明

**Files**: `.wopal/skills/dev-flow/templates/plan.md`, `.wopal/skills/dev-flow/SKILL.md`

**Pre-read**: `references/tdd-guide.md`（确认现有指南与改动一致）

**Design**:
1. **templates/plan.md**: 将 `**TDD**: false` 行及其下方注释替换。新注释说明"代码 Task 默认 true；非代码 Task（UI、配置、胶水代码、探索性原型）设为 false 并说明理由"。删除硬编码默认值 `false`，保留示例值 `true`。
2. **SKILL.md**: 在"Plan 质量门"章节中添加显式规则段落："代码 Task 默认 TDD=true，Agent 应自动启用 RED-GREEN-REFACTOR 流程。非代码 Task（UI 布局、配置变更、胶水代码、探索性原型）显式设为 false 并在注释中说明理由。"同时在 Task 字段说明中补充 Behavior 对代码 Task 的必填性。

**TDD**: false

**Changes**:
1. 修改 `templates/plan.md` 第 180-186 行：将 `**TDD**: false` 及其注释替换为 `**TDD**: true` 和新注释（代码 Task 默认 true，非代码 Task 显式设为 false 并说明理由）
2. 在 `SKILL.md` "Plan 质量门"章节末尾添加 TDD 默认规则段落
3. 在 `SKILL.md` Implementation 注释区域补充 Behavior 必填说明（代码 Task）

**Verify**:
`cd /Users/sam/coding/wopal/wopal-workspace/.wopal/skills/dev-flow && rg -c '默认 true.*代码.*Task' templates/plan.md && rg -c '代码.*Task.*默认.*TDD' SKILL.md && python -m pytest scripts/dev_flow/domain/validation/tests/test_check_doc.py -v`

**Done**:
任务产出：Plan 模板 TDD 注释已翻转，SKILL.md 已添加 TDD 默认规则，check-doc 测试全部通过
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

N/A — 单一任务（Complexity=Low），无需并行委派。Wopal 直接执行。
