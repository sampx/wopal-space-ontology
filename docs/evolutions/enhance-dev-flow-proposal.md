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

- **Complexity**: High — 同一复杂 `dev-flow` 技能需要同时完成可选规划 SOP、防共享 Delivery 死锁的 Graph 规则、Proposal 来源授权、消除重复设计审批与逐 Plan 重复验收的 CLI 精简，以及旧 Phase 前置清理与全量回归测试；拆为 7 个高内聚、可独立验证的 Task 在一轮内收口。
- **Confidence**: High — 已实查 `workflow.py`、`validation.py`、`submit.py`、`approve.py`、`complete.py`、`verify.py`、`integrate.py`、`active-plan-graph.md` 与 `templates/plan.md` 的真实实现和调用链。

## Goal

在**同一份子提案**中将 `dev-flow` 精准收口为位于 Proposal/Issue 与实施之间的**可选实施规划与任务组织层**：**保留并做强详细 Plan/Task 编写与 Git 工作树安全底座，彻底砍掉与 Proposal 重复的二次设计审批和逐 Plan 重复验收流程（不另造新状态机）**，根除共享 Delivery 与 Graph 依赖死锁，落地不强绑 GitHub Issue 的 Proposal 来源授权门禁并同轮移除旧 `Phase`/`GAPS`/目标态 `DESIGN` 前置，核对 `.wopal/rules/coding-workflow.md` 最终目标态，并同交付收口本体现状设计文档 `.wopal/docs/DESIGN-coding-workflow.md` 与 `.wopal/docs/DESIGN-capabilities.md`。

## Technical Context

### Architecture Context

产品总提案：`docs/products/wopal-space/proposals/development-governance-proposal.md`，本文件是实施子提案 **4**，也是本轮唯一对 `dev-flow` 复杂脚本进行修改的提案。

前置成果：
- 子提案 1（已归档：`.wopal/docs/evolutions/archived/20261122-enhance-doc-contracts.md`）：已交付文档底座 `dev-doc-master`（现状 DESIGN、薄主地图 + 按模块分片、去掉所有主文档头部 `Sub-DESIGNs` 强枚举、实测取证、`verify-docset.py` 12 项门禁含 `--check-sync`）、`space-master` 三级 `AGENTS.md` SOP 及最终目标态的 `.wopal/rules/coding-workflow.md`（及中文审核版）。
- 子提案 2（`.wopal/docs/evolutions/enhance-dev-proposal.md`）：交付业务 Proposal 技能 `dev-proposal`（含完整状态机、用户显式选择 `Delivery: direct | plan`、已实施提案再变更分流）、轻量静态校验器 `verify-proposals.py`、`df-proposal-review`（含实施方案质检不触发二次设计审批规则），以及本体现状子设计初版 `.wopal/docs/DESIGN-coding-workflow.md`。
- 子提案 3（`.wopal/docs/evolutions/enhance-implement-sync.md`）：交付独立于 Plan 状态机的 `df-implement`（按需调底座、覆盖整次交付基线 `--base` 的 `verify-docset.py --check-sync` 与 `verify-proposals.py`、并行写集防越界与必填 `DESIGN Sync` 块）及 `df-implement-review`（完整基线对抗式审查与影响分级严重度）。

**真实代码现状与去重依据**：
- 现有 `dev-flow/scripts/workflow.py:30-47` 定义 `planning → reviewing → executing → verifying → done`，其中 `VALID_TRANSITIONS`（第 44 行）已原生支持 `(STATUS_PLANNING, STATUS_EXECUTING)` 直通边。
- 现有 `dev-flow` 在“无 Proposal 时代”兼任了设计审批（`submit` + `approve --confirm`）与逐 Plan 验收（`verify --confirm`）；引入业务 Proposal 后，设计决定、授权范围与最终完成状态已唯一归属 Proposal，若继续保留二次设计审批与逐 Plan 重复验收，一份 Proposal 拆 3 个 Plan 会触发多轮无意义重复审批和重复验收。
- 现有 `dev-flow/SKILL.md:143,155-171,256` 与 `scripts/commands/integrate.py:140-268` 已具备**共享 Delivery**（`Delivery: <owner-plan>` + `--existing-worktree` + 统一 `integrate`）底座，且 `_validate_delivery_contract`（`integrate.py:258-259`）要求共享 Delivery 的全部成员处于 `verifying` 才能一起集成；同时 `references/active-plan-graph.md:62` 要求 Graph `edge from → to` 的上游先到 `done` 才能启动下游——**如果同一共享 Delivery 内给两个 Plan 画 `edge`，必然发生死锁**。
- 现有 `templates/plan.md:7-11` 与 `scripts/validation.py:93-110`（`check_product_phase`）仍强制检查成对的 `Product`/`Phase` 字段且无 `Source` 字段，需要在本轮为新来源链路移除旧前置，同时保留进行中旧 Plan 的最低必要兼容。

### Research Findings

- **各类事实的唯一归属（零职责重叠）**：
  - 设计决定、授权范围、`Delivery: direct | plan` 选择与设计全部实现的最终状态 → **Proposal**（无 Proposal 时为明确授权的 **Issue**）；
  - 可选详细 Plan/Task 编排、内部 Task 进度、跨 Delivery 依赖、Git 工作树与共享 Delivery 安全操作 → **可选 `dev-flow`**；
  - 代码、测试、现状 DESIGN/Proposal/AGENTS 同步与完整基线机械门禁 → **`df-implement`**（按需调底座）；
  - 独立实施评审 → **`df-implement-review`**；
  - 用户验证与正式 Git 集成 → **按 Delivery 统一验证一次并一次性放行集成**。
