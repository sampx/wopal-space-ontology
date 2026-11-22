# enhance-doc-contracts

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-11-20
- **Stage**: archived
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-enhance-doc-contracts
- **Branch**: ontology-enhance-doc-contracts
- **Base Commit**: 54c28354724102412853ac39802cb2f6d9b25070
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Medium — 保留并彻底瘦身 `dev-doc-master` 作为跨项目的现状 DESIGN 与文档写作唯一底座，落地防多 Agent 并行冲突分片、去主文档头部 `Sub-DESIGNs` 强枚举及 `verify-docset.py` 适配；有界增强 `space-master` 的 AGENTS 维护 SOP；新增 `coding` 空间技能调用规则 `.wopal/rules/coding-workflow.md`；同轮彻底清理废弃的 Phase / GAPS / 独立 BUSINESS_RULES 创作入口与装配清单引用。
- **Confidence**: High — 来源限于产品总提案、DSH 原始规范源码以及 `.wopal/` 本体现有资产，不依赖读取任何业务项目的存量 DESIGN 或 Plan。

## Goal

围绕产品总提案 [development-governance-proposal.md](../../../docs/products/wopal-space/proposals/development-governance-proposal.md)，把 WopalSpace 的跨项目文档与规范治理建立为**可驱动任意项目生成 DSH 级规范体系的元 SOP**：

1. **瘦身并升级 `dev-doc-master` 为唯一文档能力底座**：项目/子模块 DESIGN 彻底转为**现状文档**（面向最终用户、单归属、完整失败边界、实测取证、双场景同步、Slop Checklist 语义审查），通过**薄主 `DESIGN.md` 地图 + 按模块默认拆分子文档 + 去掉主文档头部 `Sub-DESIGNs` 强枚举 + 不手抄易变代码清单**从结构上防多 Agent 并行冲突，并同步适配 `verify-docset.py`。保留 PRD、产品 DESIGN、英文标题、无编号章节与用户偏好语言正文。
2. **有界增强 `space-master` 的 AGENTS 维护 SOP**：吸收 DSH 的分级归属、可执行检查证据（含非空范围与正反验证）和变更触发判断；保留现有分级强制效力、模板、Rule Audit、双语与用户审批，对历史 `BUSINESS_RULES.md` 改为只读兼容提示。
3. **新增 `.wopal/rules/coding-workflow.md`（装配至 `coding.yaml`）**：一步到位给出完整的**最终目标态**开发流程与技能协作关系图，清楚界定能力底座 vs 流程技能（含可选 `dev-flow` 中间层）的职责与调用契约，不在规则文件中残留过渡期临时说明。
4. **同轮彻底清理废弃创作资产**：物理删除 `cupdate-roadmap.md`、`cupdate-br.md`、其中文审核版、装配清单 `coding.yaml` 与 `content.yaml` 中的对应挂载，以及 `dev-doc-master` 的 Phase / GAPS / BUSINESS_RULES 参考与模板，并清理失效命令引用与旧目标态规则，经本体同步从本体能力池移除，不触碰历史业务文档。

## Technical Context

### Architecture Context

产品总提案：`docs/products/wopal-space/proposals/development-governance-proposal.md`，本文件为**子提案 1**（首先实施，无前置依赖）。后续子提案 2（`enhance-dev-proposal`）、子提案 3（`enhance-implement-sync`）与子提案 4（`enhance-dev-flow-proposal`）全部消费本提案交付的文档写作、事实取证、并行防冲突分片与语义审查合同，并按阶段增量更新 `.wopal/rules/coding-workflow.md`。

**元规范定位（WopalSpace vs DSH）**：DSH 是单一代码仓库，可以直接把 `AGENTS.md`、`docs/architecture.md`、`packages/*/README.md` 和检查脚本固化在自己仓库里；WopalSpace 面向用户设计开发多种产品与项目，抽象层级高一层——本体不写死具体项目的技术栈或目录，而是通过 `dev-doc-master`、`space-master` 和 `rules/coding-workflow.md` 提供一套通用的**元规范与可复用 SOP**，让用户在任意项目中都能驱动 Agent 长出类似 DSH 严谨度的提案、分片现状 DESIGN、分级 `AGENTS.md`、测试门禁与独立评审体系。

**技能分层与按需调用原则**：保留并瘦身后的 `dev-doc-master`、现有的 `space-master` 与常驻 `rules/testing.md` 构成**能力底座**（单一规则真相源）；流程型技能（`dev-proposal`、`df-proposal-review`、位于提案与实施之间的**可选层 `dev-flow`**、`df-implement`、`df-implement-review`）只在需要写/改/审文档或规范时按需调用底座，不各自重复抄写规则，避免日常改代码时上下文膨胀。

