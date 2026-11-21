# enhance-dev-flow-proposal

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-11-19
- **Stage**: draft
- **Mode**: (none)
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: High — 同一复杂 `dev-flow` 技能需要同时改造 Plan/Task 拆分 SOP、Graph 规则和实际 CLI 来源/授权/兼容逻辑；涉及大量脚本和回归测试，必须在一份提案内按行为拆成可独立验证的 Task。
- **Confidence**: High（旧 Plan/Graph 合同、CLI、模板和测试现状已核对）；Medium（历史无来源 Plan 的可信识别、direct 路由与多 Plan 一致性需实施阶段实际验证）。

## Goal

在**同一份子提案**中完整改造 `dev-flow`：明确 `dev-flow` 作为站在 Proposal/Issue 与实施之间的**可选编排层**（简单有界任务直接实施、复杂任务才启用 Plan），确立如何从 Issue/获批 Proposal 合理拆分 Plan 和 Task、如何委派并行（含代码与分片 `DESIGN-*.md` 的并行写集防冲突检查）及建立 Plan Graph；并将这些规则落实到来源授权、direct/多 Plan、创建/审批/交付 CLI 与历史兼容，同时将 `.wopal/rules/coding-workflow.md` 收口为完整目标态。**新 SOP 与真实命令机制一次性验收，不再单独创建拆分 SOP 提案**；保留现有 Plan 状态机，后续再考虑状态和重复审批精简。

## Technical Context

### Architecture Context

产品总提案：`docs/products/wopal-space/proposals/development-governance-proposal.md`，本文件是实施子提案 **4**，也是本轮唯一对 `dev-flow` 复杂脚本进行修改的提案。

前置成果：
- `enhance-doc-contracts`：已交付瘦身后的文档能力底座 `dev-doc-master`（现状 DESIGN、薄主地图 + 按模块分片、去掉主文档头部 `Sub-DESIGNs` 强枚举、实测取证与 Slop Checklist）、`space-master` 维护 SOP 及 `.wopal/rules/coding-workflow.md` 初版；本提案不得恢复目标态 DESIGN/Phase/GAPS 的新流程前置。
- `enhance-dev-proposal`：业务 Proposal/Delivery 的决定和授权边界、`df-proposal-review` 的实施前方案审查，以及 `coding-workflow.md` 第二阶段更新。
- `enhance-implement-sync`：`df-implement` 按需调用 `dev-doc-master`/`space-master` 完成代码、测试与所属模块现状 DESIGN 同步（含并行不越界纪律）、`df-implement-review` 的独立实施审查，以及 `coding-workflow.md` 第三阶段更新。
- 产品总提案对 PRD/Proposal/可选 `dev-flow`/DESIGN 的职责定义是设计依据，前置子提案已落实文档、提案与实施同步合同；本提案收口 `dev-flow` 并完成 `.wopal/rules/coding-workflow.md` 的最终目标态。

现行 `dev-flow/SKILL.md`、`references/plan-guide.md` 和 `templates/plan.md` 定义 Plan/Task/委派及目标态 DESIGN/Phase 前置；`references/active-plan-graph.md` 定义跨 Plan nodes、edges、groups。CLI 从 `scripts/flow.sh` 进入 `flow.py`，实际命令在 `scripts/commands/`，状态机位于 `scripts/workflow.py`，校验入口位于 `scripts/validation.py` 等。现有流程为 planning → reviewing → executing → verifying → done，归档另有命令；`approve --confirm` 同时承担用户确认及 Git 工作树初始化；这些底层状态和交付行为本轮保留。

### Research Findings