- **是否启用 Plan 由用户显式决定**：模型强弱是主观且快速变化的判断，技能中**绝不编写让 Agent 主观判定模型强弱的规则**；用户在批准 Proposal（`Delivery: direct | plan`）或派发 Issue 时显式选择是否走 Plan（Agent 仅基于跨项目、多任务并行隔离等客观事实提供简短建议）。
- **规划能力不削弱，流程管理做减法**：完整保留 `Behavior`、`Pre-read`、`Interface`、`Constraints`、`Verify`、`Done` 等详细 Plan/Task 编写能力（按任务需要填写详细程度，不抄 Proposal 设计长文，也不强行精简执行所需细节）；砍掉与 Proposal 重复的二次设计审批、逐 Plan 重复验收与旧 `Phase`/`GAPS`/目标态 `DESIGN` 前置，**不另造第三套新状态机**，复用既有 Git 工作树创建、回滚、脏树拦截、共享 Delivery 统一 `integrate` 与安全 `archive` 清理能力。
- **共享 Delivery 防死锁铁律**：同一 Git 仓库同一 Proposal 中存在先后顺序的工作，归入**同一个 Plan 中的顺序 Task**；彼此独立的多个 Plan 共享 1 个工作树和共享 `Delivery`，按 Delivery 统一验证一次并一次性 `integrate` 主分支，**严禁在同一共享 Delivery 成员之间画 Graph `edge`**；只有**跨不同 Delivery（如跨仓库或独立分批合入主分支）的真实先后依赖**才画 Graph `edge`。不同 Git 仓库不声称具备单次 Git 原子提交能力。
- **轻量历史兼容与未来通用性**：只对当前活跃目录中**进行中的旧 Plan** 保留最低必要续办兼容（兼容已有 `Product`/`Phase` 与 `Design Source`），已完成历史 Plan 不强制迁移，**不建设永久 Source 追溯、历史索引或复杂身份数据库**。新 Proposal 来源不强绑 GitHub Issue 或标准项目路径布局，为将来统一 `ontology-evolution` 留出干净通用接口（本轮不修改 `ontology-evolution` 状态机及其稀疏 Git 逻辑）。

**References**:
- `.wopal/docs/evolutions/archived/20261122-enhance-doc-contracts.md`
- `.wopal/docs/evolutions/{enhance-dev-proposal.md,enhance-implement-sync.md}`
- `.wopal/docs/{DESIGN.md,DESIGN-capabilities.md,DESIGN-coding-workflow.md}`（`DESIGN-coding-workflow.md` 由子提案 2 落地后存在）
- `.wopal/skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,AGENTS.md,AGENTS.zh-CN.md,templates/plan.md}`
- `.wopal/skills/dev-flow/references/{plan-guide.md,plan-guide.zh-CN.md,active-plan-graph.md,active-plan-graph.zh-CN.md,commands.md,issue-guide.md}`
- `.wopal/skills/dev-flow/scripts/{flow.sh,flow.py,workflow.py,validation.py,plan.py}`
- `.wopal/skills/dev-flow/scripts/commands/{plan.py,submit.py,approve.py,complete.py,verify.py,integrate.py,archive.py}`
- `.wopal/skills/dev-flow/tests/python/`
- `.wopal/skills/dev-doc-master/{SKILL.md,references/design-project-guide.md,scripts/verify-docset.py}`
- `.wopal/rules/{coding-workflow.md,testing.md}`
- `docs/products/wopal-space/proposals/development-governance-proposal.md`
- `docs/products/wopal-space/proposals/plan-orchestration-scheduler-proposal.md`（远期方向，不作为当前授权）
- `labs/ref-repos/deepseek-harness/docs/AGENTS.md`
- `labs/ref-repos/deepseek-harness/.agents/skills/dsh-doc-writing/references/structure-hierarchy.md`
- `labs/ref-repos/deepseek-harness/.agents/skills/dsh-code-review/SKILL.md`

### Key Decisions

- D-01：**定位与启用决策**：`dev-flow` 是位于 Proposal/Issue 与实施之间的**可选实施规划与任务组织层**。走 `direct`（跳过 `dev-flow`，由 `df-implement` 默认调用 `git-worktrees` 创建隔离工作树实施，不默认直改主分支）还是走 `plan`（启用 `dev-flow` 编排 Plan/Task 并由 `dev-flow` 统一管理隔离工作树与共享 Delivery，避免与 `df-implement` 重复建工作树），**由用户在批准 Proposal（`Delivery: direct | plan`）或派发 Issue 时显式决定**（Agent 仅基于跨项目、并行隔离等客观事实提简短建议，绝不凭主观判断模型强弱替用户决策）。
- D-02：**唯一主要来源与严格禁令（不强绑 GitHub Issue）**：新 Plan 必须有唯一主要 `Source`：`Issue #N` 或业务 Proposal 路径（规范路径为 `docs/products/<product>/proposals/proposed/<class>/yyyy-mm-dd-<slug>.md` 或 `projects/<project>/docs/proposals/proposed/<class>/yyyy-mm-dd-<slug>.md`，兼容前格式存量位置；实施期间稳定留在 `proposed/<class>/` 防断链）。**`implemented/`、`rejected/`、`archived/` 提案均严禁作为新 Plan 来源**（对已实施提案发起设计调整或优化必须先新建 `proposed/` 提案并获批）；DESIGN/PRD/无来源文本不能成为新增 Plan 的实施授权。Proposal 来源不强绑 GitHub Issue，为将来本体进化复用保留通用路径。
- D-03：**保留详细 Plan/Task 编写能力，不抄 Proposal 设计**：完整保留 `Behavior`、`Pre-read`、`Interface`、`Constraints`、`Verify`、`Done` 等已有写作能力；按实际任务需要填写详细程度（既不抄 Proposal 设计长文，也不削弱稳定执行所需的具体上下文）。单个 Plan 服务一个 Target Project，覆盖范围须与授权一致，严禁扩界。
- D-04：**消除重复设计审批（B-01 上半段，不另造新状态机）**：基于真实 CLI 调用链（`workflow.py:44` 已支持 `planning → executing` 直通）逐项审查 `submit` / `approve`：当 Plan 来源于已批准且 `Delivery: plan` 的 Proposal 且未超出批准范围时，Plan 在 `planning` 阶段完成机械校验（`plan check`）与必要实施方案质检（`df-proposal-review`，只核查任务衔接与不超范围）后，**免除向用户请求第二次设计审批**，直接复用既有工作树创建、共享 Delivery 初始化与失败回滚引擎安全进入 `executing`。仅当 Plan 超出 Proposal 批准范围、改变重要设计决定，或来源为无 Proposal 的独立需求/用户要求先过目时，才停等用户确认。
- D-05：**消除逐 Plan 重复验收与破除半成品合入（B-01 下半段）**：同一 Git 仓库内，同一 Proposal 拆出的多个彼此独立的 Plan 复用现有 `dev-flow` 共享 `Delivery`（`Delivery: <owner-plan>`）与 `--existing-worktree`，共用 1 个实施工作树和工作分支；全部成员完成内部 `complete` 门禁进入 `verifying` 后，**按 Delivery 只请用户统一验收 1 次**，经用户一次确认即执行统一 `integrate` 合入主分支，并完成成员 Plan 的 `done` 标记与安全 `archive` 清理（不另建新交付机制；跨不同 Git 仓库不声称具备单次 Git 原子提交能力）。单个 Plan 完成不自动把 Proposal 迁入 `implemented/`；全部批准范围交付完成时才由同交付收口迁入 `implemented/` 并完成对被替代老提案的互链/清理。
- D-06：**彻底破除共享 Delivery + Graph 死锁（B-02）**：
  - 同一 Delivery 内存在先后顺序的工作 → **写成同一个 Plan 中的顺序 Task**；
  - 同一共享 Delivery 内的多个独立 Plan → 仅以 `groups` 与共享 `Delivery` 组织，**严禁在同共享 Delivery 成员间画 Graph `edge`**；
  - 只有**跨不同 Delivery（如跨仓库或独立分批合入主分支）的真实先后依赖**，才在 `active-graph.json` 中画 `edge`（`from → to` 表示上游 Delivery 已完成 `done`）；Graph 不复制 Plan 状态，`groups` 不推导依赖，原 schema 保留，不建设 Scheduler。
