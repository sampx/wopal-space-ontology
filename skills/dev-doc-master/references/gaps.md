# GAPS Reference — Project Gap Tracking Authoring

Create or update a project-level `GAPS.md`: the record of divergence between a project's design target state and its implementation. Template: `templates/gaps.md`.

## What a GAPS Document Is

A GAPS document is a **process document**, not a design document. It records where the implementation has not yet caught up with the design, and it exists to feed planning. When the gaps it tracks are closed, the document is removed entirely — a project with no gaps has no GAPS.md.

This distinction drives every rule below. A GAPS document **references** the design; it never **inherits** from it, and it never restates design content.

## When to Use

- Record newly discovered divergence between design and implementation.
- Update gap status as work progresses.
- Close a gap when the implementation catches up.

Do not use GAPS for design decisions (that belongs in DESIGN), for phase scope and acceptance (that belongs in a Phase document), or for execution ordering across multiple plans (that belongs in the product-level roadmap).

## Header

The header carries the design truth the gaps are measured against:

```
> **Status**: Active
> **Updated**: YYYY-MM-DD
> **Design Source**: `./DESIGN.md` (the design this document measures against)
> **Companion**: <one line describing what this document tracks>
```

`Design Source` names the authoritative design document this project's gaps are measured against. Use `Design Source`, not `Parent Architecture` — a GAPS document does not inherit an architecture contract, it measures divergence from one. When the project has a document set, point at the main DESIGN; the sub-designs are reachable through its `Sub-DESIGNs` field.

`Updated` is refreshed on every edit.

## Numbering

Gap identifiers are `<PREFIX>-G<n>`, where the prefix identifies the owning project or topic. Examples: `CLI-G1`, `ONT-G3`, `ASSEMBLY-G5`.

Once assigned, an identifier is never reused and never renumbered. Closing a gap leaves its number retired, so that references in plans, issues, and commits stay resolvable. When a new gap supersedes a closed one, it takes a new number.

When one document tracks several topics, document the prefix scheme in a `## Numbering` section near the top, and explain which topics map to which prefix. A reader should never have to infer what a prefix means.

## Gap Entries

Each gap is a `###` section with a stable title and three labelled parts:

```markdown
### CLI-G3: `space sync` missing, legacy commands not removed (P0)

**Target State**: What the design says the system does.

**Current State**: What the implementation actually does today, with concrete carriers — file paths, function names, command names.

**Closing**: What closing this gap requires, as a short list when the work has distinct parts.
```



**Target state** comes from the design document and stays faithful to it. If the design and the implementation disagree about what *should* be, that is a design question — resolve it in DESIGN first, then record the gap.

**Current state** is grounded in the code. Name the actual carriers: the module, the function, the command. A current-state paragraph that could be written without opening the code is a sign the gap was not verified, and an unverified gap sends planning in the wrong direction.

**Closing** describes the work at a level that a planning step can act on, without becoming a task list. Concrete enough to scope, short enough to read.

Priority is recorded in the entry title as `(P0)` / `(P1)`, so that a reader scanning headings sees the ordering without opening each gap.

## Grouping

Group gap entries under `##` headings by topic — the dimensions along which a reader would look for gaps, such as an architectural area (`## Assembly Model`) or a document concern (`## Capability System`). Each `##` group is navigation, not classification: it exists so a reader can find the relevant gaps without reading the whole document.

## End Section

The document closes with a `## Reference Documents` section carrying reference-only material:

- The project's own design documents not already named in `Design Source`.
- Related documents that inform but do not bind.

Header links and end links are disjoint. A document named in the header never appears again in the end section — listing it twice implies an obligation the reader cannot interpret.

## Relationship to the Product Roadmap

A project's GAPS.md is the **single source of truth** for gap detail. A product-level roadmap indexes gaps by identifier and owning phase; it does not restate titles, priorities, or descriptions.

This split exists because duplicated gap descriptions drift. The roadmap points at gaps; the project document defines them.

## Quality Checklist

- [ ] Header uses `Design Source`, not `Parent Architecture`
- [ ] `Updated` date is current
- [ ] Numbering scheme documented when the document tracks multiple prefixes
- [ ] Every gap has Target State / Current State / Closing
- [ ] Every Current State names concrete code carriers (file, function, command)
- [ ] Every Target State traces back to a statement in the design document
- [ ] Priority marked in each entry title
- [ ] End section is reference-only and does not repeat header documents
- [ ] No design decisions recorded as gaps — those belong in DESIGN

## Update Mode

1. Refresh `Updated`.
2. Add new gaps with the next free number in their prefix.
3. Revise gap entries as the implementation moves.
4. When a gap closes, remove its entry. Leave no "completed" markers — a gap that no longer exists is simply gone, and the number stays retired in the numbering record.
5. Re-check the document-set: a design change may close or open gaps elsewhere in the set.
