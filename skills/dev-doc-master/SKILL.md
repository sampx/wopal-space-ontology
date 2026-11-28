---
name: dev-doc-master
description: >
  Author and audit documentation contracts — product PRDs, product DESIGNs,
  present-state project/module DESIGNs (DESIGN.md, DESIGN-<module>.md), and domain glossaries (GLOSSARY.md).
  Use when asked to create, update, module-split, or check consistency of a
  PRD, DESIGN, or domain glossary, sync a project DESIGN with verified code, or run
  /cupdate-prd and /cupdate-design. Do not use for /cupdate-agent-rules,
  /cupdate-readme, or AGENTS.md/README governance (use space-master),
  development Plans (use dev-flow), coding tasks (use df-implement), or
  independent proposal/code reviews (use df-proposal-review or
  df-implement-review).
---

# dev-doc-master — Development Documentation Master

Cross-project documentation standard and authoring base covering product PRDs, product DESIGNs, project/module **present-state DESIGNs** (main `DESIGN.md` + `DESIGN-<module>.md`), and optional domain glossaries. `/cupdate-prd` and `/cupdate-design` are thin entry commands that route here; `AGENTS.md` and project `README.md` maintenance lives in `space-master`.

## Document Set and Routing

| Document | Command | Reference | Template |
|---|---|---|---|
| Product PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| Product DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` |
| Project Present-State DESIGN | `/cupdate-design` | `references/design.md`, `references/design-project-guide.md` | `templates/design-project.md` |
| Module / Sub Present-State DESIGN | (via `/cupdate-design`) | `references/design.md`, `references/design-project-guide.md` | `templates/design-sub.md` |
| Domain glossary | (on request or delivery sync) | `references/glossary.md` | `templates/glossary.md` |
| AGENTS.md / README | `/cupdate-agent-rules` / `/cupdate-readme` | `space-master` skill | `space-master` templates |

Read `references/consistency.md` before writing any document, and load the matching reference for the document type. When authoring or updating any project or module present-state DESIGN, always load `references/design-project-guide.md`.

## Core principles

`references/consistency.md` owns document roles, naming, binding links, and shared write-set discipline. `references/design-project-guide.md` owns the five-point behavior contract standard (target and present-state), evidence, semantic review, and delivery synchronization. `references/glossary.md` owns domain definitions and their synchronization. Product PRDs and product DESIGNs can describe intent; project/module DESIGN records verified delivered behavior. Keep proposed target contracts and new definitions in Proposal until delivery.

## Workflow

1. **Route**: Identify the document type and load `references/consistency.md` plus the matching guide.
2. **Gather & Verify Facts**: Read the target doc, related docs, and **actual source code/tests**; run relevant commands or tests to verify observable claims; ask the user only for genuine product decisions, never for facts readable from the repo.
3. **Author or Synchronize**: Follow the matching template and guide; synchronize affected DESIGNs and glossary in the delivery, respecting write sets.
4. **Semantic Review & Mechanical Gate**:
   - Run the **Unified Semantic Review Checklist** and **Four-Stage Quality Inspection Loop** in `references/design-project-guide.md` (clarity and the **Slop Checklist** apply to every doc; **"already shipped and code-verified"** constrains only **Project and Module Present-State DESIGNs**, leaving Product PRDs and Product DESIGNs free to plan ahead of implementation);
   - Run the deterministic script `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md` (add `--check-sync [--base <git-ref>]` during code+doc delivery to verify orphan sub-DESIGNs, template placeholders, mandatory boundaries, and `Source Carrier` code-to-DESIGN sync; exit 0 required before reporting done).
5. **Report**: List modified paths, change summary, verified facts vs explicitly marked untested items, gate results (`PASS`/`FAIL`), affected document-set checks, and any out-of-scope drift notices for the coordinator.
