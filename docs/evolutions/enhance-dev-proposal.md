# enhance-dev-proposal

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

- **Complexity**: Medium — 新增独立能力与目录/状态/引用校验，配套改动无独立执行脚本的方案评审技能；不改 dev-flow 底层状态机。
- **Confidence**: High（现行文档职责和本体进化模板已核实）；Medium（跨业务仓库场景需要隔离测试）。

## Goal

一次性提供业务/项目 Proposal 创建、写作、批准记录、交付证据与长期维护能力，并同步更新 `df-proposal-review` 的方案审查规则，为后续 dev-flow 提供**能创建、能审查、可核验的设计决定来源**。

## Technical Context

### Architecture Context

产品总提案：docs/products/wopal-space/proposals/development-governance-proposal.md，**子提案 2**。前置 `enhance-doc-contracts` 已交付瘦身后的唯一文档底座 `dev-doc-master`（现状 DESIGN、去主文档头部 `Sub-DESIGNs` 强枚举、防并行分片、实测取证与审查合同）及 coding 空间调用规则 `.wopal/rules/coding-workflow.md` 初版。业务 Proposal 归属与现状 DESIGN 的区别按第一份的新文档规范落实；本提案负责独立业务 Proposal、实施前方案评审，以及同步增量更新 `coding-workflow.md` 纳入 Proposal 环节，不重复文档体系标准。

当前 `dev-doc-master` 已瘦身为现状文档底座并完成旧 Phase/GAPS/BR 退场，尚无业务 Proposal 专用技能。`dev-flow` 的旧无 Issue Plan 仍待子提案 4 切换，Proposal 的设计授权、直接交付、部分实施和决策留存缺少稳定契约。本提案在**同一交付**建立 Proposal 的文件/状态/批准规则与对应 `df-proposal-review` 评审能力，不提前修改旧 `dev-flow` CLI。

### Research Findings

- 可借鉴 labs/ref-repos/deepseek-harness/.agents/notes/README.md 的 Problem/Proposal/Alternatives 与实施后 Decision/Consequences；DSH 不规定本空间的用户审批或 Plan 必选关系。
- WopalSpace 的产品 Proposal 现有位置为 docs/products/{product}/proposals/，项目 Proposal 目标为 projects/{project}/docs/proposals/；本体进化文档位于 .wopal/docs/evolutions/，不纳入新业务 Proposal 技能。
- `df-proposal-review` 原本同时审阅 Plan、DESIGN 和本体进化提案；这次仅增加**业务 Proposal 的独立语义审查及新来源的适用边界**，保留原本体/旧 Plan 的审查规则、报告结构和复审预算。
- Proposal 与 Plan 只有链接和有限交付证据，不同步两套实时进度表；Proposal 部分交付仍 approved。
- 新入口不能假装旧 dev-flow 已支持 Proposal→Plan：在该功能切换前，技能允许建立/评审/记录批准的决定，但实施派发必须经过实际可用的授权路由，不能自动调用尚不存在的 CLI。

**References**:
- .wopal/skills/dev-doc-master/SKILL.md
- .wopal/skills/df-proposal-review/SKILL.md
- .wopal/skills/df-proposal-review/references/review-rubric.md
- .wopal/skills/dev-flow/SKILL.md
- .wopal/skills/ontology-evolution/{SKILL.md,templates/proposal.md}
- labs/ref-repos/deepseek-harness/.agents/notes/README.md
- docs/products/wopal-space/proposals/

### Key Decisions

- D-01：Proposal 只承载需要重要设计选择的产品/项目变更；普通缺陷仍走 Issue，不因开发动作而机械创建 Proposal。
- D-02：Proposal 从 proposed 到 approved，再在全部批准范围完成并核验后变为 implemented；被否决的进入 rejected；不复制 Plan 的 implementing/verifying。
- D-03：用户审批同时明确授权范围和 Delivery: direct|plan；新增决策或实质变更必须重新获得用户确认，格式脚本不能冒充真实授权。
- D-04：仅存稳定 Source/关联 Plan/实际提交及评审验收证据；单个 Plan 完成或被归档不自动改变 Proposal 状态；直接实施没有 Plan 也必须留痕。
- D-05：提议时的 Problem/Proposal/真实 Alternatives/Acceptance/Risks 与交付后的 Problem/Decision/Alternatives/Consequences 都要可读、准确；写作标准引用 dev-doc-master，避免复制。
- D-06：第一阶段可独立批准文档决定，但不自动触发尚未迁移的 dev-flow；任何执行门禁必须在后续增强 dev-flow 后才对新路线开放。
- D-07：`df-proposal-review` 对业务 Proposal 审查 Problem/Alternatives/Decision/边界/可测试结果；对 Plan 的拆分与依赖仍由后续 dev-flow SOP 规范。评审技能只读，不代替用户审批，且不得破坏旧本体提案审查。
- D-08：新增 `dev-proposal` 和修改后的 `df-proposal-review` 都必须有**精准简洁的 description 与正反触发验证**：前者在业务 Proposal 的必要性判断、创建、维护、审批记录时加载（普通 Bug/Issue 不强行触发）；后者在**独立审查**业务 Proposal、已有 Plan 或本体进化提案时加载，不因 Proposal 的普通写作/状态维护而误触发。两者不能因“Proposal”一词混淆作者与只读审查者职责。

