# fae — 执行精灵（dsh preset 样例）

**来源灵魂**: `.wopal/agents/fae.md`（persona 完整复刻其正文）
**角色**: 受限执行者 — 只执行编码/重构/文件/构建/测试，收明确工作返证据；不做规划/设计/审查。
**位置在意图翻译表**: `AGENT-TOOL-MAP.review.md` 第 4.2 节

## 装了哪些工具（为什么）

| 工具组 | 对应权限 | 说明 |
|---|---|---|
| 文件 + shell + 技能(skill-creator 独) + todo | read 全开、edit 开、bash 开、question=deny、plan_enter=deny、task=deny | fae 只执行 |
| ❌ tool-ask-user | question: deny | fae 不询问用户（原灵魂正文说"暂停并问"，dsh 侧会暂停报告） |
| ❌ plan-mode 组 | plan_enter: deny | fae 不规划 |
| ❌ delegation 组 | task: deny | fae 不委派 |

## persona 裁剪点

- **[CSS-1]** 两处 "Prefer Task tool" → 改为「用文件搜索工具」。原因：fae task=deny 无委派，dsh 无 Task 工具。
- **[CSS-2]** WebFetch 重定向句删除。原因：fae 无 web 工具。

## 安装要点

评审通过后装到 `~/.wopal/dsh/state/.agent-presets/fae/`，并把 `skills/` 子目录只放 skill-creator 技能副本（技能白名单 = 物理目录隔离）。