- D-07：**并行写集防冲突与不另造文档状态机**：并行检查同时覆盖代码与 `DESIGN-*.md`（并行 Task 各自仅改所属 `DESIGN-<module>.md`，共享主 `DESIGN.md` 由主控在集成时收口）。Plan 只提供 Task 对应关系，**不在 `dev-flow` 内另造第二套文档同步或 Proposal 状态机**；主控验收交接时强制检查 `df-implement` 返回的非空 `DESIGN Sync` 证据块，并在整次交付收口时核验覆盖整次交付基线（`--base <Delivery Base Commit>`）的 `verify-docset.py --check-sync` 与 `verify-proposals.py` 结果。
- D-08：**同轮清理旧前置 + 轻量历史兼容**：本轮在 `dev-flow` 自身同一次改造中彻底移除新来源链路的旧 `Phase`/`GAPS`/目标态 `DESIGN` 前置（含解除 `validation.py:check_product_phase` 对新 Plan 的强制成对约束）；同步更新模块长期工程规范 `.wopal/skills/dev-flow/AGENTS.md` 与 `AGENTS.zh-CN.md`（将 `State Machine` / `plan check` 中已退场的强制 `Product`/`Phase` 配对规则替换为新 `Source` 契约、去重后的 `planning → executing` 流程与进行中旧 Plan 最低兼容）；仅对当前活跃目录中**进行中的旧 Plan** 保留最低必要续办兼容（兼容旧 `Product`/`Phase` 与 `Design Source`），已完成历史 Plan 不强制迁移，**不建设永久 Source 追溯、历史索引或复杂身份数据库**。
- D-09：**规则核对、触发收敛与本体现状设计同交付收口**：依 `skill-creator` 精炼 `dev-flow` 中英 `description` 并完成 10+10 触发验证；核对 `.wopal/rules/coding-workflow.md`（及中文审核版）保持最终目标态一致；同交付收口更新 `.wopal/docs/DESIGN-coding-workflow.md`（完整落地本轮全部 4 个子提案的现状架构、状态机与衔接契约）及 `.wopal/docs/DESIGN-capabilities.md`（同步更新 `Skill System` 中过时的 `dev-flow` 描述），通过 `verify-docset.py` 校验。本提案 Tasks 1–6 可在子提案 2 合入后与子提案 3 并行编码与测试，但 **Task 7 的最终共享文档收口（`.wopal/docs/DESIGN-coding-workflow.md`、`.wopal/docs/DESIGN-capabilities.md` 及最终 `.wopal/rules/coding-workflow.md` 核对）与最终合入必须在子提案 3 合入 `space/<name>` 并对齐最新基线后执行**，避免共享文档冲突并保证文档如实记录全部 4 份已落地子提案的现状。

### Key Interfaces

- Authoring 产物：`Source`（`Issue #N` 或 `proposed/<class>/...` Proposal 路径）、`Target Project`、`Delivery`（同仓库多 Plan 共享同一 `<owner-plan>`）、按需详细的 Task（`Behavior`/`Pre-read`/`Interface`/`Constraints`/`Verify`/`Done`）、并行写集边界与主控 `DESIGN Sync` 交接检查；只链接 Proposal 设计决定，不复制设计文本。
- `flow.sh plan new`：保留 `ISSUE_NUMBER --project PROJECT` 路线；新增 Proposal 来源参数（不强绑 GitHub Issue，具体 CLI flag 由 Task 1/4 对真实脚本取证定案），拒绝无来源新 Plan（不得用 `Issue: N/A` 伪造授权）。
- `flow.sh plan check` / 启动执行入口（基于 Task 1 对 `submit`/`approve` 的实证裁决）：
  - 对新 Proposal 来源复用/对齐 `dev-proposal` 规则校验 `proposed/<class>/`、`Status: approved`、`Delivery: plan` 与目标项目，拒绝无来源、未批准、`Delivery: direct`、`implemented/`、`rejected/`、`archived/` 或越界，失败零半写入；
  - 对已批准且未超范围的 Proposal 来源，支持经 `planning → executing` 直接安全初始化工作树与共享 Delivery 元信息，**免除重复向用户要设计批准**（保留完整脏树检查、worktree 创建与失败回滚）；对无 Proposal 授权或超范围场景保留用户显式确认门禁；
  - 对新来源链路不再强求 `Product`/`Phase` 成对字段或前置目标态 DESIGN；对进行中旧 Plan 保留最低兼容。
- `flow.sh complete` / 统一 `integrate` / `verify` / `archive`：保留既有 3 种 worktree 模式（`normal`/`--no-worktree`/`--existing-worktree`）、`Commit Subject`、PR/本地集成与安全清理；共享 Delivery 成员全部进入 `verifying` 后按 Delivery 统一验证一次，经用户一次确认完成统一 `integrate` 及成员收尾/归档；单 Plan 完成不自动把 Proposal 迁入 `implemented/`。
- Active Plan Graph（`.wopal-space/plans/active-graph.json`）：保持 `nodes`/`edges`/`groups` 原 schema，新增规则校验/SOP 明确禁止同共享 Delivery 成员间建立 `edge`，`edge` 仅用于跨不同 Delivery 的真实依赖。