- **Plan 拆分边界**：单个 Plan 一个 Target Project、一个可独立验证的结果；同一批准的 Proposal 可以 direct 或拆成 0..N 个 Plan，不按文件数、目录数、Agent 数机械拆分。批准范围要检查完整覆盖、责任重叠及有无无效先后关系。
- **Task/委派边界**：Task 是有行为结果、输入、前置、必要 Interface/Constraints、可复现 Verify 的实施单元。并行须检查共享写集、稳定接口契约、隔离环境、验证资源、提交所有权及依赖；仅“不改同一文件”不足以判定可并行。
- **Graph 事实归属**：当前 `.wopal-space/plans/active-graph.json` 由控制 Agent 在 submit/archive 等生命周期点维护，edge from→to 表示前置 Plan 到 done 才能开始后继 Plan；group 仅为共同目标分组，不是依赖或状态真相源。禁止环、自边、重边、缺节点引用和状态复制。
- **来源与兼容**：旧 CLI 可从 Issue 或无 Issue 的 Active DESIGN 创建 Plan。新 Plan 必有唯一主要 Source（Issue 或 Proposal），获批范围与 Delivery 需真实核验；历史无 Source Plan 仍可续办，绝不能靠用户可伪造的日期字段区别旧新文件。
- **同轮替换**：本提案必须在 `dev-flow` 自身真正删除新来源路径对旧 Phase/GAPS/目标态 DESIGN 的错误前置，并建立 Source/approve/Graph 的真实检查。文档生产技能的旧命令属于 `dev-doc-master`，由其对应提案自己一次性替换。
- **质量与未来方向**：SOP 正反例、CLI 成功/拒绝/失败无副作用测试及三种 worktree 模式均应实际验证；不另建 Scheduler、任务数据库或重复的 Plan Graph 状态。
- **DSH 的适用边界**：DSH 的文档层级、单一事实归属和审查事实依据可借鉴；Plan Graph、Agent 并行和本空间审批/Git 门禁为 WopalSpace 自主设计，不能声称是 DSH 的既有能力。

**References**:
- `.wopal/skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,AGENTS.md,templates/plan.md}`
- `.wopal/skills/dev-flow/references/{plan-guide.md,plan-guide.zh-CN.md,active-plan-graph.md,active-plan-graph.zh-CN.md,commands.md,issue-guide.md}`
- `.wopal/skills/dev-flow/scripts/{flow.sh,flow.py,workflow.py,validation.py,plan.py}`
- `.wopal/skills/dev-flow/scripts/commands/{plan.py,submit.py,approve.py,complete.py,verify.py,integrate.py,archive.py}`
- `.wopal/skills/dev-flow/tests/python/`
- `.wopal/docs/evolutions/{enhance-doc-contracts.md,enhance-dev-proposal.md,enhance-implement-sync.md}`
- `docs/products/wopal-space/proposals/plan-orchestration-scheduler-proposal.md`（远期方向，不作为当前授权）
- `labs/ref-repos/deepseek-harness/docs/AGENTS.md`
- `labs/ref-repos/deepseek-harness/.agents/skills/dsh-doc-writing/references/structure-hierarchy.md`
- `labs/ref-repos/deepseek-harness/.agents/skills/dsh-code-review/SKILL.md`

### Key Decisions

