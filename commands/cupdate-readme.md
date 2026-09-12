---
description: Create or update project README.md
---

# Create or Update README

Create or update a project `README.md`.

**Input**: `$ARGUMENTS`

**Parameter Notes**: Project name. When not provided, look up the project list under `projects/` plus context to infer. Confirm if unclear.

Examples:

```bash
/cupdate-readme
/cupdate-readme projects/wopal-cli
```

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `dev-doc-master` skill.

1. Load the `dev-doc-master` skill.
2. Follow the **README Reference** in `references/readme.md` and the universal rules in `references/consistency.md` for the full workflow: document paths and naming, purpose, core rules, update mode, confirmation policy, and quality checklist.
3. Use the inline template in the README reference.

Do not duplicate or paraphrase the specification here. When in doubt, read the reference document.
