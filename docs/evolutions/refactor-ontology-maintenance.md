# refactor-ontology-maintenance

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-25
- **Stage**: accepted
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-refactor-ontology-maintenance
- **Branch**: ontology-refactor-ontology-maintenance
- **Base Commit**: 3413d885e87d38fe40217d8325e2c3b6fb0ae039
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

本体资产的全部维护面单点收编到 `ontology-evolution` 技能；`space-master` 收窄为路由指引；`wopal/ontology-maintain` 命令薄化为技能触发器；机制脚本在 CLI `space evo` 命令族完整交付后退役（CLI 交付由配套 dev-flow Plan `feature-cli-space-evo-state-machine-migration` 承载）。

## Technical Context

### Architecture Context

现状（证据先行）：

1. **`space-master` 持有旧命令面的维护协议**：`SKILL.md` 的 Ontology Maintenance 章节与 `references/ontology-maintenance.md` 承载完整操作规范，但停留在旧模型——无 `--local` 双通道 / `localState` / 上行闸，"Sync Gates" 强制审批门控叙述与定稿口径冲突，status 解读矩阵是旧输出结构，contribute 缺隔离 worktree / `--resume` / `--abort` 机制。
2. **`ontology-evolution` 持有进化工作流但缺维护面**：SKILL.md + scripts/（evo.py 2629 行 + lib/ 946 行）+ references/commands.md；SKILL.md description 仍以 `evo.sh` 指称机制（"proposal state machine via evo.sh"）；Boundary 引用的 `wopal/ontology-maintain` 本身是旧模型。
3. **`wopal/ontology-maintain` 命令引用已不存在的事物**：`wopal ontology apply`（CLI 无此命令）、`DESIGN.md §6.9.2`（章节号不存在）、`upstream-sync.md §4`（该参考文档已更名）、type/* 分支晋升模型（`DESIGN-evolution.md` 明文不设 type/* 层级）。
4. **设计真相源已定稿（2026-09-25）**：`.wopal/docs/DESIGN-capabilities.md`（收编归属）、`.wopal/docs/DESIGN-evolution.md`（命令表 + `space evo` 唯一操作面）、`projects/wopal-cli/docs/DESIGN-evolution.md`（机制契约 + 迁移分批交付）。
5. **机制操作面现状**：CLI 演进分支仅 `commit` / `integrate` 已落地（`src/commands/space.ts` evoGroupDef，help 注明状态机命令 "land in later tasks"）；技能脚本为过渡实现，两实现已漂移（fix 退役、isolated commit、realign）。

### Research Findings

- 收编的最小爆破面是文档与命令层：CLI 契约文档已定稿，无需新增设计；space-master 的 AGENTS.md / README / Skills 维护章节不属于本体维护面，不随本次收编。
- `space-master` 存在 zh-CN 镜像（SKILL.zh-CN.md），收编必须双语同步；`ontology-evolution` 无镜像，单语即可。
- 机制脚本退役必须等 CLI 命令族完整交付并入 main，否则技能失能——退役动作与 CLI 交付解耦为两步，本提案只绑定「CLI 完整交付后」的退役承诺与文档切换，具体删除动作在 CLI 合入后按 quick 模式执行。
- 前例：2026-06-12 提案 #161 曾重写 space-master 的 ontology 协作文档（clone 模型）；本次是其在新装配模型上的第二轮回写，旧 reference 文件整体退役而非第三次修补。
- **提案名是承重件，不只是标签**：`accept` 以提案 stem 派生隔离分支与 worktree 目录（`evo.py:485` → `worktree.slugify` → `branch_name`，前缀 `ontology-`）。实测本提案原名 66 chars 派生出 69 字符分支 `ontology-consolidate-ontology-maintenance-into-the-ontology-evol-20a1`（中途腰斩 + 4 位哈希兜底）。dev-flow 早已把分支总长约束在 55（`plan-guide.md:342-356`），evo 路径无等价约束。
- **两实现共有的既存缺陷（本提案不修，另案）**：`worktree.py:38,73-76` 与 CLI `src/lib/space-evo-accept.ts:77,129-131` 都把 55 上限加在 **slug** 上、之后才拼 9 字符前缀 `ontology-`（`space-evo-accept.ts:80`），而 `space-evo-accept.ts:76` 注释自述为「**Branch-name** length cap」——意图与实现不符，最终分支可达 69 chars。命名契约（slug ≤ 20）已使新增提案的分支最长 29 chars，该缺陷对存量长名与绕过规范的输入仍然潜伏。
- **池内存量**：归档提案名普遍 74–89 chars，active/backlog 9 条中 5 条超 40 chars——规范化是池级需求，非单点整改。

**参考资料**：
- `.wopal/docs/DESIGN-capabilities.md`
- `.wopal/docs/DESIGN-evolution.md`
- `projects/wopal-cli/docs/DESIGN-evolution.md`

### Key Decisions

- D-01: **收编归属**——本体维护操作协议（`ontology update` / `space sync` / `ontology contribute`、能力装配增删、status 解读、执行口径）作为 `ontology-evolution` 技能的新增 Maintenance 章节；技能是唯一规范单点，进化与维护共用同一命令面叙述。
- D-02: **space-master 保留纯路由**——Skill Usage Scenarios 表与本体段改写为路由指针（本体维护/进化 → `ontology-evolution`）；删除 `references/ontology-maintenance.md`；AGENTS.md / README / Skills 生命周期章节保留不动。
- D-03: **命令薄化**——`wopal/ontology-maintain.md` 重写为 ≤30 行薄触发器：description + 加载 `ontology-evolution` 技能 + 按 `$ARGUMENTS` 传入焦点；全部决策表与 CLI 用法删除。
- D-04: **机制退役两步走**——步骤一（本提案）：SKILL.md / references/commands.md 标注脚本为过渡实现、以 CLI `space evo` 命令族为唯一操作面目标态；步骤二（CLI 命令族合入 main 后，quick 模式）：scripts/ 目录删除、SKILL.md 机制章节改写为 `space evo` 调用协议。双实现不得长期并行。
- D-05: **执行口径按定稿**——CLI 默认 dry-run 预览，agent 按用户意图直接执行 `--confirm`，不设审批门控；`ontology contribute` 是唯一需用户逐次拍板的动作；scope determination / 主题化 PR 规则保留（内容按新 CLI 参数面改写）。
- D-06: **wopal.md 指针更新**——Mission 与 Conduct 中"本体进化方法由 space-master 承载"的表述改为 `ontology-evolution`；意图不清时先加载 space-master 的路由规则保持不变。
- D-07: **提案命名契约落点为模板，不做机器强制**——契约写入 `templates/proposal.md`：该模板是技能脚本与 CLI `space evo new` 的**共同骨架源**（CLI `src/lib/space-evo-state.ts:90` 从本体侧解析该路径，helpText 明文「no inlined copy in the CLI」），故单点落笔即双端继承，无需两处重复维护。**拒绝超限 slug 的机器强制不在本提案内**：该逻辑属 CLI 机制面，而本提案 Out of Scope 已明文排除 wopal-cli 仓库（D-04 亦规定机制归 CLI），强行纳入会同时破坏本提案边界与配套 Plan `feature-cli-space-evo-state-machine-migration` 的验收范围——留待另案。命名规范本体对齐 dev-flow `references/plan-guide.md` 命名规则段（`<type>-<slug>`，slug = 1–2 核心名词 / kebab-case / ≤ 20 chars，丢弃动词与冠词）。

### Key Interfaces

**`wopal/ontology-maintain` 命令契约（薄化后）**：

```markdown
description: maintain ontology instance and collaboration
行为：加载 ontology-evolution 技能，按 $ARGUMENTS（focus: update|contribute|sync|status，空 = 全量评估）执行技能的 Maintenance 协议。命令自身不承载任何规范。
```

**`ontology-evolution` 技能章节结构**：Semantic lane（不变）→ Mechanism lane（补过渡实现标注 + CLI 唯一操作面指针）→ Maintenance Protocols（新增：六命令表、status 解读、contribute scope/PR 规则、双通道与上行闸、执行口径）→ Boundary（更新：`wopal/ontology-maintain` 薄触发、机制归 CLI、迁移期脚本说明）。

**space-master 路由条目**：Skill Usage Scenarios 增补"本体维护与进化 → `ontology-evolution`"行；Ontology Maintenance 段压缩为路由说明（≤15 行），不含任何 CLI 用法示例。

## In Scope

- `ontology-evolution` SKILL.md：机制章节过渡标注 + Maintenance Protocols 新增 + Boundary 更新
- `ontology-evolution` references/commands.md：顶部过渡实现标注与 CLI 契约指针
- `wopal/ontology-maintain.md` 薄化重写
- `space-master` SKILL.md / SKILL.zh-CN.md：本体段改写为路由；删除 `references/ontology-maintenance.md`
- `agents/wopal.md`：两处技能指针更新

## Out of Scope

- CLI `space evo` 状态机命令交付——配套 dev-flow Plan `feature-cli-space-evo-state-machine-migration` 承载，本提案不碰 wopal-cli 仓库
- scripts/（evo.py / lib/）删除——CLI 命令族合入 main 后按 D-04 步骤二执行（quick 模式即可，无设计面）
- space-master 的 AGENTS.md / README / Skills 维护章节——非本体维护面
- `dev-flow` / `agents-collab` 等其他技能
- `docs/DESIGN-evolution.md` 等设计文档——收编表述已在设计定稿提交（1887130）中完成

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| ontology-evolution skill | `skills/ontology-evolution/SKILL.md` | 修改 | 机制过渡标注 + Maintenance 章节 + Boundary + 命名契约指针 |
| ontology-evolution skill | `skills/ontology-evolution/templates/proposal.md` | 修改 | 提案命名契约（双端共享骨架源） |
| ontology-evolution skill | `skills/ontology-evolution/references/commands.md` | 修改 | 过渡实现标注 + CLI 契约指针 + `new` 命名约束 |
| maintenance command | `commands/wopal/ontology-maintain.md` | 重写 | 薄触发器 |
| space-master skill | `skills/space-master/SKILL.md`, `skills/space-master/SKILL.zh-CN.md` | 修改 | 本体段 → 路由 |
| space-master skill | `skills/space-master/references/ontology-maintenance.md` | 删除 | 规范已收编 |
| wopal agent | `agents/wopal.md` | 修改 | 技能指针 |

## Acceptance Criteria

### Agent Verification

1. [ ] 收编单点性：`rg -l "ontology (update|contribute)" .wopal/skills/space-master/` 零命中（space-master 不再持有维护协议）；`rg -c "space sync" .wopal/skills/ontology-evolution/SKILL.md` ≥ 1（维护协议在技能内）。
2. [ ] 命令薄化：`wc -l` 报告 `commands/wopal/ontology-maintain.md` ≤ 30 行；文件含 "ontology-evolution" 加载指令；不含 "ontology apply"、"6.9.2"、"upstream-sync.md" 任何一处。
3. [ ] 路由保留：`rg -c "ontology-evolution" .wopal/skills/space-master/SKILL.md` ≥ 1；`SKILL.zh-CN.md` 同步含对应路由条目；两文件的本体段均无 `--include` / `--confirm` 用法示例。
4. [ ] 机制过渡标注：SKILL.md 含 "space evo" 与过渡实现表述；`references/commands.md` 顶部含过渡状态说明与 `projects/wopal-cli/docs/DESIGN-evolution.md` 指针。
5. [ ] 结构契约不破坏：`python3 -m pytest tests/python -q` 全绿（提案结构契约脚本未变更）。
6. [ ] agent 指针：`agents/wopal.md` 中 "ontology capability evolution" 相关表述指向 `ontology-evolution`，无残留 "carried by the `space-master` skill"。
7. [ ] 提案命名契约落地（可判定）：`rg -q "20 chars" skills/ontology-evolution/templates/proposal.md` 命中（slug 长度上限）；`rg -q "type>-<slug" skills/ontology-evolution/templates/proposal.md` 命中（命名结构）；`rg -qE "^\| .*\| .*\|$" skills/ontology-evolution/templates/proposal.md` 在命名契约段内至少命中 1 行（verbose→lean 对照表非空）；`rg -q "refactor-ontology-maintenance" skills/ontology-evolution/templates/proposal.md` 命中（对照表以本提案为反例）；`rg -q "templates/proposal.md" skills/ontology-evolution/SKILL.md` 命中（`new` 行指向模板契约）；`rg -qE "slug.{0,20}(20|noun)" skills/ontology-evolution/references/commands.md` 命中（`new` 条目补约束）。

### User Validation

#### Scenario 1: /ontology-maintain 触发技能化工作流

- Goal: 确认维护命令已从静态决策表变为技能驱动工作流。
- 验证环境: 本空间 + ellamaka 重启加载。
- Precondition: 本提案已集成到 `space/wopal-workspace` 分支并经 `space sync` 物化；ellamaka 已重启。
- 启动命令: 重启 ellamaka 后在会话输入 `/ontology-maintain status`
- User Actions:
  1. 观察命令回执：是否为加载 `ontology-evolution` 技能后的工作流输出
  2. 对照旧形态：回执不应再出现静态优先级决策表（Priority 1-6 表格）与 `wopal ontology apply` 引用
- 通过判据: 回执含实况数据（`wopal ontology status` / `space status` 输出的解读），且决策建议以技能 Maintenance 协议口径给出（执行口径 = 定稿口径）；AC#1–AC#7 断言全部通过。
- 失败反馈: 命令完整输出 + `git -C .wopal log --oneline -3`。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: ontology-evolution 技能收编改写

**Verification Intent**: AC#1, AC#4, AC#5

**Behavior**:
- SKILL.md Mechanism lane 章节含过渡实现标注（脚本为迁移期实现；唯一操作面 = CLI `space evo`，契约指针 `projects/wopal-cli/docs/DESIGN-evolution.md`）
- SKILL.md 新增 Maintenance Protocols 章节：六命令表（space status/sync/capability、ontology capability list/update/contribute、space evo）、status 解读要点（Downstream/Upstream flow、localState 清单）、contribute scope determination 与主题化 PR 规则、双通道与上行闸、执行口径（D-05）
- SKILL.md Boundary 更新：`wopal/ontology-maintain` 定位为薄触发；机制归 CLI；迁移期脚本说明
- references/commands.md 顶部标注过渡实现状态 + CLI 契约指针
- 结构契约测试保持全绿

**Pre-read**: `.wopal/docs/DESIGN-capabilities.md`；`.wopal/docs/DESIGN-evolution.md`；`projects/wopal-cli/docs/DESIGN-evolution.md`；现 `skills/ontology-evolution/SKILL.md` 全文

**Design**: 在现有 SKILL.md 上增补与定点改写，不重写语义车道内容（已对齐）。Maintenance 章节内容以设计定稿为准，禁止从旧 `ontology-maintenance.md` 搬运旧命令面内容。机制章节不改写为 CLI 用法（那是 D-04 步骤二的事），只加标注与指针。

**TDD**: false

**Changes**:
1. 运行结构契约测试确认基线全绿
2. 按上述行为改写 SKILL.md 与 references/commands.md
3. AC#1 / AC#4 的 grep 断言逐一通过

**Verify**: `python3 -m pytest tests/python -q` 全绿；`rg -n "space evo|过渡" skills/ontology-evolution/SKILL.md` 命中

**Done**:
任务产出：技能文档收编改写完成，维护协议成为技能章节。
实际触碰文件：（实施完成后由实施 Agent 回填）
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 2: 命令薄化、space-master 路由与 agent 指针

**Verification Intent**: AC#1, AC#2, AC#3, AC#5, AC#6

**Behavior**:
- `commands/wopal/ontology-maintain.md` ≤ 30 行，含技能加载指令与 `$ARGUMENTS` 焦点透传，无决策表与 CLI 用法
- `skills/space-master/SKILL.md`：Skill Usage Scenarios 增补 ontology-evolution 路由行；Ontology Maintenance 段压缩为路由说明（≤15 行、无 CLI 用法）；删除 `references/ontology-maintenance.md`
- `skills/space-master/SKILL.zh-CN.md` 同步同语义改写
- `agents/wopal.md` 两处指针更新（Mission 的本体进化承载技能；Conduct 的技能加载顺序说明保留 space-master 为路由入口）
- 结构契约测试保持全绿

**Pre-read**: 现 `commands/wopal/ontology-maintain.md`；`skills/space-master/SKILL.md` 与 `SKILL.zh-CN.md`；`agents/wopal.md`

**Design**: 薄命令保留 frontmatter description 与参数说明，正文只写"加载技能、传焦点、按技能协议执行"。space-master 路由段说明"本体维护与进化请求 → 加载 ontology-evolution"，并保留 AGENTS.md / README / Skills 章节不动。zh-CN 与英文逐段对应，不引入语义差。

**TDD**: false

**Changes**:
1. 重写 ontology-maintain.md
2. 改写 space-master 双语本体段，删除旧 reference 文件
3. 更新 wopal.md 指针
4. AC#2 / AC#3 / AC#6 断言逐一通过

**Verify**: `rg -l "ontology (update|contribute)" skills/space-master/` 零命中；`wc -l commands/wopal/ontology-maintain.md` ≤ 30；`python3 -m pytest tests/python -q` 全绿

**Done**:
任务产出：维护入口三角（技能 / 命令 / 路由）职责清晰，旧协议副本清零。
实际触碰文件：（实施完成后由实施 Agent 回填）
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 3: 提案命名契约落模板与双端文档

**Verification Intent**: AC#7, AC#5

**Behavior**:
- `templates/proposal.md` 顶部（`# {name}` 之后）新增提案命名契约注释块：结构 `<type>-<slug>`；`type` 取标准值全拼；**slug = 1–2 个核心名词、kebab-case、≤ 20 chars**；丢弃动词短语与冠词、禁止照抄标题；名称为承重件（`accept` 由 stem 派生 `ontology-<slug>` 分支与 worktree 目录，冗长名会产出不可读分支）
- 契约内含 **verbose→lean 对照表**，反例取本提案原名 `consolidate-ontology-maintenance-into-the-ontology-evolution-skill` → `refactor-ontology-maintenance`（本提案自身已于 accept 前改名，是契约的第一个实例）
- `SKILL.md` 命令表中 `new` 行注明命名契约并指向 `templates/proposal.md`（只加指针，不复制契约全文）
- `references/commands.md` 的 `new` 条目在既有派生规则旁补 slug 约束（≤ 20 chars / 1–2 核心名词），不与既有描述冲突
- 结构契约测试保持全绿；提案结构契约（`evo.py:102-121` 必需章节 + Task 六元素）不被破坏

**Pre-read**: `.wopal/skills/dev-flow/references/plan-guide.md` 命名规则段（310–356 行，含分支命名约束）；现 `skills/ontology-evolution/templates/proposal.md`；`skills/ontology-evolution/SKILL.md` 命令表段；`references/commands.md:24-36`

**Design**: 契约**只写在 `templates/proposal.md` 一处**（D-07）——该模板是技能脚本 `evo.py` 与 CLI `space evo new` 的共同骨架源，CLI 从本体侧解析该路径且不内嵌副本，因此单点落笔即双端继承；SKILL.md 与 references 只做指针与就近提示，杜绝三处复制导致漂移。契约以 HTML 注释承载（与模板既有作者指引同风格，不渲染进产出文件）。**不做机器强制**：拒绝超限 slug 属 CLI 机制面，本提案 Out Scope 已排除 wopal-cli 仓库，另案处理——实施时不得擅自改 `evo.py::_slugify` 或 CLI `space evo new` 加校验。注意 `_structure_problems` 扫描时会剥离代码围栏（`evo.py:125-132`），契约正文须为散文段落，对照表用表格而非围栏。

**TDD**: false

**Changes**:
1. 运行 `python3 -m pytest tests/python -q` 确认基线全绿
2. 在 `templates/proposal.md` 顶部加命名契约注释块（结构 + slug 规则 + 承重件说明 + 对照表）
3. `SKILL.md` 的 `new` 命令行加契约指针；`references/commands.md` 的 `new` 条目补 slug 约束
4. AC#7 的 grep 断言逐一通过；确认未触碰 `evo.py` 与 wopal-cli 仓库

**Verify**: `python3 -m pytest tests/python -q` 全绿；`rg -n "20 chars|type>-<slug|refactor-ontology-maintenance" skills/ontology-evolution/templates/proposal.md` 三者均命中；`rg -n "templates/proposal.md" skills/ontology-evolution/SKILL.md` 命中；`git -C .wopal diff --name-only <base>` 不含 `scripts/`

**Done**:
任务产出：提案命名规范成为模板级契约，新增提案双端自动继承；本提案自身已改名并作为首个实例。
实际触碰文件：（实施完成后由实施 Agent 回填）
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 文档批量改写，文件集与 Task 2 无交集 |
| 1 | Task 2 | fae | 无 | 同域文档工作，建议同一 fae 会话顺序执行以复用上下文 |
| 1 | Task 3 | fae | 无 | 同属 ontology-evolution 技能文档面，与 Task 1 共享 SKILL.md 上下文，**必须同一 fae 会话顺序执行**——并发改同一文件必冲突 |

> Wave 1 三条同批：Task 1 与 Task 3 都改 `skills/ontology-evolution/SKILL.md`，须串行；本提案 Complexity 仍为 Medium，未因新增 Task 上调（文档层改写，无代码面）。

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。
