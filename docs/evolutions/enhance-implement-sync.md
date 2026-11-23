# enhance-implement-sync

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-11-20
- **Stage**: draft
- **Mode**: (none)
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Medium — 实施 SOP 与来源/证据/文档同步的行为改变，配套实施后只读评审；两项技能均无独立 CLI，但旧 Plan 不得回退。
- **Confidence**: High（df-implement 当前禁改 DESIGN 的规则已实查）；Medium（直接实施与新 Plan 的互操作需端到端验证）。

## Goal

一次性交付 `df-implement` 与 `df-implement-review` 的成套改造：获授权的 direct 或 Plan 实施中，将**代码、测试和说明实际交付成果的 DESIGN**一同更新，并由独立只读评审核查实际实现、兼容性、测试和文档一致性；保持旧版 Plan 的约束有效直到新 CLI 切换。

## Technical Context

### Architecture Context

产品总提案：`docs/products/wopal-space/proposals/development-governance-proposal.md`，**子提案 3**；前置已归档的子提案 1（`.wopal/docs/evolutions/archived/20261122-enhance-doc-contracts.md`）与子提案 2（`.wopal/docs/evolutions/archived/20261123-enhance-dev-proposal.md`）。子提案 1 已交付瘦身后的唯一文档能力底座 `dev-doc-master`（项目/模块现状 DESIGN、防并行分片、去掉所有主文档头部 `Sub-DESIGNs` 强枚举、实测取证、`verify-docset.py` 12 项门禁含 `--check-sync` 与四道质量把控闭环、Slop Checklist 审查清单）、`space-master` 三级 `AGENTS.md` 维护 SOP，以及最终目标态的 `.wopal/rules/coding-workflow.md`（及中文审核版）；子提案 2 已交付业务 Proposal 技能 `dev-proposal` 与校验器 `verify-proposals.py`（含已实施提案再变更分流与双向互链/清理规则）。本提案直接建立流程层对能力底座与机械门禁的按需调用契约，实现代码、测试、现状 DESIGN 与 Proposal 生命周期在同一次交付中同步闭环，绝不重复抄写 `dev-doc-master`、`dev-proposal` 或 `space-master` 的细则。

当前 `.wopal/skills/df-implement/SKILL.md:13` 仍把 Active DESIGN 当作未实现目标（`DESIGN defines the target`），现行 `dev-flow/SKILL.md` 又限制实施期更新 DESIGN。新契约下，项目/模块 DESIGN 只写已交付现状，因此实施者在代码真正改变对外行为、公共接口、生效业务规则、默认值或失败边界后，**按需加载 `dev-doc-master`** 同步所属模块的 `DESIGN-<module>.md` 并于交付出口运行 `verify-docset.py --check-sync`（纯内部重构不动文档但须显式给 `--pure-refactor` 理由供评审审计）；涉及业务 Proposal 全交付迁入 `implemented/`、部分替代双向互链、完全替代清理或事实同步时，**按需加载 `dev-proposal`** 并运行 `verify-proposals.py`；留下新的长期工程约束时，**按需加载 `space-master`** 审计或更新对应层级的 `AGENTS.md`；测试继续遵循常驻规则 `rules/testing.md`。`df-implement-review` 在保留既有 Q1–Q4、只读原则与报告结构的基础上，接通四道质量闭环的第 4 道对抗式审查（实际 `git diff` ↔ 所属模块 DESIGN / Proposal 双向实证核验，**直接参照 `dev-doc-master` 审查清单与 Slop Checklist**）。正式 `dev-flow` CLI 切换由子提案 4（`enhance-dev-flow-proposal`）完成，本提案保持旧 Plan 兼容且核对 `.wopal/rules/coding-workflow.md` 最终目标态契约一致。

### Research Findings

- 实施者不能修改批准的设计决定；发现缺失约束、新 API 决策或大幅超出范围应 STOP 并回到主控/用户，而非自行改 Proposal 或把已实施提案退回 `proposed/`。
- 代码、测试、实际 DESIGN/Proposal 同步及机械校验（`verify-docset.py --check-sync`、`verify-proposals.py`）全部通过后，主控才能根据可重复验证证据接受 Task；“文档已更新”本身不是运行时验证。
- `direct` 无 Plan 时证据记在业务 Proposal 或 Issue 所属的唯一记录；Plan 路线 Task Done / `DESIGN Sync` 由控制者复核并记录，实施者不能自签验收。
- 现有 `.wopal/skills/df-implement/SKILL.md:140-147` 已使用稳定的汇报字段（`Done`、`Touched`、`Verified`、`AC Commands`、`Skipped`、`Notes/deviations`）；新增 `DESIGN Sync` 必填证据块应平滑叠加在现有字段之上，不无故重命名原有字段以免破坏现有调用习惯。
- 旧 Plan 仍按既有 DESIGN → Plan → implementation 规则执行，不能因为新的文档同步原则被追溯修改或拒绝。
- 现有 `df-implement-review` 没有独立 CLI/状态机，需要在既有四问题（Q1–Q4）和结果结构上补充对抗式 diff↔DESIGN/Proposal 证据核查，不另建独立的文档审查子提案。