- D-01：`dev-flow` 与 Plan 是**位于 Proposal/Issue 与实施之间的可选编排层**。低风险、有界且可直接验收的已批准 Proposal 或明确 Issue 走 direct 直达 `df-implement`；跨项目、多个独立交付、复杂迁移、依赖较多或需要委派并行时才启用 `dev-flow` 拆 Plan，不因有 Proposal 就机械要求 Plan。
- D-02：新 Plan 只有一个主要 Source：Issue #N 或 Proposal PATH；关联 Issue 只是追踪，DESIGN/PRD/无来源文本都不能成为新增 Plan 的实施授权。
- D-03：重要设计改变须先审查获批 Proposal，既有决定内的缺陷或明确工作走 Issue；Plan 不能扩大批准范围，冲突时停止并交用户决策。
- D-04：Proposal→Plan 的 SOP：确认批准范围→识别独立可验收成果→按 Target Project 划分 Plan→检查覆盖/重复→记录真实跨 Plan 依赖。一个 Plan 只服务一个目标项目。
- D-05：Plan→Task 的 SOP：行为成果、Pre-read、必要 Interface/Constraints、Verify、Done 证据和依赖必须清楚；既反对按文件机械碎片化，也反对不可独立验证的超大 Task。
- D-06：Agent 委派按能力、风险与权限匹配；主控保有 Task 复核、证据、提交和 Plan 状态所有权；并行检查的共享写集同时覆盖**代码文件与 `DESIGN-*.md` 文档**：按 `enhance-doc-contracts` 确立的薄主 `DESIGN.md` + 模块子文档分片（无头部 `Sub-DESIGNs` 枚举），并行 Task 各自仅修改所属模块的 `DESIGN-<module>.md`，若确需更新主 `DESIGN.md` 地图则由主控在集成汇总阶段收口，严禁并行分支同时编辑主 `DESIGN.md`；任何契约、写集、依赖、隔离、验证或提交不安全时一律串行。
- D-07：跨 Plan 依赖只归 Active Graph；Plan 管内部 Task 顺序/委派，Graph 只存节点/边/组，不复制 Plan 状态；groups 不能推导依赖。原 Graph schema 保留。
- D-08：现有 Plan 状态（planning、reviewing、executing、verifying、done）以及 submit/approve/complete/verify/integrate/archive 与第二次用户批准本轮保留；未来状态机或重复审批精简另行立项。
- D-09：只有获批 Proposal 且 Delivery 与执行路径相符才允许实施；未批准/被拒/越界不得借 Plan 或 direct 路线绕过授权。
- D-10：direct 和 Plan 交付都要求真实代码、测试、受影响 DESIGN 同步、独立评审和必要用户验证；部分 Plan done/archive 不自动把整个 Proposal 标记 implemented。
- D-11：**同一次 dev-flow 改造**同时删除新来源链路错误的旧 DESIGN/Phase/GAPS 前置并接入 Source/批准检查，不能留待文档清理或再做一次 CLI 提案。
- D-12：Graph 维护须与真实生命周期操作一致，Graph 更新失败或出现不可信状态，应暂停后续执行、调查并修复；不能伪造原命令已回滚。
- D-13：历史无来源 Plan 保留可续办，新无来源 Plan 必拒绝；身份依赖可信记录/受控基线，不能仅按用户可修改的日期或文本判定，无法可靠判断须停止并上报。
- D-14：不建设 Scheduler、cron、任务运行队列、重复状态表或额外 Graph；Plan/Task/Graph 规则可为远期自动化复用。
- D-15：只修改 `dev-flow` 直接关联 Skill、命令、模板、参考和测试；文档技能的 Phase/GAPS/BR 生产端由 `enhance-doc-contracts` 负责，不得将本技能自己的旧校验清理推给后续。
- D-16：本子提案一次审批、八个可验证 Task、一次最终交付；先研究并建立拆分/并行/Graph 的准确标准，再将其落实到 CLI/安全兼容测试。
- D-17：本次重构必须同步精炼 `dev-flow/SKILL.md` 的 `description`，明确 **`dev-flow` 作为可选编排层负责 Issue/Proposal→direct/Plan 判定、Plan/Task/Graph 编排、批准与生命周期管理**；单纯写业务 Proposal、直接编码实施、只读方案/代码评审、PRD/DESIGN 内容维护不应被笼统“development”抢占。同时将 `.wopal/rules/coding-workflow.md`（及中文审核版）更新收口为完整目标态，把 `dev-flow` 的可选位置和全链路调用图固定下来。需与 `dev-proposal`、`df-implement`、`df-proposal-review`、`df-implement-review`、`dev-doc-master` 做边界正反验证，保留旧 Plan 维护的正常触发。

### Key Interfaces

- Authoring 产物：Source、Target Project、Plan 拆分及完整覆盖理由、Task 行为/Verify/依赖、委派/并行决策；只链接 Proposal 中的设计理由，不复制设计文本。
- `flow.sh plan new ISSUE_NUMBER --project PROJECT ...` 保留 Issue 路线；新增 Proposal 来源参数（flag/argparse/调用兼容形状由 Task 5 对真实脚本取证后定案），不得用 `Issue: N/A` 伪造授权。
- `flow.sh plan check/submit/approve --confirm`：对新来源、目标项目、Proposal approved/Delivery、实施范围执行相应检查；非法输入不得造成半写入；历史 Plan 经可靠识别后走既有兼容机制。
- `flow.sh complete/verify --confirm/integrate/archive`：保留既有 Git/worktree/commit subject/PR、验收与归档行为；不可由单个 Plan 的 done 自动推算 Proposal implemented。
- Active Plan Graph 保持 `nodes/edges/groups`、edge from→to 上游 done 的原有语义；Graph 不记录重复的 Plan 状态；Task 依赖留在 Plan。
- 新 Issue/Proposal 路径不以前置目标态 DESIGN/Phase/GAPS 作为合法开工条件；历史 Plan 的已有字段仍可读取和验证。

