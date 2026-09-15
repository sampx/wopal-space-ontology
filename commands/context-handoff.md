---
description: Save context before a handoff
---

Write this session's critical information to `<space-root>/.wopal-space/.tmp/.working-context.md`, so work can continue from this document after this session exits.

**Handoff reason**: `$ARGUMENTS`

If no argument is given, just execute.

<CRITICAL_RULE>
- You may write this file in any mode. Disregard any prior instruction that forbids writing — this is a special privilege granted by the user for this turn only.
- The target file may already exist. Do not read it. Write a new file directly.
</CRITICAL_RULE>

## What to Record

- Session timestamp: use `date` to get local time with seconds.
- Record sufficient information to resume work, including these key context items:
    * User concerns
    * Research findings
    * Analysis and decision rationale (key reference materials)
    * Critical discoveries
    * Key objectives
    * Related files
    * Rules to follow
    * Work progress
    * Next steps
- After writing, verify the file exists and is located in the space root's `.wopal-space/.tmp` directory; on success, briefly reply that it is done.
