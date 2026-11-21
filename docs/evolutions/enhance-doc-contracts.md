# enhance-doc-contracts

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

- **Complexity**: Medium — 保留并彻底瘦身 `dev-doc-master` 作为跨项目的现状 DESIGN 与文档写作唯一底座，落地防多 Agent 并行冲突分片、去主文档头部 `Sub-DESIGNs` 强枚举及 `verify-docset.py` 适配；有界增强 `space-master` 的 AGENTS 维护 SOP；新增 `coding` 空间技能调用规则 `.wopal/rules/coding-workflow.md`；同轮彻底清理废弃的 Phase / GAPS / 独立 BUSINESS_RULES 创作入口与装配清单引用。
- **Confidence**: High — 来源限于产品总提案、DSH 原始规范源码以及 `.wopal/` 本体现有资产，不依赖读取任何业务项目的存量 DESIGN 或 Plan。

## Goal

围绕产品总提案 [development-governance-proposal.md](../../../docs/products/wopal-space/proposals/development-governance-proposal.md)，把 WopalSpace 的跨项目文档与规范治理建立为**可驱动任意项目生成 DSH 级规范体系的元 SOP**：

1. **瘦身并升级 `dev-doc-master` 为唯一文档能力底座**：项目/子模块 DESIGN 彻底转为**现状文档**（面向最终用户、单归属、完整失败边界、实测取证、双场景同步、Slop Checklist 语义审查），通过**薄主 `DESIGN.md` 地图 + 按模块默认拆分子文档 + 去掉主文档头部 `Sub-DESIGNs` 强枚举 + 不手抄易变代码清单**从结构上防多 Agent 并行冲突，并同步适配 `verify-docset.py`。保留 PRD、产品 DESIGN、英文标题、无编号章节与用户偏好语言正文。
2. **有界增强 `space-master` 的 AGENTS 维护 SOP**：吸收 DSH 的分级归属、可执行检查证据（含非空范围与正反验证）和变更触发判断；保留现有分级强制效力、模板、Rule Audit、双语与用户审批，对历史 `BUSINESS_RULES.md` 改为只读兼容提示。
3. **新增 `.wopal/rules/coding-workflow.md`（装配至 `coding.yaml`）**：以清晰的关系图和触发边界告诉 Agent 整个 coding 空间技能体系（能力底座 vs 流程技能，以及可选的 `dev-flow` 中间层）如何协作与按需加载；初版仅声明当前阶段已生效能力，随子提案 2/3/4 逐步增量收口。
4. **同轮彻底清理废弃创作资产**：物理删除 `cupdate-roadmap.md`、`cupdate-br.md`、其中文审核版、装配清单 `coding.yaml` 与 `content.yaml` 中的对应挂载，以及 `dev-doc-master` 的 Phase / GAPS / BUSINESS_RULES 参考与模板，并清理失效命令引用与旧目标态规则，经本体同步从本体能力池移除，不触碰历史业务文档。

## Technical Context

### Architecture Context

产品总提案：`docs/products/wopal-space/proposals/development-governance-proposal.md`，本文件为**子提案 1**（首先实施，无前置依赖）。后续子提案 2（`enhance-dev-proposal`）、子提案 3（`enhance-implement-sync`）与子提案 4（`enhance-dev-flow-proposal`）全部消费本提案交付的文档写作、事实取证、并行防冲突分片与语义审查合同，并按阶段增量更新 `.wopal/rules/coding-workflow.md`。

**元规范定位（WopalSpace vs DSH）**：DSH 是单一代码仓库，可以直接把 `AGENTS.md`、`docs/architecture.md`、`packages/*/README.md` 和检查脚本固化在自己仓库里；WopalSpace 面向用户设计开发多种产品与项目，抽象层级高一层——本体不写死具体项目的技术栈或目录，而是通过 `dev-doc-master`、`space-master` 和 `rules/coding-workflow.md` 提供一套通用的**元规范与可复用 SOP**，让用户在任意项目中都能驱动 Agent 长出类似 DSH 严谨度的提案、分片现状 DESIGN、分级 `AGENTS.md`、测试门禁与独立评审体系。

**技能分层与按需调用原则**：保留并瘦身后的 `dev-doc-master`、现有的 `space-master` 与常驻 `rules/testing.md` 构成**能力底座**（单一规则真相源）；流程型技能（`dev-proposal`、`df-proposal-review`、位于提案与实施之间的**可选层 `dev-flow`**、`df-implement`、`df-implement-review`）只在需要写/改/审文档或规范时按需调用底座，不各自重复抄写规则，避免日常改代码时上下文膨胀。

**过渡期边界**：本提案交付后、子提案 2/3/4 尚未落地前，`dev-flow` 仍按旧链路运行。本提案保留历史 Plan 续办能力，`.wopal/rules/coding-workflow.md` 初版只陈述当前真实可用的入口与过渡期边界，不提前宣称 `dev-proposal` 或新 `dev-flow` Proposal→Plan CLI 已就绪。

### Source-Based Research