### Key Interfaces

- 新技能：.wopal/skills/dev-proposal/SKILL.md（含 zh-CN、reference、template、checker/tests）。
- 方案评审：.wopal/skills/df-proposal-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric*.md}，保持现有报告格式与复审规则。
- 薄命令：.wopal/commands/cupdate-proposal.md 及中文审核版 `.wopal/docs/LANG/zh-CN/commands/cupdate-proposal.md`，必须只路由到技能，不复制生命周期算法。
- 空间调用规则：增量更新 `.wopal/rules/coding-workflow.md` 及 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`，纳入 `dev-proposal` ↔ `df-proposal-review` ↔ `dev-doc-master` 的调用边界（仍如实标注 `dev-flow` 新 Proposal 来源待子提案 4 启用）。
- 新 Proposal 文件：projects/{project}/docs/proposals/{slug}.md 或 docs/products/{product}/proposals/{slug}.md；拒绝 proposals 单数目录。
- 状态和交付字段：proposed/approved/implemented/rejected 与 Delivery: direct|plan；检查器校验合法转换前提的可检查记录，不能替用户执行真实批准。

## In Scope

- Proposal 必要性、现有决策检索、写作模板（提案阶段不动现状 DESIGN，正文表达遵循 `dev-doc-master`）、文件命名/位置、创建和维护 SOP。
- 用户批准记录与变更边界，部分/全部交付判定、直接交付与关联 Plan 的不同证据路径。
- 确定性检查器、双语资产（含命令中文审核版）、链接/更名和正反集成 fixtures。
- 同步改造 `df-proposal-review` 的业务 Proposal 评审规范及实证样例；不为评审单独再立一份子提案。
- 同步增量更新 `.wopal/rules/coding-workflow.md`（及中文审核版）纳入新上线的 Proposal 环节，不提前宣称子提案 3/4 能力已就绪。
- 对两个新增或修改技能的 `description` 精准定义必加载意图和排除边界，依据 `skill-creator` 用真实近邻场景分别验证，不扩大既有评审触发范围。

## Out of Scope

- 不修改现有任何真实业务 Proposal，不修复已迁移的产品目录。
- 不修改 dev-flow 脚本的来源与状态机、不触发真实业务 Proposal 的实施、不改变 ontology-evolution。
- 不改 `df-implement-review` 的实施后代码审查，它在 `enhance-implement-sync` 中改造。
- 不引入额外文档数据库、Proposal implementing 状态或独立的进度同步程序。

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| Proposal 技能 | .wopal/skills/dev-proposal/ | 新增 | 决策文件生命周期及写作标准 |
| 方案评审 | .wopal/skills/df-proposal-review/SKILL*.md、references/review-rubric*.md | 修改 | 重要设计决定的独立语义检查 |
| 命令入口 | .wopal/commands/cupdate-proposal.md、.wopal/docs/LANG/zh-CN/commands/cupdate-proposal.md | 新增 | 薄入口及中文审核版 |
| 空间调用规则 | .wopal/rules/coding-workflow.md、.wopal/docs/LANG/zh-CN/rules/coding-workflow.md | 修改 | 增量补入 `dev-proposal` 与 `df-proposal-review` 调用契约 |
| 测试 | 新技能内部 tests/、隔离 fixtures | 新增 | 正负行为验证 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|
| skill:dev-proposal | type-default | 为 coding 空间提供业务/项目 Proposal 编写、审批记录与维护能力 |
| command:cupdate-proposal.md | type-default | 业务/项目 Proposal 薄命令入口 |

## Acceptance Criteria

### Agent Verification

1. [ ] 新重大设计从旧决定/当前事实检索后进入 Proposal；常规 Bug 不被错误要求建立 Proposal；模板记录问题、备选、边界及可验证结果。
2. [ ] 两个合法目录可创建且可检索；单数目录、错误产品/项目或断链改名被拒绝或提示可复现的修复路径。
3. [ ] 未批准、被否决、部分实施、全部交付、范围变更等状态正负例准确；未获用户授权不得跳跃到 approved/implemented，格式检验不能伪造审批。
4. [ ] Delivery: direct 和 plan 都可记录实际证据；Plan 的 done/archive 不会使 Proposal 自动 implemented；在 dev-flow 改造前不会启动尚未支持的实施入口。
5. [ ] 技能、薄命令、模板、校验器与增量更新后的 `.wopal/rules/coding-workflow.md` 中英文语义一致；`Assembly Intent` 声明正确且全树装配检查通过；真实业务文件没有被改写。
6. [ ] `df-proposal-review` 能指出遗漏替代方案、缺少可验证结果、决策边界不清、将局部交付冒充全部实施等问题；正确业务 Proposal 通过，旧 Plan 与本体进化提案的审查行为不回退。
7. [ ] `dev-proposal` 和 `df-proposal-review` 的中英 `description` 简洁、职责/阶段清楚；每个技能完成**10 个应触发 + 10 个不应触发**的实际近邻请求检查，覆盖 Proposal 写作 vs 独立评审、普通 Issue/Bug、Plan 审查、本体进化提案和实施后代码评审。记录误触发/漏触发与修订结果；无真实触发运行时明确未自动验证。

### DSH Principles → Tasks → Verification

| DSH 已验证来源 | 本提案取用的实践 | Task 与验收 |
|---|---|---|
| `labs/ref-repos/deepseek-harness/.agents/notes/README.md` | 重大设计有独立决策记录；区分 proposed/implemented/rejected；记录替代方案与代价，但不用 DSH 的目录状态替代本空间的用户批准 | Task 1、2；AC#1、3、4 |
| `labs/ref-repos/deepseek-harness/docs/AGENTS.md` | 一项决定一个归属，目录/链接稳定；不另建重复索引与进度台账 | Task 1、3；AC#2、4 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-prose-standard/SKILL.md` | 保留授权条件、失败保证与备选决策的完整语义，禁止只有术语和空模板 | Task 1、4；AC#1、6 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-code-review/SKILL.md` | 区分确定性格式检查与基于真实事实的语义评审 | Task 2、4；AC#3、6 |

