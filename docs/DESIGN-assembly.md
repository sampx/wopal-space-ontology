# DESIGN — Assembly Model

> **Status**: Active
> **Updated**: 2026-09-25
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
  - maka

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

# 该空间加载的插件：键 = settings 顶层段名，值 = 装配进该段的插件名。
# 段名是开放的装配类目：今天 ellamaka / tui 两段，将来新的消费运行时
# 加一个键即可（如 dsh），物化规则不变。
plugins:
  ellamaka:
    - wopal-plugin
    - dsh-adapter
  tui:
    - tui-ellamaka

# 该空间加载的脚本
scripts:
  - emt
```

装配单覆盖五类可装配能力：`agents`、`skills`、`rules`、`commands`、`plugins`。前四类按名称声明；`plugins` 按「settings 段名 → 插件名列表」的映射声明，键是装配目标段名（`ellamaka` 段对应引擎的 server 插件装配，`tui` 段对应 TUI 插件装配），值是物化时在能力资产目录下解析为对应资产、并写入该段 `plugin` 数组的插件名。物化规则对每个段键一致：`settings[<段>].plugin += ../plugins/<插件名>`。

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

- **基础定义层始终物化**：基础定义层是所有空间类型一致、缺失即破坏装配/运行/演化闭环的固定内容，无条件包含在稀疏范围内。成员判据与完整清单：

  | 成员 | 归类 |
  |------|------|
  | `assembly/archetypes/<type>.yaml` | 装配定义 |
  | `assembly/schemas/<schema>.yaml` | 装配定义 |
  | `assembly/templates/` | 装配定义 |
  | `.gitignore` | 装配安全 |
  | `AGENTS.md`、`AGENTS.zh-CN.md` | 工作契约 |
  | `config/`、`docs/` | 运行与设计契约 |

  排除边界：仓库管理面（`.env.example`、`README*`、`LICENSE`、`package.json`、`.skill-lock.json`）、扩展类目（`scripts/` 等）、能力资产、`localState` 各归其位。`.env.example` 属仓库管理面（模板），空间侧实例由 `space init` 从本体源模板幂等种子为 `.wopal/.env`（已存在则跳过；`.gitignore` 持续覆盖，不入版本控制）。
- **`.gitignore` 必须物化**：gitignore 规则只对工作区内存在的 `.gitignore` 生效。它若落在稀疏范围外，磁盘上不存在该文件，规则失效——用户放入的敏感文件（如 `.env`）会被当作普通游离文件纳入版本控制。这是安全约束，不是便利性选择。
- **稀疏范围是白名单**：不在范围内的文件不会出现在磁盘上。装配区内的文件即该空间当前拥有的能力，运行时按目录扫描加载，无需读取装配记录做过滤。
- **有效范围三要素**：稀疏范围 = 当前装配单基线 ∪ `localState.added` − `localState.shadowed`（见 Two-Layer Assembly Records）。基线取**当前**装配单（使其他空间经 `capability add` 的变更在各自下次同步时生效），本地增量取空间快照的 `localState`。范围重算只在 `space sync` 下行时执行，结果仅取决于这三项，不随提交历史变化。
- **范围外新增须登记本地状态**：用户在装配区新增路径后，须记入 `localState.added` 并纳入稀疏范围，否则后续范围重算会将其从磁盘移除。登记入口是 `space capability add --local`（能力池内资产）或直接放入后由用户显式登记；未登记的未跟踪文件由 `space sync` 的范围重算保护不清扫，但不出现在任何清单中。
- **移除装配项用范围遮蔽，不提交删除**：用户移除装配单声明的能力路径时，记入 `localState.shadowed` 并从稀疏范围排除；内容保留在对象库与空间分支树中，不作为删除提交上行。显式入口是 `space capability remove --local`。
- **本地通道不进入空间分支树**：`localState` 两条目承载的能力调整（本地引入、本地移除）不产生提交。内容要么以未跟踪状态躺在磁盘（added），要么留在分支树但移出可见范围（shadowed）。空间分支树与 local main 的差异只包含共享通道（装配单声明变更、内容提交）的产物——「进 space 分支」是共享动作本身，本地通道的全部意义就是内容不进分支树。

## Two-Layer Assembly Records

装配记录分两层，各司其职：

1. **类型装配单**（本地中央仓库 `assembly/archetypes/<type>.yaml`）：声明空间类型的默认能力组合与所用骨架，是空间初始化与重建的模板；作为公共能力随中央库演进，可贡献升级。`space capability add/remove` 修改本层。
2. **空间装配快照**（空间运行态 `.wopal-space/space-meta.json`）：记录本空间的实际装配，含装配单声明的基线、空间新增与空间遮蔽三类。由 CLI 维护，不手工编辑。

装配物化使用 Git `sparse-checkout`：空间 worktree 只物化由装配单派生、经空间本地状态调整后的路径，共享中央仓库对象库，不复制历史。

**本地状态是空间私有事实**：`space-meta.json` 位于空间仓库内，不属于本体仓库，因此不会随 `space sync` 上行。它记录"本空间实际持有与不持有哪些路径"，是范围重算的唯一输入之一，跨同步持久稳定。

**能力来源与收敛路径**：装配单声明的能力来自能力池。经装配单通道引入池中不存在的自有能力时（`space capability add`，无 `--local` 旗标），内容随装配单提交在同步时上行进入 local main，自此成为池中资产，可被任意空间经 `space capability add` 装配，也可经 `ontology contribute` 分享至 upstream。本地通道（`--local` 旗标）不产生提交、不上行，内容停留在本空间（见 Two-Layer Assembly Records 的差异收敛表）。空间遮蔽是对装配单基线的本地收窄，只作用于本空间，不影响能力池与同类型其他空间。

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
    "agents": ["wopal", "fae", "rook", "maka"],
    "skills": ["dev-flow", "agents-collab"],
    "rules": ["typescript", "business-rules"],
    "commands": ["init", "commit"],
    "plugins": ["wopal-plugin"]
  },
  "localState": {
    "added": [
      { "path": "skills/newskill", "recordedAt": "2026-09-21T13:40:00Z" }
    ],
    "shadowed": [
      { "path": "skills/dev-flow", "recordedAt": "2026-09-21T13:41:00Z" }
    ]
  }
}
```

