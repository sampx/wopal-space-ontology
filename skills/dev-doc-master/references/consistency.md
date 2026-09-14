# Document-Set Consistency — Universal Rules

These rules apply to every document in the product/project documentation set: PRD, DESIGN (main and sub), Phase, README, and AGENTS.md. They exist so the document set stays coherent, avoids duplicated or contradictory claims, and keeps the maintenance cost low.

## No Chapter Numbering

Headings express structure through Markdown heading levels, not numbers. Write `## Capability Scope`, never `## 1. Capability Scope`. Chapter numbers force renumbering on every insert, move, or deletion; heading levels survive structural edits. Applies to every generated or updated document.

## Target-State Writing

Documents describe the target state only — what the system is, what exists, who owns it, what responsibility it carries. Process-state descriptions are forbidden: no "deprecated", "legacy", "moved from X", "old path", "migration", or "historical" notes. When a capability is owned elsewhere, state the ownership, not the move. A reader of a document learns the current structure and responsibilities, never the history of how it got there.

## Writing Style

Target-state content is only half the job; how it reads is the other half. These rules apply to every sentence in every document of the set.

### Natural Language

Write like a human explaining something clearly to a colleague. Read the sentence aloud — if it sounds like a machine produced it, rewrite it. Prefer plain verbs and concrete nouns over nominalizations and stacked qualifiers.

### One Idea Per Sentence

Keep sentences short and carry one thought each. When a sentence contains two independent claims, split it. Long compound sentences hide which part is the commitment and which is decoration.

### Affirmative Over Negative

State what a component does, what it owns, and who is responsible. Instead of "X does not handle Y" or "Y is not supported", write "Y is owned by X" or "Y belongs to a later phase". The reader should learn the structure, not reconstruct it from a list of absences.

### Ownership Over Exclusion

Draw boundaries through ownership rather than exclusion. "X is responsible for A; Y owns B" reads better than "X does not do B, and Y is not involved in A". Every boundary statement names the owner of each side.

## Relative Links Only

All document links are relative to the repository root or the document's directory. Absolute paths (e.g. `/Users/...`, `file:///...`) are forbidden because these documents are committed to git and shared across machines — an absolute path works only on the machine that wrote it. Use `./DESIGN.md`, `../DESIGN.md`, or `docs/products/<name>/DESIGN.md` style relative paths consistently within a document.

## Header = Mandatory, End = Reference

Every document has two link zones with distinct obligations:

- **Header** (metadata block after the title): carries only **mandatory** documents — the parent document and sibling documents that this document must follow. Examples: a PRD's `Related DESIGN`, a sub-DESIGN's `Parent: ./DESIGN.md`, a Phase's `Product PRD` + `Product DESIGN`.
- **End** (`Reference Documents`): carries **reference-only** documents — material that informs the document without binding it. The narrower name matters: it tells an author that a document belongs here only when a reader would genuinely benefit from following it, not merely because it is adjacent.

A document is either a mandatory header link or a reference end link, never both. Never list a header document again in the end section, and never promote a reference document into the header as if it were binding.

## Language

Headings and header field names are English in every document, regardless of the document's language. The quality-gate script matches these literally, and a stable heading vocabulary keeps documents comparable across projects.

Body text and header field values follow the document's language. A Chinese document reads Chinese in the body and in field explanations; its headings stay English.

## Process Documents vs Design Documents

The document set contains two kinds of documents, and they relate to the design differently:

- **Design documents** (PRD, DESIGN, Phase) *inherit*: they declare the parent documents they must follow, and their header carries those mandatory parents.
- **Process documents** (GAPS) *measure divergence from*: they name the design they track, without becoming part of its lineage.

The distinction matters for the header. A design document uses lineage fields (`Parent Architecture`, `Parent Product`, `Product Intent`). A process document uses `Design Source` — it points at the design it measures, and it does not claim to follow an architecture contract. Writing `Parent Architecture` on a GAPS document misstates the relationship and implies an obligation the document does not carry.

Process documents also carry a lifecycle note. A GAPS document states that it is removed once its gaps close, because a reader who mistakes it for permanent documentation will maintain it as such and let stale entries accumulate.

## Header = Mandatory, End = Reference

