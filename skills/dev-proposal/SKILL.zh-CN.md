---
name: dev-proposal
description: |
  分析、讨论、编写与维护业务/项目 Proposal：判断是否需要提案、澄清设计要求与决策、编写目标规格、记录用户批准、迁移或归档提案、处理已实施决定的后续变更。

  使用场景：用户要求设计或讨论一项拟写入提案的变更，或新建、修订、批准、迁移、归档、演进 Proposal。

  不适用：既定设计内的普通缺陷与任务（用 df-implement）、对 Proposal/Plan/DESIGN 的独立只读评审（用 df-proposal-review）、PRD/DESIGN 写作（用 dev-doc-master）、本体能力进化提案（用 ontology-evolution）、编排开发 Plan（用 dev-flow）。
---

# dev-proposal — Business Proposal Lifecycle

Proposal 是本次变更的**目标设计规格与重要决策记录**。先把设计讨论清楚，再写出确定、完整、可实施、可验收的设计。执行进度归 Plan 与 Issue，已交付的系统行为归项目/模块现状 DESIGN。

## When a Proposal is required

出现下面任一种情况时，写 Proposal：

- 需要在多条可行路径之间做选择，而且选择理由无法从代码读出来；
- 改变已生效的默认值、边界、权限、失败语义或对外契约；
- 推翻或部分推翻一份已 `implemented/` 的决定；
- 影响多个项目、多个模块的共同约定，或需要用户重新拍板范围。

只有下面全部成立时，才**不**写 Proposal：

- 属于既有决定范围内明确的任务或缺陷；
- 一条 Issue 或一次直接实施就能说清范围与验收；
- 不需要用户在设计层面重新选择。

普通 Bug、样式微调、机械改名、纯内部重构一律走 Issue 或直接实施。**Proposal 不是开发动作的仪式**：为了"看起来规范"而给每个改动套一份 Proposal，只会制造没人读的档案。

同一主题已有 Proposal 时，先审计再动笔：能原地同步事实就不新建，需要改决定就新建并互链，详见下文「已实施提案的再变更」。

## 设计分析与规格编写

用户要求讨论或写提案时，先读取 `references/design-discussion.md`，并读取 `references/design-practices.md` 中与实际设计对象相关的部分。调查上层设计、现有决策、代码及术语；主动建模，按设计决策树分轮讨论，直到所有重要分支都已确定。已明确的设计不重复提问。每轮及时记录决定。

讨论收口后，读取 `references/design-specification.md`，确定验证边界，将全部已确认的设计整理成目标规格并逐项核对。写规格是综合既定决定，不是再次选型。若发现遗漏的重要决定，返回讨论。

本次未授权改变的既有架构和契约继续有效；需要改变时明确范围、理由、影响及继续有效的约束，交用户决定。设计确定，代码实现自由。自检通过后交独立评审，用户批准前不得实施。

## Layout and state machine

读取 `references/lifecycle.md`，以其中的目录、字段、正文骨架、状态迁移及链接维护为准。

`proposed` → 用户批准 → `approved`（路径不变）→ 全范围交付且用户验收 → `implemented` → 不再指导日常工作时归档。提案可在 proposed 或 approved 时被否决；归档永久冻结。实施进度归 Plan/Issue。

使用当前模板。目标设计与现状 DESIGN 分离，文档归属及同步遵循 `dev-doc-master`。

## Delivery mode: the user decides

`Delivery` 只有两个值，且**必须由用户决定**，Agent 不得代选：

- **`direct`** — 跳过 `dev-flow` 拆 Plan。由 `df-implement` 默认调用 `git-worktrees` 创建隔离工作树实施，**不默认直接在主/集成分支上开发**。适合范围清楚、单点收口、无需多任务并行的交付。
- **`plan`** — 启用可选 `dev-flow` 拆解 Plan/Task，隔离工作树与共享 Delivery 由 `dev-flow` 管理。适合跨项目、多交付物或需要并行写集的交付。

Agent 可以把**客观事实**摆到用户面前帮助选择：涉及几个仓库、是否需要并行、是否要中途分批验收。**严禁**用"这个模型够强/不够强""这个任务复杂/简单"之类的主观判断替用户选路。

## 验收前的提案维护

