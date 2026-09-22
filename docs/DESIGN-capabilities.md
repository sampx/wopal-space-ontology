# DESIGN — Capability System

> **Status**: Active
> **Updated**: 2026-09-21
> **Parent**: `./DESIGN.md`（ontology overall design: Module Architecture section）
> **Parent Architecture**: `../../docs/products/wopal-space/DESIGN.md`
> **Parent Product**: `../../docs/products/wopal-space/PRD.md`

---

## Agent System

面向 2026 年具备自适应深度推理与长程规划能力的前沿模型，Agent 体系确立**“灵魂守恒、武器多态、动态装配、四维闭环”**原则。

### Four Core Roles

| 角色 | 核心职责 | 物理权限沙箱 | 核心判据 / 行为 |
|------|---------|-------------|----------------|
| **Wopal**（主控 / 统筹脑） | 意图解析、人机对齐、宏观规划、跨空间记忆承载、任务派发 | 全量感知与派发权 (`wopal_*`, `task`, `memory_manage`)，`question: allow` | 双模确认原则（自由对话须确认，工作流按 Plan 执行）；结论先行 |
| **Fae**（执行手 / 全栈工兵） | 一切实施类工作：编码、重构、构建、测试、写作、编辑、数据处理 | `edit: allow`, `bash: allow`, `task: deny`（防套娃） | 必须产出客观证据；能通过真实验证的成果是唯一指标 |
| **Rook**（审查眼 / 正交哨兵） | 一切产出质量的独立审计：方案、实施成果、文稿与数据 | 严格只读沙箱 (`read: allow`, `edit: deny`, `bash: allow` 仅限只读命令) | 严格遵守“无证据即无效”（Evidence-or-Downgrade），只认 `file:line` 事实 |
| **Maka**（进化心 / 专职海关） | 会话摩擦检测、经验蒸馏、去特异化检疫、提出自进化提案 | 独立会话沙箱 (`read: allow`；`edit` 仅放开 `docs/evolutions/`) | **只出提案、不动刀**；执行严格的三级防污染分流检疫 |

### Role Boundaries Defined by Responsibility

专职子代理按**角色**切分，不按文件类型或任务切片切分。职能重叠、上下文盲区与交接成本都源于按切片拆分角色，因此 Agent 体系的角色数量保持最小，能力差异由装配承载。

每个角色拥有明确的职责范围与物理权限沙箱：

- **规划与统筹**归 Wopal，规划流程由 `dev-flow` 承载；
- **全栈实施**归 Fae，编码、重构、构建、测试在单一上下文内原子共变；
- **独立审查**归 Rook，代码缺陷与安全风险的正交审计统一归口；
- **经验进化**归 Maka，会话摩擦的蒸馏与检疫统一归口。

### Dynamic Assembly

Agent soul 是角色级的，与空间类型无关。四个核心角色在所有空间常驻，类型差异由 `assembly/archetypes/<type>.yaml` 装配单声明的 skills / rules 承载：

- **Coding 空间**：四核心 + 工程类 skills / rules；
- **Content 空间**：四核心 + 内容类 skills / rules。

Fae 拿不同的「武器」执行，而不是换一个执行者；Rook 加载不同的审校技能，而不是换一个审查者。类型身份属于能力装配，不属于代理切分。专职子代理仅在出现真正不同的**角色**时才新增，且需专门设计确认，默认不增。

Ellamaka 启动时扫描 `.wopal/agents/`，看到的始终是这四个角色。

#### Four Assembly Layers

能力装配分四层，各层职责与作用时机不同：

| 层级 | 决定什么 | 载体 | 作用时机 |
|------|---------|------|---------|
| **能力池** | 中央仓库拥有的全部能力 | central `main` | 跨空间持续 |
| **空间武器库** | 本空间物化了哪些能力 | `assembly/archetypes/<type>.yaml` 装配单 → sparse-checkout | 空间创建 / `space capability` |
| **角色基线** | 每个角色默认能用哪些能力 | `agents/<name>.md` 的 `permission:` | 会话创建瞬间 |
| **会话装配** | 本次任务实际授予哪些能力 | `wopal_task` 的 `capabilities` 参数 | 每次派发时 |

上三层是静态声明，第四层是运行时装配。Wopal 在派发任务时，按任务性质从空间武器库中挑选能力，装配给子会话——这是「武器多态」的运行时落点。

