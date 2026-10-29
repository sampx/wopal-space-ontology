---
name: space-master
description: >
  WopalSpace 根技能与流程路由入口。意图不清、不能确定应使用哪个技能时必须加载。用于空间初始化、结构/目录布局、运行配置、装配模型，以及项目或目录 AGENTS.md、项目 README.md 的创建与维护；也用于技能安装、扫描、移除和能力编写的规范路由。本体仓库更新、同步、能力发现、贡献 PR 与能力进化直接加载 ontology-evolution，不必同时加载本技能；具体开发、技能编写与委派分别路由至 dev-flow、skill-creator、agents-collab。
---

# space-master

负责 Wopal 的流程选择、场景路由、Ontology 本体维护、AGENTS.md 维护和技能生命周期管理。

---

## 技能使用场景

空间内的技能各司其职。按场景选择，不叠加加载：

| 场景 | 加载 | 要点 |
|------|------|------|
| 开发/修复/重构（Issue/Plan 驱动） | `dev-flow` | 默认开发流程；任务走其状态机（planning → reviewing → executing → verifying → done）。本体 Issue 是例外——见下方「Issue 归哪个项目、走哪个流程」 |
| 本体维护（实例更新、空间对齐、能力装配、贡献） | `ontology-evolution` | 本体仓库操作一律直接加载该技能；本技能只做路由 |
| 本体能力进化（`.wopal/` 下的 skills、rules、agents、commands、plugins、assembly） | `ontology-evolution` | 对象判据：本体能力资产走本技能；`projects/` 下的代码仓库走 `dev-flow` |
| 委派任何子 Agent（fae/rook/wsf-* 等所有类型） | `agents-collab` | 委派前必须加载；覆盖委派工具 API、任务生命周期、双向通信、进度监控与恢复 |
| 创建/修改/评估技能 | `skill-creator` | 新建、编辑或评估技能必须加载；含描述优化与评估流程 |

本技能直接承担 WopalSpace 的空间治理工作，无需路由：

- **AGENTS.md 维护**：创建/更新项目级或目录级 AGENTS.md——规则审计、内容边界、工作流
- **README 维护**：创建/更新项目级 README.md——面向人类的项目入口文档，按空间能力条件性对齐文档集
- **技能维护**：技能生命周期——安装、扫描、移除

---

## Issue 归哪个项目、走哪个流程

每个 Issue 通过 `--project` / `project/<name>` 标签声明它要改哪个空间组件。这个标签同时决定工作落在哪、以及归哪个流程管，所以必须按**改动对象**选，不能按话题选。

标签怎么填，与 `STRUCTURE.md` 里组件的命名保持一致：

| Issue 要改的东西 | `--project` | 流程 |
|---|---|---|
| 本体组件——本体 worktree 本身（`skills/`、`rules/`、`agents/`、`commands/`、`plugins/`、`assembly/`） | 该组件在 `STRUCTURE.md` 里的项目名 | `ontology-evolution` |
| `projects/` 下的某个仓库 | 该仓库在 `STRUCTURE.md` 里的名字 | `dev-flow` |

名字要从 `STRUCTURE.md` 读，不要凭印象猜：本体项目名和仓库清单每个空间都不一样，写一个不匹配的组件名，会让 Plan 或提案落进没有任何地方指向的目录。

项目是本体组件的 Issue 就是本体工作：写成 `docs/evolutions/` 下的提案，走 `wopal space evo` 生命周期，绝不走 dev-flow 那条路——没有 Plan、没有特性分支、没有 worktree。Issue 只是需求的记录，提案才是实施的授权来源。

标签看不准时就按改动路径判断：落在本体 worktree 里就是本体工作，落在 `projects/` 下的仓库就是仓库工作。

---

## 本体维护

本体维护与能力进化由 **`ontology-evolution` 技能**执行——任何本体仓库操作（实例更新、空间对齐、能力装配、上游贡献）一律直接加载该技能，并按其维护协议（Maintenance Protocols）章节执行。无需同时加载本技能。

该技能是唯一规范单点——命令面、状态解读、双通道与上行闸、执行口径、贡献范围与原生贡献流程。创建、修复或收尾上游 PR 时，读取该技能的 `references/contribution.zh-CN.md`；其中统一短分支命名、固定 worktree、评审期间保留现场及授权清理，不在本技能重复维护。

