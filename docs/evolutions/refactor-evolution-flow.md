# refactor-evolution-flow

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: Medium — 纯文档改造，5 个 Task 分布在 3 个文件 + 1 处 AGENTS 同步；`SKILL.md` 属加载路径，改动需重启观察，故不按 Low 计。
- **Confidence**: High — 全部摩擦点为本轮 isolated 实施实测，机制侧行为已按代码逐条实证（见证据表）；目标流程已由用户定稿，无待决设计分歧。

## Goal

把 isolated 实施暴露的流程摩擦与用户定稿的流程设计固化进技能常驻文档：补齐**任务记录协议**、**角色×命令矩阵**、**并行实施规范**，并修正 `--paths` 路径基准与记录流程表述，使「实施不提交 → 主控趁会话存活及时验证 → 有问题同 task 返工 → 通过后主控一次性提交（代码+记录，落在工作分支）→ `integrate` 一次 squash」成为可照做的明文流程，而不是每轮从 git 历史考古的隐性惯例。机制侧支撑（去覆盖式 sync、阶段即时镜像、单提交承载记录）由 wopal-cli Issue #240 承接，本提案只落文档层。

## Technical Context

### Architecture Context

**现状：技能只描述「有哪些命令」，不描述「谁在什么时候跑哪个命令、记录由谁写」。**

- `SKILL.md` 的 Roles 表给出各角色职责与禁区，但不含命令归属；`Landing an evolution` 的 runbook 是无主语命令流，其中实现提交一步仅注 `# sparse-safe, per task`（`SKILL.md:218`），未指明执行者。
- 记录协议在技能内**完全缺失**：`SKILL.md` 与 `references/commands.md` 对 Done / 回填 / 记录三组关键词零命中。实际做法只存在于空间侧 git 历史——本轮三次裸提交 `45f86b6` / `6edf893` / `4c15291`（`docs(evolutions): record Task N done for refactor-plugin-config-consumption`），需考古才能复原。
- 并行实施规范只活在单个提案正文里（`refactor-plugin-config-consumption.md:230-233`），因此每轮委派都要手写重抄一遍。
- 提案模板给出 `Done:` 与 `实际触碰文件：<实施后回填>`（`templates/proposal.md:163-165`），但未注记由谁写、在哪写。

**机制侧事实（已实证，文档必须与之对齐）：**

| # | 机制事实 | 证据 |
|---|---------|------|
| b | 隔离提交前无条件用 `.wopal` 权威副本覆盖隔离工作区提案副本；覆盖前的字节仅用于提交失败回滚，**不检测副本是否被人工修改** → 主控在工作区副本回填的 Done 被静默吞掉（无报错、无警告） | `projects/wopal-cli/src/lib/space-proposal.ts:477`（调用点）、`:468-472`（注释自陈 prior bytes 只作回滚） |
| c | `--paths` 合法性判定为 `existsSync(join(worktreePath, path))` 或 `gitPathTracked(worktreePath, path)` → **基准 = 被提交侧工作区根**（isolated = 隔离工作区；quick/instant = `.wopal`） | `projects/wopal-cli/src/lib/space-proposal.ts:454-457` |
| c' | CLI help 示例写作 `--paths .wopal/skills/n/SKILL.md`，按上述语义解析为 `<工作区根>/.wopal/skills/n/SKILL.md`，既不存在也未被跟踪 → 以 `SPACE_EVO_COMMIT_TARGET_INVALID` 拒绝 | `projects/wopal-cli/src/commands/space.ts`（`commit` 帮助文本两处） |
| c'' | `references/commands.md` 三处提及 `--paths`（`:137` / `:209` / `:212`）但**从未定义基准**——失败形态是「缺失」而非「写错」 | `references/commands.md:137,209,212` |
| d | 阶段推进只在**真实跃迁**时按名提交提案文件；draft 期**内容修订**无任何提交路径 | `references/commands.md:87-88` |
| d' | `space sync` 遇未提交的跟踪变更直接中止 → draft 修订未提交会把 sync 卡死 | `projects/wopal-cli/src/lib/space-sync.ts:644-648` |
| — | 工作区根即装配根（`skills/` `docs/` `agents/` `rules/` `commands/` `plugins/` 与 `.wopal/` 同构）；`.wopal/` 前缀是**空间根视角**，不是 `--paths` 视角。提案文件在两种模式下相对路径一致：`docs/evolutions/<name>.md` | `space-proposal.ts:475`（`join(worktreePath, proposalRel)`）+ 工作区根目录实测 |

