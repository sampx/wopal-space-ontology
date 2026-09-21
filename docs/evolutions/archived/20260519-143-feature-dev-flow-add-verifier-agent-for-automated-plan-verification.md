# 143-feature-dev-flow-add-verifier-agent-for-automated-plan-verification

## Metadata

- **Issue**: #143
- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-18
- **Status**: done
- **Worktree**: issue-143-flow-add-verifier-agent-for-automated-plan-verification | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-issue-143-flow-add-verifier-agent-for-automated-plan-verification

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

为 Wopal 增加专职审查助手 rook，使其在 Plan 完成后审核方案质量、在 fae 实施后审核代码质量，以目标反推和技术债扫描减轻 Wopal 的手工检查负担。

## Technical Context

### Architecture Context

**当前协作链路**：

```text
用户 → Wopal（研究/方案/编排）→ fae（实施）→ Wopal 手工检查 → 下一步
```

当前痛点有两个：
1. **Plan 质量不稳定** —— 方案经常任务-目标脱节、验证不够可执行、依赖关系隐藏，导致 fae 按 Plan 执行时天然带入偏差。
2. **fae 实施结果技术债偏多** —— 仅靠 Wopal 手工复核，容易漏掉 stub、未连接实现、边界缺失、测试空转等问题。

**现有本体结构**：
- Agent 灵魂定义位于 `.wopal/agents/*.md`
- Skills 位于 `.wopal/skills/*/SKILL.md`
- Wopal 的委派策略定义在 `.wopal/agents/wopal-cn.md`
- fae 是明确的执行代理，不负责规划与审查（`.wopal/agents/fae-cn.md`）

这意味着 rook 最适合落成一个**新的只读审查子代理**，并通过两个专用 skill 承载 plan 审查与代码审查规范，由 Wopal 在关键节点主动委派。

### Research Findings

本次方案重点不是照搬 WSF 工作流，而是**抽取 WSF 中最成熟的审查脑子**：

1. **`wsf-plan-checker` 的价值**不在“检查 plan 是否完整”，而在“从目标反推，这个 plan 执行后是否真的能达成目标”。其中最值得继承的是：目标覆盖、任务完整性、依赖正确性、关键连接规划、范围与上下文匹配、对用户决策的遵循。
2. **`wsf-verifier` 的价值**是“不轻信执行结果，只信代码事实”。这正适合 rook 审 fae 产出：不接受“已完成”的口头描述，只根据真实文件、调用链、测试证据下结论。
3. **`wsf-code-reviewer` 的价值**是发现分级和证据锚点。rook 需要输出 Blocker / Warning / Info，且每个高等级发现都必须带 `file:line` 与具体代码。
4. **`verification-patterns.md` 是 rook 的实现审查武器库核心**：存在 / 实质性 / 已连接 / 功能性 四层验证，以及通用 stub 检测（TODO、占位文本、空实现、假动态真硬编码）。
5. **权限配置就写在 agent markdown frontmatter**：本空间的 agent 权限实践集中在 `.wopal/agents/*.md` frontmatter，现有 `wopal` / `fae` 也是如此。rook 的只读边界和 skill 可见性必须直接定义在 `rook-cn.md` 与 `rook.md` 中，而不是额外分散到其他配置文件。
6. **rook 需要中英双语灵魂层**：中文主定义用于当前空间运行，英文版 `rook.md` 保持与 `rook-cn.md` 结构、权限、路由一致，避免后续英文运行环境出现行为漂移。
7. **skill 创建要遵循 skill-creator 最佳实践**：description 负责触发；SKILL.md 主体聚焦流程、输出与注意事项；大段审查 rubric 下沉到 `references/`；正文保持精简、解释 why，并提供真实示例与引用指引。
8. OpenCode / ellamaka 的 agent 与 command 在启动时缓存加载，新增 rook agent 与 skill 后需重启运行时才能稳定识别，这应放入用户验证场景。

**参考资料**：
- `.wopal/agents/wsf-plan-checker.md`
- `.wopal/agents/wsf-verifier.md`
- `.wopal/agents/wsf-code-reviewer.md`
- `projects/space-flow/docs/zh-CN/references/verification-patterns.md`
- `.wopal/agents/wopal-cn.md`
- `.wopal/agents/wopal.md`
- `.wopal/agents/fae-cn.md`
- `~/.wopal/skills/skill-creator/SKILL.md`
- `docs/products/wopal-space-ontology/plans/backlog/50-feature-add-rook-code-review-subagent.md`

