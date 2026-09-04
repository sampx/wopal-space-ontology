# wopal — 全能巫师（dsh preset 样例）

**来源灵魂**: `.wopal/agents/wopal.md`（persona 完整复刻其正文）
**角色**: 万能巫师，理解意图、调动所有能力与技能、委派协作、自我规划。
**位置在意图翻译表**: `AGENT-TOOL-MAP.review.md` 第 4.1 节

## 装了哪些工具（为什么）

| 工具组 | 对应权限 | 说明 |
|---|---|---|
| 文件 + shell + 技能(全) + ask + todo + plan + 委派 + goal | 近乎全开 | wopal 权限几乎无 deny，dsh 给最全工具集，作为编排者 |

fae 是它的执行者、rook 是它的审查者——wopal 通过委派组把工作发出去，自己只规划与验证（见 persona Phase 3/4）。

## persona 裁剪点

- **[CSS-1]** Phase 7 `memory_manage command=search` → 改为「主动召回记忆/空间上下文」原则。原因：dsh 无 memory_manage 工具。

## 安装要点

评审通过后装到 `~/.wopal/dsh/state/.agent-presets/wopal/`。wopal 技能全开，需把 `customSkillDirs` 指向空间技能根（含 agents-collab / space-master 等）——当前样例留空，需按安装时技能根实际路径补 `skill-filesystem.config.customSkillDirs`。

> **skills/ 目录说明**：`skills/` 现保存随 wopal preset 发售的两个技能（editing-cordis-compositions、cordis-plugin-development）的**工作区源副本**（truth source），每份在正文开头新增「dsh in ellamaka (WopalSpace deployment constraints)」约束节，纠正其原文中不适用于本部署的官方 dsh CLI 约定（DSH_HOME、~/.dsh、官方 preset 安装路径等）。同步方向为**工作区 → 已安装 preset**（`$WOPAL_HOME/dsh/state/.agent-presets/wopal/skills/`），由 wopal 执行同步；不要反向覆盖工作区源副本。
