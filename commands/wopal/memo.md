---
description: Quickly record to short-term memory
---

# Quick Record (Memo)

## Content: `$ARGUMENTS`

- **With argument**: use the argument content directly
- **No argument**: scan current session context, extract information worth preserving

## Capture Rules

See the "Capture Three Questions", "Capture Types", and "Do Not Record" checklist in the Memory & Evolution section of `AGENTS.md`.

**Core principle**: only preserve information that is **highly relevant** to space optimization and project construction, and has **long-term reuse value**.

## Steps

1. **Extract candidates** (scan session context when no argument, list all candidates)
2. **Filter and display** (test each candidate against the three questions, show pass/discard with reason)
3. **Write to diary** (only write passed items):
   ```bash
   cat >> memory/diary/YYYY-MM-DD.md <<'EOF'

   ### HH:MM Topic
   - [Type] Content
   EOF
   ```
4. **Confirm**: `Recorded to diary`

## Filter Example

```
Candidate: session recovery workflow
Test: all three questions → no → discard (generic workflow, not high-value)

Candidate: soul should not reference space regulations
Test: avoids repeated research → pass (architecture design decision)
```