**References**:
- `.wopal/docs/evolutions/archived/20261122-enhance-doc-contracts.md`
- `.wopal/docs/evolutions/archived/20261123-enhance-dev-proposal.md`
- `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}`
- `.wopal/skills/df-implement-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`
- `.wopal/skills/git-worktrees/SKILL.md`
- `.wopal/skills/dev-doc-master/{SKILL.md,references/design.md,references/design-project-guide.md,scripts/verify-docset.py}`
- `.wopal/skills/dev-flow/{SKILL.md,references/plan-guide.md}`
- `.wopal/rules/{coding-workflow.md,testing.md}`

### Key Decisions

- D-01：**代码 / 测试 / 所属模块现状 DESIGN / Proposal 生命周期 / 覆盖整次交付基线的机械门禁同一交付同步**：
  - `df-implement` 仅保留轻量触发判据，绝不复制底座模板与细则：对外可见行为、接口、生效业务规则、默认值或失败边界变化，或发现原文档写错时，**按需加载 `dev-doc-master`** 同步所属模块子 `DESIGN-<module>.md`（纯内部重构不动 DESIGN）；
  - **覆盖整次交付的 Git 基线约束**：在文档目录存在且受 `dev-doc-master` 治理时，交付出口运行 `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md --check-sync --base <delivery-base>`（纯内部重构显式传入 `--pure-refactor "<reason>"` 留痕待审）。凡整次交付跨多个提交或位于独立工作分支上，**必须传入覆盖整次交付的 Git 基线**（如 `Delivery Base Commit` 或 `git-worktrees` 隔离分支起点），不得在干净工作树中省略 `--base` 导致脚本仅回退检查 `HEAD~1..HEAD` 而放过早期提交的漏同步（仅单次未提交工作树改动可省略 `--base`；不修改 `verify-docset.py`，不新增工具）；
  - 涉及业务 Proposal 时按需加载 `dev-proposal` 并运行 `verify-proposals.py`：①**批准范围全部交付且用户验收通过后**，同交付将 Proposal 从 `proposals/proposed/<class>/` 迁入 `proposals/implemented/<class>/` 并改写为现在时 `## Decision` / `## Consequences`（清除计划期标题）；部分交付必须留在 `Status: approved`；②若该 Proposal **部分替代**已有 `implemented/` 提案，全范围交付时同提交补齐新旧双向互链（未全范围交付前严禁提前修改老提案）；③若该 Proposal **完全替代**已有 `implemented/` 提案，全范围交付时当场吸收独特理由/备选/代价/验证并修好入链后删除旧文件，或迁入 `archived/<class>/`（插入 `Archived: YYYY-MM-DD`）永久冻结；④普通代码改动造成路径/符号/默认值漂移但原决定未变时，同交付原地同步受影响 `implemented/` 中的事实引用；⑤严禁把 `implemented/` 回退为 `proposed/`，严禁解冻或修改 `archived/`；⑥使用已交付校验器的真实调用形式 `python3 .wopal/skills/dev-proposal/scripts/verify-proposals.py <proposals-root> [--link-scope <docs-dir>]...`，迁移、删除或重命名导致外部文档可能断链时，按实际引用范围重复传入 `--link-scope`；
  - 留下新的长期工程约束时，**按需加载 `space-master`** 维护对应层级 `AGENTS.md`；测试遵循常驻 `rules/testing.md`。
- D-01a：**并行实施防文档冲突纪律**：并行 Task/分支中，实施者只能修改授权写集内所属模块的 `DESIGN-<module>.md`，**严禁越界修改共享主 `DESIGN.md` 或他人模块文档**；如在实施中发现授权写集之外的文档过时或写错，必须在交付报告的 `DESIGN Sync` 块中准确上报主控处理。
- D-01b：**`direct` 模式默认强制 `git-worktrees` 隔离实施（禁默认直改主分支）**：
  - 当以 **`direct` 模式**（已批准 Proposal `Delivery: direct` 或无 Plan 的直接 Issue 任务）实施项目代码变更时，**默认必须先加载 `git-worktrees` 技能创建并切换到独立工作树与功能分支后再开始编码**，严禁默认直接在主（集成）分支上直接实施（防污染主分支及干扰并发 Agent）；
  - 仅在两种明确例外下免重建工作树：①用户显式要求在主/当前分支直接修改；②调用方/主控（如 `dev-flow`）已经创建并指派好隔离工作树（不重复套娃建 worktree）；
  - 该隔离分支起点即为整次交付的 `<delivery-base>`，直接传给 `verify-docset.py --check-sync --base` 与 `df-implement-review`；实施、评审并获用户验收放行后，再按用户授权集成回主分支并通过 `git-worktrees` 安全清理（保留原有 `git-worktrees` 技能不重复造脚本）。
