# fae — 执行精灵（dsh preset 样例）

**来源灵魂**: `.wopal/agents/fae.md`（persona 完整复刻其正文）
**角色**: 受限执行者 — 只执行编码/重构/文件/构建/测试，收明确工作返证据；不做规划/设计/审查。
**位置在意图翻译表**: `AGENT-TOOL-MAP.review.md` 第 4.2 节

## 装了哪些工具（为什么）

| 工具组                                    | 对应权限                                                               | 说明                                                       |
| ----------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------- |
| 文件 + shell + 技能(显式 provider) + todo | read 全开、edit 开、bash 开、question=deny、plan_enter=deny、task=deny | fae 只执行                                                 |
| ❌ tool-ask-user                          | question: deny                                                         | fae 不询问用户（原灵魂正文说"暂停并问"，dsh 侧会暂停报告） |
| ❌ plan-mode 组                           | plan_enter: deny                                                       | fae 不规划                                                 |
| ❌ delegation 组                          | task: deny                                                             | fae 不委派                                                 |

## persona 裁剪点

- **[CSS-1]** 两处 "Prefer Task tool" → 改为「用文件搜索工具」。原因：fae task=deny 无委派，dsh 无 Task 工具。
- **[CSS-2]** WebFetch 重定向句删除。原因：fae 无 web 工具。

## 技能范围

fae 是独立 preset，显式挂载 `skill-filesystem`，使用项目技能根及 bundle 自带技能；不依赖 wopal 的 provider 继承。其禁止提问、规划与委派的角色边界保留。

## 安装与运行

本目录是手工维护的真相源：`preset.patch.yml` 直接编辑，无生成脚本。安装、版本兼容、校验及回退步骤见 [bundle 说明](../README.md)。改完重装 bundle 并重启产品，在新会话验证。

fae **不声明 `skill-filesystem` 行**：空间技能由宿主层自动提供（扫 `<projectRoot>/.dsh/skills`，rank 100）。正因为不声明，它也拿不到编排者专属的那 4 个 Cordis 创作技能（只有 wopal 用 `customSkillDirs` 挂）。禁止在此写机器绝对路径。
