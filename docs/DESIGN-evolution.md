# DESIGN — Evolution Loop

> **Status**: Active
> **Updated**: 2026-09-24
> **Parent**: `./DESIGN.md`（ontology overall design: Module Architecture section）
> **Parent Architecture**: `../../docs/products/wopal-space/DESIGN.md`
> **Parent Product**: `../../docs/products/wopal-space/PRD.md`

---

## Ontology Collaboration Model

Ontology 以「中央能力池 + 空间装配 worktree」模型承载能力演化。一个空间是能力池的一次**可写装配视图**：能力组合由装配单决定，能力内容在空间内可写可进化，进化通过 `space sync` 汇入用户级能力池。

### Layered Structure

两级仓库，职责单一：

- **本地中央仓库（`~/.wopal/ontologies/<source>/`，`local main` 分支）**：用户级稳定能力池；所有公共 `agents/`、`skills/`、`rules/`、`commands/`、`plugins/` 与类型装配单的唯一真相源。跟踪 upstream/main。
- **空间装配 worktree（`<space>/.wopal/`，`space/<name>` 分支）**：按空间装配单 sparse-checkout 物化的**真实可写文件**视图。Agent 在此正常修改与提交，无需空间外写权限。

类型语义由装配单承载，不设 `type/*` 分支层级。

### Core Rules

1. **local main 是能力唯一真相源**：共享能力不维护空间私有版本；空间的独有提交是待贡献的进化，不是长期分叉。
2. **`space sync` 定序：先上行、后下行**：先汇入空间独有进化，再 fast-forward 到 local main 最新，最终两分支指向同一提交。
3. **正常推进一律 fast-forward**：空间分支必须可对齐时才能推进；有待贡献提交时先贡献，有未提交修改时先处理工作区。
4. **冲突在隔离临时 worktree（`$WOPAL_HOME/.worktrees/`）中处理**：整合成功才推进 live space 与 local main 引用；失败双方保持原状。
5. **更新/移除/贡献前检查工作区状态**：CLI 以工作区事实为准，不单信 Git 命令退出码。
6. **默认执行，不设审批门控**：`space sync` 由 agent 按用户意图调用。安全保障由机制承担——隔离整合、ff-only、冲突即停、工作区检查——最坏结果是未发生变更，而非破坏工作区。`--dry-run` 是诊断工具，不是执行前门控。
7. **登记是唯一范围入口**：装配区内新路径的持久持有靠显式登记（`space capability add --local` 记入 `localState.added` 并扩稀疏范围）；未登记的未跟踪文件由范围重算保护不清扫，但不出现在任何清单中。登记不产生提交——`localState` 是空间私有事实，不进入空间分支树。`.gitignore` 过滤敏感文件。
8. **范围重算保留本地状态**：下行按装配单重算稀疏范围时，范围 = 装配单声明 ∪ `localState.added` − `localState.shadowed`；装配定义类基础文件始终包含。本地条目（added/shadowed）不随提交历史变化，也不上行。

## Self-Evolution Loop

Maka 专职海关与提议-实施权责分立，空间运行中产生的能力进化遵循严格的防特异性泄漏与海关检疫机制：

```
会话运行事实 / 报错日志 / 用户纠偏
  │
  ▼
[Maka 独立元认知代理 + ontology-evolution 技能]
  │  • 去特异化清洗 (De-contextualization): 抹除绝对路径与特定项目业务词
  │  • 泛化性三问 (Generalization Gate): 验证是否具备跨空间通用性
  │  • 三级分流判定: 空间私有 vs 类型专属 vs 公共核心
  ▼
生成《进化方案 (Evolution Plan)》呈交用户审查
  │
  ▼ 用户批准
[Wopal 统筹调度] ──委派──> [Fae 规范实施落盘]（空间 worktree 内提交）
                               │
                               ├─ 进化提交落在 space/<name>（待贡献）
                               ├─ 执行 space sync 汇入 local main
                               ▼
                        [Rook 正交质检守门]
                               │
                               └─ 校验 frontmatter 语法合法性与反污染底线
```