- D-02：实施者可在已批准的决定和范围内自主决定实现技术细节，但不能修改设计授权；遇到设计冲突或超出批准范围须及时 STOP 并报告涉及的行为、影响与可选处理。
- D-03：**独立于 Plan 状态机的统一质量标准**：`df-implement` 与 `df-implement-review` 的输入可以是已批准 Proposal（`direct`）、明确 Issue 或可选 Plan 中的实施 Task，不绑定任何 Plan 状态机，也不在两项技能内新增新的审批、进度或交付状态机（便于未来被本体能力进化流程复用）。`direct` 和 Plan 路线使用完全相同的测试、完整基线机械门禁、`DESIGN Sync` 证据、独立评审和验收质量标准。
- D-04：委派 Agent 只提交代码/测试/授权写集内文档变更与证据，不自主提交 Git、不审批、不写 Plan Done；主控检查差异、真实命令输出与非空 `DESIGN Sync` 块，再负责写回记录。
- D-05：新规范对进行中的旧 Plan 保留最低必要兼容分支；不追溯修改已完成的历史 Plan。
- D-06：`df-implement-review` 保留 Q1–Q4、报告格式、2 轮收敛目标和只读原则，接通四道质量闭环第 4 道对抗式审查：
  - **评审范围必须对齐覆盖整次交付的完整变更**（与交付出口相同的 `--base <delivery-base>` `git diff`，多提交交付不得只审最后一个提交）；
  - 核查授权来源→实际代码、实际完整 `git diff`→所属模块 `DESIGN-<module>.md` 与 Proposal 生命周期同步，审查文档质量与防 AI 流水账（Slop Checklist）直接参照 `dev-doc-master`（含 `references/design-project-guide.md`），不另写第二套文档标准；
  - **按真实影响分级定严重度（对齐投入产出门槛）**：真正导致交付不完整、功能行为错误、公开接口/配置/失败边界变动却漏更 DESIGN 或借虚假 `--pure-refactor` 搪塞、并行越界修改共享主 `DESIGN.md`、未全交付提前篡改老提案或冒充全交付、以及违规把 `implemented/` 回退或修改 `archived/` 等实质违约与重大事实失真判 **Blocker**；不影响核心正确性的轻微说明偏差、措辞瑕疵或局部补链遗漏按实际影响判 **Warning** 或 **Info**，避免一刀切产生低价值阻塞噪音；审查者不得修改实施代码、DESIGN 或批准记录。
- D-07：`df-implement`、`df-implement-review` 的中英 `description` 必须精准区分**执行编码/测试/按需同步 DESIGN 与 AGENTS**和**对已交付 diff、代码、测试与文档同步作独立只读评审**；前者在真实实施任务必须加载，后者在实施后代码审查必须加载。不得因“实施”“评审”“DESIGN”等共享词误选，也不得让实施前的设计方案评审误入实施后审查。
- D-08：`.wopal/rules/coding-workflow.md`（及中文审核版）已在子提案 1 按最终目标态一次落盘，本提案核对并按需微调以保持与落地后的 `df-implement` / `df-implement-review` 契约完全一致，**绝不倒退写回过渡期免责文案**。
- D-09：**本体现状设计文档同交付同步**：践行 DSH 现状文档同交付机制，在本提案实施完成后，同交付将刚落地的 `df-implement` 与 `df-implement-review` 现状契约、完整基线门禁与严重度边界更新至本体子设计文档 `.wopal/docs/DESIGN-coding-workflow.md`（若与子提案 4 并行，本分支只更新 `df-implement` / `df-implement-review` 对应章节，并在集成收口时跑通 `verify-docset.py`）。

### Key Interfaces