**设计真相源** `.wopal/docs/DESIGN-evolution.md` 描述的是机制契约（稀疏隔离、上行闸、交付终端），**不含**逐任务提交流与记录协议（实测零命中）→ 本流程纪律属技能层，无需改设计文档，二者不冲突。

**启动前提（依赖）**：wopal-cli Issue #240（`enhance(wopal-cli): rework isolated proposal record flow`）须先行落地——去覆盖式 sync、`advance` 阶段即时镜像进工作区副本、支持主控单提交承载「代码+记录」、修正 `--paths` 示例。缺任一项，D-01 的记录回填会再次被静默吞掉、两侧副本在 `integrate` 冲突、或主控在 isolated 模式下只能绕道空间侧裸提交。本提案不实现 Issue #240；若其最终行为与本提案的流程描述分叉，须先修订本提案再实施。

### Research Findings

本轮 isolated 实施（`refactor-plugin-config-consumption`，2026-09-27）实测七项摩擦：记录协议缺失（a）、隔离提交静默覆盖记录（b）、`--paths` 基准未定义且 CLI 示例带错前缀（c）、draft 期修订无提交路径（d）、角色×命令矩阵缺失（e）、并行实施规范缺失（f）、模板无记录归属注记（g）。证据见上表与 Architecture Context 正文。

**参考资料**：
- `projects/wopal-cli/docs/DESIGN-evolution.md`（机制契约，判定本提案不越界的依据）
- `projects/wopal-cli/src/lib/space-proposal.ts`（提交与覆盖行为实证）
- `.wopal/docs/evolutions/refactor-plugin-config-consumption.md`（并行纪律与 Done 记录的实际形态，格式与内容参照）

### Key Decisions

- D-01 **记录作者与位置**：实施期提案文件的**唯一作者是主控 agent**——完成勾选与记录段**全部由主控填写**，**实施 agent 绝不编辑提案文件的任何部分**，只回报材料（测试输出 / 实际触碰文件清单 / 异常）。记录位置**按模式而定**：isolated = 隔离工作区内的提案副本；quick = 空间工作区（`.wopal`）副本——quick 无隔离工作区，其代码与记录同处空间分支，不构成跨分支。**不新增 `record` 命令**。禁止项为模式相对：**isolated 模式下禁止把记录单独提交到空间侧**（跨分支），本轮 `45f86b6` / `6edf893` / `4c15291` 三次空间侧裸提交正是要根除的形态。
- D-02 **提交粒度与分支纪律**：实施 agent 完成一个 task 后**不提交**，只把成果（测试输出、实际触碰文件清单、异常）汇报给主控；主控验证通过后填写记录，并**一次性提交**（代码 + 记录同提交）。提交**落在工作分支**：isolated = 隔离分支，quick = 空间分支；**不跨分支做变更**（isolated：不在空间侧改隔离分支内容、也不在隔离工作区改 `.wopal`；quick：代码与记录同在空间分支，无跨分支问题）。
- D-03 **验证前置与同 task 返工**：主控**趁实施会话存活及时验证**——会话一死，返工成本从「同一会话内 `reply`」跃升为「重开会话 + 重新装载上下文」。有问题**立即 `reply` 同一 task**返工，不新开 task、不并行铺开；通过后才进入 D-02 的记录与提交。
- D-04 **机制依赖 Issue #240**：本提案只写「目标流程」，其机械可行性由 Issue #240 交付（去覆盖式 sync、`advance` 即时镜像、单提交承载记录、`--paths` 示例修正）。技能不得描述 CLI 尚未具备的行为；依赖未落地时本提案不得实施。
- D-05 **技能文档重写范围**：`SKILL.md` 增补**角色×命令矩阵**（覆盖 new / accept / advance / commit / integrate / archive / 记录回填七项动作的执行者）、**记录协议**、**并行实施规范**三节，并把 `Landing an evolution` runbook 改为逐行带执行者归属；`references/commands.md` 补 `--paths` 基准定义与记录流程表述；`templates/proposal.md` 补记录归属注记；本技能 `AGENTS.md` §3 同步记录归属与提交粒度两条决策边界。**不重写**命令语义（归 `references/commands.md` 与 CLI 契约）、**不新增**平行命令。
- D-06 **明确不新增命令**：`record` 之类命令一律不引入。记录编辑是普通文件编辑，发生在工作区分支的提案副本上（isolated = 隔离工作区副本；quick = 空间工作区副本）；为它开命令等于把「编辑提案」升格成状态机动作，与 `Stage is written only by commands` 的分工相悖。CLI 侧命令族保持原样。