核心进化规则：

1. **提议权与实施权严格分离**：Maka 只出提案、不动刀（Propose Only，`edit` 仅放开 `docs/evolutions/`）；具体改动经用户批准后，由 Wopal 委派 Fae 在空间 worktree 内规范提交，Rook 审查把关。
2. **进化先落在空间分支，再经 `space sync` 汇入**：空间内正常写改、提交（Agent 仅需 workspace 写权限）；`space sync` 时申请受控提权，将空间独有提交隔离整合进 local main。
3. **空间私有资产物理隔离**：属于当前项目特有的架构规范，仅限写入本地 `.wopal-space/memory/` 或项目 `AGENTS.md`，不进入装配区。

进化粒度遵循严格的海关检疫：空间私有经验物理锁死在本地，类型经验作用于类型装配，只有高度抽象且经受反污染审查的通用资产才允许回流中央。

## Capability Evolution Workflow

本体能力进化的执行机制由 `ontology-evolution` 技能承载。该技能是四个核心角色在所有空间类型下的常驻能力：任意空间都能维护与补充自己的本体能力，无需装配代码开发工作流。代码项目开发流程由 `dev-flow` 拥有（见 `./DESIGN-capabilities.md`）；本体能力进化流程由 `ontology-evolution` 拥有。两条流程的对象不同——前者面向 `projects/` 下的代码仓库，后者面向空间自身的本体能力资产。

技能分两条车道，职责不重叠：

| 车道 | 承担者 | 产出 |
|------|--------|------|
| 语义车道 | Maka 独立元认知代理 | 摩擦检测、去特异化清洗、泛化门判定、三级分流，输出《进化方案》 |
| 机制车道 | Wopal 编排、Fae 实施、Rook 守门 | 提案落盘、状态推进、稀疏隔离实施、运行时验证、交付决策 |

《进化方案》是机制车道的工作对象，不是代码任务。

### Evolution Workflow States

本体进化提案的状态机与代码开发流程使用互不重合的词汇，使两个流程在同一空间内不会被混淆：

```text
draft → accepted → implementing → validating → archived
```

| 状态 | 含义 |
|------|------|
| `draft` | 提案落盘于本体仓库 `docs/evolutions/`，等待用户审阅 |
| `accepted` | 用户接受提案，进入实施 |
| `implementing` | 实施进行中：隔离 worktree 内的实施提交（或 quick 模式直提空间分支） |
| `validating` | 改动已集成到空间分支，等待用户重启运行时观察确认 |
| `archived` | 用户确认通过，提案归档 |

提案默认不创建 Issue 载体；用户明确要求时才引入评审与 Issue。

推进状态记在提案的 `Stage` 字段。与代码开发流程相比，字段名与词表都不重叠；与设计文档的 `Status` 字段（Draft / Proposed / Active）相比，词表出现一个同形词 `draft`，靠字段名区分。三者同处 `docs/` 之下，字段名是主要的区分依据。状态推进由技能脚本承担，Agent 不手改 `Stage` 字段。

### Evolution Documents

进化提案文档位于本体仓库的 `docs/evolutions/`。提案描述的是本体自身的变更，因此与它所改变的能力资产同处一条版本控制谱系：随装配分发到每个空间，并随 `space sync` 与 `ontology contribute` 汇入能力池与上游。任何空间都能读到完整的进化历史。

| 位置 | 内容 |
|------|------|
| `docs/evolutions/<name>.md` | 活跃提案，等待审阅或正在实施 |
| `docs/evolutions/archived/` | 已完成提案 |
| `docs/evolutions/backlogs/` | 暂缓提案 |

### Isolation Discipline

本体能力的改动先在空间装配 worktree 内落地，再经 `space sync` 汇入 local main，最后由用户决定是否经 `ontology contribute` 回流上游。默认实施模式是**从 `.wopal` 派生稀疏 worktree**：派生的 worktree 继承空间的稀疏装配范围，实施边界因此天然等于空间确权的能力范围，宿主中央仓库无需切换分支。

