# {name}

<!--
Proposal naming contract — inherited by every new proposal from this shared
skeleton.

- Structure: `<type>-<slug>`; `type` uses the standard values, fully spelled
  (feature / fix / enhance / refactor / docs / test / chore / perf).
- `slug` = 1–2 core nouns, kebab-case, ≤ 20 chars. Drop verb phrases and
  articles; never copy the title.
- The name is load-bearing: `accept` derives the isolation branch and the
  worktree directory by prefixing `ontology-` to the **entire proposal name**
  (the stem): `refactor-ontology-maintenance` yields
  `ontology-refactor-ontology-maintenance`, and a verbose name produces an
  unreadable branch.

| Verbose (forbidden) | Lean (target) |
|---------------------|---------------|
| `consolidate-ontology-maintenance-into-the-ontology-evolution-skill` | `refactor-ontology-maintenance` |
-->

## Metadata

- **Type**: {type}
- **Project Path**: .wopal
- **Created**: {created}
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

<!--
  两个维度各选一档，不要自评过高：Complexity 影响委派波次划分，
  Confidence 提示读者这份提案的证据强度。
-->
- **Complexity**: <Low | Medium | High>
- **Confidence**: <High | Medium | Low>

## Goal

<!--
  一句话写清这项本体能力进化要达成什么目标。读者先看这里决定
  是否继续往下读。
-->
<这项本体能力进化要达到什么目标。>

## Technical Context

<!-- 4 个子节按需取舍，至少填一个。 -->

### Architecture Context

<!--
  现状 + 为什么需要变更。引用设计真相源（DESIGN-*.md）与关键
  代码位置（file:line），证据先行。
-->
<当前架构/机制现状、涉及模块、变更动机。证据给 file:line。>

### Research Findings

<!-- 前期调研结论；参考资料只放上下文文档路径。 -->
<调研结论摘要>

**参考资料**：
- `<上下文文档路径>`

### Key Decisions

<!-- 已确定的决策，D-NN 编号；每条写决策 + 理由，不写实现细节。 -->
- D-01: <决策内容及理由>

### Key Interfaces

<!--
  对外契约（硬约束）：命令行为、文件命名、错误码、边界条件。
  入册即红线：实施中要改这里必须先回报修订提案。无对外契约写 N/A。
-->
<契约定义，无则 N/A>

## In Scope

<!--
  本次要完成的内容，逐条可勾验。
-->
- <内容 1>
- <内容 2>

## Out of Scope

<!--
  明确不做的内容 + 原因。把"有意裁剪"和"待用户拍板"分开写，
  避免读者误判为遗漏。
-->
- <不做的内容及原因>

## Affected Files

<!--
  预计涉及范围，不是施工清单；实施允许按实际情况调整。
-->
| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| <component> | `<file>` | 修改/创建/删除 | <作用> |

## Acceptance Criteria

### Agent Verification

<!--
  两拍制：现在写行为判据（可判定、能抓住坏实现）；实施时把每条
  落成真实命令回填到此。每条需映射回 Task 的 Verification Intent。
-->
1. [ ] <行为判据 + 通过标准>

### User Validation

<!--
  只放 Agent 无法自动验证、必须由用户手动观察的项。每个场景必须
  具备：验证环境、启动命令、User Actions、通过判据、失败反馈。
-->
#### Scenario 1: <用户可感知的行为>
- Goal: <验证目标>
- 验证环境: <环境引用>
- Precondition: <前置条件>
- 启动命令: <可直接复制执行的命令>
- User Actions:
  1. <操作步骤>
- 通过判据: <可断言的预期结果>
- 失败反馈: <失败时用户提供什么>

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

<!--
  Task 拆分维度是行为组，不是文件。每个 Task 一个高内聚行为单元，
  独立可测。
-->

### Task 1: <任务标题>

**Verification Intent**: <引用的 Agent Verification 条目编号>

**Behavior**:
- <给定条件/输入 → 可观察结果>

**Pre-read**: <实施前必读文件路径>

**Design**: <实施设计：方案、关键思路、约束>

**TDD**: true

**Changes**:
1. RED：将上述 Behavior 落成失败测试
2. GREEN：实现至测试全绿

**Verify**: <验证命令>

**Done**:
任务产出：<一句话>
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

## Delegation Strategy

<!-- 2+ Task 或 Complexity = High 时必填；用 Wave 划分并行批次。 -->

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | <理由> |

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。