## In Scope

- 一次性建立 Plan 必要性、Proposal/Issue→Plan、Plan→Task、委派、并行和 Graph 依赖 SOP，并落实到 Skill、Plan Guide、模板与真实正反案例。
- Issue/Proposal 双来源、direct/多 Plan、创建/提交/批准、Graph 规则、历史 Plan 兼容和实际 CLI/集成测试。
- 同轮移除 dev-flow 自身的新来源路径对旧 DESIGN/Phase/GAPS 的前置依赖，维护中英参考及现有质量/正式交付行为。
- 同步将 `.wopal/rules/coding-workflow.md`（及中文审核版）收口为最终目标态（完整展示 Proposal/Issue → 可选 `dev-flow` → `df-implement` → `df-implement-review` 及对 `dev-doc-master`/`space-master`/`rules/testing.md` 底座的按需调用）。
- 精炼 `dev-flow` 中英技能的触发描述，用真实任务场景验证必须加载和必须由相邻技能处理的排除边界，避免遗漏合法生命周期请求。
- 保留历史 Plan 六阶段、工作树/Git 模式、独立评审和必要用户授权。

## Out of Scope

- 本轮不重写 Plan 状态机、不删除第二次 Plan approve、不大规模迁移历史 Plan、Git 工作树/PR 集成机制或旧仓库记录。
- 不增加 Scheduler、cron、Task 执行数据库或第二张 Plan Graph，不变更 Graph schema。
- 不修改 ontology-evolution、`wopal-cli`、真实业务代码/业务 DESIGN、现行 Plan 或实际 active-graph.json。
- 不在本技能修改 `dev-doc-master` 的 `cupdate-roadmap/cupdate-br` 或旧文档模板；这些应由文档技能在其完整子提案中同轮去旧和加新。

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| Plan/Task SOP | `.wopal/skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,templates/plan.md,references/plan-guide*.md}` 与必要新增参考 | 修改 | Plan 必要性、拆分、委派并行 |
| Graph | `.wopal/skills/dev-flow/references/active-plan-graph*.md` 与隔离 fixtures | 修改/新增 | 依赖、分组和一致性规范 |
| CLI 来源与审批 | `.wopal/skills/dev-flow/scripts/{flow.sh,flow.py,plan.py,validation.py,workflow.py}` 及 `scripts/commands/{plan,submit,approve}.py` | 修改 | Source/批准/旧规则退场 |
| 交付兼容 | `scripts/commands/{complete,verify,integrate,archive}.py` 等直接影响模块 | 必要修复/回归 | 保留 Git/Plan 交付 |
| 空间调用规则 | `.wopal/rules/coding-workflow.md`、`.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` | 修改 | 收口最终目标态技能协作图与可选 `dev-flow` 定位 |
| 测试 | `.wopal/skills/dev-flow/tests/python/{unit,integration}/` 与隔离 Git/Graph fixtures | 新增/修改 | SOP 与真实 CLI 正负验证 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|

## Acceptance Criteria

### Agent Verification