### Key Interfaces

- **命令行为不变**：本提案不新增、不改名、不改语义任何 `wopal space evo` 命令；其行为修正由 Issue #240 在 CLI 侧交付。本提案对 CLI 的引用只是「如实描述目标流程」。
- **文档级硬约束（新增；实施中要改必须先回报修订提案）**：
  1. 记录归属：唯一作者 = 主控（完成勾选与记录段全部由主控填写）；位置按模式 = 工作区分支的提案副本（isolated = 隔离工作区副本；quick = 空间工作区副本）；实施 agent 不编辑提案文件任何部分；isolated 模式禁止把记录单独提交到空间侧。
  2. 提交粒度：实施不提交；主控单提交（代码 + 记录）；提交落在工作分支（isolated = 隔离分支，quick = 空间分支）；禁止跨分支变更。
  3. `--paths` 基准：被提交侧工作区根；`.wopal/` 前缀是空间根视角，写进 `--paths` 会被判 invalid 拒绝。
  4. 记录回填时机：主控验证通过之后、提交之前；不通过走 D-03 返工，不落记录。

## In Scope

- `.wopal/skills/ontology-evolution/SKILL.md`：`Landing an evolution` runbook 逐行标注执行者；新增**角色×命令矩阵**（七项动作）、**任务记录协议**（D-01/D-02/D-03）、**并行实施规范**（显式 `--paths`、并发被拒重试、禁碰他人文件与工作区状态、工作区保护禁令块）。
- `.wopal/skills/ontology-evolution/references/commands.md`：补 `--paths` 路径基准定义（被提交侧工作区根，isolated / quick / instant 三态）与正确示例；补记录编辑与提交的流程表述（谁写、写在哪个副本、何时提交）。
- `.wopal/skills/ontology-evolution/templates/proposal.md`：`Done` 段补记录归属注记（由主控在工作区分支的提案副本整体填写，含完成勾选；实施 agent 不填任何部分）。
- `.wopal/skills/ontology-evolution/AGENTS.md` §3：同步记录归属与提交粒度为长期决策边界。

## Out of Scope

- **CLI 实现**（去覆盖式 sync、`advance` 阶段即时镜像、单提交承载记录、`--paths` 示例修正、`integrate` 脏工作区指引）：由 wopal-cli Issue #240 承接，提案不实施、不预判其实现细节。
- **新增任何 evo 命令**（含 `record`）：D-06 明确不引入。
- `assembly/` 装配单、装配范围与物化机制。
- 其他 evo 命令（`new` / `status` / `check` / `accept` / `advance` / `archive`）的行为与阶段机语义。
- `.wopal/docs/DESIGN-evolution.md`：已核实不含逐任务提交流与记录协议（机制契约层），本提案不产生需同步的冲突。
- `space sync` / `ontology contribute`：交付终端，用户拍板。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 技能主文档 | `skills/ontology-evolution/SKILL.md` | 修改 | runbook 执行者归属、角色×命令矩阵、记录协议、并行实施规范 |
| 命令参考 | `skills/ontology-evolution/references/commands.md` | 修改 | `--paths` 基准定义与示例、记录流程表述 |
| 提案模板 | `skills/ontology-evolution/templates/proposal.md` | 修改 | `Done` 段记录归属注记 |
| 技能开发规则 | `skills/ontology-evolution/AGENTS.md` | 修改 | 记录归属与提交粒度入 §3 决策边界 |

## Acceptance Criteria

### Agent Verification