## In Scope

- **`dev-flow`（修改技能 — 明确优化项）**：
  - 确立可选实施规划与任务组织定位，明确 `direct` vs `plan` 由用户显式选择（不让 Agent 猜模型强弱）；
  - 保留并打磨详细 Plan/Task 编写规范、多 Plan 范围覆盖检查、代码与 `DESIGN-*.md` 并行写集防冲突 SOP、主控 `DESIGN Sync` + 覆盖整次交付 `--base` 门禁验收；
  - 落地不强绑 GitHub Issue 的 Proposal 来源参数与授权门禁（拒绝无来源、未批准、`Delivery: direct`、`implemented/`、`rejected/`、`archived/`）；
  - 落实同仓库多 Plan 复用既有共享 `Delivery` 与 `--existing-worktree` 统一验证并一次性集成主分支；落实“同 Delivery 先后工作归入同 Plan 顺序 Task、跨 Delivery 才画 Graph `edge`”破除死锁；
  - 同轮移除新来源链路的旧 `Phase`/`GAPS`/目标态 `DESIGN` 前置（含解除 `validation.py:check_product_phase` 强制约束），同步更新 `.wopal/skills/dev-flow/{AGENTS.md,AGENTS.zh-CN.md}` 长期工程规范以与新 `Source` 契约及进行中旧 Plan 最低兼容一致；
  - 核对 `.wopal/rules/coding-workflow.md`（最终目标态）与 `dev-flow` 中英 `description` 10+10 触发收敛；同交付收口本体现状设计 `.wopal/docs/DESIGN-coding-workflow.md` 与 `.wopal/docs/DESIGN-capabilities.md`（最终共享文档收口须在子提案 3 合入最新基线后执行）。
- **`dev-flow`（修改技能 — 明确精简项）**：
  - **砍掉重复审批**：对已批准且不超范围的 Proposal 来源，跳过与 Proposal 重复的第二次设计审批（复用 `planning → executing` 与既有 Git 工作树安全初始化）；
  - **砍掉逐 Plan 重复用户验收**：同一共享 Delivery 的多个 Plan 合并为按 Delivery 统一找用户验证一次并一次性集成收尾；
  - **不另造新状态机 / 不另造文档状态机**：不发明第三套 Plan 状态机，不在 Plan 中维护另一套 DESIGN 或 Proposal 状态；
  - **不做过度历史兼容工程**：已完成历史 Plan 不强制迁移，不建永久 Source 追溯、历史索引或复杂身份数据库；
  - **不造调度器**：不建设 Scheduler、cron、任务队列或新 Graph schema。

## Out of Scope

- 不另造全新替代状态的第三套 Plan 状态机，不重写已验证可靠的底层 Git worktree/rollback/PR/squash 引擎。
- 不建设 Scheduler、cron、任务执行数据库或第二张 Plan Graph，不变更 Graph schema。
- 不修改 `ontology-evolution` 状态机与稀疏 Git 逻辑、不修改 `wopal-cli`、不修改真实业务代码/业务 DESIGN、现行业务 Plan 或实际 `active-graph.json`。
- 不修改 `dev-doc-master`、`dev-proposal`、`df-implement`、`df-implement-review` 的核心规范（分别归属子提案 1、2、3）。

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| Plan/Task SOP | `.wopal/skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,AGENTS.md,AGENTS.zh-CN.md,templates/plan.md,references/plan-guide.md,references/plan-guide.zh-CN.md,references/commands.md}` | modify | 可选编排定位、去重审批与按 Delivery 统一验收 SOP、详细 Plan/Task 规范、并行写集防冲突，以及同步模块 `AGENTS.md` 长期工程规范（新 `Source` 契约与旧 Plan 最低兼容） |
| Graph 规范 | `.wopal/skills/dev-flow/references/{active-plan-graph.md,active-plan-graph.zh-CN.md}` | modify | 跨 Delivery 依赖边界与严禁同共享 Delivery 成员画 `edge` 防死锁规则 |
| CLI 精简与来源门禁 | `.wopal/skills/dev-flow/scripts/{flow.sh,flow.py,plan.py,validation.py,workflow.py}` 及 `scripts/commands/{plan,submit,approve,complete,verify,integrate,archive}.py` | modify | Proposal/Issue `Source`、不强绑 Issue、已批准 Proposal 去重开工、按 Delivery 统一验证收口、旧 `Phase` 前置退场与进行中旧 Plan 最低兼容 |
| 空间调用规则 | `.wopal/rules/coding-workflow.md`, `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md` | modify (verify / align as needed) | 核对并保持最终目标态与落地 `dev-flow` 契约完全一致 |
| 本体现状设计 | `.wopal/docs/DESIGN-coding-workflow.md`, `.wopal/docs/DESIGN-capabilities.md` | modify | 同交付收口全套研发治理技能现状设计、完整状态机与 `Skill System` 准确现状 |
| 自动化测试 | `.wopal/skills/dev-flow/tests/python/{unit,integration}/` 与隔离 Git/Graph fixtures | create / modify | 去重审批、防死锁、多来源授权、共享 Delivery 统一集成与历史兼容回归 |

## Assembly Intent

| Ref | Scope | 理由 |
|---|---|---|

## Acceptance Criteria

### Agent Verification

