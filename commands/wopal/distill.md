---
description: Distill session memories to database
---

This is an immediate execution command, not a rule-reading task.
You must immediately call the context_manage tool. Do not explain the command. Do not restate rules.

The following behaviors are wrong:
- Summarizing or restating command content
- Asking the user "would you like to distill?"
- Explaining distillation principles or workflow
- Reformatting tool output

# /distill — Session Memory Distillation

## Step 1: Preview

No arguments / `distill` / `distill --force` → call `context_manage({"action": "distill"})`, add `{"force": true}` when `--force`

**Output rule**: the tool returns a complete candidate list and Next Steps guide. You must output the returned content **verbatim** in your reply — do not reformat, do not add extra notes. The user will tell you the next step after seeing the report.

## Step 2: Confirm / Cancel

Based on user reply, call the corresponding parameters:

| User Says | Call |
|-----------|------|
| "confirm" / "all" / "write" / "ok" | `context_manage({"action": "confirm"})` |
| "only 0, 2, 3" (indices) | `context_manage({"action": "confirm", "selectedIndices": [0, 2, 3]})` |
| "cancel" / "no" | `context_manage({"action": "cancel"})` |

**Output rule**: confirm returns a dedup report — also output **verbatim** in your reply.

## Notes

- Preview and confirm must complete within the same session
- Candidate data is temporarily cached in session storage; prolonged inactivity may cause expiration
