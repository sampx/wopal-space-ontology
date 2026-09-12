# Document-Set Consistency — Universal Rules

These rules apply to every document in the product/project documentation set: PRD, DESIGN (main and sub), Phase, README, and AGENTS.md. They exist so the document set stays coherent, avoids duplicated or contradictory claims, and keeps the maintenance cost low.

## No Chapter Numbering

Headings express structure through Markdown heading levels, not numbers. Write `## Capability Scope`, never `## 1. Capability Scope`. Chapter numbers force renumbering on every insert, move, or deletion; heading levels survive structural edits. Applies to every generated or updated document.

## Target-State Writing

Documents describe the target state only — what the system is, what exists, who owns it, what responsibility it carries. Process-state descriptions are forbidden: no "deprecated", "legacy", "moved from X", "old path", "migration", or "historical" notes. When a capability is owned elsewhere, state the ownership, not the move. A reader of a document learns the current structure and responsibilities, never the history of how it got there.

## Relative Links Only

All document links are relative to the repository root or the document's directory. Absolute paths (e.g. `/Users/...`, `file:///...`) are forbidden because these documents are committed to git and shared across machines — an absolute path works only on the machine that wrote it. Use `./DESIGN.md`, `../DESIGN.md`, or `docs/products/<name>/DESIGN.md` style relative paths consistently within a document.

## Header = Mandatory, End = Reference

Every document has two link zones with distinct obligations:

- **Header** (metadata block after the title): carries only **mandatory** documents — the parent document and sibling documents that this document must follow. Examples: a PRD's `Related DESIGN`, a sub-DESIGN's `上级: ./DESIGN.md`, a Phase's `Product PRD` + `Product DESIGN`.
- **End** (Related Documents / References section): carries **reference-only** documents — research, business rules, project specs, auxiliary material that is informational, not binding.

A document is either a mandatory header link or a reference end link, never both. Never list a header document again in the end section, and never promote a reference document into the header as if it were binding.

## Main Document Lists Its Sub-Documents

A suffix-free main document is the single entry point to its document tree. Its header must enumerate every `DESIGN-<topic>.md` / `PRD-<topic>.md` sub-document under it (a `Sub-DESIGNs` / `Sub-PRDs` field). Each sub-document header points back via `上级: ./DESIGN.md` (or localized equivalent). This bidirectional index must match the actual files on disk — when a sub-document is added or removed, both sides are updated. Sub-documents listed in the header are structure declarations, not references, so they never appear in the end section.

## Sub-DESIGN Enumeration Is a Filesystem Fact

The header's sub-document list is a filesystem fact, not a summary. Before writing the header, list every `DESIGN-<topic>.md` in the same directory with `ls`. The header must enumerate exactly those files — nothing more, nothing less. After writing, re-run the same listing and diff against the header. A header that misses a file breaks the bidirectional index; a header that lists a nonexistent file is a dead link. This check is part of the mandatory quality gate.

## Companion Documents vs Sub-DESIGNs

A documentation set contains two distinct kinds of supporting files:

- **Sub-DESIGNs** (`DESIGN-<topic>.md`): architecture documents that decompose a main DESIGN chapter. They follow the naming convention, carry a `上级` parent link, and are enumerated in the main header's `Sub-DESIGNs` field.
- **Companion documents** (e.g. `BRANDING.md`, `API-CONTRACT.md`): single-source-of-truth documents that belong to the set but are not architecture decompositions. They do not use the `DESIGN-<topic>.md` naming pattern, do not carry a `上级` link, and are declared in the main header's `Companion Documents` field or in the document-relationship table.

A companion document is never renamed to fit the `DESIGN-*.md` pattern, and never forced into the `Sub-DESIGNs` enumeration. The two categories are distinct and both are declared in the header.

## Metadata Field Semantics

Header metadata fields have fixed meanings:

| Field | Where | Meaning |
|---|---|---|
| `Status` | all | document lifecycle status (Active / Draft / Target Shape) |
| `Updated` | all | last update date, YYYY-MM-DD, refreshed on every edit |
| `Parent` (上级) | sub-documents | the direct parent document, `./DESIGN.md` for project sub-docs |
| `Parent Architecture` (上级架构) | sub-documents (optional) | product-level architecture document this doc must follow, when it exists |
| `Sub-DESIGNs` (子设计) | main documents | exact enumeration of all `DESIGN-<topic>.md` under it |
| `Companion Documents` (配套文档) | main documents (optional) | companion truth-source documents (BRANDING, API-CONTRACT) |
| `Related Documents` (相关文档) | end section | reference-only material, never in the header |

A sub-document header must use `Parent` (上级), not `Parent Architecture` (上级架构), for its project parent. `Parent Architecture` is reserved for product-level documents above the project DESIGN. When both exist, they are separate lines with distinct targets.

## Mandatory Quality Gate

Every document-set update ends with an automated scan that must pass before the work is reported complete:

1. Enumerate `DESIGN-*.md` on disk and diff against the main header's `Sub-DESIGNs` — bidirectional, exact match.
2. Verify every sub-document header has `上级: ./DESIGN.md` (or the localized equivalent).
3. Scan for absolute paths (`file:///`, `/Users/...`) — zero tolerance.
4. Verify relative links resolve to existing files.
5. Confirm the end section (`Related Documents`) contains no sub-DESIGNs and no header documents.
6. Scan for process-state vocabulary (已废弃, 已放弃, 迁移, 不再执行, 历史机制, deprecated, legacy, moved from).
7. Confirm every touched document has a refreshed `Updated` date.

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