1. [ ] `direct` 与 `plan` 路径由用户显式选择（技能中不含主观评判模型强弱逻辑）；已批准 Proposal 或明确 Issue 可走 `direct` 跳过 `dev-flow`（由 `df-implement` 默认调用 `git-worktrees` 创建隔离工作树实施，不默认直改主分支），或由 `dev-flow` 拆出覆盖批准范围、无遗漏/无扩界的 1..N 个 Plan（每个 Plan 归属唯一 Target Project，并由 `dev-flow` 统一管理工作树），且保留详细 Plan/Task 写作能力（按需填写，不抄 Proposal 设计长文）。
2. [ ] Task 按可独立验收的行为拆分，完整保留 `Behavior`、`Pre-read`、`Interface`、`Constraints`、`Verify`、`Done` 等字段能力；同一 Delivery 内存在先后顺序的工作归入同一 Plan 的顺序 Task；无意义碎片化、巨型任务与越权扩范围被明确指出。
3. [ ] 并行检查同时覆盖代码与 `DESIGN-*.md` 共享写集、接口契约、隔离环境与提交所有权（并行分支只写各自模块 `DESIGN-<module>.md`，共享主 `DESIGN.md` 由主控集成收口）；Plan 不另造文档同步状态机，主控拒收缺 `DESIGN Sync` 的汇报并在交付收口时核验覆盖整次交付 `--base` 的 `verify-docset.py --check-sync`（及必要时 `verify-proposals.py`）。
4. [ ] Graph 仅记录跨不同 Delivery 的真实先后依赖；合法 DAG 与分组通过，**同一共享 Delivery 成员之间画 `edge`**（防死锁）、环、自边、重边、缺节点引用、把 `groups` 当 `edges` 或复制状态的负例均被明确拦截；原 Graph schema 与真实 `active-graph.json` 不变。
5. [ ] 新 Issue 与获批 Proposal（`proposals/proposed/<class>/yyyy-mm-dd-<slug>.md` 且 `Status: approved`、`Delivery: plan`，兼容前格式存量位置且不强绑 GitHub Issue）均可由真实 CLI 创建与校验；无来源、错误项目、未批准、`Delivery: direct`、`implemented/`、`rejected/`、`archived/` 或越界来源均被拒绝且零半写入；新来源链路在本轮同步移除旧 `Phase`/`GAPS`/目标态 `DESIGN` 前置（含 `validation.py:check_product_phase` 对新 Plan 不再阻塞）。
6. [ ] **消除重复设计审批**：当 Plan 来源于已批准且 `Delivery: plan` 的 Proposal 且未超出批准范围时，通过内部质检后可通过 `planning → executing` 安全初始化工作树与共享 Delivery 元信息直接开工，**无需用户再次批准设计**；当 Plan 超出批准范围、改动设计决定或无 Proposal 授权时，CLI/流程仍停等用户确认；未另造第三套新状态机。
7. [ ] **消除逐 Plan 重复验收与防半成品合主分支**：同一 Git 仓库同一 Proposal 拆出的多个彼此独立 Plan 复用既有共享 `Delivery` 与 `--existing-worktree` 共用工作树；全部成员到 `verifying` 后按 Delivery 统一验证一次，经用户一次确认完成一次性 `integrate` 主分支及成员收尾/安全 `archive`（不同 Git 仓库不声称单次 Git 原子提交）；单个 Plan 完成不自动把 Proposal 迁入 `implemented/`。
8. [ ] 当前进行中的旧无来源 Plan（含旧 `Product`/`Phase` 与 `Design Source`）保留最低必要续办兼容，不建设复杂历史身份库；现有 `normal`/`--no-worktree`/`--existing-worktree`、commit subject、Git/PR 集成与安全清理在回归测试中不退化；真实业务文件无改写。
9. [ ] 端到端集成验证覆盖 `direct` 与详细 Plan 双路径、无重复审批、共享 Delivery 无死锁统一集成、同交付收口后的本体现状设计 `.wopal/docs/DESIGN-coding-workflow.md` 与 `.wopal/docs/DESIGN-capabilities.md`（均通过 `verify-docset.py` 校验）、最终目标态 `.wopal/rules/coding-workflow.md`（中英一致），以及 `.wopal/skills/dev-flow/{AGENTS.md,AGENTS.zh-CN.md}` 已同步为新 `Source` 契约、去重流程与进行中旧 Plan 最低兼容（不再把旧 `Product`/`Phase` 配对写成新 Plan 强制规则，中英一致）。
10. [ ] `dev-flow` 中英 `description` 简洁准确覆盖可选实施规划、Plan/Task/Graph 编排与工作树/共享 Delivery 生命周期，排除纯业务 Proposal 写作、直接编码实施、独立方案/代码评审及 DESIGN 写作；完成至少 10 个应触发 + 10 个不应触发的近邻请求验证，记录改前/改后与验证限制，中英语义一致。

### Source Principles → Tasks → Verification

| 已核实的来源 | 在 `dev-flow` 中采取的具体实践 | Task 与 AC |
|---|---|---|
| DSH `docs/AGENTS.md`、`dsh-doc-writing/references/structure-hierarchy.md` | 一类事实唯一归属（授权归 Proposal、编排归可选 Plan、现状归 DESIGN）；已实施提案不可作为新 Plan 来源，须新建 `proposed/` 提案 | Tasks 1–2、4–5；AC#1、2、5 |
| DSH `dsh-code-review/SKILL.md` | 依据真实 diff/调用链和完整基线检查收口交付，代码与现状设计同交付一致 | Tasks 6–7；AC#3、9 |
| WopalSpace `dev-flow/references/plan-guide.md`、`templates/plan.md` | 保留详细 Task 编写能力与主控复验/提交所有权，消除与 Proposal 重复的设计审批与逐 Plan 验收 | Tasks 1–2、5–6；AC#1、2、6、7 |
| WopalSpace `dev-flow/references/active-plan-graph.md` & `integrate.py` | 共享 Delivery 成员严禁互相画 Graph `edge`（同 Delivery 先后工作进同 Plan 顺序 Task）；`edge` 仅用于跨不同 Delivery 依赖 | Tasks 1、3、6；AC#4、7 |
| WopalSpace `dev-flow/scripts/{flow,workflow,validation}.py`、`commands/` | 复用既有 `planning → executing` 与工作树/回滚/共享 Delivery 安全底座做精准减法，不另造新状态机 | Tasks 1、4–7；AC#5、6、7、8 |

**DSH 没有 Plan Graph、Agent 并行、共享 Delivery 与 Git worktree 编排实现**；后者是 WopalSpace 的自主设计，不能把 DSH 文档当作实施授权或代替测试结果。

### User Validation

