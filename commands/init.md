---
description: calibrate space runtime structure
---

Calibrate the current WopalSpace runtime structure: verify the `.wopal-space/` skeleton, detect structural drift, and report template diffs for user confirmation before writing.

User-provided focus or constraints (honor these):
$ARGUMENTS

## Goal

Ensure the current space runtime matches its declared structure in `STRUCTURE.md` and that key runtime files (`REGULATIONS.md`, `memory/USER.md`, `memory/MEMORY.md`) are present and up to date. This is a maintenance command for existing spaces — not a replacement for `wopal space init`.

## Investigation scope

Read these sources to build the current-state picture:

1. **Structure truth source**: `.wopal-space/STRUCTURE.md` — frontmatter and markdown table define what the space should contain.
2. **Runtime directory**: `.wopal-space/` — scan actual directories and files against the declared structure.
3. **Space root**: check `AGENTS.md` and `.gitignore` at the space root.
4. **Ontology templates**: `.wopal/templates/` — reference templates for diff comparison (`STRUCTURE.md`, `REGULATIONS.md`, `root-AGENTS.md`, `gitignore`, `memory/USER.md`, `memory/MEMORY.md`).
5. **Schema**: `.wopal/templates/wopalspace-schema.yaml` — defines the canonical runtime and space file/directory layout.

If `STRUCTURE.md` is missing, report that `wopal space init` should be run first and stop.

## Execution order

1. **Read current state** — load `STRUCTURE.md`, scan `.wopal-space/` and space root for actual files and directories.
2. **Calibrate structure** — compare actual layout against `STRUCTURE.md` frontmatter and schema. Identify missing directories, missing files, and undeclared entries.
3. **Check runtime files** — verify presence of `REGULATIONS.md`, `memory/USER.md`, `memory/MEMORY.md`. Check if root `AGENTS.md` and `.gitignore` exist.
4. **Report template diffs** — for each runtime file that has a corresponding template, show a concise diff or summary of differences between the template and the current instance. Highlight user-authored content that must be preserved.
5. **Wait for user confirm** — present all findings as a structured report. Do not write any files until the user explicitly confirms.
6. **Write** — after confirmation, apply only the approved changes: create missing directories/files, update `STRUCTURE.md` structure facts, and preserve all user-authored content.

## Output constraints

- Structure report must reference `STRUCTURE.md` and `REGULATIONS.md` explicitly.
- Clearly label each finding as: **missing** (does not exist), **drift** (exists but differs from declared structure), or **template-diff** (instance differs from template).
- Never overwrite user-authored content in `REGULATIONS.md`, `memory/USER.md`, or `memory/MEMORY.md` without showing the diff and getting explicit confirmation.
- Preserve the interactive confirmation style: always report first, wait for user approval, then write.
- Do not move deterministic init logic (directory creation, template rendering) into this command — that belongs to `wopal space init`.

## Questions

Only ask the user questions if the runtime state cannot be resolved from the available sources. Use the `question` tool for one short batch at most.

Good questions:
- ambiguous structural entries in `STRUCTURE.md`
- conflicting information between `STRUCTURE.md` and actual layout
- user intent for undeclared directories found during scan

Do not ask about anything the schema or `STRUCTURE.md` already makes clear.
