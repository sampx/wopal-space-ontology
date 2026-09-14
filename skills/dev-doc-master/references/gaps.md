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

## Gap Discovery

Finding gaps is a bounded search, not an impression. The failure mode is a sample: the author reads a design, spots a few things the code lacks, and reports those. That produces a number with no denominator — neither the author nor the reader can tell whether it is 4 of 4 or 4 of 40.

Gaps are discovered by bounded enumeration. The bound comes from a **change of record**, not from reading around.

### Anchor the Range in a Change of Record

A gap exists between a design and an implementation. When a design has been reworked, that rework is a discrete, diffable event — use it as the search boundary.

1. **Find the pivot commit.** The commit where the design's model changed, not where it was merely formatted. A pivot rewrites the design's semantics: a model is replaced, a mechanism swapped, a structural layer removed. Doc renames, header normalization, and heading reshuffles are formatting and move nothing.
2. **Diff the design across the pivot.** `git diff <pivot>^ <head> -- <docs>` yields the exact set of design claims that changed. This is the enumeration: every semantically changed design statement is a candidate to check against the implementation.
3. **Group the diff into change themes.** Collapse the raw diff into a handful of named themes (a model swap, a new mechanism, a command-surface change, a capability-ownership move). Themes are the checklist units — they survive across many small commits and keep the audit tractable.

When no rework has occurred and the design is simply older than the code, anchor instead on the design document itself: enumerate its statements section by section.

### Verify Each Theme Against the Implementation

For every theme, locate the actual carrier in each affected project and record judgement with evidence:

| Judgement | Meaning | Required evidence |
|---|---|---|
| Landed | the implementation matches the design claim | file:line of the carrier |
| Partial | the carrier exists but does not fulfill the claim | file:line plus the specific shortfall |
| Missing | no carrier exists | the search performed (what was grepped, in what scope) |
| Doc drift | implementation is right, the design text is stale | design file:line that contradicts reality |

A judgement without a `file:line` is an impression, not a finding. `Missing` in particular requires stating the search, because absence of evidence is only meaningful when the search scope is known.

### Sweep in Both Directions

Design-to-code finds unimplemented claims. Code-to-design finds the opposite: assets, commands, and modules that exist with no design statement behind them. Both are gaps of a kind — one is missing work, the other is missing authority. Run both and record both.

### Reconcile Against the Existing Gap Set

New findings must be checked against the gaps already recorded before a new identifier is minted. An implementation shortfall is very often already covered — read the candidate gap's `Exit` criteria and ask whether they already close the finding.

This step prevents duplicate tracking, and it also prevents the opposite error: declaring "uncovered" without reading. A finding is only uncovered after the full `Exit` list of every related gap has been read. A `Target` that mentions the area is not coverage; a concrete `Exit` criterion is.

### Convergence

The audit is complete when every theme has a judgement, every judgement carries evidence, and every finding is either mapped to an existing gap or recorded as new. That is the denominator: themes enumerated = themes judged = findings accounted for.

Report the audit as the theme table plus the reconciliation result. A reader who trusts the report can re-run the diff and reach the same theme list — that is what makes the result checkable rather than asserted.

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
- [ ] Every gap was found by the bounded enumeration in Gap Discovery, not by impression — the search range is stated and diffable
- [ ] Every finding was reconciled against existing gaps' full `Exit` lists before a new identifier was minted

## Update Mode

1. Refresh `Updated`.
2. Add new gaps with the next free number in their prefix.
3. Revise gap entries as the implementation moves.
4. When a gap closes, remove its entry per Gap Lifecycle. Leave no "completed" markers — a gap that no longer exists is simply gone, and the number stays retired.
5. Re-check the document-set: a design change may close or open gaps elsewhere in the set.