- `df-implement` 输入：明确授权的已批准 Proposal（`direct`）、明确 Issue 或可选 Plan Task、原有 DESIGN/Proposal/AGENTS 约束与适用参考（独立于 Plan 状态机）。`direct` 模式默认先通过 `git-worktrees` 建立隔离工作树与分支；由 `dev-flow` 或主控已指派工作树时直接复用不重建。
- `df-implement` 交付出口门禁：涉及受 `dev-doc-master` 治理的项目文档时运行 `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md --check-sync --base <delivery-base>`（单次未提交改动可省略 `--base`；跨多提交或独立分支必须传覆盖整次交付的基线，如 `git-worktrees` 隔离分支起点；纯内部重构附 `--pure-refactor "<reason>"`）；涉及业务 Proposal 变动时运行 `python3 .wopal/skills/dev-proposal/scripts/verify-proposals.py <proposals-root> [--link-scope <docs-dir>]...`（命令路径从空间根目录起算，`--link-scope` 按被迁移/删除 Proposal 的实际外部引用范围传入）。格式校验通过不替代用户验收与授权。
- `df-implement` 返回给主控的报告结构：沿用现有 `.wopal/skills/df-implement/SKILL.md:140-147` 的 `Done`、`Touched`、`Verified`、`AC Commands`（Plan Task 适用）、`Skipped`、`Notes/deviations`，平滑新增**必填 `DESIGN Sync`** 字段（包含所用工作树/分支、`<delivery-base>` 基线与 `verify-docset.py --check-sync` / `verify-proposals.py` 实跑结果、更新的所属模块文档及对应代码事实，或 `--pure-refactor` 理由，以及并行期写集外文档漂移上报）；冲突时沿用现有 `STOP` 最小报告格式。
- `df-implement-review` 输入：授权来源（Proposal/Issue/Plan/DESIGN）、覆盖整次交付基线（`--base <delivery-base>`）的完整 `git diff`、实跑测试证据、`DESIGN Sync` 交付块、对应模块 DESIGN 与 Proposal 文件；保留原 Full/Quick/Repo-audit 报告字段，不能只给“文档已同步”的无证据结论。
- 不在两项技能中新增任何审批、进度或交付状态机，也不侵入 Git/commit 所有权，也不重造工作树管理脚本（直接调用 `git-worktrees`）。

## In Scope

- **`df-implement`（修改技能 — 优化与精简边界）**：
  - **优化**：支持已批准 Proposal（`direct`）、明确 Issue 或可选 Plan Task 统一输入（独立于 Plan 状态机）；明确 **`direct` 模式默认必须先调用 `git-worktrees` 创建隔离工作树实施**（严禁默认直改主分支；已有主控 worktree 或用户显式指定时不重复创建）；明确按需调用 `dev-doc-master`/`dev-proposal`/`space-master` 同步契约；强制在跨多提交/工作分支交付出口使用覆盖整次交付基线的 `verify-docset.py --check-sync --base <delivery-base>`（及 `verify-proposals.py`）；落实并行写集不越界纪律；沿用现有报告字段平滑新增必填 `DESIGN Sync` 证据块与冲突 STOP 规范；保留进行中旧 Plan 的最低兼容。
  - **精简**：去除“Active DESIGN 定义未实现目标”的旧前提；绝不复制底座写作/审查细则或重造 `git-worktrees` 脚本；不在 `df-implement` 内新增审批、进度或交付状态机；不无故重命名现有报告字段；不修改 `verify-docset.py` 或新造工具。
- **`df-implement-review`（修改技能 — 优化与精简边界）**：
  - **优化**：接通四道质量闭环第 4 道对抗式审查，强制评审范围对齐覆盖整次交付基线的完整 `git diff`；参照 `dev-doc-master` 语义审查清单与 Slop Checklist 双向核验代码↔测试↔DESIGN↔Proposal 同步；按真实影响与投入产出门槛分级判定 Blocker / Warning / Info。
  - **精简**：不另建第二套文档审查标准，不新增词汇匹配脚本，保留既有 Q1–Q4、只读原则、2 轮收敛目标与报告结构，不依赖 Plan 状态机。
- **规则核对、本体现状设计同交付与触发验证**：核对并按需微调 `.wopal/rules/coding-workflow.md`（及中文审核版）保持最终目标态一致并在 `df-implement` 路由说明补齐 `direct` 默认配 `git-worktrees` 隔离契约；同交付同步更新 `.wopal/docs/DESIGN-coding-workflow.md` 中 `df-implement` / `df-implement-review` 对应章节；依 `skill-creator` 完成两项技能各 10+10 近邻触发验证。

## Out of Scope