**最终规则定位边界**：按照用户要求，`.wopal/rules/coding-workflow.md` 作为最终交付规则文件直接写出完整目标态协作图与全部流程/底座技能的调用边界（不在产出规则中保留过渡期文本，以免遗忘清理）；子提案 2/3/4 落地各流程技能自身实现时仅按需核对该规则与具体技能描述的一致性即可。

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
| M-03 | `docs/AGENTS.md`：现状文档只写当前事实；决策理由与未实施方案不混入现状说明 | 项目/子模块 DESIGN **彻底转为现状文档**，清除旧“目标态写作 / Phase / GAPS / BR”规则；生效业务规则与失败边界并入对应 DESIGN；未实施设计归 Proposal（`proposals/proposed/<class>/...`）；`## Key Decisions` 仅留已落地简明结论及指向对应已实现 Proposal（`proposals/implemented/<class>/...` 或引用历史快照时 `proposals/archived/<class>/...`）的链接 | 检查 `dev-doc-master` 无新旧矛盾规则；用“把未来计划冒充已交付”的负例验证评审能拦截 |
| M-04 | `dsh-prose-standard/SKILL.md`、`docs/AGENTS.md`：完整行为契约，禁止手抄代码清单 | 用自然准确的语言写全条件、时序、责任、例外与失败后果；明确**禁止手抄源码文件树、完整命令参数表、全量 API 字段表**（以源码为准、文档只写契约并链接源码） | 以“文件清单充数 / 缺失败边界 / 遗漏条件”负例检验独立语义评审 |
| M-05 | `dsh-doc-writing/SKILL.md` Fact-check procedure、`review.md` Evidence review | 新增/修改的行为、命令、默认值、错误说明必须由代码、测试或实际运行结果核实；无法实测的声明显式标注未验证与验证方，绝不编造运行结果 | 在虚构实现上运行命令/测试，识别与代码不符及未实测却宣称通过的文案 |
| M-06 | `docs/AGENTS.md`、`packages/AGENTS.md`、`review.md`：代码变更同交付更新所属文档，无契约变化不造噪音 | 建立**双场景同步 SOP + 并行防越界纪律**：①有 Proposal 时代码+测试+所属模块 DESIGN+Proposal 从 `proposed/` 迁至 `implemented/` 同交付；②无 Proposal 日常修 Bug/小改动仅当对外可见行为/限制变化或原文档写错才改所属模块 DESIGN（及必要时同步 `implemented/` 事实引用），纯内部重构不动文档；③多 Agent 并行期只改授权写集内模块子 DESIGN，发现主文档或他人模块漂移只上报主控、严禁越界修改共享文档 | 用虚构代码变更验证四类场景：应同步缺文档、文档虚构能力、纯内部重构不动文档、并行期发现异处漂移只报不越界 |
| M-07 | `review.md`、`docs/AGENTS.md` Slop Checklist、`dsh-trim-cot-leakage`：新人测试 + 证据审查 + 防 AI 废话 | 在 `dev-doc-master` 沉淀统一语义审查清单（新人可读 + 代码实证 + **Slop Checklist**：思考过程泄露、状态标签、规则堆砌、滥用加粗、跨级重复），供 `dev-doc-master` 自检与后续 `df-implement-review` 直接复用；`verify-docset.py` 只做确定性结构/链接检查 | 干净上下文 Agent 与独立语义评审区分正反样例；`verify-docset.py` 自动化测试通过 |
| M-08 | `structure-hierarchy.md`：渐进披露与紧密耦合规则不乱拆 | 保留既有主/子文档命名与相对链接；拆分按独立模块/领域所有权判断，不把紧密耦合的单一契约机械切碎 | 虚构多模块样例归属清晰、无无意义跨页跳转 |
| M-09 | `docs/AGENTS.md`、`packages/web/AGENTS.md`：分级常驻规则，父级不复制，局部无新约束不建文件 | `space-master` 明确按空间→项目→模块/目录判断规则归属；父级已有约束不复制，子级无新增长期约束不新建/不修改 `AGENTS.md` | 虚构三级目录规范中根级通用、子级特有，无重复和错层 |
| M-10 | `scripts/AGENTS.md`、`dsh-code-review/SKILL.md`：机械检查验证非空范围与准入/排除边界；按变更路径定位规范 | `space-master` 要求新增机械规范指向真实可执行命令、失败条件与正反/非空验证；无法机械判定的留给人工语义评审；按变更路径收集适用层级规范与最小必要检查 | 识别虚构检查脚本的误报、漏报、空范围伪通过，不另造多余校验脚本 |
| M-11 | `docs/AGENTS.md`、`dsh-pre-push-checks/SKILL.md`、`dsh-code-review/SKILL.md`、`packages/AGENTS.md`（同提交同步契约精神） | 长期工程/工具/门禁约束改变时触发 Rule Audit（Keep/Delete/Fix），保留现有双语、模板与用户审批；无新长期约束时不改；对历史 `BUSINESS_RULES.md` 改为只读兼容说明 | 虚构变更验证“需同步 / 无需同步 / 失效命令需修正 / 历史 BR 仅只读参考”四种结果 |
| M-12 | `tool-design.md`、`dsh-code-review/SKILL.md`：最小上下文启动、一条规则只写一遍、流程薄路由到专职底座 | 新增 `.wopal/rules/coding-workflow.md`（装配至 `coding.yaml`），以最终目标态向 Agent 清晰说明能力底座（`dev-doc-master`、`space-master`、`rules/testing.md`）与全部流程技能（含可选 `dev-flow`）的调用契约与边界 | 检查 `coding-workflow.md` frontmatter、中英一致、无过渡期残留且用多场景检验技能路由判定 |

### Key Decisions

- D-01：保留并彻底瘦身 `dev-doc-master` 作为跨项目唯一的文档规范与写作能力底座；项目/子模块 DESIGN 全面转为现状文档，吸收 M-01–M-08。
- D-02：**全面去掉所有主 `DESIGN.md`（含产品与项目）头部的 `Sub-DESIGNs` 枚举**以消除多 Agent 并行冲突热点；保留其余既有格式（英文标题、无编号章节、用户偏好语言正文、相对链接、子文档 `Parent` 链接、头尾不重复）。同步更新 `verify-docset.py`：彻底移除 `Sub-DESIGNs` 头部索引解析/完整性校验与 `GAPS` 检查（仅在合法头字段词表保留 `Sub-DESIGNs` 容忍存量未改老文档，头部断链仍由相对链接校验兜底），不新增 DSH 双语/字数/YAML Kind 门禁。
- D-03：设计/Proposal 正文采用用户偏好语言，不引入 DSH 双语配对体系；本体能力资产按 `.wopal/AGENTS.md` 维持英文正式版与本地化审核版语义同步；项目 `AGENTS.md` 现行分层、强制效力、模板、双语与用户审批完全不变。
- D-04：产品 DESIGN 主体结构、能力路线图与 PRD 模板/规则/命令保持原样；仅允许在评审修复范围内清理 `dev-doc-master/references/design*.md:143` 指向已删 `/cupdate-roadmap` 的死链接、从 `templates/design-product.md` 去掉多余的头部 `Sub-DESIGNs` 枚举提示，以及在共用 `templates/design-sub.md` 中明晰产品子 DESIGN（允许前瞻规划）与项目模块子 DESIGN（现状实证）的双场景契约，不改变产品 DESIGN 既有规划机制。
- D-05：多 Agent 并行防文档冲突四条硬规则写入 `dev-doc-master`：①主 `DESIGN.md` 压薄为概念与模块地图；②多模块项目按模块默认拆 `DESIGN-<module>.md`（不等 500 行）；③单模块改动与修 Bug 不碰主 `DESIGN.md`，并行期发现写集外漂移只上报主控、严禁越界修改共享文档；④不手抄源码文件树、完整参数表或全量 API 列表。
- D-06：生效业务规则与失败边界并入对应 DESIGN，不再单独创建 `BUSINESS_RULES.md`；`templates/design-project.md` 中 `## Key Decisions` 定位为“已落地关键结论 + 指向对应 Proposal（`proposals/implemented/<class>/...` 或引用历史快照时 `proposals/archived/<class>/...`）的链接”，不重复决策讨论；`space-master` 对存量 `BUSINESS_RULES.md` 改为只读历史兼容提示。
- D-07：同轮彻底清理废弃资产并从装配清单与本体能力池移除（逐文件清单）：
  - 删除命令与中文审核版：`.wopal/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap.md,cupdate-br.md}`；
  - 更新全树装配清单：`.wopal/assembly/archetypes/coding.yaml`（移除 `cupdate-roadmap.md`、`cupdate-br.md`）与 `assembly/archetypes/content.yaml`（在隔离工作树放宽稀疏范围后移除 `cupdate-roadmap.md`，确保 `wopal-cli` 候选树装配完整性校验通过，并在后续本体同步时清出本体能力池）；
  - 删除 `dev-doc-master` 废弃创作资产：`references/{phase,gaps,business-rules}{,.zh-CN}.md`、`templates/{phase,gaps,business-rules}.md`；
  - 清除 `dev-doc-master/SKILL*.md`、`references/consistency*.md`、`references/design*.md`、`templates/{design-project.md,design-sub.md}` 中的旧目标态写作 / Phase / GAPS / BR 创作规则。