已核实的机制来源：
- DSH `labs/ref-repos/deepseek-harness/docs/AGENTS.md`：单事实单所有者、父级只概述直接下级并链接、参考文档只写当前事实、root/subtree 常驻规则分层、禁止手抄代码清单、以及专治 AI 文档腐烂的 **Slop Checklist**（思考过程泄露、实现状态标签、规则堆砌、滥用加粗、跨级重复）。
- DSH `labs/ref-repos/deepseek-harness/docs/architecture.md` 与 `.agents/notes/README.md`：顶层架构文档死守为极薄地图（171 行），模块细节下沉到各模块自持文档；**明确禁止集中式 `INDEX.md`**，防止互不相关的并发分支撞在同一个索引文件上冲突。
- DSH `labs/ref-repos/deepseek-harness/.agents/skills/dsh-doc-writing/{SKILL.md,references/structure-hierarchy.md,references/review.md}`：受众分类、用户可观察行为 → 概念架构 → 开发者细节渐进深度、**Fact-check procedure**（命令/配置/默认值/错误先实际执行核对，未实测显式标注）、**Newcomer test** 与 **Evidence review**。
- DSH `labs/ref-repos/deepseek-harness/.agents/skills/dsh-prose-standard/SKILL.md` 与 `dsh-trim-cot-leakage/SKILL.md`：保留完整契约要素（actor/action、条件、时序、必须/可能/禁止、异常、责任、副作用、失败后果），清除思考过程与会话视角残留。
- DSH `labs/ref-repos/deepseek-harness/packages/preset/agent-preset/skills/dsh-doc/references/tool-design.md`：最小上下文启动（Start with minimal context）与一条规则只写一遍（Say each fact once）。
- DSH `labs/ref-repos/deepseek-harness/{AGENTS.md,packages/AGENTS.md,packages/web/AGENTS.md,scripts/AGENTS.md}`、`dsh-code-review/SKILL.md`、`dsh-pre-push-checks/SKILL.md`：分级 AGENTS 规则不重复；行为变更同提交更新所属文档；检查脚本需覆盖非空范围与准入/排除边界；评审技能极薄，按改动面路由到专职标准而非重复抄规则。DSH 没有等价于 WopalSpace `space-master` 的完整 AGENTS 创建/审批/双语技能。
- WopalSpace 本体资产：`.wopal/AGENTS.md`（双语审核路径、`skill-creator` 强制前置、装配引用全树解析门禁、通用性原则）、`.wopal/skills/dev-doc-master/`（现有英文标题/无编号/用户语言正文、`verify-docset.py` 检查项与需清理的旧目标态/Phase/GAPS/BR 资产）、`.wopal/skills/space-master/`（现有 Rule Audit、双语与审批流程）、`.wopal/assembly/archetypes/coding.yaml` 与 `projects/upstream-wopal-space-ontology/assembly/archetypes/content.yaml`（两者均挂载了待删命令，受 `wopal-cli` 候选树完整性门禁强制校验）。

**隔离读取边界**：本提案全过程**禁止读取、分析或修改任何业务项目的存量 Plan（含归档）、业务 PRD/DESIGN、`projects/*/AGENTS.md` 或历史业务资料**；本体仓库自身的 `.wopal/AGENTS.md` 及 `.wopal/` 能力资产属于本提案改造对象，照常读取；全部示例与验收仅使用新建的隔离虚构样例。

### DSH Practices → WopalSpace Adoption → Verification

| ID | DSH 真实机制及原始来源 | 本轮精确采用的内容 | 验证方式 |
|---|---|---|---|
| M-01 | `docs/AGENTS.md`、`docs/architecture.md`、`.agents/notes/README.md`：单事实单所有者、薄顶层地图、物理分片、禁止集中索引防并发冲突 | **主 `DESIGN.md` 强制压薄为概念与模块地图**；多模块项目按模块/独立领域默认拆 `DESIGN-<module>.md`（不等 500 行才拆）；**去掉主文档头部 `Sub-DESIGNs` 强枚举**，消除多 Agent 并行修改冲突点 | 新建虚构多模块项目，验证模块改动不碰主 `DESIGN.md`、并行新增子文档无主文档头部冲突、`verify-docset.py` 放行 |
| M-02 | `dsh-doc-writing/SKILL.md`、`structure-hierarchy.md`：用户可观察行为 → 概念结构 → 开发者细节 | 保留英文标题与无编号章节；正文先说明实际提供的能力、用途、可观察结果和关键限制，再说明组件协作与必要细节 | 干净上下文新人/独立评审只读虚构主/子 DESIGN 能准确回答功能、工作方式、限制与下钻入口 |
| M-03 | `docs/AGENTS.md`：现状文档只写当前事实；决策理由与未实施方案不混入现状说明 | 项目/子模块 DESIGN **彻底转为现状文档**，清除旧“目标态写作 / Phase / GAPS / BR”规则；生效业务规则与失败边界并入对应 DESIGN；未实施设计归 Proposal；`## Key Decisions` 仅留已落地简明结论及指向对应 Proposal 的链接 | 检查 `dev-doc-master` 无新旧矛盾规则；用“把未来计划冒充已交付”的负例验证评审能拦截 |
| M-04 | `dsh-prose-standard/SKILL.md`、`docs/AGENTS.md`：完整行为契约，禁止手抄代码清单 | 用自然准确的语言写全条件、时序、责任、例外与失败后果；明确**禁止手抄源码文件树、完整命令参数表、全量 API 字段表**（以源码为准、文档只写契约并链接源码） | 以“文件清单充数 / 缺失败边界 / 遗漏条件”负例检验独立语义评审 |
| M-05 | `dsh-doc-writing/SKILL.md` Fact-check procedure、`review.md` Evidence review | 新增/修改的行为、命令、默认值、错误说明必须由代码、测试或实际运行结果核实；无法实测的声明显式标注未验证与验证方，绝不编造运行结果 | 在虚构实现上运行命令/测试，识别与代码不符及未实测却宣称通过的文案 |
| M-06 | `docs/AGENTS.md`、`packages/AGENTS.md`、`review.md`：代码变更同交付更新所属文档，无契约变化不造噪音 | 建立**双场景同步 SOP + 并行防越界纪律**：①有 Proposal 时代码+测试+所属模块 DESIGN+Proposal 转 `implemented` 同交付；②无 Proposal 日常修 Bug/小改动仅当对外可见行为/限制变化或原文档写错才改所属模块 DESIGN，纯内部重构不动文档；③多 Agent 并行期只改授权写集内模块子 DESIGN，发现主文档或他人模块漂移只上报主控、严禁越界修改共享文档 | 用虚构代码变更验证四类场景：应同步缺文档、文档虚构能力、纯内部重构不动文档、并行期发现异处漂移只报不越界 |
| M-07 | `review.md`、`docs/AGENTS.md` Slop Checklist、`dsh-trim-cot-leakage`：新人测试 + 证据审查 + 防 AI 废话 | 在 `dev-doc-master` 沉淀统一语义审查清单（新人可读 + 代码实证 + **Slop Checklist**：思考过程泄露、状态标签、规则堆砌、滥用加粗、跨级重复），供 `dev-doc-master` 自检与后续 `df-implement-review` 直接复用；`verify-docset.py` 只做确定性结构/链接检查 | 干净上下文 Agent 与独立语义评审区分正反样例；`verify-docset.py` 自动化测试通过 |
| M-08 | `structure-hierarchy.md`：渐进披露与紧密耦合规则不乱拆 | 保留既有主/子文档命名与相对链接；拆分按独立模块/领域所有权判断，不把紧密耦合的单一契约机械切碎 | 虚构多模块样例归属清晰、无无意义跨页跳转 |
| M-09 | `docs/AGENTS.md`、`packages/web/AGENTS.md`：分级常驻规则，父级不复制，局部无新约束不建文件 | `space-master` 明确按空间→项目→模块/目录判断规则归属；父级已有约束不复制，子级无新增长期约束不新建/不修改 `AGENTS.md` | 虚构三级目录规范中根级通用、子级特有，无重复和错层 |
| M-10 | `scripts/AGENTS.md`、`dsh-code-review/SKILL.md`：机械检查验证非空范围与准入/排除边界；按变更路径定位规范 | `space-master` 要求新增机械规范指向真实可执行命令、失败条件与正反/非空验证；无法机械判定的留给人工语义评审；按变更路径收集适用层级规范与最小必要检查 | 识别虚构检查脚本的误报、漏报、空范围伪通过，不另造多余校验脚本 |
| M-11 | `docs/AGENTS.md`、`dsh-pre-push-checks/SKILL.md`、`dsh-code-review/SKILL.md`、`packages/AGENTS.md`（同提交同步契约精神） | 长期工程/工具/门禁约束改变时触发 Rule Audit（Keep/Delete/Fix），保留现有双语、模板与用户审批；无新长期约束时不改；对历史 `BUSINESS_RULES.md` 改为只读兼容说明 | 虚构变更验证“需同步 / 无需同步 / 失效命令需修正 / 历史 BR 仅只读参考”四种结果 |
| M-12 | `tool-design.md`、`dsh-code-review/SKILL.md`：最小上下文启动、一条规则只写一遍、流程薄路由到专职底座 | 新增 `.wopal/rules/coding-workflow.md`（装配至 `coding.yaml`），向 Agent 清晰说明能力底座（`dev-doc-master`、`space-master`、`rules/testing.md`）与流程技能（含可选 `dev-flow`）的调用契约与阶段边界；初版仅声明当前已上线能力 | 检查 `coding-workflow.md` frontmatter、中英一致、无未上线虚假声明，并用多场景检验技能路由判定 |