#### Space Arsenal and Role Baseline

物化进空间的武器库**不等于**全量授予任何角色。武器库是空间拥有的能力储备，角色基线是默认授予的子集。

未进入任何角色基线的武器对相应角色不可见。这种默认不可见是刻意的：它让 Wopal 的上下文只承载当前角色真正需要的武器清单，避免无关能力占用推理预算。

Wopal 的挑选权**不受角色基线限制**。装配给会话的能力经权限合成后覆盖基线——不配置就看不见，配置了就可用。

#### Session Assembly Injection Channel

会话装配通过**会话级权限**实现。能力在会话创建时授予，会话生命周期内保持稳定，中途不改变装配。授予依据是 ellamaka 的权限合并规则：后者覆盖前者，因此会话级规则能够超越角色基线。

内置工具不进会话装配。角色基线已经完整控制工具的可见性与执行授权，重复装配只会引入歧义。

装配对 skills / rules / mcp 三类能力分别生效，合成规则、注入方式与压缩后的行为细节see the Capability Assembly Module in `./DESIGN-wopal-plugin.md`.

### Outcome-Oriented Prompts

每份 Agent 提示词保持精简，只承载角色定位、职责边界、能力武器纪律与交互风格。流程分支、操作说教与编程八股由技能与项目规范承载，不进入灵魂层。这使提示词面向前沿模型的原生推理能力，给目标与验证门禁而不干涉过程。

## Skill System

| 层次 | 职责 | 规模 | 代表 |
|------|------|------|------|
| 空间根技能 | 流程导航、场景路由、委派基础原则 | 1 | `space-master` |
| 工作流技能 | 开发状态机、Plan 规范、委派 API、WSF 产品流水线 | ~66 | `dev-flow`、`ontology-evolution`、`agents-collab`、WSF 技能族 |
| 专用技能 | 独立领域能力 | ~13 | `fc-local`、`youtube-master`、`ellamaka-config`、`automating-mail`、`mac-reminder`、`git-worktrees`、`skill-creator` 等 |

每个技能遵循三级加载：元数据（name + description）→ 主体（SKILL.md body）→ 资源（scripts / references / assets）。

两个工作流技能按对象分工：`dev-flow` 面向 `projects/` 下的代码仓库，`ontology-evolution` 面向空间自身的本体能力资产。四个核心角色在所有空间类型常驻，本体能力进化因此对每个空间可用，不依赖空间是否装配代码开发工作流。两条流程的状态词汇互不重合，实施与交付纪律见 `./DESIGN-evolution.md`。

`space-master` 是 ontology 的根技能，但其当前实现仍偏粗糙；后续应单独重构为概念模型入口、流程选择器、核心技能路由器、ontology/worktree 协作指南与多 Space 运维入口。

## Command System

| 类别 | 命令 | 载体 |
|------|------|------|
| 空间维护 | `/init`、`wopal space status`、`wopal space sync`、`wopal space capability add/remove` | `commands/init.md`、CLI 命令 |
| 记忆与进化 | `/wopal:memo`、`/wopal:evolve`、`/wopal:distill`、`/wopal:memory` | `commands/wopal/` |
| 唤醒与感知 | `/wopal:summon` | `commands/wopal/summon.md` |
| 文档管理 | `/cupdate-prd`、`/cupdate-design`、`/cupdate-roadmap`、`/cupdate-readme`、`/cupdate-br`、`/cupdate-agent-rules` | `commands/cupdate-*.md` |
| 开发支持 | `/commit`、`/review` | `commands/commit.md`、`commands/review.md` |
| 上下文管理 | `/context-continue`、`/context-handoff`、`/context-recover` | `commands/context-*.md` |
| 其他 | `/evaluate-skill` | `commands/evaluate-skill.md` |

ontology 命令可覆盖 ellamaka 内置命令。

## Rule System

| 类别 | 职责 | 载体 |
|------|------|------|
| 项目级规则 | 语言与框架约束 | `rules/typescript.md`、`rules/python.md` |
| Agent 专属规则 | Wopal 记忆规则、Fae Astro 规则等定向约束 | `rules/wopal/mem-rule.md`、`rules/fae/astro.md` |

规则通过 wopal-plugin 在 Agent 启动时注入，按条件匹配生效。规则注入为 opt-in，受 `wopal.rules.enabled` 控制，默认关闭。

## Plugin System