`Delivery: direct | plan` 和用户授权字段是 **WopalSpace 的设计**，不是 DSH 已有的命令/审批流程。

### User Validation

#### Scenario 1: 产品/项目提案样例与状态理解
- Goal: 用户能独立看懂设计选择、交付方式、未完成范围和最终决定。
- Environment: 隔离 fixtures 的两份虚构 Proposal。
- Precondition: 实施完成并经独立评审，进入 validating。
- Launch command: `wopal space evo switch enhance-dev-proposal`（切换后**重启 ellamaka** 以加载新技能、命令与更新后的规则）
- User Actions:
  1. 阅读 proposed、approved 与部分实施样例，检查界限是否清楚。
  2. 确认没有要求自己阅读代码或重复批准相同设计。
- Pass criteria: 决策、原因、已交付/未交付内容和所需授权一目了然。
- Failure feedback: 指出状态/理由/证据中不可理解或不完整的位置。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 设计 Proposal 分类与文件合同

**Verification Intent**: AC#1、AC#2
**Behavior**: 有重要设计变化时使用业务 Proposal；目录、格式及链接稳定；已有同主题 Proposal 不被无意重复创建。
**Pre-read**: 产品总提案的 Proposal 规范、`.wopal/AGENTS.md`、`skill-creator` 技能、DSH `.agents/notes/README.md`、已交付的 `dev-doc-master` 与 `.wopal/rules/coding-workflow.md`。
**Design**: 用单一技能管理必要性判定与写作；Proposal 仍为用户决策文本，非 Plan、非 DESIGN；不把项目专有路径写死在通用决策规则里。
**TDD**: false — 规范和路径设计以例证/审查优先。
**Changes**: 新技能的 SKILL、references、templates，定义路径与文档契约。
**Verify**: 创建两个合法样例与重复/非法目录反例，独立审核；同时确定 `dev-proposal` description 的必加载/不适用意图及与相邻技能的区分，不靠关键词堆砌。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: 审批、交付方式与实际状态门禁

