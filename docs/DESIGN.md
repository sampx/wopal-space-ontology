# Ontology — 空间灵魂、规约与能力基因工具包设计

> **Status**: Active
> **Updated**: 2026-06-12
> **Parent Architecture**: `docs/products/wopal-space/DESIGN-wopalspace.md`
> **Parent Product**: `docs/products/wopal-space/PRD-wopalspace.md`

## 0. Change Log

| Date | Type | Summary |
|---|---|---|
| 2026-06-13 | Updated | §6.9 Agent Ontology Maintenance Workflow — 状态解读、更新决策、能力提升、多级 fork 维护和 safe-apply/contribute 工作流。补充 `/ontology-maintain` 命令。 |
| 2026-06-13 | Updated | §6.8 — 重构 `ontology status`/`space status` 输出规范 |
| 2026-05-31 | Updated | 收敛 base capabilities + space overlay：setup 从 ontology main 物化 base，space overlay 同名覆盖。 |
| 2026-05-30 | Updated | 将 Git source / worktree 分发细节下沉到 `docs/DISTRIBUTION.md`。 |
| 2026-05-29 | Updated | 明确 STRUCTURE compact schema、Design Document Layering 与 `/init` 消费 `wopal space scan` JSON 的维护边界。 |

---

## 1. Project Role

ontology 是 WopalSpace 的 Space Ontology 层，也是空间灵魂、规约与能力基因工具包的承载面。Agent 身份、规则、技能、命令、插件、模板与辅助脚本在这里沉淀和分发；ellamaka 负责解释执行，wopal-cli 负责确定性操作编排，space runtime 负责当前空间运行态。

核心职责：空间灵魂可复用、空间规约可分发、空间能力可编排、空间经验可延续。Fork 一个 ontology = 复制一套可持续演化的空间起点。

物理分发以 Git source + worktree 模型：P1 默认 clone ontology source，显式 `--fork` 时使用 user fork；二者最终都落到 `space/<user>/<space-name>` 分支与 `<space>/.wopal/` worktree。多数加载链路相关变更在用户重启 ellamaka 后完成验证。

---

## 2. Capability Scope

ontology 拥有的目标态能力组：

| 能力域 | 拥有的目标能力 | 明确边界 |
|---|---|---|
| Agent 定义 | 3 级核心 Agent（Wopal/Fae/Rook）+ 24 个 WSF 子代理 + Translator，灵魂文件仅定义角色与决策原则 | 不持有 Agent runtime 实现 |
| 技能生态 | 80+ 技能三层体系（空间根 / 工作流 / 专用），按触发条件自动注入 | 不判断技能产品价值，不负责 skill 内容设计 |
| 命令体系 | 17+ 命令覆盖空间维护、记忆进化、项目管理、开发支持、上下文管理，可覆盖内置命令 | 不实现命令执行引擎 |
| 规则体系 | 项目级 + 空间级 + Agent 专属规则，wopal-plugin 按条件匹配注入 | 不修改 ellamaka 核心行为 |
| 运行时插件 | wopal-plugin 提供规则注入、任务委派、记忆系统、上下文管理四大能力，7 个 plugin tools | 仅限插件内部，不侵入技能/规则/命令 |
| 模板体系 | 空间初始化模板（结构、守则、用户档案）+ 文档模板（PRD/DESIGN/phase/AGENTS） | 不持有空间运行态实例 |
| 辅助脚本 | ontology 维护、git hooks 与辅助自动化脚本 | 仅承担辅助维护动作 |

---

## 3. Key Decisions

| Decision | Rationale |
|----------|-----------|
| 声明式优于命令式 | 本体声明"空间应该有什么"，引擎负责解释执行。Markdown + YAML 是一等公民。 |
| 灵魂、规约与能力协同演进 | Agent 灵魂、规则、技能、命令、模板与脚本共同构成空间本体，演进时保持角色、规约与执行面的协同。 |
| 灵魂与操作分离 | Agent 灵魂文件只定义角色与决策原则（"我是谁"），操作知识由技能承载（"我怎么做"）。 |
| 插件适配原则 | wopal-plugin 是运行时插件，集中提供规则注入、任务委派、记忆系统和上下文管理，插件能实现尽量不改造 engine。 |
| Git source + worktree 分发 | P1 默认 clone，显式 `--fork` 才进入 fork 模式；Git 分支承载 space-specific 演化，通用能力成熟后回流 upstream。 |