快速模式在 `.wopal` 空间分支内直接小步提交，适用于 typo、bug-fix 与用户明确指定的小范围文件改动；判定不清时默认走隔离模式。

稀疏装配带来三条硬约束：

1. **范围外文件由 Git 原生拒绝暂存**。需要新增能力目录时，先在实施侧扩展装配范围以使内容可写；合并后扩展 `.wopal` 装配并重新物化，验证者才能看到新能力。
2. **skip-worktree 位是装配范围的派生状态，禁止批量清除**。调整可见范围一律通过扩展装配完成；配置缺失且位被批量清除时，全量暂存会把范围外文件记为删除。
3. **合并与对象层不受稀疏影响**。分支推进、squash 合并与树比较都在对象层完成，稀疏只决定哪些文件落到磁盘。

### Delivery Terminal

进化的交付终点由用户拍板：实施产物停留在空间分支，`space sync`（汇入 local main）与 `ontology contribute`（回流上游）均由用户逐次决定，技能不内置自动上行。

加载链路相关改动以用户重启 ellamaka 后的加载结果作为验证标准。

## Maintenance and Distribution Command Surface

空间侧与 ontology 侧命令职责分离，语义稳定：

| 命令 | 方向 | 职责 |
|------|------|------|
| `space status` | — | 只读：落后 / 待贡献 / 装配状态 / 本地状态清单（added / shadowed / 未登记未跟踪文件） |
| `space sync` | 双向 | 与 local main 对齐：先上行（隔离整合空间独有进化）再下行（fast-forward 到最新），刷新装配版本；上行前校验本地状态不泄漏（见下）；默认执行，`--dry-run` 仅预览 |
| `space capability add/remove` | — | 无旗标：增删装配单中的能力并提交，随 sync 上行，同类型空间跟进；`--local`：写入 `localState`（added / shadowed）并调整稀疏范围，零提交、永不上行 |
| `ontology capability list` | — | 只读：列出本体拥有的全部能力，供空间装配挑选 |
| `ontology update` | 下行 | upstream/main → local main，本地中央仓库整合 |
| `ontology contribute` | 上行 | local main → upstream PR（fork 模式；clone 模式不支持） |

**本地通道与共享通道的分界**：`space capability` 的 `--local` 旗标决定变更归宿。无旗标走装配单通道——修改装配单、产生提交、随 sync 上行，是共享动作；`--local` 走本地通道——只写 `localState` 并调整稀疏范围，不进入空间分支树，构造上不可上行。`add --local` 对已遮蔽能力兼任恢复出口（清 shadow 条目并物化最新版）；`remove --local` 对本地引入（added，未提交）的能力撤回磁盘文件并清除登记。

**上行不泄漏本地状态（上行闸）**：`space sync` 上行前校验空间独有提交的变更路径（`git diff --no-renames --name-only main...space/<name>`）与 `localState`（added ∪ shadowed）无交集；命中即拒绝上行并给出处置指引（撤出提交或解除登记）。该闸兜底用户手动 `git add/commit` 将本地状态内容提交进空间分支的场景——本地隔离不依赖用户记得，由机制强制。

`space sync` 默认执行，不设审批门控；`--dry-run` 保留为诊断用途，展示将贡献、将更新与将纳管的清单。`ontology contribute` 仅在 fork 模式下可用，clone 模式只支持 `ontology update`。

`ontology capability list` 揭示本体拥有的全部能力，是 `space capability add/remove` 的挑选依据——空间先用它发现有什么可装，再决定装什么、以哪条通道装（共享进装配单或 `--local` 私有持有）。装配单中不存在的能力不走本命令：用户以共享意图引入时用 `space capability add`，以私有意图引入时用 `space capability add --local`。

空间内日常能力进化通过 Maka 检疫提炼后，由 Fae 在空间 worktree 提交，再经 `space sync` 汇入 local main，最终经 `ontology contribute` 回流 upstream。空间装配出的能力组合若具备类型通用性，可沉淀为类型装配单，供同类空间复用。