A suffix-free main document is the single entry point to its document tree. Its header must enumerate every `DESIGN-<topic>.md` / `PRD-<topic>.md` sub-document under it (a `Sub-DESIGNs` / `Sub-PRDs` field). Each sub-document header points back via `Parent: ./DESIGN.md`. This bidirectional index must match the actual files on disk — when a sub-document is added or removed, both sides are updated. Sub-documents listed in the header are structure declarations, not references, so they never appear in the end section.

## Sub-DESIGN Enumeration Is a Filesystem Fact

The header's sub-document list is a filesystem fact, not a summary. Before writing the header, list every `DESIGN-<topic>.md` in the same directory with `ls`. The header must enumerate exactly those files — nothing more, nothing less. After writing, re-run the same listing and diff against the header. A header that misses a file breaks the bidirectional index; a header that lists a nonexistent file is a dead link. This check is part of the mandatory quality gate.

## Companion Documents vs Sub-DESIGNs

A documentation set contains two distinct kinds of supporting files:

- **Sub-DESIGNs** (`DESIGN-<topic>.md`): architecture documents that decompose a main DESIGN chapter. They follow the naming convention, carry a `Parent` link, and are enumerated in the main header's `Sub-DESIGNs` field.
- **Companion documents** (e.g. `BRANDING.md`, `API-CONTRACT.md`): single-source-of-truth documents that belong to the set but are not architecture decompositions. They do not use the `DESIGN-<topic>.md` naming pattern, do not carry a `Parent` link, and are declared in the main header's `Companion Documents` field or in the document-relationship table.

Both directions of misclassification are errors. Promoting a companion document into the sub-design enumeration invents a structure that does not exist. Leaving a real sub-design under an ad-hoc name hides a branch of the document tree from every reader who trusts the main header as the map — the document exists, but nothing points at it.

### Classification Is by Content, Not by Name

A file's name records how it was first created, not what it became. Classify by asking what the document does:

1. **Does the main DESIGN treat it as an elaboration of one of its own sections?** The decisive signal is a delegating reference in the main document — a sentence of the form "the full protocol lives in X", "details are in X", "the release contract is in X". If the main document hands part of its own architecture to another file, that file is a sub-design, whatever it is called.
2. **Is it the sole authoritative source for one architectural concern** (a contract, a protocol, a layering model, a subsystem) rather than a cross-cutting reference table (brand constants, business rule numbering)? The former is a sub-design; the latter is a companion.

Size corroborates the answer. A supporting document that approaches the main DESIGN's own length, or that would exceed the chapter split guideline (`design.md`, roughly 150 lines) on its own, is carrying architecture — it belongs in the sub-design enumeration.

A classified sub-design is renamed to `DESIGN-<topic>.md`, given `Parent: ./DESIGN.md`, and enumerated in the main header. The rename is part of the classification, not a separate cosmetic step: the naming convention is how a reader recognizes the document's role at a glance.

## Header Field Set

Every document header uses fields drawn from one fixed vocabulary. Field names are English, always, and a document uses only the fields that apply to it — but it never invents a field name outside this set.

| Field | Applies to | Meaning |
|---|---|---|
| `Status` | every document | lifecycle status: `Active`, `Draft`, `Target Shape`, `Proposed`, `Planned`, `Completed` |
| `Updated` | every document | last update date, `YYYY-MM-DD`, refreshed on every edit |
| `Parent Architecture` | project DESIGN, sub-DESIGN | the architecture document this one follows; `N/A` at the top of a product |
| `Parent Product` | project DESIGN, sub-DESIGN | the product PRD this one follows; `N/A` when none |
| `Parent` | sub-document (PRD / DESIGN / Phase) | the direct parent document in its own tree, e.g. `./DESIGN.md` |
| `Product Intent` | product DESIGN | the PRD this DESIGN follows |
| `Sibling DESIGNs` | product DESIGN | same-level DESIGNs whose contracts this one depends on |
| `Sub-DESIGNs` | main DESIGN | exact enumeration of every `DESIGN-<topic>.md` under it |
| `Sub-PRDs` | main PRD | exact enumeration of every `PRD-<topic>.md` under it |
| `Companion Documents` | main DESIGN / PRD | companion truth sources (BRANDING, API-CONTRACT) |
| `Design Source` | GAPS | the design document this gap tracker measures against |
| `Product PRD` | Phase | the PRD this Phase follows |
| `Product DESIGN` | Phase | the DESIGN contract this Phase follows |
| `Phase ID` | Phase | the phase identifier |
| `Product` | Phase | the product this phase belongs to |
| `Scope` | any document | one line narrowing what the document covers, when the title alone is ambiguous |
| `Companion` | GAPS | one line describing what the document tracks |

