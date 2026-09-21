# refactor-ontology-evolution-skill-split

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-21
- **Status**: proposal
- **Worktree**: `.worktrees/wopal-space-ontology-evolution-skill-split`
- **Branch**: `wopal-space-ontology-evolution-skill-split`
- **Base Commit**: `49da492`（派生点：`space/wopal-workspace` HEAD）
- **Final Commit**: (done 时记录)

> **Bootstrap 说明**：本提案是本体进化流程的第一件产物，也是第一个落在 `docs/evolutions/` 的提案。设计已先行落在 `docs/DESIGN-evolution.md` 的 Capability Evolution Workflow 章节，本提案按该设计实施。流程的状态推进脚本尚未存在（正是本提案的交付物之一），因此由用户批准后按 Task 顺序执行，产出提交在 `wopal-space-ontology-evolution-skill-split` 分支上。

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

让本体能力进化成为每个空间类型的常驻能力：按 `docs/DESIGN-evolution.md` 落定本体能力进化流程的设计，为 `ontology-evolution` 技能补齐机制车道（提案状态机、稀疏隔离纪律、交付终点），并把 `ontology-worktree` 类型从 `dev-flow` 中摘除，使两条流程各有唯一入口。

## Technical Context

### Architecture Context

设计真相源已经落定在 `.wopal/docs/DESIGN-evolution.md`（本次先行的设计变更），本 Plan 是它的实施载体。

现状由三条事实构成：

1. **设计已定义、机制层空缺**。`docs/DESIGN-evolution.md` 的 Capability Evolution Workflow 定义了语义车道（Evolver 出《进化方案》）与机制车道（Wopal 编排、Fae 实施、Rook 守门）的分工、状态机 `proposal → approved → executing → verifying → done`、稀疏隔离纪律与交付终点。该技能当前池中只有 `SKILL.md`（evolver 独占的只读蒸馏技能），机制车道尚无载体。
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

**参考资料**：
- `.wopal/docs/DESIGN-evolution.md`（设计真相源）
- `projects/wopal-cli/src/lib/space-capability.ts`（capability add 的落点与再物化语义）
- `projects/wopal-cli/src/lib/space-sync.ts`（sync 上行/下行与游离文件纳管语义）

### Key Decisions

- D-01: **本体进化与代码开发分流**。`ontology-evolution` 承接本体能力进化；`dev-flow` 摘除 `ontology-worktree` 类型，回归纯代码项目语义。判据从"选技能"改为"看对象"：`projects/` 下的代码仓库 → dev-flow；空间本体能力 → ontology-evolution。割掉重叠区，从机制上消除误选。
- D-02: **状态机使用互不重合的词汇**：`proposal → approved → executing → verifying → done`。默认不带 Issue 载体，评审仅用户明确要求时进入。沿用 dev-flow 的旧状态名会造成"两个 plan 语义"混淆，故刻意区分。
- D-03: **默认隔离模式 = 从 `.wopal` 派生稀疏 worktree**（继承 patterns，边界天然等于空间确权范围）。**快速模式** = 在 `.wopal` 空间分支直接小步提交，仅限 typo、bug-fix 与用户明确指定的小范围文件改动。空间分支本身即是对 local main 的隔离边界。
- D-04: **交付是用户决定的人类终点**：进化产物先落空间分支，是否 `space sync` 上行 local main、是否 `ontology contribute` 上游，由用户逐次拍板；技能不内置自动上行。
- D-05: **不新建引擎或共享内核**。机制车道需要的基础设施只有 markdown 状态字段流转与 git 提交（Issue 层默认不参与），属一两百行量级；复刻一份到本技能比抽象跨技能引擎更便宜，也避免引入无人认领的第三类产物。
- D-06: **新能力目录必须进装配**。进化若新增能力目录，该目录须在实施前纳入实施侧装配范围，合并后再扩展 `.wopal` 装配并重新物化，否则验证者看不到新能力。
- D-07: **文档质量门按 canonical 路径判定**。`verify-docset.py` 的跨仓库相对链接检查只在 `.wopal/docs` 成立；在实施 worktree 内以该门判定文档缺陷是无效判据。文档任务的验证分两段：worktree 内跑位置无关检查（`Sub-DESIGNs` 索引、`Updated` 日期、绝对路径、过程态词汇），`canonical` 路径的完整门在合入后判定。

### Key Interfaces

**`ontology-evolution` 的机制车道入口（脚本契约）**：

```
evo.sh new <title>                    创建提案（docs/evolutions/<name>.md，Status: proposal）
evo.sh status <name|path>             打印状态、文件位置、下一步
evo.sh advance <name> --to <state>    状态推进（校验合法跃迁，非法即拒绝）
evo.sh archive <name>                 归档到 docs/evolutions/archived/
```

