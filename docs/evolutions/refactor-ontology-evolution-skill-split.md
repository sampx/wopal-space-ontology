# refactor-ontology-evolution-skill-split

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-21
- **Stage**: implementing
- **Mode**: isolated
- **Worktree**: `.worktrees/wopal-space-ontology-evolution-skill-split`
- **Branch**: `wopal-space-ontology-evolution-skill-split`
- **Base Commit**: `80202a5`（实施分支 rebase 后的 `space/wopal-workspace` HEAD；初始起点为 `00abb5e`）
- **Final Commit**: 9f543dfda34b22e69a8533bc88a59239e826e132

> **Bootstrap 说明**：本提案是本体进化流程的第一件产物，也是第一个落在 `docs/evolutions/` 的提案。设计已先行落在 `docs/DESIGN-evolution.md` 的 Capability Evolution Workflow 章节，本提案按该设计实施。流程的状态推进脚本尚未存在（正是本提案的交付物之一），因此由用户批准后按 Task 顺序执行，产出提交在 `wopal-space-ontology-evolution-skill-split` 分支上。

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

让本体能力进化成为每个空间类型的常驻能力：按 `docs/DESIGN-evolution.md` 落定本体能力进化流程的设计，为 `ontology-evolution` 技能补齐机制车道（提案状态机、隔离实施、安全提交、稀疏体检、交付终点），并把 `ontology-worktree` 类型从 `dev-flow` 中摘除，使两条流程各有唯一入口。

机制车道必须让**用户与 Agent 都无法误伤本体能力池**：稀疏装配的隐形边界（范围外文件、S 位、静默吞文件）由命令守住，而不是靠文档纪律与自觉。

## Technical Context

### Architecture Context

设计真相源已经落定在 `.wopal/docs/DESIGN-evolution.md`（本次先行的设计变更），本 Plan 是它的实施载体。

现状由三条事实构成：

1. **设计已定义、机制层空缺**。`docs/DESIGN-evolution.md` 的 Capability Evolution Workflow 定义了语义车道（Evolver 出《进化方案》）与机制车道（Wopal 编排、Fae 实施、Rook 守门）的分工、状态机 `draft → accepted → implementing → validating → archived`、稀疏隔离纪律与交付终点。该技能当前池中只有 `SKILL.md`（evolver 独占的只读蒸馏技能），机制车道尚无载体。
2. **`dev-flow` 承担了本体开发，心智错配**。`ontology-worktree` 作为 dev-flow 的 Project Type 已贯穿其 19 个源文件（10 个脚本：`plan.py`、`lib/{project,git,worktree}.py`、`commands/{plan,approve,complete,verify,verify_switch,archive,issue}.py`；7 个测试；5 份文档）。其 TDD 红绿、每任务一提交、rook 双轮预算、lint 门禁、五种验证场景、树比较判合并，服务于代码产品的集成正确性；本体能力进化的验证是重启 ellamaka 观察加载行为，交付是用户拍板 `space sync` / `ontology contribute`。
3. **技能装配已于本次会话完成**（不在本 Plan 范围）。`wopal-dev space capability add skill:ontology-evolution` 已执行：技能文件落盘、`assembly/archetypes/coding.yaml` 与 `space-meta.json` 声明生效、稀疏装配范围新增 `/skills/ontology-evolution/`。该变更当前未提交，属本次实施的一部分工作区事实。

> **术语红线**：`ontology-worktree` 有两个互不相干的含义。其一为空间组件类型（`.wopal` 是稀疏装配 worktree），出现在 `assembly/templates/{STRUCTURE,REGULATIONS}.md`、`docs/DESIGN-assembly.md`、`.wopal-space/{STRUCTURE,REGULATIONS}.md`——这些是结构文档，语义正确，不得改动。其二为 dev-flow 的 Project Type 枚举值——本 Plan 摘除的是这一个。判据以"文件是否在 `.wopal/skills/dev-flow/` 内"为准。

### Research Findings

隔离探针实证（tmp 仓库，复刻真机非 cone + 文件型 pattern 形态）：

- 从稀疏源（`.wopal`）执行 `git worktree add` **完整继承稀疏配置与 patterns**（真机实测 44 条一致，`H=459 S=160`）；从全量宿主仓库执行则不继承。
- 切换分支时，既有 patterns 覆盖内的新文件由 `git checkout` 自动物化；patterns 之外的新路径保持 S 位、磁盘不可见。
- 合并与对象层对稀疏免疫：分支推进、squash、`rev-parse` 树比较均不受影响，范围外条目合并后保持 S 位。
- 稀疏生效时 Git 原生拒绝暂存范围外文件（须 `--sparse`）；配置丢失且 S 位被批量清除时，`git add -A` 会把范围外文件记为删除。
- **规划期发现**：本体文档含跨仓库相对链接（如 `../../docs/products/wopal-space/DESIGN.md`、`../projects/*/docs/DESIGN.md`），只在 worktree 位于 `<space>/.wopal` 这一层时解析成立。因此 `verify-docset.py` 是 canonical 路径检查：真机 `.wopal/docs` 下 PASS，在 `.worktrees/<name>/docs` 下必然报跨仓库链接断裂（路径深度伪失败，与本文件内容无关）。

实施期第二轮实证（临时仓库复刻真机非 cone + 文件型 pattern 形态；全部为实跑结果）：

- **`--sparse` 的不对称与顺序陷阱**：`git mv` / `git add` 对范围外路径默认拒绝（exit 1，索引零改动），须 `--sparse`；`git commit` **无** `--sparse` 选项。但 `--sparse` 只把文件塞进索引、**不扩范围**：此后任何一次范围重算（`reapply` / `sync` 的 `applySparsePatterns`）都会把它从磁盘移走（转 `S` 位、静默消失）。正确顺序是**先 `git sparse-checkout add` 扩范围**，再走普通 git 命令；扩范围后 `reapply` 仍可见。
- **`sparse-checkout disable` 是唯一的灾难入口**：实测 `reapply` / `set` / `checkout` / `reset --hard` / `add -A` 均保留 S 位与配置；只有 `disable` **同时**清除 `core.sparseCheckout` 与全部 S 位。二者丢失后，范围外文件（本就无磁盘副本）被误判为"应存在却缺失"，`git add -A` 会把它们整批记为 `D`。
- **9/20 现场的形态已取证**：`.wopal-space/.tmp/forensic-*` 记录了 212 条 ` D`（根文件、`docs/` 49 个、`assembly/` 2 个，另有 `.gitignore` 一处 ` M`）；`git ls-files --debug` 显示当时**全部文件 `flags: 0`**（正常应为 `0x4000`，即 skip-worktree）。该批删除**未进入 git 历史**。
- **集成回 space 分支只有一条干净路径**：`git push . HEAD:space/<branch>` 被 Git 拒绝（目标分支已在 `.wopal` 检出）；`git update-ref` 能改 ref 但使 `.wopal` 立即出现 `D`/`M` 不一致（同 9/20 签名）；唯 `.wopal` 内 `merge --squash` + commit 后 status 干净、patterns 完好、树完整。
- **空间私有删除会上行污染能力池**：复刻 `sync` 的计算路径（`resolveCapability` 在主仓库探测文件存在）——第 1 轮删掉装配单内能力目录后 sync 通过并**把删除上行到 `local main`**；第 2 轮主仓库已无该能力，`resolveCapability` 抛 `ASSEMBLY_CAPABILITY_UNRESOLVED`，sync 硬失败（无 try/catch）。详见 Discovered Defects XD-01。