字段语义：

| 字段 | 含义 |
|------|------|
| `version` | 快照结构版本；`localState` 是向后兼容的字段扩充，不改版本号，读方缺失该字段时视为空 |
| `type` | 空间类型，与装配单 `type` 一致 |
| `schema` | 实际使用的骨架名，由装配单解析所得 |
| `source.ontology` | 来源 ontology 名称 |
| `source.revision` | 装配时的来源提交，供下行对齐判断 |
| `assembledAt` | 装配时间，ISO 8601 |
| `capabilities` | 装配单基线快照，按类目分组；物化时复制，此后不随空间本地变更 |
| `localState.added` | 空间新增的仓库相对路径，含记录时间；范围重算时并入 |
| `localState.shadowed` | 空间遮蔽的仓库相对路径，含记录时间；范围重算时排除 |

`capabilities` 是**物化时的基线副本**，`localState` 是其上的**本地增量**。三者的关系是：

```
有效装配 = capabilities（装配单基线） ∪ localState.added − localState.shadowed
```

由此产生四类差异，各有不同的收敛路径。装配单通道产生提交并随同步上行；本地通道不产生提交、不进入空间分支树，**构造上不可上行**：

| 变更 | 记录位置 | 是否上行 local main | 收敛方式 |
|------|----------|---------------------|----------|
| **装配单新增能力**（`space capability add`） | `capabilities` 与装配单同步更新 | 是 | 同类型其他空间在各自下次 `space sync` 时跟进 |
| **本地引入能力**（`space capability add --local`） | 仅记入 `localState.added` | **否** | 只扩本空间范围与磁盘物化；能力池不受影响；`capability add`（无旗标）转正为共享引入 |
| **本地移除能力**（`space capability remove --local`） | 仅记入 `localState.shadowed` | **否** | 只收窄本空间范围；能力池与同类型空间不受影响；`capability add --local` 或 `capability add`（无旗标）恢复 |
| **空间遮蔽基线能力**（用户直接删除装配单声明的路径，自动探测兜底） | 仅记入 `localState.shadowed` | 否 | 同本地移除；同步输出列出遮蔽项 |

