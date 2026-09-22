---
name: space-master
description: |
  WopalSpace 空间的根技能与总纲。空间的一切能力——如何运行、如何配置、如何编写命令/规则/技能/模板——都定义在本体（ontology）仓库中，经由中央能力池分发给空间，空间进化通过 space sync 回流。

  必须加载的场景：
  - 本体仓库操作：更新（update）、同步（sync）、能力发现（capability list）、贡献（contribute）、PR
  - 空间结构维护：space init/status、.wopal 目录结构、装配模型、空间如何运行与配置
  - 空间能力编写：命令、规则、技能、模板的编写与修改规范
  - AGENTS.md 编写：创建或更新项目级/目录级 AGENTS.md
  - README 编写：创建或更新项目级 README.md
  - 技能生命周期：安装、扫描、移除
  - 意图不明确、不确定用哪个流程/技能时，作为总纲路由到正确技能

  [CRITICAL] 涉及 ontology 仓库协作（update/sync/PR）时，即使用户未明确说"上游同步"，也必须加载本技能。
---

# space-master

负责 Wopal 的流程选择、场景路由、Ontology 本体维护、AGENTS.md 维护和技能生命周期管理。

---

## 技能使用场景

空间内的技能各司其职。按场景选择，不叠加加载：

| 场景 | 加载 | 要点 |
|------|------|------|
| 开发/修复/重构（Issue/Plan 驱动） | `dev-flow` | 默认开发流程；任务走其状态机（planning → reviewing → executing → verifying → done） |
| 本体能力进化（`.wopal/` 下的 skills、rules、agents、commands、plugins、assembly） | `ontology-evolution` | 对象判据：本体能力资产走本技能；`projects/` 下的代码仓库走 `dev-flow` |
| 委派任何子 Agent（fae/rook/wsf-* 等所有类型） | `agents-collab` | 委派前必须加载；覆盖委派工具 API、任务生命周期、双向通信、进度监控与恢复 |
| 创建/修改/评估技能 | `skill-creator` | 新建、编辑或评估技能必须加载；含描述优化与评估流程 |

本技能直接承担 WopalSpace 的空间治理工作，无需路由：

- **本体运维**：同步、贡献、提升、PR 全流程——运行模式、贡献路径、范围判定、PR 拆分、同步门禁
- **AGENTS.md 维护**：创建/更新项目级或目录级 AGENTS.md——规则审计、内容边界、工作流
- **README 维护**：创建/更新项目级 README.md——面向人类的项目入口文档，按空间能力条件性对齐文档集
- **技能维护**：技能生命周期——安装、扫描、移除

---

## 本体维护

### 中央能力池模型

本体维护围绕一条权威历史线展开：

```
upstream/main  →  local main（中央能力池）  →  space/<name>（装配 worktree）
```

`local main` 是中央能力池——本机所有空间可装配能力的唯一真相源。每个空间以自己的 `space/<name>` 分支挂载 `.wopal/` 装配 worktree，由装配单经 sparse-checkout 物化。空间从池中读取能力，不复制能力血统。

能力有两个流动方向：

| 方向 | 命令 | 作用 |
|------|------|------|
| **下行** | `wopal ontology update` | 把 `upstream/main` 拉入 `local main` |
| **空间对齐** | `wopal space sync` | 空间分支与 `local main` 双向对齐 |
| **上行** | `wopal ontology contribute` | 把 `local main` 的变更作为 PR 贡献到 `upstream` |

### 空间同步

`wopal space sync` 是空间的唯一对齐命令，取代原有的 `space update` / `space contribute` 组合。

它按顺序执行两个阶段：

1. **先行上行。** 空间独有的进化（空间新增或修改的能力）在隔离的临时 worktree 中整合进 `local main`。成功则推进 `local main`；冲突则停止同步并呈现冲突，两侧均保持不动。
2. **随后下行。** 上行干净后，空间 fast-forward 到最新的 `local main`。

