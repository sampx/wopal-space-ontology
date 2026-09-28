---
name: ontology-evolution
description: |
  本体能力进化流程。覆盖这项工作的两半：把运行中获得的经验——会话错误、用户纠正、记忆中沉淀的经验教训与解决方案——写成进化提案；以及把已批准的提案安全落地（隔离实施、验证、归档）。提案通常由 Maka 起草，这是它的核心使命；Wopal 也可以撰写，并主控落地过程。Fae 负责落地变更，Rook 负责审查；批准、验证与交付由用户掌握。

  必须加载的场景：
  - 把会话中的经验教训、错误或用户纠正沉淀为持久能力
  - 判断一条知识该住在哪里（空间记忆 / 类型装配 / 中央池）
  - 产出供用户批准的进化提案
  - 在候选能力进入能力池之前，审查它是否夹带项目私有污染
  - 推进进化提案的阶段，或查看某项进化的状态
  - 实施对本体自身能力（skills、rules、agents、commands、plugins、assembly）的变更
  - 在空间内创建、更新、分发或贡献本体能力资产
  - 任何「进化提案 / evolution proposal / evolution stage / 能力进化」类请求

  Object test：本体能力资产（本空间自己的 skills、rules、agents、commands、plugins、assembly、docs/evolutions）→ 本技能。`projects/` 下的代码仓库 → dev-flow，不用本技能。
---

# ontology-evolution — 本体进化

把运行中获得的经验，沉淀为本体的持久能力——并让这项改进安全落地。

一切汇聚于同一件产物：**进化提案**——`docs/evolutions/` 下的一个文件，写明要改什么、为什么、如何验证。撰写与落地是同一流程的两个环节；落地永远等待用户的明确批准。

## 角色与分工

| 角色 | 做什么 | 绝不做什么 |
|------|--------|------------|
| **Maka** | 核心使命：分析会话中的错误、用户纠正、以及记忆中沉淀的经验教训与解决方案；撰写并打磨 `docs/evolutions/` 下的进化提案 | 触碰本体能力资产、运行落地流程 |
| **Wopal** | 也可以撰写提案。主控落地全过程：与用户一起阅读提案、accept、编排并委派实施、推进阶段流转、验证结果直至归档 | 不亲自改动资产（落地由 Fae 执行） |
| **Fae** | 落地变更——修改资产并在空间分支上提交 | 推进提案阶段 |
| **Rook** | 在结果继续前进之前审查它 | 修任何东西 |
| **用户** | 在落地开始前批准提案；验证落地的变更；决定交付 | — |

提案本身从不构成实施授权：无论由谁撰写，每份提案都要等待用户批准后才能落地。跨过这道门之后，安全靠机制保证——隔离、按名暂存、可见性校验——而不是靠信任。

---

# 编写进化提案

目的不是记录发生了什么，而是改变能力，让同样的情况下次处理得更好。

## 值得观察的来源

| 信号 | 表现 | 通常意味着 |
|------|------|------------|
| 会话错误 | 一次失败暴露了错误假设 | 缺一道护栏 |
| 用户反复纠正 | 用户就同一行为纠正了不止一次 | 某条规则缺失或不清楚 |
| 记忆中的教训 | 记忆里沉淀着还没有任何能力承载的教训、临时绕法或修复 | 它应该住进某个资产 |
| 重复劳动 | 同一个辅助方法或路子被反复重建 | 应该抽成一项能力 |
| 有效模式 | 某个做法效果特别好 | 值得固化，让它可以复现 |

例行完成不是经验。要找的是「行为本应不同」的那个时刻。

## 先剥离具体情况

- 绝对路径、项目 / 产品 / 客户名、只在此处成立的业务词 → 换成通用措辞或直接去掉
- 会话 id、时间戳、提交哈希 → 去掉

检验标准：一个从未见过这个空间的读者，也能理解并运用这条经验。

## 判断归属

| 层级 | 去向 | 适用情形 |
|------|------|----------|
| **空间私有** | `.wopal-space/memory/` 或项目的 `AGENTS.md` | 只在本空间 / 本项目成立 |
| **类型级** | `config/types/<type>.yaml` 装配，或类型范围内的资产 | 对一切同类型空间成立，对其他类型不成立 |
| **公共池** | 中央池（`agents/`、`skills/`、`rules/`） | 对任何类型的任何空间都成立 |

