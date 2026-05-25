---
description: Create or update product DESIGN documents
---

# Create or Update DESIGN

Create or update a product or project DESIGN document.

**Input**:

- `$1` (type keyword: `product` / `project`, optional)
- `$2` (name, optional, rest semantics)

| `$1` | Action |
|------|--------|
| (empty) | Infer from context; target missing → create, exists → update |
| `product` | Product DESIGN, `$2` = product name |
| `project` | Project DESIGN, `$2` = project name |

- If ambiguous, ask the user

---

## Core Principles

### Output Language

Write the generated or updated document in the user's preferred language unless the user explicitly requests another language.

### Document Paths

**Product DESIGN**: preserve the existing path when updating. Default for new files: `docs/products/<product-name>/DESIGN-<product-name>.md`. Acceptable existing variants: `DESIGN.md`, `DESIGN-*.md`.

**Project DESIGN**: preserve the existing path when updating. Default for new files: `docs/products/<project-name>/DESIGN.md`.

### Preconditions

DESIGN should be grounded in a PRD.

**Required context**:

- Target PRD, if present
- Parent product PRD / DESIGN, for project DESIGNs
- Existing target DESIGN, if updating
- Current conversation context: user decisions, research conclusions, and confirmed requirements
- Implemented code or project docs, when updating from actual implementation

If no PRD exists and the user is not explicitly asking for a design-first draft, ask whether to create the PRD first.

**WopalSpace-specific context**:

- `.wopal-space/STRUCTURE.md`
- `.wopal-space/REGULATIONS.md`
- `docs/products/wopal-space/PRD-wopalspace.md`
- `docs/products/wopal-space/DESIGN-wopalspace.md`

### Core Rules

- DESIGN answers: how the system is structured, how parts interact, and why key choices were made.
- DESIGN may include target-state design when the direction is decided but not fully implemented.
- DESIGN must not duplicate PRD-level vision, target users, or product roadmap except as short references.
- DESIGN must not become an implementation checklist, coding standard, or command transcript.
- Product DESIGN owns system composition, architecture layers, project contracts, runtime model, flows, governance, and key decisions.
- Project DESIGN owns internal module architecture, technical stack choices, interfaces, data / state model, and PRD-phase-aligned implementation status.
- Existing accurate content should be preserved and tightened, not rewritten for novelty.
- Outdated content should be revised or removed when evidence is clear.
- Open uncertainties should be marked as needing confirmation, not silently decided.

### Writing Quality Bar

DESIGN must use design-language, not process-language.

**Required qualities**:

- Concise technical claims: every paragraph should define a structure, boundary, contract, state owner, technology choice, or runtime behavior.
- Design-state wording: describe target architecture and ownership, not temporary implementation location or task progress.
- Evidence-backed claims: when updating from code, translate code facts into design responsibilities and contracts.
- Boundary clarity: every integration or technology choice should say what the system owns and what it must not own.
- Phase-aware status: implementation status should answer how PRD roadmap phases have landed, not merely list modules.

**Forbidden writing**:

- Template commentary such as "this section should...".
- Filler architecture prose that does not change the reader's understanding of the system.
- Decorative diagrams that are harder to read than a sentence or table.
- Implementation-state headings like "current location" as primary design structure.
- By default, do not place temporary implementation artifacts such as backlog items, task plans, or command logs into related documents.

---

## Shared Document Header

Every DESIGN should start with concise metadata after the title:

```markdown
> **Status**: Active  
> **Updated**: YYYY-MM-DD  
> **Product Intent**: `<prd-path>`
```

Project DESIGN should also include:

```markdown
> **Parent Architecture**: `<parent-design-path>`
```

## Section 0: Change Log

Every DESIGN should place `Change Log` after metadata and before section 1:

```markdown
## 0. Change Log

| Date | Type | Summary |
|---|---|---|
| YYYY-MM-DD | Created / Updated | One-line summary |
```

Rules:

- Record only meaningful design intent, architecture, boundary, contract, or status changes.
- Do not record typo fixes or formatting-only polish.
- On update, append one row.
- Keep Summary to one line.
- Do not place Change Log at the end.

---

## Templates

- Product DESIGN: `templates/design-product.md`
- Project DESIGN: `templates/design-project.md`

---

## Update Mode

When updating an existing DESIGN:

1. Preserve the existing path and title unless clearly wrong.
2. Update the `Updated` date.
3. Reconcile against user-confirmed requirements, conversation decisions, implementation facts, related PRD / DESIGN, and known roadmap or implementation evidence.
4. Add missing required sections when the structure is incomplete.
5. Remove or revise obsolete architecture, boundary, interface, or status claims when evidence is clear.
6. Append one Change Log row in Section 0.
7. Keep unresolved items explicit as "Needs confirmation" or equivalent in the document language.

Do not paste code-level implementation details into DESIGN. Translate code facts into architecture, contracts, state ownership, boundaries, or implementation status.

## Quality Checklist

- [ ] Correct template selected: product or project
- [ ] Document language follows user preference
- [ ] Header includes current Updated date
- [ ] DESIGN is grounded in the PRD
- [ ] DESIGN uses concise technical design-language, not template / process commentary
- [ ] Product DESIGN explains cross-project architecture and ownership
- [ ] Project role is concise, technical, and boundary-focused
- [ ] Project module architecture uses design-state language, not implementation-location language
- [ ] Project DESIGN explains modules, technical stack, contracts, state, and PRD-phase-aligned implementation status
- [ ] Technical stack choices include rationale and ownership boundaries
- [ ] Implementation status is aligned to PRD phases or roadmap, not a flat module table
- [ ] Related documents exclude backlog plans and temporary implementation artifacts by default
- [ ] DESIGN avoids PRD-level vision / user / roadmap duplication
- [ ] DESIGN avoids task-level implementation instructions
- [ ] Existing accurate content preserved
- [ ] Obsolete content revised or removed
- [ ] Change Log updated
- [ ] Related durable documents linked

## Response After Completion

Respond in the user's language with:

1. File path
2. Create / update summary
3. Meaningful added, revised, removed / deprecated, and needs-confirmation items
4. Suggested next step, usually `/cupdate-agent-rules` or implementation planning
