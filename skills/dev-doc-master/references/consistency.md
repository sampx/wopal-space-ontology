# Document-Set Consistency — Universal Rules

These rules apply to every document in the product and project documentation set: PRDs, Product DESIGNs, and Present-State Project/Module DESIGNs, along with their boundaries against Proposals and `AGENTS.md`. They keep every fact single-owned, verifiable, low-conflict, and readable at low maintenance cost.

## No Chapter Numbering

Headings express structure through Markdown heading levels, not numbers. Write `## Capability Scope`, never `## 1. Capability Scope`. Chapter numbers force renumbering on every edit; plain heading levels survive structural changes.

## Present-State Accuracy (Project/Sub-DESIGN) and Forbidden Process Narration

**Project and module DESIGNs are present-state documents**: they describe only shipped, verifiable capabilities, interface contracts, active business rules, and failure boundaries actually running in code. Unimplemented proposals, planned APIs, and future goals belong in **Proposals**, never disguised as live behavior inside a project DESIGN.

**Product PRDs and Product DESIGNs** carry product intent, system layering, and capability maps, where directional goals are permitted while concrete paths and component claims must match repository reality.

All design documents **forbid process-state narration**: no `deprecated`, `legacy`, `moved from X`, `old path`, `migration`, `no longer`, `已废弃`, `已放弃`, `不再执行`, or `历史机制`. When ownership lives elsewhere, state current ownership directly without migration history.

## Writing Style

Accurate facts are half the job; human clarity is the other half. Apply these rules to every sentence in the set.

### Natural Language

Write like an engineer clearly explaining the system to a colleague taking it over. Read sentences aloud — if they sound template-assembled or robotic, rewrite them using plain verbs and concrete nouns.

### One Idea Per Sentence

Keep sentences focused on one primary claim. Split compound sentences that bury contract conditions or caveats.

### Affirmative and Ownership Clarity Over Vague Exclusion

State what a component does, owns, and delivers before stating exceptions. Phrase boundaries by naming both sides' owners (for example, `"X handles request routing; Y owns session persistence"`) rather than vague lists of absences. However, always state mandatory negative guards (`must not`), preconditions, and complete failure consequences explicitly so affirmative phrasing never hides failure guarantees.

## Relative Links Only

All links are relative to the repository root or the document directory (such as `./DESIGN-auth.md` or `../proposals/implemented/architecture/2026-11-20-oauth.md`). Absolute paths (`/Users/...`, `/Volumes/...`, `file:///...`) are forbidden so committed docs remain valid across machines.

## Header = Mandatory, End = Reference

Every document separates two link zones with distinct obligations:

- **Header** (metadata block below the title): carries only **mandatory** binding dependencies — parent or constraining sibling documents (such as PRD `Related DESIGN`, sub-DESIGN `Parent: ./DESIGN.md`, project DESIGN `Parent Architecture` / `Parent Product`, or product DESIGN `Sibling DESIGNs`).
- **End** (`## Reference Documents`): carries **reference-only** material that informs without binding.

A document never appears in both the header and `## Reference Documents`.

### The Obligation Test

When placement is unclear, ask whether a reader must follow that document to evaluate this one:

- **Must follow it** → Header (cross-repo paths or different naming do not weaken binding obligation).
- **Would benefit from background** → `## Reference Documents`.

## Language

Section headings and header field names stay **English** in every document regardless of body language (`## Module Architecture`, `> **Status**:`). Tooling matches these tokens literally and a shared heading vocabulary keeps documents comparable across projects.

Body text and header field explanations follow the user's preferred language.

## Anti-Conflict Architecture and Single Ownership

Multi-agent parallel execution collides on centralized indexes and shared monolith docs. Prevent conflicts structurally with five rules:

1. **One owner per fact**: Explain each contract once in its owning document; never copy-paste blocks across main DESIGN, sub-DESIGN, Proposal, and `AGENTS.md`.
2. **Thin main `DESIGN.md` map + default per-module sub-DESIGNs**: Multi-module projects keep main `DESIGN.md` thin (positioning, capability overview, core cross-module flows, and `## Module Architecture` map) and split module internals, contracts, active business rules, and failure bounds into `DESIGN-<module>.md` by default (without waiting for 500 lines). Only tightly coupled small single-module projects remain a single `DESIGN.md`.
3. **Retire `Sub-DESIGNs` header enumeration from all main DESIGNs**: Main `DESIGN.md` headers (for both Product and Project DESIGNs) do not enumerate `DESIGN-*.md` files; readers discover them by filename (`DESIGN-*.md`) and body links/maps while each sub-document links back via `Parent: ./DESIGN.md`. Parallel edits to distinct sub-documents never contend on the main header.
4. **Single-module isolation and write-set discipline**: Routine single-module changes and bug fixes do not touch main `DESIGN.md`. During parallel work, edit only sub-DESIGNs inside your authorized write set; **report out-of-scope drift to the coordinator and never cross write-set boundaries to edit shared docs**.
5. **Never copy-paste volatile code inventories**: Never transcribe source file trees, full CLI option tables, or exhaustive API field lists; describe contract boundaries and link to source files.

