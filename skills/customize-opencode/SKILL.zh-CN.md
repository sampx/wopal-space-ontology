---
name: customize-opencode
description: |
  仅在用户编辑或创建 opencode 自身配置时使用：opencode.json、opencode.jsonc、.opencode/ 目录下的文件，或 ~/.config/opencode/ 目录下的文件。创建或修复 opencode 的 agents、subagents、skills、plugins、MCP servers 或 permission rules 时也适用。不要用于用户自己的应用代码，也不要用于任何并非配置 opencode 自身的项目。
---

# Customizing opencode

opencode 会严格校验自身配置，字段错误时拒绝启动。下面的形态覆盖常见使用面，但它们只是**概要，并非权威来源**。

## Reference guides

长篇章节按主题拆分到 `references/`：

- `references/schema.md` — 已发布的 JSON Schema 与完整的 `opencode.json` 参考。
- `references/plugin.md` — `plugin` 列表与插件模块契约。
- `references/mcp.md` — MCP 服务器配置（`local` / `remote`）。
- `references/permission.md` — 权限规则（`allow` / `ask` / `deny`）。
- `references/troubleshooting.md` — 配置损坏时的逃生舱，以及编辑指引。

## Applying changes

配置在 opencode 启动时加载一次，不会热重载。保存 `opencode.json`、agent 文件、技能、插件或任何其它配置期文件的更改后，**告知用户退出并重启 opencode**，更改才会生效。在此之前运行中的会话会继续使用已加载的配置。

## Where files live

| Scope                         | Path                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Project config                | `./opencode.json`, `./opencode.jsonc`, or `.opencode/opencode.json` (opencode walks up from the cwd to the worktree root) |
| Global config                 | `~/.config/opencode/opencode.json` (NOT `~/.opencode/`)                                                                   |
| Project agents                | `.opencode/agent/<name>.md` or `.opencode/agents/<name>.md`                                                               |
| Global agents                 | `~/.config/opencode/agent(s)/<name>.md`                                                                                   |
| Project skills                | `.opencode/skill(s)/<name>/SKILL.md`                                                                                      |
| Global skills                 | `~/.config/opencode/skill(s)/<name>/SKILL.md`                                                                             |
| External skills (auto-loaded) | `~/.claude/skills/<name>/SKILL.md`, `~/.agents/skills/<name>/SKILL.md`                                                    |

各作用域的配置会深度合并。项目配置覆盖全局配置。`opencode.json` 中未知的顶层键会被拒绝，抛出 `ConfigInvalidError`。

## Skills

opencode 的技能加载器会在技能目录内扫描 `**/SKILL.md`。文件必须恰好命名为 `SKILL.md`，并且存放在以技能名命名的独立文件夹中：

```
.opencode/skills/my-skill/SKILL.md
```

Frontmatter:

```markdown
---
name: my-skill
description: One sentence covering what this skill does AND when to trigger it. Front-load the literal keywords or filenames the user is likely to say.
---

# My Skill

(skill body in markdown: instructions, examples, references)
```

- `name` 必填，小写连字符分隔，最多 64 字符，且与文件夹名一致。
- `description` 实际上是必填的：没有描述的技能会被过滤掉，永远不会呈现给模型。同时覆盖技能**做什么**以及**何时**使用。用第三人称书写（"Use when..."，而非"I help with..."）。前置加载具体的触发关键词与文件名；如果技能在相邻主题上应保持安静，用"Use ONLY when..."加以约束。
- 可选：`license`、`compatibility`、`metadata`（字符串到字符串的映射）。

通过 `skills.paths`（递归扫描 `**/SKILL.md`）与 `skills.urls`（每个 URL 提供一份技能列表）从非默认位置注册技能。

## Agents

有两种定义 agent 的方式。任何非平凡场景都使用文件形式。

### Inline (in `opencode.json`)

```json
{
  "agent": {
    "my-reviewer": {
      "description": "Reviews PRs for style violations.",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-6",
      "permission": { "edit": "deny", "bash": "ask" },
      "prompt": "You are a strict PR reviewer..."
    }
  }
}
```

### File

```
.opencode/agent/my-reviewer.md      OR     .opencode/agents/my-reviewer.md
```

```markdown
---
description: Reviews PRs for style violations.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: deny
  bash: ask
---

You are a strict PR reviewer. Focus on...
```

文件正文会成为 agent 的 `prompt`。不要在 frontmatter 中再写 `prompt:`。

`mode` 取值为 `"primary"`、`"subagent"`、`"all"` 之一。

允许的顶层 frontmatter 字段：`name, model, variant, description, mode,
hidden, color, steps, options, permission, disable, temperature, top_p`。任何未知字段会被静默路由到 `options`。

禁用内置 agent：`agent: { build: { disable: true } }`，或在文件中于 frontmatter 里写 `disable: true`。

`default_agent` 必须指向一个非隐藏、主模式（primary-mode）的 agent。

### Built-in agents

opencode 自带 `build`、`plan`、`general`、`explore`，外加可选的
`scout`（受 `OPENCODE_EXPERIMENTAL_SCOUT` 门控）。隐藏的内部 agent：
`compaction`、`title`、`summary`。要覆盖内置字段，在 `agent: { <name>: { ... } }` 中定义同名键。
