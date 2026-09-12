# DESIGN Reference — Product / Project DESIGN Authoring

Create or update product DESIGN or project DESIGN. Templates: `templates/design-product.md` (product), `templates/design-project.md` (project).

## Two Design Flows

| Flow | Use Case | Chain |
|---|---|---|
| Standard | Multi-project product requiring cross-project architecture coordination | PRD → Product DESIGN → Roadmap → Project DESIGN → Plan |
| Simplified | Standalone project with no associated product | Project DESIGN (with product-level design) → Plan |

In the standard flow, product DESIGN handles phase decomposition and architecture contracts; project DESIGN handles single-project internal architecture. In the simplified flow, project DESIGN assumes product-level responsibility (Header `Parent Product: N/A`).

## Discussion Focus

- **Product DESIGN**: system layering and subsystem boundaries, runtime model, end-to-end flows, phase decomposition (current phase's overall goal; detail deferred to `/cupdate-roadmap`).
- **Project DESIGN**: project role and boundaries, capability scope, module architecture, technology choices, interface contracts, data model.
- DESIGN keeps only architecture, boundaries, contracts, runtime model, and evolution skeleton. It does not keep implementation status, delivery progress, acceptance results, or task lists.
- Product DESIGN's Evolution Roadmap is a phase skeleton: each Phase keeps only the title, Goal, and Phase document link.

## Document Naming and Splitting

- Main product DESIGN has no suffix: `docs/products/<product-name>/DESIGN.md`.
- Sub-DESIGNs split by topic use `DESIGN-<topic>.md` (kebab-case), same directory as the main DESIGN. No suffix = main, suffixed = sub.
- Split when the main DESIGN grows too long (roughly over 500 lines, or a single chapter over roughly 150 lines). Keep a chapter summary and a link to the sub-DESIGN in the main document.
- The sub-DESIGN header keeps the parent link: `> **上级**: ./DESIGN.md` (or localized equivalent). Sub-DESIGNs may split further only when the topic itself exceeds the size guideline.
- The main document header lists all its sub-DESIGNs (a `Sub-DESIGNs` field). Bidirectional index with sub-DESIGN parent links; must match actual files.

## Header

Header links carry mandatory documents only:

- **Product DESIGN**: `Product Intent` (the PRD this DESIGN follows) + `Sibling DESIGNs` (same-level DESIGNs whose contracts this DESIGN depends on) + `Sub-DESIGNs` (all `DESIGN-<topic>.md` under it) + `Companion Documents` (BRANDING / API-CONTRACT type truth sources) when they exist.
- **Project DESIGN**: `Parent Architecture` (the parent product DESIGN) + `Parent Product` (the parent PRD) + `Sub-DESIGNs` when they exist + `Companion Documents` when they exist.
- Project-level implementation DESIGNs (`projects/*/docs/DESIGN.md`) are references, not siblings — they belong in Related Documents unless they are the direct parent.

## Sub-DESIGN Enumeration (mandatory, filesystem-backed)

The `Sub-DESIGNs` header field is a filesystem fact:

1. Run `ls <docs-dir>/DESIGN-*.md` (or `glob`) **before** writing the header.
2. List exactly those files in the header — one bullet per file, `./DESIGN-<topic>.md` with a short purpose.
3. Re-run the same listing **after** writing and diff against the header.

A header that misses a real file, or lists a file that does not exist, fails the quality gate. This rule exists because a main DESIGN's reader relies on the header as the complete map of its document tree; a partial or phantom list silently loses or invents architecture documents.

## Companion Documents in the Header

Documents like `BRANDING.md` (branding truth source) or `API-CONTRACT.md` (API contract) belong to the set but are not `DESIGN-<topic>.md` decompositions. Declare them in a `Companion Documents` (配套文档) header field, or in the document-relationship table at the top of the main document. Never rename them to fit the `DESIGN-*.md` pattern and never fold them into `Sub-DESIGNs`. This keeps the two categories distinct and prevents naming drift.

## Metadata Field Semantics

- Sub-documents use `Parent` (上级) for the project parent: `上级: ./DESIGN.md`.
- `Parent Architecture` (上级架构) is reserved for product-level documents above the project DESIGN.
- `Status` / `Updated` are mandatory on every document; refresh `Updated` on every edit.
- `Sub-DESIGNs` (子设计) and `Companion Documents` (配套文档) live in the main document header only.

## Discussion Completion Standard

The discussion can end and writing begin when: product DESIGN has clear architecture boundaries and current phase goal; project DESIGN (standard) has clear internal decisions; project DESIGN (simplified) can proceed to Plan; remaining key questions are listed and do not block the architecture expression.

## Update Mode

1. Preserve existing paths and titles.
2. Update the `Updated` date.
3. Align discussion conclusions with existing content.
4. Fill in missing sections.
5. Revise or remove outdated content; delete implementation status and delivery progress.
6. Mark unresolved items as needing confirmation.

**Document-set consistency**: main update → check sub-DESIGNs for stale contracts; sub-DESIGN update → check the main DESIGN chapter that decomposed into it; any DESIGN update → check product PRD and Phase documents for contradictions. Verify the bidirectional index.

## Quality Checklist

- [ ] Correct template selected: product or project
- [ ] Document language follows user preference
- [ ] Header includes current `Updated` date
- [ ] Accurate existing content preserved; obsolete content revised/removed
- [ ] Unconfirmed items marked as needing confirmation
- [ ] Body uses design language; no template commentary, process explanation, task list, or command transcript
- [ ] No implementation status, delivery progress, acceptance results, checkbox tasks, or "completed / pending" module status
- [ ] Product: grounded in the PRD; Evolution Roadmap keeps only phase skeleton
- [ ] Project: grounded in parent PRD/DESIGN (or `Parent Product: N/A`); capability scope is target-state only
- [ ] Header = mandatory links only; Related Documents = reference-only; no duplication
- [ ] Whole document set reviewed: sub-DESIGNs, parent DESIGN, PRD, Phase aligned when affected
- [ ] Bidirectional sub-document index consistent

## Mandatory Quality Gate (before reporting complete)

Run `scripts/verify-docset.py <docs-dir> --main DESIGN.md` (or `PRD.md`). The script must exit 0 before the update is reported complete. It checks, on the actual filesystem:

1. `Sub-DESIGNs` header matches `DESIGN-*.md` files on disk — bidirectional, exact match
2. Every sub-document carries a `上级` parent link to the main document
3. Zero absolute paths (`file:///`, `/Users/...`)
4. All relative links resolve to existing files
5. No sub-DESIGN or header document appears in the end `Related Documents` section
6. No process-state vocabulary (已废弃 / 已放弃 / 迁移 / deprecated / legacy)
7. Every document has an `Updated` date

Any FAIL means the update is incomplete — fix and re-run until PASS. Include the scan result (PASS/FAIL) in the completion report.

## Response After Completion

Respond in the user's language with: file path; creation/update summary; suggested next step (product DESIGN → `/cupdate-roadmap`; standard project DESIGN → `/cupdate-agent-rules`; simplified → create Plan); verification result.