- D-08：新增 `.wopal/rules/coding-workflow.md` 与 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`，通过 `Assembly Intent` 以 `type-default` 装配到 `coding.yaml`。规则正文直接写清最终目标态下能力底座与全部流程技能（`dev-proposal`、`df-proposal-review`、可选 `dev-flow`、`df-implement`、`df-implement-review` 及 `ontology-evolution` 例外）的调用契约与跨层约束，不在正式产出规则中残留过渡期描述。
- D-09：`space-master` 保持 `AGENTS.md` 与 `README.md` 唯一管理技能，不建平行技能、不改现存业务 `AGENTS.md`；在保留双语与用户审批的前提下，按用户拍板补齐 **Harness 自动注入三级 `AGENTS.md` 模板体系**（项目根 `templates/agent-rules.md` 去掉 `- Business Rules:` 残留并接入 `Doc sync` 门禁及现状 `DESIGN` 同步常驻规则；新增轻量 `templates/agent-rules-docs.md` 作为 `docs/` 目录不可绕过护栏卡并在建项目规范时主动提议建档；新增轻量 `templates/agent-rules-subdir.md` 供有独特局部约束的子目录按需使用）及 `readme-maintenance` 的“关键限制 + 仅独立发布 monorepo 子包可建薄 README”边界。
- D-10：修改任何 Skill 前按 `.wopal/AGENTS.md` 加载 `skill-creator`；精炼 `dev-doc-master` 和 `space-master` 的中英 `description`（含修复 `dev-doc-master/SKILL.md:11` 现有 `or any /cupdate-* request` 误抢 `/cupdate-agent-rules`、`/cupdate-readme` 的问题），并完成各 10+10 真实近邻正反触发验证。
- D-11：本提案仅负责文档能力底座、`space-master` 维护 SOP、`coding-workflow.md` 初版与废弃资产清理；`dev-proposal`、`df-implement`/`df-implement-review` 与 `dev-flow` 分别在子提案 2/3/4 交付。

### Key Interfaces

- `dev-doc-master`（主技能 + `references/design.md` + `references/consistency.md` + 对应 `.zh-CN.md`）：跨项目唯一文档规范与写作/审查引擎；新增规则直接落在 `references/design.md`（若超过合理阅读长度，仅拆出单一具名文件 `references/design-project-guide.{md,zh-CN}.md` 并由 `SKILL.md` 单点链接，不产生碎片或调研过程文档）。
- `/cupdate-design`（`.wopal/commands/cupdate-design.md` 及中文审核版）：沿用现有命令名与产品/项目分流；项目/子模块分支指向新的现状 DESIGN 写作、并行分片与实测取证规范；产品 DESIGN 分支保持原样。
- `verify-docset.py`（`.wopal/skills/dev-doc-master/scripts/verify-docset.py`）：保留原有 CLI 参数（`<docs-dir> [--main DESIGN.md] [--strict]`）并新增 `--check-sync [--base <git-ref>] [--pure-refactor <reason>]` 代码同步审计选项；**彻底移除 `Sub-DESIGNs` 头部索引解析/完整性校验与 `GAPS.md` 强制规则**；落实第 1–12 项确定性门禁（子文档 `Parent` 链接、主正文非参考区可达性/零孤立子文档、零绝对路径、相对链接可达、头尾不重复、零模板占位符与空表格行、非空 `##` 章节与项目/生效模块文档必备 `## Business Rules and Failure Boundaries`、过程态词汇、`Updated` 日期、合法头字段、`Status` 校验及 `--check-sync` 基于 `Source Carrier` 的代码↔DESIGN 变更映射）。
- `/cupdate-prd`：完全不变。
- `/cupdate-agent-rules`、`/cupdate-readme` & `space-master`：双语审阅与用户审批流不变；`space-master` 提供三级 `AGENTS.md` 模板（`templates/agent-rules.md` 项目根点火开关、`templates/agent-rules-docs.md` 轻量 `docs/` 护栏卡、`templates/agent-rules-subdir.md` 按需局部子目录规范），`references/agents-md-maintenance*.md` 增补 Harness 自动注入分层引导与 M-09–M-11 判据，`references/readme-maintenance*.md` 补强关键限制与 monorepo 独立发布子包边界（并顺手修复中文审核版 `docs/LANG/zh-CN/commands/cupdate-readme.md` 过期的 `dev-doc-master` 指向）。
- `.wopal/rules/coding-workflow.md`（及中文审核版）：标准 rule frontmatter（`trigger: model_decision`、`description`、`keywords`），定义 coding 空间装配技能的分层关系、按需调用规则与阶段边界，只写 Agent 可执行约束。
- `/cupdate-roadmap`、`/cupdate-br`：彻底物理删除命令、审核版、装配清单挂载与专用创作资产，不留空壳。