### Key Decisions

- D-01: **rook 采用“灵魂 + 双 skill”架构** —— 灵魂层只定义身份、边界、路由与输出契约；具体审查规范分别下沉到 `df-plan-review` 与 `df-implement-review`，便于后续独立迭代。
- D-02: **rook 是只读审查者，不承担修复职责** —— rook 不写代码、不改文件、不跑实现性修复；发现问题后由 Wopal 决策并让 fae 修正，以保持批判距离。
- D-03: **Plan 审查采用 WSF 的目标反推方法论** —— 不审“填得是否完整”，而审“这个计划执行后是否会达成目标”，重点覆盖目标覆盖、任务完整性、依赖、关键连接、验证可证伪性、范围控制。
- D-04: **代码审查采用“verifier 先、reviewer 后”的双层方法** —— 先核实目标是否达成，再扫描 bug / security / debt，避免 rook 退化成只挑代码味道的 lint 化审查员。
- D-05: **rook 的代码审查必须内建技术债嗅觉** —— 强制继承四层验证与 stub 检测，并增加测试质量审计，专门拦截 placeholder、空实现、假验证、跳过测试等隐性债务。
- D-06: **Wopal 在两个节点必须委派 rook** —— Plan 编写完成后必须做方案审查；fae 每个关键实施波次或最终交付后必须做代码审查，rook 成为默认守门员，而非偶尔使用的可选工具。
- D-07: **本期同步交付 `rook-cn.md` 与 `rook.md`** —— 两份灵魂层保持同构，保证中英文运行环境下的权限、路由与输出契约一致。
- D-08: **rook 的权限约束直接定义在 agent frontmatter** —— 至少显式限制 skill 可见范围；其余只读约束也优先通过 markdown frontmatter 与灵魂层红线表达，不引入额外配置分散权限来源。
- D-09: **rook 的两个 skill 采用 skill-creator 推荐结构** —— `SKILL.md` 负责触发与工作流，审查 rubric、示例与扩展说明下沉到 `references/`，避免技能正文臃肿失控。

### Key Interfaces

**1. Wopal → rook 委派契约**

```text
review_type: plan | implementation
goal: 为 Wopal 增加可审方案与审代码的 rook 助手
plan_path: /Users/sam/coding/wopal/wopal-workspace/docs/products/wopal-space-ontology/plans/143-feature-dev-flow-add-verifier-agent-for-automated-plan-verification.md
files_to_read:
  - /Users/sam/coding/wopal/wopal-workspace/.wopal/agents/wsf-plan-checker.md
  - /Users/sam/coding/wopal/wopal-workspace/.wopal/agents/wsf-verifier.md
focus:
  - check scope reduction
depth: standard | deep
```

要求：Wopal 在 prompt 中提供明确的 `review_type`、目标、文件清单与关注点；rook 先读完上下文，再自行加载对应 skill。

**0. rook 权限落点契约**

```yaml
permission:
  skill:
    "*": deny
    df-plan-review: allow
    df-implement-review: allow
```

要求：rook 的技能可见性与只读边界直接放在 `.wopal/agents/rook-cn.md` 与 `.wopal/agents/rook.md` frontmatter，避免权限来源分散。

**2. rook 输出契约**

```markdown
# 审查报告

## 概要
- 审查类型: Plan | Code
- 判定: PASS | REVISE | BLOCK
- 统计: Blocker N / Warning N / Info N

## Blocker
### B-01: Missing executable verification
- 位置: `docs/products/.../143-...md:210`
- 代码: `**Verify**: Manual — later`
- 问题: 验证不可执行，Wopal 无法据此确认方案或实现已达标
- 修复建议: 改成可运行命令，或明确仅限用户人工验证的原因

## Warning
...

## Positive Findings
- Delegation wave is explicit and dependency order is readable
```

规则：没有 `file:line` 与代码证据的发现不得升为 Blocker / Warning。

## In Scope

