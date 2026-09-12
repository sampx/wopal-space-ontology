# PRD Reference — Product PRD Authoring

Create or update a product PRD document. Template: `templates/prd.md`.

## Document Paths and Naming

- Main PRD has no suffix: `docs/products/<product-name>/PRD.md`.
- Sub-PRDs (if split by topic) use `PRD-<topic>.md` and express a parent-child relationship with the main PRD. When sub-PRDs exist, the main PRD header lists them in a `Sub-PRDs` field; they are structure declarations and never appear in Related Documents.
- When updating, preserve the existing file path.

## Context Collection

Read enough context to avoid inventing requirements. **Required**: existing target PRD, related DESIGN documents, and current conversation context (user needs, decisions, research conclusions, unresolved questions). When updating from implementation, inspect code or project docs only to extract product facts, current capabilities, and actual boundaries — never turn implementation details into PRD content.

WopalSpace-specific context: prefer canonical startup and structure files `.wopal-space/STRUCTURE.md` and `.wopal-space/REGULATIONS.md`.

## Writing Rules

- PRD answers: what to build, for whom, why it matters, and what product outcomes it serves.
- PRD must not explain internal architecture, APIs, storage schemas, implementation steps, or coding conventions.
- Product PRD owns vision, users, product shape, capability boundaries, governance, and evolution.
- Capability Scope / Core Capability Boundaries describe target-state boundaries only: owned capabilities, excluded capabilities, delegation boundaries. No phase timing, current/future grouping, implementation status, delivery progress, module state, checkboxes, or "done / partial / pending" labels. Implementation status belongs in Phase, Plan, UAT, or Verification documents.
- No standalone success-standard or validation-signal sections in PRDs. If validation signals are needed, place them in Plans, UAT, verification documents, or roadmap phase acceptance notes.
- PRD body uses product language, not documentation-authoring language. Do not explain what a section is for or how the template should be used.
- Each paragraph and table row communicates a product fact: user problem, product role, user benefit, owned capability, excluded boundary, product entry, or roadmap outcome.
- Preserve required structure but rewrite weak wording; preserve accurate existing content (tighten, don't rewrite for novelty); revise or remove outdated content when evidence is clear; mark open uncertainties as needing confirmation.

## Header

The header holds only mandatory documents: the DESIGN (or sibling DESIGNs) this PRD follows, plus sub-PRDs when they exist. Reference-only documents belong in Related Documents, never the header.

```markdown
> **Status**: Active  
> **Updated**: YYYY-MM-DD  
> **Related DESIGN** (mandatory): `<path>` — the DESIGN contract this PRD follows  
> **Sub-PRDs** (mandatory when they exist): list every `PRD-<topic>.md`
```

Use localized field labels if the document language is not English.

## Writing Quality Bar

Preferred: "Users can ...", "Wopal can ...", "The CLI provides ...", "This capability reduces ...", "CLI owns ... / does not own ...", "Phase N delivers ...".

Reject and rewrite: section commentary ("This section describes ..."), template commentary ("According to the template ..."), vague evolution language ("has grown into ..."), abstract contrast without product value ("not an API platform"), architecture-only labels without user benefit ("exposes product interfaces").

## Update Mode

1. Preserve the existing document path and title unless clearly wrong.
2. Update the `Updated` date.
3. Reconcile against user-confirmed requirements, implemented code facts, and related PRD/DESIGN documents.
4. Add missing required sections; remove or revise obsolete claims; keep unresolved items explicit.
5. Remove standalone success-standard or validation-signal sections.

**Document-set consistency**: review DESIGN (product + project) and Phase documents against the updated PRD; align when the capability boundaries or vision change. Sub-PRDs stay consistent with the main PRD; the `Sub-PRDs` header list matches actual files.

## Quality Checklist

- [ ] Correct template selected: product
- [ ] Document language follows user preference
- [ ] PRD stays product-level, no architecture/implementation details
- [ ] Capability Scope contains target-state boundaries only
- [ ] Implementation status not in PRD (belongs in Phase/Plan/UAT/Verification)
- [ ] No standalone success-standard / validation-signal section
- [ ] Required structure preserved, weak wording improved
- [ ] No template commentary or documentation-authoring language
- [ ] Every paragraph/table row communicates a product fact or boundary
- [ ] Existing accurate content preserved; obsolete content revised/removed
- [ ] Header = mandatory links only; Related Documents = reference-only; no duplication
- [ ] Whole document set reviewed and aligned

## Response After Completion

Respond in the user's language with: file path; create/update summary; meaningful added/revised/removed/needs-confirmation items; the affected document set (checked / aligned / needs follow-up); suggested next step (PRD done → `/cupdate-design`).
