# DESIGN Reference — Product / Project DESIGN Authoring

Create or update product DESIGN or project DESIGN. Templates: `templates/design-product.md` (product), `templates/design-project.md` (project).

## Two Design Flows

| Flow | Use Case | Chain |
|---|---|---|
| Standard | Multi-project product requiring cross-project architecture coordination | PRD → Product DESIGN (architecture + Capability Roadmap) → Project DESIGN → Phase → Plan |
| Simplified | Standalone project with no associated product | Project DESIGN (with product-level design) → Plan |

In the standard flow, product DESIGN handles architecture contracts and the capability map; project DESIGN handles single-project internal architecture. In the simplified flow, project DESIGN assumes product-level responsibility (Header `Parent Product: N/A`).

## Discussion Focus

- **Product DESIGN**: system layering and subsystem boundaries, runtime model, end-to-end flows, capability roadmap (the capability dimensions and their maturity steps).
- **Project DESIGN**: project role and boundaries, capability scope, module architecture, technology choices, interface contracts, data model.
- DESIGN keeps only architecture, boundaries, contracts, runtime model, and the capability map. It does not keep implementation status, delivery progress, acceptance results, or task lists.

## Capability Roadmap

The product DESIGN's `Capability Roadmap` is a capability map, not a time-line of phases. Each row is a capability dimension; the columns are its maturity steps (current shape / next milestone / target shape) with an owning project.

The map describes direction, not dates. It answers "what shape does this capability still grow toward", never "when will it ship". This is what keeps it from drifting away from reality: a capability's direction is fixed by architecture, while a phase schedule guessed months ahead is not.

A phase is cut from this map: a phase is a batch of capability steps that can be verified together. The phase's Goal traces to a row and a target step. The map's `Phase` entries keep only the title, Goal, and phase document link.

When a capability dimension advances or a new one appears, add or update its row. New capability dimensions surface from project designs — a project DESIGN that introduces a new architectural concern registers it here.

## Document Naming and Splitting

- Main product DESIGN has no suffix: `docs/products/<product-name>/DESIGN.md`.
- Sub-DESIGNs split by topic use `DESIGN-<topic>.md` (kebab-case), same directory as the main DESIGN. No suffix = main, suffixed = sub.
- Split when the main DESIGN grows too long (roughly over 500 lines, or a single chapter over roughly 150 lines). Keep a chapter summary and a link to the sub-DESIGN in the main document.
- The sub-DESIGN header keeps the parent link: `> **Parent**: ./DESIGN.md`. Sub-DESIGNs may split further only when the topic itself exceeds the size guideline.
- The main document header lists all its sub-DESIGNs (a `Sub-DESIGNs` field). Bidirectional index with sub-DESIGN parent links; must match actual files.

## Header

Header links carry mandatory documents only:

- **Product DESIGN**: `Product Intent` (the PRD this DESIGN follows) + `Sibling DESIGNs` (the project DESIGNs of its core subsystems) + `Sub-DESIGNs` (all `DESIGN-<topic>.md` under it) + `Companion Documents` (BRANDING / API-CONTRACT type truth sources) when they exist.
- **Project DESIGN**: `Parent Architecture` (the parent product DESIGN) + `Parent Product` (the parent PRD) + `Sub-DESIGNs` when they exist + `Companion Documents` when they exist.

## Product DESIGN and Project DESIGNs

A product DESIGN organizes its core subsystems. Each subsystem has its own project DESIGN carrying that subsystem's internal architecture. The two are documents at different levels, and the relationship between them is ownership, not adjacency.

- The product DESIGN's `Core Projects` section gives each subsystem its role, boundary, and interaction contract, and links to that subsystem's project DESIGN.
- Those project DESIGNs belong in the header's `Sibling DESIGNs` field. The product DESIGN depends on their contracts, so a reader of the product architecture must be able to reach them from the header. **A document that states a contract this DESIGN must follow is a sibling — wherever its file lives.**
- Cross-repository location does not weaken the link. A project DESIGN in another repository is still a sibling when its contract binds this document. Repository boundaries say where files live, not how strongly they bind.

The header is the reader's map of what this design depends on. Moving a binding document to the end section tells the reader it is optional reading, which is the opposite of the truth.

## Sibling DESIGNs vs Reference Documents

The distinction is obligation, not proximity:

- **Sibling DESIGNs** (header): documents whose contracts this DESIGN must follow. A reader cannot evaluate this design without them.
- **Reference Documents** (end section): material that informs without binding — research, external specifications, auxiliary notes, third-party design write-ups.

A document is one or the other, never both. When a document's contract binds this design, it belongs in the header even if it is long, external, in another repository, or written by another team. When it merely gives useful background, it belongs in the end section.

The temptation to treat every related document as "reference" is exactly what this field prevents. `Reference Documents` is not a bucket for documents that seem related; it carries documents a reader would benefit from following but that this design does not depend on.

## Sub-DESIGN Enumeration (mandatory, filesystem-backed)

The `Sub-DESIGNs` header field is a filesystem fact:

1. Run `ls <docs-dir>/DESIGN-*.md` (or `glob`) **before** writing the header.
2. List exactly those files in the header — one bullet per file, `./DESIGN-<topic>.md` with a short purpose.
3. Re-run the same listing **after** writing and diff against the header.

A header that misses a real file, or lists a file that does not exist, fails the quality gate. This rule exists because a main DESIGN's reader relies on the header as the complete map of its document tree; a partial or phantom list silently loses or invents architecture documents.

## Companion Documents in the Header

Documents like `BRANDING.md` (branding truth source) or `API-CONTRACT.md` (API contract) belong to the set but are not `DESIGN-<topic>.md` decompositions. Declare them in a `Companion Documents` header field, or in the document-relationship table at the top of the main document. Never rename them to fit the `DESIGN-*.md` pattern and never fold them into `Sub-DESIGNs`. This keeps the two categories distinct and prevents naming drift.

The reverse error is equally real: a supporting document that in fact carries one of the main DESIGN's own architectural concerns must be recognized as a sub-design, even when it was originally written under a descriptive name like `TESTING.md` or `CAPABILITY-PROTOCOL.md`. Leave it in place and the document tree loses a branch — the file exists, but the main header never points at it. Classification criteria and the rename that follows are in `consistency.md` (Companion Documents vs Sub-DESIGNs).

## Metadata Field Semantics

- Sub-documents use `Parent` for the project parent: `Parent: ./DESIGN.md`.
- `Parent Architecture` is reserved for product-level documents above the project DESIGN.
- `Status` / `Updated` are mandatory on every document; refresh `Updated` on every edit.
- `Sub-DESIGNs` and `Companion Documents` live in the main document header only.

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
- [ ] Product: grounded in the PRD; Capability Roadmap is a capability map (rows are capability dimensions, columns are maturity steps), phase entries keep only title + Goal + link
- [ ] Project: grounded in parent PRD/DESIGN (or `Parent Product: N/A`); capability scope is target-state only
- [ ] Header = mandatory links only; Reference Documents = reference-only; no duplication
- [ ] Whole document set reviewed: sub-DESIGNs, parent DESIGN, PRD, Phase aligned when affected
- [ ] Bidirectional sub-document index consistent
- [ ] Every supporting document classified by content: each one carrying a main DESIGN concern is a sub-design, named and enumerated; each one that is a cross-cutting truth source stays a companion
- [ ] No delegating reference in the main document points at a file that is neither a sub-design nor a declared companion
- [ ] Product DESIGN: every core subsystem's project DESIGN is listed in `Sibling DESIGNs`, regardless of which repository it lives in
- [ ] `Reference Documents` carries no document whose contract this design follows

## Mandatory Quality Gate (before reporting complete)

Run `scripts/verify-docset.py <docs-dir> --main DESIGN.md` (or `PRD.md`). The script must exit 0 before the update is reported complete. It checks, on the actual filesystem:

1. `Sub-DESIGNs` header matches `DESIGN-*.md` files on disk — bidirectional, exact match
2. Every sub-document carries a `Parent` link to the main document
3. Zero absolute paths (`file:///`, `/Users/...`)
4. All relative links resolve to existing files
5. No sub-DESIGN or header document appears in the end `Reference Documents` section
6. No process-state vocabulary (已废弃 / 已放弃 / 迁移 / deprecated / legacy)
7. Every document has an `Updated` date

Any FAIL means the update is incomplete — fix and re-run until PASS. Include the scan result (PASS/FAIL) in the completion report.

## Response After Completion

Respond in the user's language with: file path; creation/update summary; suggested next step (product DESIGN → `/cupdate-roadmap`; standard project DESIGN → `/cupdate-agent-rules`; simplified → create Plan); verification result.