- 不变更 `df-proposal-review` 的**实施前**设计审查（由子提案 2 `enhance-dev-proposal` 负责）。
- 不修改 `dev-flow` 状态机、Plan 创建/批准/Graph 命令，不修改 `verify-docset.py`，不改变 `ontology-evolution`。
- 不修改真实业务代码、业务 PRD/DESIGN/Plan 或实施记录。

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| 实施技能 | `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}` | modify | 统一多来源实施、按需调用底座与完整基线门禁、并行不越界与必填 `DESIGN Sync` 合同 |
| 实施评审 | `.wopal/skills/df-implement-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}` | modify | 完整交付范围对抗式 diff↔DESIGN/Proposal 双向核验与影响分级严重度，参照 `dev-doc-master` 清单 |
| 空间调用规则 | `.wopal/rules/coding-workflow.md`, `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` | modify (verify / align as needed) | 核对并保持最终目标态与落地技能契约一致，不写过渡期文字 |
| 本体现状设计 | `.wopal/docs/DESIGN-coding-workflow.md` | modify | 同交付补充已落地的 `df-implement` 与 `df-implement-review` 现状契约与门禁边界 |
| 隔离验证样例 | `.wopal-space/.tmp/` 临时验证 fixtures（验证后自行清理） | create (ephemeral) | 证据块、多提交 `--base` 漏同步反例、Proposal 替代互链、并行不越界与 STOP 回归 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|

## Acceptance Criteria

### Agent Verification

1. [ ] 对已授权 `direct`、Issue 和 Plan 样例，实施者在 `direct` 模式下默认先调用 `git-worktrees` 创建隔离工作树与分支后再实施（严禁默认直改主分支；Plan 委派已有主控工作树时不重复建），实现公开行为后按需加载 `dev-doc-master` 同步所属模块子 DESIGN 并在交付出口以分支起点或 `Delivery Base Commit` 为 `--base` 跑通 `verify-docset.py --check-sync`（跨多提交/独立分支交付必须传入覆盖整次交付的 `--base <delivery-base>`，隔离多提交反例能拦住早期提交漏同步；纯内部重构不动文档但显式提供 `--pure-refactor` 理由）；涉及业务 Proposal 时按需加载 `dev-proposal` 并跑通 `verify-proposals.py`：全范围交付迁入 `implemented/<class>/` 并改写 `Decision`/`Consequences`，部分替代同交付补双向互链（未全交付前不提前改老提案），完全替代当场合并删除或迁入 `archived/<class>/`，纯路径/默认漂移原地同步 `implemented/` 事实（严禁回退 `implemented/` 或改动 `archived/`）；并行任务发现写集外漂移仅在 `DESIGN Sync` 上报主控而不越界修改共享主 `DESIGN.md`；有新长期工程约束时按需调用 `space-master`；不写未来未交付功能。
2. [ ] 对越权设计变化、缺失批准范围、接口冲突等负例，实施者 STOP 并报告，不擅自篡改 Proposal/Plan。
3. [ ] 沿用现有 `df-implement` 报告字段并附必填 `DESIGN Sync` 证据块（含所用工作树/分支、`--base` 基线与实跑输出）的委派汇报能被控制者复核；实施者不会自己批准 Task、改 Done 或提交正式交付；两项技能均不绑定或新增 Plan 状态机。
4. [ ] 进行中的旧版 Plan 继续保留最低必要兼容流程，不被新文档规范追溯强制修改；没有真实业务文件变更。
5. [ ] `df-implement-review` 能基于覆盖整次交付的完整 `git diff`（含多提交早期漏同步反例），参照 `dev-doc-master` 审查清单（5 项必填覆盖要素、新人测试、证据审查与 Slop Checklist）以代码/测试/文档实证准确区分严重度（缺实现、旧行为回归、公开契约变动漏更 DESIGN 或虚假 `--pure-refactor`、并行越界改共享主文档、未落地提前改老提案、违规回退 `implemented/` 或改 `archived/` 判 Blocker；轻微说明偏差或局部补链遗漏按影响判 Warning/Info）；合法实现可通过，原有 Q1–Q4、只读原则、2 轮收敛目标与报告结构保持；`.wopal/rules/coding-workflow.md` 中英版本保持最终目标态且 `.wopal/docs/DESIGN-coding-workflow.md` 同步更新并通过 `verify-docset.py`。
6. [ ] `df-implement`、`df-implement-review` 两项中英 `description` 精准简洁、触发语义一致；每项均通过 10 个应触发 + 10 个不应触发的实际近邻场景，覆盖编码实施、实施后 diff 评审、实施前方案评审、纯文档维护以及 `dev-flow` 的 Plan 管理。记录改前/改后、误选/漏选及修复复验，没有真实加载评估时明确标注未自动验证。

### DSH Principles → Tasks → Verification