- 新增 `rook-cn` 子代理灵魂定义，明确只读边界、路由规则、判定等级与证据要求
- 新增 `rook.md` 英文版灵魂定义，与 `rook-cn.md` 保持权限、路由与输出契约一致
- 新增 `df-plan-review` skill，按 skill-creator 规范拆成 `SKILL.md + references/`，沉淀 Plan 审查维度、反 scope reduction 规则与 revision loop 约束
- 新增 `df-implement-review` skill，按 skill-creator 规范拆成 `SKILL.md + references/`，沉淀四层验证、bug/security/debt 检查与测试质量审计
- 更新 `wopal-cn.md` 与 `wopal.md` 的委派策略与验证纪律，使 rook 成为 Plan 审核与 fae 实施复核的默认助手
- 更新 `dev-flow` 技能的流程指令（`SKILL.md`），在 Plan 完成后与 fae 实施完成后明确插入 rook 审查节点
- 核验并定义 rook 的 permission 落点：仅使用 agent markdown frontmatter
- 更新 `.wopal/AGENTS.md`，把 rook 的角色、路径和协作边界同步到 ontology 项目规范
- 完成 rook 的运行时烟雾验证方案（重启后可识别、Plan 审查可输出结果、代码审查可输出结构化报告）

## Out of Scope

- 将 rook 接入 `complete.py` 或其他脚本级自动门控 —— 本期只做 AI 审查助手，不做流程引擎改造
- 自动修复能力 —— rook 只报告问题，修复仍由 fae 执行
- 新建 `rook-collab` 独立 skill —— 先由 Wopal 直接按委派契约调用 rook，避免能力碎片化
- 修改空间级或全局配置文件 —— 权限仅放在 agent markdown frontmatter，不引入额外配置同步成本
 - 修复 dev-flow 的 Plan 校验盲区 —— 本期先交付 rook 方案，校验器问题另立修复任务

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Rook Agent | `.wopal/agents/rook-cn.md` | 创建 | rook 的灵魂层定义：身份、只读边界、路由、判定与输出契约 |
| Rook Agent EN | `.wopal/agents/rook.md` | 创建 | rook 英文灵魂层，与中文版保持同构 |
| Dev-Flow Skill | `.wopal/skills/dev-flow/SKILL.md` | 修改 | 在 Plan 评审与实施复核环节接入 rook 审查节点 |
| Plan Review Skill | `.wopal/skills/df-plan-review/SKILL.md` | 创建 | 方案审查主技能，负责任务触发、流程、输出结构 |
| Plan Review Reference | `.wopal/skills/df-plan-review/references/review-rubric.md` | 创建 | 方案审查维度、scope reduction 规则、revision loop 细则 |
| Implement Review Skill | `.wopal/skills/df-implement-review/SKILL.md` | 创建 | 代码审查主技能，负责任务触发、流程、输出结构 |
| Implement Review Reference | `.wopal/skills/df-implement-review/references/review-rubric.md` | 创建 | 四层验证、stub 模式、测试质量审计细则 |
| Wopal Delegation CN | `.wopal/agents/wopal-cn.md` | 修改 | 将 rook 集成进中文委派与验证纪律 |
| Wopal Delegation EN | `.wopal/agents/wopal.md` | 修改 | 将 rook 集成进英文委派与验证纪律 |
| Ontology Constitution | `.wopal/AGENTS.md` | 修改 | 同步 rook 的角色、路径与协作约定 |

## Acceptance Criteria

### Agent Verification

