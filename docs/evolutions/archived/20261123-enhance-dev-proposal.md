# enhance-dev-proposal

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-11-20
- **Stage**: archived
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-enhance-dev-proposal
- **Branch**: ontology-enhance-dev-proposal
- **Base Commit**: c5ea6ccaf0d4deb932c89888b4de039d712863a4
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Medium — 新增独立能力与目录/状态/引用校验，配套改动无独立执行脚本的方案评审技能；不改 dev-flow 底层状态机。
- **Confidence**: High（现行文档职责和本体进化模板已核实）；Medium（跨业务仓库场景需要隔离测试）。

## Goal

一次性提供业务/项目 Proposal 创建、写作、批准记录、交付证据与长期维护能力，并同步更新 `df-proposal-review` 的方案审查规则，为后续 dev-flow 提供**能创建、能审查、可核验的设计决定来源**。

## Technical Context

### Architecture Context

产品总提案：`docs/products/wopal-space/proposals/development-governance-proposal.md`，**子提案 2**。前置子提案 1（已归档：`.wopal/docs/evolutions/archived/20261122-enhance-doc-contracts.md`）已交付瘦身后的唯一文档底座 `dev-doc-master`（项目/模块现状 DESIGN、去所有主文档头部 `Sub-DESIGNs` 强枚举、防并行分片、实测取证、`verify-docset.py` 12 项门禁与 Slop Checklist 审查合同）及最终目标态的 coding 空间调用规则 `.wopal/rules/coding-workflow.md`（及中文审核版）。业务 Proposal 归属与现状 DESIGN 的区别按子提案 1 交付的文档规范落实；本提案负责落地独立业务 Proposal 技能与命令、改造实施前方案评审，并核对保持 `.wopal/rules/coding-workflow.md` 最终目标态契约一致，不重复文档体系标准。

当前 `dev-doc-master` 已瘦身为现状文档底座并完成旧 Phase/GAPS/BR 退场，尚无业务 Proposal 专用技能。`dev-flow` 的旧无 Issue Plan 仍待子提案 4 切换，Proposal 的设计授权、直接交付、部分实施和已实施后的再演进/替代缺少稳定契约。本提案在**同一交付**建立 Proposal 的目录/状态/授权/演进规则、确定性校验器、装配挂载与对应 `df-proposal-review` 评审能力，不提前修改旧 `dev-flow` CLI。

### Research Findings

- 可完整借鉴 `labs/ref-repos/deepseek-harness/.agents/notes/{README.md,implemented/AGENTS.md,archived/AGENTS.md}` 与 `.agents/skills/dsh-archive-agent-notes/SKILL.md` 的二维目录布局（`{lifecycle}/{class}/yyyy-mm-dd-<slug>.md`）、生命周期转迁、正文时态切换、`implemented/` 事实同步、**已实施决策不可原地篡改（部分替代新建互链 / 完全替代吸收删除或归档冻结）**、微小变更直接删除与 `archived/` 永久冻结规则；但 WopalSpace **不放在 `.agents/notes/`**、**不引入中英 `.i18n.yaml` 三元组配对**，且用户显式批准、`Delivery: direct|plan` 与可选 `dev-flow` 属于 WopalSpace 自有机制。
- WopalSpace 的产品 Proposal 根目录为 `docs/products/{product}/proposals/`，项目 Proposal 目标根目录为 `projects/{project}/docs/proposals/`（下按 DSH 分为 `{proposed,implemented,rejected,archived}/{feature,bug-fix,simplification,architecture,process,testing}/yyyy-mm-dd-<slug>.md`）；存量前格式文件保持历史只读兼容，不强制迁移；本体进化文档位于 `.wopal/docs/evolutions/`，不纳入新业务 Proposal 技能。
- `df-proposal-review` 原本同时审阅 Plan、DESIGN 和本体进化提案；本次增加**业务 Proposal 的独立语义审查与边界分流**，保留原本体/旧 Plan 的审查规则、报告结构和复审预算；同时发现当前 `df-proposal-review/SKILL.md:170` 与 `references/review-rubric.md:198,212` 在 Document mode 中仍残留已随子提案 1 退场的 `bidirectional index`（头部 `Sub-DESIGNs` 强枚举）与笼统 `target-state writing` 表述，须在本轮 Task 4 一并校准到最新 `dev-doc-master` 契约，避免新旧规则打架。
- Proposal 与 Plan 只有链接和有限交付证据，不同步两套实时进度表；Proposal 部分交付仍留在 `proposed/` 且保持 `Status: approved`。
- `.wopal/rules/coding-workflow.md`（及中文审核版）已在子提案 1 按最终目标态一次落盘并完整包含 `dev-proposal`、`/cupdate-proposal`、`df-proposal-review` 路由，本提案只核对并按需微调以保持与落地技能一致，**绝不倒退写回任何过渡期提示文案**；同时 `dev-proposal` 技能自身严格诚实守界：在子提案 4 改造 `dev-flow` CLI 前，不得假装或自动调用尚不存在的 Proposal→Plan CLI。

**References**:
- `.wopal/docs/evolutions/archived/20261122-enhance-doc-contracts.md`
- `.wopal/skills/dev-doc-master/{SKILL.md,references/design-project-guide.md,scripts/verify-docset.py}`
- `.wopal/skills/df-proposal-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`
- `.wopal/skills/dev-flow/SKILL.md`
- `.wopal/skills/ontology-evolution/{SKILL.md,templates/proposal.md}`
- `.wopal/rules/coding-workflow.md`
- `.wopal/assembly/{archetypes/coding.yaml,templates/command.md}`
- `labs/ref-repos/deepseek-harness/.agents/notes/{README.md,implemented/AGENTS.md,archived/AGENTS.md}`
- `labs/ref-repos/deepseek-harness/.agents/skills/{dsh-archive-agent-notes,dsh-prose-standard,dsh-code-review}/SKILL.md`
- `docs/products/wopal-space/proposals/development-governance-proposal.md`

### Key Decisions