---

## 4. Module Architecture

### 4.1 Agent 体系

| 模块 | 职责 | 载体 |
|------|------|------|
| 核心三级 | Wopal（主控）/ Fae（执行）/ Rook（审查），职责分离协作 | `agents/wopal.md`、`agents/fae.md`、`agents/rook.md` |
| WSF 子代理 | 24 个专职 Agent（mapper、researcher、planner、executor、reviewer、auditor、verifier 等），覆盖产品调研到验收全生命周期 | `agents/wsf-*.md` |
| Translator | 内容翻译，保留技术术语 | `agents/translator.md` |

协作闭环：Wopal 规划并委派 Fae 实施，委派 Rook 审查 Fae 产出。修订循环上限 3 轮。权限隔离通过 ellamaka agent frontmatter 的 `permission.skill` 字段实现。

### 4.2 技能体系

| 层次 | 职责 | 规模 | 代表 |
|------|------|------|------|
| 空间根技能 | 流程导航、场景路由、委派基础原则 | 1 | `space-master` |
| 工作流技能 | 开发状态机、Plan 规范、委派 API、WSF 产品流水线 | ~66 | `dev-flow`、`agents-collab`、WSF 技能族 |
| 专用技能 | 独立领域能力 | ~13 | `fc-local`、`youtube-master`、`ellamaka-config`、`automating-mail`、`mac-reminder`、`git-worktrees`、`skill-creator` 等 |

每个技能遵循三级加载：元数据（name + description）→ 主体（SKILL.md body）→ 资源（scripts / references / assets）。

`space-master` 是 ontology 的根技能，但其当前实现仍偏粗糙；后续应单独重构为概念模型入口、流程选择器、核心技能路由器、ontology/worktree 协作指南与多 Space 运维入口。

### 4.3 命令体系

| 类别 | 命令 | 载体 |
|------|------|------|
| 空间维护 | `/init` | `commands/init.md` |
| 记忆与进化 | `/wopal:memo`、`/wopal:evolve`、`/wopal:distill`、`/wopal:memory` | `commands/wopal/` |
| 唤醒与感知 | `/wopal:summon` | `commands/wopal/summon.md` |
| 文档管理 | `/cupdate-prd`、`/cupdate-design`、`/cupdate-roadmap`、`/cupdate-agent-rules`、`/cupdate-readme` | `commands/cupdate-*.md` |
| 开发支持 | `/commit`、`/review` | `commands/commit.md`、`commands/review.md` |
| 上下文管理 | `/context-continue`、`/context-handoff`、`/context-recover` | `commands/context-*.md` |
| 其他 | `/evaluate-skill`、`/extract-br` | `commands/evaluate-skill.md`、`commands/extract-br.md` |

ontology 命令可覆盖 ellamaka 内置命令。

### 4.4 规则体系

| 类别 | 职责 | 载体 |
|------|------|------|
| 项目级规则 | 语言与框架约束 | `rules/typescript.md`、`rules/python.md` |
| 空间级规则 | 通用行为规范 | `rules/business-rules.md` |
| Agent 专属规则 | Wopal 记忆规则、Fae Astro 规则等定向约束 | `rules/wopal/mem-rule.md`、`rules/fae/astro.md` |

规则通过 wopal-plugin 在 Agent 启动时注入，按条件匹配生效。

### 4.5 插件体系

wopal-plugin 由 TypeScript 编写，Bun 执行，基于 EllaMaka Plugin SDK。

| 模块 | 职责 | 禁用开关 |
|------|------|---------|
| Global（入口） | 加载 .env、检查开关、注册 Hooks/Tools | 无 |
| Rules | 规则发现 → 条件匹配 → 注入系统提示词 | `WOPAL_RULES_INJECTION_ENABLED` |
| Memory | LanceDB 存储、语义检索、蒸馏注入 | `WOPAL_MEMORY_ENABLED`（总控） |
| Task | 非阻塞子会话启动、状态监控、双向通信、并发控制 | 无（始终启用） |
| Monitor | 周期性调度引擎，统一管理监控策略 | 无（始终启用） |
| Context | 会话摘要、上下文压缩与恢复 | 无（始终启用） |

