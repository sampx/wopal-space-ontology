# ChatGPT Project 指令模板

当某个 Project 要在 WopalSpace 工作空间里工作时，粘贴到 项目设置 → 指令。

这段文字故意很短。Project 是共享容器：它的指令对该 Project 下**每一条**会话生效，
而其中大多数与 Codex 协作无关。所以它只声明工作空间在哪、开头该读什么。所有
C2C 相关的东西——Session 标识/目标、专家角色、request 契约、相关技能与工作区指针——都由需要它的那一条
会话的第一条 request 携带。不要把 C2C 机制写在这里。

```
This Project works inside one WopalSpace workspace.

- Workspace: {{space_name}} (spaceId: {{space_id}})
- Connector: {{connector_name}}

Start every new conversation by reading AGENTS.md at the space root, then
follow the loading chain it names. Treat the workspace as the source of truth:
read it instead of assuming it.
```

占位符：

| 占位符 | 来源 | 示例 |
| --- | --- | --- |
| `{{space_name}}` | 工作空间显示名 | `编码空间` |
| `{{space_id}}` | `wopal space list` | `wopal-workspace` |
| `{{connector_name}}` | ChatGPT 侧连接器名 | `WopalSpace-Bot` |

如果用户已有的 Project 指令已经覆盖这些内容，就保持原样。技能不要求 Project
指令有特定写法——它自带契约。

注意：粘贴的正文是英文，因为 ChatGPT 执行时以英文为准；本中文文件只作对照。
不要把中文注释粘进 Project 指令。