- D-01：Proposal 只承载需要重要设计选择的产品/项目变更；普通缺陷或既有决定内的明确任务仍走 Issue，不因开发动作而机械创建 Proposal。
- D-02：Proposal 目录与生命周期严格对齐 DSH，并在 `dev-proposal` 技能中显式固化完整状态机图：在 `docs/products/{product}/proposals/` 与 `projects/{project}/docs/proposals/` 下建立 `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md` 结构，其中 `lifecycle` 为 `proposed | implemented | rejected | archived`（`archived/<class>/` 不含 `implemented`），`class` 为 DSH 固定六类闭集（`feature | bug-fix | simplification | architecture | process | testing`）；禁止单数 `proposal/` 与集中式 `INDEX.md`。新建为 `Status: proposed` 并存于 `proposed/<class>/`；用户批准后就地记为 `Status: approved`（文件**留在 `proposed/<class>/`** 避免实施期间 Plan 断链）；全部批准范围交付并经用户验收放行后，在同一交付中迁入 `implemented/<class>/` 并转为 `Status: implemented`；被否决则按“是否防止重犯有诱惑力的错误”决定移入 `rejected/<class>/`（`Status: rejected — <one-line reason>`）或直接删除；已完成使命且不再指导日常工作的 `implemented/` 记录可迁入 `archived/<class>/` 并于 `Status: implemented` 下一行追加 `Archived: YYYY-MM-DD` 永久冻结（严禁归档 `proposed/`；微小 UI 或纯机械变更不归档直接删除）。**精简原则**：绝不在 Proposal 中复制 Plan 的 `implementing`/`verifying`/`done` 过程状态。
- D-03：用户审批同时明确授权范围，并由**用户显式决定 `Delivery: direct | plan`**（`direct` 表示跳过 `dev-flow` 拆 Plan，由 `df-implement` 默认调用 `git-worktrees` 创建隔离工作树实施，不默认直接在主/集成分支上实施；`plan` 表示启用可选 `dev-flow` 拆解 Plan/Task 并由 `dev-flow` 管理隔离工作树与共享 Delivery；Agent 仅基于是否跨项目、是否需要多任务并行隔离等客观事实提供简短建议，严禁在技能中主观评判模型强弱来替用户选择执行路径）；新增决策或实质范围变更必须重新获得用户确认，格式脚本不能冒充真实授权。
- D-04：**已实施提案后续变更分流红线与交付证据边界**：
  - 仅存稳定 Source/关联 Plan/实际提交及评审验收证据；单个 Plan 完成或归档不自动改变 Proposal 状态；直接实施（`direct`）没有 Plan 也必须留痕。
  - **纯事实漂移（原决定未变）**：后续代码挪路径、改名或调整局部实现细节但设计决定与边界不变时，在同交付中**原地更新** `implemented/<class>/` 的事实描述（直接改现状，不新建提案、不追加变更日志）。
  - **设计调整 / 优化 / 局部推翻（部分替代）**：凡需要改变原决定、核心默认值、边界或需用户重新拍板的调整与优化（哪怕口头上称为“优化”或“局部增强”），**必须新建一份 `proposed/<class>/yyyy-mm-dd-<slug>.md` 提案**走独立评审与用户审批；**严禁把已 `implemented/` 提案退回 `proposed/` 或原地改写为另一项决定**；新提案在未全范围交付前**不得提前修改老 `implemented/` 提案**；全范围交付迁入 `implemented/<class>/` 时**同交付双向互链**（新提案写明部分替代了老提案的哪些决策以及老提案哪些决策继续有效，老提案把被替代段改为现状并链向新提案）。
  - **彻底推翻 / 功能下线（完全替代）**：必须新建提案；全范围交付时当场处置老 `implemented/`（不等日后大扫除）——吸收保留全部独特理由、备选方案、代价、验证与遗留缺口并修好全部入链后**删除旧文件**，或若仍有独立历史价值则迁入 `archived/<class>/` 永久冻结。
  - **已归档 `archived/` 提案**：永久只读冻结，绝不解冻修改；后续演进只能新建活跃提案并按需引用其作历史背景。
- D-05：严格对齐 DSH 正文骨架转换：`proposed/<class>/`（含 `proposed`/`approved` 态）使用未来时骨架（`## Problem` / `## Proposal` / `## Alternatives considered` / `## Acceptance criteria` / `## Risks`）；迁入 `implemented/<class>/` 时同交付机械改写为现在时骨架（`## Decision` 取代 `## Proposal`，`## Consequences` 吸收 `## Acceptance criteria` 与 `## Risks`，严禁残留 `## Proposal`、`## Plan`、`## Migration plan`、`## Acceptance criteria` 等计划期标题）；`rejected/` 保留提议期正文与 `Status: rejected — <one-line reason>`；`archived/` 仅插入 `Archived: YYYY-MM-DD` 后永久冻结且跳过出链检查。正文写作与可读性标准直接引用 `dev-doc-master`（含 `references/design-project-guide.md`），绝不重复抄写。
- D-06：本阶段可独立创建、评审、记录已批准业务 Proposal 与交付证据，但不自动触发尚未迁移的 `dev-flow` Proposal→Plan CLI；该执行门禁留待子提案 4 切换开放。`.wopal/rules/coding-workflow.md`（及中文审核版）保持子提案 1 已落地的最终目标态，本提案仅核对其与实际落地的 `dev-proposal`、`/cupdate-proposal`、`df-proposal-review` 名称与契约一致，绝不倒退写回过渡期免责文案。
- D-07：`df-proposal-review` 新增业务 Proposal 独立只读审查模式，审查问题成立性、备选方案、决策边界、是否违规原地改写已有 `implemented/` 决策（以及部分/完全替代边界是否清楚）、风险和可测试结果；明确当审阅由已批准 Proposal 派生的 Plan 时，只核查实施方案质量、任务衔接与不超出 Proposal 批准范围，**绝不把 Plan 质检变成第二次设计审批**；完整保留 `Cost-benefit gate`（投入产出门槛）与 `Review-scope gate`（评审范围门槛）；同时校准其 Document mode 中与子提案 1 冲突的旧 `bidirectional index` / 笼统 `target-state writing` 表述；保留旧本体提案与旧 Plan 的审查规则、报告结构和 2 轮收敛目标，不代替用户审批。
- D-08：新增 `dev-proposal` 和修改后的 `df-proposal-review` 都必须有**精准简洁的 `description` 与 10+10 正反触发验证**：前者在业务 Proposal 的必要性判断、创建、演进分流、审批记录、迁移与归档清理时加载（普通 Bug/Issue 不强行触发）；后者在**独立只读审查**业务 Proposal、已有 Plan、设计文档或本体进化提案时加载，不因 Proposal 的普通写作/状态维护而误触发。两者不能因“Proposal”一词混淆作者与只读审查者职责。
- D-09：**本体现状设计文档同交付落盘**：践行 DSH 现状文档同交付机制，在本提案全部技能与脚本验证通过后，同交付创建本体现状子设计文档 `.wopal/docs/DESIGN-coding-workflow.md`（仅记录已落地的子提案 1 底座能力 + 本提案刚落地的 `dev-proposal` 与 `df-proposal-review` 真实状态机、契约与边界，绝不提前写入尚未落地的子提案 3/4 能力），并在 `.wopal/docs/DESIGN.md` 的 `## Module Architecture` 挂接链接，运行 `dev-doc-master/scripts/verify-docset.py` 校验通过。

### Key Interfaces