#### Scenario 1: 验收可选编排、零重复审批与共享 Delivery 无死锁执行
- Goal: 用户一次性验证“批 Proposal 后直接开工不重复审批 → 详细 Plan/Task 编排 → 同仓库多 Plan 共享工作树统一验收集成 → 本体现状设计同步落地”整套闭环。
- Environment: 本提案隔离工作树与虚构 Issue、已批准 Proposal、已 `implemented/` 老提案、同仓多 Plan 与跨仓多 Plan 隔离 Git/Graph fixtures。
- Precondition: 全部 7 个 Task 验证并独立评审通过，进入 validating（并与子提案 1–3 一并开展全链路整体验收）。
- Launch command: `wopal space evo switch enhance-dev-flow-proposal`（切换后**重启 ellamaka** 以加载更新后的技能、脚本与现状设计）
- User Actions:
  1. 查看同仓库同一 Proposal 的顺序任务（单 Plan 顺序 Task）与多独立 Plan（共享 Delivery + 无内部 Graph 边 + 统一验收一次）样例。
  2. 验证已批准 Proposal 启动 Plan 不触发二次设计审批、超范围时触发停等确认，以及未批准/`implemented/`/`archived/` Proposal 被 CLI 拒绝。
  3. 审阅最终收口的本体现状设计 `.wopal/docs/DESIGN-coding-workflow.md`，确认整套技能架构、状态机与衔接契约清晰可读且与真实实现一致。
- Pass criteria: 全程最多 2 次用户拍板（批 Proposal + 统一验收集成）、零死锁、详细 Plan 编写能力完整、旧 Git 安全能力不退化、本体现状设计准确可读。
- Failure feedback: 指出重复审批点、死锁路径、命令错误或现状设计失真位置。
- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 取证现有 `dev-flow` CLI 调用链，定案流程去重边界与状态/命令精简清单

**Verification Intent**: AC#4、AC#5、AC#6、AC#7、AC#8
**Behavior**: 基于真实源码定案：① 现有 `submit`/`approve`/`complete`/`verify`/`integrate`/`archive` 中哪些 Git 安全与工程操作保留、哪些重复人工审批与逐 Plan 验收步骤对已批准 Proposal 免除（复用 `workflow.py:44` `planning → executing` 直通边与既有共享 Delivery，不另造新状态机）；② `validation.py:check_product_phase` 与 `templates/plan.md` 的新 `Source` 字段切换方案与进行中旧 Plan 最低兼容判定（不建复杂历史身份库）；③ 共享 Delivery 与 Graph 的防死锁契约边界。
**Pre-read**: `.wopal/skills/dev-flow/{SKILL.md,templates/plan.md,AGENTS.md}`、`references/{plan-guide.md,active-plan-graph.md,commands.md}`、`scripts/{flow.py,workflow.py,validation.py,plan.py}`、`scripts/commands/{plan,submit,approve,complete,verify,integrate,archive}.py` 及现有 `tests/python/`。
**Design**: 产出可核对的“命令/状态调用与去重映射表”和最小改动方案，明确后续 Task 2–7 各自边界；确保全部底层 Git 安全护栏（脏树检查、worktree 创建与回滚、squash integrate、安全 archive）完整保留。
**TDD**: false — 源码调用链取证与去重架构定案。
**Changes**: 确认并记录到 `dev-flow` 内部参考/设计边界，不提前破坏现有测试。
**Verify**: 运行现有 `dev-flow` `pytest` 基线确认当前全部通过；对照源码逐条核验去重清单无遗漏消费者。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: 重构 Plan/Task Authoring SOP（用户显式选路径、保留详细 Task 与并行写集防冲突）

**Verification Intent**: AC#1、AC#2、AC#3
**Behavior**: 清晰写明 `direct` vs `plan` 由用户在批准 Proposal 或派发 Issue 时显式决定（绝不含主观判断模型强弱逻辑）；完整保留详细 Plan/Task 编写字段（`Behavior`/`Pre-read`/`Interface`/`Constraints`/`Verify`/`Done`），按任务需要填写而不抄 Proposal 设计长文；同一 Delivery 内有先后顺序的工作写进同一 Plan 顺序 Task；并行检查同时覆盖代码与 `DESIGN-*.md` 写集（并行分支只改所属模块子 DESIGN，主 `DESIGN.md` 由主控收口）；Plan 不另造文档同步状态机，主控交接验收要求非空 `DESIGN Sync` 证据块并核验覆盖整次交付 `--base` 的 `verify-docset.py --check-sync`。
**Pre-read**: Task 1、已交付的 `dev-doc-master`（`references/design-project-guide.md`）、`dev-proposal`、`df-implement` handoff 规范、现有 `dev-flow/references/plan-guide*.md` 与 `templates/plan.md`。
**Design**: 更新 `dev-flow/references/plan-guide.md`、`plan-guide.zh-CN.md` 与 `templates/plan.md`（新增 `Source` 字段、允许新 Plan 省略旧 `Phase`），用正反例明确合理拆分、详细 Task 写法、安全/危险并行与缺 `DESIGN Sync` 拒收。
**TDD**: false — Authoring SOP、模板与正反隔离演练案例验证。
**Changes**: `.wopal/skills/dev-flow/{templates/plan.md,references/plan-guide.md,references/plan-guide.zh-CN.md}`。
**Verify**: 用同仓顺序工作（单 Plan 顺序 Task）、同仓多独立 Plan（共享 Delivery）、跨仓多 Plan、危险并行（撞共享主 `DESIGN.md`）与缺 `DESIGN Sync` 拒收案例逐一演练核查，确保旧模板仍兼容现有 CLI。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: 重构 Active Plan Graph 规则并根除共享 Delivery 死锁（B-02）

**Verification Intent**: AC#4
**Behavior**: 明确 `active-graph.json` 仅表达**跨不同 Delivery（如跨仓库或独立分批合入主分支）的真实先后依赖**；**严禁在同一共享 Delivery 成员之间画 `edge`**（同 Delivery 内先后工作归入同一 Plan 的顺序 Task）；合法 DAG 与 `groups` 分组通过，共享 Delivery 内部画边、环、自边、重边、缺节点、把 `groups` 当 `edges` 或复制状态均被检测拦截；保持原 Graph schema，不建设 Scheduler。
**Pre-read**: Tasks 1–2、`.wopal/skills/dev-flow/references/active-plan-graph*.md`、`scripts/commands/integrate.py`、现有 Graph fixtures。
**Design**: 同步更新中英版 `active-plan-graph*.md`（同时清除第 13、20 行已退场的 `Phase document` / `Phase Related Plans` 残留引用），并在测试中提供覆盖共享 Delivery 禁边与 DAG 非法反例的确定性校验用例。
**TDD**: true — 编写隔离 Graph fixtures 自动化测试覆盖合法跨 Delivery DAG、共享 Delivery 成员互画 `edge` 死锁反例、环、自边、重边、缺节点与非法分组（RED → GREEN）。
**Changes**: `.wopal/skills/dev-flow/references/{active-plan-graph.md,active-plan-graph.zh-CN.md}` 及隔离 Graph 校验测试与 fixtures。
**Verify**: 运行 Graph 正反自动化测试全部通过；确认真实 `.wopal-space/plans/active-graph.json` 未被改动。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: CLI 落地 `Source` 契约、解除旧 `Phase` 前置与进行中旧 Plan 最低兼容