### 4.6 模板体系

| Template | 渲染目标 | 职责 |
|----------|---------|------|
| `wopalspace-schema.yaml` | 空间目录结构 | 声明 space runtime 与 workspace 根目录结构 |
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

模板的 schema 字段定义、生成规则、消费规则与各模板设计详见 §6.4。

### 4.7 辅助脚本体系

| 目录 | 职责 |
|------|------|
| `scripts/git-hooks/` | ontology 开发与提交阶段使用的 hooks 脚本 |
| `scripts/emt` / `scripts/oct` | 辅助维护入口脚本 |
| `scripts/oc-auto-approve.py` | 本地辅助自动化脚本 |
| `scripts/setup-git-hooks.sh` | hooks 安装脚本 |

### 4.8 配置体系

`.wopal/config/settings.jsonc` 提供空间级 ellamaka 配置层：provider、model、agent 权限和功能开关。与全局配置 `~/.wopal/config/settings.jsonc` 合并生效。

---

## 5. Technical Stack Choices

| Domain | Choice | Rationale | Boundary |
|--------|--------|-----------|----------|
| 声明式格式 | Markdown + YAML | ellamaka 原生支持的声明式格式 | 不承载运行时状态 |
| 插件运行时 | TypeScript | OpenCode Plugin SDK 原生语言，Bun 执行 | 仅限插件内部，不侵入技能/规则/命令 |
| 辅助脚本 | Shell / Python | 适合 hooks 安装、开发辅助和轻量自动化 | 仅承担辅助维护动作，不替代插件运行时能力 |
| 记忆存储 | LanceDB | 嵌入式向量数据库，零运维，向量 + FTS + LIKE 混合检索 | 仅记忆模块使用，不作为空间主存储 |
| 版本控制与分发 | Git | clone / fork + worktree 模型支持分支化演化和上游回流 | 不替代空间运行态结构 |

---

## 6. Interfaces and Contracts

### 6.1 ellamaka 加载接口

ellamaka 在 wopal-space mode 下从 ontology 加载：

1. `agents/*.md` — Agent 灵魂定义与 frontmatter 权限配置
2. `skills/*/SKILL.md` — 技能元数据与指令（按触发条件注入）
3. `commands/*.md` 与 `commands/wopal/*.md` — 命令定义（可覆盖内置命令）
4. `plugins/wopal-plugin.ts` — 插件入口（symlink → src/index.ts）
5. `config/settings.jsonc` — 空间级配置合并

多数加载链路相关改动以 ellamaka 重启后的加载结果作为验证标准。

### 6.2 wopal-plugin 工具接口

| 工具 | 职责 |
|------|------|
| `wopal_task` | 非阻塞子会话启动 |
| `wopal_task_output` | 任务状态与输出查询 |
| `wopal_task_reply` | 双向通信与恢复 |
| `wopal_task_abort` | 任务终止 |
| `wopal_task_finish` | 任务完成清理 |
| `memory_manage` | LanceDB 记忆 CRUD + 蒸馏 |
| `context_manage` | 会话摘要 + 上下文压缩 |

### 6.3 初始化与维护目标

Ontology 提供初始化协议，wopal-cli 负责确定性 materialize，`/init` 负责智能校准。CLI 实现建立在 ontology 模板、schema 与 `/init` 维护机制逐步验证成熟的基础上。

`wopal space init` 是创建/初始化入口。新建、已有目录补齐、合法 space 注册与 active space 设置均由 `space init` 承载。

P1 默认使用 clone 模式 materialize ontology source，降低新用户初始化成本；用户显式传入 `--fork` 时进入 fork 模式。`STRUCTURE.md` 模板中的 ontology source 使用 `${ONTOLOGY_REPO}` 占位符，表达实际使用的 ontology source。

空间类型选择：

```bash
wopal space init my-space --type coding
wopal space init my-space --type sampx/content
```

- 不传 `--type` 时默认 `common`，映射到 Git ref `main`。
- `--type coding` 映射到 `type/coding`。
- `--type sampx/content` 映射到 `type/sampx/content`。
- 禁止直接传入 `space/*`、`feature/*`、`contribute/*`。
- 选中的 base ref 必须存在于 ontology repo 中。

