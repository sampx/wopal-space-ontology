# DESIGN — Assembly Model

> **Status**: Active
> **Updated**: 2026-09-14
> **Parent**: `./DESIGN.md`（ontology overall design: Module Architecture section）
> **Parent Architecture**: `../../docs/products/wopal-space/DESIGN.md`
> **Parent Product**: `../../docs/products/wopal-space/PRD.md`

---

## Assembly Definitions vs Capability Assets

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

装配定义不物化进空间：空间只承载物化结果（能力资产与 `.wopal-space/` 运行态），装配源头保留在中央仓库。CLI 初始化时从中央仓库读取装配定义，按定义物化到空间。

## Archetype Manifest

装配单声明一个空间类型的全部装配决策，是空间初始化的唯一依据：

```yaml
# 示例: .wopal/assembly/archetypes/coding.yaml
version: 1
type: coding
description: 全栈工程研发空间

# 空间骨架。省略时按约定取 <type>-space-schema.yaml
# schema: coding-space-schema.yaml

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

装配单覆盖五类可装配能力：`agents`、`skills`、`rules`、`commands`、`plugins`。全部字段按名称声明，物化时在能力资产目录下解析为对应资产。

脚本等扩展类目的装配语义在后续演进中定义。

## Space Schema

装配单通过 `schema` 字段选择空间骨架。骨架声明该类型空间的结构：需要哪些运行时文件、哪些目录、哪些空间级文件。

`schema` 字段可省略，此时按约定取同名骨架 `<type>-space-schema.yaml`。约定覆盖多数场景，显式声明服务于复用既有骨架的定制类型——例如行业类型放置自己的装配单、但沿用 `coding` 的空间结构时，写入 `schema: coding-space-schema.yaml` 即可。

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

### Schema Consumption Rules

CLI 读取骨架后按以下规则消费：

- `runtime.path` 指向 `.wopal-space/`，其中 `files.target` 是相对 runtime path 的路径。
- `space.files.target` 是相对 space root 的路径。
- `template` 从 `assembly/templates/` 读取。
- `keep` 表示创建目录后可写入 `.gitkeep` 保留空目录。
- 必需模板缺失时，CLI 以 fail fast 方式报告缺失模板与 ontology source/path，并保持 space registry 与 active space 状态不变。

骨架决定该类型空间的最小结构。扩展目录（如 `labs/`、`external/`）由用户创建后经 `/init` 扫描写入实例 `STRUCTURE.md`。

## Materialization Flow

空间初始化时，CLI 依次执行：

1. 读取 `.wopal/assembly/archetypes/<type>.yaml`，得到装配决策
2. 按 `schema` 字段读取 `.wopal/assembly/schemas/<schema>.yaml`，得到空间骨架
3. 按骨架创建目录、渲染模板文件到空间根与 `.wopal-space/`
4. 按装配单通过 Git sparse-checkout 在 `<space>/.wopal/` worktree 内物化能力资产
5. 生成 `.wopal-space/space-meta.json`，记录类型、骨架与装配快照

空间内正常修改与提交，进化经 `space sync` 汇入 local main。

### Capability Name Resolution

装配单以**能力名**声明能力（如 `skills: [dev-flow]`），物化前解析为仓库内路径。解析按类目尝试候选形态，取第一个存在者：

| 类目 | 候选形态 | 例 |
|------|----------|-----|
| `skills` | `<cat>/<name>` | `dev-flow` → `skills/dev-flow/` |
| `rules` | `<cat>/<name>`、`<cat>/<name>.md` | `typescript` → `rules/typescript.md` |
| `commands` | `<cat>/<name>`、`<cat>/<name>.md` | `commit` → `commands/commit.md`；`wopal` → `commands/wopal/` |
| `agents` | `<cat>/<name>`、`<cat>/<name>.md` | `wopal` → `agents/wopal.md` |
| `plugins` | `<cat>/<name>`、`<cat>/<name>.md` | `wopal-plugin` → `plugins/wopal-plugin.md` |

`commands` 与 `agents` 同时存在文件形态与目录形态，因此候选顺序不能按类目固定，须逐项探测。名称无法解析为任何存在路径时 fail fast，报告名称、类目与 ontology source。

### Sparse Materialization Mechanics

物化使用 Git `sparse-checkout`（non-cone 模式，支持文件级路径），机制约束如下：

- **基础定义始终物化**：装配单（`assembly/archetypes/<type>.yaml`）、骨架（`assembly/schemas/<schema>.yaml`）、模板（`assembly/templates/`）与仓库根 `.gitignore` 无条件包含在稀疏范围内。
- **`.gitignore` 必须物化**：gitignore 规则只对工作区内存在的 `.gitignore` 生效。它若落在稀疏范围外，磁盘上不存在该文件，规则失效——用户放入的敏感文件（如 `.env`）会被当作普通游离文件纳入版本控制。这是安全约束，不是便利性选择。
- **稀疏范围是白名单**：不在范围内的文件不会出现在磁盘上。装配区内的文件即该空间当前拥有的能力，运行时按目录扫描加载，无需读取装配记录做过滤。
- **工作区外新增需显式扩展范围**：用户在装配区新增文件后，须将其纳入稀疏范围（`sparse-checkout add`），否则后续范围重算（如下行同步）会将其从磁盘移除。`space sync` 的游离文件纳管负责此步骤。

## Two-Layer Assembly Records

装配记录分两层，各司其职：

1. **类型装配单**（本地中央仓库 `assembly/archetypes/<type>.yaml`）：声明空间类型的默认能力组合与所用骨架，是空间初始化与重建的模板；作为公共能力随中央库演进，可贡献升级。`space capability add/remove` 修改本层。
2. **空间装配快照**（空间运行态 `.wopal-space/space-meta.json`）：记录本空间的实际装配，含装配单声明的能力与空间自有能力两类。由 CLI 维护，不手工编辑。

装配物化使用 Git `sparse-checkout`：空间 worktree 只物化装配单选中的路径，共享中央仓库对象库，不复制历史。

**能力来源与收敛路径**：装配单声明的能力来自能力池。池中不存在的自有能力由用户直接放入装配区，`space sync` 上行后进入 local main，自此成为池中能力，可被任意空间经 `space capability add` 装配，也可经 `ontology contribute` 分享至 upstream。空间自有能力仅存在于上行之前，不存在长期的"空间私有能力"状态。

### Space Assembly Snapshot Structure

`space-meta.json` 是空间装配的机器可读事实，供 `space status`、`space sync` 与 `space capability` 消费：

```jsonc
{
  "version": 1,
  "type": "coding",
  "schema": "coding-space-schema.yaml",
  "source": {
    "ontology": "wopal-space-ontology",
    "revision": "60a4cf5"
  },
  "assembledAt": "2026-09-14T10:30:00Z",
  "capabilities": {
    "agents": ["wopal", "fae", "rook", "evolver"],
    "skills": ["dev-flow", "agents-collab"],
    "rules": ["typescript", "business-rules"],
    "commands": ["init", "commit"],
    "plugins": ["wopal-plugin"]
  }
}
```

字段语义：

| 字段 | 含义 |
|------|------|
| `version` | 快照结构版本，用于未来结构演进的兼容判定 |
| `type` | 空间类型，与装配单 `type` 一致 |
| `schema` | 实际使用的骨架名，由装配单解析所得 |
| `source.ontology` | 来源 ontology 名称 |
| `source.revision` | 装配时的来源提交，供下行对齐判断 |
| `assembledAt` | 装配时间，ISO 8601 |
| `capabilities` | 实际装配的能力清单，按类目分组 |

`capabilities` 与类型装配单的关系是**实例与模板**：装配单声明该类型的默认组合，快照记录本空间的实际组合。两者在两个方向上产生差异：

- **装配单新增能力**（`space capability add`）：装配单与快照同时更新，同类型其他空间在各自下次 `space sync` 时跟进。
- **空间自有能力**（用户直接向装配区放入池中不存在的文件）：仅记录于快照，不写入装配单；`space sync` 上行后进入能力池，此后可经装配单被其他空间引用。

`source.revision` 是下行同步的判断依据：`space sync` 比较该提交与 local main 的关系，决定是否需要下行合入。


## Configuration Layers and Write Authority

三层配置，各司其职：

| 层级 | 文件 | 作用域 | Git 跟踪 | 职责 |
|------|------|--------|----------|------|
| 全局 | `~/.wopal/config/settings.jsonc` | 所有空间 | 否 | 跨空间共享的 provider、model、全局功能开关 |
| 空间级（公共）| `.wopal/config/settings.jsonc` | 当前空间 | 是 | 空间共享的 ellamaka 运行配置，随仓库传播 |
| 空间级（私有）| `.wopal/config/settings.local.jsonc` | 当前空间 | 否（git 忽略）| 覆盖公共默认值的本地开发者配置 |

CLI 只写 `settings.local.jsonc`，永不改写 `settings.jsonc`——后者随 space 分支经 `space sync` 汇入 central main，任何实例相关内容写入都会污染中央能力池。

### Plugin Assembly Layers

插件装配由装配单驱动，空间级配置承载物化结果：

| 类别 | 承载文件 | 分发方式 |
|------|---------|---------|
| 空间插件 | 空间级 `.wopal/config/settings.local.jsonc` | CLI 按装配单生成，git 忽略，可再生 |

共享 `settings.jsonc` 不硬编码插件引用。装配单的 `plugins` 字段是插件声明的唯一真相源：CLI 在 `space init` 与 `space capability add/remove` 时读取装配单，把插件引用生成到空间级 `settings.local.jsonc`。该文件可由 CLI 再生——换机器后重新按装配单装配即恢复，因此不进入版本控制。

插件在 settings 中的引用使用相对空间 config 目录的路径（`../plugins/<name>`），使同一份配置在所有空间与机器上一致。

## Assets Outside the Manifest

以下资产不进入装配单，由各自机制承载：

| 资产 | 归属 | 理由 |
|------|------|------|
| `assembly/` | 装配定义 | 装配单、骨架与模板本身是物化源头，不参与物化 |
| `prompts/` | wopal-plugin | 插件运行时的提示词资产，随插件分发；插件目录与用户级同名文件可覆盖，源码内保留默认值 |
| 插件静态资源 | 所属插件目录 | 随插件走，如 `plugins/tui-ellamaka/asset/` |
| `config/settings.jsonc` | 空间配置 | 空间共享运行配置，随 main 分发；不承载插件引用 |

## Permission Ownership and User Override

Agent 的权限基准属于角色本身，写在 `agents/<name>.md` 的 frontmatter `permission:` 中，随装配物化进入空间 worktree。权限不进入类型装配单：装配单声明「装配哪些能力」，不承载权限数值。

用户若要为本空间覆盖某 agent 的权限，写入 `.wopal/config/settings.local.jsonc` 的 `ellamaka.agent.<name>.permission`。该文件被 git 忽略，覆盖只作用于当前空间，不会随 space 分支提交回 central main。ellamaka 的加载顺序保证 `settings.local.jsonc` 深合并覆盖 `settings.jsonc`，因此本地覆盖天然生效。

## Template Contract

各模板的 schema、字段、生成规则与消费规则在此定义。

### `STRUCTURE.md` Schema and Generation Rules

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

### Minimal Space Template

初始化模板表达可启动 WopalSpace 的最小协议，聚焦通用结构而非特定 space 的组织习惯。

CLI 首次初始化必须创建：

```text
<space>/
  AGENTS.md
  .gitignore
  .wopal/
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

