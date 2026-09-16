---
name: dev-doc-master
description: >
  Author and maintain the product/project documentation set — PRD, DESIGN
  (main and sub), Phase/Roadmap, README, BUSINESS_RULES, and GAPS — and
  keep the set consistent with the repository. Use when the user asks to
  create, update, split, or align any of these documents, or when
  document-set consistency needs checking (header vs reference links,
  bidirectional sub-document index, cross-document alignment), for example
  "write a PRD", "update the design doc", "split this design", "create a
  phase doc", "update the README", "business rules", or any /cupdate-*
  request. Do not use for writing development Plans (use dev-flow) or for
  reviewing implementation code (use df-implement-review).
---

# dev-doc-master — Development Documentation Master

Authoring and maintenance workflow for the product/project documentation set: PRD, DESIGN (main + sub), Phase/Roadmap, README, and BUSINESS_RULES. This skill owns the rules and templates; the `/cupdate-*` commands are thin entries that route here.

## When to Use

- Create or update a product PRD, product DESIGN, project DESIGN, Phase document, roadmap, project README, or project BUSINESS_RULES.
- Split an oversized main document into topic sub-documents.
- Align a document set after a change (PRD ↔ DESIGN ↔ Phase ↔ README ↔ BUSINESS_RULES ↔ AGENTS.md).
- Record or update project gaps between design target state and implementation (`GAPS.md`).

## Document Set and Routing

| Document | Command | Reference | Template |
|---|---|---|---|
| Product PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| Product / Project DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` / `templates/design-project.md` |
| Sub-DESIGN | (via `/cupdate-design`) | `references/design.md` | `templates/design-sub.md` |
| Phase | `/cupdate-roadmap` | `references/phase.md` | `templates/phase.md` |
| Project README | `/cupdate-readme` | `references/readme.md` | (inline in `references/readme.md`) |
| Project GAPS | (no command) | `references/gaps.md` | `templates/gaps.md` |
| Project BUSINESS_RULES | `/cupdate-br` | `references/business-rules.md` | `templates/business-rules.md` |
| AGENTS.md | `/cupdate-agent-rules` | space-master skill | space-master skill templates |

Load the matching reference file before writing. All references share the common rules in `references/consistency.md` — read it once per session.

## Universal Rules (applied to every document in the set)

Read `references/consistency.md` for the full text. In short:

- **No chapter numbering**: headings use Markdown heading levels only. No `## 1.` prefixes.
- **Relative links only**: all document links are relative to the repository root or the document's directory. Absolute paths are forbidden (docs are committed to git and shared).
- **Header = mandatory, end = reference**: header links carry only the documents this document must follow (parent, siblings). The end section carries reference-only material. A document is never listed twice — an entry in both zones makes the obligation unreadable.
- **Main document lists sub-documents**: a suffix-free main document header enumerates its `DESIGN-<topic>.md` / `PRD-<topic>.md` sub-documents; each sub-document header points back via `Parent: ./DESIGN.md`. Bidirectional index must match actual files.
- **Document-set consistency**: updating one document is never isolated. Review the whole set (PRD, DESIGN main/sub, Phase, README, AGENTS.md) and align every document affected by the change. Report the affected set in the completion response.
- **Target-state writing**: documents describe the target state only — what the system is, what exists, who owns it. Process-state descriptions are forbidden: no "deprecated", "legacy", "moved from X", "old path", or "migration" notes. When a capability is owned elsewhere, state the ownership, not the move.
- **Gap detail has one home**: gap detail lives in the project `GAPS.md`. A Phase document lists the gaps its scope closes by identifier, title, priority, and design pointer — it never restates Current / Target / Exit.
- **A gap is a design statement, an issue is a code defect**: a gap records an unimplemented design contract, a design change the code has not followed, or an experimental design area awaiting convergence. A satisfied contract with a bug is an issue, not a gap. Every gap belongs to exactly one project — work spanning projects is split so each half is closable on its own. Method: `references/gaps.md` (What Counts as a Gap).
- **A Phase document carries no capability-roadmap trace**: the Goal states the capability the phase delivers, in product language. Where each capability dimension stands is answered by the Capability Roadmap in the product DESIGN. A trace duplicated into the phase document costs maintenance and drifts from the map it copies.
- **Gaps are found by bounded enumeration**: when a design has been reworked, anchor the search on the pivot commit's design diff and verify each change theme against the implementation with `file:line` evidence. Reconcile findings against existing gaps' full `Exit` lists before minting a new identifier. Method: `references/gaps.md` (Gap Discovery).
- **Writing style**: natural language that reads like a human wrote it; one idea per sentence; affirmative over negative; ownership over exclusion. State what a component does and owns rather than listing what it does not do.

## Language

The skill's own references and templates are written in English, and section headings stay English in the produced documents. Two reasons: the quality-gate script matches headings literally, and a stable heading set keeps documents comparable across projects and languages.

Document body text follows the user's preferred language. When the user writes Chinese, the body is Chinese; when English, English.

Header **field names** stay English so the quality-gate script can parse them. Header **field values** follow the document language, so a reader gets a natural explanation rather than a bilingual mix:

```
> **Design Source**: `./DESIGN.md`（差距对照的设计真相源）
> **Companion**: 追踪本项目的目标态差距，逐项解决后关闭。
```

This split means a document's structure is language-independent — a reader or a script finds the same headings and fields everywhere — while its content reads naturally to its audience. Headings stay English for the same reason as field names: the gate script matches them literally, and a stable heading set keeps documents comparable across projects.

## Naming Conventions

- Main PRD: `PRD.md` (no suffix). Main DESIGN: `DESIGN.md` (no suffix).
- Sub-documents: `PRD-<topic>.md`, `DESIGN-<topic>.md` (kebab-case), same directory as main. No suffix = main, suffixed = sub.
- Split threshold: roughly 500 lines per main document, or 150 lines per chapter.
- A supporting document is classified by content, not by its current name. One that carries a main DESIGN concern is a sub-design and is renamed to match; one that is a cross-cutting truth source stays a companion. See `references/consistency.md` (Companion Documents vs Sub-DESIGNs) for the criteria.
- See `references/consistency.md` and the design reference for the full splitting rules.

## Workflow

1. **Route**: identify the document type from the command or user request; load the matching reference.
2. **Gather context**: read the existing target document, its parent/sibling documents, and the actual code (for updates). Never invent facts.
3. **Decide, don't ask**: resolve every question the rules or the repository can answer by reading. `references/consistency.md` defines which document carries which kind of fact; the code is the evidence for concrete facts. Discuss with the user only what genuinely requires their decision — a product intent that is not settled, a scope call, or a direction change. Present that decision, not a survey of the options you could have resolved yourself.
4. **Write**: produce the document from the template, applying the universal rules.
5. **Verify**: run the quality checklist in the reference, then run the **mandatory quality gate**: `scripts/verify-docset.py <docs-dir> --main DESIGN.md`. The script scans the actual filesystem for sub-design enumeration, parent links, absolute paths, broken links, end-section duplication, process-state vocabulary, and missing dates. It must exit 0 before the update is reported complete. Check document-set consistency and the bidirectional index.
6. **Report**: file path, change summary, quality-gate result (PASS/FAIL), and the whole affected document set (checked / aligned / needs follow-up).

## Document-Set Consistency (always)

Updating a PRD affects DESIGN and Phase. Updating a main DESIGN affects sub-DESIGNs. Updating a Phase affects PRD and DESIGNs. Updating README affects DESIGN and AGENTS.md. The completion response must state which related documents were checked, aligned, or still need a follow-up update.
