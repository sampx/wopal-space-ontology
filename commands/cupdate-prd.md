---
description: Create or update product PRD documents
---

# Create or Update PRD

Create or update a product PRD document.

**Input**: `$ARGUMENTS`

**Parameter Notes**: Product name. When not provided, look up `docs/products/` to infer.

- Project-level information is maintained in DESIGN documents; PRDs exist only at product level.

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `dev-doc-master` skill.

1. Load the `dev-doc-master` skill.
2. Follow the **PRD Reference** in `references/prd.md` and the universal rules in `references/consistency.md` for the full workflow: document paths and naming, context collection, writing rules, header, update mode, and quality checklist.
3. Use the template at `templates/prd.md` inside the skill.

Do not duplicate or paraphrase the specification here. When in doubt, read the reference document.