### Key Decisions

- D-01：保留并彻底瘦身 `dev-doc-master` 作为跨项目唯一的文档规范与写作能力底座；项目/子模块 DESIGN 全面转为现状文档，吸收 M-01–M-08。
- D-02：**去掉主文档头部的 `Sub-DESIGNs` 强枚举**以消除多 Agent 并行冲突热点；保留其余既有格式（英文标题、无编号章节、用户偏好语言正文、相对链接、子文档 `Parent` 链接、头尾不重复）。同步更新 `verify-docset.py`：移除主文档缺少 `Sub-DESIGNs` 枚举的报错与 `GAPS` 创作要求，保留对历史/产品文档已有 `Sub-DESIGNs` 字段的兼容，不新增 DSH 双语/字数/YAML Kind 门禁。
- D-03：设计/Proposal 正文采用用户偏好语言，不引入 DSH 双语配对体系；本体能力资产按 `.wopal/AGENTS.md` 维持英文正式版与本地化审核版语义同步；项目 `AGENTS.md` 现行分层、强制效力、模板、双语与用户审批完全不变。
- D-04：产品 DESIGN 模板与 PRD 模板/规则/命令保持原样；**仅允许清理 `dev-doc-master/references/design*.md:143` 指向已删 `/cupdate-roadmap` 的失效下一步推荐链接**（仅清死链，不改产品 DESIGN 机制）。
- D-05：多 Agent 并行防文档冲突四条硬规则写入 `dev-doc-master`：①主 `DESIGN.md` 压薄为概念与模块地图；②多模块项目按模块默认拆 `DESIGN-<module>.md`（不等 500 行）；③单模块改动与修 Bug 不碰主 `DESIGN.md`，并行期发现写集外漂移只上报主控、严禁越界修改共享文档；④不手抄源码文件树、完整参数表或全量 API 列表。
- D-06：生效业务规则与失败边界并入对应 DESIGN，不再单独创建 `BUSINESS_RULES.md`；`templates/design-project.md` 中 `## Key Decisions` 定位为“已落地关键结论 + 指向对应 Proposal 的链接”，不重复决策讨论；`space-master` 对存量 `BUSINESS_RULES.md` 改为只读历史兼容提示。
- D-07：同轮彻底清理废弃资产并从装配清单与本体能力池移除（逐文件清单）：
  - 删除命令与中文审核版：`.wopal/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap.md,cupdate-br.md}`；
  - 更新全树装配清单：`.wopal/assembly/archetypes/coding.yaml`（移除 `cupdate-roadmap.md`、`cupdate-br.md`）与 `assembly/archetypes/content.yaml`（在隔离工作树放宽稀疏范围后移除 `cupdate-roadmap.md`，确保 `wopal-cli` 候选树装配完整性校验通过，并在后续本体同步时清出本体能力池）；
  - 删除 `dev-doc-master` 废弃创作资产：`references/{phase,gaps,business-rules}{,.zh-CN}.md`、`templates/{phase,gaps,business-rules}.md`；
  - 清除 `dev-doc-master/SKILL*.md`、`references/consistency*.md`、`references/design*.md`、`templates/{design-project.md,design-sub.md}` 中的旧目标态写作 / Phase / GAPS / BR 创作规则。