依次自问：换一个空间成立吗？换一个同类型的项目成立吗？对任何空间都成立吗？「也许」不算「是」——拿不准就往低层放。局部的经验日后可以提升；被污染的池子很难清洗。

## 落笔

`wopal space evo new "<title>"` 会从 `templates/proposal.md` 生成 `docs/evolutions/<name>.md`，初始 `Stage: draft`。模板是提案形态的唯一来源——每一节都要填写；残留占位符会在 `accept` 时被拒绝。

- 进化提案文档使用用户偏好语言编写；模板的标题与字段标签保持原样。
- 每条主张都要有证据锚点：会话事实、错误、用户纠正、代码位置（`file:line`）。未验证的话必须标注为未验证。
- 少而扎实胜过多而单薄。一次分析可能产出多条候选——一条候选一份提案。

## 交接

落盘的提案就在等待用户阅读；只要它还是提案，作者可以继续打磨。用户批准之后进入落地阶段，由 Wopal 主控。

---

# 落地已批准的提案

落地纪律由 wopal-cli 保证——先检查、后写入、按名暂存、隔离与可见性校验。本节记录的是命令管不了的部分：角色分工、用户决策点与验证哲学。落地操作全部通过 `wopal space evo` 命令族完成。

## 状态机

```
draft → accepted → implementing → validating → archived
```

| 阶段 | 含义 |
|------|------|
| `draft` | 提案在 `docs/evolutions/` 落盘，等待用户阅读 |
| `accepted` | 用户已批准；隔离工作树已创建，模式已记录 |
| `implementing` | 变更正在落地：提交发生在隔离工作树（或快速模式下直接落在空间分支） |
| `validating` | 变更已集成到空间分支；用户重启并观察 |
| `archived` | 用户已确认；提案归档 |

`accepted → implementing` 与 `validating → archived` 是仅有的前进边。评审不占据阶段：用户要求评审时才发生，它不会凭空发明一个状态。没有回退边——已落地的变更要返工，是发新提交，不是回退阶段。

**阶段词汇与 dev-flow 刻意完全不同**（`planning / reviewing / approved / executing / verifying / done`）。混用两套词汇会让 agent 把两个流程弄混——永远不要「统一」它们。

## 命令清单

从空间根目录运行：`wopal space evo <command> [args]`。

| 命令 | 作用 |
|------|------|
| `wopal space evo new "<title>"` | 从 `templates/proposal.md` 生成 `docs/evolutions/<name>.md`，`Stage: draft`；标题受模板中的命名契约约束 |
| `wopal space evo status [name]` | 列出活跃提案；或显示某份提案的阶段与已记录元数据 |
| `wopal space evo check <name\|path>` | 诊断提案（元数据、占位符、结构）与空间工作树的稀疏形态 |
| `wopal space evo advance <name> --to <state>` | 推进状态机；非法跃迁会被拒绝 |
| `wopal space evo accept <name> [--no-worktree]` | 对提案过门禁（占位符 + 结构），然后以事务方式派生或重挂隔离工作树 |
| `wopal space evo commit [<name>]` | `implementing` 阶段的稀疏安全提交：先扩范围、再按名暂存。不带名字即 instant 模式——缺陷修复路径 |
| `wopal space evo integrate [name]` | 把隔离工作 squash 进空间分支；拒绝任何会「落地即隐身」的内容 |
| `wopal space evo archive <name> [--keep-worktree]` | 把 `archived` 提案移入 `docs/evolutions/archived/YYYYMMDD-<name>.md`，清理隔离产物 |

命令族的保证（由 CLI 强制，而非靠自觉）：

- **Stage 只由命令写入。** 永远不要手改 `- **Stage**:`；字段找不到的提案无法推进。
- **拒绝先于写入。** 被拒绝的命令不会留下任何改动。
- **绝不整包暂存。** 一律按名暂存，且先扩稀疏范围；没有任何命令会跑 `git add -A`。
- **重复执行是安全的。** 重复 advance 是无操作；重复 accept 会收养或重挂，而不是和既有状态打架。

命令级细节——包括 `commit`/`integrate` 共享的预检——在 `references/commands.md`。

## 隔离实施纪律

默认实施模式：**从 `.wopal` 派生工作树**。派生工作树继承空间的稀疏装配模式，因此它的可见边界等于空间有权拥有的能力集——宿主仓库永不切换分支。

七条约束：