## Companion Documents vs Sub-DESIGNs

Classify supporting documents by **architectural role**, not by initial filename:

- **Sub-DESIGNs** (`DESIGN-<module>.md` or `DESIGN-<topic>.md`): documents decomposing an independent module or architectural concern of the main DESIGN. They carry `Parent: ./DESIGN.md`, are linked from the main document's map or section, and never appear in `## Reference Documents`.
- **Companion documents** (such as `BRANDING.md` or `API-CONTRACT.md`): cross-cutting single-source-of-truth references that are not module decompositions. Keep their filenames and declare them in the main header's `Companion Documents` field or relationship table.

If an ad-hoc document (such as `AUTH-PROTOCOL.md`) actually owns a module or architectural subsystem's contract, rename it to `DESIGN-<module>.md`, add `Parent: ./DESIGN.md`, and link it from the main module map.

## Document Lifecycle: Draft and Active

| Status | Meaning | Notes |
|---|---|---|
| `Draft` | Draft | Newly authored or incomplete doc awaiting verification and review |
| `Proposed` | Proposed | Drafted and awaiting confirmation before taking effect |
| `Active` | Active | Verified current contract in effect (normal state for present-state DESIGNs) |

Design documents have no `Completed` status: implementation status lives in Proposals and optional Plans. Present-state DESIGNs update in place as the system evolves and stay `Active`.

## Header Field Set

Header field names come from this fixed English vocabulary (never invent ad-hoc fields):

| Field | Applies to | Meaning |
|---|---|---|
| `Status` | every document | Lifecycle state: `Draft`, `Proposed`, `Active` |
| `Updated` | every document | Last verified edit date, `YYYY-MM-DD`, refreshed on edit |
| `Parent Architecture` | project DESIGN, sub-DESIGN | Product DESIGN this follows; `N/A` for standalone projects |
| `Parent Product` | project DESIGN, sub-DESIGN | Product PRD this follows; `N/A` when none |
| `Parent` | sub-document (sub-PRD / sub-DESIGN) | Direct parent in the same tree, e.g. `./DESIGN.md` |
| `Product Intent` | product DESIGN | PRD followed by the product DESIGN |
| `Sibling DESIGNs` | product DESIGN | Core subsystem project DESIGNs constraining the product architecture |
| `Sub-DESIGNs` | Legacy compatibility | Retained in vocabulary solely to tolerate untouched legacy docs without unknown-field errors; omitted from all Product and Project main DESIGN headers |
| `Sub-PRDs` | main PRD | Enumeration of `PRD-<topic>.md` files when split |
| `Companion Documents` | main DESIGN / PRD | Cross-cutting companion truth sources (`BRANDING.md`, `API-CONTRACT.md`) |
| `Scope` | any document | One line narrowing scope when the title alone is ambiguous |

Rules:

- Never include fields inapplicable to the document type.
- Keep `Parent` (`./DESIGN.md`) and `Parent Architecture` on separate lines.

## Mandatory Quality Gate

Complete both semantic review and deterministic checks before marking work done:

1. **Semantic Review (required)**: Apply clarity checks, the **5-Point Required Coverage Checklist**, and the **Slop Checklist** in `references/design-project-guide.md` across all docs; apply **"already shipped and code/run-verified"** (Newcomer present-state & live Evidence Review) specifically to **Project and Module Present-State DESIGNs**, keeping Product PRDs and Product DESIGNs (including Product Sub-DESIGNs) free to plan ahead of implementation.
2. **Deterministic Gate (required)**: Run `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md` (add `--check-sync [--base <git-ref>]` during code+doc delivery; or `--main PRD.md` for PRDs) and verify:
   - Sub-documents (`DESIGN-*.md`) discovered on disk each carry `Parent: ./DESIGN.md` (`Sub-DESIGNs` header enumeration is retired; untouched legacy docs carrying that field remain tolerated) and are linked from the main document body outside `Reference Documents` (zero orphan sub-DESIGNs)
   - Zero absolute paths (`/Users/...`, `/Volumes/...`, `file:///...`)
   - Relative Markdown links and header `./` or `../` backticked paths resolve to existing files
   - `## Reference Documents` does not repeat header links or local sub-DESIGNs
   - Zero unreplaced template placeholders or empty table skeleton rows
   - Non-empty `##` sections and mandatory `## Business Rules and Failure Boundaries` on Project main and Active Module DESIGNs
   - Zero process-state forbidden terms (`deprecated`, `moved from`, `no longer`, `已废弃`, `已放弃`, `不再执行`, `历史机制`, etc.), valid `Updated` date, allowed English header field names, and valid `Status` (`Draft` / `Proposed` / `Active`)
   - Optional `--check-sync`: maps touched non-test code paths via `Source Carrier` in `## Module Architecture` and requires synchronized updates in owning `DESIGN-<module>.md` unless `--pure-refactor "<reason>"` is explicitly declared for reviewer inspection

## Document-Set Consistency and Change Flow

Check affected documents when editing, strictly respecting parallel write-set boundaries:

| Change Made | Check for Alignment | Boundary Note |
|---|---|---|
| PRD | Product DESIGN, affected project DESIGN boundaries | Unbuilt capabilities go to Proposals, not present-state DESIGN |
| Product DESIGN | Affected subsystem present-state DESIGNs (drift check or Proposal trigger) | Preserve product architecture and capability-map conventions |
| Code / Feature / Bug Fix | Affected `DESIGN-<module>.md` (+ thin main `DESIGN.md` only if boundaries change) + Proposal | Pure internal refactor skips DESIGN; report out-of-scope drift to coordinator |
| Project main `DESIGN.md` | Affected `DESIGN-<module>.md`, parent architecture boundaries | Keep main doc a thin map; push details to sub-DESIGNs |
| Module `DESIGN-<module>.md` | Corresponding row in main `DESIGN.md` module map | Update main map only if module ownership/existence changed |
| `AGENTS.md` | Owning project/module DESIGN and actual build/test commands | Long-term operational rule edits go through `space-master` |

## Document Roles: What Belongs Where

Every fact has one authoritative home:

| Artifact | Owns | Does Not Own |
|---|---|---|
| **PRD** | Product intent, user problem, value proposition, product scope | Internal architecture, module layout, tech choices, test scripts |
| **Proposal** (`proposals/{proposed,implemented,rejected,archived}/{class}/...`) | Design rationale, alternatives considered, unbuilt proposal specs (`proposed/`), shipped decision & consequences (`implemented/`), guardrail rejections (`rejected/`) | Current system manual; task-by-task execution tracking |
| **Product DESIGN** | System layering, subsystem boundaries, runtime model, E2E flows, capability roadmap | Per-project internals, delivery tracking |
| **Project / Sub DESIGN** (present-state) | **Shipped, verified** capabilities (user-first), module collaboration, contracts & state ownership, **active business rules**, complete failure bounds | Unbuilt plans, reasoning logs, hand-copied source trees / parameter tables |
| **Plan** (optional, complex work) | Complex multi-module/multi-project task breakdown, parallel write sets, orchestration | Architecture approval (Proposal) or permanent system manual (DESIGN) |
| **AGENTS.md** | Agent commands, gates, conventions, verification rules (via `space-master`) | Architecture narrative, business-rule prose, proposal deliberation |

**Legacy compatibility note**: Projects no longer create standalone `BUSINESS_RULES.md` (nor `Phase` or `GAPS.md` trackers); active business rules and failure bounds belong inside the owning main/sub DESIGN, while rule changes under consideration belong in Proposals. Existing `BUSINESS_RULES.md` files stay read-only historical references and receive no new rules or updates.

**Split the two faces of operational mechanisms cleanly**: *What* a deploy/build pipeline is (topology, state locations, rollback semantics) belongs in DESIGN; *what commands/gates* an agent must run belong in `AGENTS.md`. Cross-link instead of copying.

## Scope Discipline for an Alignment Pass

Fix rule-governed defects without inventing product policy:

- **Fix rule-governed issues**: header field vocabulary, relative links, absolute path removal, process-state wording, thinning oversized main maps, removing AI slop and unverified claims.
- **Never invent unsettled product decisions**: record ambiguity for the user/coordinator rather than guessing paradigms.
- **Verify from source and execution first**: read code and run checks to resolve factual ambiguity before asking questions.
- **Report out-of-scope drift instead of crossing write sets**: fix files inside your scope and surface out-of-scope drift to the coordinator.
