# GAPS Reference — Project Gap Tracking Authoring

Create or update a project-level `GAPS.md`: the record of divergence between a project's design target state and its implementation. Template: `templates/gaps.md`.

## What a GAPS Document Is

A GAPS document records where a project's implementation has not yet caught up with its design. It exists to feed planning: a reader opens it to learn what is still missing, how far the design and the code have drifted apart, and which gaps are worth closing next.

It is a **process document**, not a design document. It measures divergence from the design; it never inherits a design contract and never restates design content. When every gap it tracks is closed, the document is deleted entirely — a project with no gaps has no `GAPS.md`.

The document has three surfaces:

- **A header** declaring the design it measures against (`Design Source`).
- **Topic groups** (`##`) holding the gap entries, one topic per architectural area or document concern.
- **Gap entries** (`###`), each carrying `Current` / `Target` / `Design` / `Exit`.

## Naming and Location

The file is named `GAPS.md` and lives in the project's `docs/` directory, beside the `DESIGN.md` it measures against.

```
projects/<project>/docs/
├── DESIGN.md
├── DESIGN-<topic>.md
└── GAPS.md
```

There is exactly one `GAPS.md` per project. Topics are grouped inside it under `##` headings — not split into separate files. When a document set grows large enough that one project's gaps no longer fit one readable file, that is a signal the project should be split, not that gaps should be scattered.

The ontology worktree places its `GAPS.md` at `.wopal/docs/GAPS.md`, following the same rule: beside its `DESIGN.md`.

## Numbering

Gap identifiers are `<PREFIX>-G<n>`: a project or topic prefix, a literal `-G`, and a sequential number. Examples: `CLI-G1`, `ONT-G3`, `ASSEMBLY-G5`, `ELL-G1`.

**Prefix.** The prefix identifies the owning project or topic. A single-prefix document uses the project name (`CLI-G<n>`). A document that tracks several distinct areas uses one prefix per area, and the prefix alone carries the meaning: `ASSEMBLY-G<n>` is runtime assembly, `ELL-G<n>` is desktop and onboarding. A reader never has to look up what a prefix means — it is the area name.

**Sequence.** Numbers run independently per prefix and increment by one. `CLI-G1`, `CLI-G2`, `CLI-G3` are the first three CLI gaps; `ASSEMBLY-G1` starts its own sequence.

**Immutability.** Once assigned, an identifier is never reused and never renumbered. A closed gap leaves its number retired, so references in plans, issues, and commits stay resolvable forever. A gap that supersedes a closed one takes a new number.

The numbering record is the document's own git history. A retired number is visible in the commit that removed the entry; there is no separate ledger to maintain, and no `Numbering` section in the document body.

## Header

The header carries the design truth the gaps are measured against:

```
> **Status**: Active
> **Updated**: YYYY-MM-DD
> **Design Source**: `./DESIGN.md` (the design this document measures against)
> **Companion**: <one line describing what this document tracks>
```

`Design Source` names the authoritative design document this project's gaps are measured against. Use `Design Source`, not `Parent Architecture` — a GAPS document does not inherit an architecture contract, it measures divergence from one. When the project has a document set, point at the main DESIGN; the sub-designs are reachable through its `Sub-DESIGNs` field.

The source design must be **formal** (`Active`). A gap is the distance between a settled target and the current reality, so measuring against a draft produces gaps that the next design revision invalidates. When the design is still `Draft` or `Proposed`, promote it to `Active` first, then open the gap. See the document lifecycle rules in `consistency.md`.

`Updated` is refreshed on every edit.

## Gap Entries

Each gap is a `###` section with a stable title and four labelled parts. The labels are English — they are structured field names, and the quality gate matches them literally.

```markdown
### CLI-G3: `space sync` missing, legacy commands not removed (P0)

**Current**: What the implementation actually does today, with concrete carriers — file paths, function names, command names.

**Target**: What the design says the system does.

**Design**: Where the solution is documented.

**Exit**:
- [ ] verifiable closing criterion
- [ ] verifiable closing criterion
```

**Current** is grounded in the code. Name the actual carriers: the module, the function, the command. A current paragraph that could be written without opening the code is a sign the gap was not verified, and an unverified gap sends planning in the wrong direction.

