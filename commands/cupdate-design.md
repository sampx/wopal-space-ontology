---
description: Create or update a product DESIGN or project DESIGN
---

# Create or Update DESIGN

Create or update product DESIGN (product architecture) or project DESIGN (project internal design). Simple projects may skip product DESIGN and follow the simplified flow: project DESIGN (with self-defined product-level design) → Plan.

**Input**: `$1` `$2`

**Parameter Notes**: `<name> [product|project]`. When not provided, infer from `docs/products/` and `projects/*/docs/` directory matching; confirm with the user if unclear.

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `dev-doc-master` skill.

1. Load the `dev-doc-master` skill.
2. Follow the **DESIGN Reference** in `references/design.md` and the universal rules in `references/consistency.md` for the full workflow: two design flows, discussion focus, document naming and splitting, header, update mode, and quality checklist.
3. Use the templates at `templates/design-product.md` (product) and `templates/design-project.md` (project) inside the skill.

Do not duplicate or paraphrase the specification here. When in doubt, read the reference document.
