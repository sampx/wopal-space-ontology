# wopal — 全能巫师（dsh preset 样例）

**来源灵魂**: `.wopal/agents/wopal.md`（persona 完整复刻其正文）
**角色**: 万能巫师，理解意图、调动所有能力与技能、委派协作、自我规划。
**位置在意图翻译表**: `AGENT-TOOL-MAP.review.md` 第 4.1 节

## 装了哪些工具（为什么）

**基座 = 官方 `cordis`（创造模式）预设全能力**，叠加 wopal 团队定制：

| 能力域 | 来源 | 说明 |
|---|---|---|
| shell + filesystem（tool-bash/pwsh/fs/fs-search） | cordis | 文件与命令执行 |
| **tool-jobs（后台任务）** | cordis | job_output / job_list / job_kill / 取消 / 完成通知 |
| skills 全开 + tool-skill | cordis + wopal | `customSkillDirs` 指向本空间技能根（29 技能全可见） |
| **tool-cordis（创造模式核心）** | cordis | 运行时检查、插件实验、preset 创作指导（自引用工具集） |
| planning / compaction | cordis | plan mode + 压缩（tool-result-pruner） |
| delegation（subagent/workflow/ralph） | cordis + wopal | 通用委派 + **fae/rook 专用队员**（带灵魂与武器白名单） |
| tool-ask-user / tool-todo / tool-goal / tool-web | cordis | 询问 / 待办 / 目标 / web 搜索 |
| tool-subagent-codex / claude-code | cordis | 可选 provider，默认 disabled（安装 Bundle 后启用） |

fae 是它的执行者、rook 是它的审查者——wopal 通过委派组把工作发出去，自己只规划与验证（见 persona Phase 3/4）。

> **继承方式**：以 `cordis` preset（`@deepseek-ai/dsh/config/agent-presets/cordis/agent.cordis.yml`）为基座逐项对齐，wopal 独有项仅 fae/rook 两个团队子代理。对齐检查：`comm -23 <(cordis ids) <(wopal ids)` 应为空。

## persona 裁剪点

- **[CSS-1]** Phase 7 `memory_manage command=search` → 改为「主动召回记忆/空间上下文」原则。原因：dsh 无 memory_manage 工具。

## 安装要点

评审通过后装到 `~/.wopal/dsh/state/.agent-presets/wopal/`。wopal 技能全开，需把 `customSkillDirs` 指向空间技能根（含 agents-collab / space-master 等）——当前样例留空，需按安装时技能根实际路径补 `skill-filesystem.config.customSkillDirs`。

> **skills/ 目录说明**：`skills/` 现保存随 wopal preset 发售的两个技能（editing-cordis-compositions、cordis-plugin-development）的**工作区源副本**（truth source），每份在正文开头新增「dsh in ellamaka (WopalSpace deployment constraints)」约束节，纠正其原文中不适用于本部署的官方 dsh CLI 约定（DSH_HOME、~/.dsh、官方 preset 安装路径等）。同步方向为**工作区 → 已安装 preset**（`$WOPAL_HOME/dsh/state/.agent-presets/wopal/skills/`），由 wopal 执行同步；不要反向覆盖工作区源副本。