- 新技能：`.wopal/skills/dev-proposal/{SKILL.md,SKILL.zh-CN.md}`、配套 `references/`、`templates/`（`proposed` 未来时与 `implemented` 现在时骨架模板）与确定性校验器 `.wopal/skills/dev-proposal/scripts/verify-proposals.py`（及隔离测试）。
- 方案评审：`.wopal/skills/df-proposal-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`，新增业务 Proposal 审查模式并校准 Document mode 旧表述，保持现有报告格式与 2 轮复审目标。
- 薄命令：`.wopal/commands/cupdate-proposal.md` 及中文审核版 `.wopal/docs/LANG/zh-CN/commands/cupdate-proposal.md`（按 `.wopal/assembly/templates/command.md` 编写），只路由到 `dev-proposal`，不复制生命周期算法。
- 装配清单与空间调用规则：在 `.wopal/assembly/archetypes/coding.yaml` 落实 `Assembly Intent`（挂载 `skill:dev-proposal` 与 `command:cupdate-proposal.md`）；核对并按需同步 `.wopal/rules/coding-workflow.md` 及 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`，保持最终目标态契约一致，不加入过渡期文案。
- 新 Proposal 文件路径：`projects/{project}/docs/proposals/{lifecycle}/{class}/yyyy-mm-dd-<slug>.md` 或 `docs/products/{product}/proposals/{lifecycle}/{class}/yyyy-mm-dd-<slug>.md`（`lifecycle ∈ {proposed, implemented, rejected, archived}`，`class ∈ {feature, bug-fix, simplification, architecture, process, testing}`）；拒绝单数 `proposal/`、未知分类目录或集中 `INDEX.md`；对既有存量前格式文件保持历史只读兼容。
- 确定性校验器（`scripts/verify-proposals.py`）检查契约（仅限单快照静态确定性规则，不引入历史数据库、冻结哈希清单、Git 历史比对或跨仓库全量扫描）：
  1. 目录结构与分类闭集校验：拒绝单数 `proposal/`、未知分类目录或集中 `INDEX.md`，校验 `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md` 命名规范（对存量前格式文件保持历史只读兼容）；
  2. 路径 `{lifecycle}` 与文件头 `Status` 一致性校验：`proposed`/`approved` 仅允许位于 `proposed/`，`implemented` 仅允许位于 `implemented/` 或带有效 `Archived: YYYY-MM-DD` 的 `archived/`，`rejected — <reason>` 仅允许位于 `rejected/`（单快照层面可发现如 `implemented/` 中误写 `Status: proposed` 或 `archived/` 缺日期/状态不符等静态失配）；
  3. 生命周期骨架校验：`proposed/` 必填 `## Problem`、`## Proposal`、`## Alternatives considered`、`## Acceptance criteria`、`## Risks`；`implemented/` 必填 `## Problem`、`## Decision`、`## Alternatives considered`、`## Consequences` 且禁用计划期标题；`rejected/` 必填 `## Problem`、`## Proposal`、`## Alternatives considered`；
  4. 授权与交付字段校验：`Status: approved` 必须具备明确用户批准记录、授权范围与 `Delivery: direct | plan`（格式校验不替代或伪造真实用户批准）；
  5. 普通链接与 `archived/` 边界校验：校验非冻结目录文件的相对出链可达且无绝对路径，支持当前提案目录/给定文档目录内的本地入链断链扫描；对 `archived/` 文件只校验目录位置、`Status: implemented` 与 `Archived: YYYY-MM-DD` 元信息，不编辑它也不校验其出链。跨提交的历史状态回退（如把曾为 `implemented/` 的文件移回 `proposed/`）与已归档正文篡改由 Agent 行为规范与正常评审把关，不靠脚本维护历史状态库或哈希清单。

## In Scope

- **`dev-proposal`（新增技能 — 能力落地与精简边界）**：
  - **建立/优化**：明文固化完整 Proposal 状态机图；Proposal 必要性判定、起草前同主题审计与**已实施提案后续变更分流决策树**（纯事实原地同步 / 凡设计调整或优化必须新建 `proposed/` 提案并同交付双向互链 / 完全替代吸收删除或归档冻结 / `archived/` 永不解冻）；用户批准记录与由用户显式决定的 `Delivery: direct | plan`；双骨架模板（`proposed` 未来时与 `implemented` 现在时，提案阶段不动现状 DESIGN，正文规范引用 `dev-doc-master`）；轻量静态确定性校验器 `scripts/verify-proposals.py`、薄命令 `/cupdate-proposal` 与双语资产、`.wopal/assembly/archetypes/coding.yaml` 装配挂载。
  - **明确精简**：不引入 `implementing`/`verifying`/`done` 过程状态；不引入集中 `INDEX.md` 或 `.i18n.yaml` 双语配对；`verify-proposals.py` 仅做单快照静态检查（不建历史数据库、冻结哈希清单或跨仓库扫描）；不让 Agent 凭主观猜模型强弱代替用户选 `direct`/`plan`；不复制 `dev-doc-master` 细则。
- **`df-proposal-review`（修改技能 — 优化与精简边界）**：
  - **优化**：新增业务 Proposal 独立只读审查模式（含替代/演进合规检查）；明确审阅已批准 Proposal 派生的 Plan 时只核查实施方案质量与不超范围、不触发第二次设计审批；保留 `Cost-benefit gate` 与 `Review-scope gate`；同步校准 Document mode 中与子提案 1 冲突的旧 `bidirectional index` 与笼统 `target-state writing` 表述。
  - **精简**：不新造替代语义评审的关键字门禁脚本，不改变既有报告结构与 2 轮收敛目标，不扩大既有触发范围。
- **规则核对与本体现状设计同交付**：核对并按需同步 `.wopal/rules/coding-workflow.md`（及中文审核版）保持最终目标态一致（不写过渡期说明）；同交付创建本体现状子设计文档 `.wopal/docs/DESIGN-coding-workflow.md`（记录已落地的子提案 1+2 现状）并在 `.wopal/docs/DESIGN.md` 挂接链接；依据 `skill-creator` 完成 `dev-proposal` 与 `df-proposal-review` 各 10+10 近邻触发验证。

## Out of Scope

- 不修改现有任何真实业务 Proposal，不迁移已存在的存量产品/项目目录。
- 不修改 `dev-flow` 脚本的来源与状态机、不触发真实业务 Proposal 的实施、不改变 `ontology-evolution`。
- 不改 `df-implement` 与 `df-implement-review`（它们在子提案 3 `enhance-implement-sync` 中改造）。
- 不引入额外文档数据库、Proposal `implementing` 状态或独立的实时进度同步程序。

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| Proposal 技能 | `.wopal/skills/dev-proposal/{SKILL.md,SKILL.zh-CN.md,references/*,templates/*,scripts/verify-proposals.py}` | create | 业务 Proposal 生命周期、再变更分流、写作模板与确定性校验器 |
| 方案评审 | `.wopal/skills/df-proposal-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}` | modify | 新增业务 Proposal 独立只读语义审查并校准 Document mode 旧表述 |
| 命令入口 | `.wopal/commands/cupdate-proposal.md`, `.wopal/docs/LANG/zh-CN/commands/cupdate-proposal.md` | create | 薄入口命令及中文审核版 |
| 装配清单 | `.wopal/assembly/archetypes/coding.yaml` | modify | 按 `Assembly Intent` 挂载 `skill:dev-proposal` 与 `command:cupdate-proposal.md` |
| 空间调用规则 | `.wopal/rules/coding-workflow.md`, `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` | modify (verify / align as needed) | 核对并保持最终目标态与落地技能/命令一致，不写过渡期文字 |
| 本体现状设计 | `.wopal/docs/DESIGN-coding-workflow.md`（create）、`.wopal/docs/DESIGN.md`（modify） | create / modify | 同交付沉淀已落地的子提案 1+2 技能现状设计与状态机，并在主地图挂链 |
| 隔离测试 | `.wopal-space/.tmp/` 隔离验证脚本与 fixtures（验证后按规范清理）或技能内部回归测试 | create | 覆盖目录/状态/授权/演进分流/归档冻结与更名入链正负行为 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|
| skill:dev-proposal | type-default | 为 coding 空间提供业务/项目 Proposal 编写、演进分流、审批记录与维护能力 |
| command:cupdate-proposal.md | type-default | 业务/项目 Proposal 薄命令入口 |

