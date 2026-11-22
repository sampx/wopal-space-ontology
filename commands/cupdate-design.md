---
description: Create or update a product DESIGN or project DESIGN
---

# Create or Update DESIGN

Create or update a product DESIGN (product architecture) or a project/module present-state DESIGN (verified current system behavior, contracts, active business rules, and failure bounds). Standalone projects skip product DESIGN (`Parent Architecture: N/A`, `Parent Product: N/A`).

**Input**: `$1` `$2`

**Parameter Notes**: `<name> [product|project]`. When not provided, infer from `docs/products/` and `projects/*/docs/` directory matching; confirm with the user if unclear.

---

## How to Work

The authoritative specification lives in the `dev-doc-master` skill.

1. Load the `dev-doc-master` skill.
2. Follow the **DESIGN Reference** (`references/design.md`), **Present-State Project DESIGN Guide** (`references/design-project-guide.md` when authoring or syncing project/module docs), and universal rules (`references/consistency.md`).
3. Use the templates at `templates/design-product.md` (product), `templates/design-project.md` (project thin main map with `Source Carrier` paths), and `templates/design-sub.md` (universal fixed anchors + flexible domain sections + 5-Point Required Coverage).
4. Run `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md` (add `--check-sync [--base <git-ref>]` during code delivery) and verify exit 0 before reporting done.