1. **默认隔离。** 工作树从 `.wopal` 派生；`accept` 校验该派生是空间的忠实稀疏副本。
2. **宿主仓库永不切换分支。** 它承载其他空间依赖的基础能力，始终停留在 `main`。
3. **在空间分支上合并。** 合并在 `.wopal` 内、空间分支上进行，验证通过后一次 squash。
4. **先装配再暂存。** 新能力目录先加入空间范围（先扩范围再暂存）；`integrate` 拒绝任何会「落地即隐身」的路径——已提交但运行时看不见的文件（可见性校验；CLI 契约里叫 "corpus assertion"）。
5. **不要批量清除 skip-worktree 位。** 它们是装配范围的派生态；调整可见范围只能通过扩大装配，让预检去验证范围，而不是靠自觉。
6. **验证 = 重启并观察。** 任何触及加载路径的变更，都以用户重启 ellamaka 后看到的行为为准；测试全绿不能代替观察。
7. **交付是用户的最终决定。** `space sync` 与 `ontology contribute` 一次一个、只在用户发话时执行。本技能不含任何自动上行路径——这是设计，不是遗漏。

### 快速模式

拼写修复、既有资产里的小缺陷修复、以及用户明确圈定的小改动，可以直接在 `.wopal` 空间分支上小步提交——空间分支本身就是对 `local main` 的隔离边界。判断不清楚时，走隔离模式。扩大范围是用户的决定，不是 agent 的方便。

### 缺陷立即修复

**缺陷**——既有、已商定的行为出了错——立即修复，不走提案。提案要提供的那道评审，对已经商定的行为早已完成；真正重要的记录是那次提交。

路径是 `wopal space evo commit` 的 **instant 模式**——不带提案名，配 `-m <message>`，且 `--paths <p>...` / `--all` 二选一：

- 直接提交在空间分支上——和快速模式一样，分支即对 `local main` 的隔离边界。
- 安全契约照旧：稀疏状态不健康就拒绝、先扩范围、按名暂存。快路径跳过的是流程，永远不是安全。
- 不产生提案产物，也不移动任何阶段。

没有独立的 `fix` 命令——这是设计，不是缺口；不要新增它、别名或壳。影子注册（shadow-registration）职责属于 `capability remove --local`。

缺陷是**修复**已商定的行为；任何**改变**行为的改动——新能力、契约变更、流程步骤要换种行为——都是进化，走提案流程。分不清时先问。给一个本应评审的改动选择了快路径，比给一个修复选了慢路径更糟。

## 落地全流程

```
Proposal (approved)
  → wopal space evo new "<title>"                    # draft from templates/proposal.md
  → user reads the proposal
  → wopal space evo accept <name>                    # gate + isolated worktree
  → wopal space evo advance <name> --to implementing
  → implement, then wopal space evo commit <name>    # sparse-safe, per task
  → wopal space evo integrate <name>                 # squash onto the space branch
  → wopal space evo advance <name> --to validating
  → user restarts ellamaka and confirms
  → wopal space evo advance <name> --to archived
  → wopal space evo archive <name>                   # dated name + isolation cleanup
  → delivery decision (space sync / ontology contribute) — user only
```

快速模式跳过 integrate：`wopal space evo commit <name>` 直接落在空间分支上，分支本身就是隔离边界。

`integrate` 只在实施完成后跑一次。每提交一次就 squash 是行不通的：squash 会产生新的 commit id，下一次 squash 因此失去合并基点、报 add/add 冲突。integrate 之后的重做是空间分支上的新提交，不是第二个 squash。

---

# 维护协议

除进化生命周期之外，本技能还负责本体的维护面：实例更新、空间对齐、能力装配。

## 命令面

| 命令 | 方向 | 职责 |
|------|------|------|
| `wopal space status` | — | 只读：空间分支相对 `local main`（可贡献 / 落后）、远端差异、装配快照健康度、本地状态清单（added / shadowed / 未注册） |
| `wopal space sync [--confirm]` | 双向 | 与 `local main` 对齐：先把空间独有的进化向上整合（隔离工作树、冲突即停），再快进向下 |
| `wopal space capability add/remove <kind>:<name> [--local]` | manifest / local | 共享通道：编辑原型 manifest 并重新物化；只接受能力池已有的能力（池中不存在的名字在触碰 manifest 之前就被拒绝），且**不产生 Git 提交**——提交 manifest 是单独的显式步骤。`--local`：作为空间私有状态保留或丢弃——零提交、永不上行 |
| `wopal ontology capability list` | — | 只读：能力池拥有什么——`space capability add` 的选择清单 |
| `wopal ontology update [--confirm]` | 向下 | `upstream/main` → `local main` |
| `wopal ontology contribute --message <msg> [--include/--exclude <glob>] [--confirm]` | 向上 | `local main` → 上游 PR（fork 模式；在隔离工作树中 squash 合并；冲突时 `--resume` / `--abort`） |