**本地状态的两个条目都是私有事实，不进入空间分支树**：`localState.added` 的路径以未跟踪状态存在于磁盘——它不在任何提交里，`git diff main...space` 看不到它，上行在构造上不可能发生；`localState.shadowed` 只收窄稀疏范围，内容留在对象库与空间分支树中，不产生删除提交。`localState` 本身存放于空间根目录 `.wopal-space/space-meta.json`（管理面），不属于本体仓库，永不随 `space sync` 上行。

`source.revision` 是下行同步的判断依据：`space sync` 比较该提交与 local main 的关系，决定是否需要下行合入。

### Protected Paths

装配运行所需的结构定义不可缺失：装配单（`assembly/archetypes/`）、骨架（`assembly/schemas/`）、模板（`assembly/templates/`）、仓库根 `.gitignore`、空间根 `AGENTS.md` 与 `AGENTS.zh-CN.md`。这些路径的内容可自由修改并随同步上行，但**删除与重命名**会使空间无法物化。`.env.example` 不属于保护集合：它不入装配范围，空间侧的环境契约由 `space init` 种子的 `.env` 实例承载（用户资产，`.gitignore` 覆盖）。

保护机制在写入侧实现，判据是"路径是否落在保护集合内"：

| 操作 | 受保护路径 | 装配单声明的能力路径 | 其他路径 |
|------|-----------|---------------------|----------|
| 修改内容 | 允许，随同步上行 | 允许，随同步上行 | 允许，随同步上行 |
| 删除 | 恢复 | 记入 `localState.shadowed` | 正常删除 |
| 重命名 | 恢复 | 按遮蔽旧路径 + 新增新路径处理 | 正常重命名 |

受保护路径的删除或重命名由写入命令在提交前从索引与工作区一并恢复，不产生提交。恢复使用路径级操作（`git restore --staged --worktree <path>`），不触碰用户的其他未提交改动。


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

共享 `settings.jsonc` 不硬编码插件引用。装配单的 `plugins` 字段是插件声明的唯一真相源：CLI 在 `space init` 与 `space capability add/remove` 时读取装配单，按声明的段把插件引用生成到空间级 `settings.local.jsonc` 的对应段——`ellamaka` 段写 `ellamaka.plugin`（引擎的 server 插件装配），`tui` 段写 `tui.plugin`（TUI 插件装配）。两类装配项由消费方各自装载：引擎按 `ellamaka.plugin` 装 server 插件，TUI 运行时按 `tui.plugin` 装 TUI 插件。该文件可由 CLI 再生——换机器后重新按装配单装配即恢复，因此不进入版本控制。

**插件条目只含路径引用，零内联配置。** 插件引用生成时只写路径（如 `["../plugins/dsh-adapter"]`），不携带 options——条目是纯装配事实，保证可再生。插件的行为配置统一放 settings 的 `wopal.pluginConfig.<插件名>` 节，走配置继承链（用户全局默认 → 空间覆写）。装配单可以为插件声明默认配置（`configDefaults`），CLI 装配时把默认值补丁写进 `wopal.pluginConfig` 节而不是内联进条目——默认值与用户调整都落在继承链上，设置面板与 `wopal config schema` 因此天然覆盖插件配置。

插件在 settings 中的引用使用相对空间 config 目录的路径（`../plugins/<name>`），使同一份配置在所有空间与机器上一致。

## Assets Outside the Manifest

以下资产不进入装配单，由各自机制承载：

| 资产 | 归属 | 理由 |
|------|------|------|
| `assembly/` | 装配定义 | 装配单、骨架与模板本身是物化源头，作为基础定义层随装配物化；不作为能力资产被装配单声明 |
| `prompts/` | wopal-plugin | 插件运行时的提示词资产，随插件分发；插件目录与用户级同名文件可覆盖，源码内保留默认值 |
| 插件静态资源 | 所属插件目录 | 随插件走，如 `plugins/tui-ellamaka/asset/` |
| `config/settings.jsonc` | 空间配置 | 空间共享运行配置，随 main 分发；不承载插件引用 |
| `.env.example`、`README*`、`LICENSE`、`package.json`、`.skill-lock.json` | 仓库管理面 | 本体源仓库工具链消费；`.env.example` 的空间侧实例由 `space init` 种子为 `.env`，不随装配物化 |

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
