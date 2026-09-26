# refactor-ontology-maintenance

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-25
- **Stage**: validating
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-refactor-ontology-maintenance
- **Branch**: ontology-refactor-ontology-maintenance
- **Base Commit**: 3413d885e87d38fe40217d8325e2c3b6fb0ae039
- **Final Commit**: 25e7e41243ac64150fccde976504d0d586d1e358

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

本体资产的全部维护面单点收编到 `ontology-evolution` 技能；`space-master` 收窄为路由指引；`wopal/ontology-maintain` 命令薄化为技能触发器；机制脚本在 CLI `space evo` 命令族完整交付后退役（CLI 交付由配套 dev-flow Plan `feature-cli-space-evo-state-machine-migration` 承载）。

## Technical Context

### Architecture Context

现状（证据先行）：

1. **`space-master` 持有旧命令面的维护协议**：`SKILL.md` 的 Ontology Maintenance 章节与 `references/ontology-maintenance.md` 承载完整操作规范，但停留在旧模型——无 `--local` 双通道 / `localState` / 上行闸，"Sync Gates" 强制审批门控叙述与定稿口径冲突，status 解读矩阵是旧输出结构，contribute 缺隔离 worktree / `--resume` / `--abort` 机制。
2. **`ontology-evolution` 持有进化工作流但缺维护面**：SKILL.md + scripts/（evo.py 1683 行 + lib/ 946 行，合计 2629 行）+ references/commands.md；SKILL.md description 仍以 `evo.sh` 指称机制（"proposal state machine via evo.sh"）；Boundary 引用的 `wopal/ontology-maintain` 本身是旧模型。
3. **`wopal/ontology-maintain` 命令引用已不存在的事物**：`wopal ontology apply`（CLI 无此命令）、`DESIGN.md §6.9.2`（章节号不存在）、`upstream-sync.md §4`（该参考文档已更名）、type/* 分支晋升模型（`DESIGN-evolution.md` 明文不设 type/* 层级）。
4. **设计真相源已定稿（2026-09-25）**：`.wopal/docs/DESIGN-capabilities.md`（收编归属）、`.wopal/docs/DESIGN-evolution.md`（命令表 + `space evo` 唯一操作面）、`projects/wopal-cli/docs/DESIGN-evolution.md`（机制契约 + 迁移分批交付）。
5. **机制操作面现状（2026-09-26 更新）**：CLI `space evo` 八命令**已全部合入 main 并交付**（`wopal-cli` v0.3.24，合并提交 `9f6f424`）——`new` / `status` / `check` / `advance` / `accept` / `commit` / `integrate` / `archive`，注册于 `src/commands/space.ts` evoGroupDef。原「仅 `commit` / `integrate` 已落地、状态机命令 land in later tasks」的记载已过时。两实现的三处漂移（fix 退役、isolated commit、realign）已在迁移中收敛，**CLI 成为机制车道唯一操作面**——这使 D-04 的文档切换具备前置条件。技能脚本自此成为待退役实体。

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
- D-04: **机制文档完全切换到 CLI，脚本实体重行后删**——本提案内，`SKILL.md` / `references/commands.md` / `AGENTS.md` 三个说明文件**全部改写为 `wopal space evo` 调用协议，任何说明文件不再出现 `evo.sh` / `evo.py` / `bash scripts/...` 任何一处引用**（用户 2026-09-26 指令：文档先行，为下一步彻底删除脚本铺路）。**`fix` 的处置是设计决议而非能力缺口**：前序 CLI Plan `20260925-enhance-wopal-cli-capability-local-channel-evo-command-ergonomics-upload-gate` 的 **D-04** 决议「`space evo fix` 退役」——即时提交并入 `space evo commit`（省略 `<name>` 即 instant 模式），**不保留别名或 shim**，`SPACE_EVO_FIX_*` 错误码并入 commit 族，shadow 登记职责移交 `capability remove --local`；其 D-05 定下 commit「提案上下文可省、即时模式显式」的参数面。配套迁移 Plan `20260926-feature-cli-space-evo-state-machine-migration` 的 **D-07** 追认「fix 不迁移……**不新增 `space evo fix`**」，并有可执行断言（`wopal space evo fix` 须报 unknown command，见其 UAT 步骤 10）。因此文档须把 instant mode 表述为**设计指定路径**，不得写成「因缺少 fix 而退求其次」，并明示**不得重新引入独立 fix 命令或 shim**——否则会被后续 agent 读成待补缺口而好心实现，直接违反该断言。（注：本提案 D-04 与前序 CLI Plan D-04 编号撞名，跨文档引用必须限定 Plan 名。）**脚本实体（`evo.py` 1683 行 + `lib/` 946 行）与 `tests/python/` 4 个测试文件的删除是下一步独立 quick 模式操作**（无设计面，不进提案生命周期），本提案不删——给仍在跑的代码删测试是错的。改完后存在一个**刻意容忍的短暂不一致**：脚本与测试仍可运行，但已无任何文档描述它们；下一步删除落地即消失。
- D-05: **执行口径按定稿**——CLI 默认 dry-run 预览，agent 按用户意图直接执行 `--confirm`，不设审批门控；`ontology contribute` 是唯一需用户逐次拍板的动作；scope determination / 主题化 PR 规则保留（内容按新 CLI 参数面改写）。
- D-06: **wopal.md 指针更新**——Mission 与 Conduct 中"本体进化方法由 space-master 承载"的表述改为 `ontology-evolution`；意图不清时先加载 space-master 的路由规则保持不变。
- D-07: **提案命名契约落点为模板，不做机器强制**——契约写入 `templates/proposal.md`：该模板是技能脚本与 CLI `space evo new` 的**共同骨架源**（CLI `src/lib/space-evo-state.ts:90` 从本体侧解析该路径，helpText 明文「no inlined copy in the CLI」），故单点落笔即双端继承，无需两处重复维护。**拒绝超限 slug 的机器强制不在本提案内**：该逻辑属 CLI 机制面，而本提案 Out of Scope 已明文排除 wopal-cli 仓库（D-04 亦规定机制归 CLI），强行纳入会同时破坏本提案边界与配套 Plan `feature-cli-space-evo-state-machine-migration` 的验收范围——留待另案。命名规范本体对齐 dev-flow `references/plan-guide.md` 命名规则段（`<type>-<slug>`，slug = 1–2 核心名词 / kebab-case / ≤ 20 chars，丢弃动词与冠词）。

### Key Interfaces

**`wopal/ontology-maintain` 命令契约（薄化后）**：

```markdown
description: maintain ontology instance and collaboration
行为：加载 ontology-evolution 技能，按 $ARGUMENTS（focus: update|contribute|sync|status，空 = 全量评估）执行技能的 Maintenance 协议。命令自身不承载任何规范。
```

**`ontology-evolution` 技能章节结构**：Semantic lane（不变）→ Mechanism lane（**完全改写为 `wopal space evo` 八命令调用协议**，零脚本命令残留）→ Maintenance Protocols（新增：六命令表、status 解读、contribute scope/PR 规则、双通道与上行闸、执行口径）→ Boundary（更新：`wopal/ontology-maintain` 薄触发、机制归 CLI、缺陷修复走 `space evo commit` instant 模式）。

**`evo.sh` → `wopal space evo` 命令映射（D-04 硬约束）**：

| 旧脚本命令 | CLI 对应物 | 备注 |
|---|---|---|
| `evo.sh new` | `wopal space evo new` | 骨架仍取本体侧 `templates/proposal.md` |
| `evo.sh status` | `wopal space evo status` | 具名给详情，省名列全部 |
| `evo.sh check` | `wopal space evo check` | |
| `evo.sh advance --to <s>` | `wopal space evo advance --to <s>` | |
| `evo.sh accept [--no-worktree]` | `wopal space evo accept [--no-worktree]` | |
| `evo.sh commit` | `wopal space evo commit` | isolated 模式在隔离 worktree 内提交 |
| `evo.sh integrate` | `wopal space evo integrate` | |
| `evo.sh archive` | `wopal space evo archive` | |
| **`evo.sh fix -m <m> (--paths/--all)`** | **`wopal space evo commit -m <m> (--paths/--all)`** | **设计决议退役**（前序 CLI Plan D-04 + 迁移 Plan D-07）：instant 模式是指定路径，**不新增 `space evo fix`、不保留别名或 shim**；shadow 登记移交 `capability remove --local` |

**space-master 路由条目**：Skill Usage Scenarios 增补"本体维护与进化 → `ontology-evolution`"行；Ontology Maintenance 段压缩为路由说明（≤15 行），不含任何 CLI 用法示例。

## In Scope

- `ontology-evolution` SKILL.md：机制章节**完全改写为 `wopal space evo` 调用协议**（非过渡标注）+ Maintenance Protocols 新增 + Boundary 更新
- `ontology-evolution` references/commands.md：**整篇改写为 `wopal space evo` 命令参考**，脚本命令零残留
- `ontology-evolution` AGENTS.md：清除全部 `evo.sh` / `evo.py` / `scripts/` 引用，保留仍为真的部分（结构契约、D-NN 纪律、双车道边界、缺陷即时修复改指 instant 模式）
- `ontology-evolution` templates/proposal.md：提案命名契约（Task 3）
- `wopal/ontology-maintain.md` 薄化重写
- `space-master` SKILL.md / SKILL.zh-CN.md：本体段改写为路由；删除 `references/ontology-maintenance.md`
- `agents/wopal.md`：两处技能指针更新

## Out of Scope

- CLI `space evo` 状态机命令交付——配套 dev-flow Plan `feature-cli-space-evo-state-machine-migration` 承载，本提案不碰 wopal-cli 仓库
- **scripts/（evo.py / lib/）实体的删除**——按 D-04 属下一步独立 quick 模式操作；本提案只切文档，脚本留存
- **tests/python/ 4 个测试文件的删除**——与脚本实体同批删除；脚本仍在则测试须留存
- space-master 的 AGENTS.md / README / Skills 维护章节——非本体维护面
- `dev-flow` / `agents-collab` 等其他技能
- `docs/DESIGN-evolution.md` 等设计文档——收编表述已在设计定稿提交（1887130）中完成

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| ontology-evolution skill | `skills/ontology-evolution/SKILL.md` | 修改 | 机制章节完全改写为 `space evo` + Maintenance 章节 + Boundary + 命名契约指针 |
| ontology-evolution skill | `skills/ontology-evolution/references/commands.md` | 重写 | 整篇改为 `wopal space evo` 命令参考（保留稀疏安全与语料断言知识）+ `new` 命名约束 |
| ontology-evolution skill | `skills/ontology-evolution/AGENTS.md` | 修改 | 清除脚本架构描述，保留仍为真的规则 |
| ontology-evolution skill | `skills/ontology-evolution/templates/proposal.md` | 修改 | 提案命名契约（双端共享骨架源） |
| maintenance command | `commands/wopal/ontology-maintain.md` | 重写 | 薄触发器 |
| space-master skill | `skills/space-master/SKILL.md`, `skills/space-master/SKILL.zh-CN.md` | 修改 | 本体段 → 路由 |
| space-master skill | `skills/space-master/references/ontology-maintenance.md` | 删除 | 规范已收编 |
| wopal agent | `agents/wopal.md` | 修改 | 技能指针 |

## Acceptance Criteria

### Agent Verification

1. [x] 收编单点性：`rg -l "ontology (update|contribute)" skills/space-master/` 零命中（space-master 不再持有维护协议）；`rg -c "space sync" skills/ontology-evolution/SKILL.md` ≥ 1（维护协议在技能内）。**路径基准**：断言以**隔离 worktree 根**为基准（`skills/...`），因为被验对象是隔离分支上的实现；`.wopal/skills/...` 的空间副本在 `integrate` 前仍是集成前内容，**须于 integrate 后以空间根形式复验一次**。
2. [x] 命令薄化：`wc -l` 报告 `commands/wopal/ontology-maintain.md` ≤ 30 行；文件含 "ontology-evolution" 加载指令；不含 "ontology apply"、"6.9.2"、"upstream-sync.md" 任何一处。
3. [x] 路由保留：`rg -c "ontology-evolution" skills/space-master/SKILL.md` ≥ 1（实测 5）；`SKILL.zh-CN.md` 同步含对应路由条目（实测 5，两镜像均 110 行、结构对齐）；两文件的本体段均无 `--include` / `--confirm` 用法示例（实测 0）。路径基准同 AC#1。
4. [x] **机制文档完全切换到 CLI（D-04 核心判据）**：`rg -c 'evo\.sh|evo\.py' skills/ontology-evolution/SKILL.md skills/ontology-evolution/references/commands.md skills/ontology-evolution/AGENTS.md` 三文件**全部零命中**；`rg -c 'bash scripts/' skills/ontology-evolution/{SKILL.md,references/commands.md,AGENTS.md}` 零命中；`rg -c 'wopal space evo' skills/ontology-evolution/SKILL.md` ≥ 1（机制章节以 CLI 命令面叙述）；`rg -q 'space evo commit' skills/ontology-evolution/SKILL.md` 命中（缺陷即时修复指向 instant 模式，且 `rg -q -i 'no separate .fix. command|not.*reintroduc|retired' skills/ontology-evolution/SKILL.md` 须命中——文档必须记录「`fix` 为设计决议退役、不得重新引入独立 fix 命令或 shim」，否则会被读成待补缺口）；`rg -c 'wopal space evo' skills/ontology-evolution/references/commands.md` ≥ 8（整篇命令参考已切换，覆盖八条子命令）；`rg -q 'add --sparse|corpus assertion' skills/ontology-evolution/references/commands.md` 命中（改写命令面时**不得丢失**稀疏安全与语料断言的工程知识——该知识为本文件独占，`docs/DESIGN-evolution.md` 零覆盖）；**且** `python3 -m pytest tests/python -q` 仍全绿（脚本未删，测试不得被破坏）。
5. [x] 结构契约不破坏：`python3 -m pytest tests/python -q` 全绿（提案结构契约脚本未变更）。
6. [x] agent 指针：`agents/wopal.md` 中 "ontology capability evolution" 相关表述指向 `ontology-evolution`，无残留 "carried by the `space-master` skill"。
7. [x] 提案命名契约落地（可判定）：`rg -q "20 chars" skills/ontology-evolution/templates/proposal.md` 命中（slug 长度上限）；`rg -q "type>-<slug" skills/ontology-evolution/templates/proposal.md` 命中（命名结构）；`rg -q "^\| .*\| .*\|$" skills/ontology-evolution/templates/proposal.md` 在命名契约段内至少命中 1 行（verbose→lean 对照表非空）；`rg -q "refactor-ontology-maintenance" skills/ontology-evolution/templates/proposal.md` 命中（对照表以本提案为反例）；`rg -q "templates/proposal.md" skills/ontology-evolution/SKILL.md` 命中（`new` 行指向模板契约）；`rg -q "slug.{0,20}(20|noun)" skills/ontology-evolution/references/commands.md` 命中（`new` 条目补约束）。**断言须用 ripgrep 原生语法**：`-E` 在 rg 中是 `--encoding` 而非扩展正则，`rg -qE` 会以 exit 2 失败（实施 Agent 实测发现并回报，已修正）。**

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

### Task 1: 机制文档完全切换到 space evo + 维护协议收编

**Verification Intent**: AC#1, AC#4, AC#5

**Behavior**:
- **SKILL.md Mechanism lane 章节完全改写为 `wopal space evo` 调用协议**：八条子命令逐条给出调用形态（`new` / `status` / `check` / `advance --to` / `accept [--no-worktree]` / `commit` / `integrate` / `archive`），**零 `evo.sh` 残留**；契约指针指向 `projects/wopal-cli/docs/DESIGN-evolution.md`
- **「Defect repair is immediate」整节改写**：CLI 无 `fix` 子命令，缺陷即时修复统一表述为 `wopal space evo commit -m "<msg>" (--paths <p>... | --all)` 的 instant 模式（不带提案名）
- SKILL.md 新增 Maintenance Protocols 章节：六命令表（space status/sync/capability、ontology capability list/update/contribute）、status 解读要点（Downstream/Upstream flow、localState 清单）、contribute scope determination 与主题化 PR 规则、双通道与上行闸、执行口径（D-05）
- SKILL.md Boundary 更新：`wopal/ontology-maintain` 定位为薄触发；机制归 CLI；**不得出现「迁移期脚本」或任何脚本存在性说明**
- **references/commands.md 整篇改写为 `wopal space evo` 命令参考**：11 个章节中 9 个 `## evo.sh <cmd>` 标题全部改为 `wopal space evo <cmd>`；`State writes are script-only` 改写为 stage 只由命令写入；**稀疏安全工程知识必须原样保留**（`git add -A` 实测行为表、`git add --sparse` 不扩范围的陷阱、语料断言的不可替代性、integrate 的语料断言与回滚边界）——该知识为本文件独占，`docs/DESIGN-evolution.md` 零覆盖，改写命令面时不得丢失
- 结构契约测试保持全绿（脚本未删，`tests/python/` 4 个测试文件仍须通过）

**Pre-read**: `.wopal/docs/DESIGN-capabilities.md`；`.wopal/docs/DESIGN-evolution.md`；`projects/wopal-cli/docs/DESIGN-evolution.md`；现 `skills/ontology-evolution/SKILL.md` 全文；现 `references/commands.md` 全文；本提案 Key Interfaces 的 `evo.sh → space evo` 映射表

**Design**: 在现有 SKILL.md 上增补与定点改写，不重写语义车道内容（已对齐）。Maintenance 章节内容以设计定稿为准，**禁止从旧 `ontology-maintenance.md` 搬运旧命令面内容**，且不得夹带已废弃引用（`ontology apply`、`DESIGN.md §6.9.2`、`upstream-sync.md`）——那些是 Task 2 的清理对象，但 Task 1 同样不得引入。机制章节按 D-04 从「标注过渡」升级为「完全切换」：不是加一句「脚本是过渡实现」，而是把整节操作面叙述改写成 CLI 形态后**删除**脚本存在的叙述。commands.md 改写遵循「命令面换、知识留」：`add --sparse` 实测表与语料断言段落描述的是稀疏装配的固有危险，与哪个实现无关，必须留存。测试超时是已知坑，见 Changes 第 1 项。

**TDD**: false

**Changes**:
1. 运行结构契约测试确认基线全绿（**注意超时**：`test_sparse_safety.py` 单文件约 81s、全量约 85s，须给 ≥180s 预算；默认 60s 会 kill 进程并误判为失败）
2. 改写 SKILL.md：Mechanism lane → `space evo` 协议；缺陷修复节 → instant 模式；新增 Maintenance Protocols；更新 Boundary
3. 整篇改写 references/commands.md 为 `space evo` 命令参考，保留稀疏安全与语料断言知识
4. AC#1 / AC#4 断言逐一通过；确认两文件 `evo.sh` / `evo.py` / `bash scripts/` 零命中

**Verify**: `python3 -m pytest tests/python -q` 全绿（≥180s 超时）；`rg -c 'evo\.sh|evo\.py' skills/ontology-evolution/SKILL.md skills/ontology-evolution/references/commands.md` 零命中；`rg -c 'wopal space evo' skills/ontology-evolution/references/commands.md` ≥ 8；`rg -q 'add --sparse|corpus assertion' skills/ontology-evolution/references/commands.md` 命中；`rg -n 'space evo' skills/ontology-evolution/SKILL.md` 命中

**Done**:
任务产出：机制文档完成向 `wopal space evo` 的完全切换，脚本命令零残留；维护协议成为技能章节。
实际触碰文件：`skills/ontology-evolution/SKILL.md`、`skills/ontology-evolution/references/commands.md`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

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
实际触碰文件：`commands/wopal/ontology-maintain.md`、`skills/space-master/SKILL.md`、`skills/space-master/SKILL.zh-CN.md`、`skills/space-master/references/ontology-maintenance.md`（删除）、`agents/wopal.md`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

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
实际触碰文件：`skills/ontology-evolution/templates/proposal.md`、`skills/ontology-evolution/SKILL.md`、`skills/ontology-evolution/references/commands.md`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

### Task 4: AGENTS.md 清除脚本架构描述

**Verification Intent**: AC#4, AC#5

**Behavior**:
- `skills/ontology-evolution/AGENTS.md` 中 `evo.sh` / `evo.py` / `scripts/` / `bash scripts/` **全部零命中**（当前实测：`evo.sh`×6、`evo.py`×1、`scripts/`×10）
- `Stage` 只由命令写入的规则保留，但归属改为 CLI 机制面（原表述指向 `scripts/lib/proposal.py`，随脚本删除将失效）
- 「缺陷即时修复」小节改指 `wopal space evo commit` instant 模式
- 仍然为真的开发规则原样保留：提案结构契约（必需章节 + Task 六元素）、`D-NN` 编号纪律、Semantic/Mechanism 双车道边界、脚本**尚存**这一事实不写进文档（D-04 容忍的短暂不一致）
- `tests/python/` 4 个测试文件**保留不动**——脚本仍在，给活代码删测试是错的；二者同批删除属下一步

**Pre-read**: 现 `skills/ontology-evolution/AGENTS.md` 全文；本提案 D-04；`projects/wopal-cli/docs/DESIGN-evolution.md`（确认 stage 写入的机制面归属）

**Design**: AGENTS.md 是**开发规则**文档，其中关于 `sparse.py` / `worktree.py` / `proposal.py` 架构的描述随脚本删除即将全部失效。本任务按 D-04 提前清除，使技能文档整体达成零脚本引用；代价是改完后脚本实体与 `tests/python/` 仍存在却已无文档描述——这是 D-04 明示容忍的短暂不一致，下一步删除落地即消失。**不得**借机扩写新的架构章节，删除优先于重写；确实需要保留的规则用 CLI 表述重述一句即可。

**TDD**: false

**Changes**:
1. 读 AGENTS.md 全文，标出全部脚本引用点
2. 逐处清除或改写为 CLI 表述，保留仍为真的规则
3. AC#4 中 AGENTS.md 相关的断言通过；确认 `tests/python/` 与 `scripts/` 文件树未被触碰

**Verify**: `rg -c 'evo\.sh|evo\.py|bash scripts/' skills/ontology-evolution/AGENTS.md` 零命中；`rg -q 'space evo' skills/ontology-evolution/AGENTS.md` 命中；`python3 -m pytest tests/python -q` 全绿（≥180s 超时）；`git status --short` 不含 `scripts/` 与 `tests/`

**Done**:
任务产出：技能开发规则与用户文档一致，机制面描述全部指向 CLI。
实际触碰文件：`skills/ontology-evolution/AGENTS.md`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 机制面完全切换，改写面最大；文件集与 T2/T4 无交集 |
| 1 | Task 3 | fae | 无 | 与 T1 同改 SKILL.md / commands.md，**必须同一 fae 会话顺序执行**，不可并发 |
| 1 | Task 4 | fae | 无 | 独立单文件（AGENTS.md），无共享文件面 |
| 1 | Task 2 | fae | 无 | 文件集与 T1/T3/T4 无交集 |

**委派分批**（受 fae 上下文预算约束，单委派 ≤30 步）：

| 轮次 | Task | fae 会话 | 说明 |
|---|---|---|---|
| 1 | T1 → T3 | 复用现有会话 | T1/T3 共享文件面，必须同会话串行 |
| 2 | T4 → T2 | **新开** | 无共享上下文需求；按用户规则 fae 接近 40% 即新开，不 reply 复用 |

> 四条 Task 同为 Wave 1（无相互阻塞），但**不得并行**：全部落在同一隔离 worktree 的同一 git index 上，并发提交会争抢 index.lock 并混合提交边界。

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。
