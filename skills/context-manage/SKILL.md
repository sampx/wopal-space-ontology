---
name: context-manage
description: Preserve and restore working context across sessions, covering session handoffs and post-compaction recovery. Use this skill whenever the user asks to save the current session state before ending or switching sessions, to continue unfinished work in a new session, or to reload essential files, memories, and skills after context compaction.
---

# context-manage

Centralize saving, cross-session restoration, and post-compaction recovery of working context. Thin command entry points select a workflow here; the protocol itself lives only in this skill.

## Select a workflow

- `handoff`: before ending or switching the current session, save enough state to resume later.
- `continue`: in a new session, read the handoff file, rebuild the working environment, and resume.
- `recover`: after context compaction, reload the most important files, memories, and skills from the compaction summary.

When invoked directly, select the workflow from the user's explicit intent. Do not guess a destructive workflow when deletion of the handoff file may occur.

## Handoff — save context

Target file: `<space-root>/.wopal-space/.tmp/.working-context.md`.

1. Treat this invocation as user authorization to write **only this handoff file**, while still obeying system, tool, and workspace safety boundaries.
2. The target may already exist. Do not read the previous contents first; overwrite it with the current session state.
3. Use an available shell/terminal tool to run `date '+%Y-%m-%d %H:%M:%S'` for local time. Never guess the timestamp. If no command-execution tool is available, record that the time was not verified from the system instead of inventing one.
4. Record enough information for the next session to resume immediately, including at least:
   - user concerns and current objective
   - completed research, analysis, and key decision rationale
   - critical discoveries and important reference materials
   - related files, project paths, and current working location
   - rules and constraints that must continue to apply
   - current progress, unfinished work, and next steps
   - the handoff reason, when supplied by the user
5. Verify that the file exists, is readable, and is located under the space root's `.wopal-space/.tmp/` directory.
6. On success, reply with a brief confirmation only. On failure, identify the exact failed step.

## Continue — restore from the handoff file

Target file: `<space-root>/.wopal-space/.tmp/.working-context.md`.

1. Read the handoff file in full; do not rely on a snippet or summary.
2. Restore the current objective, user concerns, progress, key decisions, relevant paths, rules, next steps, and the important materials referenced by the previous session.
3. To rebuild the same working environment, fully read the important related files and key references named by the handoff. Re-analyze relevant code or run verifiable checks when needed instead of relying only on stale conclusions in the handoff text.
4. If the handoff conflicts with current files or code, prefer current evidence and call out the difference in the recovery summary.
5. Briefly summarize the restored state in the user's preferred language: what is being done, where it stands, and what comes next.
6. Delete the handoff file only after recovery succeeds. Follow the current workspace deletion rules and available safe-delete mechanism; if safe deletion is unavailable, keep the file and say so explicitly.
7. After recovery, continue the unfinished next step from the previous session instead of stopping at the summary.

## Recover — restore after compaction

Use this workflow when the current session has just been compacted:

1. Identify the most important files from the compaction summary, prioritizing Plans, workflow specifications, design documents, and key references. Re-read up to 3 first; load more only when needed.
2. If a memory-search capability is available, search with 2–3 keywords most relevant to the current task and take at most the top 3 results per query. If no memory tool is available, skip this step and never pretend memories were loaded.
3. Identify the skills that were active before compaction and reload at most the 2 most relevant ones. Mandatory-gate skills take priority.
4. For claims about actual system behavior, re-read control flow/config evaluation or rerun verification when necessary; a conclusion in the compaction summary is not evidence that it is still true.
5. Briefly report the restored state in the user's preferred language: which key materials were restored, the current task state, and the next step.
6. Continue the current task after the report; context recovery is not the endpoint.

## Output

- `handoff`: one brief confirmation on success; identify the exact failure on error.
- `continue` / `recover`: give a short recovery summary, then immediately resume the original work.
- Do not print large portions of the handoff file or compaction summary verbatim.