## Acceptance Criteria

### Agent Verification

1. [x] 新重大设计从旧决定/当前事实检索后进入 `proposed/<class>/yyyy-mm-dd-<slug>.md`；常规 Bug 不被错误要求建立 Proposal；提案阶段与实施后骨架均遵循 DSH 结构与 `dev-doc-master` 写作标准。
2. [x] 产品与项目 `proposals/{proposed,implemented,rejected,archived}/{feature,bug-fix,simplification,architecture,process,testing}/yyyy-mm-dd-<slug>.md` 结构可创建且可检索；单数 `proposal/` 目录、未知分类目录、集中 `INDEX.md`、路径与 `Status`/骨架静态失配、`archived/` 缺少 `Archived: YYYY-MM-DD` 或非 `implemented` 状态、以及当前提案树内的相对断链均被 `verify-proposals.py` 拒绝并给出可复现的修复指引（不建历史数据库、冻结哈希清单或跨仓库扫描）。
3. [x] 未批准、被否决（留存 `rejected/` vs 删除）、部分实施（仍留 `proposed/`）、全部交付迁入 `implemented/` 并切换 `Decision`/`Consequences`、**已实施提案后续变更三类分流（纯事实原地改 / 设计调整与优化新建 `proposed/` 提案并同交付双向互链、严禁退回 `implemented/` 或未落地前改老提案 / 完全替代吸收删除或归档冻结）**、`archived/` 永久冻结与范围变更等规则与正负例准确（静态路径/状态/骨架/授权字段由 `verify-proposals.py` 校验，跨提交回退与归档内容篡改由 Agent 规则与评审把关）；未获用户授权不得跳跃到 `approved`/`implemented`，格式检验不能伪造审批。
4. [x] `Delivery: direct` 和 `plan` 都可记录实际证据；Plan 的 done/archive 不会使 Proposal 自动 `implemented`；在 `dev-flow` 改造前不会启动尚未支持的实施入口。
5. [x] 技能、薄命令、模板、校验器、`.wopal/assembly/archetypes/coding.yaml` 挂载与最终目标态 `.wopal/rules/coding-workflow.md` 中英文语义一致（无过渡期文案残留）；`Assembly Intent` 声明正确且全树装配检查通过；同交付产出的本体现状设计 `.wopal/docs/DESIGN-coding-workflow.md`（仅记载已落地的子提案 1+2 真实能力）与 `.wopal/docs/DESIGN.md` 地图链接通过 `verify-docset.py` 校验；真实业务文件没有被改写。
6. [x] `df-proposal-review` 能指出遗漏替代方案、缺少可验证结果、决策边界不清、违规原地改写 `implemented/` 决策（未新建替代提案或未说明替代边界）、将局部交付冒充全部实施等问题；正确业务 Proposal 通过，旧 Plan、本体进化提案与校准后的 Document mode（与子提案 1 现状 DESIGN 规则一致）审查行为准确无回退。
7. [x] `dev-proposal` 和 `df-proposal-review` 的中英 `description` 简洁、职责/阶段清楚；每个技能完成 **10 个应触发 + 10 个不应触发** 的实际近邻请求检查，覆盖 Proposal 写作/演进分流 vs 独立评审、普通 Issue/Bug、Plan 审查、本体进化提案和实施后代码评审。记录改前/改后 `description`、误触发/漏触发与修订结果；无真实触发运行时明确标注未自动验证。

### DSH Principles → Tasks → Verification

| DSH 已验证来源 | 本提案取用的实践 | Task 与验收 |
|---|---|---|
| `labs/ref-repos/deepseek-harness/.agents/notes/{README.md,implemented/AGENTS.md,archived/AGENTS.md}` & `dsh-archive-agent-notes/SKILL.md` | 完整对齐 `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md` 目录体系（不含 `.agents/notes/` 与双语 `.i18n.yaml` 配对）、正文字段转迁、`implemented/` 事实原地同步、**设计变更严禁原地篡改原决策（部分替代新建互链 / 完全替代吸收删除或冻结归档）**、`rejected` 判据与 `archived/` 永久冻结；保留本空间的用户显式审批与 `Delivery: direct \| plan` | Task 1、2、3；AC#1–4 |
| `labs/ref-repos/deepseek-harness/docs/AGENTS.md` | 一项决定一个归属，目录/链接稳定；不另建重复索引与进度台账 | Task 1、3；AC#2、4 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-prose-standard/SKILL.md` | 保留授权条件、失败保证与备选决策的完整语义，禁止只有术语和空模板 | Task 1、4；AC#1、6 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-code-review/SKILL.md` | 区分确定性格式检查与基于真实事实的语义评审 | Task 2、4；AC#3、6 |

`Delivery: direct | plan`、用户授权字段以及“禁止把已 `implemented/` 提案退回 `proposed/` 重新走审批”的门禁是 **WopalSpace 的自有设计**，不是 DSH 已有的命令/审批流程。

### User Validation

#### Scenario 1: 产品/项目提案样例与状态理解
- Goal: 用户能独立看懂设计选择、交付方式、未完成范围、已实施提案后续优化的演进关系与最终决定。
- Environment: 隔离 fixtures 的虚构 Proposal 样例（含新建 `proposed`/`approved`、部分实施、全交付迁入 `implemented/` 与对已实施提案发起设计优化的新提案互链）。
- Precondition: 实施完成并经独立评审，进入 validating（或按用户安排与子提案 3–4 统一验收）。
- Launch command: `wopal space evo switch enhance-dev-proposal`（切换后**重启 ellamaka** 以加载新技能、命令与更新后的规则）
- User Actions:
  1. 阅读 `proposed`、`approved`、部分实施与“对已实施提案发起设计优化”的新旧互链样例，检查界限是否清楚。
  2. 确认没有要求自己阅读代码或重复批准相同设计。
- Pass criteria: 决策、原因、替代关系、已交付/未交付内容和所需授权一目了然。
- Failure feedback: 指出状态/理由/演进规则/证据中不可理解或不完整的位置。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 设计对齐 DSH 的 Proposal 目录分类、骨架、再变更分流与文件合同