**参考资料**：
- `.wopal/docs/DESIGN-evolution.md`（设计真相源）
- `projects/wopal-cli/src/lib/space-capability.ts`（capability add 的落点与再物化语义）
- `projects/wopal-cli/src/lib/space-sync.ts`（sync 上行/下行与游离文件纳管语义）

### Key Decisions

- D-01: **本体进化与代码开发分流**。`ontology-evolution` 承接本体能力进化；`dev-flow` 摘除 `ontology-worktree` 类型，回归纯代码项目语义。判据从"选技能"改为"看对象"：`projects/` 下的代码仓库 → dev-flow；空间本体能力 → ontology-evolution。割掉重叠区，从机制上消除误选。
- D-02: **状态词汇与 dev-flow 零重叠，并用独立字段承载**：`draft → accepted → implementing → validating → archived`。实测 dev-flow 的词表是 `planning / reviewing / approved / executing / verifying / done`——若沿用 `approved / executing / verifying / done`，五个状态会撞四个，且 `executing`、`verifying` 恰好最容易被误读成 dev-flow 的审批与验证语义。故全部换词，并用 `Stage` 字段承载提案推进状态，与设计文档的 `Status` 字段（Draft / Proposed / Active）也区分开：字段名与词表双重不重叠。默认不带 Issue 载体，评审仅用户明确要求时进入。
- D-03: **默认隔离模式 = 从 `.wopal` 派生稀疏 worktree**（继承 patterns，边界天然等于空间确权范围）。**快速模式** = 在 `.wopal` 空间分支直接小步提交，仅限 typo、bug-fix 与用户明确指定的小范围文件改动。空间分支本身即是对 local main 的隔离边界。
- D-04: **交付是用户决定的人类终点**：进化产物先落空间分支，是否 `space sync` 上行 local main、是否 `ontology contribute` 上游，由用户逐次拍板；技能不内置自动上行。
- D-05: **不新建引擎或共享内核**。机制车道需要的基础设施只有 markdown 状态字段流转与 git 提交（Issue 层默认不参与），属一两百行量级；复刻一份到本技能比抽象跨技能引擎更便宜，也避免引入无人认领的第三类产物。
- D-06: **新能力目录必须进装配**。进化若新增能力目录，该目录须在实施前纳入实施侧装配范围，合并后再扩展 `.wopal` 装配并重新物化，否则验证者看不到新能力。
- D-07: **文档质量门按 canonical 路径判定**。`verify-docset.py` 的跨仓库相对链接检查只在 `.wopal/docs` 成立；在实施 worktree 内以该门判定文档缺陷是无效判据。文档任务的验证分两段：worktree 内跑位置无关检查（`Sub-DESIGNs` 索引、`Updated` 日期、绝对路径、过程态词汇），`canonical` 路径的完整门在合入后判定。
- D-08: **稀疏边界必须由命令守住，不能只靠文档纪律**。"永不批量清除 S 位"写在 `SKILL.md` 里是自律，机器不认；`commit`/`check` 必须把它变成可执行的拒绝。这是本提案从 9/20 事件学到的第一条。
- D-09: **危险形态的判据是"索引与稀疏范围不一致"，不是"用户删了东西"**。稀疏生效时，用户删除范围外文件对 Git 完全不可见（`S` 位的定义），无需处理；真正的灾难形态是 S 位丢失后，范围外文件被误判为"应存在却不在磁盘"，进而在 `git add -A` 时整批记为删除。9/20 的 212 个 `D` 即此形态。
- D-10: **集成回 space 分支必须在 `.wopal` 内以 squash merge 完成**。实证：`git push . HEAD:space/<branch>` 被 Git 拒绝（目标分支已在 `.wopal` 检出）；`git update-ref` 强行改写 ref 会让 `.wopal` 立即进入损坏状态（出现 `D` 记录，即 9/20 同类签名）。唯 `merge --squash` 路径干净：status 空、patterns 完好、树完整。
- D-11: **用户临时增删空间内容不改装配单**。"空间添加目录"与"空间删除目录"与装配单解耦：增删都隔离在 space 分支，装配单仅在用户显式执行 `space capability add/remove` 时变更。装配单与运行时能力允许不一致（现状亦然，`resolveCapability` 只在重新物化时校验）。
- D-12: **runtime overlay 的写入归 CLI，本提案只做契约预留**。临时增删改的状态需被 `sync` 维持，其写入者必须唯一——`space-meta.json` 已由 CLI 的 `refreshSnapshot`/`writeSpaceSnapshot` 管理，Python 侧再写即制造第二真相源。本提案定义的 `commit` 只记录自身元数据（分支、基线），overlay 留待 CLI 接口就位后对接。
- D-13: **本期以 Python 落地，命令契约按 CLI 可实现的形式设计**。理由：`accept`/`commit`/`check` 所需的稀疏操作仅"读现成 patterns + 加一条 + 校验 S 位"，不依赖 CLI 的装配单解析；Python 侧可即刻解决 VSCode 报错、静默吞文件、无 worktree 自动化三个真实痛点，且设计可快速试错。迁移 `wopal ontology evolve` 时重写实现而保留契约。隔离实施不自行实现 overlay 写入（见 D-12），避免与 CLI 冲突。
- D-14: **隔离 worktree 命名规范回归既有约定**。目录置于 `<space>/.worktrees/`，分支前缀 `ontology-*`（如 `ontology-maka-rename`），取代此前过长的 `wopal-space-ontology-evolution-skill-split`；与 `git-worktrees` 技能的目录约定对齐，但其稀疏能力不在本期补入（该技能以后单独优化）。

### Discovered Defects (out of scope, escalated)

本提案实施期间发现两处**本体之外的既有缺陷**。按 D-11/D-12 的边界，修复不属于本技能，另行立 Issue 交由其他 Agent 处理；此处登记以确保不丢失。

**XD-01: `space sync` 将空间私有删除误当池级变更上行（`wopal-cli`）**

复刻 `space sync` 的真实计算路径（`resolveCapability` 在主仓库检查文件存在）实证：

| 轮次 | 行为 |
|---|---|
| 第 1 轮 | 空间分支删除某个装配单内能力目录 → 主仓库该能力仍在 → 解析成功 → sync 通过 → **删除被上行到 `local main`，污染能力池** |
| 第 2 轮 | 主仓库已无该能力 → `resolveCapability` 抛 `ASSEMBLY_CAPABILITY_UNRESOLVED` → **sync 硬失败（无 try/catch），所有同类空间受影响** |

期望语义：空间私有删除应隔离在 space 分支，`local main` 与装配单均不受影响；装配单与运行时能力允许不一致，不应硬失败。修复需引入 runtime overlay 语义（`added` / `removed` / `renamed`）。

**XD-02: 稀疏状态损坏时缺乏护栏（本技能可缓解一半）**

`git sparse-checkout disable` 是唯一会**同时**清除 `core.sparseCheckout` 与 S 位的命令（实测 `reapply` / `set` / `checkout` / `reset --hard` / `add -A` 均保留）。二者同时丢失后，范围外文件被误判为删除，`git add -A` 会整批记为 `D`——9/20 现场的 212 个 `D` 即此形态（该批删除最终未进入历史）。

本提案的 `commit` / `check` 在前置检查中拦截此形态（见 Task 5）；命令之外的路径（用户直接跑 `git add -A`）无法覆盖，属于遗留风险。

### Key Interfaces

**`ontology-evolution` 的机制车道入口（脚本契约）**：

