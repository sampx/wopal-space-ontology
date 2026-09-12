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

- **Product DESIGN**: `Product Intent` (the PRD this DESIGN follows) + `Sibling DESIGNs` (same-level DESIGNs whose contracts this DESIGN depends on) + `Sub-DESIGNs` (all `DESIGN-<topic>.md` under it).
- **Project DESIGN**: `Parent Architecture` (the parent product DESIGN) + `Parent Product` (the parent PRD) + `Sub-DESIGNs` when they exist.
- Project-level implementation DESIGNs (`projects/*/docs/DESIGN.md`) are references, not siblings — they belong in Related Documents unless they are the direct parent.

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

## Response After Completion

Respond in the user's language with: file path; creation/update summary; suggested next step (product DESIGN → `/cupdate-roadmap`; standard project DESIGN → `/cupdate-agent-rules`; simplified → create Plan); verification result.
