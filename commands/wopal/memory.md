---
description: Manage LanceDB long-term memory
---

# /memory — Memory Management Command

**This is an immediate tool-call command, not a rule document.** Upon receiving this command, you must immediately call the `memory_manage` tool to perform the requested operation.

## Arguments: `$ARGUMENTS`

| User Input | What You Must Do |
|------------|------------------|
| No argument / `list` | Call `memory_manage(command="list", limit=100)` — fetch all at once, do not batch |
| `list --category X` | Call `memory_manage(command="list", category="X", limit=100)` |
| `list --limit N` | Call `memory_manage(command="list", limit=N)` — use the user-specified limit |
| `search <query>` | Call `memory_manage(command="search", query="<query>")` |
| `stats` | Call `memory_manage(command="stats")` |
| `delete <id1,id2,...>` | **Show summary of content to delete first, wait for user confirmation**, then call `memory_manage(command="delete", query="<ids>")` |

## Output Requirements

**When the user runs `list`, their goal is to review each memory entry and decide what to keep or remove.** You must write the **full content of every memory entry** returned by the tool into your reply. Omitting any entry = user cannot make informed decisions = task failure.

**Tool return values are invisible to the user.** Calling the tool without output = the user sees nothing = task incomplete.

**Display obligation**: all subcommands initiated through this command (including search, stats, injected) must display results to the user. This display obligation is controlled by the `/memory` command layer and is separate from the tool layer — when the Agent autonomously calls search in other contexts, display is not required.

## Notes

- Deletion is irreversible. Always show content first and wait for user confirmation.