## In Scope

- `dev-doc-master` 瘦身升级：现状 DESIGN 内容规范、防多 Agent 并行冲突分片、无主文档头部 `Sub-DESIGNs` 枚举、双场景同步 SOP、实测取证、Slop Checklist 语义审查、生效业务规则并入 DESIGN，以及同步清理同技能内旧目标态/Phase/GAPS/BR 规则。
- `templates/{design-project.md,design-sub.md}` 的通用结构升级：项目主模板增强 `## Module Architecture` 的 `Source Carrier` 路径映射与跨模块核心协作流（并保持与产品 DESIGN 的上下文咬合，不绑定 DSH Cordis 插件扩展点）；子模块模板采用**固定首尾锚点 + 1..N 个领域自由分节 + 五项必填覆盖要素核对单**，同时明确 `## Key Decisions` 定位与去掉头部 `Sub-DESIGNs` 提示（保留英文标题与无编号章节布局）。
- `verify-docset.py` 升级为 12 项确定性门禁（去 `Sub-DESIGNs` 头部强枚举与 GAPS 规则，新增零孤立子文档、零模板占位符/空表行、非空章节与必备 `## Business Rules and Failure Boundaries`，以及可选 `--check-sync` 代码→DESIGN 同步检查）并配套正反自动化回归测试；在 `design-project-guide*.md` 写入“四道质量检验与把控闭环”。
- `/cupdate-design`（及中文审核版）的项目/子模块引导更新。
- 物理删除 `cupdate-roadmap.md`、`cupdate-br.md`、其中文审核版、装配清单 `coding.yaml` 与 `content.yaml` 中的对应引用，以及 `dev-doc-master` 中 `phase/gaps/business-rules` 的参考与模板。
- `space-master` 的 Harness 自动注入三级 `AGENTS.md` 模板体系（更新 `templates/agent-rules.md` 接通 `Doc sync` 门禁与现状 `DESIGN` 同步并清理 `- Business Rules:` 残留；新增 `templates/agent-rules-docs.md` 与 `templates/agent-rules-subdir.md`）、`agents-md-maintenance*.md`（M-09–M-11 + 分层模板矩阵 + 主动提议建 `docs/AGENTS.md`）、`readme-maintenance*.md`（关键限制 + monorepo 独立发布子包 README 边界）及 `/cupdate-agent-rules`、`/cupdate-readme` 中英同步。
- 新增 `.wopal/rules/coding-workflow.md`（及中文审核版，挂载到 `coding.yaml`）说明 coding 空间技能协作与调用边界。
- 依 `skill-creator` 精炼 `dev-doc-master` 与 `space-master` 的中英 `description` 并完成 10+10 正反触发验证，用新建隔离虚构多模块项目完成净上下文端到端验收。

## Out of Scope

- DSH 的双语文档配对/sidecar、README YAML Kind、`<details>` 折叠、字数预算门禁与官网投影机制。
- 修改产品 DESIGN 主体流程/能力图或 PRD 模板/规则/命令（仅允许清理 `design*.md` 指向已删 `/cupdate-roadmap` 的死链接，从 `templates/design-product.md` 去掉头部 `Sub-DESIGNs` 枚举提示，以及在 `templates/design-sub.md` 明确产品前瞻 vs 项目现状双场景边界）。
- 改变项目 `AGENTS.md` 的双语审阅与用户确认审批流，或另建独立 AGENTS 管理技能。
- 修改 `dev-proposal`（子提案 2）、`df-implement`/`df-implement-review`（子提案 3）、`dev-flow`（子提案 4）或 `ontology-evolution` 状态机。
- 读取、分析、迁移或改写任何业务项目的存量 Plan（含归档）、业务 DESIGN/PRD/BR 或 `projects/*/AGENTS.md`。

## Affected Files

| Component | Files | Operation | Boundary |
|---|---|---|---|
| DESIGN 能力底座 | `.wopal/skills/dev-doc-master/{SKILL.md,SKILL.zh-CN.md,references/design.md,references/design.zh-CN.md,references/consistency.md,references/consistency.zh-CN.md}`（超长时最多增一份具名 `references/design-project-guide.{md,zh-CN}.md`） | 修改（同轮去旧加新） | 产品 DESIGN 与 PRD 规则不重构；仅清理 `design*.md:143` 死命令链接 |
| 项目/子模块模板 | `.wopal/skills/dev-doc-master/templates/{design-project.md,design-sub.md,design-product.md}` | 修改结构与引导文案 | 全部主/子模板去掉头部 `Sub-DESIGNs` 提示；`design-project.md` 增加 `Source Carrier` 同步映射说明、跨模块协作流与按需领域章节提示；`design-sub.md` 升级为通用“固定首尾锚点 + 1..N 领域自由分节 + 五项必填覆盖要素”并显式区分产品前瞻 vs 项目现状双契约；`design-project.md` 明晰可点击相对 Markdown `Proposal` 链接 |
| 确定性校验脚本 | `.wopal/skills/dev-doc-master/scripts/verify-docset.py`（及对应隔离测试） | 修改 | 彻底移除 `Sub-DESIGNs` 头部索引解析/完整性校验与 GAPS 规则；落实第 1–12 项确定性门禁（含零孤立子文档、零占位符/空表行、必备 `Business Rules and Failure Boundaries` 及 `--check-sync` 代码→DESIGN 同步检查），保留历史字段兼容 |
| DESIGN 薄入口 | `.wopal/commands/cupdate-design.md`、`.wopal/docs/LANG/zh-CN/commands/cupdate-design.md` | 修改 | 命令名、参数与产品 DESIGN 分支不变 |
| 废弃命令与创作资产 | `.wopal/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap.md,cupdate-br.md}`、`.wopal/skills/dev-doc-master/references/{phase,gaps,business-rules}{,.zh-CN}.md`、`.wopal/skills/dev-doc-master/templates/{phase,gaps,business-rules}.md` | **删除** | 不留空壳，不改任何真实业务文件 |
| 全树装配清单 | `.wopal/assembly/archetypes/coding.yaml`、`assembly/archetypes/content.yaml` | 修改 | 移除已删命令挂载；`coding.yaml` 通过 `Assembly Intent` 纳入 `coding-workflow.md` |
| coding 空间调用规则 | `.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` | **新增** | 只写 Agent 可执行的最终目标态协作与调用边界，不含过渡期说明 |
| AGENTS 与 README 治理底座 | `.wopal/skills/space-master/{SKILL.md,SKILL.zh-CN.md,references/agents-md-maintenance*.md,references/readme-maintenance*.md,templates/agent-rules.md}`、`commands/{cupdate-agent-rules,cupdate-readme}.md`、`docs/LANG/zh-CN/commands/{cupdate-agent-rules,cupdate-readme}.md`（修改）；`skills/space-master/templates/{agent-rules-docs.md,agent-rules-subdir.md}`（**新增**） | 修改 / 新增 | 保留双语审阅与用户确认审批流；历史 BR 仅只读兼容；提供项目根 / `docs/` / 子目录三级 Harness 自动注入模板并接通 `Doc sync` 点火开关 |
| 保留基线 | `references/prd*.md`、`templates/prd.md`、`commands/cupdate-prd.md` | 不修改 | 现有行为与格式原样保持 |
| 隔离验证素材 | `.wopal-space/.tmp/` 下新建的虚构多模块代码、测试、DESIGN 与三级 AGENTS 样例 | 创建并自行清理 | 不读取或写入任何业务项目文件 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|
| rule:coding-workflow.md | type-default | 为 coding 空间提供装配技能调用边界、协作关系与按需加载规则 |