1. [ ] **结构门禁**：提案结构完整、可被 `accept` 接受。验证：`wopal space evo check refactor-evolution-flow` 退出 0，输出中无 `content:` 与 `structure:` 问题行（draft 期允许 `note:`）。
2. [ ] **角色×命令矩阵**：`SKILL.md` 存在角色×命令矩阵表，逐项覆盖 new / accept / advance / commit / integrate / archive / 记录回填七项动作的执行者；`Landing an evolution` runbook 每条命令均带执行者归属，无裸命令行。验证：矩阵表存在且七项动作各有归属；runbook 逐行与矩阵一致。
3. [ ] **记录协议**：记录协议节命中全部四条断言——① 唯一作者 = 主控 agent（完成勾选与记录段均由主控填写，实施 agent 不编辑提案文件任何部分）；② 编辑位置**按模式**：isolated = 隔离工作区内的提案副本、quick = 空间工作区（`.wopal`）副本；③ 时机 = 主控验证通过后、提交前；④ 禁止项（isolated 模式禁止把记录单独提交到空间侧；不新增 `record` 命令）。验证：四条断言逐条可 grep 命中；quick 分支的位置表述存在，且未被「绝不编辑 `.wopal`」类绝对表述覆盖。
4. [ ] **并行实施规范**：`SKILL.md` 存在并行实施规范节，命中全部四项——① 提交必须显式 `--paths`（省略会扫入其他任务在途改动）；② 因并发被拒时原样重试；③ 禁自行处置他人文件与工作区状态；④ 工作区保护禁令（禁 `reset` / `checkout` / `restore` / `clean` / `stash` 等触碰工作区的操作）。验证：四项逐条命中。
5. [ ] **`--paths` 基准**：`references/commands.md` 明确写出基准 = 被提交侧工作区根（isolated = 隔离工作区；quick / instant = `.wopal`），并说明 `.wopal/` 前缀是空间根视角、用于 `--paths` 会被判 invalid 拒绝。验证：`rg -n -- '--paths' .wopal/skills/ontology-evolution/SKILL.md .wopal/skills/ontology-evolution/references/` 中**所有** `--paths` 示例均按该基准书写（无 `.wopal/` 前缀），且基准定义句存在（扫描范围限定文档文件，避开 `scripts/` 与 `tests/` 的实现与用例噪声）。
6. [ ] **模板与 AGENTS 同步**：`templates/proposal.md` 的 `Done` 段带记录归属注记（主控在工作区分支的提案副本整体填写，含完成勾选；实施 agent 不填任何部分）；本技能 `AGENTS.md` §3 含记录归属与提交粒度两条决策边界。验证：两文件对应注记可 grep 命中。
7. [ ] **旧表述零命中与跨文件一致**：`SKILL.md` 不再含未归属的 `per task` runbook 注释；`SKILL.md` 与 `references/commands.md` 对「实施不提交 / 主控单提交 / 落在工作分支」的表述一致，无相互矛盾的句子。验证：`rg -n 'sparse-safe, per task' .wopal/skills/ontology-evolution/` 零命中；两文件就提交粒度的表述人工比对无冲突（同一句话或同一措辞）。

### User Validation

#### Scenario 1: 冷读执行者复述 isolated 双任务全流程
- Goal: 确认**只读 SKILL.md 的 agent** 能无歧义执行 isolated 双任务全流程（谁写记录、谁提交、提交落在哪个分支、并行时如何隔离路径），不再需要 git 历史考古。
- 验证环境: 本空间 dev 构建的 ellamaka；开一个**全新会话**，不提供本提案、不提供历史上下文。
- Precondition: 本提案已集成到空间分支。
- 启动命令: `cd projects/ellamaka && ./scripts/dev.sh tui`
- User Actions:
  1. 新开会话，要求 agent「只读 `.wopal/skills/ontology-evolution/SKILL.md`，口述 isolated 模式下两个并行 task 的完整执行流程：每步谁执行、记录写在哪、验证在什么时候、提交由谁做、提交落在哪个分支、`integrate` 在哪一步」；
  2. 追问两个歧义点：「实施 agent 能不能自己改提案文件的 Done？」「`--paths` 里的路径要不要带 `.wopal/` 前缀？」
- 通过判据: 复述与 SKILL.md 文本一致；两个歧义点均给出唯一答案（实施 agent 不改提案记录任何部分，含完成勾选；`--paths` 不带 `.wopal/` 前缀，基准是工作区根）；quick 模式下记录位置答「空间工作区副本」而非「隔离工作区」；无「需要查 git 历史」这类无来源回答。
- 失败反馈: 贴出 agent 完整回答，并指出与哪条文档冲突。

- [ ] 用户已完成上述功能验证并确认结果符合预期