1. [x] `test -f .wopal/agents/rook-cn.md` 退出码 0 — rook 中文 agent 已创建
2. [x] `test -f .wopal/agents/rook.md` 退出码 0 — rook 英文 agent 已创建
3. [x] `rg -n '^permission:|df-plan-review|df-implement-review|PASS \| REVISE \| BLOCK' .wopal/agents/rook-cn.md` ≥ 4 — 中文灵魂层含 frontmatter 权限、skill 路由与判定等级
4. [x] `rg -n '^permission:|df-plan-review|df-implement-review|PASS \| REVISE \| BLOCK' .wopal/agents/rook.md` ≥ 4 — 英文灵魂层含 frontmatter 权限、skill 路由与判定等级
5. [x] `test -f .wopal/skills/df-plan-review/SKILL.md && test -f .wopal/skills/df-plan-review/references/review-rubric.md` 退出码 0 — Plan 审查 skill 与 reference 已创建
6. [x] `rg -n '^description:|触发|输出|参考|示例' .wopal/skills/df-plan-review/SKILL.md` ≥ 4 — Plan skill 符合 skill-creator 主体规范
7. [x] `rg -n '目标覆盖|任务完整性|依赖|关键连接|验证可证伪|范围与上下文匹配|scope reduction|revision loop' .wopal/skills/df-plan-review/references/review-rubric.md` ≥ 8 — Plan 审查 rubric 齐备
8. [x] `test -f .wopal/skills/df-implement-review/SKILL.md && test -f .wopal/skills/df-implement-review/references/review-rubric.md` 退出码 0 — 代码审查 skill 与 reference 已创建
9. [x] `rg -n '^description:|trigger|output|reference|example' .wopal/skills/df-implement-review/SKILL.md` ≥ 4 — Implement skill 符合 skill-creator 主体规范
10. [x] `rg -n '存在|实质性|已连接|功能性|stub|bug|security|debt|测试质量' .wopal/skills/df-implement-review/references/review-rubric.md` ≥ 8 — 代码审查 rubric 齐备
11. [x] `rg -n 'rook' .wopal/agents/wopal-cn.md && rg -n 'rook' .wopal/agents/wopal.md` 均 ≥ 3 — 中英文 Wopal 委派策略已接入 rook
12. [x] `rg -n 'rook|rook-cn|rook.md|df-plan-review|df-implement-review' .wopal/AGENTS.md` ≥ 4 — ontology 项目规范已同步 rook 约定
13. [x] `rg -n 'rook' .wopal/skills/dev-flow/SKILL.md` ≥ 3 — dev-flow 流程已接入 rook 审查节点（Plan 评审 + 实施复核）
14. [x] 重启运行时后，Wopal 可委派 rook 审查本 Plan 并返回 `PASS|REVISE|BLOCK` 结构化结果 — rook 运行时可识别
15. [x] 在一个 fae 实施样例上委派 rook 做代码审查，报告至少包含概要、等级统计、证据锚点与修复建议 — 审查输出契约有效

### User Validation

#### Scenario 1: Plan 完成后 rook 可替代 Wopal 做方案守门
- Goal: 验证 Wopal 在写完方案后可委派 rook 审查 Plan，并收到可执行的审查结论
- Precondition: 已重启运行时；rook agent 与两个 skill 已部署到当前空间
- User Actions:
  1. 让 Wopal 对一个新写好的 Plan 触发 rook 审查
  2. 观察 rook 是否基于目标覆盖、依赖、验证充分性等维度输出结构化报告
- Expected Result: rook 返回 `PASS` / `REVISE` / `BLOCK` 判定，且 Blocker / Warning 都带证据锚点，Wopal 可据此优化方案

#### Scenario 2: fae 实施后 rook 可替代 Wopal 做代码复核
- Goal: 验证 Wopal 在 fae 完成实施后可委派 rook 做代码审查，并用结果驱动后续修复
- Precondition: 已有一轮 fae 实施产出，可供 rook 读取 Plan 与变更文件
- User Actions:
  1. 让 Wopal 在 fae 返回完成后委派 rook 做代码审查
  2. 观察 rook 是否检查目标达成、stub、连接关系、测试质量，并输出修复建议
  3. 观察 Wopal 是否能根据 rook 报告决定继续推进或要求 fae 修复
- Expected Result: rook 的代码审查报告可明确区分 Blocker / Warning，Wopal 能依据报告减少手工检查并推动 fae 补齐问题

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 创建 rook 灵魂层定义

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**: 新增一个中文只读审查子代理 `rook-cn`；当 Wopal 委派 Plan 审查或代码审查时，rook 能先读上下文、自行路由到正确 skill，并输出带等级判定与证据锚点的结构化报告。

**Files**: `.wopal/agents/rook-cn.md`, `.wopal/agents/rook.md`

**Pre-read**: `.wopal/agents/fae-cn.md`, `.wopal/agents/wopal-cn.md`, `.wopal/agents/wsf-plan-checker.md`, `.wopal/agents/wsf-verifier.md`, `.wopal/agents/wsf-code-reviewer.md`