wopal-plugin 由 TypeScript 编写，Bun 执行，基于 EllaMaka Plugin SDK。

| 模块 | 职责 | 可配置 |
|------|------|--------|
| Global（入口） | 构造 instance runtime、加载三层配置、检查开关、注册 Hooks/Tools | 无 |
| Rules | 规则发现 → 条件匹配 → 注入用户消息 | `wopal.rules.enabled`（默认关闭，opt-in） |
| Memory | LanceDB 存储、语义检索、记忆注入 | `wopal.memory.enabled`（总控）、`wopal.memory.injection`（仅注入） |
| Task | 非阻塞子会话启动、状态监控、双向通信、并发控制 | 恒启用 |
| Monitor | 周期性调度引擎，统一管理监控策略 | 恒启用 |
| Context | 上下文压缩与恢复、标题生成、蒸馏 | `wopal.context.enabled`（门控标题/恢复/蒸馏，压缩恒启用） |

每次 plugin invocation 以 `PluginInput.wopalSpaceRoot` 作为唯一空间根来源。字段缺失表示非 WopalSpace instance。effective env 由进程启动环境、`$WOPAL_HOME/.env` 与 `<wopalSpaceRoot>/.wopal/.env` 合并生成，并保持只读，不写回 `process.env`。

| 资源 | 非 WopalSpace | WopalSpace |
|------|---------------|------------|
| Rules | `$WOPAL_HOME/rules` | `$WOPAL_HOME/rules` + `<wopalSpaceRoot>/.wopal/rules` |
| Plugin log | `$WOPAL_HOME/logs/wopal-plugin.log` | `<wopalSpaceRoot>/.wopal-space/logs/wopal-plugin.log` |
| Memory prompts | `$WOPAL_HOME/prompts` | `<pluginRoot>/prompts` + `$WOPAL_HOME/prompts` |
| Memory database | `$WOPAL_HOME/storage/memory` | `$WOPAL_HOME/storage/memory` |
| Session context | `$WOPAL_HOME/storage/session_context` | `$WOPAL_HOME/storage/session_context` |

### TUI Brand Plugin

`tui-ellamaka` 插件为 WopalSpace 模式注入 TUI 品牌元素：首页 logo 块字符画与阴影、提示行紧凑 logo、会话提示行 logo 与会话 ID，以及 Nord 系 `ellamaka-theme.json` 主题。该插件随 `.wopal/` ontology 分发，不属于 ellamaka 引擎仓库。

插件静态资源（主题文件、音频）随插件目录放置，由插件按相对路径解析。

## Template System

空间骨架模板素材位于 `assembly/templates/`，由骨架声明决定渲染去向。

| Template | 渲染目标 | 职责 |
|----------|---------|------|
| `root-AGENTS.md` | `<space>/AGENTS.md` | 启动入口，指向 STRUCTURE / USER / REGULATIONS |
| `gitignore` | `<space>/.gitignore` | 忽略运行态噪音，防止日志、缓存、备份误提交 |
| `STRUCTURE.md` | `.wopal-space/STRUCTURE.md` | 空间结构模板 |
| `REGULATIONS.md` | `.wopal-space/REGULATIONS.md` | 空间守则模板 |
| `memory/USER.md` | `.wopal-space/memory/USER.md` | 用户档案模板 |
| `memory/MEMORY.md` | `.wopal-space/memory/MEMORY.md` | 文件型长期记忆模板 |
| `BOOTSTRAP.md` | `<space>/BOOTSTRAP.md` | 首次启动引导，`/init` 完成后删除 |
| `command.md` | 命令文件 | 命令模板 |

模板的 schema 字段定义、生成规则、消费规则与各模板设计see the Template Contract in `./DESIGN-assembly.md`.

> 文档撰写模板（PRD / DESIGN / Phase / AGENTS.md）是技能资产，随 `dev-doc-master` 与 `space-master` 技能分发，由 `/cupdate-*` 命令消费，不进入空间装配。

## Script System

| 目录 | 职责 |
|------|------|
| `scripts/git-hooks/` | ontology 开发与提交阶段使用的 hooks 脚本 |
| `scripts/emt` / `scripts/oct` | 辅助维护入口脚本 |
| `scripts/oc-auto-approve.py` | 本地辅助自动化脚本 |
| `scripts/setup-git-hooks.sh` | hooks 安装脚本 |