**Verification Intent**: AC#5、AC#8
**Behavior**: `flow.sh plan new` 保留 Issue 路线并新增不强绑 GitHub Issue 的 Proposal 来源参数；新无来源 Plan（含用 `Issue: N/A` 伪造授权）被明确拒绝且零半写入；新来源 Plan 不再受旧 `Product`/`Phase` 成对检查（`validation.py:check_product_phase`）或目标态 DESIGN 前置阻塞；当前活跃目录中**进行中的旧无来源 Plan**（含旧 `Product`/`Phase`）保留最低必要续办兼容，不建设复杂历史身份数据库。
**Pre-read**: Task 1–3、`scripts/{flow.sh,flow.py,plan.py,validation.py}`、`scripts/commands/plan.py`、`tests/python/`。
**Design**: 在 `plan new` 与 `validation.py` 落地 `Source` 字段读写与校验，解除新来源链路的 `check_product_phase` 强制要求（仅对含旧 `Product`/`Phase` 的进行中历史 Plan 保持兼容读取），保证所有拒绝路径在首次写入前失败。
**TDD**: true — 覆盖合法 Issue 创建、合法 Proposal 创建（无 GitHub Issue）、新无来源拒绝、新 Plan 省略 `Product`/`Phase` 放行、以及进行中旧 Plan 续办兼容的 RED → GREEN 自动化测试。
**Changes**: `.wopal/skills/dev-flow/scripts/{flow.sh,flow.py,plan.py,validation.py}`、`scripts/commands/plan.py` 与 `tests/python/`。
**Verify**: 在隔离 Git fixtures 上跑通全部新增与原有 unit/integration 测试，确认失败无副作用。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 5: CLI 落地 Proposal 授权门禁与已批准 Proposal 去重开工流程（B-01 上半段）

**Verification Intent**: AC#5、AC#6
**Behavior**: 对 `Source: Proposal` 复用/对齐 `dev-proposal` 规则校验其位于 `proposed/<class>/`（或前格式存量位置）、`Status: approved` 且 `Delivery: plan`；未批准、`Delivery: direct`、`implemented/`、`rejected/`、`archived/`、错误目标项目或越界均被拒绝且零半写入。**消除二次设计审批**：对于来源为已批准 Proposal 且未超出批准范围的 Plan，完成内部质检后可通过 `planning → executing` 复用现有 worktree 创建、共享 Delivery 初始化与回滚安全机制直接开工，不再要求用户重复批准设计；仅当超范围或无 Proposal 授权（如独立 Issue 或用户显式要求）时仍停等用户确认；不另造新状态机。
**Pre-read**: Task 1、Task 4、`dev-proposal/{SKILL.md,scripts/verify-proposals.py}`、`scripts/{workflow.py,commands/submit.py,commands/approve.py}`。
**Design**: 依据 Task 1 定案精简 `submit`/`approve` 对已批准 Proposal 的重复人工审批门槛，保留全部 Git 脏树拦截、worktree/branch 创建、共享 Delivery 字段校验与失败回滚保护，确保无任何静默绕过授权路径。
**TDD**: true — 覆盖未批准/`Delivery: direct`/`implemented/`/`rejected/`/`archived/`/越界拒绝、已批准 Proposal 免二次审批安全建工作树开工、超范围拦截、以及失败零半写入的 RED → GREEN 自动化测试。
**Changes**: `.wopal/skills/dev-flow/scripts/{workflow.py,validation.py,commands/submit.py,commands/approve.py}` 与 `tests/python/`。
**Verify**: 在隔离 Git fixtures 运行正负 CLI 测试，核实免二次审批开工路径安全建出工作树且全部拒绝路径无半写入残留。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 6: CLI 与 SOP 落地同仓库共享 Delivery 统一验证/集成与多 Plan 衔接（B-01 下半段 + B-02）

**Verification Intent**: AC#1、AC#4、AC#7
**Behavior**: 同一 Git 仓库同一 Proposal 拆出的多个彼此独立 Plan 复用既有共享 `Delivery` 与 `--existing-worktree` 共用工作树与工作分支；各自完成 `complete` 进入 `verifying` 后，**按 Delivery 只请用户统一验收 1 次**，用户一次确认即可完成一次性 `integrate` 合入主分支及所有成员 Plan 的 `done` 标记与安全 `archive` 清理（不再逐 Plan 分别找用户验收）；不同 Git 仓库不声称单次 Git 原子提交；任何单个 Plan 完成不自动把 Proposal 迁入 `implemented/`（也不提前改写被替代老提案）。
**Pre-read**: Tasks 1–5、`scripts/commands/{complete,verify,integrate,archive}.py`、`dev-flow/SKILL.md` 共享 Delivery 章节。
**Design**: 复用现有 `integrate.py` 的共享 Delivery 发现与成员校验逻辑，打通“按 Delivery 统一验证一次 → 统一集成 → 成员统一收尾与最后安全清理工作树”，同时校验共享 Delivery 成员不在 Graph 中互画死锁边，不另建新交付机制。
**TDD**: true — 隔离模拟同仓库 2 个独立 Plan 共享 Delivery 统一验收与一次性集成、单成员未就绪拦截、跨两仓库独立 Delivery 衔接、以及部分 Plan 完成不自动改 Proposal `implemented` 的 RED → GREEN 测试。
**Changes**: `.wopal/skills/dev-flow/scripts/commands/{complete,verify,integrate,archive}.py`（最小必要调整）、`references/commands.md` 与 `tests/python/`。
**Verify**: 运行隔离多 Plan 集成测试，验证主分支不会出现半成品中间提交、工作树安全清理且无成员状态错位。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 7: 全量回归、最终态规则核对、`dev-flow` 触发收敛与本体现状设计同交付收口