1. [ ] 对简单、有界的批准 Proposal/Issue 能合理选择 direct；跨项目或多个独立交付的 Proposal 可拆合理 Plan，各有明确目标项目和验收边界，批准范围无重复/遗漏。
2. [ ] Task 按可独立验收的行为拆分，包含 Pre-read、必要接口/约束、依赖、Verify、Done 证据；无意义碎片化、巨型任务、伪依赖与扩范围被明确指出。
3. [ ] Agent 能力与风险匹配；Task 并行候选同时检查代码与 `DESIGN-*.md` 的共享写集、契约、依赖、隔离、测试资源与提交所有权，确保并行分支只写各自模块子 DESIGN、共享主 `DESIGN.md` 由主控收口，危险并行改为串行或重新拆分。
4. [ ] Graph 的合法 DAG 与分组通过；环、自边、重边、缺节点引用、把 groups 当 edges 或复制状态的负例被指出；schema 与历史文件不变。
5. [ ] 新 Issue 与获批 Proposal 来源的 Plan 可由真实 CLI 创建、提交、批准；无来源、错误项目、未批准/被拒/越界来源被拒，失败不半写入。
6. [ ] 旧无 Source/Issue: N/A 的 Plan 可靠识别并继续生命周期；新无来源 Plan 不能伪装历史文件绕过授权，身份有可信依据和真实回归。
7. [ ] 获批 Proposal 可以 direct 或关联不同 Target Project 的多个 Plan；部分交付不自动变 implemented，真实跨 Plan 依赖与来源不失真。
8. [ ] 新 Plan 的创建、提交、批准/正式实施在本轮同时去掉旧 Phase/GAPS/目标态 DESIGN 前置并增加来源授权校验，不遗留半完成的旧入口。
9. [ ] 旧 Plan 生命周期、normal/no-worktree/existing-worktree、commit subject、Git/PR 集成、用户验收和归档行为在测试中不退化，实际业务文件与 Graph 无改写。
10. [ ] 新 direct/Plan 路线与代码、测试、所属模块现状 DESIGN、独立评审和用户验证相符；非法扩范围被阻止，中英文规则、`.wopal/rules/coding-workflow.md`（完整目标态）与实际命令一致。
11. [ ] SOP 与 CLI 的所有关键条件均有实际正负案例或独立语义审查，不新增 Scheduler/第二份状态或进度台账。
12. [ ] `dev-flow` 的 `description` 简洁准确地覆盖 Issue/Proposal→direct/Plan 组织、Plan/Task/Graph 编排、批准和生命周期管理，排除纯业务 Proposal 写作、编码实施、独立方案/代码评审及 DESIGN 写作；至少 10 个应触发和 10 个不应触发的近邻请求得到验证，旧 Plan 生命周期的合法加载不退化。记录改前/改后、误触发/漏触发和实际测试能力的限制，中英语义一致。

### Source Principles → Tasks → Verification

| 已核实的来源 | 在 dev-flow 中采取的具体实践 | Task 与 AC |
|---|---|---|
| DSH `docs/AGENTS.md`、`dsh-doc-writing/references/structure-hierarchy.md` | 一项事实只有一个归属；紧密关联规则保持在一起，不为拆分而碎片化 | Tasks 1–4；AC#1、2、4 |
| DSH `dsh-code-review/SKILL.md` | 依据真实 diff/调用链和已执行检查进行审核，代码与文档说明在同一交付中一致 | Tasks 5–8；AC#5、8、9、10 |
| WopalSpace `dev-flow/references/plan-guide.md`、`templates/plan.md` | Task 是可单独验证的行为单元，主控保留委派/提交/复验所有权 | Tasks 2、3；AC#1、2、3 |
| WopalSpace `dev-flow/references/active-plan-graph.md` | Graph 唯一记录跨 Plan 依赖；groups 不推导 edges，并行需要稳定契约/隔离条件 | Tasks 3、4、7；AC#3、4、7 |
| WopalSpace `dev-flow/scripts/flow.py`、`workflow.py`、`commands/` | 来源、审批、Git/工作树的实际成功/拒绝和失败无副作用行为可重复验证 | Tasks 5–8；AC#5、6、8、9 |

**DSH 没有 Plan Graph、Agent 并行、用户审批和 Git 状态机的现成实现**；后者是 WopalSpace 的自主设计，不能把 DSH 文档当作实施授权或代替测试结果。

### User Validation