- D-08：新增 `.wopal/rules/coding-workflow.md` 与 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`，通过 `Assembly Intent` 以 `type-default` 装配到 `coding.yaml`。本轮初版写清能力底座与当前可用流程技能的边界（标注 `dev-flow` 作为复杂任务编排定位及过渡期真实状态，不提前宣称 `dev-proposal` 与新 `dev-flow` CLI 已上线）；后续子提案 2/3/4 落地时增量更新该文件直至最终目标态。
- D-09：`space-master` 保持 `AGENTS.md` 唯一管理技能，仅按 M-09–M-11 补强 maintenance SOP，不建平行技能、不改现存业务 `AGENTS.md`。
- D-10：修改任何 Skill 前按 `.wopal/AGENTS.md` 加载 `skill-creator`；精炼 `dev-doc-master` 和 `space-master` 的中英 `description`（含修复 `dev-doc-master/SKILL.md:11` 现有 `or any /cupdate-* request` 误抢 `/cupdate-agent-rules`、`/cupdate-readme` 的问题），并完成各 10+10 真实近邻正反触发验证。
- D-11：本提案仅负责文档能力底座、`space-master` 维护 SOP、`coding-workflow.md` 初版与废弃资产清理；`dev-proposal`、`df-implement`/`df-implement-review` 与 `dev-flow` 分别在子提案 2/3/4 交付。

### Key Interfaces

- `dev-doc-master`（主技能 + `references/design.md` + `references/consistency.md` + 对应 `.zh-CN.md`）：跨项目唯一文档规范与写作/审查引擎；新增规则直接落在 `references/design.md`（若超过合理阅读长度，仅拆出单一具名文件 `references/design-project-guide.{md,zh-CN}.md` 并由 `SKILL.md` 单点链接，不产生碎片或调研过程文档）。
- `/cupdate-design`（`.wopal/commands/cupdate-design.md` 及中文审核版）：沿用现有命令名与产品/项目分流；项目/子模块分支指向新的现状 DESIGN 写作、并行分片与实测取证规范；产品 DESIGN 分支保持原样。
- `verify-docset.py`（`.wopal/skills/dev-doc-master/scripts/verify-docset.py`）：保留原有 CLI 参数（`<docs-dir> [--main DESIGN.md] [--strict]`），**取消主文档缺少 `Sub-DESIGNs` 头部枚举的失败检查与 `GAPS.md` 强制规则**；保留子文档 `Parent` 链接、零绝对路径、相对链接可达、头尾不重复、过程态词汇、`Updated` 日期、合法头字段与 `Status` 检查（允许历史/产品文档保留 `Sub-DESIGNs` 字段不报错）。
- `/cupdate-prd`：完全不变。
- `/cupdate-agent-rules` & `space-master`：入口、模板、双语与审批不变；`references/agents-md-maintenance*.md` 增补 M-09–M-11 判断标准并将 `BUSINESS_RULES.md` 改为只读历史兼容说明。
- `.wopal/rules/coding-workflow.md`（及中文审核版）：标准 rule frontmatter（`trigger: model_decision`、`description`、`keywords`），定义 coding 空间装配技能的分层关系、按需调用规则与阶段边界，只写 Agent 可执行约束。
- `/cupdate-roadmap`、`/cupdate-br`：彻底物理删除命令、审核版、装配清单挂载与专用创作资产，不留空壳。

## In Scope

- `dev-doc-master` 瘦身升级：现状 DESIGN 内容规范、防多 Agent 并行冲突分片、无主文档头部 `Sub-DESIGNs` 枚举、双场景同步 SOP、实测取证、Slop Checklist 语义审查、生效业务规则并入 DESIGN，以及同步清理同技能内旧目标态/Phase/GAPS/BR 规则。
- `templates/{design-project.md,design-sub.md}` 的引导文案对齐现状文档、去掉 `Sub-DESIGNs` 头部提示、明确 `## Key Decisions` 定位（保留英文标题与章节布局）。
- `verify-docset.py` 适配去掉 `Sub-DESIGNs` 强枚举与 GAPS 规则，并补充正反自动化回归测试。
- `/cupdate-design`（及中文审核版）的项目/子模块引导更新。
- 物理删除 `cupdate-roadmap.md`、`cupdate-br.md`、其中文审核版、装配清单 `coding.yaml` 与 `content.yaml` 中的对应引用，以及 `dev-doc-master` 中 `phase/gaps/business-rules` 的参考与模板。
- `space-master` 的 AGENTS 维护 SOP 有界增强（M-09–M-11 + 历史 BR 兼容）。
- 新增 `.wopal/rules/coding-workflow.md`（及中文审核版，挂载到 `coding.yaml`）说明 coding 空间技能协作与调用边界。
- 依 `skill-creator` 精炼 `dev-doc-master` 与 `space-master` 的中英 `description` 并完成 10+10 正反触发验证，用新建隔离虚构多模块项目完成净上下文端到端验收。

## Out of Scope

- DSH 的双语文档配对/sidecar、README YAML Kind、`<details>` 折叠、字数预算门禁与官网投影机制。
- 修改产品 DESIGN 模板/主体流程或 PRD 模板/规则/命令（仅允许清理 `design*.md:143` 指向已删 `/cupdate-roadmap` 的死链接）。
- 改变项目 `AGENTS.md` 的分级强制效力、模板、双语机制或用户审批流，或另建独立 AGENTS 管理技能。
- 修改 `dev-proposal`（子提案 2）、`df-implement`/`df-implement-review`（子提案 3）、`dev-flow`（子提案 4）或 `ontology-evolution` 状态机。
- 读取、分析、迁移或改写任何业务项目的存量 Plan（含归档）、业务 DESIGN/PRD/BR 或 `projects/*/AGENTS.md`。

## Affected Files

| Component | Files | Operation | Boundary |
|---|---|---|---|
| DESIGN 能力底座 | `.wopal/skills/dev-doc-master/{SKILL.md,SKILL.zh-CN.md,references/design.md,references/design.zh-CN.md,references/consistency.md,references/consistency.zh-CN.md}`（超长时最多增一份具名 `references/design-project-guide.{md,zh-CN}.md`） | 修改（同轮去旧加新） | 产品 DESIGN 与 PRD 规则不重构；仅清理 `design*.md:143` 死命令链接 |
| 项目/子模块模板 | `.wopal/skills/dev-doc-master/templates/{design-project.md,design-sub.md}` | 修改引导文案 | 去掉 `Sub-DESIGNs` 头部提示与旧目标态措辞，明晰 `Key Decisions`；英文标题/无编号/章节结构不变 |
| 确定性校验脚本 | `.wopal/skills/dev-doc-master/scripts/verify-docset.py`（及对应隔离测试） | 修改 | 去掉主文档 `Sub-DESIGNs` 强枚举报错与 GAPS 规则，保留其余链接/结构检查并兼容历史字段 |
| DESIGN 薄入口 | `.wopal/commands/cupdate-design.md`、`.wopal/docs/LANG/zh-CN/commands/cupdate-design.md` | 修改 | 命令名、参数与产品 DESIGN 分支不变 |
| 废弃命令与创作资产 | `.wopal/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/skills/dev-doc-master/references/{phase,gaps,business-rules}{,.zh-CN}.md`、`.wopal/skills/dev-doc-master/templates/{phase,gaps,business-rules}.md` | **删除** | 不留空壳，不改任何真实业务文件 |
| 全树装配清单 | `.wopal/assembly/archetypes/coding.yaml`、`assembly/archetypes/content.yaml` | 修改 | 移除已删命令挂载；`coding.yaml` 通过 `Assembly Intent` 纳入 `coding-workflow.md` |
| coding 空间调用规则 | `.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` | **新增** | 只写 Agent 可执行协作与调用边界；初版不宣称未上线技能/CLI |
| AGENTS 维护 SOP | `.wopal/skills/space-master/{SKILL.md,SKILL.zh-CN.md,references/agents-md-maintenance.md,references/agents-md-maintenance.zh-CN.md}` | 修改 | 模板、分级强制效力、双语、用户审批不变；历史 BR 仅只读兼容 |
| 保留基线 | `templates/design-product.md`、`references/prd*.md`、`templates/prd.md`、`commands/cupdate-prd.md`、`commands/cupdate-agent-rules.md`、`space-master/templates/agent-rules.md` | 不修改 | 现有行为与格式原样保持 |
| 隔离验证素材 | `.wopal-space/.tmp/` 下新建的虚构多模块代码、测试、DESIGN 与三级 AGENTS 样例 | 创建并自行清理 | 不读取或写入任何业务项目文件 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|
| rule:coding-workflow.md | type-default | 为 coding 空间提供装配技能调用边界、协作关系与按需加载规则 |

