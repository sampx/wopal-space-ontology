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

产品总提案：docs/products/wopal-space/proposals/development-governance-proposal.md，**子提案 3**；前置 `enhance-doc-contracts` 和 `enhance-dev-proposal`。**瘦身后的文档能力底座 `dev-doc-master`（现状 DESIGN、防并行分片、无头部 `Sub-DESIGNs` 枚举、实测取证与 Slop Checklist 审查清单）、`space-master` 维护 SOP 及 `.wopal/rules/coding-workflow.md` 已由前置提案交付**；本提案直接建立流程层对能力底座的按需调用契约，实现后的代码、测试与用户可读现状 DESIGN 在同一次交付中同步，绝不把 `dev-doc-master` 或 `space-master` 的细则再抄一遍。

当前 `df-implement/SKILL.md` 依赖 Active DESIGN 作为目标，认为实施只是让代码满足提前写好的设计；现行 `dev-flow/SKILL.md` 又明确“实施时不得更新 DESIGN”。新的契约是 DESIGN 只写已交付现状，因此实施者在代码真正改变对外行为、公共接口、生效业务规则或限制后，**按需加载 `dev-doc-master`** 同步所属模块的现状 DESIGN（纯内部重构不动文档）；留下新的长期工程约束时，**按需加载 `space-master`** 审计或更新对应层级的 `AGENTS.md`；测试继续遵循常驻规则 `rules/testing.md`。`df-implement-review` 在保留既有 Q1–Q4 的基础上，**按需参照 `dev-doc-master` 语义审查清单**核验代码↔DESIGN 双向一致与防 AI 流水账，并同步增量更新 `.wopal/rules/coding-workflow.md`。正式 CLI 切换由 `enhance-dev-flow-proposal` 完成，避免新旧机制在同一路径上相互冲突。

### Research Findings

- 实施者不能修改批准的设计决定；发现缺失约束、新 API 决策或大幅超出范围应 STOP 并回到主控/用户，而非自行改 Proposal。
- 代码、测试、实际 DESIGN 同步后，主控才能根据可重复验证证据接受 Task；“文档已更新”本身不是运行时验证。
- direct 无 Plan 时证据记在业务 Proposal 或 Issue 所属的唯一进度记录；Plan 路线 Task Done / Design Sync 由控制者记录，实施者不能自签验收。
- 旧 Plan 仍按既有 DESIGN → Plan → implementation 规则执行，不能因为新的文档同步原则被追溯修改或拒绝。
- 现有 `df-implement-review` 没有独立 CLI/状态机，需要在既有四问题和结果结构上补充证据与文档检查，不另建一个实施质量子提案。

**References**:
- .wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md}
- .wopal/skills/df-implement-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric.md,references/review-rubric.zh-CN.md}
- .wopal/skills/dev-flow/{SKILL.md,references/plan-guide.md}
- .wopal/skills/dev-doc-master/references/design.md
- .wopal/docs/evolutions/enhance-doc-contracts.md（已经交付的 DESIGN 写作与事实审查合同）
- .wopal/docs/evolutions/enhance-dev-proposal.md

### Key Decisions

- D-01：代码/测试/受影响的用户可读现状 DESIGN 同一交付同步：`df-implement` 仅保留轻量触发判据——纯内部重构不动 DESIGN；对外可见行为/接口/生效业务规则/限制变化或原文档写错时，**按需加载 `dev-doc-master`** 同步所属模块子 `DESIGN-<module>.md`；留下新长期工程约束时，**按需加载 `space-master`** 维护对应层级 `AGENTS.md`；测试遵循常驻 `rules/testing.md`。
- D-01a：**并行实施防文档冲突纪律**：并行 Task/分支中，实施者只能修改授权写集内所属模块的 `DESIGN-<module>.md`，**严禁越界修改共享主 `DESIGN.md` 或他人模块文档**；如在实施中发现授权写集之外的文档过时或写错，必须在交付报告的 `DESIGN Sync` 中上报主控处理。
- D-02：实施者可在已批准的决定和范围内调整实现技术细节，但不能修改设计授权；冲突及时 STOP 并报告涉及的行为、影响与可选处理。
- D-03：direct 和 Plan 路线使用相同的测试、文档同步、审查和验收质量标准；区别仅在组织方式和记录位置。
- D-04：委派 Agent 只提交代码变更与证据，不自主提交/审批、不写 Plan Done；主控检查差异与真实命令，再负责写回记录。
- D-05：新规范在旧 Plan 上保留兼容分支；只有新 dev-flow 切换完成后，才能将新契约作为新来源路线的默认行为。
- D-06：`df-implement-review` 保留 Q1–Q4、报告格式、复审预算和只读原则，在其中核查批准范围→代码、代码事实→DESIGN、失败边界及用户可理解性，**审查文档质量与防 AI 流水账（Slop Checklist）时直接参照 `dev-doc-master` 审查清单**，不另写第二套文档标准；审查者不得修改实施代码、DESIGN 或批准记录。
- D-07：`df-implement`、`df-implement-review` 的 `description` 必须精准区分**执行编码/测试/按需同步 DESIGN 与 AGENTS**和**对已交付 diff、代码及测试作独立只读评审**；前者在真实实施任务必须加载，后者在实施后代码审查必须加载。不得因“实施”“评审”“DESIGN”等共享词误选，也不得让实施前的设计方案评审误入实施后审查。
- D-08：同步增量更新 `.wopal/rules/coding-workflow.md`（及中文审核版），正式写入 `df-implement` → `dev-doc-master`/`space-master` 与 `df-implement-review` → `dev-doc-master` 的按需调用接力规则及并行不越界约束。