#### Scenario 1: 验收拆分策略与真实授权执行
- Goal: 用户一次性检查“合理 Plan/Task 拆分→委派与并行判断→CLI 安全执行→独立验证”是否形成完整机制。
- Environment: 本提案隔离工作树与虚构 Issue、approved Proposal、两个目标项目、临时 Git/Graph fixtures。
- Precondition: 八个 Task 均验证并独立评审通过，已进入 validating。
- Launch command: `wopal space evo switch enhance-dev-flow-proposal`（切换后**重启 ellamaka** 以加载更新后的技能、脚本与最终版空间调用规则）
- User Actions:
  1. 检查简单 direct、跨项目多 Plan、Task 粒度、安全/不安全并行的样例。
  2. 检查两种来源 CLI、Graph 依赖、未批准 Proposal/新无来源 Plan 的拒绝和历史 Plan 回归。
  3. 检查部分 Plan done 不等于 Proposal implemented，实际业务资料无变更。
- Pass criteria: 拆分边界与委派决定合理，CLI/Graph/正式交付安全且可重现，旧行为不退化。
- Failure feedback: 指出具体错误拆分、输入、结果、状态或日志。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 从真实 Plan/Graph 合同反推拆分边界

**Verification Intent**: AC#4、AC#5、AC#6、AC#9、AC#11
**Behavior**: 明确 Plan 现有一个项目、Graph 唯一依赖、旧模板/CLI 必需字段、现有状态/Git 门禁和历史兼容边界。
**Pre-read**: 当前 dev-flow CLI 真实调用链、dev-flow SKILL、plan-guide、active-plan-graph、templates/plan.md、AGENTS.md、现有 Plan 检查测试。
**Design**: 记录真实消费者、来源约束和格式边界，明确本提案的 SOP、模板、脚本及测试分别在哪个后续 Task 修改；不得把同一 dev-flow 改造留给另一份提案。
**TDD**: false — 合同与风险取证。
**Changes**: SOP 的兼容清单和范围边界。
**Verify**: 旧 Plan/Graph 的已有测试和参考示例无变化。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: Issue/Proposal→Plan 划分 SOP 与范围覆盖检查

**Verification Intent**: AC#1、AC#2
**Behavior**: 对明确 Issue 或已批准 Proposal 判定 direct/plan，按独立可交付成果/目标项目分出合理 Plan，覆盖每项批准范围，不发明第二套业务决定。
**Pre-read**: Task 1、已交付的业务 Proposal 合同、Plan Authoring Guide、项目/产品结构映射。
**Design**: SOP 顺序固定：确认授权与目标→识别具体结果→判定独立交付边界→划分 Target Project→覆盖/重复审查→标明跨 Plan 依赖；拒绝按人头/文件数机械拆分。
**TDD**: false — 深度语义案例与独立 Proposal 评审验证。
**Changes**: plan-guide 与必要新 reference、隔离正反案例。
**Verify**: 同一 Proposal 的 direct、1 Plan、跨项目多 Plan、错误漏项等案例均能给出有根据的结论。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: Plan→Task 及委派/并行 SOP（含 DESIGN 写集防冲突）

**Verification Intent**: AC#2、AC#3
**Behavior**: 每 Task 有可验证成果、输入/前置、必要契约与交接记录，能够依据能力和安全条件委派；代码或 `DESIGN-*.md` 共享路径碰撞、需要并发改共享主 `DESIGN.md` 以及不稳定接口不被误判为可并行。
**Pre-read**: Tasks 1–2、已交付的 `dev-doc-master` 防并行分片规则、`df-implement` handoff 与并行不越界纪律、旧 Task/Delegation Strategy 模板、已有 Git worktree/提交安全规则。
**Design**: 任务粒度由可独立验收的行为而不是文件行数决定；对并行实施增加“契约、写集（含代码与模块子 DESIGN）、环境、验证、提交”五方面检查：并行 Task 各自只更新所属 `DESIGN-<module>.md`，共享主 `DESIGN.md` 地图变动留给主控在集成时收口，冲突时选择串行或先隔离。
**TDD**: false — SOP 与隔离调度演练。
**Changes**: plan-guide、模板兼容性扩展、委派示例与正反 fixtures。
**Verify**: 多 Agent 并行可行（互不相交的代码+模块子 DESIGN）与不可行（共享主 `DESIGN.md` 或重叠写集）案例均能复现理由，旧模板仍被真实 CLI 接受。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: Graph 组织规则与多 Plan 模拟