**Design**:
以 `fae-cn.md` 的轻量 frontmatter 风格为基础，新增 `rook-cn.md`。正文只保留 rook 始终需要知道的内容：
1. **身份与边界** —— rook 是职业质疑者，只读不改；不写代码、不修 bug、不提交；发现问题只报告。
2. **核心判断原则** —— goal-first、do-not-trust-claims、evidence-or-downgrade、fail-closed。
3. **skill 路由规则** —— Plan 文档走 `df-plan-review`；实现结果/代码文件走 `df-implement-review`；不明确时优先实现审查。
4. **输出契约** —— `PASS | REVISE | BLOCK`，并统一 Blocker / Warning / Info 结构与证据规则。
5. **只读红线块位置前置** —— 在人格定义前显式写出 READ-ONLY 红线，降低误用概率。
6. **权限优先落点在 frontmatter** —— 至少显式收敛 `skill` 可见范围，且中英文版 frontmatter 保持一致。

**TDD**: false

**Changes**:
1. 设计 `rook-cn.md` 与 `rook.md` 的 frontmatter、权限落点、只读红线、角色描述、路由规则与输出契约。
2. 将 WSF 的目标反推、不轻信 claim、证据优先等原则压缩成适合 rook 的灵魂层表述。
3. 确保中英文版语义对齐，不把细则堆进灵魂层，细节留给 skill。

**Verify**:
`test -f .wopal/agents/rook-cn.md && test -f .wopal/agents/rook.md && rg -n '^permission:|df-plan-review|df-implement-review|PASS \| REVISE \| BLOCK' .wopal/agents/rook-cn.md .wopal/agents/rook.md`

**Done**:
任务产出：rook 中英文灵魂层文件已创建，具备统一的权限、边界、路由与输出契约。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 创建 df-plan-review 审查技能

**Verification Intent**: AC#5, AC#6, AC#7

**Behavior**: 当 rook 接收到 Plan 审查任务时，能依据统一的六维规则判断方案是否真的能达成目标，并输出可驱动修订的 Blocker / Warning，而不是泛泛评论。

**Files**: `.wopal/skills/df-plan-review/SKILL.md`, `.wopal/skills/df-plan-review/references/review-rubric.md`

**Pre-read**: `.wopal/agents/wsf-plan-checker.md`, `docs/products/wopal-space-ontology/plans/backlog/50-feature-add-rook-code-review-subagent.md`, `.wopal/skills/dev-flow/templates/plan.md`

**Design**:
创建专职 Plan 审查 skill，按 skill-creator 推荐结构组织：`SKILL.md` 放触发、流程、输出与示例，详细 rubric 下沉到 `references/review-rubric.md`。核心继承 `wsf-plan-checker`，但裁剪为 dev-flow 可执行版本：
1. 六个审查维度：目标覆盖、任务完整性、依赖与波次正确性、关键连接已规划、验证可证伪、范围与上下文匹配。
2. 增加 **scope reduction** 检查：禁止 planner 擅自把用户明确要求缩成“v1 / static / 以后再接”。
3. 增加 **revision loop** 约束：同一 Plan 最多建议三轮修订，避免无限对抗。
4. 输出以“问题为什么阻碍达成目标”为核心，而不是罗列模板格式问题。
5. 对 dev-flow 的字段顺序、Verify 命令要求、Wave 依赖规范做专项校验，确保 rook 审查贴合本空间的真实 Plan 模板。

**TDD**: false

**Changes**:
1. 设计 skill frontmatter 与“略 pushy”的触发描述，使 rook 在 plan 审查场景稳定加载。
2. 在 `SKILL.md` 中写流程、输出结构、示例与 references 加载指引。
3. 在 `references/review-rubric.md` 中编写六维审查流程、scope reduction 规则、判定等级与 revision loop 说明。

**Verify**:
`test -f .wopal/skills/df-plan-review/SKILL.md && test -f .wopal/skills/df-plan-review/references/review-rubric.md && rg -n '目标覆盖|任务完整性|依赖与波次正确性|关键连接已规划|验证可证伪|范围与上下文匹配|scope reduction' .wopal/skills/df-plan-review/references/review-rubric.md`

**Done**:
任务产出：rook 已获得可执行的 Plan 审查工作规范。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 创建 df-implement-review 审查技能