## 读状态

`wopal ontology status` 报告双向流：**向下**（`upstream → origin → local main`）与**向上**（`local main → origin → upstream`），后者以待办文件集呈现。

`wopal space status` 报告空间链接：**可贡献** 还是 **落后 local main**、装配快照状态、以及**本地状态清单**——`added` / `shadowed` / 未注册的未跟踪文件。本地状态路径天生空间私有：它们永远不会上行到 `local main`。

## 双通道与上行门禁

`space capability` 有两条通道。不带 `--local` 时，改动编辑装配 manifest 并重新物化——但自身不产生提交，且只接受能力池已有的能力，所以提交 manifest 是单独的步骤。带 `--local` 时，只写空间的 `localState`（`added` / `shadowed`）并调整稀疏范围——零提交、结构上无法上行；对影子能力执行 `add --local` 也是恢复出口。

向上整合之前，`space sync` 会检查**上行门禁**：任何空间独有提交都不得触碰 `localState` 路径（added ∪ shadowed）。命中即拒绝同步并给出补救：撤回该提交，或注销登记。门禁为手动 `git add`/`commit` 本地状态内容兜底：本地隔离不依赖操作者记得规则。

## 执行立场

CLI 默认 dry-run 预览；`--confirm` 落地执行。既定立场：agent 直接依用户意图行事并传 `--confirm`——不额外叠加审批门；`--dry-run` 是诊断，不是前置条件。安全来自机制：隔离集成、仅快进、冲突即停、工作树校验——最坏情况是「变更没发生」，而不是「工作树被搞坏」。唯一例外是 `ontology contribute`：每次贡献都是用户的决定，一次一个。

## 贡献范围与主题 PR

范围与用户一起、基于证据确定：

1. 先枚举全部待处理路径（`git diff --name-status <base>...<target>`），按目录 / 功能域分组，逐组标注「共享」或「类型专属」——先展示完整清单，再问任何问题。
2. 按结构归类，不凭感觉：共享 = 对每种空间类型都有意义；类型专属 = 只对一种类型有意义。不确定时，查能力池（`ontology capability list`）与本体设计，而不是猜。
3. 用户圈定范围：哪些组上行、哪些排除、哪些留在空间内。
4. 空间独有的资产永不出现在任何贡献里。

一个主题一个 PR：`--include` / `--exclude` 从待处理集里划出一份连贯的贡献，`--message` 写清这项变更交付了什么（结果态），而不是机械动作。不相关的工作要拆分，绝不捆在一起。

---

# 边界

- **提案等待用户。** 无论谁写的，只有用户批准后才落地——作者绝不悄悄实施自己的提案。
- **Maka 只写不做。** Maka 的编辑范围是 `docs/evolutions/`；触碰能力资产 = 严重失职。把猜测当作事实呈报，比没有提案更糟。
- **落地：Wopal 主控、Fae 执行、Rook 把关。** 本流程永不自行上行。
- **`/wopal:evolve` 与 `/wopal:distill`** 属于记忆进化回路（日记 → 长期记忆文件 / 记忆库），不是本流程的入口；从这里沉淀出的本体变更，仍走本技能的提案流程。
- **`wopal/ontology-maintain`** 是薄触发器：它以 focus 参数加载本技能，自身不携带协议——上面「维护协议」就是协议。
- **技能只负责规范，执行交给 wopal-cli。** 本技能只有文档和模板，没有脚本；维护与落地的每一步都通过 wopal-cli 命令完成——命令明细见上文「维护协议」与「落地已批准的提案」。
- **装配叠加**：资产经由叠加机制按空间装配（`docs/DESIGN-distribution.md`）；技能操作的是装配后的工作树（`.wopal`），永远不直接操作中央池。

---

# 参考

- 状态机与交付终端：`docs/DESIGN-evolution.md`（Capability Evolution Workflow）
- 命令契约与阶段语义：`references/commands.md`
- 提案骨架：`templates/proposal.md`
- 稀疏隔离背景：`docs/DESIGN-distribution.md`
- 本技能的开发规约：`AGENTS.md`