**Verification Intent**: AC#1、AC#3、AC#4、AC#11
**Behavior**: 同一来源的多个 Plan 可用 Graph 分组和 edge 表示正确先后；无关任务不造伪依赖；非法环/引用被发现。
**Pre-read**: Tasks 1–3、active-plan-graph、现有测试/fixtures、Plan 状态机。
**Design**: 对 Graph 只设跨 Plan 顺序与组织，不复制 Plan 状态；允许并行根；不得提前实现 Scheduler 或修改真实 Graph；原状态约束保持。
**TDD**: true — 可机械验证的 Graph 反例用已有 JSON fixture 检查路径或测试工具覆盖，不增加与未来实现耦合的新运行字段。
**Changes**: Graph 参考及真实适用的测试 fixtures；仅必要修改 dev-flow SKILL 发现入口。
**Verify**: 使用隔离样例检验合法 DAG、环、自边、重复边、缺节点、非法成员，并运行 Plan 旧回归。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 5: 查明创建/校验路径与历史 Plan 兼容判定

**Verification Intent**: AC#5、AC#6、AC#9
**Behavior**: 明确 Issue/no-Issue 创建入口、字段/命名/状态检查位置和旧无 Source Plan 的识别方式，任何新 Plan 都不可伪装成旧文件。
**Pre-read**: Tasks 1–4 的 SOP/Graph 合同、scripts/flow.{sh,py}、commands/{plan,submit,approve}.py、plan.py、validation.py、workflow.py、Plan 目录与 tests/python 的现有行为测试。
**Design**: 先对真实调用链制作输入→状态改变表；对存量 Plan 来源判定必须有可信依据（如既有被跟踪的记录/显式切换基线），不可仅依赖可伪造日期；若现场没有安全的兼容依据，停止并返回用户确定最小迁移/例外策略。
**TDD**: true — 新无来源拒绝与旧存量可续办的对照 RED。
**Changes**: 入口/校验模块及必要测试 fixtures 的最小改动；确定具体新 Proposal CLI flag。
**Verify**: 在隔离 Git fixtures 上分别执行合法创建/无来源创建/旧存量 submit/approve 的真实命令，确认失败无副作用。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 6: Proposal 来源与批准门禁

**Verification Intent**: AC#5、AC#7、AC#8
**Behavior**: 新 Source: Proposal 的 Plan 可草拟；只有真实 approved 且授权 Delivery: plan 的 Proposal 可推进执行；被拒/未批准/路径错误不越权。
**Pre-read**: Task 5、enhance-dev-proposal 的模板/校验器、Plan 元数据与 Project Path 检查、既有同步 Issue 逻辑。
**Design**: 新 Source 指唯一批准文件，Issue 只作关联；审批时校验用户授权已存在且 Plan 在批准范围内；既有第二次 approve --confirm 暂时保留，禁止通过 flag 误触发既有 Git/工作树副作用。
**TDD**: true — 未批准/拒绝/越界/错误目录和正确 approved 样例。
**Changes**: plan new、submit/approve 来源处理、模板、tests。
**Verify**: 对新 Source 的实际 CLI 入口跑正负案例，确认状态和 Git 均无半执行。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 7: direct 与多 Plan/Graph 衔接

**Verification Intent**: AC#1、AC#4、AC#7、AC#8
**Behavior**: 已获授权的简单 Proposal 无 Plan 直接执行；复杂 Proposal 生成经 Tasks 2–4 的 SOP 确认的多个 Plan，Graph 只有真实依赖且无环；任何一个 Plan 完成不自动改变 Proposal 决定状态；新来源链路不再强求目标态 DESIGN/Phase/GAPS 前置条件。
**Pre-read**: Tasks 1–6、active-plan-graph、旧 Task/委派与 Graph 生命周期钩子。
**Design**: 复用现有 Graph 文件的 nodes/edges/groups 与控制 Agent 手工维护纪律；不新增 Graph Scheduler 或复制进度；新来源使用真实 Source 与批准决定，不能被旧 Phase/GAPS/目标态 DESIGN 检查反向阻断。Graph 更新失败按既有规则立即阻止后续审批并修复一致性。
**TDD**: true — 来源/多 Plan/合法/非法 Graph 及部分交付正负案例。
**Changes**: dev-flow SOP 使用点、必要检查与测试、参考文档。
**Verify**: 隔离模拟 direct、两项目 Plan、Plan 部分 done 与来源回溯；Graph 无效场景不能开工。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 8: 既有交付兼容、收口 `coding-workflow.md` 与新流程端到端验证