工作容器（如 `projects/`、`contents/`、`docs/`）由骨架声明决定，随空间类型不同。`labs/`、`external/`、`scripts/` 属于特定 space 的组织扩展，不进入最小模板；若用户后续创建这些目录，由 `/init` 扫描后再写入实例 `STRUCTURE.md`。

空间骨架声明确定性创建结构与模板映射，Consumption rules are in Schema Consumption Rules.

`.gitignore` 由 CLI 首次渲染；重复初始化时若已存在 `.gitignore`，CLI 保留现有内容，并报告缺失的 WopalSpace 建议忽略项。

### `root-AGENTS.md` Template

`root-AGENTS.md` 作为模板存在，实例化目标是 space root 的 `AGENTS.md`。它定位为空间启动提示与用户个性化规则入口。

模板职责：

1. 提醒 Agent 在上下文压缩或信息缺失时可重新读取 `.wopal-space/STRUCTURE.md`、`.wopal-space/REGULATIONS.md`、`.wopal-space/memory/USER.md` 与 `.wopal-space/memory/MEMORY.md`。
2. 提供用户空间个性化规则的写入位置。

空间事实由 `STRUCTURE.md` 承载，工作规则由 `REGULATIONS.md` 承载，详细技能路由由 `space-master` 承载。

### `REGULATIONS.md` Template

`REGULATIONS.md` 初始化时写入通用空间守则，之后作为用户可持续维护的运行态文件。ontology 守则升级通过 diff/建议呈现，由用户确认后吸收。

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