**Verification Intent**: AC#1、AC#2、AC#3
**Behavior**: 有重要设计变化时使用业务 Proposal；目录按 `{proposed,implemented,rejected,archived}/{class}/yyyy-mm-dd-<slug>.md`（`class` 为 DSH 6 类闭集）组织，路径、生命周期骨架与链接稳定；起草前审计同主题现存提案，明确落实“纯事实原地改 / 设计调整与优化必须新建 `proposed/` 提案并禁止回退 `implemented/` / 完全替代吸收删除或归档冻结 / `archived/` 永不解冻”的决策树。
**Pre-read**: 产品总提案的 Proposal 规范、`.wopal/AGENTS.md`、`skill-creator` 技能、DSH `.agents/notes/{README.md,implemented/AGENTS.md,archived/AGENTS.md}`、`.agents/skills/dsh-archive-agent-notes/SKILL.md`、已交付的 `dev-doc-master`（含 `references/design-project-guide.md`）与 `.wopal/rules/coding-workflow.md`。
**Design**: 用单一技能 `dev-proposal` 管理必要性判定、目录树布局、骨架模板（`proposed` 未来时 vs `implemented` 现在时）、已实施提案再变更分流、替代合并与归档清理规则；先写中文审核版 `SKILL.zh-CN.md` 及参考/模板再同步英文正式版；Proposal 仍为用户决策文本，非 Plan、非 DESIGN；正文表达规范直接引用 `dev-doc-master` 绝不抄写；不把具体项目路径写死在通用规则里，且兼容既有前格式存量文件。
**TDD**: false — 规范、模板和路径契约设计以例证与审查优先。
**Changes**: `.wopal/skills/dev-proposal/{SKILL.md,SKILL.zh-CN.md,references/*,templates/*}`，定义路径、分类、骨架与再变更分流契约。
**Verify**: 创建合法样例（product/project、`proposed`/`approved`/`implemented`/`archived` 及部分替代双向互链）与非法反例（单数目录、未知分类、混留计划期标题、直接把 `implemented/` 改回 `proposed/`），对照契约逐项审核；同时确定 `dev-proposal` `description` 的必加载/不适用意图及与相邻技能的区分，不靠关键词堆砌。
**Done**:
Task output: 新增 `dev-proposal` 技能与配套参考/模板（先中文审核版 `SKILL.zh-CN.md`、`references/*.zh-CN.md`、`templates/*.zh-CN.md`，再同步英文正式版）。技能明文固化：完整生命周期状态机（`proposed → approved → implemented → archived`，`rejected` 旁路，`archived/` 无 `implemented` 层）、`{lifecycle}/{class}/yyyy-mm-dd-<slug>.md` 两轴布局与六类闭集、禁用单数 `proposal/`／集中 `INDEX.md`／`.i18n.yaml` 配对、存量前格式只读兼容；`approved` 留在 `proposed/` 防断链、不引入 `implementing`/`verifying`/`done`、部分交付不迁移、Plan 完成不自动 `implemented`；用户显式决定 `Delivery: direct | plan` 且 `direct` 默认由 `df-implement` 配 `git-worktrees` 隔离实施，严禁 Agent 主观评判模型强弱代选；已实施提案再变更三类分流（纯事实原地同步／设计调整与优化必须新建 `proposed/` 并禁止退回 `implemented/` 或未全交付前改老提案、全交付双向互链／完全替代吸收删除或归档冻结，`archived/` 永久只读）；`proposed` 未来时与 `implemented` 现在时双骨架模板，正文写作标准直接引用 `dev-doc-master` 不抄写；诚实边界声明不假装调用尚不存在的 Proposal→Plan CLI。验证：契约审计 31 条全部 PASS（含中英双份与通用性检查，技能资产不含空间名/项目路径/本地语言标签），非法反例 12 条逐条映射到对应拒绝条款、合法样例 5 条（`approved` 三字段、部分替代互链、`implemented` 现在时骨架、`archived` 冻结元信息、`rejected` 状态行理由）全部 PASS，模板英文章节标题在中文审核版中保留且正文节数一致。
Files touched: `skills/dev-proposal/SKILL.md`（create）、`skills/dev-proposal/SKILL.zh-CN.md`（create）、`skills/dev-proposal/references/lifecycle.md`（create）、`skills/dev-proposal/references/lifecycle.zh-CN.md`（create）、`skills/dev-proposal/references/evolution-triage.md`（create）、`skills/dev-proposal/references/evolution-triage.zh-CN.md`（create）、`skills/dev-proposal/templates/proposal-proposed.md`（create）、`skills/dev-proposal/templates/proposal-proposed.zh-CN.md`（create）、`skills/dev-proposal/templates/proposal-implemented.md`（create）、`skills/dev-proposal/templates/proposal-implemented.zh-CN.md`（create）
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 2: 审批、生命周期迁移、演进分流与确定性静态校验器

