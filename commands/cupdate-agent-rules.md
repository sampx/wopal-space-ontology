---
description: Create or update project AGENTS.md
---

# Create or Update Agent Rules

Create or update project-level (`<project>/AGENTS.md`), docs-directory (`<project>/docs/AGENTS.md`), or module/subdirectory-level (`<project>/<dir>/AGENTS.md`) `AGENTS.md` files.

**Input**: `$1` `$2`

**Parameter Notes**: `[path|project-name] [extra-rules-context]`. Path or project name is required. When only a project name is given, infer candidates from `.wopal-space/STRUCTURE.md` and `projects/` and confirm if ambiguous. Whenever targeting a project root in a space assembling `dev-doc-master` whose `docs/` directory lacks `docs/AGENTS.md`, proactively propose bootstrapping `<project>/docs/AGENTS.md` in the same confirmation plan.

---

## How to Work

The authoritative specification lives in the `space-master` skill.

1. Load the `space-master` skill.
2. Follow the **AGENTS.md Maintenance** section in the skill and its `references/agents-md-maintenance.md`: tier template selection (`templates/agent-rules.md` / `agent-rules-docs.md` / `agent-rules-subdir.md`), rule audit, quality gates (including `Doc sync`), confirmation plan, language version order, and checklist.
3. If the command cannot be resolved, use the skill's routing table to find the right workflow.
