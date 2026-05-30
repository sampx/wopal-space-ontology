---
description: Evolve short-term memory to long-term knowledge
---

# Self-Evolution (Evolve)

## Goal

Extract valuable information from diaries and preserve it in the right location.

> Diaries are a staging pool. Evolution is true preservation — not just recording what happened, but **learning** from experience.

## Workflow

### 1. Scan Information Sources

Scan simultaneously:
- **Current session**: key events, decisions, errors
- **Short-term memory**: diaries under `memory/diary/`

**Skip tagged entries**: `[进化吸收]` `[进化排除]`

### 2. Determine Destination

See the "Preservation Locations" and "Optimization Directions" in the Memory & Evolution section of `AGENTS.md`:

| Information Type | Destination |
|------------------|-------------|
| Cross-session general knowledge / experience | `MEMORY.md` |
| User preferences | `USER.md` |
| Work rules / conventions | `AGENTS.md` |
| Project-specific knowledge | Project `AGENTS.md` |
| Core behavioral traits | Soul (system prompt) |

### 3. Present Plan

```
Evolution Plan:

📝 MEMORY.md
  + [Knowledge] OpenCode API at labs/ref-repos/opencode/packages/sdk/openapi.json

👤 USER.md
  + [Preference] "出方案" = write a plan document, not verbal explanation

📐 AGENTS.md
  + [Rule] Skill scripts must cd into directory before execution

Confirm execution?
```

### 4. Execute and Tag

After user confirmation:
1. Write to the corresponding long-term file
2. Append evolution tag **inside the type label** of the diary entry:
   - Preserved → `[Type-进化吸收: brief reason]`
   - Not preserved → `[Type-进化排除: brief reason]`

```markdown
- [Tacit Knowledge-进化吸收: written to MEMORY.md] **Background**: ... **Event**: ... **Conclusion**: ...
- [Pitfall-进化排除: implementation detail] **Background**: ... **Event**: ... **Conclusion**: ...
```

### 5. Diary Archival

Move all diaries except today's to `memory/diary/archived/`. Use `date '+%Y-%m-%d'` to get today's date. Keep only the diary file matching today's date; archive all others.

## Value Judgment

See the "Capture Three Questions" and "Do Not Record" rules in the Memory & Evolution section of `AGENTS.md`.

**Core principle**:
- Only preserve information that is **highly relevant** to space optimization and project construction with **long-term reuse value**
- Do not record general knowledge, transient state, session logs, or mere error descriptions