## Acceptance Criteria

### Agent Verification

1. [x] `dev-doc-master`（中英版与相关 references、模板）已完整落实 M-01–M-08：项目/子模块 DESIGN 转为现状文档，涵盖用户优先写作、防多 Agent 并行冲突四条硬规则（薄主地图、按模块默认分片、并行不越界上报主控、不手抄易变代码清单）、生效业务规则并入 DESIGN、`## Key Decisions` 轻量定位、实测取证、双场景同步 SOP 与 Slop Checklist 语义审查；技能内不再残留相互矛盾的旧目标态/Phase/GAPS/BR 创作规则。
2. [x] 全部主文档头部 `Sub-DESIGNs` 枚举提示与索引检查已彻底移除；`verify-docset.py` 升级为第 1–12 项确定性门禁并经 17/17 自动化正反回归测试验证：无 `Sub-DESIGNs` 头部的新项目与产品多模块 DESIGN 均通过校验，存量历史文档保留 `Sub-DESIGNs` 字段不报未知字段错，且孤立子文档、模板占位符残留、空章节/空表行、缺 `Business Rules and Failure Boundaries`、缺 `Parent`、断链、绝对路径、头尾重复、过程态词汇、缺 `Updated`、非法头字段与 `--check-sync` 未同步改动均可精确拦截。
3. [x] 产品 DESIGN 主体机制（含产品子 DESIGN 先于实施规划能力）、PRD 模板/规则/命令、项目 `AGENTS.md` 双语审阅与用户确认审批流保持不变（仅清理 `references/design*.md` 指向已删 `/cupdate-roadmap` 的死链接、去掉 `templates/design-product.md` 头部多余的 `Sub-DESIGNs` 枚举，并在 `templates/design-sub.md` 明确产品前瞻 vs 项目现状双场景契约）；英文标题、无编号章节与用户偏好语言正文规则不变，无 DSH 双语配对或格式包袱。
4. [x] 废弃资产已彻底物理删除且全树引用零残留：`.wopal/commands/{cupdate-roadmap,cupdate-br}.md`、`.wopal/docs/LANG/zh-CN/commands/{cupdate-roadmap,cupdate-br}.md`、`dev-doc-master/references/{phase,gaps,business-rules}{,.zh-CN}.md`、`dev-doc-master/templates/{phase,gaps,business-rules}.md` 均不存在；`assembly/archetypes/coding.yaml` 与 `assembly/archetypes/content.yaml` 已移除对应条目，通过装配树完整性检查且无断链引用。
5. [x] `/cupdate-design`（及中文审核版）的项目/子模块引导已指向新规范，产品 DESIGN 分支不变；`dev-doc-master` 与 `space-master` 的中英版本及 `.wopal/docs/LANG/zh-CN/` 审核版全部语义对齐。
6. [x] 以干净上下文 Agent 仅依据更新后的 `dev-doc-master` 处理新建虚构多模块项目：最终用户不读代码即可说清已交付能力、模块分工、生效规则与失败限制；并行修改两个模块时各自只改所属子 DESIGN、不撞主 `DESIGN.md`；无 Proposal 修 Bug、纯内部重构、发现写集外漂移只报不越界、虚构未实现能力与未实测宣称均由独立语义评审准确区分。
7. [x] `space-master`（中英版与模板）已落实 M-09–M-11（三级归属、父子不重复、机械门禁挂真命令与非空/正反测试证据、变更触发 Rule Audit、无新约束不改）、Harness 自动注入三级 `AGENTS.md` 模板体系（项目根 `agent-rules.md` 接通 `Doc sync` 门禁与现状 `DESIGN` 同步并清理 `- Business Rules:` 残留；新增轻量 `agent-rules-docs.md` 护栏卡与 `agent-rules-subdir.md` 局部模板）、`readme-maintenance` 关键限制与 monorepo 独立发布子包边界，并将历史 `BUSINESS_RULES.md` 改为只读兼容说明；经隔离三级目录盲测与模板一致性核验通过。
8. [x] `.wopal/rules/coding-workflow.md`（及中文审核版）已创建并合乎 rule frontmatter 规范（`trigger`、`description`、`keywords`）与 `Assembly Intent` 声明，以最终目标态清晰呈现端到端开发流程、能力底座与流程技能（含可选 `dev-flow` 中间层）的调用边界，不残留过渡期临时表述。
9. [x] 依 `skill-creator` 精炼 `dev-doc-master` 与 `space-master` 的中英 `description`（含修复 `dev-doc-master` 原有 `or any /cupdate-* request` 误抢 `/cupdate-agent-rules` 与 `/cupdate-readme` 的缺陷）：两者各自完成 10 个应触发 + 10 个不应触发的真实近邻场景检查并记录改前/改后结果（无自动触发评测器时明确标注限制），同时确认 `coding-workflow.md` 触发词精准不误吸无关会话。
10. [x] 任务全过程未读取、分析或修改任何业务项目的存量 Plan、业务 DESIGN/PRD/BR 或 `projects/*/AGENTS.md`；全部临时虚构验证素材建于 `.wopal-space/.tmp/` 并在收尾清理干净；`git diff --check` 与 `wopal space evo check enhance-doc-contracts` 通过。

