---
description: Create or update a project BUSINESS_RULES.md
---

# Create or Update Business Rules

Create or update a project-level `BUSINESS_RULES.md` — the single source of truth for a product's business rules.

**Input**: `$ARGUMENTS`

**Parameter Notes**: Project name. When not provided, look up `projects/` plus context to infer. Confirm if unclear.

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `dev-doc-master` skill.

1. Load the `dev-doc-master` skill.
2. Follow the **BUSINESS_RULES Reference** in `references/business-rules.md` and the universal rules in `references/consistency.md` for the full workflow: rule definition boundary, document scope, header, body format, source priority, extraction steps, update mode, and quality checklist.
3. Use the template at `templates/business-rules.md` inside the skill.