User 解析：fork 模式优先从 `origin` remote 解析 GitHub owner；clone 模式尝试 `gh api user`；fallback OS 用户名 slug 化。

Space branch 命名：`space/<user>/<space-name>`，写入 `spaces.<name>.branch` 和 `spaces.<name>.user`。

配置写入 `$WOPAL_HOME/config/settings.jsonc` 的 `ontologies.<name>` 节点（含 `path`、`origin`、`upstream`、`fork`）和 `spaces.<name>` 节点（含 `ontology`、`branch`、`user`、`type`）。

CLI 负责：

1. 解析 space name/path 与 ontology source。
2. 准备 `<space>/.wopal/` ontology worktree。
3. 读取 `wopalspace-schema.yaml` 与必需模板。
4. 创建 core runtime、`projects/`、`contents/`、`docs/`。
5. 首次渲染 `AGENTS.md`、`.gitignore`、`STRUCTURE.md`、`REGULATIONS.md`、`memory/USER.md`、`memory/MEMORY.md`。
6. rerun 时创建缺失项并保留已有文件内容。
7. 在完整成功后注册 space 并设置 active space。
8. 提供 `wopal space scan` 只读扫描入口，输出 repo / module JSON 事实。
9. 输出下一步：进入 space、启动 ellamaka、运行 `/init` 做首次智能校准。

CLI 边界：

- `wopal space scan` 只做 repo / module 事实发现和已有描述提取，不读写 `STRUCTURE.md`。
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

`/init` 聚焦 CLI 初始化后的结构维护：消费 scan 事实、维护 compact `STRUCTURE.md`、runtime 检查、模板差异提示与用户确认后的写入。

### 6.4 模板合约

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

`wopalspace-schema.yaml` 声明确确定性创建结构与模板映射。必需模板缺失时，CLI 以 fail fast 方式报告缺失模板、ontology source/path 和修复建议，并保持 space registry 与 active space 状态不变。

`.gitignore` 由 CLI 首次渲染；重复初始化时若已存在 `.gitignore`，CLI 保留现有内容，并报告缺失的 WopalSpace 建议忽略项。

#### `wopalspace-schema.yaml` 设计

`wopalspace-schema.yaml` 是 CLI 确定性初始化的输入。P1 目标结构使用 `runtime` / `space` 概念命名，分别描述 `.wopal-space/` 运行态目录与 space root 目录。

目标 schema 语义：

```yaml
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
    - template: memory/MEMORY.md
      target: memory/MEMORY.md
  dirs:
    - path: memory/diary
      keep: [.gitkeep]
    - path: logs
      keep: [.gitkeep]
    - path: .tmp
    - path: INBOX
    - path: backup
      keep: [.gitkeep]

space:
  files:
    - template: root-AGENTS.md
      target: AGENTS.md
    - template: gitignore
      target: .gitignore
  dirs:
    - path: projects
      keep: [.gitkeep]
    - path: contents
      keep: [.gitkeep]
    - path: docs
      keep: [.gitkeep]
```

CLI 消费规则：

- `runtime.path` 指向 `.wopal-space/`，其中 `files.target` 是相对 runtime path 的路径。
- `space.files.target` 是相对 space root 的路径。
- `template` 均从 `<space>/.wopal/templates/` 读取。
- `keep` 表示创建目录后可写入 `.gitkeep` 保留空目录。
- schema 声明最小空间结构：`projects/`、`contents/`、`docs/`；`labs/`、`external/`、`scripts/` 等扩展目录由用户创建后再由 `/init` 扫描进实例结构。

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

### 6.5 Design Document Layering

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

### 6.6 Distribution Summary

ontology 的分发走 Git source + worktree 模型。wopal-cli 通过 `wopal space init` / `wopal setup` 封装 clone/fork/worktree 过程，将其与 space runtime 初始化串联。

稳定边界：

1. 默认使用 clone-based canonical source flow。
2. `--fork` 是显式选择的替代模式。
3. `space/<user>/<name>` 分支承载 space-specific 演化。
4. `<space>/.wopal/` 是 ontology worktree，由 CLI materialize，由 ellamaka 运行时加载。

详细 source 输入、materialization、template handoff 和 runtime loading handoff 见 `docs/DISTRIBUTION.md`。

### 6.7 Base Capabilities and Space Overlay