### User Validation

#### Scenario 1: 新现状 DESIGN 规范、并行防冲突与空间调用规则验收
- Goal: 用户确认瘦身后的 `dev-doc-master`、`space-master` 维护 SOP、新规则 `coding-workflow.md` 与废弃资产清理均达到预期，且不读代码就能看懂新建虚构项目的现状 DESIGN。
- Environment: 本提案新建的隔离虚构多模块项目代码、测试、主/子 DESIGN 与三级 `AGENTS.md`（位于 `.wopal-space/.tmp/`）；不使用任何现存业务文档/Plan。
- Precondition: 全部 Task 完成、独立只读实施评审通过，提案进入 `validating`。
- Launch command: `wopal space evo switch enhance-doc-contracts`（切换后**重启 ellamaka** 以加载更新后的技能、命令与新规则）
- User Actions:
  1. 查看虚构多模块项目的主 `DESIGN.md`（薄地图、无头部 `Sub-DESIGNs` 枚举）与模块子 `DESIGN-<module>.md`（英文标题、无编号章节、中文正文），确认不读代码即可理解能力、生效业务规则、失败边界与实测依据。
  2. 查看多 Agent 并行改不同模块互不碰撞主文档的正例，以及“虚构未实现能力 / 拿文件清单充数 / 越界改共享文档”的反例评审结论。
  3. 审阅 `.wopal/rules/coding-workflow.md` 的最终目标态技能分层图与调用边界（确认 `dev-flow` 为可选中间层且无过渡期临时文字），以及 `space-master` 在虚构三级目录上的 AGENTS 维护判定。
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
Task output: 已完成 `dev-doc-master` 的瘦身与现状化改造：中英版 `SKILL*.md`、`references/consistency*.md`、`references/design*.md` 与 `templates/{design-project.md,design-sub.md}` 全部升级为项目/子模块现状 DESIGN 契约，并抽出单一具名参考 `references/design-project-guide.{md,zh-CN}.md`。完整落实 M-01–M-08 与 D-01–D-06（薄主地图、默认按模块拆 `DESIGN-<module>.md`、去掉项目主文档头部 `Sub-DESIGNs` 强枚举、并行写集外漂移只报主控、不手抄代码清单、生效业务规则并入 DESIGN、`## Key Decisions` 链接 `proposals/implemented/<class>/...`、实测取证与未实测显式标注、双场景同步、Slop Checklist 统一语义审查清单），清理原有目标态/Phase/GAPS/BR 规则及 `design*.md` 失效 `/cupdate-roadmap` 链接，保持产品 DESIGN 模板与 PRD 规则不变。经自动化扫描确认零残留旧规则/死链且中英行结构一致；独立实施评审由用户另行安排。
Files touched: skills/dev-doc-master/SKILL.md, skills/dev-doc-master/SKILL.zh-CN.md, skills/dev-doc-master/references/consistency.md, skills/dev-doc-master/references/consistency.zh-CN.md, skills/dev-doc-master/references/design.md, skills/dev-doc-master/references/design.zh-CN.md, skills/dev-doc-master/references/design-project-guide.md, skills/dev-doc-master/references/design-project-guide.zh-CN.md, skills/dev-doc-master/templates/design-project.md, skills/dev-doc-master/templates/design-sub.md, docs/evolutions/enhance-doc-contracts.md
- [x] The implementation agent has completed all development and verification steps above.

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
Task output: 已按 TDD 方式适配 `scripts/verify-docset.py`（移除主文档缺少 `Sub-DESIGNs` 头部枚举报错与 `check_gaps_docs` 检查，保留对历史/产品文档已有 `Sub-DESIGNs` 的兼容并继续拦截幻影死链），在 `.wopal-space/.tmp/verify-docset-tests/test_verify_docset.py` 先测出 2 个预期 RED 后修改实现至 13/13 全部 PASS（覆盖无 `Sub-DESIGNs` 多模块通过、历史 `Sub-DESIGNs` 兼容、幻影文件失败、历史 `GAPS.md` 放行、PRD 共存、缺 `Parent`/断链/绝对路径/头尾重复/过程词/缺日期/非法头字段与 Status）；同步更新 `/cupdate-design` 中英文引导，保留产品 DESIGN 分支不变。独立实施评审由用户另行安排。
Files touched: skills/dev-doc-master/scripts/verify-docset.py, commands/cupdate-design.md, docs/LANG/zh-CN/commands/cupdate-design.md, docs/evolutions/enhance-doc-contracts.md
- [x] The implementation agent has completed all development and verification steps above.

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
Task output: 已物理删除 D-07 清单全部 13 个废弃文件（`commands/{cupdate-roadmap,cupdate-br}.md`、`docs/LANG/zh-CN/commands/{cupdate-roadmap,cupdate-br}.md`、`skills/dev-doc-master/references/{phase,gaps,business-rules}{,.zh-CN}.md`、`skills/dev-doc-master/templates/{phase,gaps,business-rules}.md`）；在 `assembly/archetypes/coding.yaml` 移除 `cupdate-roadmap.md` 与 `cupdate-br.md`，并在隔离工作树拉出 `assembly/archetypes/content.yaml` 后移除 `cupdate-roadmap.md`。检查确认 13 个路径均已删除且活动命令/技能/装配清单零残留引用；随后通过 `wopal space evo commit` 候选树装配校验。独立实施评审由用户另行安排。
Files touched: commands/cupdate-roadmap.md, commands/cupdate-br.md, docs/LANG/zh-CN/commands/cupdate-roadmap.md, docs/LANG/zh-CN/commands/cupdate-br.md, skills/dev-doc-master/references/phase.md, skills/dev-doc-master/references/phase.zh-CN.md, skills/dev-doc-master/references/gaps.md, skills/dev-doc-master/references/gaps.zh-CN.md, skills/dev-doc-master/references/business-rules.md, skills/dev-doc-master/references/business-rules.zh-CN.md, skills/dev-doc-master/templates/phase.md, skills/dev-doc-master/templates/gaps.md, skills/dev-doc-master/templates/business-rules.md, assembly/archetypes/coding.yaml, assembly/archetypes/content.yaml, docs/evolutions/enhance-doc-contracts.md
- [x] The implementation agent has completed all development and verification steps above.

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
Task output: 已完成 `space-master` AGENTS 维护 SOP 的有界增强与触发收敛：在中英文 `SKILL*.md` 与 `references/agents-md-maintenance*.md` 中落地 M-09（space→project→module 三级归属、父子零重复、无独特约束不建文件）、M-10（可执行门禁须具备非空扫描范围与至少 1+1 正反验证、按受影响路径自底向上收集规范、语义项留给独立评审）与 M-11（仅长期约束变更触发 Rule Audit、将存量 `BUSINESS_RULES.md` 改为只读历史参考且不向其新增/从其抽取规则），完整保留分级效力、模板、双语与审批流；依 `skill-creator` 精炼中英 `description`。经 `.wopal-space/.tmp/space-master-eval/` 干净上下文子代理盲测（5 项场景 Case A–D 与 EN/CN 对齐检查全部通过，已顺手修正 Checklist 末条中英措辞微差），并完成 10+10 近邻触发对照记录（已注明无 `claude -p` 自动触发评测环境限制）；`git diff --check` 干净。独立实施评审由用户另行安排。
Files touched: skills/space-master/SKILL.md, skills/space-master/SKILL.zh-CN.md, skills/space-master/references/agents-md-maintenance.md, skills/space-master/references/agents-md-maintenance.zh-CN.md, docs/evolutions/enhance-doc-contracts.md
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 5: 新增 `coding` 空间技能调用规则 `.wopal/rules/coding-workflow.md` 并精炼 `dev-doc-master` 触发描述