**Verification Intent**: AC#1–12
**Behavior**: 新路线符合代码/测试/所属模块现状 DESIGN 同步和独立评审；旧 status、批准、complete/verify/integrate/archive 与 3 种 Git 交付模式仍可靠；`.wopal/rules/coding-workflow.md`（及中文审核版）收口为完整目标态，清楚表达 `dev-flow` 的可选中间层位置与全部技能协作边界。
**Pre-read**: Tasks 1–7、`skill-creator` 技能、`.wopal/rules/coding-workflow.md`（及中文审核版）、commands/{complete,verify,integrate,archive}.py、工作树/commit subject 相关测试、`enhance-implement-sync` 与 `enhance-dev-proposal` 中已更新的评审合同。
**Design**: 对真实命令做正负集成检查；不修改历史文件，必须在此 Task 确认 `dev-flow` 新来源链路已移除 Phase/GAPS/目标态 DESIGN 的旧前置检查；验收记录及 Git 必须核对真实落点；最终更新 `coding-workflow.md` 去除过渡期限制提示。
**TDD**: true — 新来源和旧交付状态的端到端回归。
**Changes**: 最小必要的脚本/参考/模板修正、tests/python fixtures、中英技能，以及 `.wopal/rules/coding-workflow.md` 与 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`。
**Verify**: 运行 `dev-flow` 全量相关 pytest/实际 `flow.sh` 模拟命令，检查真实目录白名单、状态机、正式交付和未审批拒绝；核对 `coding-workflow.md` 中英一致且准确反映完整目标态；对照 `skill-creator` 的 description 规范测试 `dev-flow` 10+10 近邻触发场景（与 Proposal 写作、直接实施、两类评审及文档维护交叉比较），记录描述改前/改后和重测结论。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | enhance-doc-contracts、enhance-dev-proposal、enhance-implement-sync | 取证已交付文档合同和 Plan/Graph/CLI 当前契约 |
| 2 | Task 2 | Wopal 主控 | Task 1 | Plan 合理划分与范围覆盖 |
| 3 | Task 3 | Wopal 主控 | Task 2 | Task 粒度、委派与并行 |
| 4 | Task 4 | Wopal 主控 | Task 3 | Graph 依赖及正负模拟 |
| 5 | Task 5 | Wopal 主控 | Task 1、4 | 新旧来源身份与安全基线 |
| 6 | Task 6 | Wopal 主控 | Task 5 | Proposal 来源/批准门禁 |
| 7 | Task 7 | Wopal 主控 | Task 4、6 | direct、多 Plan 与 Graph 衔接 |
| 8 | Task 8 | Wopal 主控 | Tasks 1–7 | 实际 CLI 与正式交付回归 |

**同一份提案、八个 Task、一次用户批准与最终验收。** 每 Task 由 Wopal 主控亲自实施、实际验证、C2C/ChatGPT 加载 df-implement-review 独立只读评审、修复再复验，通过后回填并提交；不委派 Fae、不调用 Rook。用户仍独立批准、验证与授权正式集成。

## Delivery

此子提案保持 draft，不继承产品总提案的实施授权，获批前不修改技能代码。**本提案在同一轮内完成 dev-flow 的 SOP、Task 委派并行、Graph、真实 CLI 与旧前置规则退出**；不能再把 SOP 或相关旧校验留给下一份实施提案。其他 Skill 所属的 Phase/GAPS/BR 文档生产入口已由前置 `enhance-doc-contracts` 完成退场。Plan 状态机精简、第二次审批去重和自动 Scheduler 不属于本轮。
