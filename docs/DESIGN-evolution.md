# DESIGN — Evolution Loop

> **Status**: Active
> **Updated**: 2026-09-14
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
4. **冲突在隔离临时 worktree 中处理**：整合成功才推进 live space 与 local main 引用；失败双方保持原状。
5. **更新/移除/贡献前检查工作区状态**：CLI 以工作区事实为准，不单信 Git 命令退出码。

## Self-Evolution Loop

Evolver 专职海关与提议-实施权责分立，空间运行中产生的能力进化遵循严格的防特异性泄漏与海关检疫机制：

```
会话运行事实 / 报错日志 / 用户纠偏
  │
  ▼
[Evolver 独立元认知代理 + ontology-evolution 技能]
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

1. **提议权与实施权严格分离**：Evolver 只出方案、不动刀（Read & Propose Only）；具体改动经用户批准后，由 Wopal 委派 Fae 在空间 worktree 内规范提交，Rook 审查把关。
2. **进化先落在空间分支，再经 `space sync` 汇入**：空间内正常写改、提交（Agent 仅需 workspace 写权限）；`space sync` 时申请受控提权，将空间独有提交隔离整合进 local main。
3. **空间私有资产物理隔离**：属于当前项目特有的架构规范，仅限写入本地 `.wopal-space/memory/` 或项目 `AGENTS.md`，不进入装配区。

进化粒度遵循严格的海关检疫：空间私有经验物理锁死在本地，类型经验作用于类型装配，只有高度抽象且经受反污染审查的通用资产才允许回流中央。

## Maintenance and Distribution Command Surface

空间侧与 ontology 侧命令职责分离，语义稳定：

| 命令 | 方向 | 职责 |
|------|------|------|
| `space status` | — | 只读：落后 / 待贡献 / 装配状态 |
| `space sync` | 双向 | 与 local main 对齐：先上行（隔离整合空间独有进化）再下行（fast-forward 到最新），刷新装配版本 |
| `space capability add/remove` | — | 增删本空间装配的能力，重新物化；可贡献为类型装配单 |
| `ontology capability list` | — | 只读：列出本体拥有的全部能力，供空间装配挑选 |
| `ontology update` | 下行 | upstream/main → local main，本地中央仓库整合 |
| `ontology contribute` | 上行 | local main → upstream PR（fork 模式；clone 模式不支持） |

`space sync` 遵循先预览后执行：dry-run 展示将贡献与更新的清单，用户确认后 `--confirm` 执行。`ontology contribute` 仅在 fork 模式下可用，clone 模式只支持 `ontology update`。

`ontology capability list` 揭示本体拥有的全部能力，是 `space capability add/remove` 的挑选依据——空间先用它发现有什么可装，再决定装什么。

空间内日常能力进化通过 Evolver 检疫提炼后，由 Fae 在空间 worktree 提交，再经 `space sync` 汇入 local main，最终经 `ontology contribute` 回流 upstream。空间装配出的能力组合若具备类型通用性，可沉淀为类型装配单，供同类空间复用。

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

提示词是核心资产。Evolver 检疫提炼并提出方案，经用户批准后由 Wopal 调度 Fae 更新中央仓库的提示词文件，实现跨空间协同进化。

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