```
evo.sh new <title>                      创建提案（docs/evolutions/<name>.md，Stage: draft）
evo.sh status <name|path>               打印状态、文件位置、下一步
evo.sh accept <name> [--no-worktree]    接受并进入实施：派生隔离 worktree + 记录元数据（--no-worktree 走快速模式）
evo.sh advance <name> --to <state>      状态推进（校验合法跃迁，非法即拒绝）
evo.sh commit <name> -m <message>       稀疏安全提交：扩范围 → 暂存 → 提交 → 集成回 space 分支
evo.sh check <name>                     体检：提案格式 + 稀疏状态 + 索引一致性
evo.sh archive <name>                   归档到 docs/evolutions/archived/
```

- 状态集合（有序）：`draft → accepted → implementing → validating → archived`
- 非法跃迁（跳级、倒退）返回非零退出码，stderr 列出合法后继状态。
- 状态写入仅通过脚本；Agent 不得手改 `Stage` 字段。
- Issue 层不在契约内（默认无 Issue；用户明确要求时才由 CLI 侧介入）。
- `accept` 是唯一创建 worktree 的入口；`--no-worktree` 时元数据记录为快速模式，`commit` 直接在 `.wopal` 空间分支提交。
- `commit` 是唯一允许改工作区的命令，必须：先扩装配范围、拒绝危险形态、提交后集成回 space 分支。
- 命令名与参数按 CLI 子命令可实现的形式设计（迁移目标：`wopal ontology evolve <action>`，见 D-13）。
- 脚本路径与调用方式在实施时按技能目录约定确定，对外契约以上表为准。

## In Scope

- 落定本体能力进化的设计：`docs/DESIGN.md`、`docs/DESIGN-evolution.md`、`docs/DESIGN-capabilities.md`。
- 为 `ontology-evolution` 补机制车道：状态机脚本、隔离实施纪律、安全提交、稀疏体检、交付终点，并改写其 `SKILL.md`（从 evolver 独占只读扩展为语义车道 + 机制车道）。
- 摘除 `dev-flow` 的 `ontology-worktree` 类型：脚本、测试、文档全部清理。
- 固化技能路由判据：本体能力 → ontology-evolution；代码仓库 → dev-flow。
- **补齐机制车道的实施闭环**（本提案第二轮扩充）：
  - `accept` 动作：派生稀疏隔离 worktree 并记录提案元数据，用户可选择不建 worktree 走快速模式。
  - `commit` 动作：稀疏安全的提交通道——先扩装配范围再提交、隔离模式集成回 space 分支。
  - `check` 动作：提案格式校验与稀疏体检，替代"靠自觉"。
  - Agent 自定义 git 命令的护栏：检测危险形态并拒绝。
  - 命令契约按 CLI 可实现的形式设计，为迁移 `wopal ontology evolve` 预留（本期不迁移实现）。

## Out of Scope

- 不再执行能力装配（已于本次会话完成，属既有工作区事实）。
- 不做 GAPS 差距分析，不新增 GAPS 条目（按用户决定）。
- 不改 `wopal-cli` 的 `space sync` / `space capability` 实现。**本提案发现的 sync 语义缺陷另立 Issue，由其他 Agent 处理**（见 Discovered Defects）。
- 不新增共享引擎或公共内核（D-05）。
- 不改动空间组件类型语义的结构文档（见术语红线）。
- 不清理 `.wopal` 中与本议题无关的既有未跟踪文件。
- **不实现 runtime overlay 的写入**：临时增删改的状态由 CLI 侧（`space sync` / `space capability`）承载，本提案只做命令契约预留与只读消费（见 D-12）。
- 不迁移到 `wopal ontology evolve` CLI 实现（本期以 Python 落地，见 D-13）。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 设计文档 | `docs/DESIGN.md`, `docs/DESIGN-evolution.md`, `docs/DESIGN-capabilities.md` | 修改 | 落定进化流程设计（真相源） |
| ontology-evolution | `skills/ontology-evolution/SKILL.md`, `skills/ontology-evolution/scripts/` | 修改/创建 | 机制车道（状态机 + 稀疏纪律 + 交付终点） |
| dev-flow 脚本（10） | `skills/dev-flow/scripts/{plan.py,lib/{project,git,worktree}.py,commands/{plan,approve,complete,verify,verify_switch,archive,issue}.py}` | 修改 | 摘除 dev-flow 的 ontology-worktree Project Type |
| dev-flow 文档（5） | `skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,references/{commands.md,plan-guide.md,plan-guide.zh-CN.md}}` | 修改 | 移除本体类型说明与验证场景 |
| dev-flow 测试（7） | `skills/dev-flow/tests/python/unit/{test_approve,test_git_semantics,test_plan_cmd,test_push_race_recovery,test_verify,test_verify_switch,test_worktree_context}.py` | 修改 | 移除本体类型断言，保留标准流程回归 |
| space-master 路由（1 行） | `skills/space-master/references/agents-md-maintenance.md:190` | 修改 | 该行以 dev-flow 的 Project Type 语境描述类型归属，改为指向新技能 |
| Agent 能力面（2） | `agents/fae.md`, `agents/rook.md` | 修改 | 机制车道要求 Fae 实施、Rook 守门都能加载该技能，白名单补 `ontology-evolution` |
| Agent 更名（2） | `agents/evolver.md` → `agents/maka.md`, `docs/LANG/zh-CN/agents/{evolver.md → maka.md}` | 重命名/修改 | 进化使者更名 maka，保留炼金术士设定；`edit` 按提案范围精确放开 |
| 装配与名单同步（5） | `assembly/archetypes/coding.yaml`, `docs/{DESIGN,DESIGN-capabilities,DESIGN-evolution,DESIGN-assembly}.md`, `skills/ontology-evolution/{SKILL.md,AGENTS.md}` | 修改 | agents 名单与全部 `Evolver` 署名同步为 `maka`；稀疏 pattern 同步 |
| 机制车道命令面 | `skills/ontology-evolution/{SKILL.md,AGENTS.md,references/commands.md}`, `skills/ontology-evolution/scripts/{evo.py,lib/{repo,proposal,sparse,worktree}.py}`, `skills/ontology-evolution/tests/python/unit/*` | 修改/创建 | 补 `accept` / `commit` / `check` 与稀疏安全模块 |
| 结构文档 | `assembly/templates/STRUCTURE.md`, `docs/DESIGN-evolution.md` | 修改 | 记录 runtime overlay 边界与命令契约（仅设计文字，不改组件类型语义） |

## Acceptance Criteria

### Agent Verification