顺序很关键：先上行意味着下行 fast-forward 落地时的 `local main` 已经包含空间自身的工作，不会丢失或重放任何变更。

始终先预览，再确认：

```bash
wopal space sync            # dry-run：显示什么会移动、移到哪
wopal space sync --confirm  # 执行
```

同步前用 `wopal space status` 查看空间与 `local main` 的分歧与装配状态。

### 能力发现与装配

两个命令族覆盖能力面，职责不同：

| 命令 | 作用域 | 用途 |
|------|--------|------|
| `wopal ontology capability list` | 本体 | 列出本体拥有的全部能力，按类目分组——空间装配的菜单 |
| `wopal space capability add/remove` | 空间 | 增删本空间装配能力并重新物化 |

`wopal space capability add/remove` 更新空间装配快照并重跑物化。该变更后续可作为类型装配单贡献，使同类型的其他空间继承。

另一个 `wopal capability` 命令与此无关：它暴露 CLI 自身的机器能力 OpenAPI 契约。

### 上游贡献

向上游贡献**仅在 fork 模式**可用。clone 模式下 `origin` 直接指向 canonical upstream，`wopal ontology contribute` 不可用——若用户需要 PR，引导其转为 fork 模式。

```bash
wopal ontology status        # 确认模式与分歧
wopal ontology contribute    # dry-run
wopal ontology contribute --include "a/**,b/**" --message "<message>" --confirm
```

### 贡献范围判定

贡献范围由**用户**决定，绝不擅自假设或回推：

1. **先呈现完整清单。** 枚举每一个待处理文件（`git diff --name-status`），按目录或功能区块分组，在提问之前先把完整清单展示给用户。禁止在展示可贡献内容之前问"你想贡献什么"。
2. **按结构判定，不靠直觉。** 判断该能力是所有空间类型共有，还是只属于某一类型。不确定时读本体设计，确认该能力是否已存在于 `local main` / `upstream/main`。禁止凭记忆或感觉判定。
3. **用户圈定范围，再确认。** 由用户选定哪些组贡献、哪些排除、哪些仅留在空间。空间私有资产（未验证或空间专属技能）绝不离开空间。用户未明确确认文件范围前，不得执行 `--confirm`。

完整流程与判定细节：`references/ontology-maintenance.md`。

### 按话题拆分 PR

**一个 PR 一个话题。** 不同目录或功能区块的变更必须拆成独立 PR。有依赖的 PR 先贡献；独立话题顺序不限。

**多轮变更合并为一个 PR。** 同一话题累积的全部变更合为一个 PR 贡献——禁止拆分，也不要询问用户是否拆分。

#### PR 文案规则

**文案描述变更交付了什么，而不是做了什么。** 写合并后读者获得的结果状态，而不是产生该结果的机械动作。自问：**"合并之后读者得到什么？"**——回答这个，而不是"我做了什么"。

- ❌ 动作 + 路径：`docs(space-master): add agents-md maintenance guide`（说的是"我加了个指南"，没说内容）
- ✅ 内容：`docs(space-master): AGENTS.md maintenance rules and update guidance`
- ❌ 空动作：`docs: sync templates and rules to main`（完全没说内容）
- ✅ 内容：`docs(templates): concurrency safety protection and sensitive-file read prohibition`

格式：`<type>(<scope>): <以结果状态描述的内容>`，描述所交付能力的名词短语。

**每批都要重跑完整门禁**：每个 PR 独立经过同步分析与预检门禁。

### 同步门禁

每次同步操作（`space sync`、`ontology update`、`ontology contribute`）都必须按序通过两道门禁：

#### 门禁一：同步分析

绝不自动同步。Agent 必须先掌握全貌：

1. `wopal space status` —— 空间层分歧与装配状态
2. `wopal ontology status` —— 本体层分歧（ahead/behind、文件级 diff）
3. 按贡献范围判定执行：呈现完整清单，由用户圈定范围，任何 `--confirm` 操作前取得**明确**的范围确认。dry-run 检视永远不能替代用户的范围批准。