#### Scenario 2: 重启后技能加载与流程段可见
- Goal: 确认改写加载路径资产（`SKILL.md`）后技能仍正常装载，重构后的流程段在真实会话中可见。
- 验证环境: 本空间 dev 构建；验证入口见 `projects/ellamaka/AGENTS.md`（Manual Verification Entry Points）。
- Precondition: 本提案已集成到空间分支；Agent Verification 全绿。
- 启动命令: `cd projects/ellamaka && ./scripts/dev.sh tui`
- User Actions:
  1. 重启 TUI 并新开一个会话；
  2. 确认 `ontology-evolution` 技能可加载，且角色×命令矩阵 / 记录协议 / 并行实施规范三节在实际加载内容中可读。
- 通过判据: 技能正常加载无报错；三节内容在实际加载的技能文本中可见；`.wopal-space/logs/dev/` 下无技能装载类 error。
- 失败反馈: 提供日志片段与实际加载到的技能文本。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: runbook 执行者归属与角色×命令矩阵

**Verification Intent**: AC#2、AC#7

**Behavior**:
- `SKILL.md` 的 `Landing an evolution` runbook 每条命令带执行者标注（new / accept / advance / commit / integrate / archive 及记录回填），quick 模式差异分支同样标注；
- 存在角色×命令矩阵表，七项动作各有唯一执行者，无「未指明」格子；`implementing` 阶段的 `commit` 归属写明为主控（D-02），不写成实施者；
- 旧的无归属 runbook 注释消失（`# sparse-safe, per task` 一类）。

**Pre-read**: `.wopal/skills/ontology-evolution/SKILL.md`（Roles 表与 `Landing an evolution` 全节）；`.wopal/docs/evolutions/refactor-plugin-config-consumption.md:221-233`（实际归属与纪律形态参照）

**Design**: 在 Roles 表之后新增「角色×命令矩阵」小节：行=动作，列=执行者 / 依据 / 备注；`advance` 按阶段写明跃迁由主控推进。runbook 改为带执行者的行内标注，与矩阵逐行一致。矩阵是「谁跑什么」的唯一真相源，runbook 只做时序叙述，不重复判定归属。quick 模式（`--no-worktree`）单列一行说明差异：跳过 `integrate`，`commit` 直接落在空间分支。

**TDD**: false（文档重写，无逻辑变更；判据为可 grep 的文本契约）

**Changes**:
1. 起草矩阵表（七项动作 × 执行者 / 依据），逐项对照 D-01/D-02/D-03 定归属。
2. 重写 `Landing an evolution` runbook：逐行加执行者标注，删除未归属注释，quick 分支补差异行。
3. 自查：矩阵与 runbook 逐行一致，无未指明归属。

**Verify**: `rg -n 'per task' .wopal/skills/ontology-evolution/SKILL.md` 零命中；矩阵表存在且七项动作各有归属（逐行核对 runbook 与矩阵）。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 2: 任务记录协议

**Verification Intent**: AC#3

**Behavior**:
- 记录协议节写明：实施期提案文件唯一作者 = 主控 agent——完成勾选与记录段**全部由主控填写**；实施 agent 绝不编辑提案文件任何部分（含勾 Done、回填实际触碰文件），只回报材料；
- 编辑位置**按模式**：isolated = 隔离工作区内的提案副本；quick = 空间工作区（`.wopal`）副本——quick 无隔离工作区，代码与记录同处空间分支，不属跨分支；
- isolated 模式另给出**耐久理由**说明为何不在空间侧编辑记录：① 空间侧与工作区分支是两条独立历史，记录只落空间侧就无法与代码同提交、也无法随工作分支一起回滚；② 空间侧留有未提交的记录编辑会让 `.wopal` 变脏，直接阻塞 `integrate`（对脏工作区硬拒绝，`references/commands.md:246`）；③ 两侧副本分叉会在 `integrate` 的三方合并中冲突。覆盖式 sync 仅作历史背景提及（Issue #240 将移除它，不得作为长期理由）；
- 时机 = 主控验证通过之后、提交之前；不通过走同 task 返工，不落记录；
- 禁止项：不新增 `record` 命令（D-06）、isolated 模式禁止把记录单独提交到空间侧（点明本轮三次裸提交为要根除的形态）；
- 记录内容下限：测试输出、实际触碰文件清单、异常。

**Pre-read**: `.wopal/skills/ontology-evolution/SKILL.md`（Roles 表）；`templates/proposal.md:163-165`（Done 段现状）；`.wopal/docs/evolutions/refactor-plugin-config-consumption.md:159-162`（Done 实际填写形态）