1. [x] 设计文档在 canonical 路径通过质量门：`python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md` 退出 0；`Sub-DESIGNs` 索引与实际文件一致（6 个子设计）；三份文档 `Updated` 均为本次日期。
2. [x] 状态机行为可验证：`evo.sh new` 产出 `Stage: draft`；`advance --to accepted` 成功；`advance --to archived`（跳级）非零退出且文件未被修改；`draft→accepted→implementing→validating→archived` 逐级走通；脚本单测全绿。
3. [x] 稀疏隔离可复现：从 `.wopal` 派生 worktree 后，其 `sparse-checkout list` 与 `.wopal` 一致，范围外文件为 S 位且磁盘不可见；宿主仓库全程停留在 `main`。
4. [x] dev-flow 已无本体类型痕迹：`skills/dev-flow/` 内 `.py` 与 `.md` 文件的 `ontology-worktree` **字面**命中为 0（`__pycache__` 不计），且本体类型**符号**命中为 0（`ONTOLOGY_WORKTREE`、`ontology_worktree`、`_switch_ontology`、`_print_ontology_verification_guidance`、`get_ontology_main_repo`、`resolve_project_info`）；`ProjectType` 枚举仅剩 `standard`；dev-flow 测试套件全绿。**同时断言双向不误伤**：`assembly/templates/STRUCTURE.md` 与 `.wopal-space/STRUCTURE.md` 中的 `ontology-worktree`（空间组件类型）仍然存在，`skills/dev-flow/tests/` 中的 `space-ontology`（项目名）与 `project/ontology`（label）仍然存在。
5. [x] 技能文档明确交付终点：`SKILL.md` 写明 `space sync` / `ontology contribute` 由用户拍板，技能内无自动上行代码路径。
6. [x] 进化使者更名与边界调整：`agents/maka.md` 存在且自称 Maka、保留炼金术士设定；`agents/evolver.md` 与 LANG 旧名文件已消失；稀疏 pattern 含 `/agents/maka.md` 且不含 `evolver`；`edit` 为 `{"*": deny}` + 提案目录 `allow`；装配单 agents 名单为 `maka`；`agents/`、`skills/ontology-evolution/`、`assembly/`、`docs/DESIGN*.md` 内 `evolver` 引用为 0。
7. [x] 机制车道命令面可验证：`evo.sh accept <name>` 派生 `.worktrees/ontology-*` 隔离 worktree 并写入 Worktree/Branch/Base Commit 元数据，派生后 patterns 与 `.wopal` 一致、宿主仓库仍在 `main`；`--no-worktree` 时元数据标记快速模式且不创建 worktree；`evo.sh commit` 对范围外新文件先扩范围再提交（`--sparse` 不再是手工负担），隔离模式下提交后 space 分支已含该提交（`merge --squash`，`.wopal` status 干净、patterns 完好），且 `commit` 拒绝（a）索引含范围外文件而范围未扩（b）范围被关闭（`core.sparseCheckout=false`）且 S 位缺失——实测唯一会把删除计入索引的形态；范围开启而仅位漂移时以强告警呈现（Task 5 隔离探针实证修正）（c）稀疏配置缺失；`evo.sh check` 检出上述危险形态并以非零退出报告；全部新增单测通过。

### User Validation

#### Scenario 1: 新技能可被发现并驱动一次真实进化

- Goal: 确认 `ontology-evolution` 在真实会话中被加载，且提案驱动的流程可用
- 验证环境: 重启 ellamaka 后新开会话（技能加载链路变更须重启生效，见 `.wopal/docs/DESIGN.md` 的加载约定）
- Precondition: Task 2 已完成并提交在实施分支
- 启动命令: `wopal-dev space capability list`
- User Actions:
  1. 重启 ellamaka，新开一个会话
  2. 提出一个真实的小改进（例如给某条规则补 keywords）
  3. 执行 `evo.sh status <提案名>`，观察状态与下一步提示
- 通过判据: 提案创建于 `.wopal/docs/evolutions/`，`Stage: draft`；`evo.sh advance` 可推进到 `accepted`；dev-flow 状态机未介入
- 失败反馈: 提供 `.wopal-space/logs/wopal-plugin.log` 与 `evo.sh status` 输出

#### Scenario 2: dev-flow 不再接受本体类型

- Goal: 确认两条流程已彻底分流
- 验证环境: 同一空间，终端即可
- Precondition: Task 3 已完成
- 启动命令: `wopal-dev space capability list`
- User Actions:
  1. 在会话中要求对一项本体能力做 issue/plan 驱动的开发
  2. 观察 agent 选择的技能
- 通过判据: 无路径把本体工作交给 dev-flow；`skills/dev-flow/` 内检索 `ontology-worktree` 为 0 命中
- 失败反馈: 提供 agent 选择技能的原文与命中文件列表

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 落定本体能力进化设计

**Verification Intent**: AC#1

**Behavior**:
- `docs/DESIGN-evolution.md` 含 Capability Evolution Workflow 章节 → 定义两条车道分工、状态机 `draft → accepted → implementing → validating → archived`、稀疏隔离纪律、交付终点
- `docs/DESIGN.md` 的 Key Decisions 与 Plan Workflow Contract → 声明本体进化与代码开发分流，且两个状态机词汇互不重合
- `docs/DESIGN-capabilities.md` 的 Skill System → 两个工作流技能按对象分工
- 三份文档 `Updated` 刷新为本次日期；`Sub-DESIGNs` 索引未变（6 个）
- 文档不含过程态词汇（"迁移""不再""deprecated"一类），不描述历史

**Pre-read**: `docs/DESIGN.md`, `docs/DESIGN-evolution.md`, `docs/DESIGN-capabilities.md`

**Design**:
设计真相源是 `DESIGN-evolution.md`：它已经拥有 Self-Evolution Loop 与 Ontology Collaboration Model 两个架构关注点，机制车道是同一关注点缺失的一半，因此扩展该文档而非新建文件——新建会制造第二处权威。

写作遵循 `dev-doc-master` 的目标态规则：只描述系统是什么、谁拥有什么，不写实现步骤、不写交付进度、不写历史沿革。设计中的每条约束都要能对应一个可观察行为，作为后续 Task 的验收锚点。

**TDD**: false（文档变更；验证以质量门与内容断言完成）

