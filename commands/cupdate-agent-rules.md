---
description: Create or update project AGENTS.md
---

# Create or Update Agent Rules

Create or update project-level or directory-level `AGENTS.md`.

**Input**: `$1` `$2`

**Parameter Notes**: `[path|project-name] [extra-rules-context]`. Path or project name is required. When only a project name is given, infer candidates from `.wopal-space/STRUCTURE.md` and `projects/`; confirm if the target cannot be resolved uniquely.

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `space-master` skill.

1. Load the `space-master` skill.
2. Follow the **AGENTS.md Maintenance** section in the skill and its `references/agents-md-maintenance.md` for the full workflow: rule audit, confirmation plan, language version order, and quality checklist.
3. If the command cannot be resolved, use the skill's routing table to find the right workflow.

Do not duplicate or paraphrase the specification here. When in doubt, read the reference document.

## Link and Heading Rules

- All document links must use relative paths (relative to the repository root or the document's directory). Absolute paths are forbidden because these documents are committed to git and shared across machines.
- AGENTS.md headings use Markdown heading levels without chapter numbering. Do not write `## 1. ...` numbered headings; express structure with heading levels only.
