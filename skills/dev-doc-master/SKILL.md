---
name: dev-doc-master
description: Authoring and maintenance of development documentation — product PRD, product/project DESIGN (including sub-DESIGN splitting), phase/roadmap documents, and project README. Use whenever the user asks to create or update a PRD, DESIGN, design document, phase document, roadmap, or README; when a main document needs splitting into topic sub-documents; or when document-set consistency (header vs reference links, bidirectional sub-document index, cross-document alignment) needs enforcement. Covers document naming rules, mandatory header links vs reference-only end links, no chapter numbering, relative-path-only links, and whole-document-set consistency on every update.
---

# dev-doc-master — Development Documentation Master

Authoring and maintenance workflow for the product/project documentation set: PRD, DESIGN (main + sub), Phase/Roadmap, and README. This skill owns the rules and templates; the `/cupdate-*` commands are thin entries that route here.

## When to Use

- Create or update a product PRD, product DESIGN, project DESIGN, Phase document, roadmap, or project README.
- Split an oversized main document into topic sub-documents.
- Align a document set after a change (PRD ↔ DESIGN ↔ Phase ↔ README ↔ AGENTS.md).

## Document Set and Routing

| Document | Command | Reference | Template |
|---|---|---|---|
| Product PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| Product / Project DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` / `templates/design-project.md` |
| Phase / Roadmap | `/cupdate-roadmap` | `references/phase.md` | `templates/phase.md` |
| Project README | `/cupdate-readme` | `references/readme.md` | (inline in `references/readme.md`) |
| AGENTS.md | `/cupdate-agent-rules` | space-master skill | space-master skill templates |

Load the matching reference file before writing. All references share the common rules in `references/consistency.md` — read it once per session.

## Universal Rules (applied to every document in the set)

Read `references/consistency.md` for the full text. In short:

- **No chapter numbering**: headings use Markdown heading levels only. No `## 1.` prefixes.
- **Relative links only**: all document links are relative to the repository root or the document's directory. Absolute paths are forbidden (docs are committed to git and shared).
- **Header = mandatory, end = reference**: header links carry only the documents this document must follow (parent, siblings). End-of-document links (Related Documents / References) carry reference-only auxiliary material. A document is never listed twice.
- **Main document lists sub-documents**: a suffix-free main document header enumerates its `DESIGN-<topic>.md` / `PRD-<topic>.md` sub-documents; each sub-document header points back via `上级: ./DESIGN.md`. Bidirectional index must match actual files.
- **Document-set consistency**: updating one document is never isolated. Review the whole set (PRD, DESIGN main/sub, Phase, README, AGENTS.md) and align every document affected by the change. Report the affected set in the completion response.

## Naming Conventions

- Main PRD: `PRD.md` (no suffix). Main DESIGN: `DESIGN.md` (no suffix).
- Sub-documents: `PRD-<topic>.md`, `DESIGN-<topic>.md` (kebab-case), same directory as main. No suffix = main, suffixed = sub.
- Split threshold: roughly 500 lines per main document, or 150 lines per chapter.
- See `references/consistency.md` and the design reference for the full splitting rules.

## Workflow

1. **Route**: identify the document type from the command or user request; load the matching reference.
2. **Gather context**: read the existing target document, its parent/sibling documents, and the actual code (for updates). Never invent facts.
3. **Discuss / plan**: guide discussion for new documents, or present the update plan for existing ones. Obtain explicit user confirmation before writing.
4. **Write**: produce the document from the template, applying the universal rules.
5. **Verify**: run the quality checklist in the reference; check document-set consistency and the bidirectional index.
6. **Report**: file path, change summary, and the whole affected document set (checked / aligned / needs follow-up).

## Document-Set Consistency (always)

Updating a PRD affects DESIGN and Phase. Updating a main DESIGN affects sub-DESIGNs. Updating a Phase affects PRD and DESIGNs. Updating README affects DESIGN and AGENTS.md. The completion response must state which related documents were checked, aligned, or still need a follow-up update.