**Changes**:
1. `DESIGN-evolution.md`：新增 Capability Evolution Workflow 章节（两车道分工表、状态机表、稀疏隔离三条硬约束、交付终点）
2. `DESIGN.md`：Key Decisions 增补分流决策；Plan Workflow Contract 增补本体进化状态机与出处
3. `DESIGN-capabilities.md`：Skill System 增补两技能分工说明
4. `DESIGN-evolution.md`：Evolution Workflow States 的状态表与新增 Evolution Documents 小节，声明提案落点 `docs/evolutions/` 与 `Stage` 字段
5. 三份文档刷新 `Updated`

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace && \
python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md && \
grep -q "Capability Evolution Workflow" .wopal/docs/DESIGN-evolution.md && \
grep -q "draft → accepted → implementing → validating → archived" .wopal/docs/DESIGN-evolution.md
```

> 该门按 D-07 在 canonical 路径判定。实施 worktree 内的等价位置无关检查为：`Sub-DESIGNs` 索引一致、三份 `Updated` 为本日、无绝对路径、无过程态词汇。

**Done**:
任务产出：本体能力进化流程的设计真相源落定。
实际触碰文件：`docs/DESIGN-evolution.md`（Capability Evolution Workflow 章节）、`docs/DESIGN.md`（分流决策与 Plan Workflow Contract）、`docs/DESIGN-capabilities.md`（Skill System 分工）；三份 `Updated` 刷新。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: ontology-evolution 补机制车道

**Verification Intent**: AC#2, AC#3, AC#5

**Behavior**:
- `evo.sh new "标题"` → 在 `docs/evolutions/` 生成提案文件，`Stage: draft`
- `evo.sh advance <name> --to accepted` → `Stage: accepted`，退出码 0
- `evo.sh advance <name> --to archived`（从 draft 跳级）→ 退出码非零，stderr 列出合法后继状态，文件未被修改
- `draft→accepted→implementing→validating→archived` 逐级可走通
- `evo.sh status <name>` → 打印状态、文件路径、下一步命令
- 重复 advance 到同一状态不产生重复行（幂等）
- 从 `.wopal` 派生 worktree → 继承 44 条 pattern，范围外文件 S 位、磁盘不可见
- 无任何代码路径自动执行 `space sync` / `ontology contribute`

**Pre-read**: `skills/dev-flow/scripts/plan.py`（状态字段读取与命名的参考实现）; `skills/ontology-evolution/SKILL.md`（现有只读边界）

**Design**:
机制车道刻意保持薄：单一脚本 + markdown 状态字段。不引入 Issue 层，不引入 worktree 管理命令——隔离由 git 原语按纪律执行，脚本只负责状态流转。

**状态机**：`draft → accepted → implementing → validating → archived`（D-02），承载于提案的 `Stage` 字段。评审不占状态位，仅用户明确要求时由用户主导。

**稀疏隔离纪律**（写入 `SKILL.md`，作为执行车道的硬约束）：

1. **默认隔离**：从 `.wopal`（稀疏源）派生 worktree，派生后断言其 patterns 与 `.wopal` 一致、范围外文件为 S 位。
2. **宿主仓库永不切分支**：宿主仓库承载其他空间依赖的 base capabilities，始终停在 `main`。
3. **合并在空间分支上发生**：合并动作在 worktree 或 `.wopal` 内完成，合并后空间分支即含完整树。
4. **新能力目录必须进装配**：先扩实施侧装配范围以写入内容，合并后再扩 `.wopal` 装配并物化。
5. **S 位禁忌**：永不批量清除 skip-worktree 位；范围调整一律走扩展装配。
6. **验证 = 重启后观察**：加载链路变更以重启 ellamaka 后的加载结果为准。
7. **交付是用户终点**：`space sync` 与 `ontology contribute` 由用户逐次拍板。

**快速模式**：仅 typo、bug-fix、用户明确指定的小范围改动允许在 `.wopal` 空间分支直接小步提交；判定不清时默认走隔离模式。

**边界划分**：Evolver 出《进化方案》（只读提案）；Wopal 编排与规范提交；Fae 实施落盘；Rook 审查守门。与既有 `/wopal:evolve`、`/wopal:distill`、`wopal/ontology-maintain` 命令的分工在 `SKILL.md` 中写清，避免职责重叠。

**TDD**: true

**Changes**:
1. RED：为 `evo.sh` 写失败测试（new / status / advance 的合法与非法跃迁、幂等、状态字段只被脚本写入）
2. GREEN：实现状态机脚本，使测试全绿
3. REFACTOR：抽出发行字段解析与状态校验的公共函数
4. 改写 `SKILL.md`：定位从 evolver 独占只读扩展为语义车道 + 机制车道，补稀疏纪律七条、快速模式判据、角色分工与交付终点

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace/.worktrees/wopal-space-ontology-evolution-skill-split/skills/ontology-evolution && python3 -m pytest tests/ -q
```

**Done**:
任务产出：提案驱动、含稀疏隔离纪律与交付终点的完整 `ontology-evolution` 技能。
实际触碰文件：
- `skills/ontology-evolution/SKILL.md`（改写：语义车道 + 机制车道，稀疏纪律七条，快速模式，按车道划界的 Boundary，扩展 description）
- `skills/ontology-evolution/AGENTS.md`（新增：技能开发规范与测试规则）
- `skills/ontology-evolution/references/commands.md`（新增：对外命令契约）
- `skills/ontology-evolution/scripts/evo.sh`（新增：CLI 入口，exec 转发并透传退出码）
- `skills/ontology-evolution/scripts/evo.py`（新增：new/status/advance/archive 实现与提案模板）
- `skills/ontology-evolution/scripts/lib/{__init__,repo,proposal}.py`（新增：仓库根解析、状态机与 `Stage` 字段读写）
- `skills/ontology-evolution/tests/python/{__init__.py,support/{__init__,bootstrap}.py,unit/{__init__,test_proposal_state,test_repo_root,test_cli_behavior}.py}`（新增：39 个测试）
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: dev-flow 摘除 ontology-worktree 类型

**Verification Intent**: AC#4

**Behavior**:
- `skills/dev-flow/` 内 `.py` 与 `.md` 的 `ontology-worktree` 字面命中为 0
- 本体类型相关的**全部符号**归零：`ONTOLOGY_WORKTREE`、`ontology_worktree`、`_switch_ontology`、`_print_ontology_verification_guidance`，以及仅供本体分支使用的辅助函数（如 `get_ontology_main_repo`、`resolve_project_info`、`_get_wopal_repo_name`）——删除本体分支后这些成为死代码，必须一并清除
- `ProjectType` 枚举仅剩 `standard`；本体专用解析路径与标记移除
- 本体 worktree 的创建、切换、清理、合并判定分支全部移除；`verify_switch` 仅保留标准路径
- dev-flow 全量单测通过（标准流程零回归）
- dev-flow 文档不再出现本体类型与对应验证场景
- **反向陷阱**：本体类型专属标识符必须清除，但以下**同名不同物**的标识符必须原样保留，不得误删——`space-ontology`（项目名，出现在测试 fixture 与计划路径中）、`project/ontology`（Issue label）、`Target Project: ontology`（项目名）。判据是语义归属，不是字符串相似。
- 结构文档中的 `ontology-worktree`（空间组件类型）保持存在

**Pre-read**: `skills/dev-flow/scripts/lib/project.py`, `skills/dev-flow/scripts/lib/git.py:470-540`, `skills/dev-flow/scripts/commands/approve.py`, `skills/dev-flow/scripts/lib/workspace.py:93`

**Design**:
删除顺序是先移植、后删除：Task 2 已把稀疏实施纪律写入 `ontology-evolution`，本 Task 才动手拆。保留 standard 流程全部行为。

**判定口径必须用符号而非字面**：本体的实现分支大量使用枚举符号 `ProjectType.ONTOLOGY_WORKTREE.value` 而非字面量 `"ontology-worktree"`（`approve.py` 有 11 处、`verify.py`、`issue.py` 亦然）。只按字面 grep 会漏判，留下活的本体分支。完成判据必须同时覆盖字面与符号两个口径，外加"本体辅助函数已无调用点"。

**逐文件要点**：
- `lib/project.py` / `scripts/plan.py`：`ProjectType` 降为单值 `standard`；`plan.py` 的 `resolve_project_info`/`_get_wopal_repo_name` 若仅服务本体类型则删除
- `lib/git.py`：`check_branch_merged` 去掉本体集成分支推导，回落为 `main`
- `lib/workspace.py`：`get_ontology_main_repo` 在 dev-flow 内已无调用点后删除
- `commands/approve.py`：5 处本体分支（worktree 基线解析、worktree 路径推导、unmerged 检查豁免、worktree 创建、base_commit 推导）全部删除
- `commands/verify.py` / `commands/complete.py`：删除本体 final_commit 推导与 `_print_ontology_verification_guidance` 及其分派
- `commands/verify_switch.py`：删除 `_switch_ontology` 及 `run_verify_switch` 的本体分派
- `commands/archive.py`：删除本体 worktree/branch 清理支路
- `commands/issue.py`：删除本体类型 Issue body 元数据注入
- `lib/worktree.py`：`project_type` 字段注释去本体类型

**测试策略**：删除本体专用断言与用例而非整文件；标准流程用例必须原样通过，作为零回归证据。`test_verify_switch.py` 的 `TestOntologySwitch` 类、`_make_ontology_ctx`、以及标记 `def test_ontology_*` 的用例整体删除；`test_approve.py`、`test_git_semantics.py`、`test_verify.py`、`test_plan_cmd.py`、`test_push_race_recovery.py`、`test_worktree_context.py` 中的本体用例/插件删除。`space-ontology` 项目名相关的测试（`test_plan_link_contract.py`、`test_plan_path_migration.py`、`test_project_resolver.py`、`test_submit.py`、`test_sync_*`）**不属于本体类型**，必须保留。

