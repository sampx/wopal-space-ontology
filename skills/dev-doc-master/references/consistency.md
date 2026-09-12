# Document-Set Consistency — Universal Rules

These rules apply to every document in the product/project documentation set: PRD, DESIGN (main and sub), Phase, README, and AGENTS.md. They exist so the document set stays coherent, avoids duplicated or contradictory claims, and keeps the maintenance cost low.

## No Chapter Numbering

Headings express structure through Markdown heading levels, not numbers. Write `## Capability Scope`, never `## 1. Capability Scope`. Chapter numbers force renumbering on every insert, move, or deletion; heading levels survive structural edits. Applies to every generated or updated document.

## Relative Links Only

All document links are relative to the repository root or the document's directory. Absolute paths (e.g. `/Users/...`, `file:///...`) are forbidden because these documents are committed to git and shared across machines — an absolute path works only on the machine that wrote it. Use `./DESIGN.md`, `../DESIGN.md`, or `docs/products/<name>/DESIGN.md` style relative paths consistently within a document.

## Header = Mandatory, End = Reference

Every document has two link zones with distinct obligations:

- **Header** (metadata block after the title): carries only **mandatory** documents — the parent document and sibling documents that this document must follow. Examples: a PRD's `Related DESIGN`, a sub-DESIGN's `上级: ./DESIGN.md`, a Phase's `Product PRD` + `Product DESIGN`.
- **End** (Related Documents / References section): carries **reference-only** documents — research, business rules, project specs, auxiliary material that is informational, not binding.

A document is either a mandatory header link or a reference end link, never both. Never list a header document again in the end section, and never promote a reference document into the header as if it were binding.

## Main Document Lists Its Sub-Documents

A suffix-free main document is the single entry point to its document tree. Its header must enumerate every `DESIGN-<topic>.md` / `PRD-<topic>.md` sub-document under it (a `Sub-DESIGNs` / `Sub-PRDs` field). Each sub-document header points back via `上级: ./DESIGN.md` (or localized equivalent). This bidirectional index must match the actual files on disk — when a sub-document is added or removed, both sides are updated. Sub-documents listed in the header are structure declarations, not references, so they never appear in the end section.

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