**Verification Intent**: AC#3、AC#4
**Behavior**: proposed/approved/implemented/rejected 的合法转换和记录可验证，部分实施不提前转 implemented；direct/plan 的证据要求一致。
**Pre-read**: Task 1、ontology-evolution 的用户授权规则、旧 dev-flow 的 approve 入口和直接实施限制。
**Design**: 只检查可核验的授权证据与状态/内容关系，不把文本字段视为身份认证；不得自动用 Proposal 去执行旧 CLI；状态管理不引入实时 Task 表。
**TDD**: true — 状态转换、缺授权、错误交付证据使用正负案例驱动。
**Changes**: 状态 reference、检查器、测试 fixtures。
**Verify**: 对成功状态和非法跳转实际运行检查器；确认无真实仓库写入。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: 命令路由、改名维护、空间规则增量更新与互操作边界

**Verification Intent**: AC#2、AC#4、AC#5、AC#7
**Behavior**: `cupdate-proposal` 稳定路由至唯一技能；移动/更名后入链完整；`.wopal/rules/coding-workflow.md` 如实纳入 `dev-proposal` 与 `df-proposal-review` 的调用契约；后续 `dev-flow` 能读取唯一 Source 路径。
**Pre-read**: Task 1–2、`.wopal/commands/cupdate-*`、`.wopal/rules/coding-workflow.md`（及中文审核版）、`skill-creator` 技能、`dev-flow` 计划中的 Source 契约。
**Design**: 命令保持薄并同步中文审核版；目录/引用校验落在所属检查器；更新 `coding-workflow.md` 时只纳入已落地能力，对尚不支持新来源的旧 `dev-flow` 明确拒绝而非伪装成功。
**TDD**: true — 覆盖合法/非法路径、状态、断链以及路由行为。
**Changes**: `.wopal/commands/cupdate-proposal.md`、`.wopal/docs/LANG/zh-CN/commands/cupdate-proposal.md`、`.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`、新技能必要路由与 tests。
**Verify**: 在隔离产品/项目样本运行新建、审核、改名与非法输入模拟；运行实际命令触发路径与装配检查；核对 `coding-workflow.md` 中英一致；针对 `dev-proposal` 完成 10+10 正反触发测试和描述收敛，不能误入独立只读评审流程。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: 将业务 Proposal 的评审能力并入原有方案评审技能

**Verification Intent**: AC#1、AC#3、AC#6、AC#7

**Behavior**: 提案提交用户批准以前，`df-proposal-review` 对问题、备选方案、明确决策边界、风险和可复现实证进行独立审查。不能把“已批准”误当作质量合格、不能因为格式有效就放过没有设计依据的决定；旧本体提案/Plan 的审查仍正常。

**Pre-read**: Task 1–3、`skill-creator` 技能、`df-proposal-review/{SKILL.md,references/review-rubric.md}` 及中文版本；DSH `.agents/notes/README.md`、`dsh-prose-standard/SKILL.md`；本体进化/历史 Plan 的原报告和复审要求。

**Design**: 在原方案评审技能中新增业务 Proposal 的模式分流，只读评估“是否值得做、为何选它、是否越界、能否验收”；保留既有报告分类和复审预算。不要额外创建一套 Proposal 审查脚本或替代人工判断的关键字门禁。

**TDD**: false — 语义判断由正确、缺方案、缺授权、错误夸大已交付范围等实证样例进行盲审；不以文本包含关系模拟推理结果。

**Changes**: `df-proposal-review` 的主技能、rubric、中文版本及必要样例，链接新 `dev-proposal` 规范。

**Verify**: 分别评审正确和错误业务 Proposal、一个历史 Plan 与一个旧本体 Proposal；报告须指出明确问题和证据，不改变既有结构和预算；针对 `df-proposal-review` 完成 10+10 正反触发测试，涵盖写作/审批、实施后代码评审和旧审查正例，记录前后 description 与结果。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | enhance-doc-contracts | 消费已交付的文档与事实归属合同 |
| 2 | Task 2 | Wopal 主控 | Task 1 | 状态与授权 |
| 3 | Task 3 | Wopal 主控 | Task 2 | 路由及集成验证 |
| 4 | Task 4 | Wopal 主控 | Task 3 | 决策记录与独立评审在同一交付闭环 |

本子提案逐 Task 由 Wopal 实施/验证，每 Task 都经 C2C/ChatGPT 使用 df-implement-review 独立只读评审并修复后提交；不委派 Fae 实施、不调用 Rook。用户控制提案批准、最终验证与集成。

## Delivery

此文件 Stage: draft；获批后依本体进化命令独立交付。本次仅建立 Proposal 能力与稳定合同，不提前声称新 dev-flow 的 Plan 入口已生效。