**Verification Intent**: AC#2、AC#3、AC#4
**Behavior**: `proposed`（含 `approved` 留存防断链）→ `implemented`（迁移+正文转现在时 `Decision`/`Consequences`）/ `rejected`（留存或删除）→ `archived`（去 `implemented` 层+`Archived: YYYY-MM-DD` 永久冻结）的当前快照形态可机械验证；部分实施不提前迁入 `implemented/`；Agent 规则明确 `implemented/` 仅允许原地同步事实（严禁退回 `proposed/` 或未落地前修改老提案）与 `archived/` 永久只读冻结，由正常评审把关；`direct`/`plan` 证据要求一致。
**Pre-read**: Task 1、`ontology-evolution` 的用户授权规则、DSH `dsh-archive-agent-notes/SKILL.md` 校准标准与归档规范、`.wopal/rules/testing.md`、旧 `dev-flow` 的 approve 入口和直接实施限制。
**Design**: TDD 编写 `.wopal/skills/dev-proposal/scripts/verify-proposals.py`（纯 Python 标准库，只做单快照静态确定性检查）：校验目录生命周期与 `Status` 匹配、六类闭集、零 `INDEX.md` / 零单数 `proposal/`、骨架必填与禁用标题、授权与 `Delivery: direct | plan` 字段、`archived/` 必填 `Archived: YYYY-MM-DD` 且不查其出链、以及非冻结目录的相对出链与本地入链断链扫描；明确不建历史数据库、冻结哈希清单、Git 历史回退比对或跨仓库全量扫描；不得自动用 Proposal 去执行旧 CLI，也不引入实时 Task 表。
**TDD**: true — 目录/状态静态失配（含 `implemented/` 误写 `Status: proposed` 或残留计划期标题、`archived/` 缺 `Archived: YYYY-MM-DD` 或非 `implemented` 状态）、缺授权/`Delivery` 字段、断链/非法分类/单数目录/集中 `INDEX.md`、以及合法迁移与双向互链快照全部由正负自动化用例驱动（RED → GREEN）。
**Changes**: `.wopal/skills/dev-proposal/scripts/verify-proposals.py`、演进/状态/归档参考细化与隔离自动化测试 fixtures。
**Verify**: 在隔离临时目录运行自动化测试套件与 `python3 scripts/verify-proposals.py` 覆盖全部正负例，确认通过且无真实仓库写入。
**Done**:
Task output: TDD 落地纯 Python 标准库静态校验器 `scripts/verify-proposals.py`（argparse/json/re/sys/pathlib，无第三方依赖、无 subprocess、无 hashlib、不读 `.git`）与隔离回归套件 `scripts/test_verify_proposals.py`。RED 先行：47 条用例在实现缺失时全部失败（`can't open file ... verify-proposals.py` + 31 errors/14 failures），实现后 47/47 ok。覆盖面：目录与六类闭集、单数 `proposal/`、集中 `INDEX.md`、`archived/implemented/` 深层、文件名日期前缀、路径↔`Status` 双向失配、`rejected` 缺一行理由、`approved` 三字段（`Approved`/`Authorized scope`/`Delivery`）与 `direct|plan` 闭集、`archived/` 必填 `Archived: YYYY-MM-DD` 且必须 `Status: implemented`、`implemented/` 四个计划期标题禁用、`proposed`/`implemented`/`rejected` 骨架必填、相对断链与绝对路径、前格式存量只读兼容（默认跳过、`--strict` 变失败）、缺失根目录不崩栈。判别力用 4 个变异体验证：关闭状态/路径校验、关闭禁用标题校验、跳过授权校验、把全部文件当 legacy——分别被 4/5/4/25 条用例击杀。另补 `--link-scope <dir>`（可重复）把引用 Proposal 的外部文档纳入扫描，让「更名/删除后入链断链」在调用方被发现；隔离实测迁移链 `proposed → implemented → archived` 与重命名后未修链（FAIL）/修链后（PASS）/归档后出链失效仍 PASS 全部符合契约。脚本明确不含历史数据库、冻结哈希清单、Git 历史回退比对与跨仓库全量扫描。
Files touched: `skills/dev-proposal/scripts/verify-proposals.py`（create）、`skills/dev-proposal/scripts/test_verify_proposals.py`（create）、`skills/dev-proposal/references/lifecycle.md`（modify）、`skills/dev-proposal/references/lifecycle.zh-CN.md`（modify）
Review fix: 独立实施后评审（BLOCKER 4 / WARNING 5 / INFO 2）已全部处置。校验器补齐状态行唯一性、`Class`/`Created` 必填、`Approved` 真实日期与批准人、`Archived` 紧贴 `Status: implemented`、父目录入口下并存的单数 `proposal/`、文件名与 `Created` 日历合法性、`/home/` 与 `/root/` 绝对路径，并让根目录游离 Markdown 显式报跳过而非静默忽略；29 个问题码全部有 `FIX_HINTS` 且各有能独立失败的用例。用例 47 → 77（RED 先行 14 条失败 → GREEN 77 通过），7 个变异体全部被击杀。评审建议中 slug 词数与章节顺序两项经判断属写作约定而非结构不变量，未纳入机械校验（已在 `lifecycle.md` 写明该边界）。第二轮复审追加：`/home/`、`/root/` 定向识别曾误伤 `https://example.com/home/...` 等合法外链，已改为按命中位置判断——落在 URL 区间内的绝对路径片段不算本地路径，URL 之外的真实本地路径仍照常拦截；用例 83 条，4 个变异体（含「豁免过宽」方向）全部被击杀。
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 3: 命令路由、装配挂载、规则核对、改名入链维护与 `dev-proposal` 触发收敛