## Acceptance Criteria

### Agent Verification

1. [ ] `dev-doc-master`（中英版与相关 references、模板）已完整落实 M-01–M-08：项目/子模块 DESIGN 转为现状文档，涵盖用户优先写作、防多 Agent 并行冲突四条硬规则（薄主地图、按模块默认分片、并行不越界上报主控、不手抄易变代码清单）、生效业务规则并入 DESIGN、`## Key Decisions` 轻量定位、实测取证、双场景同步 SOP 与 Slop Checklist 语义审查；技能内不再残留相互矛盾的旧目标态/Phase/GAPS/BR 创作规则。
2. [ ] 主文档头部 `Sub-DESIGNs` 强枚举已移除；`verify-docset.py` 经自动化正反测试验证：无 `Sub-DESIGNs` 头部的新多模块项目 DESIGN 通过校验，保留对历史/产品文档已有 `Sub-DESIGNs` 字段的兼容，且子文档缺 `Parent`、断链、绝对路径、头尾重复、过程态词汇、缺 `Updated` 或非法头字段仍可靠失败。
3. [ ] 产品 DESIGN 模板、PRD 模板/规则/命令、项目 `AGENTS.md` 现行分层/模板/双语/审批流程保持不变（仅清理 `references/design*.md:143` 指向已删 `/cupdate-roadmap` 的死链接）；英文标题、无编号章节与用户偏好语言正文规则不变，无 DSH 双语配对或格式包袱。
4. [ ] 废弃资产已彻底物理删除且全树引用零残留：`.wopal/commands/{cupdate-roadmap,cupdate-br}.md`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap,cupdate-br}.md`、`dev-doc-master/references/{phase,gaps,business-rules}{,.zh-CN}.md`、`dev-doc-master/templates/{phase,gaps,business-rules}.md` 均不存在；`assembly/archetypes/coding.yaml` 与 `assembly/archetypes/content.yaml` 已移除对应条目，通过装配树完整性检查且无断链引用。
5. [ ] `/cupdate-design`（及中文审核版）的项目/子模块引导已指向新规范，产品 DESIGN 分支不变；`dev-doc-master` 与 `space-master` 的中英版本及 `.wopal/docs/LANG/zh-CN/` 审核版全部语义对齐。
6. [ ] 以干净上下文 Agent 仅依据更新后的 `dev-doc-master` 处理新建虚构多模块项目：最终用户不读代码即可说清已交付能力、模块分工、生效规则与失败限制；并行修改两个模块时各自只改所属子 DESIGN、不撞主 `DESIGN.md`；无 Proposal 修 Bug、纯内部重构、发现写集外漂移只报不越界、虚构未实现能力与未实测宣称均由独立语义评审准确区分。
7. [ ] `space-master`（中英版）的维护 SOP 已落实 M-09–M-11（三级归属、父子不重复、机械门禁挂真命令与非空/正反测试证据、变更触发 Rule Audit、无新约束不改）并将历史 `BUSINESS_RULES.md` 改为只读兼容说明；在新建虚构三级目录正反样例上经干净上下文盲测与独立评审验证。
8. [ ] `.wopal/rules/coding-workflow.md`（及中文审核版）已创建并合乎 rule frontmatter 规范（`trigger`、`description`、`keywords`）与 `Assembly Intent` 声明，清晰呈现能力底座与流程技能（含可选 `dev-flow` 中间层）的调用边界，且如实反映当前过渡期状态，不提前宣称未上线技能或 CLI 已可用。
9. [ ] 依 `skill-creator` 精炼 `dev-doc-master` 与 `space-master` 的中英 `description`（含修复 `dev-doc-master` 原有 `or any /cupdate-* request` 误抢 `/cupdate-agent-rules` 与 `/cupdate-readme` 的缺陷）：两者各自完成 10 个应触发 + 10 个不应触发的真实近邻场景检查并记录改前/改后结果（无自动触发评测器时明确标注限制），同时确认 `coding-workflow.md` 触发词精准不误吸无关会话。
10. [ ] 任务全过程未读取、分析或修改任何业务项目的存量 Plan、业务 DESIGN/PRD/BR 或 `projects/*/AGENTS.md`；全部临时虚构验证素材建于 `.wopal-space/.tmp/` 并在收尾清理干净；`git diff --check` 与 `wopal space evo check enhance-doc-contracts` 通过。

### User Validation

#### Scenario 1: 新现状 DESIGN 规范、并行防冲突与空间调用规则验收
- Goal: 用户确认瘦身后的 `dev-doc-master`、`space-master` 维护 SOP、新规则 `coding-workflow.md` 与废弃资产清理均达到预期，且不读代码就能看懂新建虚构项目的现状 DESIGN。
- Environment: 本提案新建的隔离虚构多模块项目代码、测试、主/子 DESIGN 与三级 `AGENTS.md`（位于 `.wopal-space/.tmp/`）；不使用任何现存业务文档/Plan。
- Precondition: 全部 Task 完成、独立只读实施评审通过，提案进入 `validating`。
- Launch command: `wopal space evo switch enhance-doc-contracts`（切换后**重启 ellamaka** 以加载更新后的技能、命令与新规则）
- User Actions:
  1. 查看虚构多模块项目的主 `DESIGN.md`（薄地图、无头部 `Sub-DESIGNs` 枚举）与模块子 `DESIGN-<module>.md`（英文标题、无编号章节、中文正文），确认不读代码即可理解能力、生效业务规则、失败边界与实测依据。
  2. 查看多 Agent 并行改不同模块互不碰撞主文档的正例，以及“虚构未实现能力 / 拿文件清单充数 / 越界改共享文档”的反例评审结论。
  3. 审阅 `.wopal/rules/coding-workflow.md` 的技能分层与调用边界（确认 `dev-flow` 为可选中间层且过渡期表述真实），以及 `space-master` 在虚构三级目录上的 AGENTS 维护判定。
  4. 核对 `cupdate-roadmap`、`cupdate-br` 及 Phase/GAPS/BR 创作资产已从命令、技能与 `coding.yaml`/`content.yaml` 中彻底删除，产品 DESIGN 与 PRD 模板未受破坏。
- Pass criteria: 文档清晰易懂、并行防冲突机制扎实、空间调用规则清楚准确、废弃资产清理干净、既有保留基线原样不动。
- Failure feedback: 指明正文不清、规则冲突、调用边界模糊、越界改动或废弃资产残留的具体位置。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 瘦身重构 `dev-doc-master` 为现状 DESIGN 与防并行冲突文档底座

**Verification Intent**: AC#1、AC#3、AC#5、AC#10

**Behavior**: `dev-doc-master` 彻底去除旧“目标态写作 / Phase / GAPS / BR”规则，建立项目/子模块现状 DESIGN 的完整写作、防多 Agent 并行冲突分片、生效业务规则归属、实测取证、双场景同步 SOP 与 Slop Checklist 语义审查规范，并保持产品 DESIGN 与 PRD 原样。

**Pre-read**: 本提案；产品总提案 `docs/products/wopal-space/proposals/development-governance-proposal.md`；`.wopal/AGENTS.md`；`skill-creator` 技能；DSH `docs/AGENTS.md`、`docs/architecture.md`、`.agents/notes/README.md`、`dsh-doc-writing/{SKILL.md,references/structure-hierarchy.md,references/review.md}`、`dsh-prose-standard/SKILL.md`、`dsh-trim-cot-leakage/SKILL.md`；现有 `.wopal/skills/dev-doc-master/{SKILL*.md,references/design*.md,references/consistency*.md,templates/design-project.md,templates/design-sub.md}`。**禁止读取任何业务项目的存量 DESIGN 或 Plan。**

**Design**: 直接修订 `SKILL*.md`、`references/design*.md`、`references/consistency*.md` 及 `templates/{design-project.md,design-sub.md}`（若 `design.md` 过长，仅抽出单一具名 `references/design-project-guide.{md,zh-CN}.md`，不在技能目录留调研对照文档）。明确落地：主 `DESIGN.md` 压薄地图 + 按模块默认拆 `DESIGN-<module>.md` + 去掉头部 `Sub-DESIGNs` 枚举 + 并行期发现写集外漂移只报主控 + 禁止手抄易变代码清单 + 生效业务规则进对应 DESIGN + `## Key Decisions` 仅留落地结论与 Proposal 链接 + Slop Checklist。先改中文审核版再同步正式英文版。

**TDD**: false — 声明式技能规则与模板文案，无对应业务代码单元；通过前后 diff 核对、规则一致性检查与 Task 6 干净上下文盲测验证。

**Changes**: `.wopal/skills/dev-doc-master/{SKILL.md,SKILL.zh-CN.md,references/design.md,references/design.zh-CN.md,references/consistency.md,references/consistency.zh-CN.md,templates/design-project.md,templates/design-sub.md}`（以及必要时的单一具名 `references/design-project-guide.{md,zh-CN}.md`）。

**Verify**: 逐项对照 M-01–M-08 与 D-01–D-06 核对英文正式版与 `.zh-CN.md` 语义一致；确认技能内不再残留“目标态写作 / Phase / GAPS / BR”旧规则，且产品 DESIGN/PRD 规则未改（仅允许准备清理 `design*.md:143` 死链）。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: 适配 `verify-docset.py`（去头部 `Sub-DESIGNs` 强枚举与 GAPS 规则）并更新 `/cupdate-design`

**Verification Intent**: AC#2、AC#3、AC#5、AC#10

**Behavior**: `verify-docset.py` 不再因主文档缺少 `Sub-DESIGNs` 头部枚举而报错，不再强制执行已退场的 `GAPS.md` 规则，同时保留对历史/产品文档已有 `Sub-DESIGNs` 字段的兼容及全部确定性链接/路径/格式检查；`/cupdate-design`（及中文审核版）的项目/子模块引导指向新现状 DESIGN 规范。

**Pre-read**: Task 1 产出；`.wopal/skills/dev-doc-master/scripts/verify-docset.py`；`.wopal/commands/cupdate-design.md` 与 `.wopal/docs/LANG/zh-CN/commands/cupdate-design.md`；`.wopal/rules/testing.md`。

**Design**: 保持 `verify-docset.py` 现有命令行接口不变，去掉 `check_subdesign_index` 强制缺失报错与 `check_gaps_docs` 创作检查；对仍保留 `Sub-DESIGNs` 的历史或产品文档不报未知字段错；保留子文档 `Parent` 链接、零绝对路径、相对链接解析、头尾不重复、过程态词汇、`Updated` 日期与合法头字段校验。`/cupdate-design` 保持薄入口与产品 DESIGN 分支不变。

**TDD**: true — 涉及真实可执行脚本逻辑变更：先在 `.wopal-space/.tmp/` 编写正反回归测试（无 `Sub-DESIGNs` 头部的新多模块文档当前必 FAIL → 改后 PASS；历史含 `Sub-DESIGNs` 文档保持 PASS；断链/缺 `Parent`/绝对路径/头尾重复/过程态词汇/非法头字段持续 FAIL）。

**Changes**: `.wopal/skills/dev-doc-master/scripts/verify-docset.py`、`.wopal/commands/cupdate-design.md`、`.wopal/docs/LANG/zh-CN/commands/cupdate-design.md` 及临时回归测试脚本（验证后按规范处理）。

**Verify**: 运行 `verify-docset.py` 全部正反用例均按预期 PASS/FAIL；核对 `cupdate-design.md` 与中文审核版一致且未改产品 DESIGN 分支。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: 物理删除废弃命令、Phase/GAPS/BR 创作资产并同步全树装配清单

**Verification Intent**: AC#3、AC#4、AC#10

**Behavior**: `cupdate-roadmap.md`、`cupdate-br.md`、其中文审核版、`dev-doc-master` 的 Phase/GAPS/BR 参考与模板全部物理删除；`coding.yaml` 与 `content.yaml` 同步移除对应命令挂载；`references/design*.md:143` 的失效 `/cupdate-roadmap` 推荐链接清理干净；全树装配完整性校验通过且零悬空引用。

**Pre-read**: Tasks 1–2；`.wopal/AGENTS.md`（Capability references resolve）；`.wopal/assembly/archetypes/coding.yaml`；`projects/upstream-wopal-space-ontology/assembly/archetypes/content.yaml`（用于确认挂载行，实施时在隔离工作树放宽稀疏范围直接修改本工作树内的 `assembly/archetypes/content.yaml`）；待删命令与参考文件清单。

**Design**: 按 D-07 逐文件删除，不留提示空壳；在隔离工作树放宽稀疏范围将 `assembly/archetypes/content.yaml` 拉出后移除 `cupdate-roadmap.md`，并在 `assembly/archetypes/coding.yaml` 移除 `cupdate-roadmap.md` 与 `cupdate-br.md`，确保 `wopal space evo commit` / `integrate` 的候选树装配门禁通过，后续经本体同步彻底清出本体能力池。

**TDD**: true — 删除前确认目标文件与装配挂载存在，删除后用确定性检查断言：全部待删路径不存在、`.wopal/` 内无失效 `/cupdate-roadmap` / `/cupdate-br` / `references/{phase,gaps,business-rules}` / `templates/{phase,gaps,business-rules}` 活动引用、全树装配清单校验通过。

**Changes**: 删除 `.wopal/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/skills/dev-doc-master/references/{phase,gaps,business-rules}{,.zh-CN}.md`、`.wopal/skills/dev-doc-master/templates/{phase,gaps,business-rules}.md`；修改 `assembly/archetypes/coding.yaml`、`assembly/archetypes/content.yaml` 及 `dev-doc-master/references/design*.md:143`。

**Verify**: 运行文件存在性检查、`rg` 零死链检查以及 `wopal-cli` 装配树校验（或 `wopal space evo commit` 候选树检查）；确认未触碰任何真实业务文档。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: 有界增强 `space-master` 的 AGENTS 维护 SOP 并精炼触发描述

**Verification Intent**: AC#3、AC#5、AC#7、AC#9、AC#10

**Behavior**: `space-master` 在保留既有分层强制效力、模板、Rule Audit、双语与用户审批的前提下，补强三级归属判定、父子不重复、机械门禁挂真命令与非空/正反验证证据、变更触发更新判断与历史 `BUSINESS_RULES.md` 只读兼容说明；`space-master` 中英 `description` 简洁精准，不与 `dev-doc-master` 或 `ontology-evolution` 互相误抢。

**Pre-read**: `.wopal/AGENTS.md`；`skill-creator` 技能；DSH `AGENTS.md`、`docs/AGENTS.md`、`packages/AGENTS.md`、`packages/web/AGENTS.md`、`scripts/AGENTS.md`、`dsh-code-review/SKILL.md`、`dsh-pre-push-checks/SKILL.md`；现有 `.wopal/skills/space-master/{SKILL.md,SKILL.zh-CN.md,references/agents-md-maintenance.md,references/agents-md-maintenance.zh-CN.md}`。**禁止读取任何业务项目的 `projects/*/AGENTS.md`、DESIGN 或 Plan。**

**Design**: 仅在现有 `SKILL*.md` 与 `agents-md-maintenance*.md` 中做有界增补，不新增平行脚本或改动 `templates/agent-rules.md` 与 `/cupdate-agent-rules`。同步按 `skill-creator` 优化 `space-master` 中英 `description`，明确空间治理、项目/模块 `AGENTS.md` 与 `README.md` 的触发边界，排除项目现状 DESIGN 写作与本体维护直入场景。

**TDD**: false — 声明式技能规则；通过新建隔离三级虚构目录正反案例的干净上下文盲测 + 独立语义评审，以及 10+10 触发用例验证。

**Changes**: `.wopal/skills/space-master/{SKILL.md,SKILL.zh-CN.md,references/agents-md-maintenance.md,references/agents-md-maintenance.zh-CN.md}`。

**Verify**: 用干净上下文 Agent 仅凭更新后的 `space-master` 处理虚构三级目录的“应局部建规范 / 父级已覆盖不建 / 空扫描门禁反例 / 无新约束不改 / 历史 BR 仅只读参考”场景并独立评审；完成 `space-master` 的 10+10 正反触发验证并记录改前/改后结果（无自动评测器时标注限制）。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 5: 新增 `coding` 空间技能调用规则 `.wopal/rules/coding-workflow.md` 并精炼 `dev-doc-master` 触发描述

**Verification Intent**: AC#5、AC#8、AC#9、AC#10

**Behavior**: `coding` 空间拥有统一的技能调用规则 `.wopal/rules/coding-workflow.md`（及中文审核版，通过 `Assembly Intent` 挂载至 `coding.yaml`），清楚界定能力底座（`dev-doc-master`、`space-master`、`rules/testing.md`）与流程技能（含可选 `dev-flow` 中间层）的协作与按需调用边界，且如实表达当前过渡期状态；`dev-doc-master` 中英 `description` 精炼准确，修复原 `or any /cupdate-* request` 误抢缺陷且不再包含已删 Roadmap/BR 触发词。

**Pre-read**: Tasks 1–4；产品总提案 `development-governance-proposal.md`；`.wopal/AGENTS.md`（Rules 与 i18n 规范）；`skill-creator` 技能；现有 `.wopal/rules/{git.md,testing.md}` 格式参考；`.wopal/skills/dev-doc-master/SKILL*.md`。

**Design**: `coding-workflow.md` 按 `.wopal/AGENTS.md:72-77` 编写 `trigger: model_decision`、`description` 与精准 `keywords`，正文只写 Agent 可执行约束与清晰路由表/关系图，不复制任何具体技能内部步骤；明确标出当前阶段已上线能力，留出清晰结构供子提案 2/3/4 增量补入 `dev-proposal`、`df-implement` 同步钩子与新 `dev-flow` 入口。`dev-doc-master` 的 `description` 只列其真正拥有的文档与命令（PRD、产品 DESIGN、项目/子模块现状 DESIGN、`/cupdate-prd`、`/cupdate-design`），明确排除 `AGENTS.md`/`README.md`（归 `space-master`）、Plan 编排（归 `dev-flow`）与编码实施（归 `df-implement`）。

**TDD**: false — 声明式规则与技能触发描述；通过结构/中英核对与 10+10 近邻触发验证检验。

**Changes**: 新增 `.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`；更新 `.wopal/skills/dev-doc-master/{SKILL.md,SKILL.zh-CN.md}` 的 `description` 及与 `coding-workflow.md` 的衔接表述。

**Verify**: 核对 `coding-workflow.md` frontmatter 合法、中英一致、无未上线虚假声明且与 `space-master` 路由不冲突；完成 `dev-doc-master` 10+10 正反触发验证（覆盖 `/cupdate-agent-rules`、`/cupdate-readme`、已删 `/cupdate-roadmap` & `/cupdate-br` 排除，以及 PRD/产品 DESIGN/项目现状 DESIGN 命中），记录改前/改后对比与限制。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 6: 隔离虚构多模块样例的端到端净上下文验收与收口检查

**Verification Intent**: AC#1–10

**Behavior**: 在干净上下文的隔离虚构多模块项目中，验证新 `dev-doc-master`、`space-master`、`verify-docset.py` 与 `coding-workflow.md` 协同工作正常：文档用户友好、事实实测可证、多 Agent 并行改不同模块无主文档冲突、废弃资产清理干净且允许文件差异无越界。

**Pre-read**: Tasks 1–5；DSH `review.md` 与 `docs/AGENTS.md` Slop Checklist；本提案全部 AC 与 User Validation 场景。**只使用本 Task 在 `.wopal-space/.tmp/` 新建的隔离虚构素材。**

**Design**: 在 `.wopal-space/.tmp/` 创建包含两个独立模块的虚构项目代码、测试、薄主 `DESIGN.md`、模块子 `DESIGN-<a>.md` / `DESIGN-<b>.md` 与三级 `AGENTS.md`，用干净上下文 Agent 仅凭改后的本体规则/技能执行：①新建/更新现状 DESIGN 并运行真实命令取证；②模拟两路并行任务分别改模块 A/B，验证互不触碰主 `DESIGN.md` 且发现写集外漂移仅上报主控；③模拟无 Proposal 修 Bug 与纯内部重构；④模拟“虚构能力 / 文件清单充数 / 思考过程泄露”反例交独立只读评审检验。验证后清理 `.wopal-space/.tmp/` 临时素材。

**TDD**: false — 端到端行为与语义盲测，配合既有确定性脚本与仓库门禁共同验收。

**Changes**: 仅修复验收中暴露的技能/规则/脚本细节缺陷；不得触碰任何真实业务文档或 Plan。

**Verify**: 运行 `verify-docset.py` 全套正反测试、`git diff --check`、`wopal space evo check enhance-doc-contracts`；出具 M-01–M-12 → 改造文件 → 隔离样例 → 验收证据矩阵，汇总两项 Skill `description` 与新规则的改前/改后触发验证报告，核对实际改动文件列表严格落在允许范围内并确认临时文件已清理。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | 无 | 瘦身重构 `dev-doc-master` 现状 DESIGN 合同与防并行规则 |
| 2 | Task 2 | Wopal 主控 | Task 1 | 适配 `verify-docset.py` 与 `/cupdate-design` 并写正反测试 |
| 3 | Task 3 | Wopal 主控 | Tasks 1–2 | 物理删除废弃命令/资产并同步全树装配清单 |
| 4 | Task 4 | Wopal 主控 | Task 1 | 有界增强 `space-master` AGENTS 维护 SOP 与触发精炼 |
| 5 | Task 5 | Wopal 主控 | Tasks 1–4 | 新增 `coding-workflow.md` 规则并精炼 `dev-doc-master` 描述 |
| 6 | Task 6 | Wopal 主控 | Tasks 1–5 | 隔离多模块端到端净上下文盲测与收口校验 |

**执行与评审分工说明（显式覆盖本体进化默认的 Fae/Rook 委派模式，与子提案 2/3/4 保持一致）**：本子提案逐 Task 由 Wopal 主控实施并验证，每 Task 完成后经 C2C/ChatGPT 加载 `df-implement-review` 执行独立只读评审、修复复验后再回填 `Done` 并提交；不委派 Fae、不调用 Rook。用户继续独立掌控提案批准、最终验证（含 `switch` 后重启 ellamaka 观察）与正式集成。

## Delivery

本提案保持 `draft`，获批前不修改任何能力资产。完成并经用户授权集成与本体同步后：
1. `dev-doc-master` 成为瘦身、纯粹的跨项目文档与现状 DESIGN 能力底座，去掉主文档头部 `Sub-DESIGNs` 强枚举，内置防多 Agent 并行冲突分片、实测取证、双场景同步与 Slop Checklist，并同步适配 `verify-docset.py`；
2. `space-master` 保留现有 AGENTS 分级强制效力、模板、双语与审批流，补强分级归属、真实命令门禁证据、变更触发判定与历史 BR 兼容；
3. `.wopal/rules/coding-workflow.md` 正式装配到 `coding` 空间，清晰说明能力底座与流程技能的调用关系，随子提案 2/3/4 增量完善；
4. `cupdate-roadmap`、`cupdate-br` 与 Phase/GAPS/BR 创作资产从命令、技能、`coding.yaml`/`content.yaml` 及本体能力池彻底清理，产品 DESIGN 与 PRD 基线原样保留，不读取或修改任何业务项目的存量文档与 Plan。