### Key Interfaces

- df-implement 的输入是明确授权的 Issue/direct 或 Proposal/Plan Task、原有 DESIGN/AGENTS 约束与适用参考。
- df-implement-review 的输入是授权来源、实际 diff、实际执行的测试、对应 DESIGN 与失败行为证据；反馈保留原报告字段，不能只给“文档已同步”的无证据结论。
- 返回给主控：Goal、Accomplished、Files、Verified（实际命令和结果）、DESIGN Sync（变动的所属模块文档、对应代码事实，以及并行期发现但未越界修改的写集外文档漂移上报）、Status/STOP 原因。
- 不另造 Plan/Proposal 工作状态，也不侵入 Git/commit 所有权。

## In Scope

- `df-implement` 的实施前取证、变更边界、按需调用 `dev-doc-master`/`space-master` 同步契约、并行不越界纪律、STOP/交接 SOP。
- 双路线的证据字段和最小正负 fixtures；旧 Plan 默认路线兼容。
- 在同一次交付内更新 `df-implement-review` 的 rubric 和中英版，按需参照 `dev-doc-master` 审查清单对新旧路线的实现质量与设计同步实行只读审查。
- 同步增量更新 `.wopal/rules/coding-workflow.md`（及中文审核版），记录实施与实施评审对能力底座的调用契约。
- 同轮精炼两项技能的 `description`，以 `skill-creator` 的近邻正反触发场景核实必加载、职责区分与中英语义一致性。

## Out of Scope

- 不变更 `df-proposal-review` 的**实施前**设计审查（已并入 enhance-dev-proposal）。
- 不修改 dev-flow 状态机、Plan 创建/批准/Graph 命令，不改变本体进化。
- 不修改真实业务代码、PRD/DESIGN/Plan 或实施记录。

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| 实施技能 | .wopal/skills/df-implement/{SKILL.md,SKILL.zh-CN.md} | 修改 | 双路线实施、按需调用文档/规范底座与并行不越界合同 |
| 实施评审 | .wopal/skills/df-implement-review/{SKILL.md,SKILL.zh-CN.md,references/review-rubric*.md} | 修改 | 真实实现及参照 `dev-doc-master` 的 DESIGN 双向核验 |
| 空间调用规则 | .wopal/rules/coding-workflow.md、.wopal/docs/LANG/zh-CN/rules/coding-workflow.md | 修改 | 增量补入实施与实施评审的按需调用接力规则 |
| 支持参考/隔离样例 | 必要的 df-implement 内部参考和临时 fixtures | 新增/修改 | 证据、并行不越界与 STOP 回归 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|

## Acceptance Criteria

### Agent Verification

