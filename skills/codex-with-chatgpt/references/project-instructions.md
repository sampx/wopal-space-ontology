# ChatGPT Project Instructions Template

Paste into 项目设置 → 指令 when a Project should work inside a WopalSpace
workspace.

The text is deliberately minimal. A Project is a shared container: its
instructions apply to every conversation under it, most of which have nothing
to do with Codex collaboration. So it declares only where the workspace is and
what to read first. Everything C2C-specific — the Session identity/goal, expert role, request contract,
relevant skills, and workspace pointers — travels in the first request of the
conversation that needs it. Never put C2C mechanics here.

```
This Project works inside one WopalSpace workspace.

- Workspace: {{space_name}} (spaceId: {{space_id}})
- Connector: {{connector_name}}

Start every new conversation by reading AGENTS.md at the space root, then
follow the loading chain it names. Treat the workspace as the source of truth:
read it instead of assuming it.
```

Placeholders:

| Placeholder | Source | Example |
| --- | --- | --- |
| `{{space_name}}` | workspace display name | `编码空间` |
| `{{space_id}}` | `wopal space list` | `wopal-workspace` |
| `{{connector_name}}` | connector name in ChatGPT | `WopalSpace-Bot` |

If the user already has a Project instruction that covers this, leave it
alone. The skill does not require any particular Project wording; it carries
its own contract.
