---
name: dev-doc-master
description: >
  Author and audit documentation contracts — product PRDs, product DESIGNs,
  and present-state project/module DESIGNs (DESIGN.md, DESIGN-<module>.md).
  Use when asked to create, update, module-split, or check consistency of a
  PRD or DESIGN, sync a project DESIGN with verified code, or run
  /cupdate-prd and /cupdate-design. Do not use for /cupdate-agent-rules,
  /cupdate-readme, or AGENTS.md/README governance (use space-master),
  development Plans (use dev-flow), coding tasks (use df-implement), or
  independent proposal/code reviews (use df-proposal-review or
  df-implement-review).
---

# dev-doc-master — Development Documentation Master

Cross-project documentation standard and authoring base covering product PRDs, product DESIGNs, and project/module **present-state DESIGNs** (main `DESIGN.md` + `DESIGN-<module>.md`). `/cupdate-prd` and `/cupdate-design` are thin entry commands that route here; `AGENTS.md` and project `README.md` maintenance lives in `space-master`.

## When to Use

- Create or update a product PRD or product DESIGN.
- Author, synchronize, or module-split a project/module present-state DESIGN (making delivered capabilities, active business rules, and failure boundaries clear to readers).
- Run semantic review (newcomer test, evidence check, Slop Checklist) and deterministic consistency validation on a documentation set.

> Unimplemented design proposals, alternatives considered, and approval states belong in **Proposals** (`proposals/{proposed,implemented,rejected,archived}/{class}/yyyy-mm-dd-<slug>.md`), never written ahead of code into project present-state DESIGNs.

## Document Set and Routing

| Document | Command | Reference | Template |
|---|---|---|---|
| Product PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| Product DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` |
| Project Present-State DESIGN | `/cupdate-design` | `references/design.md`, `references/design-project-guide.md` | `templates/design-project.md` |
| Module / Sub Present-State DESIGN | (via `/cupdate-design`) | `references/design.md`, `references/design-project-guide.md` | `templates/design-sub.md` |
| AGENTS.md / README | `/cupdate-agent-rules` / `/cupdate-readme` | `space-master` skill | `space-master` templates |

Read `references/consistency.md` before writing any document, and load the matching reference for the document type. When authoring or updating any project or module present-state DESIGN, always load `references/design-project-guide.md`.

## Core Principles (full rules in `references/consistency.md` and `references/design-project-guide.md`)

- **Present-State Accuracy (Project/Sub-DESIGN) vs Product Intent (PRD/Product DESIGN)**: Project and module DESIGNs describe **only shipped, verified behavior, constraints, and active business rules** actually running in code — never unbuilt blueprints or task lists. Product PRDs and Product DESIGNs preserve their architecture and capability-map rules. All DESIGNs forbid process-state narration (`deprecated`, `legacy`, `moved from`, `no longer`, `已废弃`, `历史机制`).
- **Anti-Conflict Structure for Multi-Agent Parallelism**:
  1. Keep main `DESIGN.md` thin as a project positioning, core flow, and module map — never pile module internals into it;
  2. Split multi-module or multi-domain projects into `DESIGN-<module>.md` **by default** (do not wait for a 500-line threshold); keep tightly coupled small single-module projects in a single `DESIGN.md`;
  3. **Omit `Sub-DESIGNs` header enumeration from main DESIGNs** (both Product and Project main DESIGNs stay free of header `Sub-DESIGNs` lists — sub-documents identify themselves by `DESIGN-*.md` filename and `Parent: ./DESIGN.md`, while main docs link from body sections/maps), eliminating header collisions;
  4. Routine single-module work and bug fixes do not touch main `DESIGN.md`; during parallel work, edit only the sub-DESIGN inside your authorized write set, **report out-of-scope drift to the coordinator, and never cross write-set boundaries to edit shared docs**.
- **Never Copy-Paste Volatile Code Inventories**: Never transcribe full source trees, complete CLI option tables, or full API field inventories into DESIGNs; express complete behavior contracts satisfying the 5-Point Required Coverage Checklist (actor/trigger, sequence, permissions `must`/`may`/`must not`, state side effects, full failure outcomes & recovery) inside universal fixed entry/exit anchors + flexible `1..N` domain-concept sections, and link to `Source Carrier` paths.
- **Business Rules and Key Decisions Placement**: Do not create separate `BUSINESS_RULES.md` files (legacy ones remain read-only historical references); active business rules and failure boundaries live directly inside `## Business Rules and Failure Boundaries` (required on active Project main and module sub-DESIGNs). `## Key Decisions` keeps concise shipped conclusions plus links to `proposals/implemented/<class>/...` (or `proposals/archived/<class>/...` for sealed snapshots).
- **Evidence-Backed Fact-Checking and Honesty**: Verify commands, config keys, defaults, routes, errors, and limits against real code, tests, or live execution before asserting them; explicitly mark unverified claims as untested with the condition required to verify them.
- **English Headings + User-Preferred Body Language**: Keep Markdown headings (unnumbered, e.g., `## Module Architecture`) and header field names English across all docs so tooling and cross-project reads stay consistent; write body prose and field explanations in the user's preferred language. Use relative links only; put binding parents/siblings in the header and reference-only links in `## Reference Documents` with zero duplication.

## Naming and Splitting Rules

- Main documents have no suffix: `PRD.md`, `DESIGN.md`. Sub-documents use `PRD-<topic>.md` and `DESIGN-<module>.md` (kebab-case, same directory as main).
- Split by **independent module or domain ownership**, defaulting to module sub-DESIGNs in multi-module projects to support parallel work; do not mechanically slice tightly coupled contracts into fragmented hops.
- Cross-cutting truth sources (`BRANDING.md`, `API-CONTRACT.md`) stay companion documents declared in `Companion Documents`, classified by role rather than historical filename.

## Workflow

1. **Route**: Identify the document type and load `references/consistency.md` plus the matching guide.
2. **Gather & Verify Facts**: Read the target doc, related docs, and **actual source code/tests**; run relevant commands or tests to verify observable claims; ask the user only for genuine product decisions, never for facts readable from the repo.
3. **Author or Synchronize**: Follow the template and dual-scenario sync rules (update in the same delivery as Proposals/features, or update only the affected `DESIGN-<module>.md` on visible bug fixes; skip DESIGN edits on pure internal refactoring; respect parallel write-set boundaries).
4. **Semantic Review & Mechanical Gate**:
   - Run the **Unified Semantic Review Checklist** and **Four-Stage Quality Inspection Loop** in `references/design-project-guide.md` (clarity and the **Slop Checklist** apply to every doc; **"already shipped and code-verified"** constrains only **Project and Module Present-State DESIGNs**, leaving Product PRDs and Product DESIGNs free to plan ahead of implementation);
   - Run the deterministic script `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md` (add `--check-sync [--base <git-ref>]` during code+doc delivery to verify orphan sub-DESIGNs, template placeholders, mandatory boundaries, and `Source Carrier` code-to-DESIGN sync; exit 0 required before reporting done).
5. **Report**: List modified paths, change summary, verified facts vs explicitly marked untested items, gate results (`PASS`/`FAIL`), affected document-set checks, and any out-of-scope drift notices for the coordinator.