1. [ ] 对已授权 direct 和 Plan 样例，实施者在实现公开行为后按需加载 `dev-doc-master` 同步所属模块子 DESIGN（纯内部重构不动文档），并提供具体代码、测试与文档对应关系；并行任务中发现写集外文档漂移仅上报主控而不越界修改共享主 `DESIGN.md`；有新长期工程约束时按需调用 `space-master`；不写未来未交付功能。
2. [ ] 对越权设计变化、缺失批准范围、接口冲突等负例，实施者 STOP 并报告，不擅自篡改 Proposal/Plan。
3. [ ] 委派报告能被控制者复核，有真实测试与文件证据；实施者不会自己批准 Task、改 Done 或提交正式交付。
4. [ ] 旧版已有 Plan 继续沿用旧流程，不被新文档规范追溯强制修改；没有真实业务文件变更。
5. [ ] `df-implement-review` 能参照 `dev-doc-master` 审查清单（含 Slop Checklist）以代码/测试/文档实证指出缺实现、旧行为回归、错误失败边界、缺 DESIGN 更新、并行越界修改共享文档和用户读不懂的说明；合法实现可以通过，原有 Q1–Q4、只读原则、复审预算与报告结构保持；`.wopal/rules/coding-workflow.md` 中英版本已增量同步。
6. [ ] `df-implement`、`df-implement-review` 两项 `description` 精准简洁、中文和英文触发语义一致；每项均通过 10 个应触发 + 10 个不应触发的实际近邻场景，覆盖编码实施、实施后 diff 评审、实施前方案评审、纯文档维护以及 dev-flow 的 Plan 管理。记录误选/漏选及修复复验，没有真实加载评估时不得声称已自动验证。

### DSH Principles → Tasks → Verification

| DSH 已验证来源 | 本提案取用的实践 | Task 与验收 |
|---|---|---|
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-code-review/SKILL.md` | 代码变更和公开行为/错误说明在同一 diff 更新；审查源于实际代码，不以只读的过去 DESIGN 当新行为的唯一标准 | Task 2、4；AC#1、5 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-doc-writing/SKILL.md` | 运行所声称的操作，对当前 checkout 实际事实取证；可阅读的说明与精确的失败边界同时保留 | Task 2、4；AC#1、5 |
| `labs/ref-repos/deepseek-harness/.agents/skills/dsh-prose-standard/SKILL.md` | 保留所有重要条件、不变量、失败保证，避免代码清单和重复解释 | Task 2、4；AC#1、5 |
| `labs/ref-repos/deepseek-harness/docs/AGENTS.md` | 事实只留一个所有者；需要的细节链接到所属层级 | Task 1、3、4；AC#3、4、5 |

`direct`、Plan 验收主控权及 C2C 委派规则是 **WopalSpace 自有机制**，不是 DSH 提供的生命周期。

### User Validation

#### Scenario 1: 交付后的 DESIGN 与代码说明相符
- Goal: 用户理解新实施交付如何把“做了什么”写进 DESIGN。
- Environment: 隔离的虚构实现与一份 direct 或 Plan 示例。
- Precondition: Tasks 和独立评审通过，已进入 validating。
- Launch command: `wopal space evo switch enhance-implement-sync`（切换后**重启 ellamaka** 以加载更新后的技能与空间调用规则）
- User Actions:
  1. 阅读实施证据与同步后的 DESIGN，不打开代码判断实现结果与限制。
  2. 查看一次设计冲突被阻止的示例。
- Pass criteria: DESIGN 描述已交付事实且决策未被 Agent 私自扩张。
- Failure feedback: 指出不对应的设计段落或越权行为。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 核对旧实施规则与新授权接口

**Verification Intent**: AC#2、AC#4
**Behavior**: 清楚区分旧 Plan 的设计前置规则与未来 Proposal/Issue 新路径，保持旧路线可用。
**Pre-read**: 当前 df-implement、dev-flow、Plan Guide、已经交付的 enhance-doc-contracts 文档体系与业务 Proposal 技能。
**Design**: 标明“已授权的新路径”和“既有旧路径”的适用条件，不按文档名字猜测来源；以真实 Plan metadata/source 为判断依据。
**TDD**: false — 规则归属与适配分析。
**Changes**: df-implement SKILL 的前置输入/兼容规则及中英说明。
**Verify**: 对旧 Plan 与新 Proposal 示例分别验证授权路由与旧约束保持。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: 代码、测试、按需同步 DESIGN/AGENTS 与并行不越界及冲突停止

**Verification Intent**: AC#1、AC#2
**Behavior**: 对外行为/接口/生效业务规则/限制变化时按需加载 `dev-doc-master` 同步所属模块子 DESIGN；有新长期工程约束时按需加载 `space-master`；纯内部重构不动文档；并行期不越界修改共享主 `DESIGN.md` 或他人模块文档，写集外漂移上报主控；缺少设计授权或暴露变更冲突时 STOP，不能通过提前改 DESIGN 使测试伪通过。
**Pre-read**: Task 1、`dev-doc-master` 现状写作与防并行规则、`space-master` AGENTS 维护 SOP、`rules/testing.md`、`df-implement` STOP/report 规则。
**Design**: 将按需调用 `dev-doc-master`/`space-master` 写入 `df-implement` 的轻量触发判据，绝不把文档模板或写作细则复制到 `df-implement`；明确并行写集边界，只改所属模块子文档、跨文档漂移写入 `DESIGN Sync` 上报主控。
**TDD**: false — SOP + 事实语义样例（含并行不越界与纯内部重构反例），验证由 review 阶段进一步覆盖。
**Changes**: `df-implement` 实施纪律、中英版、必要的支持参考。
**Verify**: 用虚构多模块代码变化验证必须同步、纯内部重构不动文档、并行越界拦截、虚构能力与遗漏失败边界等场景。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: 统一委派结果、直接实施证据与 `df-implement` 触发收敛