## Distribution Boundary

ontology 的分发走 Git source + worktree 模型。wopal-cli 通过 `wopal space init` / `wopal setup` 封装 clone/fork/worktree 过程，将其与 space runtime 初始化串联。

稳定边界：

1. 默认使用 clone-based canonical source flow。
2. `--fork` 是显式选择的替代模式。
3. `space/<space-name>` 分支承载 space-specific 演化。
4. `<space>/.wopal/` 是 ontology worktree，由 CLI materialize，由 ellamaka 运行时加载。

详细 source 输入、materialization、template handoff 和 runtime loading handoff 见 `./DESIGN-distribution.md`。

## Base Capabilities and Space Overlay

Ontology 通过两层模型为 WopalSpace 提供可覆盖的能力分发：

**User-level base capabilities**：`~/.wopal/skills`、`~/.wopal/agents`、`~/.wopal/commands`、`~/.wopal/rules`、`~/.wopal/plugins` 以及 `~/.wopal/dsh/agents-presets` 是面向所有 space 的基础能力入口。setup 从 `~/.wopal/ontologies/wopal-space-ontology/{agents,skills,commands,rules,plugins,dsh/agents-presets}` 物化它们：macOS / Linux 使用 symlink，Windows 使用 managed copy。DSH Profile（`web` / `ellamaka-tools`）的 `package.json` 与 `cordis.patch.yml` 声明模板则通过确定性物理复制（Copy）物化至 `$WOPAL_HOME/dsh/home/profiles/`，再由 `ellamaka dsh init` 驱动闭包与依赖补齐。

**Space overlay**：`<space>/.wopal/skills`、`<space>/.wopal/agents`、`<space>/.wopal/commands`、`<space>/.wopal/rules`、`<space>/.wopal/plugins` 承载当前 space 的定制能力。同名能力由 space overlay 覆盖 base，ellamaka 按优先级顺序加载：

```text
~/.agents/skills
-> ~/.wopal/skills           # base
-> <space>/.wopal/skills     # overlay，优先级最高
```

覆盖机制：ellamaka 先并发解析所有 `SKILL.md`，再按目录优先级顺序串行合并；后出现的同名 skill 稳定覆盖前者。Agents / commands / rules / plugins 的加载机制同理。

本模型将 ontology main repo 的基础能力与各 space 的定制能力解耦：通用能力由 ontology main 统一维护，setup 只负责物化 base capabilities；space 内自由定制增量覆盖。

## System Prompt Self-Evolution

提示词是核心资产。Maka 检疫提炼并提出方案，经用户批准后由 Wopal 调度 Fae 更新中央仓库的提示词文件，实现跨空间协同进化。

## Design Knowledge Layering

WopalSpace 的设计知识按三层分工，避免细节错位和维护混乱：

| 文档 | 定位 | 内容 |
|---|---|---|
| 产品 DESIGN | 跨项目的稳定架构契约 | 系统分层、子系统职责边界、"谁负责什么"。详细契约和 schema 以项目 DESIGN 为准 |
| 项目 DESIGN | 单个项目的稳定设计真相 | 命令契约、JSON schema、模块架构、数据模型、关键决策。阶段范围和验收以 Phase 文档为准 |
| Phase 文档 | 某阶段的范围与验收条件 | Phase scope、involved projects、exit criteria、风险。架构细节以项目 DESIGN 为准 |

关系：

- 产品 DESIGN 回答"系统如何组成"；项目 DESIGN 回答"单个项目如何实现"；Phase 文档回答"这一阶段要交付什么"。
- 稳定契约只进项目 DESIGN，不进 Phase 文档——Phase 最终归档后不应成为查找架构细节的入口。
- 产品 DESIGN 引用但不复制项目 DESIGN 细节；Phase 文档引用但不复制 DESIGN 契约。
- Phase 讨论中形成的设计决策，在讨论完毕后沉淀到对应项目 DESIGN；Phase 文档只保留范围和验收。