## AGENTS.md 维护

创建或更新项目级、目录级 `AGENTS.md` 时，按以下规则开展工作：

1. **规则审计先行**：更新现有 `AGENTS.md` 前，必须逐条审计现有规则（判据见参考文档的 Rule Audit）：
   - **删**：引用的代码已不存在 / 结构或 CI 已自动保证 / 只是设计细节、不含可执行约束（长期*工作约束*即使 DESIGN 有描述也要精简保留）/ 纯实现事实
   - **留**：安全边界（删除范围、凭证单写入口）、行为约束、长期工作约束（日志、输出/路由、部署/发布限制、测试与验证、编码纪律）、`Code Review Rules` 章节（标题原样保留，内容照常审计）、User-Supplied Rules
   - **改**：目录描述过时、与更新的设计机制冲突、中英版本漂移
2. **先建立质量门禁**：写规则前，把该技术栈标准的格式化、lint/静态分析、类型检查、单元测试和集成测试接入项目可执行命令；规范只写这些命令和失败条件，不让 Agent 自行判断
3. **更新前出计划**：展示审计分类结果（保留/删除/修正 + 理由）和拟变更清单，获用户确认后才动笔
4. **先审核版，后正式版**：先更新 `AGENTS.<locale>.md`，每个标题与英文模板完全一致，只翻译正文；确认后再更新正式英文 `AGENTS.md`
5. **Code Review Rules 章节**：代码类项目的 `AGENTS.md` 必须包含 `## Code Review Rules` 章节——新建项目按模板生成，更新项目时原样保留（禁止删除、改名、翻译标题；纯文档目录可省略）。章节内只写方向性骨架：项目使用的审查流程、报缺陷边界、项目特有检查点。可复用模板不得写入任何具体项目的规则
6. 不更新是默认且合法的结果——只有代码、测试、配置和既有文档无法承载边界时才更新

**完整规范**：`references/agents-md-maintenance.zh-CN.md`。

## README 维护

创建或更新项目级 `README.md` 时，按以下规范开展工作：

1. **能力感知先行**：读取 `.wopal-space/space-meta.json` 的空间类型（`type`）与已装配技能（`capabilities.skills`）；元数据缺失时探测文件系统（是否存在 `docs/`、`DESIGN.md`、`AGENTS.md`）。文档集对齐仅在空间装配了相关文档集技能时执行，未装配则跳过，绝不假设。
2. **更新前出计划**：展示完整优化方案（目标文件路径、一句话项目描述、模块/核心命令概览、增删改章节、规范文档引用），获用户确认后才动笔
3. **先中文审核版，后英文正式版**：用户偏好语言非英文时，先生成 `README.<locale>.md` 供审核；确认后更新正式英文 `README.md`
4. **命令必须验证**：安装/运行/开发命令一律从 package 与配置文件核实，绝不猜测

**完整规范**：`references/readme-maintenance.md`。

---

## 技能维护

### 生命周期

```
找 → 下 → 扫 → 装 → 评 → 删
```

```bash
wopal skills find "<query>"              # 搜索注册表
wopal skills download owner/repo@name    # 下载到审核区
wopal skills scan <name>                 # 安全扫描（强制步骤）
wopal skills install /path --force       # 安装到运行时
wopal skills remove <name> --force       # 从空间移除
```

### 技能规则

1. **安装前必须扫描。** `wopal skills scan` 是强制步骤——检查恶意代码、数据外泄、非法触发器。禁止跳过。
2. **变更后必须验证。** 安装或编辑后：`ls -la .wopal/skills/<name>/SKILL.md` 和 `wopal skills list`。
3. **创建/修改走 `skill-creator`。** 新建或编辑技能必须加载 `skill-creator` 技能。

---

## 参考资料

技能正文覆盖核心要点。遇到故障或边缘场景时，**必须阅读参考文档**——完整协议在其中：

| 文档 | 内容 |
|------|------|
| `references/skills-maintenance.md` | 完整生命周期细节、安全扫描检查项、质量评估标准 |
| `references/agents-md-maintenance.zh-CN.md` | AGENTS.md 维护完整中文规范：质量门禁、内容边界、规则审计判据、工作流、质量清单 |
| `references/readme-maintenance.md` | README 维护完整规范：能力感知、语言版本规则、模板、质量清单 |
