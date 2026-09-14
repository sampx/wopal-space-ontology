# Ontology — 空间灵魂、规约与能力基因工具包设计

> **Status**: Active
> **Updated**: 2026-09-14
> **Parent Architecture**: `docs/products/wopal-space/DESIGN.md`
> **Parent Product**: `docs/products/wopal-space/PRD.md`
> **Sub-DESIGNs**:
> - `./DESIGN-distribution.md`
> - `./DESIGN-dsh-adapter.md`
> - `./DESIGN-wopal-plugin.md`

---
## Project Role

ontology 是 WopalSpace 的 Space Ontology 层，也是空间灵魂、规约与能力基因工具包的承载面。Agent 身份、规则、技能、命令、插件、模板与辅助脚本在这里沉淀和分发；ellamaka 负责解释执行，wopal-cli 负责确定性操作编排，space runtime 负责当前空间运行态。

核心职责：空间灵魂可复用、空间规约可分发、空间能力可编排、空间经验可延续。Fork 一个 ontology = 复制一套可持续演化的空间起点。

物理分发以「中央仓库 + 空间装配 worktree」模型：local main 是能力唯一真相源，每个空间是 `space/<name>` 装配 worktree（详见 [Ontology 协作模型](#ontology-协作模型)）。加载链路相关变更在用户重启 ellamaka 后完成验证。

---

## Capability Scope

ontology 拥有的目标态能力组：

| 能力域 | 拥有的目标能力 | 明确边界 |
|---|---|---|
| Agent 体系 | 4 维核心角色（Wopal/Fae/Rook + Evolver）跨类型常驻；类型差异由 skills / rules 能力装配承载，不靠新增代理切分 | 不持有 Agent runtime 实现；不硬编码微型工种 |
| 技能生态 | 空间根 / 工作流 / 专用技能池，通过空间装配清单（BOM）按需物化与 JIT 动态注入 | 不判断技能产品价值，不负责 skill 内容设计 |
| 命令体系 | 覆盖空间维护、自进化、项目管理、开发支持、上下文管理，可覆盖内置命令 | 不实现命令执行引擎 |
| 规则体系 | 项目级 + 空间级 + 领域专属规则，wopal-plugin 条件匹配注入 | 不修改 ellamaka 核心行为 |
| 运行时插件 | wopal-plugin 提供规则注入、任务委派、记忆系统、上下文管理四大能力，7 个 plugin tools | 仅限插件内部，不侵入技能/规则/命令 |
| 模板与装配 | 空间骨架与模板 + 类型装配单（`assembly/archetypes/*.yaml`，声明 agents / skills / rules / commands / plugins / scripts） | 不持有空间运行态实例 |
| 辅助脚本 | ontology 维护、git hooks 与辅助自动化脚本 | 仅承担辅助维护动作 |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| 声明式优于命令式 | 本体声明"空间应该有什么"，引擎负责解释执行。Markdown + YAML 是一等公民。 |
| 灵魂与操作分离 | Agent 灵魂文件只定义角色边界与决策原则（"我是谁"），操作知识由技能承载（"我怎么做"）。 |
| 提示词目标化（Outcome-Oriented）优于过程干涉（Hand-Holding） | 面向 2026 前沿模型原生推理与测试时计算（TTC），提示词只给目标与验证门禁，不承载操作说教，不干涉过程。 |
| 中央能力池集中维护 + 空间装配 worktree（BOM 装配模型） | 本体资产在单一 `main` 分支集中维护，通过 `assembly/archetypes/*.yaml` 声明装配单，空间端以装配 worktree（sparse-checkout）按需物化。一处优化全域受益，进化经 `space sync` 汇入 local main。 |
| 进化的"提议权"与"实施权"分离 | Evolver 专职元认知分析、去特异化清洗与出方案（Read & Propose Only）；落地由 Wopal 统筹、Fae 在空间 worktree 内规范提交、Rook 审查守门。 |
| 插件适配原则 | wopal-plugin 是运行时插件，集中提供规则注入、任务委派、记忆系统和上下文管理，插件能实现尽量不改造 engine。 |
| 运行时装配经会话级权限落地 | 能力装配以会话级权限为注入通道，会话创建时授予、生命周期内稳定。装配参数只接受能力名称，权限规则由插件构造，Agent 不接触权限细节。 |
| Plugin instance 隔离 | Ellamaka 通过 `PluginInput.wopalSpaceRoot` 传递可选空间根。wopal-plugin 为每次 `server(input)` 调用构造独立 RuntimeContext、effective env、logger 与 memory client。 |

---

## Module Architecture

### Agent 体系

面向 2026 年具备自适应深度推理与长程规划能力的前沿模型，Agent 体系确立**“灵魂守恒、武器多态、动态装配、四维闭环”**原则：

#### 四核职能分工

| 角色 | 核心职责 | 物理权限沙箱 | 核心判据 / 行为 |
|------|---------|-------------|----------------|
| **Wopal**（主控 / 统筹脑） | 意图解析、人机对齐、宏观规划、跨空间记忆承载、任务派发 | 全量感知与派发权 (`wopal_*`, `task`, `memory_manage`)，`question: allow` | 双模确认原则（自由对话须确认，工作流按 Plan 执行）；结论先行 |
| **Fae**（执行手 / 全栈工兵） | 全栈落地编码、重构、编译构建、测试用例运行、提交验证 | `edit: allow` (全栈文件), `bash: allow`, `task: deny` (防套娃) | 必须产出客观测试与构建结果；能通过真实测试的代码是唯一指标 |
| **Rook**（审查眼 / 正交哨兵） | 独立正交质量审计、代码缺陷与安全风险排查、技术债预警 | 严格只读沙箱 (`read: allow`, `edit: deny`, `bash: allow` 仅限只读命令) | 严格遵守“无证据即无效”（Evidence-or-Downgrade），只认 `file:line` 事实 |
| **Evolver**（进化心 / 专职海关） | 会话摩擦检测、经验蒸馏、去特异化检疫、提出自进化提案 | 独立会话沙箱 (`read: allow`, `edit: deny` 对中央库只读提案) | **只出方案、不动刀**；执行严格的三级防污染分流检疫 |

#### 动态装配（Capabilities are assembled, agents are constant）
Agent soul 是角色级的，与空间类型无关。四个核心角色在所有空间常驻，类型差异由 `assembly/archetypes/<type>.yaml` 装配单声明的 skills / rules 承载：

- **Coding 空间**：四核心 + 工程类 skills / rules；
- **Content 空间**：四核心 + 内容类 skills / rules。

Fae 拿不同的「武器」执行，而不是换一个执行者；Rook 加载不同的审校技能，而不是换一个审查者。类型身份属于能力装配，不属于代理切分。专职子代理仅在出现真正不同的**角色**时才新增，且需专门设计确认，默认不增。

Ellamaka 启动时扫描 `.wopal/agents/`，看到的始终是这四个角色。

##### 装配的四个层级

能力装配分四层，各层职责与作用时机不同：

| 层级 | 决定什么 | 载体 | 作用时机 |
|------|---------|------|---------|
| **能力池** | 中央仓库拥有的全部能力 | central `main` | 跨空间持续 |
| **空间武器库** | 本空间物化了哪些能力 | `assembly/archetypes/<type>.yaml` 装配单 → sparse-checkout | 空间创建 / `space capability` |
| **角色基线** | 每个角色默认能用哪些能力 | `agents/<name>.md` 的 `permission:` | 会话创建瞬间 |
| **会话装配** | 本次任务实际授予哪些能力 | `wopal_task` 的 `capabilities` 参数 | 每次派发时 |

上三层是静态声明，第四层是运行时装配。Wopal 在派发任务时，按任务性质从空间武器库中挑选能力，装配给子会话——这是「武器多态」的运行时落点。

##### 空间武器库与角色基线的关系

物化进空间的武器库**不等于**全量授予任何角色。武器库是空间拥有的能力储备，角色基线是默认授予的子集。

未进入任何角色基线的武器对相应角色不可见。这种默认不可见是刻意的：它让 Wopal 的上下文只承载当前角色真正需要的武器清单，避免无关能力占用推理预算。

Wopal 的挑选权**不受角色基线限制**。装配给会话的能力经权限合成后覆盖基线——不配置就看不见，配置了就可用。

##### 会话装配的注入通道

会话装配通过**会话级权限**实现。能力在会话创建时授予，会话生命周期内保持稳定，中途不改变装配。授予依据是 ellamaka 的权限合并规则：后者覆盖前者，因此会话级规则能够超越角色基线。

内置工具不进会话装配。角色基线已经完整控制工具的可见性与执行授权，重复装配只会引入歧义。

装配对 skills / rules / mcp 三类能力分别生效，合成规则、注入方式与压缩后的行为细节见 `./DESIGN-wopal-plugin.md` 的能力装配模块。

#### 角色边界由职责定义
专职子代理按**角色**切分，不按文件类型或任务切片切分。职能重叠、上下文盲区与交接成本都源于按切片拆分角色，因此 Agent 体系的角色数量保持最小，能力差异由装配承载。

每个角色拥有明确的职责范围与物理权限沙箱：

- **规划与统筹**归 Wopal，规划流程由 `dev-flow` 承载；
- **全栈实施**归 Fae，编码、重构、构建、测试在单一上下文内原子共变；
- **独立审查**归 Rook，代码缺陷与安全风险的正交审计统一归口；
- **经验进化**归 Evolver，会话摩擦的蒸馏与检疫统一归口。

#### 提示词目标化与系统提示词自进化
**提示词目标化（Outcome-Oriented）**：每份 Agent 提示词保持精简，只承载角色定位、职责边界、能力武器纪律与交互风格。流程分支、操作说教与编程八股由技能与项目规范承载，不进入灵魂层。这使提示词面向前沿模型的原生推理能力，给目标与验证门禁而不干涉过程。

**系统提示词自进化（“入魂 / 入脑”）**：提示词是核心资产。Evolver 检疫提炼并提出方案，经用户批准后由 Wopal 调度 Fae 更新中央仓库的提示词文件，实现跨空间协同进化。

### 技能体系

| 层次 | 职责 | 规模 | 代表 |
|------|------|------|------|
| 空间根技能 | 流程导航、场景路由、委派基础原则 | 1 | `space-master` |
| 工作流技能 | 开发状态机、Plan 规范、委派 API、WSF 产品流水线 | ~66 | `dev-flow`、`agents-collab`、WSF 技能族 |
| 专用技能 | 独立领域能力 | ~13 | `fc-local`、`youtube-master`、`ellamaka-config`、`automating-mail`、`mac-reminder`、`git-worktrees`、`skill-creator` 等 |

每个技能遵循三级加载：元数据（name + description）→ 主体（SKILL.md body）→ 资源（scripts / references / assets）。

`space-master` 是 ontology 的根技能，但其当前实现仍偏粗糙；后续应单独重构为概念模型入口、流程选择器、核心技能路由器、ontology/worktree 协作指南与多 Space 运维入口。

### 命令体系

| 类别 | 命令 | 载体 |
|------|------|------|
| 空间维护 | `/init`、`wopal space status`、`wopal space sync`、`wopal space capability add/remove` | `commands/init.md`、CLI 命令 |
| 记忆与进化 | `/wopal:memo`、`/wopal:evolve`、`/wopal:distill`、`/wopal:memory` | `commands/wopal/` |
| 唤醒与感知 | `/wopal:summon` | `commands/wopal/summon.md` |
| 文档管理 | `/cupdate-prd`、`/cupdate-design`、`/cupdate-roadmap`、`/cupdate-agent-rules`、`/cupdate-readme` | `commands/cupdate-*.md` |
| 开发支持 | `/commit`、`/review` | `commands/commit.md`、`commands/review.md` |
| 上下文管理 | `/context-continue`、`/context-handoff`、`/context-recover` | `commands/context-*.md` |
| 其他 | `/evaluate-skill`、`/extract-br` | `commands/evaluate-skill.md`、`commands/extract-br.md` |

ontology 命令可覆盖 ellamaka 内置命令。

### 规则体系

| 类别 | 职责 | 载体 |
|------|------|------|
| 项目级规则 | 语言与框架约束 | `rules/typescript.md`、`rules/python.md` |
| 空间级规则 | 通用行为规范 | `rules/business-rules.md` |
| Agent 专属规则 | Wopal 记忆规则、Fae Astro 规则等定向约束 | `rules/wopal/mem-rule.md`、`rules/fae/astro.md` |

规则通过 wopal-plugin 在 Agent 启动时注入，按条件匹配生效。

### 插件体系

wopal-plugin 由 TypeScript 编写，Bun 执行，基于 EllaMaka Plugin SDK。

| 模块 | 职责 | 可配置 |
|------|------|--------|
| Global（入口） | 构造 instance runtime、加载三层配置、检查开关、注册 Hooks/Tools | 无 |
| Rules | 规则发现 → 条件匹配 → 注入系统提示词 | 恒启用 |
| Memory | LanceDB 存储、语义检索、记忆注入 | `wopal.memory.enabled`（总控）、`wopal.memory.injection`（仅注入） |
| Task | 非阻塞子会话启动、状态监控、双向通信、并发控制 | 恒启用 |
| Monitor | 周期性调度引擎，统一管理监控策略 | 恒启用 |
| Context | 上下文压缩与恢复、标题生成、蒸馏 | `wopal.context.enabled`（门控标题/恢复/蒸馏，压缩恒启用） |

每次 plugin invocation 以 `PluginInput.wopalSpaceRoot` 作为唯一空间根来源。字段缺失表示非 WopalSpace instance。effective env 由进程启动环境、`$WOPAL_HOME/.env` 与 `<wopalSpaceRoot>/.wopal/.env` 合并生成，并保持只读，不写回 `process.env`。

| 资源 | 非 WopalSpace | WopalSpace |
|------|---------------|------------|
| Rules | `$WOPAL_HOME/rules` | `$WOPAL_HOME/rules` + `<wopalSpaceRoot>/.wopal/rules` |
| Plugin log | `$WOPAL_HOME/logs/wopal-plugin.log` | `<wopalSpaceRoot>/.wopal-space/logs/wopal-plugin.log` |
| Memory prompts | `$WOPAL_HOME/prompts` | `<wopalSpaceRoot>/.wopal/prompts` + `$WOPAL_HOME/prompts` |
| Memory database | `$WOPAL_HOME/storage/memory` | `$WOPAL_HOME/storage/memory` |
| Session context | `$WOPAL_HOME/storage/session_context` | `$WOPAL_HOME/storage/session_context` |

#### TUI 品牌插件

`tui-ellamaka` 插件为 WopalSpace 模式注入 TUI 品牌元素：首页 logo 块字符画与阴影、提示行紧凑 logo、会话提示行 logo 与会话 ID，以及 Nord 系 `ellamaka-theme.json` 主题。该插件随 `.wopal/` ontology 分发，不属于 ellamaka 引擎仓库。

插件静态资源（主题文件、音频）随插件目录放置，由插件按相对路径解析。

### 模板体系

模板素材位于 `assembly/templates/`，由骨架声明决定渲染去向。

| Template | 渲染目标 | 职责 |
|----------|---------|------|
| `root-AGENTS.md` | `<space>/AGENTS.md` | 启动入口，指向 STRUCTURE / USER / REGULATIONS |
| `gitignore` | `<space>/.gitignore` | 忽略运行态噪音，防止日志、缓存、备份误提交 |
| `STRUCTURE.md` | `.wopal-space/STRUCTURE.md` | 空间结构模板 |
| `REGULATIONS.md` | `.wopal-space/REGULATIONS.md` | 空间守则模板 |
| `memory/USER.md` | `.wopal-space/memory/USER.md` | 用户档案模板 |
| `memory/MEMORY.md` | `.wopal-space/memory/MEMORY.md` | 文件型长期记忆模板 |
| `command.md` | 命令文件 | 命令模板 |
| `prd.md` | 产品 PRD | PRD 模板 |
| `design-product.md` | 产品 DESIGN | 总体设计模板 |
| `design-project.md` | 项目 DESIGN | 项目设计模板（含能力范围与演进路线） |
| `phase.md` | 阶段文档 | 产品阶段范围与验收条件模板 |
| `agent-rules.md` | 项目 AGENTS.md | 开发规范模板 |

模板的 schema 字段定义、生成规则、消费规则与各模板设计详见 [模板合约](#模板合约)。

### 辅助脚本体系

| 目录 | 职责 |
|------|------|
| `scripts/git-hooks/` | ontology 开发与提交阶段使用的 hooks 脚本 |
| `scripts/emt` / `scripts/oct` | 辅助维护入口脚本 |
| `scripts/oc-auto-approve.py` | 本地辅助自动化脚本 |
| `scripts/setup-git-hooks.sh` | hooks 安装脚本 |

### 配置体系与装配清单 (BOM)

#### 配置层级
三层配置，各司其职：

| 层级 | 文件 | 作用域 | Git 跟踪 | 职责 |
|------|------|--------|----------|------|
| 全局 | `~/.wopal/config/settings.jsonc` | 所有空间 | 否 | 跨空间共享的 provider、model、全局功能开关 |
| 空间级（公共）| `.wopal/config/settings.jsonc` | 当前空间 | 是 | 空间共享的 ellamaka 与插件配置，随仓库传播 |
| 空间级（私有）| `.wopal/config/settings.local.jsonc` | 当前空间 | 否（git 忽略）| 覆盖公共默认值的本地开发者配置 |

#### 装配定义目录（Assembly）

装配相关的定义集中在 `.wopal/assembly/`，与可被装配的能力资产在根目录就区分开：

```
.wopal/
├── assembly/                  # 装配定义
│   ├── archetypes/            # 类型装配单
│   │   ├── coding.yaml
│   │   └── content.yaml
│   ├── schemas/               # 空间骨架声明
│   │   ├── coding-space-schema.yaml
│   │   └── content-space-schema.yaml
│   └── templates/             # 渲染素材
│       ├── STRUCTURE.md
│       ├── REGULATIONS.md
│       ├── root-AGENTS.md
│       └── memory/
├── agents/                    # 能力资产
├── skills/
├── rules/
├── commands/
├── plugins/
├── scripts/
└── config/                    # 运行配置（settings 类）
```

装配定义与能力资产是两个层级的语义：装配定义回答「空间该长什么样、该装什么能力」，能力资产是「可被装配的武器本身」。

#### 类型装配单（Archetype Manifest）

装配单声明一个空间类型的全部装配决策，是空间初始化的唯一依据：

```yaml
# 示例: .wopal/assembly/archetypes/coding.yaml
version: 1
type: coding
description: 全栈工程研发空间

# 该类型使用的空间骨架
schema: coding-space-schema.yaml

# 该空间挂载的 Agent（四维核心角色跨类型常驻，不随类型变化）
agents:
  - wopal
  - fae
  - rook
  - evolver

# 该空间所需技能
skills:
  - dev-flow
  - agents-collab
  - git-worktrees

# 该空间加载的规则
rules:
  - typescript
  - python
  - business-rules

# 该空间加载的命令
commands:
  - init
  - commit
  - review
  - wopal/memo

# 该空间加载的插件
plugins:
  - wopal-plugin
  - dsh-adapter

# 该空间加载的脚本
scripts:
  - emt
```

装配单覆盖六类可装配能力：`agents`、`skills`、`rules`、`commands`、`plugins`、`scripts`。全部字段按名称声明，物化时在能力资产目录下解析为对应资产。

#### 空间骨架声明（Space Schema）

装配单通过 `schema` 字段选择空间骨架。骨架声明该类型空间的结构：需要哪些运行时文件、哪些目录、哪些空间级文件：

```yaml
# 示例: .wopal/assembly/schemas/coding-space-schema.yaml
version: 1
runtime:
  path: .wopal-space
  files:
    - template: STRUCTURE.md
      target: STRUCTURE.md
    - template: REGULATIONS.md
      target: REGULATIONS.md
    - template: memory/USER.md
      target: memory/USER.md
  dirs:
    - path: memory/diary
      keep: [.gitkeep]
    - path: logs
    - path: .tmp
    - path: INBOX
space:
  files:
    - template: root-AGENTS.md
      target: AGENTS.md
    - template: gitignore
      target: .gitignore
  dirs:
    - path: projects
    - path: docs
```

`runtime` 描述空间运行态（`.wopal-space/`）结构，`space` 描述空间根目录结构。`files` 声明「模板素材 → 目标路径」的映射，`dirs` 声明需要创建的目录。

不同类型的空间结构不同：coding 空间需要 `projects/`，content 空间需要 `contents/`。骨架按类型选择，使空间结构成为类型差异的一部分。

模板素材统一存放于 `assembly/templates/`，多套骨架共用。骨架只声明映射关系，不重复承载素材内容。

#### 物化流程

空间初始化时，CLI 依次执行：

1. 读取 `.wopal/assembly/archetypes/<type>.yaml`，得到装配决策
2. 按 `schema` 字段读取 `.wopal/assembly/schemas/<schema>.yaml`，得到空间骨架
3. 按骨架创建目录、渲染模板文件到空间根与 `.wopal-space/`
4. 按装配单通过 Git sparse-checkout 在 `<space>/.wopal/` worktree 内物化能力资产
5. 生成 `.wopal-space/space-meta.json`，记录类型、骨架与装配快照

空间内正常修改与提交，进化经 `space sync` 汇入 local main。

#### settings 分层与插件装配

插件分两类，装配方式不同：

| 类别 | 承载文件 | 分发方式 |
|------|---------|---------|
| 全空间通用插件 | `.wopal/config/settings.jsonc` | 随 main 分发，人工维护 |
| 空间特有插件 | 空间根 `settings.local.jsonc` | CLI 按装配单生成，git 忽略 |

通用插件（如 `wopal-plugin`、`dsh-adapter`）写入 `settings.jsonc`，所有空间一致。空间特有插件按装配单生成到 `settings.local.jsonc`，该文件可再生——换机器后重新按装配单装配即恢复。

插件在 settings 中的引用使用相对空间 config 目录的路径（`../plugins/<name>`），使同一份配置在所有空间与机器上一致。

#### 不进装配单的资产

以下资产不进入装配单，由各自机制承载：

| 资产 | 归属 | 理由 |
|------|------|------|
| `assembly/` | 装配定义 | 装配单、骨架与模板本身是物化源头，不参与物化 |
| `prompts/` | wopal-plugin | 插件内部运行时提示词，内置为插件默认值，文件层仅作可选覆盖 |
| 插件静态资源 | 所属插件目录 | 随插件走，如 `plugins/tui-ellamaka/asset/` |
| `config/settings.jsonc` | 空间配置 | 全空间通用配置，随 main 分发 |

装配定义不物化进空间：空间只承载物化结果（能力资产与 `.wopal-space/` 运行态），装配源头保留在中央仓库。CLI 初始化时从中央仓库读取装配定义，按定义物化到空间。

#### 配置分层与写入权

空间配置分两层，写入权限严格区分：

| 文件 | Git 跟踪 | 写入方 | 内容 |
|------|----------|--------|------|
| `.wopal/config/settings.jsonc` | 是（随 main 分发） | 人工维护 | 空间公共配置：instructions、permission 基准、插件相对路径引用 |
| `.wopal/config/settings.local.jsonc` | 否（gitignore） | CLI / 用户 | 私有覆盖：model、apiKey、本地 permission 覆盖 |

CLI 只写 `settings.local.jsonc`，永不改写 `settings.jsonc`——后者随 space 分支经 `space sync` 汇入 central main，任何实例相关内容写入都会污染中央能力池。

#### 权限归属与用户覆盖

Agent 的权限基准属于角色本身，写在 `agents/<name>.md` 的 frontmatter `permission:` 中，随装配物化进入空间 worktree。权限不进入类型装配单：装配单声明「装配哪些能力」，不承载权限数值。

用户若要为本空间覆盖某 agent 的权限，写入 `.wopal/config/settings.local.jsonc` 的 `ellamaka.agent.<name>.permission`。该文件被 git 忽略，覆盖只作用于当前空间，不会随 space 分支提交回 central main。ellamaka 的加载顺序保证 `settings.local.jsonc` 深合并覆盖 `settings.jsonc`，因此本地覆盖天然生效。

---

## Technical Stack Choices

| Domain | Choice | Rationale | Boundary |
|--------|--------|-----------|----------|
| 声明式格式 | Markdown + YAML | ellamaka 原生支持的声明式格式 | 不承载运行时状态 |
| 插件运行时 | TypeScript | OpenCode Plugin SDK 原生语言，Bun 执行 | 仅限插件内部，不侵入技能/规则/命令 |
| 辅助脚本 | Shell / Python | 适合 hooks 安装、开发辅助和轻量自动化 | 仅承担辅助维护动作，不替代插件运行时能力 |
| 记忆存储 | LanceDB | 嵌入式向量数据库，零运维，向量 + FTS + LIKE 混合检索 | 仅记忆模块使用，不作为空间主存储 |
| 版本控制与分发 | Git | clone / fork + 装配 worktree 模型；中央仓库承载能力演化，空间 worktree 按装配单物化 | 不替代空间运行态结构 |

---

## Interfaces and Contracts

### ellamaka 加载接口

ellamaka 在 wopal-space mode 下从 ontology 加载：

1. `agents/*.md` — Agent 灵魂定义与 frontmatter 权限配置
2. `skills/*/SKILL.md` — 技能元数据与指令（按触发条件注入）
3. `commands/*.md` 与 `commands/wopal/*.md` — 命令定义（可覆盖内置命令）
4. `plugins/<name>/` — 插件目录；在 `config/settings.jsonc` 中以相对路径 `../plugins/<name>` 声明
5. `config/settings.jsonc` + `config/settings.local.jsonc` — 空间级配置（公共 + 私有覆盖）

多数加载链路相关改动以 ellamaka 重启后的加载结果作为验证标准。

### wopal-plugin 工具接口

| 工具 | 职责 |
|------|------|
| `wopal_task` | 非阻塞子会话启动，可携带能力装配参数 |
| `wopal_task_output` | 任务状态与输出查询 |
| `wopal_task_reply` | 双向通信与恢复 |
| `wopal_task_abort` | 任务终止 |
| `wopal_task_finish` | 任务完成清理 |
| `wopal_capability_list` | 列出空间武器库可用能力（含未授予任何角色的） |
| `memory_manage` | LanceDB 记忆 CRUD 与语义检索（list/stats/search/add/update/delete/injected） |
| `context_manage` | 会话上下文管理（status/dump/compact）+ 蒸馏（distill/confirm/cancel） |

`wopal_capability_list` 暴露空间武器库全量能力，`wopal_task` 的装配参数只接受能力名称数组。清单字段、清单契约与派发契约的完整定义见 `./DESIGN-wopal-plugin.md` 的能力装配模块。

### 初始化与维护目标

Ontology 提供初始化协议，wopal-cli 负责确定性 materialize，`/init` 负责智能校准。CLI 实现建立在 ontology 模板、schema 与 `/init` 维护机制逐步验证成熟的基础上。

`wopal space init` 是创建/初始化入口。新建、已有目录补齐、合法 space 注册与 active space 设置均由 `space init` 承载。

clone 模式为默认，`--fork` 进入 fork 模式（详见 [Ontology 协作模型](#ontology-协作模型)）。`STRUCTURE.md` 模板中的 ontology source 使用 `${ONTOLOGY_REPO}` 占位符。

空间类型选择：

```bash
wopal space init my-space --type coding
wopal space init my-space --type content
```

- `--type` 为必填，`coding` 与 `content` 是当前支持的类型。类型语义由装配单承载，本地中央仓库 `main` 是能力合集，不对应任何空间类型。
- `--type coding` 使用 `assembly/archetypes/coding.yaml` 装配单，声明该类型默认装配的能力与所用骨架。
- 装配单存在且可读；空间初始化时按装配单 sparse-checkout 物化能力文件。
- 用户可在初始化后通过 `wopal space capability add/remove` 调整空间装配清单。

User 解析：fork 模式优先从 `origin` remote 解析 GitHub owner；clone 模式尝试 `gh api user`；fallback OS 用户名 slug 化。

空间装配记录：`.wopal-space/space-meta.json` 记录类型、骨架、来源 revision、装配时间与装配快照。

配置写入 `$WOPAL_HOME/config/settings.jsonc` 的 `ontologies.<name>` 节点（含 `path`、`origin`、`upstream`、`fork`）和 `spaces.<name>` 节点（含 `ontology`、`branch`、`user`、`type`）。

CLI 负责：

1. 解析 space name/path 与 ontology source。
2. 读取 `assembly/archetypes/<type>.yaml`，得到装配决策与 `schema` 指向。
3. 读取 `assembly/schemas/<schema>.yaml` 与 `assembly/templates/` 素材。
4. 准备 `<space>/.wopal/` 装配 worktree（sparse-checkout 按装配单物化）。
5. 按骨架创建运行态目录与空间级目录。
6. 首次渲染骨架声明的全部文件到空间根与 `.wopal-space/`。
7. 按装配单生成空间特有插件配置到 `settings.local.jsonc`。
8. 写入 `.wopal-space/space-meta.json`（类型、骨架与装配快照）。
9. rerun 时创建缺失项并保留已有文件内容。
10. 在完整成功后注册 space 并设置 active space。
9. 提供 `wopal space scan` 只读扫描入口，输出 repo / module JSON 事实。
10. 输出下一步：进入 space、启动 ellamaka、运行 `/init` 做首次智能校准。

CLI 边界：

- `wopal space scan` 聚焦 repo / module 事实发现和已有描述提取。`STRUCTURE.md` 读写由 `/init` 负责。
- `/init` 承担 scan JSON 消费、结构更新方案生成和用户确认后的写入。
- 用户与 `/wopal:evolve` 承担运行态文件内容维护。
- 用户确认流程承接 `REGULATIONS.md` 差异吸收。
- 记忆命令承接用户偏好与长期记忆沉淀。
- 项目规则命令承接项目业务规则维护。

`/init` 负责：

1. 读取 `.wopal-space/STRUCTURE.md`。
2. 调用或消费 `wopal space scan` 输出的 repo / module JSON 事实。
3. 按 compact schema 与 managed/user block 规则生成 frontmatter/table diff。
4. 校验 `.wopal-space/` runtime 固定结构，不深扫 runtime 内容，不把 runtime 写入 table。
5. 提示模板与实例文件之间需要用户人工处理的差异。
6. 先输出 plan/diff，等待用户确认后写入。

### 模板合约

本节定义各模板的 schema、字段、生成规则与消费规则。

#### `STRUCTURE.md` schema 与生成规则

`STRUCTURE.md` 是空间实例的 compact 结构事实文件。它会进入 Agent 启动上下文，因此实例文件只保留低 token、高价值、可行动的空间索引，不承载全量扫描清单。

文件由两层组成：

1. **YAML frontmatter**：机器可解析的启动索引，用于定位空间组件、固定运行态目录和已确认的高价值 repo。
2. **Markdown table**：Agent / 人类可读的空间资产地图，用于解释已确认资产路径、类型、层级和职责。

frontmatter 生成规则：

- 保留 `version`、`space`、`space-component-type`、`ontology-worktree`、`space-runtime` 和 `repos`。
- `space-runtime` 保留目录 / 文件用途描述，因为它直接进入 Agent 启动上下文；`.wopal-space/` 不进入 Markdown table。
- `repos` 只记录 pinned / high-value repo，不记录 scan 发现的全量 repo；大量低频 repo 留在 scan 输出或用户手工说明中。
- frontmatter 不记录 `collection`、普通 module、全量 `AGENTS.md`、docs 子目录或临时扫描结果。
- 用户未知 key 必须保留；结构 key 由 `/init` 在展示 diff 并获得用户确认后更新。

Markdown table schema：

| Field | Meaning |
|---|---|
| `path` | 相对 space root 的路径 |
| `type` | 组件类型，如 `ontology-worktree`、`space-runtime`、`projects`、`contents`、`labs`、`docs` |
| `level` | 结构层级，如 `worktree`、`repo`、`clone`、`module`、`collection`、`dir` |
| `description` | Agent 可读职责说明，不写规则正文 |

Markdown table 维护规则：

- 表格分为 managed block 与 user block；managed block 可由 `/init` 在确认后重写，user block 永不修改。
- managed block 默认只放 `.wopal` 固定关键模块、frontmatter pinned repos、用户确认的重要 module / collection。
- root `AGENTS.md` 是 ellamaka 启动入口，不进入表格。
- `wopal space scan` 发现的新 repo 或 `AGENTS.md` 模块不自动进入表格；`/init` 只报告并等待用户确认。
- 用户从 managed table 删除的非固定资产，不得因再次扫描被静默补回。

描述来源规则：

- 受控 repo / module 的首选描述来源是对应 `AGENTS.md` frontmatter `description`。
- 次选来源是 `AGENTS.md` positioning / 第一段、`README.md` 第一段或 package metadata description。
- CLI scan 只提取已有描述，不生成描述；需要新描述时由 `/init` 展示方案并等待用户确认。

维护边界：

- CLI 按模板创建初始 `STRUCTURE.md`，并由 `wopal space scan` 提供 repo / module 事实扫描 JSON。
- `/init` 负责后续结构校准：消费 scan JSON、对照 compact schema 生成更新方案、保留用户描述，并在用户确认后写入。
- schema 与生成规则维护在设计文档和模板说明中；空间实例的 `STRUCTURE.md` 聚焦结构事实。

#### 最小空间模板设计

P1 初始化模板表达可启动 WopalSpace 的最小协议，聚焦通用结构而非特定 space 的组织习惯。

CLI 首次初始化必须创建：

```text
<space>/
  AGENTS.md
  .gitignore
  .wopal/
  projects/
  contents/
  docs/
  .wopal-space/
    STRUCTURE.md
    REGULATIONS.md
    memory/
      USER.md
      MEMORY.md
      diary/
    logs/
    .tmp/
    INBOX/
    backup/
```

`projects/`、`contents/`、`docs/` 是 WopalSpace 的核心工作容器，必须初始化并写入 `STRUCTURE.md`。`labs/`、`external/`、`scripts/` 属于特定 space 的组织扩展，不进入最小模板；若用户后续创建这些目录，由 `/init` 扫描后再写入实例 `STRUCTURE.md`。

空间骨架声明确定性创建结构与模板映射，消费规则见「骨架消费规则」。

`.gitignore` 由 CLI 首次渲染；重复初始化时若已存在 `.gitignore`，CLI 保留现有内容，并报告缺失的 WopalSpace 建议忽略项。

#### 骨架消费规则

CLI 读取骨架后按以下规则消费：

- `runtime.path` 指向 `.wopal-space/`，其中 `files.target` 是相对 runtime path 的路径。
- `space.files.target` 是相对 space root 的路径。
- `template` 从 `assembly/templates/` 读取。
- `keep` 表示创建目录后可写入 `.gitkeep` 保留空目录。
- 必需模板缺失时，CLI 以 fail fast 方式报告缺失模板与 ontology source/path，并保持 space registry 与 active space 状态不变。

骨架决定该类型空间的最小结构。扩展目录（如 `labs/`、`external/`）由用户创建后经 `/init` 扫描写入实例 `STRUCTURE.md`。

#### `root-AGENTS.md` 模板设计

`root-AGENTS.md` 作为模板存在，实例化目标是 space root 的 `AGENTS.md`。它定位为空间启动提示与用户个性化规则入口。

模板职责：

1. 提醒 Agent 在上下文压缩或信息缺失时可重新读取 `.wopal-space/STRUCTURE.md`、`.wopal-space/REGULATIONS.md`、`.wopal-space/memory/USER.md` 与 `.wopal-space/memory/MEMORY.md`。
2. 提供用户空间个性化规则的写入位置。

空间事实由 `STRUCTURE.md` 承载，工作规则由 `REGULATIONS.md` 承载，详细技能路由由 `space-master` 承载。

#### `REGULATIONS.md` 模板设计

P1 的 `REGULATIONS.md` 初始化时写入通用空间守则，之后作为用户可持续维护的运行态文件。ontology 守则升级通过 diff/建议呈现，由用户确认后吸收。

模板应包含以下通用规则族：

- 安全红线：误删防护、工作边界、目录保护、敏感信息保护。
- Git 基本法：实施前检查、提交前检查、提交格式、历史不可变原则。
- 子代理委托：任何委派前加载 `agents-collab`，并遵守路径与目标项目上下文检查。
- 记忆与进化：长期记忆写入需去重、展示、等待用户确认。
- 核心技能入口：介绍 `space-master`、`agents-collab`、`dev-flow` 三个空间核心技能。

核心技能概要：

| 技能 | 空间职责 | 触发场景 |
|---|---|---|
| `space-master` | 空间技能根与流程路由总入口 | 任务意图不清、空间运维、ontology 协作、技能体系、流程选择、多 Space 管理 |
| `agents-collab` | 子代理协作协议 | 任何 fae、rook 或 general 子代理委派前 |
| `dev-flow` | Issue/Plan 驱动开发状态机 | Issue、Plan、审批、执行、验证、归档 |

### Design Document Layering

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

### Distribution Summary

ontology 的分发走 Git source + worktree 模型。wopal-cli 通过 `wopal space init` / `wopal setup` 封装 clone/fork/worktree 过程，将其与 space runtime 初始化串联。

稳定边界：

1. 默认使用 clone-based canonical source flow。
2. `--fork` 是显式选择的替代模式。
3. `space/<space-name>` 分支承载 space-specific 演化。
4. `<space>/.wopal/` 是 ontology worktree，由 CLI materialize，由 ellamaka 运行时加载。

详细 source 输入、materialization、template handoff 和 runtime loading handoff 见 `./DESIGN-distribution.md`。

### Base Capabilities and Space Overlay

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

### Ontology 协作模型

Ontology 以「中央能力池 + 空间装配 worktree」模型承载能力演化。一个空间是能力池的一次**可写装配视图**：能力组合由装配单决定，能力内容在空间内可写可进化，进化通过 `space sync` 汇入用户级能力池。

#### 分层结构

两级仓库，职责单一：

- **本地中央仓库（`~/.wopal/ontologies/<source>/`，`local main` 分支）**：用户级稳定能力池；所有公共 `agents/`、`skills/`、`rules/`、`commands/`、`plugins/` 与类型装配单的唯一真相源。跟踪 upstream/main。
- **空间装配 worktree（`<space>/.wopal/`，`space/<name>` 分支）**：按空间装配单 sparse-checkout 物化的**真实可写文件**视图。Agent 在此正常修改与提交，无需空间外写权限。

类型语义由装配单承载，不设 `type/*` 分支层级。

#### 装配单（BOM）

两层装配单，各司其职：

1. **类型装配单**（本地中央仓库 `assembly/archetypes/<type>.yaml`）：声明空间类型的默认能力组合与所用骨架，是空间初始化与重建的模板；作为公共能力随中央库演进，可贡献升级。
2. **空间装配快照**（空间运行态 `.wopal-space/space-meta.json`）：记录本空间的实际装配——`type`、`schema`、来源 `revision`、`assembledAt` 与显式能力列表。由 CLI 初始化并维护，用户通过 `wopal space capability add/remove` 增删能力，不手工编辑。

装配物化使用 Git `sparse-checkout`：空间 worktree 只物化装配单选中的路径，共享中央仓库对象库，不复制历史。

#### 核心规则

1. **local main 是能力唯一真相源**：共享能力不维护空间私有版本；空间的独有提交是待贡献的进化，不是长期分叉。
2. **`space sync` 定序：先上行、后下行**：先汇入空间独有进化，再 fast-forward 到 local main 最新，最终两分支指向同一提交。
3. **正常推进一律 fast-forward**：空间分支必须可对齐时才能推进；有待贡献提交时先贡献，有未提交修改时先处理工作区。
4. **冲突在隔离临时 worktree 中处理**：整合成功才推进 live space 与 local main 引用；失败双方保持原状。
5. **更新/移除/贡献前检查工作区状态**：CLI 以工作区事实为准，不单信 Git 命令退出码。

#### 自进化闭环：Evolver 专职海关与提议-实施权责分立

空间运行中产生的能力进化遵循严格的防特异性泄漏与海关检疫机制：

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

#### 维护与分发命令面

空间侧与 ontology 侧命令职责分离，语义稳定：

| 命令 | 方向 | 职责 |
|------|------|------|
| `space status` | — | 只读：落后 / 待贡献 / 装配状态 |
| `space sync` | 双向 | 与 local main 对齐：先上行（隔离整合空间独有进化）再下行（fast-forward 到最新），刷新装配版本 |
| `space capability add/remove` | — | 增删空间装配单中的能力，重新物化 |
| `ontology update` | 下行 | upstream/main → local main，本地中央仓库整合 |
| `ontology contribute` | 上行 | local main → upstream PR（fork 模式；clone 模式不支持） |

`space sync` 遵循先预览后执行：dry-run 展示将贡献与更新的清单，用户确认后 `--confirm` 执行。`ontology contribute` 仅在 fork 模式下可用，clone 模式只支持 `ontology update`。

空间内日常能力进化通过 Evolver 检疫提炼后，由 Fae 在空间 worktree 提交，再经 `space sync` 汇入 local main，最终经 `ontology contribute` 回流 upstream。

---
## Data and State Model

ontology 本身是无状态的声明式能力包，不持有运行时状态：

| State | Location | Owner | Rules |
|-------|----------|-------|-------|
| Agent 灵魂定义 | `agents/*.md` | ontology | 定义者，ellamaka 加载执行 |
| 技能定义 | `skills/*/SKILL.md` | ontology | 定义者，按触发条件注入 |
| 规则定义 | `rules/*.md` | ontology + wopal-plugin | ontology 定义，wopal-plugin 执行注入 |
| 命令定义 | `commands/*.md` | ontology + ellamaka | ontology 定义，ellamaka 执行 |
| 辅助脚本 | `scripts/**` | ontology | 维护与辅助自动化载体 |
| 插件运行时状态 | wopal-plugin 进程内 | wopal-plugin | 运行载体，ontology 不持有 |
| 记忆数据 | `$WOPAL_HOME/storage/memory` 下的 LanceDB | memory_manage | ontology 提供工具，不持有数据 |
| 会话状态 | ellamaka session | ellamaka | ontology 不持有 |
| 空间结构 | `.wopal-space/STRUCTURE.md` | `/init` | ontology 提供模板，不持有实例 |
| 空间装配快照 | `.wopal-space/space-meta.json` | `wopal space` CLI | 记录空间类型、骨架、来源 revision、装配时间与装配快照 |
| 空间守则 | `.wopal-space/REGULATIONS.md` | 用户 + `/wopal:evolve` | ontology 提供初始化模板，不持有实例 |

Runtime 维护由 ontology commands 驱动：`/init`（结构校准）、`/wopal:memo`（日记暂存）、`/wopal:evolve`（经验沉淀）、`/wopal:distill`（记忆蒸馏）、`/cupdate-agent-rules`（项目规范更新）。

### Memory Runtime Files

空间运行时记忆由多层文件/存储组成，各有明确的维护者：

| File / Store | 职责 | Maintainer |
|---|---|---|
| `memory/USER.md` | 稳定用户偏好、沟通方式、工作习惯 | `/wopal:evolve` |
| `memory/MEMORY.md` | 适合文件保存的空间级经验 | `/wopal:evolve` |
| `memory/diary/` | 会话经验和候选沉淀暂存池 | `/wopal:memo` / `/wopal:evolve` |
| LanceDB | 可检索可注入的记忆 | `memory_manage` / `/wopal:distill` / `/wopal:memory` |

规则：

1. USER.md 记录稳定用户偏好和画像。
2. MEMORY.md 记录适合文件保存的空间级经验。
3. LanceDB 记录可检索的知识、经验、避坑。
4. diary 是暂存池，不是最终知识库。
5. 可从代码直接获得的信息不污染长期记忆层。

---

## Related Documents

| 文档 | 说明 |
|------|------|
| `projects/wopal-cli/docs/DESIGN.md` | wopal-cli 子系统设计 — 统一操作入口 |
| `.wopal/docs/BUSINESS_RULES.md` | 本体业务规则 |