**Verification Intent**: AC#1–10
**Behavior**: 现有 `normal`/`--no-worktree`/`--existing-worktree`、commit subject、PR/本地集成、安全清理与进行中旧 Plan 兼容全部不退化；`direct` 与详细 Plan 双路径端到端满足测试、覆盖整次交付 `--base` 的 `verify-docset.py --check-sync`、`verify-proposals.py` 与独立评审；核对并同步 `.wopal/skills/dev-flow/{AGENTS.md,AGENTS.zh-CN.md}`（将 `State Machine` / `plan check` 长期规范更新为新 `Source` 契约、去重后的 `planning → executing` 流程与进行中旧 Plan 最低兼容，移除对新 Plan 的强制 `Product`/`Phase` 配对条款，中英一致）；`.wopal/rules/coding-workflow.md`（及中文审核版）保持最终目标态一致；**本 Task 的最终共享文档收口须在子提案 3（`enhance-implement-sync`）实际合入 `space/<name>` 并对齐最新基线后执行**，同交付收口本体现状设计文档 `.wopal/docs/DESIGN-coding-workflow.md`（完整记录本轮已落地的全部 4 个子提案现状、完整状态机与跨技能衔接契约）及 `.wopal/docs/DESIGN-capabilities.md`（同步更新 `Skill System` 中过时的 `dev-flow` 描述）；`dev-flow` 中英 `description` 完成 10+10 近邻触发收敛。
**Pre-read**: Tasks 1–6、子提案 3 合入 `space/<name>` 后的最新基线文档、`skill-creator` 技能、`.wopal/skills/dev-flow/{AGENTS.md,AGENTS.zh-CN.md}`、`.wopal/rules/coding-workflow.md`（及中文审核版）、`.wopal/docs/{DESIGN.md,DESIGN-capabilities.md,DESIGN-coding-workflow.md}`、`dev-doc-master/scripts/verify-docset.py`。
**Design**: 收口 `dev-flow/{SKILL.md,SKILL.zh-CN.md,AGENTS.md,AGENTS.zh-CN.md}` 写清最终状态流转与可选编排职责（清除旧 `Phase`/`GAPS`/目标态 `DESIGN` 前置残留，同步清理 `AGENTS*.md` 中过时的 `Product`/`Phase` 强制配对表述），对齐子提案 3 合入后的最新基线并核对 `coding-workflow.md` 中英最终目标态，按 `dev-doc-master` 现状设计规范更新本体 `.wopal/docs/DESIGN-coding-workflow.md` 与 `DESIGN-capabilities.md` 并运行 `verify-docset.py` 校验通过。
**TDD**: true — 新来源、去重审批、共享 Delivery 统一集成与旧交付模式的端到端回归测试。
**Changes**: `.wopal/skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,AGENTS.md,AGENTS.zh-CN.md}`、最小必要脚本/测试收口、`tests/python/`、`.wopal/docs/{DESIGN-coding-workflow.md,DESIGN-capabilities.md}`，以及按需微调 `.wopal/rules/coding-workflow.md` 与 `.wopal/docs/LANG/zh-CN/rules/coding-workflow.md`。
**Verify**: 运行 `dev-flow` 全量 `pytest` 与真实 `flow.sh` 模拟命令全部通过；运行 `python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md` 核验本体设计文档（确认已完整覆盖全部 4 份已落地子提案、无未落地虚构内容且链接完整）；核对 `.wopal/skills/dev-flow/{AGENTS.md,AGENTS.zh-CN.md}` 与 `.wopal/rules/coding-workflow.md`（及中文版）中英一致且均无对新 Plan 强制 `Product`/`Phase` 配对的过时条款；依 `skill-creator` 完成 `dev-flow` 10+10 近邻触发测试（与 `dev-proposal`、`df-implement`、`df-proposal-review`、`df-implement-review`、`dev-doc-master` 交叉对照），记录改前/改后与验证限制。
**Done**:
Task output: (实施后填写)
Files touched: (实施后填写)
- [ ] The implementation agent has completed all development and verification steps above.

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|---|---|---|---|---|
| 1 | Task 1 | Wopal 主控 | enhance-doc-contracts、enhance-dev-proposal | 源码调用链取证与去重边界定案 |
| 2 | Task 2 | Wopal 主控 | Task 1 | 可选规划 SOP、详细 Plan/Task 规范与并行防冲突 |
| 3 | Task 3 | Wopal 主控 | Task 2 | 跨 Delivery Graph 规则与共享 Delivery 防死锁 |
| 4 | Task 4 | Wopal 主控 | Task 1、3 | 不强绑 Issue 的 `Source` 契约、解除旧 `Phase` 前置与最低历史兼容 |
| 5 | Task 5 | Wopal 主控 | Task 4 | Proposal 授权门禁与已批准 Proposal 去重开工流程 |
| 6 | Task 6 | Wopal 主控 | Task 3、5 | 同仓库共享 Delivery 统一验证/集成与多 Plan 衔接 |
| 7 | Task 7 | Wopal 主控 | Tasks 1–6、`enhance-implement-sync` 已合入最新基线 | 全量回归、模块 `AGENTS*.md`/最终态规则核对、触发收敛与本体现状设计同交付收口 |

**同一份提案、七个高内聚 Task、一次用户批准与最终验收。** 由 Wopal 主控逐 Task 亲自实施、实际验证并回填提交，不委派 Fae、不调用 Rook；全部 Task 实施完成后由用户安排其他 Agent 加载 `df-implement-review` 执行独立只读评审。用户仍独立批准、验证与授权正式集成。

## Delivery

此子提案保持 `Stage: draft`，不继承产品总提案的实施授权，获批后依本体进化命令以 `isolated` 隔离模式独立交付：Tasks 1–6 可在子提案 2 合入后与子提案 3 安全并行开发（各自写集物理不重叠），**但本提案 Task 7 的最终共享文档收口与最终合入必须在子提案 3（`enhance-implement-sync`）实际合入 `space/<name>` 并对齐最新基线后执行**。**本提案在同一轮内完成 `dev-flow` 的可选编排 SOP、去重审批与按 Delivery 统一验收、Graph 防死锁、真实 CLI 改造、旧前置退出、`AGENTS*.md` 同步及本体现状设计文档收口**；不另造第三套状态机，不建设自动 Scheduler，本轮不修改 `ontology-evolution`。
