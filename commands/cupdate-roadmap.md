---
description: Guide product phase discussions and produce phase definition and tracking documents
---

# Create or Update Roadmap

Guide the user through per-phase discussion of goals, current state, scope, targets and gaps (with design updates), and holistic review to surface residual risks. Produces phase definition and tracking documents.

**Input**: `$1` `$2`

**Parameter Notes**: `<name> [phase-id]`. When not provided, infer the product name from `docs/products/`; confirm with the user if unclear. `phase-id` is optional; when omitted, default to the current Active phase.

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `dev-doc-master` skill.

1. Load the `dev-doc-master` skill.
2. Follow the **Phase Reference** in `references/phase.md` and the universal rules in `references/consistency.md` for the full workflow: phase goal discussion, current state, scope, targets and gaps, residual risks, document-update discipline, and quality checklist.
3. Use the template at `templates/phase.md` inside the skill.

Do not duplicate or paraphrase the specification here. When in doubt, read the reference document.
