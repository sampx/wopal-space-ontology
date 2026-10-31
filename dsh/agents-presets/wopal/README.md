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

## 安装与运行

本目录是手工维护的真相源：`preset.patch.yml` 直接编辑，无生成脚本。安装、版本兼容、校验及回退步骤见 [bundle 说明](../README.md)。改完重装 bundle 并重启产品，在新会话验证。

wopal 的 `skill-filesystem.config.customSkillDirs` **只挂包内那 4 个 Cordis 创作技能**，锚在 preset 自身 `baseUrl`（随包分发，换机换挂载点都成立）。空间技能不在此声明：宿主层的 `skill-filesystem` 自动扫描 `<projectRoot>/.dsh/skills`（project-dsh 根，rank 100，projectRoot = 最近的含 `.git` 目录）。`agents-collab` 等是否可见由装配决定（`assembly/archetypes/coding.yaml` 的 `skills:` 清单），缺失应跑装配补齐 —— **严禁在 preset 里写绝对路径去兜**。

> **skills/ 目录说明**：`skills/` 保存随 wopal preset 分发的 4 个技能（`editing-cordis-compositions`、`cordis-plugin-development`、`cordis-composition-reference`、`agent-experience`）。每个技能正文开头有「dsh in ellamaka (WopalSpace deployment constraints)」约束节，记录本部署对官方 dsh CLI 约定的覆盖（DSH_HOME、~/.dsh、官方 preset 安装路径等）。本目录由 git 版本管理，运行时侧不再回写。fae / rook 不挂本目录。