| DSH 已验证来源 | 本提案取用的实践 | Task 与验收 |
|---|---|---|
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-code-review/SKILL.md` | 代码变更和公开行为/错误说明在同一交付范围更新；审查源于覆盖整次交付的实际代码，不以只读的过去 DESIGN 当新行为的唯一标准 | Task 2、4；AC#1、5 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-doc-writing/SKILL.md` | 运行所声称的操作，对当前 checkout 实际事实取证；可阅读的说明与精确的失败边界同时保留 | Task 2、4；AC#1、5 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-prose-standard/SKILL.md` | 保留所有重要条件、不变量、失败保证，避免代码清单和重复解释 | Task 2、4；AC#1、5 |
| `labs/ref-repos/deepseek-harness/docs/AGENTS.md` & `.agents/notes/implemented/AGENTS.md` | 事实只留一个所有者；已实施决策不可原地篡改，改事实原地更新、改决定新建提案并于同交付互链/清理 | Task 1、2、3、4；AC#1、3、4、5 |

`direct`、Plan 验收主控权、`verify-docset.py --check-sync --base` + `DESIGN Sync` 四道质量闭环以及独立只读评审委派规则是 **WopalSpace 自有机制**，不是 DSH 提供的生命周期。

### User Validation

#### Scenario 1: 交付后的 DESIGN、门禁证据与代码说明相符
- Goal: 用户理解新实施交付如何把“做了什么”通过覆盖整次交付的机械门禁与评审同步写进 DESIGN 与 Proposal。
- Environment: 隔离的虚构实现（含多提交交付样本）与一份 `direct` 或 Plan 示例。
- Precondition: Tasks 和独立评审通过，已进入 validating（或按用户安排与子提案 4 统一验收）。
- Launch command: `wopal space evo switch enhance-implement-sync`（切换后**重启 ellamaka** 以加载更新后的技能）
- User Actions:
  1. 阅读实施报告中的 `DESIGN Sync` 证据（含 `--base` 基线检查输出）与同步后的模块 DESIGN、Proposal 互链，不打开代码判断实现结果与限制。
  2. 查看一次设计冲突被 STOP 阻止及一次多提交早期漏同步/虚假 `--pure-refactor` 被评审拦截的示例。
- Pass criteria: DESIGN 描述已交付事实、覆盖整次交付的机械门禁与评审闭环可靠、且决策未被 Agent 私自扩张。
- Failure feedback: 指出不对应的设计段落、漏拦情况或越权行为。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 核对旧实施规则、多来源授权接口与 `direct` 工作树隔离入口

**Verification Intent**: AC#1、AC#2、AC#3、AC#4
**Behavior**: 清楚区分进行中旧 Plan 的兼容路径与新多来源路径（已批准 Proposal `direct` / 明确 Issue / 可选 Plan Task），不绑定也不新增 Plan 状态机；明确 `direct` 模式默认必须先调用 `git-worktrees` 创建并进入隔离工作树（严禁默认直改主分支），而由 `dev-flow` 或主控已指派工作树时直接复用不重复创建；明确禁止实施者自行扩张或篡改批准决定。
**Pre-read**: 当前 `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}`、`git-worktrees/SKILL.md`、`dev-flow/{SKILL.md,references/plan-guide.md}`、已交付的 `dev-doc-master` 文档体系（含 `references/design-project-guide.md`）与 `dev-proposal` 技能。
**Design**: 标明“已授权的新路径（已批准 Proposal `direct` 默认走 `git-worktrees` 隔离、明确 Issue 与可选 Plan Task 复用主控工作树）”和“进行中旧 Plan 最低兼容路径”的适用条件，不按文档名字猜测来源，以真实授权来源/metadata 为判断依据。
**TDD**: false — 规则归属与兼容适配设计。
**Changes**: `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}` 的前置输入、`git-worktrees` 默认隔离约定、授权边界与旧 Plan 兼容规则。
**Verify**: 对进行中旧 Plan、新 Proposal `direct`（含自动建隔离 worktree 正例与禁止默认直改主分支校验）/ Issue / Plan Task（不重复套娃建 worktree）示例分别验证授权路由、STOP 触发条件与旧约束保持。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: 代码、测试、按需同步 DESIGN/Proposal/AGENTS、完整基线机械门禁与并行不越界