**Target** comes from the design document and stays faithful to it. If the design and the implementation disagree about what *should* be, that is a design question — resolve it in DESIGN first, then record the gap.

**Design** points at the document that carries the solution, by its own name. The reader follows it for the full contract; the gap entry does not restate it.

**Exit** lists the criteria that close the gap, as checkboxes. They describe delivery facts, not implementation steps, and each is independently verifiable. The checkboxes are the closing criteria, not a progress tracker: the gap is removed once all of them are met and its Plan reaches `done`. They are not hand-maintained in place.

Priority is recorded in the entry title as `(P0)` / `(P1)`, so that a reader scanning headings sees the ordering without opening each gap.

## Grouping

Group gap entries under `##` headings by topic — the dimensions along which a reader would look for gaps, such as an architectural area (`## Assembly Model`) or a document concern (`## Capability System`). Each `##` group is navigation, not classification: it exists so a reader can find the relevant gaps without reading the whole document.

The document goes straight from its header to the first topic group. Prose sections explaining what the document is or how to number it belong in this reference, not in the document body.

## End Section

The document closes with a `## Reference Documents` section carrying reference-only material:

- The project's own design documents not already named in `Design Source`.
- Related documents that inform but do not bind.

Header links and end links are disjoint. A document named in the header never appears again in the end section — listing it twice implies an obligation the reader cannot interpret.

## Relationship to the Capability Roadmap and Phases

A project's GAPS.md is the **single source of truth** for gap detail. The product DESIGN's Capability Roadmap describes product-level capability direction; a Phase document lists the gaps its scope closes, by identifier, title, priority, and design pointer, without restating their descriptions.

This split exists because duplicated gap descriptions drift. The Phase points at gaps; the project document defines them. Execution order across multiple plans belongs to the Phase document, not to GAPS.

## Gap Lifecycle

A gap has two states: **open** (it exists in `GAPS.md`) and **closed** (it is gone). There is no third state, and no status field — the presence or absence of the entry is the status.

A gap closes when its `Exit` criteria are met and the Plan that carried it reaches `done`. The `Exit` criteria are the gap's own verification statements; they are verified during Plan execution.

Closing procedure:

1. Confirm the gap's `Exit` criteria are all met, with the Plan in `done`.
2. Remove the gap entry from `GAPS.md`.
3. Leave the identifier retired — the number is never reused.
4. The Phase document's gap inventory entry drops when the gap disappears from `GAPS.md`.

Do not add a `Status` field, an "in progress" marker, or a "completed" note. A Plan's own state already tells a reader that a gap is being worked on; a second status in GAPS duplicates that and drifts out of sync.

## Quality Checklist

- [ ] File is `GAPS.md` in the project's `docs/`, beside the `DESIGN.md` it measures
- [ ] Header uses `Design Source`, not `Parent Architecture`
- [ ] `Design Source` points at a formal document (`Active`), never a draft
- [ ] `Updated` date is current
- [ ] Every identifier follows `<PREFIX>-G<n>`; no number is reused or renumbered
- [ ] No `About This Document` or `Numbering` prose section in the body — the document goes straight from the header to its topic groups
- [ ] Every gap has the four labelled parts: `Current` / `Target` / `Design` / `Exit`
- [ ] Every `Current` names concrete code carriers (file, function, command)
- [ ] Every `Target` traces back to a statement in the design document
- [ ] Every `Design` names the document carrying the solution
- [ ] Every `Exit` is a checkbox list of verifiable closing criteria
- [ ] Priority marked in each entry title
- [ ] End section is reference-only and does not repeat header documents
- [ ] No design decisions recorded as gaps — those belong in DESIGN
- [ ] No status field or "in progress" marker on any gap — presence or absence is the status

## Update Mode

1. Refresh `Updated`.
2. Add new gaps with the next free number in their prefix.
3. Revise gap entries as the implementation moves.
4. When a gap closes, remove its entry per Gap Lifecycle. Leave no "completed" markers — a gap that no longer exists is simply gone, and the number stays retired.
5. Re-check the document-set: a design change may close or open gaps elsewhere in the set.