**Verification Intent**: AC#8, AC#9, AC#10

**Behavior**: 当 rook 接收到 fae 实施结果或代码文件列表时，能先验证目标是否真正落地，再扫描 bug / security / debt，并用证据锚点报告问题，减少 Wopal 的手工复查负担。

**Files**: `.wopal/skills/df-implement-review/SKILL.md`, `.wopal/skills/df-implement-review/references/review-rubric.md`

**Pre-read**: `.wopal/agents/wsf-verifier.md`, `.wopal/agents/wsf-code-reviewer.md`, `projects/space-flow/docs/zh-CN/references/verification-patterns.md`

**Design**:
创建专职实现审查 skill，按 skill-creator 推荐结构组织：`SKILL.md` 放触发、流程、输出与示例，详细 rubric 下沉到 `references/review-rubric.md`。组合 `wsf-verifier` 与 `wsf-code-reviewer` 的长处：
1. **第一层：目标验证** —— 不信 fae 的“已完成”，只根据代码与 Plan 检查目标是否真正被实现。
2. **第二层：问题扫描** —— 分 bug / security / debt 三类问题，避免 rook 变成单纯 style reviewer。
3. **四层验证模型** —— 存在、实质性、已连接、功能性，其中前 3 层是硬检查主轴。
4. **stub 与技术债扫描** —— TODO/FIXME、占位文本、空 return、空 handler、假动态真硬编码、只测存在不测行为。
5. **测试质量审计** —— 检查 skipped/disabled tests、循环自证、弱断言，防止“有测试但没证明需求”。
6. **审查深度模式** —— 默认 standard，复杂变更可切 deep，支持跨文件连线检查。

**TDD**: false

**Changes**:
1. 设计 skill frontmatter 与“略 pushy”的实现审查触发描述。
2. 在 `SKILL.md` 中写流程、输出结构、示例与 references 加载指引。
3. 在 `references/review-rubric.md` 中编写目标验证、四层验证、bug/security/debt 分类、测试质量审计与输出契约。

**Verify**:
`test -f .wopal/skills/df-implement-review/SKILL.md && test -f .wopal/skills/df-implement-review/references/review-rubric.md && rg -n '存在|实质性|已连接|功能性|stub|bug|security|debt|测试质量' .wopal/skills/df-implement-review/references/review-rubric.md`

**Done**:
任务产出：rook 已获得可执行的代码审查工作规范。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: 将 rook 接入 Wopal 委派策略与 ontology 规范

**Verification Intent**: AC#11, AC#12, AC#13

**Behavior**: Wopal 在 Plan 完成后和 fae 关键实施节点后都会主动委派 rook；ontology 项目规范也明确 rook 的角色、路径与边界，使这套协作方式稳定可继承。

**Files**: `.wopal/agents/wopal-cn.md`, `.wopal/agents/wopal.md`, `.wopal/AGENTS.md`, `.wopal/skills/dev-flow/SKILL.md`

**Pre-read**: `.wopal/agents/wopal-cn.md`, `.wopal/agents/wopal.md`, `.wopal/AGENTS.md`, `.wopal/skills/dev-flow/SKILL.md`, `.wopal/agents/rook-cn.md`, `.wopal/agents/rook.md`, `.wopal/skills/df-plan-review/SKILL.md`, `.wopal/skills/df-implement-review/SKILL.md`

**Design**:
在 `wopal-cn.md` 中补充 rook 的委派规则：
1. Plan 写完后，先让 rook 审方案，再决定是否进入 approve。
2. fae 每个关键波次或最终交付后，让 rook 审代码；若有 Blocker，则优先通过 `wopal_task_reply` 让 fae 修正。
3. 将 rook 纳入 Phase 4 / Phase 5 的委派与验证纪律，明确其不是可选锦上添花，而是默认守门员。

在 `.wopal/AGENTS.md` 中同步：
1. rook 的文件位置与 skill 位置；
2. rook 只读边界；
3. rook 与 fae / Wopal 的协作关系；
4. 运行时缓存导致需重启后识别的新 agent / skill 验证要求。

在 `.wopal/skills/dev-flow/SKILL.md` 中接入 rook，修改三处：