#### 门禁二：预检

推送前始终检查：

1. 先**不带 `--confirm`** 运行（dry-run）
2. 确认列表中只出现你变更的文件
3. 若有误，调整 `--include` glob 后重新 dry-run
4. 之后才：带 `--confirm` 重跑

> 省略 `--include` 会推送分支上的一切——包括所有人累积的变更。无法撤销。
> 仔细看 dry-run 输出中的 `exclude` 列表——被排除的文件永远不会进入 PR。若应贡献的文件出现在那里，说明 glob 写错了。

### 本体规则

1. **多个模式用逗号分隔——绝不串联 `--include`。** `--include` 是单值参数；串联（`--include A --include B`）只保留最后一个（已实测验证），覆盖其余——这会把未覆盖的变更一并推出（不可逆）。多个模式写为 `--include "a/**,b/**,c"`（逗号分隔，空格可选）。`--exclude` 同理。
2. **clone 模式阻止 `contribute`。** 若需要 PR，引导用户转为 fork 模式。
3. **每次操作后核验。** 运行 `wopal ontology status` 与 `git diff --stat upstream/main origin/main`。

## AGENTS.md 维护

创建或更新项目级/目录级 `AGENTS.md` 时，按以下规范开展工作：

1. **规则审计先行**：更新现有 `AGENTS.md` 前，必须逐条审计现有规则（「规则审计」判据）：
   - **删**：代码已删除 / 结构自动保证（单一真相源）/ 重复权威文档 / 纯实现事实
   - **留**：安全边界（删除范围、凭证单写入口）、行为约束、User-Supplied Rules
   - **改**：目录描述过时、与设计文档机制冲突、中英版本漂移
2. **更新前出计划**：展示审计分类结果（保留/删除/修正 + 理由）+ 拟变更清单，获用户确认后才动笔
3. **先中文审核版，后英文正式版**：用户确认审核版后，再同步英文版
4. 不更新是默认且合法的结果——只有代码、测试、配置和既有文档无法承载边界时才更新

**完整规范**（内容边界、工作流、质量清单）见 `references/agents-md-maintenance.md`。命令 `/cupdate-agent-rules` 仅作入口引导，不承载规范。

## README 维护

创建或更新项目级 `README.md` 时，按以下规范开展工作：

1. **能力感知先行**：读取 `.wopal-space/space-meta.json` 的空间类型（`type`）与已装配技能（`capabilities.skills`）；元数据缺失时探测文件系统（是否存在 `docs/`、`DESIGN.md`、`AGENTS.md`）。文档集对齐仅在空间装配了相关文档集技能时执行，未装配则跳过，绝不假设。
2. **更新前出计划**：展示完整优化方案（目标文件路径、一句话项目描述、模块/核心命令概览、增删改章节、规范文档引用），获用户确认后才动笔
3. **先中文审核版，后英文正式版**：用户偏好语言非英文时，先生成 `README.<locale>.md` 供审核；确认后更新正式英文 `README.md`
4. **命令必须验证**：安装/运行/开发命令一律从 package 与配置文件核实，绝不猜测

**完整规范**（能力感知、模板、质量清单）见 `references/readme-maintenance.md`。命令 `/cupdate-readme` 仅作入口引导，不承载规范。

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
| `references/ontology-maintenance.md` | 中央能力池模型与模式契约、状态信号解读矩阵、按文件类型的冲突处理、远程分支清理、贡献范围与 PR 拆分流程 |
| `references/skills-maintenance.md` | 完整生命周期细节、安全扫描检查项、质量评估标准 |
| `references/agents-md-maintenance.md` | AGENTS.md 维护完整规范：内容边界、规则审计判据、工作流、质量清单 |
| `references/readme-maintenance.md` | README 维护完整规范：能力感知、语言版本规则、模板、质量清单 |