**Verification Intent**: AC#1、AC#3、AC#4、AC#6
**Behavior**: direct 和 Plan 实施返回同样强度的证据（含 `DESIGN Sync` 及写集外漂移上报），主控可独立复验；旧 Plan 的记录所有权不被修改。
**Pre-read**: Task 1–2、`skill-creator` 技能、现有 `df-implement` handoff、`dev-flow` Task Done/AC 记录要求。
**Design**: 明确 Files/Verified/DESIGN Sync/STOP 报告规范，不复制 Graph 进度；以项目和来源选择记录落点。
**TDD**: false — 记录合同用隔离正反案例和独立评审验证。
**Changes**: `df-implement` 的 handoff/report、中英 `description` 与示例。
**Verify**: 模拟 direct、Plan、STOP 三种返回，由主控完成复核，检查实现者不能自签验收；精炼 `df-implement` description，完成 10+10 近邻正反触发测试，不能把普通 Plan 编排/只读评审/纯文档维护误判为实施。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: 在独立实施评审中接入 `dev-doc-master` 审查清单并增量更新 `coding-workflow.md`

**Verification Intent**: AC#1、AC#2、AC#5、AC#6

**Behavior**: `df-implement-review` 在实际 diff 和测试证据中判断新功能是否真的完成、旧行为是否退化、错误边界是否正确、代码公开行为是否同步到用户可理解的所属模块 DESIGN，且参照 `dev-doc-master` 审查清单抓出假实现、缺测试、并行越界改共享文档、文件清单充数、AI 思考过程泄露与虚构行为；同时增量更新 `.wopal/rules/coding-workflow.md` 记录实施与评审对能力底座的调用契约。

**Pre-read**: Task 1–3、`skill-creator` 技能、`dev-doc-master` 语义审查清单与 Slop Checklist、`.wopal/rules/coding-workflow.md`（及中文审核版）、`df-implement-review/{SKILL.md,references/review-rubric.md}` 及中文版本、DSH `dsh-code-review/SKILL.md`、`dsh-doc-writing/references/review.md`、`dsh-prose-standard/SKILL.md`。

**Design**: 保留原 Q1–Q4 四问题及报告/复审规则，补充授权设计→实际代码、代码公开行为→所属模块 DESIGN 两条证据链，文档语义与 Slop Checklist 直接链接 `dev-doc-master` 不重复抄写；增量更新 `coding-workflow.md`（及中文审核版），不提前宣称子提案 4 的新 `dev-flow` CLI 已上线。

**TDD**: false — 审查语义采用多组确切 code+tests+DESIGN 案例与干净上下文独立判断验证；无需新增不可靠的词汇匹配脚本。

**Changes**: `df-implement-review` 的 Skill、rubric、中英版，以及 `.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` 与必要正负样例。

**Verify**: 对真实一致样例、未实现关键行为、未同步 DESIGN、并行越界改共享主文档、遗漏错误边界、只有文件名清单与思考过程泄露样例分别独立出报告；检查只读、旧 Plan 审查、复审预算不变及 `coding-workflow.md` 中英一致；精炼 `df-implement-review` description，完成 10+10 近邻正反触发验证，不能因只出现“review”就抢占方案评审。

**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | enhance-doc-contracts、enhance-dev-proposal | 输入、文档合同与兼容研究 |
| 2 | Task 2 | Wopal 主控 | Task 1 | 同步与冲突纪律 |
| 3 | Task 3 | Wopal 主控 | Task 2 | 交接证据落点 |
| 4 | Task 4 | Wopal 主控 | Task 3 | 与实施证据同轮完成独立评审能力 |

逐 Task 由 Wopal 实施/验证，经 C2C/ChatGPT 的 df-implement-review 独立只读评审通过再提交，不委派 Fae、不调用 Rook；最终用户验证与集成遵循本体进化现有规则。

## Delivery

本子提案独立 draft；新规则先可用但不擅自切换旧 Plan。若后续 dev-flow 切换尚未完成，本子提案不得宣称全链路新流程已经上线。