1. **C 节「委派原则」** — 在现有 fae 委派规则后追加 rook 委派规则：
   - 审查类 Task（Plan 评审、代码审查）默认委派 rook，实施类 Task 委派 fae
   - Wopal 完整职责链：Plan 切片 → 委派 fae 实施 → 委派 rook 审查 → 根据结果推进/修正 → 下一 Wave
   - fae 产出未经 rook 代码审查不得进入 `complete`

2. **B 节「Plan 写完后，进入方案评审」** — 在 `flow.sh approve` 前插入 rook 审查：
   - 替换步骤 4-5，新流程：委派 rook 审 Plan → 根据 PASS/REVISE/BLOCK 决定修 Plan 或继续 → 通过后执行 `flow.sh approve`
   - 连续 3 轮 BLOCK/REVISE → 保留分歧注释，由用户在 approve 时抉择
   - 更新「不要这样做」列表：增加「跳过 rook Plan 审查直接 approve」

3. **D 节「实施完成后，进入用户验证阶段」** — 在 Done 勾选之后、`complete` 之前插入 rook 审查：
   - 替换步骤 1-3，新流程：确认 Done 勾选 → 委派 rook 审 fae 实施结果 → 根据 PASS/REVISE/BLOCK 决定继续或要求 fae 修正 → 通过后补齐 Agent Verification → `flow.sh complete`
   - 更新「不要这样做」列表：增加「rook BLOCK 后强行 complete」
   - 更新边缘场景 #2/#3：增加「rook 审查 BLOCK 时不得执行 complete」

在权限配置上同步：
1. 明确 rook 权限主定义位置是 `.wopal/agents/rook-cn.md` 与 `.wopal/agents/rook.md` frontmatter；
2. 明确权限实践只在 agent markdown frontmatter 维护，不引入额外配置来源；
3. 明确 rook 的 skill 可见范围受 frontmatter 控制，避免后续误配。

**TDD**: false

**Changes**:
1. 修改 `wopal-cn.md` 与 `wopal.md`，增加 rook 的路由与协作规则。
2. 修改 `.wopal/AGENTS.md`，把 rook 纳入 ontology 项目规范。
3. 修改 `.wopal/skills/dev-flow/SKILL.md`，在委派原则、B 节（方案评审）、D 节（实施复核）三处接入 rook 审查规则与判定处理流程。
4. 明确 rook 权限配置只在 agent markdown frontmatter 中维护，避免后续分散配置。
5. 明确运行时烟雾验证步骤，确保后续实现者知道如何验证 rook 实际可用。

**Verify**:
`rg -n 'rook' .wopal/agents/wopal-cn.md .wopal/agents/wopal.md && rg -n 'rook|rook-cn|rook.md|df-plan-review|df-implement-review' .wopal/AGENTS.md && rg -n 'rook' .wopal/skills/dev-flow/SKILL.md`

**Done**:
任务产出：中英文 Wopal 委派策略、ontology 规范与 dev-flow 流程已正式接入 rook。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | rook 灵魂层文件创建（`.md` 文件），Wopal 提供详细 Design 后委派 |
| 2 | Task 2 | fae | Task 1 | df-plan-review 技能文件创建，依赖 rook 灵魂层的权限与路由定义做引用对齐 |
| 2 | Task 3 | fae | Task 1 | df-implement-review 技能文件创建，依赖 rook 灵魂层的只读边界与输出契约 |
| 3 | Task 4 | fae | Task 1, Task 2, Task 3 | Wopal 委派策略、ontology 规范、dev-flow 流程指令更新，基于前三项产出回写 |

**Wopal 职责**：每个 Wave 启动前审阅对应 Task 的 Design 并提供详细委派 prompt（含 files_to_read、输出要求、Plan 文件路径）；每个 Wave 完成后验证 fae 产出（文件存在性、内容质量、AC 合规）。

**fae 委派要求**：
- prompt 末尾附加：`完成后在 Plan 文件中编辑对应 Task 的 Done checkbox（- [ ] → - [x]），Plan 文件路径：/Users/sam/coding/wopal/wopal-workspace/docs/products/wopal-space-ontology/plans/143-feature-dev-flow-add-verifier-agent-for-automated-plan-verification.md`
- 禁止 fae 修改 Plan Status