Two rules follow from this table:

- A document does not use a field that does not apply to it. A Phase document has no `Sub-DESIGNs`; a GAPS document has no `Parent Product`.
- A document does not invent a field. If a fact does not fit the vocabulary, it belongs in the body, not in the header.

`Parent` and `Parent Architecture` are separate obligations and may both appear: `Parent` points at the immediate document in the current tree (`./DESIGN.md`), `Parent Architecture` points at the product-level architecture above the whole project. They are never merged into one line.

## Metadata Field Semantics

Header metadata fields have fixed meanings:

| Field | Where | Meaning |
|---|---|---|
| `Status` | all | document lifecycle status (Active / Draft / Target Shape) |
| `Updated` | all | last update date, YYYY-MM-DD, refreshed on every edit |
| `Parent` | sub-documents | the direct parent document, `./DESIGN.md` for project sub-docs |
| `Parent Architecture` | sub-documents | product-level architecture document this doc must follow, when it exists |
| `Sub-DESIGNs` | main documents | exact enumeration of all `DESIGN-<topic>.md` under it |
| `Companion Documents` | main documents | companion truth-source documents (BRANDING, API-CONTRACT) |
| `Reference Documents` | end section | reference-only material, never in the header |

A sub-document header uses `Parent` for its project parent, not `Parent Architecture`. `Parent Architecture` is reserved for product-level documents above the project DESIGN. When both exist, they are separate lines with distinct targets.

## Mandatory Quality Gate

Every document-set update ends with an automated scan that must pass before the work is reported complete:

1. Enumerate `DESIGN-*.md` on disk and diff against the main header's `Sub-DESIGNs` — bidirectional, exact match.
2. Verify every sub-document header has `Parent: ./DESIGN.md`.
3. Scan for absolute paths (`file:///`, `/Users/...`) — zero tolerance.
4. Verify relative links resolve to existing files.
5. Confirm the end section (`Reference Documents`) contains no sub-DESIGNs and no header documents.
6. Scan for process-state vocabulary (已废弃, 已放弃, 迁移, 不再执行, 历史机制, deprecated, legacy, moved from).
7. Confirm every touched document has a refreshed `Updated` date.
8. For process documents (`GAPS.md`): confirm the header uses `Design Source` rather than a lineage field, and that header and end links are disjoint.

Run `scripts/verify-docset.py <docs-dir>` where available; otherwise run the equivalent grep checks by hand. The scan result is part of the completion report.

## Document-Set Consistency on Every Update

Updating one document is never isolated. A change to any document can invalidate claims in its parents, children, or siblings. Before finalizing any update:

1. Identify the affected set: parents (what this document follows), children (sub-documents), and siblings (documents sharing the same parent or describing the same phase/project).
2. Check each affected document for stale claims that contradict the change; revise or remove them when evidence is clear.
3. Align the bidirectional index and header links.
4. Align Phase Goals with the DESIGN Evolution Roadmap; align DESIGN architecture with the PRD vision; align README module/command lists with DESIGN and actual code.

The completion response must state which related documents were checked, which were aligned, and which still need a follow-up update.

## Change Flow Per Document Type

| Document changed | Must check |
|---|---|
| PRD | DESIGN (product + project), Phase documents, sub-PRDs |
| Main DESIGN | Sub-DESIGNs, product PRD, Phase documents |
| Sub-DESIGN | Main DESIGN chapter that decomposed into it, PRD, Phase |
| Phase / Roadmap | PRD, product DESIGN, project DESIGNs, sub-DESIGNs |
| README | Project DESIGN, AGENTS.md, actual code |
| AGENTS.md | Project DESIGN, PRD, README, actual code |
