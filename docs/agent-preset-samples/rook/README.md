# rook — 黑门乌鸦（dsh preset 样例）

**来源灵魂**: `.wopal/agents/rook.md`（persona 完整复刻其正文）
**角色**: 只读审查者 — 审计 plan 与代码质量，返回结构化报告；绝不执行/修复/规划。
**位置在意图翻译表**: `AGENT-TOOL-MAP.review.md` 第 4.3 节

## 装了哪些工具（为什么）

| 工具组 | 对应权限 | 说明 |
|---|---|---|
| 文件(读) + shell(读输出取证) + 技能(两 review 独) + todo | read 全开、bash 开、question=deny、task=deny | rook 只读审查 |
| ❌ tool-ask-user | question: deny | rook 不询问（审查发现的歧义写进报告 Requirement Questions） |
| ❌ delegation 组 | task: deny | rook 不委派 |

## persona 裁剪点

- 零裁剪。rook 全文（Identity 之后）与 dsh 兼容。

## READ_ONLY 如何落实

原灵魂正文的 `<READ_ONLY_BOUNDARY>` 已完整复刻进 persona。真正"禁写"在 dsh 靠 **fs 沙箱 read-only 模式**（评审文档「待定边界」第 2 点），不在 preset 层删文件工具——因为 dsh 的文件工具读写合一，删了就什么都做不了。

## 安装要点

评审通过后装到 `~/.wopal/dsh/state/.agent-presets/rook/`，并把 `skills/` 子目录只放 df-plan-review + df-implement-review 两个技能副本。
