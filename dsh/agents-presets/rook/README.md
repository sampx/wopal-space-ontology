# rook — 黑门乌鸦（dsh preset 样例）

**来源灵魂**: `.wopal/agents/rook.md`（persona 完整复刻其正文）
**角色**: 只读审查者 — 审计 plan 与代码质量，返回结构化报告；绝不执行/修复/规划。
**位置在意图翻译表**: `AGENT-TOOL-MAP.review.md` 第 4.3 节

## 装了哪些工具（为什么）

| 工具组                                                 | 对应权限                                     | 说明                                                        |
| ------------------------------------------------------ | -------------------------------------------- | ----------------------------------------------------------- |
| 文件(读) + shell(读输出取证) + 技能(继承 wopal) + todo | read 全开、bash 开、question=deny、task=deny | rook 只读审查                                               |
| ❌ tool-ask-user                                       | question: deny                               | rook 不询问（审查发现的歧义写进报告 Requirement Questions） |
| ❌ delegation 组                                       | task: deny                                   | rook 不委派                                                 |

## persona 裁剪点

- 零裁剪。rook 全文（Identity 之后）与 dsh 兼容。

## READ_ONLY 如何落实

原灵魂正文的 `<READ_ONLY_BOUNDARY>` 已完整复刻进 persona。真正"禁写"在 dsh 靠 **fs 沙箱 read-only 模式**（评审文档「待定边界」第 2 点），不在 preset 层删文件工具——因为 dsh 的文件工具读写合一，删了就什么都做不了。

## 技能范围

rook 不单独声明技能目录，作为 wopal 子代理继承父组成的技能范围（随 wopal 的 `skill-filesystem`）。今后需要收紧 rook 可见技能时，再为本 preset 引入独立技能根或 toolFilter 收敛。

## 安装与运行

本目录是手工维护的真相源：`preset.patch.yml` 直接编辑，无生成脚本。安装、版本兼容、校验及回退步骤见 [bundle 说明](../README.md)。改完重装 bundle 并重启产品，在新会话验证。

rook **不声明 `skill-filesystem` 行**：空间技能由宿主层自动提供（扫 `<projectRoot>/.dsh/skills`，rank 100）。正因为不声明，它也拿不到编排者专属的那 4 个 Cordis 创作技能（只有 wopal 用 `customSkillDirs` 挂）。禁止在此写机器绝对路径。只读边界由 fs 沙箱执行策略承担，不因技能可见而放宽。