**TDD**: true

**Changes**:
1. RED：调整测试——移除本体类型用例，保留标准用例，作为删除目标的失败基线
2. GREEN：逐文件摘除本体分支，使测试全绿、命中归零
3. REFACTOR：删除本体分支遗留的死代码（辅助函数、常量、注释）；同步 `skills/space-master/references/agents-md-maintenance.md` 的类型归属表述

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace/.worktrees/wopal-space-ontology-evolution-skill-split && \
test -z "$(grep -rl 'ontology-worktree' skills/dev-flow --include='*.py' --include='*.md' 2>/dev/null)" && \
test -z "$(grep -rlE 'ONTOLOGY_WORKTREE|ontology_worktree|_switch_ontology|_print_ontology_verification_guidance' skills/dev-flow --include='*.py' 2>/dev/null)" && \
test -z "$(grep -rlE 'get_ontology_main_repo|resolve_project_info' skills/dev-flow --include='*.py' 2>/dev/null)" && \
test -n "$(grep -l 'ontology-worktree' assembly/templates/STRUCTURE.md)" && \
test -n "$(grep -rl 'space-ontology' skills/dev-flow/tests --include='*.py' 2>/dev/null)" && \
cd skills/dev-flow && python3 -m pytest tests/python/ -q
```
> 前两条断言本体类型字面与符号归零；第三条断言本体辅助函数已无调用；后两条断言结构文档与反向保留项（`space-ontology` 项目名）未被误伤。


**Done**:
任务产出：dev-flow 回归纯代码项目语义，本体开发路径唯一化。
实际触碰文件：
- `skills/dev-flow/scripts/lib/project.py`（`ProjectType` 降为单值 `standard`，删除 `ONTOLOGY_WORKTREE`）
- `skills/dev-flow/scripts/plan.py`（`ProjectType` 降为单值；删除 `_get_wopal_repo_name`、`resolve_project_info` 及其导入）
- `skills/dev-flow/scripts/lib/workspace.py`（删除 `get_ontology_main_repo` 及其头部说明）
- `skills/dev-flow/scripts/lib/git.py`（`check_branch_merged` 移除本体集成分支推导，回落 `main`）
- `skills/dev-flow/scripts/lib/worktree.py`（`project_type` 字段注释去本体类型）
- `skills/dev-flow/scripts/commands/approve.py`（删除 5 处本体分支与相关导入）
- `skills/dev-flow/scripts/commands/verify.py`（删除本体 final_commit 推导与本体残留清理块）
- `skills/dev-flow/scripts/commands/complete.py`（删除 `_print_ontology_verification_guidance` 及分派）
- `skills/dev-flow/scripts/commands/verify_switch.py`（删除 `_switch_ontology` 及本体分派，仅留标准路径）
- `skills/dev-flow/scripts/commands/archive.py`（删除本体 worktree/branch 清理支路）
- `skills/dev-flow/scripts/commands/issue.py`（删除本体类型 Issue body 元数据注入）
- `skills/dev-flow/scripts/commands/plan.py`（`project_path`/`project_type` 参数注释去本体类型）
- `skills/dev-flow/tests/python/unit/{test_verify_switch,test_approve,test_git_semantics,test_verify,test_plan_cmd,test_push_race_recovery,test_worktree_context,test_issue_body_file}.py`（删除本体用例/夹具/断言，保留全部标准用例）
- `skills/dev-flow/{SKILL.md,SKILL.zh-CN.md}`（场景 2 与分支铁律去本体类型）
- `skills/dev-flow/references/{commands.md,plan-guide.md,plan-guide.zh-CN.md}`（去本体项目类型描述与映射行）
- `skills/space-master/references/agents-md-maintenance.md`（类型归属表述改为组件类型 + 指向 `ontology-evolution`）
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: 进化使者更名 maka 与只读边界调整

**Verification Intent**: AC#6

**Behavior**:
- `agents/maka.md` 承载原 evolver 的语义车道职责，自称改为 **Maka**，保留"炼金术士"角色设定（巫师世界的炼金师，把原始经验炼成活的能力）
- `agents/evolver.md` 不再存在；`docs/LANG/zh-CN/agents/maka.md` 为对应中文镜像
- 稀疏装配 pattern 由 `/agents/evolver.md` 变为 `/agents/maka.md`，且不再残留旧 pattern
- maka 的 `edit` 权限由 `deny` 改为**按路径限定放开**：`{"*": "deny", ".wopal/docs/evolutions/*": "allow"}`——可编辑提案，不可改能力资产本身
- 装配单 `assembly/archetypes/coding.yaml` 的 agents 名单更新为 `maka`
- 设计文档名单与技能文档引用全部同步，工作区内 `evolver` 引用为 0

**Pre-read**: `agents/evolver.md`, `assembly/archetypes/coding.yaml`, `docs/DESIGN-capabilities.md:22`, `skills/ontology-evolution/SKILL.md`

**Design**:
更名是「文件重命名 + 装配 pattern 同步」的联合操作，两者必须一起变——agent 名取自文件名（ellamaka `entry-name.ts` 取 basename），而装配 pattern 是精确文件路径。

隔离探针实证（临时仓库，复刻真机非 cone + 文件型 pattern 形态）：
- **`git mv --sparse` 可绕过稀疏顺序陷阱**：`git mv` 默认拒绝更新稀疏范围外的索引条目，加 `--sparse` 后成功（exit 0，`status` 显示 `R` 重命名，物体层完整）。这比"先扩 pattern 再 mv"更少一次状态变更。
- **`/docs/` 是目录级 pattern**，`docs/LANG/**` 天然在范围内，中文镜像无需新增 pattern。唯一需改的 pattern 是精确文件型的 `/agents/evolver.md`。
- pattern 变更属装配范围调整，走 `git sparse-checkout add` 扩展，**禁止**批量清除 skip-worktree 位。

权限调整的边界判据：`edit` 的 pattern 匹配**相对空间根**的路径（ellamaka `tool/edit.ts` 以 `path.relative(instance.worktree, filePath)` 构造 pattern）。空间根本体含 `.wopal/` 目录，故提案路径须带 `.wopal/` 前缀；只放开提案目录，保住"提议权与实施权分离"这条核心约束。设计文档 `DESIGN-capabilities.md` 中 `edit: deny` 的描述同步改为精确边界表述。

**TDD**: false（agent 定义、装配清单与设计文档，无逻辑代码；验证以文件与 pattern 断言完成）

**Changes**:
1. `git mv --sparse agents/evolver.md agents/maka.md`；同法处理 `docs/LANG/zh-CN/agents/evolver.md` → `maka.md`
2. `git sparse-checkout add /agents/maka.md`；随后移除已失效的 `/agents/evolver.md` pattern
3. `agents/maka.md`：自称 Evolver → Maka；保留炼金术士设定；`edit` 改为 `{"*": deny, ".wopal/docs/evolutions/*": allow}`
4. `docs/LANG/zh-CN/agents/maka.md`：同步中文自称与权限
5. `assembly/archetypes/coding.yaml`：agents 名单 `evolver` → `maka`
6. 引用同步：`skills/ontology-evolution/{SKILL.md,AGENTS.md}`（语义车道署名）、`docs/DESIGN.md`、`docs/DESIGN-capabilities.md`、`docs/DESIGN-evolution.md`、`docs/DESIGN-assembly.md`

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace/.worktrees/wopal-space-ontology-evolution-skill-split && \
test ! -e agents/evolver.md && \
test -f agents/maka.md && \
test -f docs/LANG/zh-CN/agents/maka.md && \
test -z "$(grep -rl 'evolver' agents/ skills/ontology-evolution/ assembly/ docs/DESIGN*.md 2>/dev/null)" && \
grep -q '^  - maka$' assembly/archetypes/coding.yaml && \
git sparse-checkout list | grep -qx '/agents/maka.md' && \
! git sparse-checkout list | grep -q 'evolver' && \
grep -q 'Maka' agents/maka.md && \
grep -q '炼金术士' docs/LANG/zh-CN/agents/maka.md
```

**Done**:
任务产出：进化使者命名本地化（maka），只读边界按提案范围精确放开。
实际触碰文件：
- `agents/evolver.md` → `agents/maka.md`（重命名：自称 Maka，保留炼金术士设定；`edit` 改为 `{"*": deny, ".wopal/docs/evolutions/*": allow}`；边界措辞由 "Read & Propose Only" 精确化为 "Propose Only"）
- `docs/LANG/zh-CN/agents/evolver.md` → `docs/LANG/zh-CN/agents/maka.md`（同步中文自称、权限与边界）
- `assembly/archetypes/coding.yaml`（agents 名单 `evolver` → `maka`）
- `skills/ontology-evolution/{SKILL.md,AGENTS.md}`（语义车道署名 Evolver → Maka；边界改为 Propose Only）
- `docs/{DESIGN,DESIGN-capabilities,DESIGN-evolution,DESIGN-assembly}.md`（名单与署名同步；`edit: deny` 描述改为仅放开提案目录）
- 稀疏 pattern：`/agents/evolver.md` → `/agents/maka.md`（44 条不变，`git sparse-checkout set --no-cone` 应用）
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 5: 机制车道补实施闭环（accept / commit / check）

**Verification Intent**: AC#7

**Behavior**:
- `evo.sh accept <name>`：校验当前 Stage 为 `draft` 或 `accepted` → 派生隔离 worktree → 写元数据 → 推进至 `accepted`（若尚未）
- `evo.sh accept <name> --no-worktree`：不建 worktree，元数据标记快速模式
- `evo.sh commit <name> -m <msg>`：稀疏安全提交（扩范围 → 暂存 → 提交 → 集成）
- `evo.sh check <name>`：体检并输出结论，危险形态非零退出
- 危险形态一律**拒绝且不改文件**（与状态机同样的原子性契约）

**Pre-read**: `skills/ontology-evolution/scripts/{evo.py,lib/proposal.py,lib/repo.py}`；`skills/dev-flow/scripts/lib/{worktree,git}.py`（对齐既有实现）；`docs/DESIGN-evolution.md`（Isolation Discipline）

**Design**:

**① 为什么需要这三个命令**

现状是"状态机齐备、实施闭环空缺"：`accepted → implementing` 推进时**什么都不发生**——没有 worktree、没有元数据、没有提交通道。本次实施的真实过程暴露了全部代价：

- 手工 `git worktree add` + 手工敲 patterns 断言
- 元数据（Worktree/Branch/Base Commit）手填，rebase 后失效 3 次
- 手工 `git mv --sparse` / `git add --sparse`，靠探针试错才知道必须加 `--sparse`
- 用户面对 VSCode 的稀疏报错无从下手
- 集成回 space 分支无路径，被 `git push .` 拒绝后才找到 `merge --squash`

**② `accept`：唯一创建 worktree 的入口**

对齐 dev-flow 的 `approve` 语义（`commands/approve.py` + `lib/worktree.py:write_worktree_context`）：

```
accept <name> [--no-worktree]
  1. 校验 Stage ∈ {draft, accepted}
  2. 默认模式：
     - 从 .wopal 派生 git worktree add .worktrees/ontology-<slug> -b ontology-<slug> space/<name>
       （从稀疏源派生 → 继承 patterns 与 S 位；实测 44 条逐行一致）
     - 断言派生结果的 sparse-checkout list 与 .wopal 一致
     - 写元数据：Worktree / Branch / Base Commit(space 分支 HEAD) / Mode: isolated
  3. --no-worktree：
     - 不创建 worktree，写 Mode: quick，元数据 Worktree 留空
  4. 提交元数据变更（提案文件）
```

命名规范（D-14）：目录 `<space>/.worktrees/ontology-<slug>`，分支 `ontology-<slug>`。

**③ `commit`：稀疏安全的提交通道**

这是本 Task 的核心。职责是让"用户改本体"这件事**不可能误伤能力池**。

```
commit <name> -m <msg>
  前置检查（任一不通过即拒绝，零副作用）：
    A. 稀疏配置完好：core.sparseCheckout=true 且 patterns 非空
       （缺失 → 拒绝，提示状态损坏）
    B. 无范围外删除：
       git diff --cached --diff-filter=D 中的路径若不在 patterns 覆盖内
       → 拒绝（这是 S 位丢失导致的能力池删除假象）
       → 补充阈值告警：D 数量 > 20 时无论范围一律强告警（9/20 为 212）
    C. 无未扩范围的索引条目：
       索引中新增路径若不在 patterns 覆盖内 → 自动扩范围（见下），不拒绝
  执行：
    1. 对索引/工作区中不在范围的新路径：git sparse-checkout add /<path>/ 或 /<path>
       （先扩范围，再让普通 git 命令生效 —— 避免 --sparse 造成的"未来被 reapply 吞掉"）
    2. git add <paths>  （范围已扩，无需 --sparse）
    3. git commit -m <msg>
    4. 隔离模式：集成回 space 分支
       进入 .wopal（其 HEAD 即 space 分支）执行 git merge --squash <feature-branch>
       → git commit
       → 断言 .wopal status 干净、patterns 完好
       快速模式：无需集成（已直接提交在 space 分支）
    5. 回填提案元数据（Final Commit 等）
```

**为什么是"先扩范围"而不是"加 `--sparse`"**：探针实证——`git add --sparse` 只强行把文件塞进索引，**不扩范围**；此后任何一次范围重算（`sync` 的 `applySparsePatterns`）都会把它从磁盘移走（S 位、静默消失）。先扩范围则文件真正进入装配范围，`reapply` 后依然可见。`--sparse` 是应急补丁，先扩范围才是正确解。

**为什么集成必须走 `.wopal` 内 `merge --squash`**（D-10 实证）：

| 方案 | 实测结果 |
|---|---|
| `git push . HEAD:space/<branch>` | 被拒（target 已在 `.wopal` 检出） |
| `git update-ref refs/heads/space/... <sha>` | ref 改了，但 `.wopal` 立即出现 `D`/`M` 不一致——**9/20 同类签名** |
| `.wopal` 内 `merge --squash` + commit | status 空、patterns 完好、树完整 |

**④ `check`：提案与稀疏体检**

```
check <name>
  提案格式：Metadata 必备字段存在且取值合法（Stage ∈ 状态集、Type、Created）
            Task 结构：每 Task 含 Verification Intent / Behavior / Verify / Done
            占位符残留检测（`<...>` 未替换）
  稀疏状态：patterns 非空、配置完好、S 位与 patterns 一致
            索引与稀疏范围一致性（范围外条目数）
            未集成提交检测（隔离模式：feature 分支是否领先 space 分支）
  退出码：有问题非零，输出分类清单
```

**⑤ 与 runtime overlay 的边界**（D-11 / D-12）

本技能**不写** overlay。空间临时增删由 CLI 承载；`commit` 只记录自身需要的元数据（分支、基线），不碰 `space-meta.json`。命令契约预留接口形态，等 CLI 侧就位后对接。

**TDD**: true

**Changes**:
1. RED：为 `accept` / `commit` / `check` 写失败测试（含所有危险形态的拒绝路径与原子性断言）
2. GREEN：实现 `scripts/lib/sparse.py`（配置读取、范围判定、S 位检查、扩范围）、`scripts/lib/worktree.py`（派生与集成），在 `evo.py` 注册三个子命令
3. REFACTOR：抽出危险形态判定为公共函数（`commit` 与 `check` 共用）
4. 改写 `SKILL.md`：机制车道命令表、隔离/快速两模式的实施流程、`commit` 为唯一写工作区入口、overlay 边界说明
5. 更新 `references/commands.md` 与 `AGENTS.md`（开发规范新增稀疏模块约定）

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace/.worktrees/wopal-space-ontology-evolution-skill-split/skills/ontology-evolution && python3 -m pytest tests/ -q
```

**Done**:
任务产出：机制车道具备完整实施闭环，稀疏边界由命令守住。
实际触碰文件：
- `skills/ontology-evolution/scripts/lib/sparse.py`（新增：稀疏读取、`preflight` 危险形态判定、`widen` 动态扩范围）
- `skills/ontology-evolution/scripts/lib/worktree.py`（新增：隔离 worktree 派生、隔离断言、`.wopal` 内 squash 集成）
- `skills/ontology-evolution/scripts/lib/proposal.py`（新增：通用元数据字段读写 `get_field` / `set_field`）
- `skills/ontology-evolution/scripts/evo.py`（新增 `accept` / `commit` / `integrate` / `check` 子命令；提案与状态记录的落库收敛到 `_sync_record`）
- `skills/ontology-evolution/tests/python/unit/test_sparse_safety.py`（新增：机制车道安全闭环行为测试）
- `skills/ontology-evolution/{SKILL.md,AGENTS.md,references/commands.md}`（补机制车道命令面、稀疏安全不变量与两种模式的实施流程）

> **设计在实施中被实证修正（5 处）**。初版方案若干判据建立在未验证推断上，全部由本轮隔离探针实测推翻并改为实测形态：
> 1. **"批量 D 阈值"判据删除**。原计划按 `git status` 的 ` D` 计数拒绝提交；实测删除 25 个 S 位文件后计数为 0 —— 该判据永不可触达，属伪安全网。改为直接判定"范围与 S 位是否一致"。
> 2. **`core.sparseCheckout` 检查改为取布尔值**。实测 `git sparse-checkout disable` 保留 key 并写入 `false`（worktree 中 `git config --unset` 返回 5，根本清不掉），只判存在性会把已损毁的结账读成"已启用"。
> 3. **S 位读取改用 `ls-files --debug` 的 flags**，不用 `-t` 的标签字母：实测范围内条目带上 skip-worktree 后 `-t` 仍打印 `H`。`CE_SKIP_WORKTREE` 为 `0x4000`，范围外条目另带 `0x40000000`，故用掩码判定。
> 4. **危险形态严重度按实测分级**（三态表记录在 `references/commands.md`）：范围开、位被清 → `status` 报 ` D`，但 `git add -A` 仍不暂存任何东西（git 自身兜底）；范围关、位被清 → 同一命令真的把删除计入索引。故"位漂移"是警告，**"范围被关"才是不可逆关口**。初版文案把前者说成即时毁池，属 overclaim，已按实测改写。
> 5. **隔离断言由"pattern 相等"改为"超集"**。派生 worktree 会随新增能力目录自行扩范围，"比空间看得多"是进化进行中的正常形态，丢 pattern 才是故障；原等值断言会把正常的进化过程判成违约。
>
> **集成路径发现并修复两处静默失效缺陷**：
> - `merge --squash` 在空间范围未扩时，会把新增能力目录记为**无磁盘副本的 skip-worktree 条目**——已提交、已列出、运行时永远看不见（能力静默不加载）。`integrate` 现在先采用特性分支的范围再合并，合并后 `reapply` 物化。
> - 提案在空间分支与派生 worktree 各有一份副本。`advance` / `archive` 只改本地副本会把 `.wopal` 留脏，直接堵死下一次 `integrate`（其前置检查拒绝脏工作区）。现由 `_sync_record` 统一落库两份，归档的删除与新路径一并记录。
>
> **验证实证**：74 个单测全绿；另在临时仓库复刻真机布局（宿主 `main` + `.wopal` 非 cone 稀疏 + 派生 worktree）跑通全链路 `new → accept → commit（自动扩范围）→ advance → integrate → validating → archived → archive`，全程 `.wopal` 与派生 worktree `status` 均干净、宿主停在 `main`、新增能力目录已物化到磁盘、范围外文件保持 S 位；五类拒绝路径（稀疏关闭 / 位漂移 / 非法跃迁 / 未 accept 提交 / 快速模式集成）均非零退出且零副作用。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 6: 交付决策与路由收口

**Verification Intent**: AC#5

**Behavior**:
- 汇总本次改动清单（文件 + 提交 SHA）供用户决策
- 用户明确同意后才执行 `space sync`（上行 local main）；未同意则保持分支状态
- 上游贡献仅在用户明确要求时执行
- 路由判据写入两个技能的触发面与 `space-master` 路由说明

**Pre-read**: `projects/wopal-cli/src/lib/space-sync.ts`

**Design**:
本 Task 是人的终点而非机器终点，技能不得内置自动上行。执行 sync 前先干跑预览（`wopal-dev space sync` 默认 dry-run），确认范围仅含本次改动再 `--confirm`。同时把"看对象选技能"写入两个技能与 space-master 路由，作为防止误选的持久机制。

**TDD**: false（决策与路由文本收口）

**Changes**:
1. 汇总改动清单与候选上行范围，提交用户决策
2. 用户确认后执行 sync（或按用户要求保持分支）
3. 写入路由判据并提交文档变更

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace && wopal-dev space sync    # dry-run 预览，确认范围仅含本次改动
```

**Done**:
任务产出：交付决策闭环，路由判据固化。
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | Wopal 直接执行 | 无 | 设计决策属统筹输出，草稿已在实施分支完成，剩余为断言与提交 |
| 2 | Task 2 | fae | Task 1 | 脚本实现 + 技能文档改写，属实现工作 |
| 3 | Task 3 | fae | Task 2（先移植后删除） | 跨 19 源文件的类型摘除，需测试护航 |
| 4 | Task 4 | Wopal 直接执行 | Task 3 | 单文件重命名 + 装配 pattern 同步 + 权限精调，改动面小但涉及稀疏派生状态 |
| 5 | Task 5 | fae | Task 2 | 机制车道命令面实现，含稀疏模块与全部单元测试 |
| 6 | Task 6 | Wopal + 用户 | Task 3, Task 4, Task 5 | 交付决策是人类闸门，不可委派 |

Wave 2 与 Wave 3 是强依赖（先移植后删除），必须串行，不得并行拆分给不同 fae，避免上下文丢失导致稀疏纪律与删除顺序错位。

Task 4 由 Wopal 直接执行而非委派：改动面小（2 个文件重命名 + 3 处配置/文档同步），但涉及稀疏派生状态与装配 pattern 的操作顺序，属最高风险点，由掌握完整实证的 Wopal 亲手处理更稳妥。

Task 5 与 Task 4 串行：它消费 Task 4 建立的命名规范，且改动同一批文件（`SKILL.md`、`AGENTS.md`）。Task 5 委派 fae 时须附上本提案记录的全部实证（`--sparse` 陷阱、`push` / `update-ref` 禁用、`merge --squash` 路径、9/20 形态判据），避免其重新试错。