**Verification Intent**: AC#1、AC#2
**Behavior**: `direct` 模式在 `git-worktrees` 隔离工作树内完成编码与测试；对外行为/接口/生效业务规则/默认值/失败边界变化时按需加载 `dev-doc-master` 同步所属模块子 `DESIGN-<module>.md`，交付出口以 `git-worktrees` 分支起点或 `Delivery Base Commit` 为 `--base` 运行 `verify-docset.py --check-sync --base <delivery-base>`（跨多提交或独立分支必须传入覆盖整次交付的 Git 基线，防止默认仅查最近 1 次提交漏检；纯内部重构不动 DESIGN 但显式提供 `--pure-refactor "<reason>"`）；**已批准 Proposal 必须在批准范围全交付且用户验收通过后**才同交付完成 `proposed/<class>/` → `implemented/<class>/` 迁移改写、部分替代双向互链（未全交付前不提前改老提案）或完全替代合并删除/归档冻结，未满足时保持 `Status: approved`，纯事实漂移则原地同步 `implemented/`；运行 `verify-proposals.py <proposals-root>`，涉及路径移动/删除时还需按引用范围传入 `--link-scope <docs-dir>` 核查外部入链（严禁回退 `implemented/` 或改动 `archived/`）；有新长期工程约束时按需加载 `space-master`；并行期不越界修改共享主 `DESIGN.md` 或他人模块文档，写集外漂移在 `DESIGN Sync` 上报主控；缺少设计授权或暴露变更冲突时 STOP。
**Pre-read**: Task 1、`git-worktrees/SKILL.md`、`dev-doc-master/{SKILL.md,references/design-project-guide.md,scripts/verify-docset.py}`、`dev-proposal/{SKILL.md,scripts/verify-proposals.py}`、`space-master` AGENTS 维护 SOP、`rules/testing.md`、`df-implement` STOP/report 规则。
**Design**: 将按需调用 `git-worktrees`/`dev-doc-master`/`dev-proposal`/`space-master` 与覆盖整次交付基线的机械出口门禁写入 `df-implement` 的轻量触发判据，绝不把文档模板或写作细则复制到 `df-implement`，也不修改 `verify-docset.py` 或重造工作树脚本；明确并行写集边界，只改所属模块子文档、跨文档漂移写入 `DESIGN Sync` 上报主控。
**TDD**: false — SOP + 真实运行 `git-worktrees`（隔离临时 Git 仓）、`verify-docset.py --check-sync --base` 与 `verify-proposals.py` 的隔离多模块语义样例（含 `direct` 隔离创建与分支起点校验、**多提交中早期提交改了模块代码但漏同步 DESIGN 的反例**、纯内部重构、部分替代互链、并行越界拦截与 STOP 冲突反例）。
**Changes**: `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}` 的同步纪律与完整基线出口门禁（先中文审核版后同步英文正式版）。
**Verify**: 在 `.wopal-space/.tmp/` 用虚构多模块多提交仓库实跑 `git-worktrees` 隔离工作流、`verify-docset.py --check-sync --base <delivery-base>` 与 `verify-proposals.py <proposals-root>`（迁移/删除时增加对应的 `--link-scope <docs-dir>`），验证 `direct` 隔离实施、多提交早期漏同步精准拦截、正常同步放行、纯内部重构 `--pure-refactor`、未获用户验收不得迁入 `implemented/`、部分替代同交付互链、跨目录引用断链、并行越界拦截、虚构能力与遗漏失败边界等场景，验完清理临时文件。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: 统一委派报告（新增必填 `DESIGN Sync`）、直接实施证据与 `df-implement` 触发收敛

**Verification Intent**: AC#1、AC#3、AC#4、AC#6
**Behavior**: `direct`、Issue 和 Plan 实施沿用现有 `df-implement` 报告字段并统一返回必填 `DESIGN Sync` 证据块（含所用工作树/分支、`--base` 基线与门禁输出、文档同步摘要或 `--pure-refactor` 理由与写集外漂移上报），主控可独立复验；旧 Plan 的记录所有权不被修改。
**Pre-read**: Task 1–2、`skill-creator` 技能、现有 `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}`、`dev-flow` Task Done/AC 记录要求。
**Design**: 在现有 `Done / Touched / Verified / AC Commands / Skipped / Notes/deviations` 基础上平滑新增必填 `DESIGN Sync`，不无故改名已有字段，不复制 Graph 进度，不新增状态机；以项目和来源选择记录落点。
**TDD**: false — 记录合同用隔离正反案例（`direct` 隔离工作树、Plan、STOP、缺 `DESIGN Sync` 拒收）验证。
**Changes**: `.wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}` 的 handoff/report 与中英 `description`。
**Verify**: 模拟 `direct`、Plan、STOP 三种返回，检查实现者不能自签验收且缺 `DESIGN Sync` 时主控可明确拦截；依 `skill-creator` 精炼 `df-implement` 中英 `description`，完成 10+10 近邻正反触发测试，不能把普通 Plan 编排/只读评审/纯文档维护误判为实施。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: 在独立实施评审中接入完整基线对抗式审查、分级严重度并同交付更新本体现状设计

**Verification Intent**: AC#1、AC#2、AC#5、AC#6