- 状态集合（有序）：`proposal → approved → executing → verifying → done`
- 非法跃迁（跳级、倒退）返回非零退出码，stderr 列出合法后继状态。
- 状态写入仅通过脚本；Agent 不得手改 `Status` 字段。
- Issue 层不在契约内（默认无 Issue；用户明确要求时才由 CLI 侧介入）。
- 脚本路径与调用方式在实施时按技能目录约定确定，对外契约以上表为准。

## In Scope

- 落定本体能力进化的设计：`docs/DESIGN.md`、`docs/DESIGN-evolution.md`、`docs/DESIGN-capabilities.md`。
- 为 `ontology-evolution` 补机制车道：状态机脚本、稀疏隔离纪律、交付终点，并改写其 `SKILL.md`（从 evolver 独占只读扩展为语义车道 + 机制车道）。
- 摘除 `dev-flow` 的 `ontology-worktree` 类型：脚本、测试、文档全部清理。
- 固化技能路由判据：本体能力 → ontology-evolution；代码仓库 → dev-flow。

## Out of Scope

- 不再执行能力装配（已于本次会话完成，属既有工作区事实）。
- 不做 GAPS 差距分析，不新增 GAPS 条目（按用户决定）。
- 不改 `wopal-cli` 的 `space sync` / `space capability` 实现。
- 不新增共享引擎或公共内核（D-05）。
- 不改动空间组件类型语义的结构文档（见术语红线）。
- 不清理 `.wopal` 中与本议题无关的既有未跟踪文件（`plugins/wopal-plugin/pnpm-lock.yaml`、`pnpm-workspace.yaml`）。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 设计文档 | `docs/DESIGN.md`, `docs/DESIGN-evolution.md`, `docs/DESIGN-capabilities.md` | 修改 | 落定进化流程设计（真相源） |
| ontology-evolution | `skills/ontology-evolution/SKILL.md`, `skills/ontology-evolution/scripts/` | 修改/创建 | 机制车道（状态机 + 稀疏纪律 + 交付终点） |
| dev-flow 脚本（10） | `skills/dev-flow/scripts/{plan.py,lib/{project,git,worktree}.py,commands/{plan,approve,complete,verify,verify_switch,archive,issue}.py}` | 修改 | 摘除 dev-flow 的 ontology-worktree Project Type |
| dev-flow 文档（5） | `skills/dev-flow/{SKILL.md,SKILL.zh-CN.md,references/{commands.md,plan-guide.md,plan-guide.zh-CN.md}}` | 修改 | 移除本体类型说明与验证场景 |
| dev-flow 测试（7） | `skills/dev-flow/tests/python/unit/{test_approve,test_git_semantics,test_plan_cmd,test_push_race_recovery,test_verify,test_verify_switch,test_worktree_context}.py` | 修改 | 移除本体类型断言，保留标准流程回归 |
| space-master 路由（1 行） | `skills/space-master/references/agents-md-maintenance.md:190` | 修改 | 该行以 dev-flow 的 Project Type 语境描述类型归属，改为指向新技能 |

## Acceptance Criteria

### Agent Verification