**Verification Intent**: AC#2、AC#4、AC#5、AC#7
**Behavior**: `/cupdate-proposal` 稳定路由至 `dev-proposal`；`.wopal/assembly/archetypes/coding.yaml` 完整挂载新技能与命令；移动/更名/删除后入链断链可检测并修复；`.wopal/rules/coding-workflow.md`（及中文审核版）保持最终目标态且与实际落地的 `dev-proposal`、`/cupdate-proposal` 契约完全一致（不写入任何过渡期文字）；后续 `dev-flow` 能读取唯一稳定的 Source 路径。
**Pre-read**: Task 1–2、`.wopal/assembly/templates/command.md`、`.wopal/commands/cupdate-design.md`、`.wopal/assembly/archetypes/coding.yaml`、`.wopal/rules/coding-workflow.md`（及中文审核版）、`skill-creator` 技能、`dev-flow` 计划中的 Source 契约。
**Design**: 命令严格按 `.wopal/assembly/templates/command.md` 保持薄入口（`description ≤ 50 chars`）并同步中文审核版；在 `coding.yaml` 挂载 `skill:dev-proposal` 与 `command:cupdate-proposal.md`；核对 `coding-workflow.md` 中英最终目标态仅做必要措辞对齐，绝不倒退写回过渡期免责声明；`dev-proposal` 对尚不支持 Proposal 来源的旧 `dev-flow` 保持诚实拒调边界。
**TDD**: true — 覆盖迁移（`proposed/` → `implemented/` → `archived/`）、更名与完全替代删除后的入链修复/断链拦截以及命令路由与装配引用解析检查。
**Changes**: `.wopal/commands/cupdate-proposal.md`、`.wopal/docs/LANG/zh-CN/commands/cupdate-proposal.md`、`.wopal/assembly/archetypes/coding.yaml`、按需微调 `.wopal/rules/coding-workflow.md` 及 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`、以及相关测试。
**Verify**: 在隔离产品/项目样本运行新建（`proposed/<class>/`）、审核、目录迁移（`proposed/` → `implemented/` → `archived/` + 入链修复）、更名/删除断链检测与非法输入模拟；验证命令路由与全树装配引用解析；核对 `coding-workflow.md` 中英一致且零过渡期文案；针对 `dev-proposal` 完成 10+10 正反触发测试和描述收敛，不能误入独立只读评审流程。
**Done**:
Task output: 新增薄命令 `commands/cupdate-proposal.md`（`description` 46 字符 ≤ 50，四步：加载契约 → 定归属与起点 → 执行 → 校验，只路由 `dev-proposal`，不复制生命周期算法）及中文审核版 `docs/LANG/zh-CN/commands/cupdate-proposal.md`（`description` 20 字符，步骤与要点数一致）。`assembly/archetypes/coding.yaml` 挂载 `skill:dev-proposal` 与 `command:cupdate-proposal.md`；全树装配引用解析实测 47 项引用（4 agents / 15 skills / 6 rules / 19 commands / 2 plugins）全部 OK，0 unresolved。核对 `rules/coding-workflow.md` 及中文审核版：已处于子提案 1 落盘的最终目标态，过渡期文案扫描（尚未/暂未/过渡/temporary/not yet/TODO 等）零命中，故本轮不改其内容；EN/ZH 结构对账（frontmatter keywords 20 项完全一致、`trigger` 同为 `model_decision`、H2 3 / H3 2、路由表 9 行、跨层硬约束 1-2-3）全部 PASS，且规则中提到的 `dev-proposal`、`cupdate-proposal`、`df-proposal-review` 等名称与实际落地的 skill/command 一一对应。`dev-proposal` 保持诚实边界：正文明确「在 `dev-flow` 支持前不要假装或自动调用不存在的 Proposal→Plan 命令」，中英一致；引用到的 `dev-flow`、`df-implement`、`git-worktrees`、`df-proposal-review`、`dev-doc-master` 均为已存在技能。依 `skill-creator` 完成 `dev-proposal` 10+10 近邻触发验证：10 条应触发（写提案/记录批准与 Delivery/迁移 implemented/归档清理/已实施提案调整分流）全部正确归入 `dev-proposal`，10 条不应触发分别正确落到 `df-proposal-review`（独立评审）、`df-implement-review`（实施后评审）、`dev-doc-master`（PRD、DESIGN 拆分）、`dev-flow`（Plan 拆解）、`space-master`（AGENTS.md）、`ontology-evolution`（本体进化）或无人认领（一次性脚本、普通 Bug 修复），0 误触发 0 漏触发；`description` 的排除子句逐项覆盖普通 Bug、独立评审、PRD/DESIGN、本体提案与 Plan 编排五类近邻，未堆砌关键词。验证限制：当前环境无法对真实模型做运行时注入触发，故采用确定性路由核对（收集全仓已挂载技能 `description` + 逐条标注期望归属）替代，真实触发仍需重启 ellamaka 后人工抽检。
Files touched: `commands/cupdate-proposal.md`（create）、`docs/LANG/zh-CN/commands/cupdate-proposal.md`（create）、`assembly/archetypes/coding.yaml`（modify）
Review fix: `rules/coding-workflow.md` 与中文审核版的路由表补一句：已批准 Proposal 中记录的 `Delivery` 选择优先于「简单有界任务直接 `df-implement`」的经验判断（W-01）；中英同步，未加入过渡期文案，装配引用复检 46 项全部可解析。
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 4: 将业务 Proposal 评审能力并入 `df-proposal-review`、校准 Document mode 旧表述并同交付沉淀本体现状设计

**Verification Intent**: AC#1、AC#3、AC#5、AC#6、AC#7

**Behavior**: 业务 Proposal 提交用户批准以前，`df-proposal-review` 对问题成立性、备选方案、明确决策边界、对既有 `implemented/` 提案的替代关系（拦截违规原地篡改旧决策或未落地前改写老提案）、风险和可复现实证进行独立只读审查；审阅已批准 Proposal 派生的 Plan 时只核查实施方案质量与不超范围，不触发二次设计审批；不能把“已批准”误当作质量合格，不能因为格式有效就放过没有设计依据的决定；同时 Document mode 与子提案 1 交付的现状 DESIGN 规则对齐（去掉过时的 `bidirectional index` 与笼统 `target-state writing` 冲突表述）；旧本体提案/Plan 的审查规则、报告结构与 2 轮收敛目标保持不变；收口时同交付创建本体现状子设计 `.wopal/docs/DESIGN-coding-workflow.md`（仅记录已落地的子提案 1+2 现状与状态机）并在 `.wopal/docs/DESIGN.md` 挂链。

**Pre-read**: Task 1–3、`skill-creator` 技能、`df-proposal-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`、`dev-doc-master/{SKILL.md,references/design-project-guide.md,scripts/verify-docset.py}`、`.wopal/docs/{DESIGN.md,DESIGN-capabilities.md}`；DSH `.agents/notes/README.md`、`dsh-prose-standard/SKILL.md`；本体进化/历史 Plan 的原报告和复审要求。

**Design**: 在当前最新 `df-proposal-review`（完整保留 `Cost-benefit gate` / 投入产出门槛与 `Review-scope gate` / 评审范围门槛）基础上，新增业务 Proposal 审查模式分流，只读评估“是否值得做、为何选它、是否越界、是否违规篡改已有决策、能否验收”，并写明审阅由已批准 Proposal 派生的 Plan 时不触发第二次设计审批；同步校准 Document mode 中指向 `dev-doc-master` 的过时描述（不要求主文档头部 `Sub-DESIGNs` 枚举，明确产品 DESIGN 前瞻 vs 项目/模块 DESIGN 现状）；保留既有报告分类与 2 轮复审目标；不额外创建替代语义判断的关键字脚本；按 `dev-doc-master` 现状设计规范同交付落盘 `.wopal/docs/DESIGN-coding-workflow.md` 与 `.wopal/docs/DESIGN.md` 模块地图链接。

**TDD**: false — 语义判断由正确业务 Proposal、缺备选方案、缺授权边界、违规原地篡改 `implemented/` 决策、错误夸大已交付范围等实证样例进行盲审；本体现状设计以 `verify-docset.py` 与语义检查核验。

**Changes**: `.wopal/skills/df-proposal-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}`、`.wopal/docs/DESIGN-coding-workflow.md`（新增）与 `.wopal/docs/DESIGN.md`（模块地图链接更新）。

**Verify**: 分别盲审正确与缺陷业务 Proposal（含“违规原地篡改已实施提案”反例）、一份历史 Plan、一份旧本体提案与一份无 `Sub-DESIGNs` 头部的多模块现状 DESIGN；报告须指出明确问题和证据，不改变既有结构与复审目标；运行 `verify-docset.py` 核验本体设计文档（确认无未落地能力冒充现状）；针对 `df-proposal-review` 完成 10+10 正反触发测试，涵盖写作/演进分流、实施后代码评审和旧审查正例，记录改前/改后 `description` 与结果。

**Done**:
Task output: 升级 `df-proposal-review`（SKILL.md / SKILL.zh-CN.md / references/review-rubric.md / references/review-rubric.zh-CN.md 四份同批同步，中英 H2+H3 数分别为 36/36 与 44/44，完全对齐）。新增**业务 Proposal 只读审查模式**（P1 决策是否真的定下来——含批准链与"格式有效≠授权"；P2 事实核实；P3 备选方案真实性 + 替代/演进合规台账，明确拦截原地改写 `implemented/`、退回 `proposed/`、未全交付先改老记录、完全替代后新老并存等四类 Blocker；P4 可证伪性含部分交付不得冒充全部；P5 精简），并单列「审阅由已批准 Proposal 派生的 Plan」小节：只核查范围忠实度、覆盖完整、顺序交接，明确不做第二次设计审批，内部手法差异不算 finding。**完整保留** `Cost-benefit gate`（投入产出门槛）与 `Review-scope gate`（评审范围门槛）原文，保留 Plan 模式 Q1–Q4、Document 模式 D1–D4、报告结构、PASS/REVISE/BLOCK 三裁决与 2 轮收敛目标（技能目录仍无脚本层，不新造语义关键字门禁）。校准 Document 模式两处过时表述：删除 `bidirectional index`（主 DESIGN 头部 `Sub-DESIGNs` 强枚举），改为"子文档靠 `DESIGN-*.md` 文件名 + `Parent` 链接发现、主文档正文链下来、无头部索引是正确的"，并明确把"头部没列子文档"判为误报方向；把笼统 `target-state writing` 拆成按文档类型分别判定（项目/模块现状 DESIGN 只写已交付现实、禁历史叙述；产品 PRD/产品 DESIGN 允许前瞻，仅过程叙事与虚假上线声明算问题）。四份文件 `bidirectional index`/`双向索引`/`target-state writing`/`目标态写作` 残留计数全部为 0。
验证：① 盲审 5 份隔离样例（主控亲自只读评审，未委派 Fae、未调用 Rook，遵守本提案 Delegation Strategy）：`good` 脚本 PASS → 语义 PASS；`missing-alternatives`（把备选章节改名）脚本 FAIL(SKELETON_MISSING_SECTION) → 语义 REVISE；`no-boundary`（唯一 AC 为"更干净更好维护"且无边界）脚本 PASS → 语义 BLOCK；`tampered`（原地把 `implemented/` 的 Decision 改成新行为、仍是 `Status: implemented`）脚本 PASS → 语义 BLOCK（P3 反例命中）；`overclaim`（已迁 `implemented/` 且写"Two of five consumers migrated ... The approved scope is complete"）脚本 PASS → 语义 BLOCK（P4 命中）。其中三份脚本全 PASS 而语义均有实质缺陷，实证了"格式门禁 ≠ 设计合格"的分工必要性，也证明升级后的技能可在无脚本线索时识别"违规原地篡改"与"部分冒充全部"。② 旧域无回退：一份历史 Plan（`Status: executing`、两个 Task、AC 引用）按 Q1–Q4 仍可正常评审；本体进化提案的 Q4 能力门禁原文保留；一份**无 `Sub-DESIGNs` 头部**的多模块现状 DESIGN 通过 `verify-docset.py`（PASS），并按校准后 D1 四项检查（无头部枚举、子文档 `Parent` 回链、正文模块地图可达、地图不在 Reference Documents）全部 PASS——同一份文档在旧 `bidirectional index` 文本下会被误报为"缺头部索引"，据此确认误报已消除。③ 同交付产出本体现状设计 `docs/DESIGN-coding-workflow.md`（Status: Active、7 个 H2、含 `## Business Rules and Failure Boundaries`、无 `Sub-DESIGNs` 头部），只在隔离工作树内新落地的子提案 1+2 真实能力（`dev-doc-master` / `dev-proposal` / `verify-proposals.py` 22 个问题码分 5 组 / `verify-docset.py` 12 项检查 / `df-proposal-review` 三模式 / `rules/coding-workflow.md` 路由 / archetype 挂载），未写入任何子提案 3/4 能力；在 `docs/DESIGN.md` 的 `## Module Architecture` 表格新增一行挂链。文档集门禁：因隔离 worktree 的 sparse 范围不含 `../../docs/products/` 与 `../../projects/`，直接在隔离树跑会产出 19 条 isolation-artifact 链接失败，故按空间真实层级搭镜像（`.wopal/docs` + 符号链接 `docs/products`、`projects/ellamaka`、`projects/wopal-cli`）分别跑基线（改动前 HEAD 的 `docs/`）与本次改动，逐行 diff 结果**零新增失败**（唯一差异是 `DESIGN.md:244 → 245` 的行号位移，由新增表格行引起）；新增的 `DESIGN-coding-workflow.md` 未出现在任何 FAIL 行中。既有失败均为改动前已存在（6 份 DESIGN 缺 `## Business Rules and Failure Boundaries`、`DESIGN-distribution.md` 正文未挂链、`DESIGN-plan-orchestration.md` 目标文件在空间中本就不存在），按"不新增 warning、不替存量债买单"处理，未顺手改动无关文档。④ 事实核查：文档中"22 个问题码""47 条用例""12 项检查（11 项固定 + 第 12 项 `--check-sync` 可选）""description 46 字符""archetype 两处挂载"逐项对回源码/装配单确认；引用的 24 个路径中 6 个为预期例外（2 个稀疏范围外、1 个是被禁示例 `INDEX.md`、3 个脚本按技能前缀引用且实际存在），自身相对链接 0 断链。⑤ 按 `skill-creator` 完成 `df-proposal-review` 10+10 近邻触发验证：10 条应触发（评审 proposal / Plan / 进化提案 / DESIGN / 子 DESIGN / 已批准提案的替代合规 / 可证伪性检查）全部正确归入，10 条不应触发分别落到 `df-implement`（照提案写代码）、`dev-proposal`（新建提案、生命周期迁移）、`df-implement-review`（实施后评审、PR 回归）、`space-master`（README）、`skill-creator`（改 description）、或无人认领（Bug 排查、修断链、跑测试），0 误触发 0 漏触发；`description` 改前为"Review a proposal before execution. Use when the user asks to review, check, or verify a Plan, evolution proposal, or design document (PRD, DESIGN)…"（未覆盖业务 Proposal、未排除作者职责与实施后评审），改后补上 business/project Proposal 并显式排除 `dev-proposal`/`ontology-evolution` 作者职责与 `df-implement-review` 代码评审。验证限制：当前环境无法对真实模型做运行时注入触发，采用确定性路由核对（收集仓内已挂载技能 `description` + 逐条标注期望归属）替代，真实触发需重启 ellamaka 后人工抽检；盲审由主控在同一上下文内完成，独立性弱于外部评审者，最终独立评审仍按提案安排由加载 `df-implement-review` 的其他 Agent 执行。
Files touched: `skills/df-proposal-review/SKILL.md`（modify）、`skills/df-proposal-review/SKILL.zh-CN.md`（modify）、`skills/df-proposal-review/references/review-rubric.md`（modify）、`skills/df-proposal-review/references/review-rubric.zh-CN.md`（modify）、`docs/DESIGN-coding-workflow.md`（create）、`docs/DESIGN.md`（modify）
Review fix: 中文 `review-rubric.zh-CN.md` 的 D2 表格里混入了 6 行业务 Proposal / Plan 派生案例（英文对应行本就在「校准演练」表），已搬回同位置，现中英 D2 均为 5 行、校准演练均为 29 行，结构对等；`docs/DESIGN-coding-workflow.md` 校正为 29 个问题码分五组 + 1 个用法错误码 `ROOT_MISSING`，并补充根目录游离 Markdown 的 `outside-lifecycle-layout` 跳过规则与 77 条用例口径。
- [x] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | enhance-doc-contracts | 消费已交付的文档与事实归属合同，建立 Proposal 目录与再变更分流契约 |
| 2 | Task 2 | Wopal 主控 | Task 1 | TDD 落地确定性状态/授权/演进/归档冻结校验器 |
| 3 | Task 3 | Wopal 主控 | Task 2 | 命令路由、装配挂载、规则核对、入链维护与触发收敛 |
| 4 | Task 4 | Wopal 主控 | Task 3 | 决策记录与独立只读方案评审在同一交付闭环 |

本子提案由 Wopal 主控逐 Task 实施/验证并提交（不委派 Fae、不调用 Rook），全部 Task 实施完成后由用户安排其他 Agent 加载 `df-implement-review` 执行独立只读评审；用户控制提案批准、最终验证与集成。

## Delivery

此文件 `Stage: draft`；获批后依本体进化命令以 `isolated` 隔离模式独立交付。本次仅建立业务 Proposal 能力、校验器、命令装配与独立方案评审，不提前修改或自动调用尚未改造的 `dev-flow` Proposal→Plan CLI。