**Verification Intent**: AC#5、AC#8、AC#9、AC#10

**Behavior**: `coding` 空间拥有统一的技能调用规则 `.wopal/rules/coding-workflow.md`（及中文审核版，通过 `Assembly Intent` 挂载至 `coding.yaml`），直接以最终目标态清楚界定能力底座（`dev-doc-master`、`space-master`、`rules/testing.md`）与全部流程技能（含可选 `dev-flow` 中间层）的协作与按需调用边界；`dev-doc-master` 中英 `description` 精炼准确，修复原 `or any /cupdate-* request` 误抢缺陷且不再包含已删 Roadmap/BR 触发词。

**Pre-read**: Tasks 1–4；产品总提案 `development-governance-proposal.md`；`.wopal/AGENTS.md`（Rules 与 i18n 规范）；`skill-creator` 技能；现有 `.wopal/rules/{git.md,testing.md}` 格式参考；`.wopal/skills/dev-doc-master/SKILL*.md`。

**Design**: `coding-workflow.md` 按 `.wopal/AGENTS.md:72-77` 编写 `trigger: model_decision`、`description` 与精准 `keywords`，正文直接写出最终目标态两张协作图、完整路由表与跨层硬约束，不复制任何具体技能内部步骤，也不在正式规则文件里写入过渡期临时文本。`dev-doc-master` 的 `description` 只列其真正拥有的文档与命令（PRD、产品 DESIGN、项目/子模块现状 DESIGN、`/cupdate-prd`、`/cupdate-design`），明确排除 `AGENTS.md`/`README.md`（归 `space-master`）、Plan 编排（归 `dev-flow`）与编码实施（归 `df-implement`）。

**TDD**: false — 声明式规则与技能触发描述；通过结构/中英核对与 10+10 近邻触发验证检验。

**Changes**: 新增 `.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`；更新 `.wopal/skills/dev-doc-master/{SKILL.md,SKILL.zh-CN.md}` 的 `description` 及与 `coding-workflow.md` 的衔接表述。

**Verify**: 核对 `coding-workflow.md` frontmatter 合法、中英一致、为干净最终目标态且与 `space-master` 路由不冲突；完成 `dev-doc-master` 10+10 正反触发验证（覆盖 `/cupdate-agent-rules`、`/cupdate-readme`、已删 `/cupdate-roadmap` & `/cupdate-br` 排除，以及 PRD/产品 DESIGN/项目现状 DESIGN 命中），记录改前/改后对比与限制。