1. [ ] 设计文档在 canonical 路径通过质量门：`python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md` 退出 0；`Sub-DESIGNs` 索引与实际文件一致（6 个子设计）；三份文档 `Updated` 均为本次日期。
2. [ ] 状态机行为可验证：`evo.sh new` 产出 `Status: proposal`；`advance --to approved` 成功；`advance --to done`（跳级）非零退出且文件未被修改；`proposal→approved→executing→verifying→done` 逐级走通；脚本单测全绿。
3. [ ] 稀疏隔离可复现：从 `.wopal` 派生 worktree 后，其 `sparse-checkout list` 与 `.wopal` 一致，范围外文件为 S 位且磁盘不可见；宿主仓库全程停留在 `main`。
4. [ ] dev-flow 已无本体类型痕迹：`skills/dev-flow/` 内 `.py` 与 `.md` 文件的 `ontology-worktree` 命中为 0（`__pycache__` 不计）；`ProjectType` 枚举仅剩 `standard`；dev-flow 测试套件全绿。**同时断言结构文档未被误改**：`assembly/templates/STRUCTURE.md` 与 `.wopal-space/STRUCTURE.md` 中的 `ontology-worktree`（空间组件类型）仍然存在。
5. [ ] 技能文档明确交付终点：`SKILL.md` 写明 `space sync` / `ontology contribute` 由用户拍板，技能内无自动上行代码路径。

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
- 通过判据: 提案创建于 `.wopal/docs/evolutions/`，`Status: proposal`；`evo.sh advance` 可推进到 `approved`；dev-flow 状态机未介入
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
- `docs/DESIGN-evolution.md` 含 Capability Evolution Workflow 章节 → 定义两条车道分工、状态机 `proposal → approved → executing → verifying → done`、稀疏隔离纪律、交付终点
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
4. `DESIGN-evolution.md`：Evolution Workflow States 的 `proposal` 行与新增 Evolution Documents 小节，声明提案落点 `docs/evolutions/`
5. 三份文档刷新 `Updated`

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace && \
python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md && \
grep -q "Capability Evolution Workflow" .wopal/docs/DESIGN-evolution.md && \
grep -q "proposal → approved → executing → verifying → done" .wopal/docs/DESIGN-evolution.md
```

> 该门按 D-07 在 canonical 路径判定。实施 worktree 内的等价位置无关检查为：`Sub-DESIGNs` 索引一致、三份 `Updated` 为本日、无绝对路径、无过程态词汇。

**Done**:
任务产出：本体能力进化流程的设计真相源落定。
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: ontology-evolution 补机制车道

**Verification Intent**: AC#2, AC#3, AC#5

**Behavior**:
- `evo.sh new "标题"` → 在 `docs/evolutions/` 生成提案文件，`Status: proposal`
- `evo.sh advance <name> --to approved` → `Status: approved`，退出码 0
- `evo.sh advance <name> --to done`（从 proposal 跳级）→ 退出码非零，stderr 列出合法后继状态，文件未被修改
- `proposal→approved→executing→verifying→done` 逐级可走通
- `evo.sh status <name>` → 打印状态、文件路径、下一步命令
- 重复 advance 到同一状态不产生重复行（幂等）
- 从 `.wopal` 派生 worktree → 继承 44 条 pattern，范围外文件 S 位、磁盘不可见
- 无任何代码路径自动执行 `space sync` / `ontology contribute`

**Pre-read**: `skills/dev-flow/scripts/plan.py`（状态字段读取与命名的参考实现）; `skills/ontology-evolution/SKILL.md`（现有只读边界）

**Design**:
机制车道刻意保持薄：单一脚本 + markdown 状态字段。不引入 Issue 层，不引入 worktree 管理命令——隔离由 git 原语按纪律执行，脚本只负责状态流转。

**状态机**：`proposal → approved → executing → verifying → done`（D-02）。评审不占状态位，仅用户明确要求时由用户主导。

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
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: dev-flow 摘除 ontology-worktree 类型

**Verification Intent**: AC#4

**Behavior**:
- `skills/dev-flow/` 内 `.py` 与 `.md` 的 `ontology-worktree` 命中为 0
- `ProjectType` 枚举仅剩 `standard`；本体专用解析路径与标记移除
- 本体 worktree 的创建、切换、清理、合并判定分支全部移除；`verify_switch` 仅保留标准路径
- dev-flow 全量单测通过（标准流程零回归）
- dev-flow 文档不再出现本体类型与对应验证场景
- 结构文档中的 `ontology-worktree`（空间组件类型）保持存在

**Pre-read**: `skills/dev-flow/scripts/lib/project.py`, `skills/dev-flow/scripts/lib/git.py:470-540`

**Design**:
删除顺序是先移植、后删除：Task 2 已把稀疏实施纪律写入 `ontology-evolution`，本 Task 才动手拆。逐文件处理 19 处源文件命中，保留 standard 流程全部行为。`ProjectType` 枚举降为单值（`lib/project.py` 与 `scripts/plan.py` 两处定义）；`check_branch_merged` 去掉本体集成分支推导，回落为 `main`；`commands/issue.py` 删除本体类型的 Issue body 元数据注入；`commands/verify_switch.py` 删除 `_switch_ontology`。

测试策略：删除本体专用断言而非整文件；标准流程用例必须原样通过，作为零回归证据。

**TDD**: true

**Changes**:
1. RED：调整测试——移除本体类型用例，保留标准用例，作为删除目标的失败基线
2. GREEN：逐文件摘除本体分支，使测试全绿、命中归零
3. REFACTOR：清理残留常量与注释；同步 `skills/space-master/references/agents-md-maintenance.md:190` 的类型归属表述

**Verify**:
```bash
cd /Volumes/U500G/coding/wopal-workspace/.worktrees/wopal-space-ontology-evolution-skill-split && \
test -z "$(grep -rl 'ontology-worktree' skills/dev-flow --include='*.py' --include='*.md' 2>/dev/null)" && \
test -n "$(grep -l 'ontology-worktree' assembly/templates/STRUCTURE.md)" && \
cd skills/dev-flow && python3 -m pytest tests/python/ -q
```

**Done**:
任务产出：dev-flow 回归纯代码项目语义，本体开发路径唯一化。
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: 交付决策与路由收口

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
| 4 | Task 4 | Wopal + 用户 | Task 2, Task 3 | 交付决策是人类闸门，不可委派 |

Wave 2 与 Wave 3 是强依赖（先移植后删除），必须串行，不得并行拆分给不同 fae，避免上下文丢失导致稀疏纪律与删除顺序错位。