**Behavior**: `df-implement-review` 基于覆盖整次交付的完整 `git diff`（与交付出口一致的 `--base` 范围）和测试证据对抗式判断：新功能是否真的完成、旧行为是否退化、错误边界是否正确、代码公开行为/配置/失败边界变动是否同步到用户可理解的所属模块 `DESIGN-<module>.md`，参照 `dev-doc-master` 审查清单（5 项必填覆盖要素、新人测试、证据审查与 Slop Checklist）抓出假实现、缺测试、多提交早期漏同步、并行越界改共享主 `DESIGN.md`、文件清单充数、AI 思考过程泄露与虚构行为，并核查 Proposal 全交付迁移/替代互链/禁止回退 `implemented/` 与冻结 `archived/`；按真实影响结合投入产出门槛分级判定 Blocker / Warning / Info（不因轻微说明偏差一刀切阻塞）；同时核对 `.wopal/rules/coding-workflow.md`（及中文审核版）保持最终目标态一致（在 `df-implement` 路由说明补齐 `direct` 默认配 `git-worktrees` 隔离契约），并同交付将刚落地的 `df-implement` 与 `df-implement-review` 现状契约更新至 `.wopal/docs/DESIGN-coding-workflow.md`。

**Pre-read**: Task 1–3、`skill-creator` 技能、`dev-doc-master/{references/design-project-guide.md,scripts/verify-docset.py}`、`.wopal/rules/coding-workflow.md`（及中文审核版）、`.wopal/docs/DESIGN-coding-workflow.md`、`df-implement-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`、DSH `dsh-code-review/SKILL.md`、`dsh-doc-writing/references/review.md`、`dsh-prose-standard/SKILL.md`。

**Design**: 保留原 Q1–Q4 四问题、只读原则、2 轮收敛目标与报告结构，补充授权来源→实际代码、覆盖整次交付完整 `git diff`→所属模块 DESIGN/Proposal 两条双向证据链及按影响分级严重度校准，文档语义与 Slop Checklist 直接链接 `dev-doc-master` 绝不重复抄写；核对 `.wopal/rules/coding-workflow.md`（及中文审核版）仅按需对齐最终目标态，绝不倒退写回过渡期免责文案；同交付更新 `.wopal/docs/DESIGN-coding-workflow.md` 对应章节。

**TDD**: false — 审查语义采用多组确切 code+tests+DESIGN+Proposal 隔离案例（含多提交早期漏同步与轻微说明偏差分级反例）在干净上下文独立盲审验证；不新增不可靠的词汇匹配脚本。

**Changes**: `.wopal/skills/df-implement-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`、`.wopal/docs/DESIGN-coding-workflow.md`，以及按需微调 `.wopal/rules/coding-workflow.md` 与 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`。

**Verify**: 在隔离样例上对真实一致、未实现关键行为、多提交中早期提交改了公开行为却漏更 DESIGN、公开行为变动借虚假 `--pure-refactor` 搪塞、并行越界改共享主文档、未全交付提前改老提案/回退 `implemented/`、轻微说明偏差（应定 Warning/Info 而非 Blocker）、遗漏错误边界、只有文件名清单与思考过程泄露样例分别独立盲审出报告；检查只读、进行中旧 Plan 审查、2 轮收敛目标不变、`coding-workflow.md` 中英最终目标态一致且 `.wopal/docs/DESIGN-coding-workflow.md` 通过 `verify-docset.py`；依 `skill-creator` 精炼 `df-implement-review` 中英 `description`，完成 10+10 近邻正反触发验证，不能因出现“review”就抢占方案评审。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | enhance-doc-contracts、enhance-dev-proposal | 多来源统一输入（不绑 Plan 状态机）与旧 Plan 兼容适配 |
| 2 | Task 2 | Wopal 主控 | Task 1 | 按需调用底座、覆盖整次交付的 `--base` 机械门禁与并行不越界纪律 |
| 3 | Task 3 | Wopal 主控 | Task 2 | 平滑叠加必填 `DESIGN Sync` 汇报块与触发收敛 |
| 4 | Task 4 | Wopal 主控 | Task 3 | 同轮闭合完整基线对抗式评审、严重度校准与本体现状设计同交付 |

由 Wopal 主控逐 Task 实施/验证并提交，不委派 Fae、不调用 Rook；全部 Task 实施完成后由用户安排其他 Agent 加载 `df-implement-review` 执行独立只读评审；最终用户验证与集成遵循本体进化现有规则。

## Delivery

此文件 `Stage: draft`；获批后依本体进化命令以 `isolated` 隔离模式独立交付（可在子提案 2 合入后与子提案 4 安全并行）。新规则对进行中旧 Plan 保持最低兼容，不擅自切换 `dev-flow` CLI（留待子提案 4）。