Ontology 通过两层模型为 WopalSpace 提供可覆盖的能力分发：

**User-level base capabilities**：`~/.wopal/skills`、`~/.wopal/agents`、`~/.wopal/commands`、`~/.wopal/rules`、`~/.wopal/plugins` 是面向所有 space 的基础能力入口。setup 从 `~/.wopal/ontologies/wopal-space-ontology/{agents,skills,commands,rules,plugins}` 物化它们：macOS / Linux 使用 symlink，Windows 使用 managed copy。

**Space overlay**：`<space>/.wopal/skills`、`<space>/.wopal/agents`、`<space>/.wopal/commands`、`<space>/.wopal/rules`、`<space>/.wopal/plugins` 承载当前 space 的定制能力。同名能力由 space overlay 覆盖 base，ellamaka 按优先级顺序加载：

```text
~/.agents/skills
-> ~/.wopal/skills           # base
-> <space>/.wopal/skills     # overlay，优先级最高
```

覆盖机制：ellamaka 先并发解析所有 `SKILL.md`，再按目录优先级顺序串行合并；后出现的同名 skill 稳定覆盖前者。Agents / commands / rules / plugins 的加载机制同理。

本模型将 ontology main repo 的基础能力与各 space 的定制能力解耦：通用能力由 ontology main 统一维护，setup 只负责物化 base capabilities；space 内自由定制增量覆盖。

### 6.8 Ontology Branch Model and Collaboration

Ontology 以 Git 分支承载能力演化，按角色分为五类分支。`wopal ontology` 命令族提供 clone 和 fork 两种模式下统一的同步、更新与贡献操作。

#### Branch Naming Convention