**Design**: 作为独立小节置于状态机之后、runbook 之前——读者在看到流程之前先知道「谁有资格改提案」。以「作者与位置 / 时机 / 禁止项 / 内容下限」四段式组织，每段一句判定加一句理由。机制侧依赖只以「由 Issue #240 承接」一句带过，不展开 CLI 实现。

**TDD**: false（文档新增，无逻辑变更）

**Changes**:
1. 写四段式记录协议（D-01 / D-02 / D-03 / D-06 落点）。
2. 补机制侧依赖说明与被根除形态的对照。
3. 自查四条断言均可 grep 命中。

**Verify**: `rg -n '主控|唯一作者|实施 agent' .wopal/skills/ontology-evolution/SKILL.md` 命中记录协议节；四条断言逐条命中。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 3: 并行实施规范常驻化

**Verification Intent**: AC#4

**Behavior**:
- `SKILL.md` 存在并行实施规范节（同一隔离工作区、多任务并行场景），命中四项：显式 `--paths`（省略会扫入他人在途改动，故禁止省略）；因并发（index 占用等）被拒时原样重试；禁自行处置他人文件与工作区状态；工作区保护禁令块（禁 `reset` / `checkout` / `restore` / `clean` / `stash` 等触碰工作区的操作，未提交变更一律上报不处置）。
- 该节为常驻段落，不再逐轮手抄进委派 prompt。

**Pre-read**: `.wopal/docs/evolutions/refactor-plugin-config-consumption.md:230-233`（现行纪律原文，四项的权威来源）；`.wopal/skills/ontology-evolution/AGENTS.md` §3（规则分层与 Test Discipline 写法参照）

**Design**: 以现行纪律原文为基线提升为技能常驻节，措辞从「本提案的纪律」改为「任何隔离并行实施的纪律」。四项各一句判定 + 一句理由（尤其「省略 `--paths` 会收集全部跟踪改动」必须带后果说明，否则会被当成可选优化）。与 Task 2 分节，避免记录协议被并行纪律稀释。

**TDD**: false（文档新增，无逻辑变更）

**Changes**:
1. 将四项纪律提升为常驻节，补后果说明。
2. 补「委派 prompt 无需再手抄本节」的一句指向。
3. 自查四项逐条命中。

**Verify**: `rg -n '并发|工作区|禁' .wopal/skills/ontology-evolution/SKILL.md` 命中并行实施节；四项逐条核对命中。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 4: `--paths` 路径基准与记录流程表述修正

**Verification Intent**: AC#5、AC#7

**Behavior**:
- `references/commands.md` 明确写出 `--paths` 基准 = 被提交侧工作区根，并分态说明（isolated = 隔离工作区；quick / instant = `.wopal`）；
- 说明 `.wopal/` 前缀是空间根视角而非 `--paths` 视角，用于 `--paths` 会因解析为 `<工作区根>/.wopal/...` 而被判 invalid 拒绝（错误码 `SPACE_EVO_COMMIT_TARGET_INVALID`）；
- 文档内（`SKILL.md` 与 `references/`）所有 `--paths` 示例按该基准书写（现状：`references/commands.md` 只有三处提及，**既无示例也从未定义基准**——需从「缺失」补为「有定义 + 有正确示例」）；
- 补记录流程表述：记录编辑发生在工作区副本、由主控执行、随代码一次性提交。

**Pre-read**: `.wopal/skills/ontology-evolution/references/commands.md:130-227`（`commit` 全节）；`projects/wopal-cli/src/lib/space-proposal.ts:443-465`（基准判定与拒绝信息原文）

**Design**: 基准定义放在 `commit` 节的 `--paths` 首次出现处，三态一句话说清；错误示例作为反例单列一句（引用真实错误码与拒绝文案来源）。记录流程表述以「见 SKILL.md 记录协议」的交叉引用承接，避免两处各写一套而产生分叉（AC#7）。CLI 帮助文本的错误示例**不在本提案修**——归 Issue #240，本提案只描述正确基准。

**TDD**: false（文档修正，无逻辑变更）

**Changes**:
1. 在 `commit` 节补基准定义（三态）与反例说明。
2. 补一条可照抄的正确示例。
3. 补记录流程交叉引用；自查与 `SKILL.md` 表述一致。

