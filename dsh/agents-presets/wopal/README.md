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

评审通过后装到 `~/.wopal/dsh/home/.agent-presets/wopal/`。wopal 技能全开，需把 `customSkillDirs` 指向空间技能根（含 agents-collab / space-master 等）——当前样例留空，需按安装时技能根实际路径补 `skill-filesystem.config.customSkillDirs`。

> **skills/ 目录说明**：`skills/` 保存随 wopal preset 发售的两个技能（editing-cordis-compositions、cordis-plugin-development）。每个技能正文开头有「dsh in ellamaka (WopalSpace deployment constraints)」约束节，记录本部署对官方 dsh CLI 约定的覆盖（DSH_HOME、~/.dsh、官方 preset 安装路径等）。运行时 `$DSH_HOME/.agent-presets/`（= `$WOPAL_HOME/dsh/home/.agent-presets/`）是软链，指向本版本管理源 `.wopal/dsh/agents-presets/`——在此编辑，改动经软链直接生效于运行时；本目录由 git 版本管理，勿在运行时侧反向改写。