已批准的 Proposal 是提案驱动交付中获批变更的唯一目标依据，包含设计决定、授权范围和验收要求；未明确变更的既有设计约束仍有效。自动化实施不得自行改变这些内容。用户在实施后的测试、验证中明确提出并认可的调整，包括增加功能、扩大范围和改变方向，即为本次交付的有效授权；尚未明确的决定由用户确认，不重复审批已经明确的决定。

在原文件内将新决定融入授权范围、设计依据、目标方案、验收标准及受影响的决策理由和剩余风险，优先在调整代码前完成；若代码已调整，则在交付前补齐。保持 `Status: approved`、原路径和交付基线。主控协调共享文件及 Plan 写集。已验收的 `implemented/` 提案遵循后文的历史决策规则。

提案正文使用用户偏好语言，面向用户，以最终目标态、正向肯定式语言写清设计。直接替换失效内容，使整份文档准确、简洁、自洽；Git 保存修改历史，不追加补丁式说明、变更流水账或并列的新旧方案。

## Workflow

1. **判定必要性**：按上文三条门槛确认这次改动需要 Proposal。不需要就转 Issue 或直接实施，并说明理由。
2. **分析并讨论设计**：按上文设计方法调查上层设计、当前事实及同主题活跃与已实施记录，解决重要未决问题。命中的处理见「已实施提案的再变更」。
3. **写规格并自检**：复制 `templates/proposal-proposed.md` 到 `proposed/<class>/yyyy-mm-dd-<slug>.md`，按目标规格规范填写。核对所有已确认决定、架构继承、设计契约与验收，必要时回到讨论。
4. **独立评审并等用户读**：交 `df-proposal-review` 独立评审，解决重要问题。文件保持 `Status: proposed`，不自行推进。
5. **记录批准**：用户明确同意后，补齐 `Approved`、`Authorized scope`、`Delivery` 三条，状态改为 `approved`，文件位置不变。
6. **创建交付分支或工作树前，先提交已批准的 Proposal**：在集成分支上单独提交这次 Proposal 变更，再从该提交开始交付，让已批准的记录进入交付基线。这个提交只包含 Proposal 变更。
7. **交付**：按 `Delivery` 分流。交付过程中把 Source、关联 Plan、实际提交与评审验收证据链在 Proposal 里（链接即可，不复制进度表）。
8. **全范围交付且用户验收后迁移**：移动到 `implemented/<class>/`，改 `Status: implemented`，同交付机械改写骨架为现在时（`Decision` / `Consequences`），并同步受影响的现状 DESIGN。
9. **否决时**：判断这份否决理由是否能防止**将来有人再犯同样有诱惑力的错误**。能——移入 `rejected/<class>/` 并把理由写进状态行；不能——整份删除，并修好所有入链。
10. **归档清理**：`implemented/` 中已完成使命、不再指导日常工作的记录移入 `archived/<class>/`，插入 `Archived: YYYY-MM-DD` 后永久冻结。微小的 UI 调整或纯机械变更不归档，直接删除并修好入链。

每一步都要跑一次校验（路径相对本技能目录）：

```bash
python3 scripts/verify-proposals.py <proposals-root>
```

退出码 0 才算写法合规；脚本只查单快照的静态事实，设计质量仍由评审与用户判断。

## Evolving an implemented proposal

变更已实施决定前，读取 `references/evolution-triage.md`，区分纯事实同步、部分替代和完全替代。保护历史决策，在同一已验收交付中完成相应互链、吸收或归档。

## Honest boundaries

- 本技能只负责 Proposal 的写作、批准记录、迁移与冻结。它**不执行实施**，也不替用户批准。
- 独立评审由 `df-proposal-review` 承担。本技能写，它审；不要自己给自己发通行证。

## References

- 设计分析与分轮讨论：`references/design-discussion.md`
- 目标设计规格与自检：`references/design-specification.md`
- 分类设计最佳实践：`references/design-practices.md`
- 状态机、字段与迁移细则：`references/lifecycle.md`
- 再变更分流与替代合并的判断细则：`references/evolution-triage.md`
- 骨架模板：`templates/proposal-proposed.md`、`templates/proposal-implemented.md`
- 静态校验器：`scripts/verify-proposals.py`
- 正文表达规范：`dev-doc-master`（`references/consistency.md`、`references/design-project-guide.md`）