**Verify**: `rg -n -- '--paths' .wopal/skills/ontology-evolution/SKILL.md .wopal/skills/ontology-evolution/references/` — 文档内所有 `--paths` 示例均不带 `.wopal/` 前缀；基准定义句存在；反例含 `SPACE_EVO_COMMIT_TARGET_INVALID`（扫描范围限定文档，避开 `scripts/` 与 `tests/` 的噪声）。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 5: 提案模板记录注记与技能 AGENTS 同步

**Verification Intent**: AC#6

**Behavior**:
- `templates/proposal.md` 的 `Done` 段补注记：记录段**整体**（完成勾选 + 任务产出 + 实际触碰文件）由**主控**在**工作区分支的提案副本**（isolated = 隔离工作区副本；quick = 空间工作区副本）填写；**实施 agent 不编辑提案文件任何部分**，只回报材料（测试输出 / 实际触碰文件清单 / 异常）——消除「待实施后回填」的归属歧义；
- 模板注记与 `check` 的占位符扫描不冲突（注记不得引入未替换的尖括号占位符，否则提案过不了 `accept` 门禁）；
- 本技能 `AGENTS.md` §3 新增记录归属与提交粒度两条决策边界（长期原则，非实现细节），与 `SKILL.md` 记录协议一致。

**Pre-read**: `.wopal/skills/ontology-evolution/templates/proposal.md:160-166`；`.wopal/skills/ontology-evolution/AGENTS.md` §3；`projects/wopal-cli/src/lib/space-evo-state.ts:53-56`（占位符扫描正则，理解注记写法约束）

**Design**: 模板注记写在 `Done` 段的 HTML 注释里（模板本身是带作者注释的骨架，注记不进入渲染正文），措辞与 `SKILL.md` 记录协议逐句对齐。`AGENTS.md` 只收决策边界（谁写记录、谁提交、落在哪个分支），不复制流程细节——细节归 `SKILL.md`，`AGENTS.md` 按其分层原则只留必须一致的长期约束。

**TDD**: false（文档修改，无逻辑变更）

**Changes**:
1. 模板 `Done` 段加记录归属注记。
2. `AGENTS.md` §3 加两条决策边界。
3. 自查：模板改动未引入未替换占位符（`check` 语义上仍可过门禁）。

**Verify**: `rg -n '主控' .wopal/skills/ontology-evolution/templates/proposal.md .wopal/skills/ontology-evolution/AGENTS.md` 命中；模板占位符扫描结果与改动前一致（未新增尖括号占位）。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

本提案自身按其定稿流程实施（自我一致）：实施 agent 不提交，主控验证通过后一次性提交「代码 + 记录」，落在工作分支。

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 runbook 归属 + 矩阵 | fae | Issue #240 已落地 | `SKILL.md` 改动链起点；先定归属，后两节才有引用对象 |
| 1 | Task 4 `commands.md` 基准与流程表述 | fae | 无 | 与 `SKILL.md` 文件不相交，可与 Task 1 并行；交叉引用用占位措辞，Wave 3 校对一致性 |
| 1 | Task 5 模板注记 + AGENTS 同步 | fae | 无 | 文件不相交，可并行；AGENTS 只收决策边界，不依赖前序正文 |
| 2 | Task 2 任务记录协议 | fae | Task 1 | 与矩阵同文件，串行；协议需引用已定好的执行者归属 |
| 3 | Task 3 并行实施规范 | fae | Task 1 | 同 `SKILL.md`，串行 |

并行纪律（同一隔离工作区；本节内容即 Task 3 的产出，此处先行适用）：

- Task 1 / 2 / 3 改同一文件 `SKILL.md`，**必须串行**，不得并行委派。
- 显式 `--paths` 提交，禁止省略（省略会扫入其他任务在途改动）。
- 因并发被拒时原样重试；禁自行处置他人文件与工作区状态。
- 委派 prompt 末尾附工作区保护禁令块。

## Delivery

- 实施留在工作分支（isolated = 隔离分支；quick = 空间分支），`integrate` 一次 squash 收口；`space sync` / `ontology contribute` 由用户拍板，技能不自动上行。
- 归档闭环：核对本提案与 Issue #240 的落地一致性（`--paths` 示例两侧是否都已修正、覆盖式 sync 是否确已去除）；若 Issue #240 行为与本提案流程描述分叉，先修订本提案再归档。