| Prefix | Semantics | Source |
|---|---|---|
| `main` | 通用本体基线，所有类型空间共享的基础能力 | origin pull |
| `type/<name>` | 上游维护的类型本体（如 type/coding、type/content、type/hr） | 从 main 衍生，上游维护 |
| `type/<user>/<name>` | 用户自建的类型本体 | 用户从 main 或 type/* 衍生 |
| `space/<user>/<name>` | 空间实例本体，绑定到特定 space，`<user>` 为命名空间，`<name>` 为空间所在目录名 | 从 type/* 或 main 衍生，space init 时创建 |
| `contribute/<target>/<topic>` | 贡献分支，用于向上游提交 PR | 临时，PR 合并后删除 |
| `feature/<name>` | 开发分支，dev-flow worktree 使用 | 临时，合并后删除 |

#### Topology

```
origin (wopal-cn/ontology)
  ├── main                ← 通用基线
  ├── type/coding         ← 编码类型本体
  ├── type/content        ← 自媒体类型本体
  └── type/hr             ← 人力资源类型本体

~/.wopal/ontologies/wopal-space-ontology/  (本地克隆)
  ├── main                ← origin/main 镜像
  ├── type/coding         ← origin/type/coding 镜像
  ├── type/sampx/content  ← 用户自建类型本体
  ├── space/sampx/wopal-workspace  ← 空间实例（基于 type/coding）
  └── space/sampx/media-space     ← 另一个空间实例（基于 type/content）

<space>/.wopal/           ← 对应 space/<user>/<name> 分支的 worktree
```

本地目录名为 `wopal-space-ontology`，上游 canonical URL 为 `https://github.com/wopal-cn/ontology`。本地目录名和上游 repo 名不必相同。

#### Mode: Clone vs Fork

Clone 是降低使用门槛的默认模式，fork 作为可选替代保留：

| 模式 | origin 指向 | 启动方式 | push 能力 |
|---|---|---|---|
| Clone（默认） | wopal-cn/ontology（上游） | `wopal space init` | 无直接 push，贡献走 auto-fork PR |
| Fork | `<user>/wopal-space-ontology`（用户 fork） | `wopal space init --fork` | 可 push 到 fork |

上游 ontology canonical URL 为 `https://github.com/wopal-cn/ontology`。Fork 模式下本地仓库同时配置 `origin`（用户 fork）和 `upstream`（上游）两个 remote。

两种模式下分支命名和同步操作完全一致。

#### 命令族

`wopal ontology` 命令族提供统一的同步接口，设计为 agent 与人类均可使用：

| 命令 | 操作 | 说明 |
|---|---|---|
| `list` | 列出所有已注册的 ontology：上游 URL、本地路径、模式、能力分支层级、空间实例 | 全局视图，不需 effective space |
| `status` | 展示当前空间的本体身份、Instance 状态、三层 Ahead/Behind 比较 | agent 解读结构化输出后与用户讨论 |
| `update` | 拉取上游本体 type 更新到当前空间实例分支 | fork 模式 fetch upstream 全量 + merge upstream/<type-ref>；clone 模式 fetch origin + merge origin/<type-ref>；仅 fast-forward |
| `apply --from A --to B` | 同一 repo 内分支间 merge | checkout 目标分支 → merge 来源分支 → 报告结果；删除文件安全检测 |
| `contribute --source --target --commits` | cherry-pick 精选提交 → auto-fork PR 到上游 | 仅 cherry-pick，不做全量 merge；commit 选择由 agent 决定 |

**Agent 工作流模式**：CLI 输出清晰 Markdown 格式，agent 解读后与用户讨论选择哪些变更同步、贡献哪些 commits，再构造精确 CLI 命令执行。CLI 不做自主决策（merge 冲突解决、cherry-pick 选择、贡献策略均为 agent/用户职责）。

#### Type 约束与 `--type` 选择

空间实例在 `space init` 时记录其衍生来源能力类型 `type`，存储于空间注册表 `spaces.<name>.type`。`type` 仅允许 `main` 或 `type/*`，禁止指向 `space/*` 或其他分支类型。

用户通过 `--type` 表达能力选择：

```bash
wopal space init my-space --type coding
```

Type 映射：

| 用户输入 | 配置 `type` | Git ref |
|---|---|---|
| 未传 `--type` | `common` | `main` |
| `coding` | `coding` | `type/coding` |
| `sampx/content` | `sampx/content` | `type/sampx/content` |

#### `ontology list` 输出结构

`ontology list` 展示 ontology 仓库真实状态，分为三层：

1. **Upstream Ontology**：上游维护的 `main` 和 `type/*` 分支能力。
2. **Fork / Local Ontology**：
   - **Capability Branches**：本地能力分支 `main` + `type/*` + `type/<user>/*`，标明来源（上游镜像 / 用户自建）。
   - **Space Instances**：`space/<user>/<name>` 分支，展示能力分支被应用到哪些空间。交叉读取 `spaces.<name>.type` 展示 "Based on" 关系。
3. **Development**：`feature/*` 和 `contribute/*` 临时分支。

Fork 模式使用 `git branch -r --list 'upstream/*'` 的远程追踪引用来判断分支归属，不使用纯命名规则猜测。无远程追踪数据时回退命名约定。

`ontology list` 不展示 `Used by spaces`。空间关联状态由 `space status` 和 `ontology status` 展示。

#### `space status` 与 `ontology status`

两者共享 `SpaceOntologyContext` resolver，输出本体身份块（包含 Mode/Upstream/Fork/Repo/Types/Instance）。

**`space status` 输出结构**：

```
## Space: <name>

- **Path**: <path>
- **INBOX**: <inbox-dir>

### Ontology

- **Mode**: fork|clone
- **Upstream**: <sanitized-upstream-url>
- **Fork**: <sanitized-origin-url>           ← 仅 fork 模式
- **Repo**: <local-repo-path>
- **Types**: common (main), coding (type/coding), ...

### Instance

- **Branch**: space/<user>/<space-name>
- **User**: <user>
- **Type**: common → main
- **Worktree**: <worktree-path>
- **Status**: clean | dirty (N files)
```

**`ontology status` 输出结构**（在 `space status` 基础上追加 Ahead/Behind 表）：

```
### Ahead / Behind

| Relation | Baseline | Ahead | Behind |
|---|---|---:|---:|
| Upstream | upstream/<type-ref> | N | M |
| Fork | origin/<type-ref> | N | M |        ← 仅 fork 模式
| Remote | origin/<instance-branch> | N | M |
```

**语义**：
- `Upstream`：空间实例/复制本体相对于上游本体的差距
- `Fork`：空间实例相对于复制本体 type 基线的差距（仅 fork 模式）
- `Remote`：相对远程追踪分支的未推送提交

**共享实现**：`resolveSpaceOntologyContext(config)` 返回 `SpaceOntologyContext`，`renderOntologyIdentity(ctx, output)` 在两命令中复用身份块输出。

**设计决策**：
- 不输出工作树文件列表——对 agent 决策无帮助，增加 token 消耗
- Ahead/Behind 比较基：fork 模式用 `origin/<type-ref>` 代替本地 `main`（避免过期导致虚假 behind）
- `update` fork 模式直接 `merge upstream/<type-ref>`，跳过 `origin/main` 中转

#### 安全机制

`apply` 操作自动检测源分支是否删除了目标分支上存在的文件，发现时警告但不阻断——合并决策由用户或 agent 判断。

---

### 6.9 Agent Ontology Maintenance Workflow

本节定义 agent 如何消费 `wopal ontology` CLI 输出、解读状态并引导用户完成本体维护决策。

#### 6.9.1 Status Interpretation

`ontology status` 输出三段信息：

| 段 | 内容 | Agent 解读 |
|---|------|-----------|
| Ontology（身份块） | Mode、Upstream/Fork URL、Types 列表 | 确认当前空间的本体拓扑（fork/clone、有哪些 type 可选） |
| Instance | Branch、User、Type、Worktree、Status | 确认当前分支身份和 worktree 干净/脏状态 |
| Ahead / Behind | 三层 ahead/behind 数与 baseline | 判断需要执行哪个操作 |

解读规则：

- **Worktree dirty** → 任何操作前必须先提醒用户提交变更（`git commit`）
- **Remote ahead > 0** → 有未推送的提交，提醒用户 push
- **Upstream behind > 0** → 上游有更新，建议 `wopal ontology update`
- **Fork behind > 0**（fork 模式）→ 复制本体的 type 基线落后上游，建议先在主仓库 update type 分支
- **Upstream ahead > 0**（大量）→ 空间实例超前上游很多，讨论是否 `contribute`

#### 6.9.2 Decision Framework

Agent 根据 status 输出，按以下优先级决策：

| 优先级 | 观察 | 动作 | 理由 |
|--------|------|------|------|
| 1 | Worktree dirty | 提醒用户 `git commit` | 脏状态阻塞所有操作 |
| 2 | Remote ahead > 0 | 提醒用户 `git push` | 未推送提交可能丢失 |
| 3 | Upstream behind > 0 | 建议 `wopal ontology update` | 先拉取上游，减少后续冲突 |
| 4 | Fork behind > 0 | 建议在主仓库 `git checkout main && git pull upstream main && git push origin main`，再 `update` | fork 镜像过期则 space 实例基线不准 |
| 5 | Upstream ahead > 0（少量） | 可继续在 worktree 工作 | 少量超前是正常的空间定制 |
| 6 | Upstream ahead 巨大 | 讨论是否 contribute | 可能是成熟能力集合，应回流 |

#### 6.9.3 Capability Promotion Flow

空间孵化出新能力后，提升到 type 或 main 的标准流程：

**提升到 type 分支**：

```
1. Agent 与用户确认：该能力适用于同类空间（如 coding 类），非空间私有限定
2. Agent 建议：wopal ontology apply --from space/sampx/ws --to type/coding
3. CLI 执行 merge，报告结果。冲突时 agent 手动解决
4. 验证 type 分支工作正常
5. 讨论是否 contribute type/coding 到上游
```

**提升到 main**：

```
1. Agent 与用户确认：该能力适用于所有空间
2. 先提升到 type 分支验证，稳定后 contribute 到 main
3. 避免直接从 space 分支 contribute 到 main（跳过 type 验证层）
```

#### 6.9.4 Safe-Apply Workflow

`apply` 操作是 merge，可能产生冲突。Agent 的安全流程：

```
1. 执行 wopal ontology status → 确认 worktree clean
2. 与用户讨论 merge 方向：from → to，说明意图
3. 检查 ahead/behind：to 分支如果有 ahead，merge 可能冲突
4. 执行 wopal ontology apply --from <A> --to <B>
5. 成功 → 报告 merged
6. 冲突 → 列出冲突文件，按冲突处理指南操作
7. merge 后提醒用户验证功能、重启 ellamaka（如有 agent/skill 变更）
```

冲突处理优先级（与上游本文 §4 一致）：

| 冲突场景 | 处理 |
|----------|------|
| 上游修改了通用能力，本地也修改了同一文件 | 保留上游版本，手动移植本地特有改动 |
| 上游重构了文件结构 | 以上游新结构为准，迁移本地逻辑 |
| 双方新增同名文件 | 对比内容，合并两边的改动 |

#### 6.9.5 Contribute Workflow

```
1. Agent 执行 ontology status → 获取 ahead/behind 信息
2. 列出当前分支相对目标分支的新增 commit
3. 与用户逐个讨论：哪些应贡献（通用逻辑），哪些只属于本空间（定制内容）
4. 确认贡献范围后，执行：
   wopal ontology contribute --source <branch> --target <target> --commits <hash1,hash2>
5. 报告 PR URL
```

筛选原则见 `references/upstream-sync.md`。

#### 6.9.6 Multi-Level Fork Chain Maintenance

用户的复制本体可被他人 fork 为上游。Agent 需要识别并处理多级 fork 链：

```
B 的 fork 是 A 的上游
  → A 的 upstream 指向 B 的 fork
  → A 执行 ontology status → Upstream behind > 0
  → A 执行 ontology update → 从 B 拉取更新
```

Agent 无需知道 fork 链深度——`status` 的 `Upstream` 行自动反映最近上游的差距。`update` 自动从 `upstream` remote 拉取。多级 fork 对 CLI 透明。

#### 6.9.7 命令 `/ontology-maintain`

Agent 使用 `/ontology-maintain` 命令触发完整本体维护流程：

**触发条件**：Agent 识别到需要本体维护（status 显示异常、用户要求同步/贡献、工作流阶段要求）

**流程**（参照 `/init` 模式）：

```
Step 1: Collect Context
  - 执行 wopal ontology status
  - 执行 wopal ontology list（了解全局 type 分布）
  - 检查工作树状态（git status in worktree）

Step 2: Analyze & Propose
  - 解读 status 输出
  - 按 Decision Framework 排序建议
  - 展示具体操作命令和预期结果

Step 3: Report & Confirm
  - 结构化报告当前状态
  - 列出建议操作及理由
  - 等待用户确认

Step 4: Execute
  - 按确认的方案构建并执行 CLI 命令
  - 每次操作后验证结果
  - 如有冲突，按 Safe-Apply Workflow 处理
```

---

## 7. Data and State Model

ontology 本身是无状态的声明式能力包，不持有运行时状态：

| State | Location | Owner | Rules |
|-------|----------|-------|-------|
| Agent 灵魂定义 | `agents/*.md` | ontology | 定义者，ellamaka 加载执行 |
| 技能定义 | `skills/*/SKILL.md` | ontology | 定义者，按触发条件注入 |
| 规则定义 | `rules/*.md` | ontology + wopal-plugin | ontology 定义，wopal-plugin 执行注入 |
| 命令定义 | `commands/*.md` | ontology + ellamaka | ontology 定义，ellamaka 执行 |
| 辅助脚本 | `scripts/**` | ontology | 维护与辅助自动化载体 |
| 插件运行时状态 | wopal-plugin 进程内 | wopal-plugin | 运行载体，ontology 不持有 |
| 记忆数据 | LanceDB（space runtime 内） | memory_manage | ontology 提供工具，不持有数据 |
| 会话状态 | ellamaka session | ellamaka | ontology 不持有 |
| 空间结构 | `.wopal-space/STRUCTURE.md` | `/init` | ontology 提供模板，不持有实例 |
| 空间守则 | `.wopal-space/REGULATIONS.md` | 用户 + `/wopal:evolve` | ontology 提供初始化模板，不持有实例 |

Runtime 维护由 ontology commands 驱动：`/init`（结构校准）、`/wopal:memo`（日记暂存）、`/wopal:evolve`（经验沉淀）、`/wopal:distill`（记忆蒸馏）、`/cupdate-agent-rules`（项目规范更新）。

### 7.1 Memory Runtime Files

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

## 8. Related Documents

| 文档 | 说明 |
|------|------|
| `projects/wopal-cli/docs/DESIGN.md` | wopal-cli 子系统设计 — 统一操作入口 |
| `.wopal/docs/DISTRIBUTION.md` | ontology 的 Git source、worktree、template handoff 与 runtime loading 契约 |
| `.wopal/docs/BUSINESS_RULES.md` | 本体业务规则 |