**Done**:
Task output: 已新增 `rules/coding-workflow.md` 与 `docs/LANG/zh-CN/rules/coding-workflow.md` 并在 `assembly/archetypes/coding.yaml` 的 `rules` 段挂载；规则具备标准 `trigger: model_decision`、`description` 与精准 `keywords`，正文不硬编码工作区路径与 `.zh-CN`；已按用户正式验收反馈改写为干净的完整最终目标态（包含端到端流程全景图、能力底座 vs 流程技能分层图、完整场景路由表与跨层硬约束，彻底移除过渡期临时文本）。同步依 `skill-creator` 精炼 `dev-doc-master` 中英 `description`（移除 `or any /cupdate-* request` 误抢与已删 Roadmap/BR 词条，明确排除 `/cupdate-agent-rules`、`/cupdate-readme`、Plan 编排、编码与独立评审）并完成 10+10 近邻触发验证记录（已注明无 `claude -p` 自动评测限制）。独立实施评审由用户另行安排。
Files touched: rules/coding-workflow.md, docs/LANG/zh-CN/rules/coding-workflow.md, assembly/archetypes/coding.yaml, skills/dev-doc-master/SKILL.md, skills/dev-doc-master/SKILL.zh-CN.md, docs/evolutions/enhance-doc-contracts.md
- [x] The implementation agent has completed all development and verification steps above.

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
Task output: 已在隔离虚构双模块工程 `.wopal-space/.tmp/doc-contracts-e2e/`（`pulse-gateway`）完成干净上下文端到端盲测与全量收口检查：①作者子代理独立生成薄主 `DESIGN.md`（无头部 `Sub-DESIGNs`）、`DESIGN-auth.md` 与 `DESIGN-ratelimit.md`，实测跑通 `test_gateway.py`（2/2 PASS）与 `verify-docset.py`（PASS），核实不存在硬件 HSM 并拒绝写入，纯内部变量重命名不动 `DESIGN-auth.md`，在 `DESIGN-ratelimit.md` 写集内细化 `ERR_MISSING_KEY` 时守住边界不越界修改 `DESIGN.md` 并上报协调者；②盲读新人子代理不读源码准确答出全部能力、分工、未上线 `OAuth2 PKCE`/HSM 排除与失败后果，并对 `bad-doc-samples/DESIGN.md` 全部 5 类缺陷（未来冒充现状、虚假验证断言、符号树充数、Slop 泄露/WIP/历史词/粗体滥用、冗余/失效 `Sub-DESIGNs`）逐一拦截；③【评审修复、可读性闭环与 `space-master` 点火开关强化轮】依次落实独立评审 W-01/W-02/W-04/I-01、按用户要求移除 `coding-workflow.md` 过渡期文字、完成 `templates/{design-project.md,design-sub.md}` 通用化折中升级、在 `design-project-guide*.md` 落地“可读性红线 + 五组正反校准范例 + 纠偏学习闭环”与“四道质量检验与把控闭环”、将 `verify-docset.py` 扩充至第 1–12 项确定性门禁（17/17 TDD 回归通过），并补齐 `space-master` 的 Harness 自动注入三级 `AGENTS.md` 模板体系（更新 `templates/agent-rules.md` 接入 `Doc sync` 门禁与现状 `DESIGN` 同步并清掉 `- Business Rules:` 残留；新增 `templates/agent-rules-docs.md` 与 `templates/agent-rules-subdir.md`；升级 `agents-md-maintenance*.md`、`readme-maintenance*.md`、`SKILL*.md` 及 `cupdate-agent-rules`/`cupdate-readme` 中英同步，并经干净上下文子代理验证三级规范自动生成能力）；④核对 `git diff --check` 零异常、`wopal space evo check` 通过，且临时验证目录已清理。当前停在 `implementing` 阶段，待用户验收与独立复核（`54c2835..HEAD`）。
Files touched: docs/evolutions/enhance-doc-contracts.md, skills/dev-doc-master/{SKILL.md,SKILL.zh-CN.md,scripts/verify-docset.py,templates/{design-project.md,design-sub.md,design-product.md},references/{consistency.md,consistency.zh-CN.md,design.md,design.zh-CN.md,design-project-guide.md,design-project-guide.zh-CN.md}}, skills/space-master/{SKILL.md,SKILL.zh-CN.md,references/{agents-md-maintenance.md,agents-md-maintenance.zh-CN.md,readme-maintenance.md,readme-maintenance.zh-CN.md},templates/{agent-rules.md,agent-rules-docs.md,agent-rules-subdir.md}}, commands/{cupdate-design.md,cupdate-agent-rules.md,cupdate-readme.md}, docs/LANG/zh-CN/commands/{cupdate-design.md,cupdate-agent-rules.md,cupdate-readme.md}, rules/coding-workflow.md, docs/LANG/zh-CN/rules/coding-workflow.md
- [x] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | 无 | 瘦身重构 `dev-doc-master` 现状 DESIGN 合同与防并行规则 |
| 2 | Task 2 | Wopal 主控 | Task 1 | 适配 `verify-docset.py` 与 `/cupdate-design` 并写正反测试 |
| 3 | Task 3 | Wopal 主控 | Tasks 1–2 | 物理删除废弃命令/资产并同步全树装配清单 |
| 4 | Task 4 | Wopal 主控 | Task 1 | 有界增强 `space-master` AGENTS 维护 SOP 与触发精炼 |
| 5 | Task 5 | Wopal 主控 | Tasks 1–4 | 新增 `coding-workflow.md` 规则并精炼 `dev-doc-master` 描述 |
| 6 | Task 6 | Wopal 主控 | Tasks 1–5 | 隔离多模块端到端净上下文盲测与收口校验 |

**执行与评审分工说明（显式覆盖本体进化默认的 Fae/Rook 委派模式，与子提案 2/3/4 保持一致）**：本子提案由 Wopal 主控逐 Task 实施、验证并回填提交，不委派 Fae、不调用 Rook；全部 Task 实施完成后由用户安排其他 Agent 加载 `df-implement-review` 执行独立只读评审。用户继续独立掌控提案批准、最终验证（含 `switch` 后重启 ellamaka 观察）与正式集成。

## Delivery

本提案保持 `draft`，获批前不修改任何能力资产。完成并经用户授权集成与本体同步后：
1. `dev-doc-master` 成为瘦身、纯粹的跨项目文档与现状 DESIGN 能力底座，去掉主文档头部 `Sub-DESIGNs` 强枚举，内置防多 Agent 并行冲突分片、实测取证、双场景同步与 Slop Checklist，并同步适配 `verify-docset.py`；
2. `space-master` 保留现有 AGENTS 分级强制效力、模板、双语与审批流，补强分级归属、真实命令门禁证据、变更触发判定与历史 BR 兼容；
3. `.wopal/rules/coding-workflow.md` 正式装配到 `coding` 空间，一步到位定义端到端开发流程、能力底座与全部流程技能（含可选 `dev-flow`）的最终目标态调用关系；
4. `cupdate-roadmap`、`cupdate-br` 与 Phase/GAPS/BR 创作资产从命令、技能、`coding.yaml`/`content.yaml` 及本体能力池彻底清理，产品 DESIGN 与 PRD 基线原样保留，不读取或修改任何业务项目的存量文档与 Plan。
