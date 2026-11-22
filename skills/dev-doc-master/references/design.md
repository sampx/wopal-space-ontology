# DESIGN Reference — Product & Project Present-State DESIGN Authoring

Create or update a Product DESIGN (`templates/design-product.md`) or a Project/Module Present-State DESIGN (`templates/design-project.md`, `templates/design-sub.md`). When authoring or updating any project or module present-state DESIGN, always read [`design-project-guide.md`](design-project-guide.md) as well for anti-conflict splitting, fact-checking, dual-scenario sync, and semantic review rules.

## Positioning of the Two DESIGN Tiers

| Tier | Role | Templates | References |
|---|---|---|---|
| **Product DESIGN** (including Product Sub-DESIGNs) | Cross-project system layering, subsystem boundaries, runtime model, E2E flows, capability roadmap (**allowed and expected to plan ahead of project implementation**) | `templates/design-product.md`, `templates/design-sub.md` (Product Sub-DESIGN mode) | This file (product sections) + `consistency.md` |
| **Project / Module Present-State DESIGN** | **Shipped, verified manual of the current system**: tells end users and newcomers what the system delivers now, architecture & contracts, active business rules, and complete failure bounds | `templates/design-project.md`, `templates/design-sub.md` (Project Module mode) | This file + [`design-project-guide.md`](design-project-guide.md) |

## Two Workflows

| Flow | Context | Evolution & Sync Loop |
|---|---|---|
| **Standard (multi-project product)** | PRD → Product DESIGN (layering + `Sibling DESIGNs` + capability map) | Substantial changes go through Proposals (`proposals/proposed/<class>/...`) and, upon delivery, update affected project/module present-state DESIGNs and move the Proposal to `implemented/<class>/` |
| **Simplified (standalone project)** | Standalone project without product PRD/DESIGN (`Parent Product: N/A`, `Parent Architecture: N/A`) | Maintained via project main/sub present-state DESIGNs; substantial changes go through project `proposals/proposed/<class>/...` and deliver code + tests + module DESIGN + Proposal move to `implemented/`; small fixes follow dual-scenario sync |

> Note: Project workflows no longer create or update `Phase` documents or `GAPS.md`. Unimplemented capability proposals belong in Proposals.

## Discussion Focus

- **Product DESIGN**: system layering and subsystem boundaries, runtime model, end-to-end flows, capability roadmap (capability dimensions and maturity steps — direction, not schedule).
- **Project / Module Present-State DESIGN**: user-first delivered capabilities and key limits, thin main map, module contracts, tech choices, external contracts (triggers, sequence, side effects, failure bounds), active business rules, and data/state ownership.
- DESIGNs never contain task checklists, live implementation status flags, or meeting transcripts.

## Product DESIGN: Capability Roadmap (Unchanged)

The product DESIGN `Capability Roadmap` is a directional capability map, never a timeline. Rows are capability dimensions and columns are maturity steps with owning projects, describing architectural direction rather than delivery dates. Update rows when capability dimensions evolve; route concrete implementation decisions through Proposals.

## Document Naming and Splitting

- Main Product DESIGN has no suffix: `docs/products/<product-name>/DESIGN.md`.
- Main Project Present-State DESIGN has no suffix (in the project's docs directory, e.g. `docs/DESIGN.md`).
- Sub-DESIGNs use `DESIGN-<module>.md` (kebab-case) in the same directory as the main DESIGN.
- **Default per-module splitting for multi-module projects (anti-conflict)**: Whenever a project has distinct modules or independent domains, **keep main `DESIGN.md` thin as a conceptual and module map and push module contracts into `DESIGN-<module>.md` by default** (do not wait for a 500-line threshold). Only small, tightly coupled single-module projects stay a single `DESIGN.md`. Conversely, keep tightly coupled parts of one contract together rather than fragmenting them mechanically (criteria in `design-project-guide.md`).
- **Match `templates/design-sub.md` mode to its parent tier**: Product Sub-DESIGNs (decomposing a product main `DESIGN.md`) are allowed and expected to plan target product architecture and future capabilities ahead of implementation; Project Module Sub-DESIGNs (decomposing a project main `DESIGN.md`) strictly follow present-state, code-verified rules.
- **Sub-documents link up; main DESIGNs omit `Sub-DESIGNs` header enumeration**: Every sub-DESIGN carries `> **Parent**: ./DESIGN.md`. **All main `DESIGN.md` headers (Product and Project alike) omit `Sub-DESIGNs` lists** — `DESIGN-*.md` filenames clearly distinguish sub-docs on disk while main docs link as needed from body sections or module maps, eliminating header collisions and pointless index checks (`Sub-DESIGNs` stays in the header vocabulary only to tolerate untouched legacy files).

## Header Rules

Header links carry binding dependencies only:

- **Product DESIGN**: `Product Intent` (followed PRD) + `Sibling DESIGNs` (subsystem project DESIGNs) + `Companion Documents` when present. **Do not enumerate `Sub-DESIGNs`.**
- **Project Present-State DESIGN**: `Parent Architecture` (`N/A` if standalone) + `Parent Product` (`N/A` if standalone) + `Companion Documents` when present. **Do not enumerate `Sub-DESIGNs`.**
- **Sub-DESIGN (Product Sub-DESIGN or Project Module Sub-DESIGN)**: `Parent: ./DESIGN.md` + `Parent Architecture` + `Parent Product`.

## Product DESIGN and Project DESIGNs

A product DESIGN coordinates core subsystems whose internals live in their respective project DESIGNs:

- The product DESIGN's `Core Projects` section assigns each subsystem's role, boundary, and cross-project interaction contract, linking to each project DESIGN.
- List those constraining project DESIGNs in the product DESIGN header's `Sibling DESIGNs`, even across repositories — binding contracts belong in the header, not `Reference Documents`.

## Sibling DESIGNs vs Reference Documents

Obligation determines placement, not path proximity:

- **Sibling DESIGNs** (header): upstream/downstream systems whose contracts bind this design.
- **Reference Documents** (end section): informative background (research notes, external specs, historical snapshots) that does not bind this document.

Never list the same document in both places.

## Companion Documents in the Header

Truth sources like `BRANDING.md` or `API-CONTRACT.md` that serve cross-cutting concerns keep their descriptive names and are declared in `Companion Documents`. Supporting files that actually detail an architectural module or subsystem of the main DESIGN are renamed to `DESIGN-<module>.md`, given `Parent: ./DESIGN.md`, and linked from the main body map (`consistency.md` details classification by content).

## Metadata Field Semantics

- Required on every document: `Status` (`Draft` / `Proposed` / `Active`) and `Updated` (`YYYY-MM-DD`, refreshed on every edit).
- Shipped, verified project/module present-state DESIGNs carry `Status: Active`; `Draft` / `Proposed` applies only to newly drafted docs not yet active. Design docs have no `Completed` status.
- Sub-documents keep `Parent: ./DESIGN.md` and `Parent Architecture` on separate lines.

## Update Mode and Sync Flow

1. Preserve existing paths and English headings.
2. Verify actual code, config defaults, and live test/command outputs first (**see `design-project-guide.md`**).
3. Refresh the `Updated` date.
4. Update affected sections per the dual-scenario sync rules (skip DESIGN edits on pure internal refactoring; single-module changes touch only `DESIGN-<module>.md`; report out-of-scope drift to the coordinator during parallel work).
5. Ensure active business rules and complete failure boundaries are present; mark any unverifiable claim explicitly as untested.

## Quality Checklist

### Universal and Product DESIGN Checks

- [ ] Correct template chosen (`design-product.md`, `design-project.md`, or `design-sub.md`)
- [ ] English unnumbered headings and English header field names; body prose and field explanations match user language preference
- [ ] Current `Updated` date; accurate `Status` (`Active` for live present-state DESIGNs)
- [ ] Header = mandatory links only; `Reference Documents` = reference-only; zero overlap; all links relative and valid
- [ ] Zero process-state terms (`deprecated`, `legacy`, `moved from`, `已废弃`, `历史机制`, etc.)
- [ ] Product DESIGN (when applicable): grounded in PRD; `Capability Roadmap` stays directional rather than dated schedules; core subsystems listed in `Sibling DESIGNs`

### Project & Module Present-State DESIGN Checks (full rubric in `design-project-guide.md`)

- [ ] **Present-state truth & fact-checking**: All claims match shipped code; no unbuilt plans presented as live; commands, defaults, and limits verified against code/execution, with untested items explicitly marked
- [ ] **Anti-conflict & universal structure**: Main `DESIGN.md` stays a thin map with inter-module collaboration flows, `Source Carrier` path prefixes, and no `Sub-DESIGNs` header enumeration; multi-module details sit in `DESIGN-<module>.md` using fixed entry/exit anchors + flexible `1..N` domain-concept `##` sections (`Parent: ./DESIGN.md`, zero orphan sub-DESIGNs); zero hand-copied source trees, full CLI option tables, or full API field inventories
- [ ] **User-first & 5-Point Required Coverage**: Understandable without reading code; critical flows cover actor/trigger, component sequence, permissions `must`/`may`/`must not`, side effects/state ownership, and complete failure outcomes & recovery; `## Business Rules and Failure Boundaries` present; `Key Decisions` keeps shipped conclusions + Proposal links only
- [ ] **Slop Checklist passes**: Zero CoT/session leakage, implementation status labels, rule bloat, bold abuse, or cross-level duplication

## Mandatory Quality Gate (before reporting complete)

Complete the semantic checklist above, then run `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md` (add `--check-sync [--base <git-ref>]` during code+doc delivery; must exit 0 before reporting done). The script verifies on disk:

1. Every `DESIGN-*.md` sub-document discovered on disk carries a `Parent: ./DESIGN.md` link (`Sub-DESIGNs` header enumeration is retired) and is linked from the main document body outside `Reference Documents` (zero orphan sub-DESIGNs)
2. Zero absolute paths (`file:///`, `/Users/...`, `/Volumes/...`)
3. All relative links resolve to existing files
4. `Reference Documents` repeats no header links or local sub-DESIGNs
5. Zero unreplaced template placeholders or empty table skeleton rows
6. Non-empty `##` sections and mandatory `## Business Rules and Failure Boundaries` on Project main and Active Module DESIGNs
7. Zero process-state forbidden terms, valid `Updated` date, allowed English header field names, and valid `Status`
8. Optional `--check-sync`: changed non-test code files under `Source Carrier` paths have synchronized updates in their owning `DESIGN-<module>.md` (or declared `--pure-refactor "<reason>"` for independent review)

## Response After Completion

Respond in the user's preferred language with: touched file paths; change summary; **verified evidence vs explicitly marked untested items**; semantic review and `verify-docset.py` results (`PASS`/`FAIL`); any out-of-scope drift notices surfaced during parallel execution; and the appropriate next step (for Product DESIGN: align affected subsystem present-state DESIGNs or open Proposals as needed; for Project DESIGN: run `/cupdate-agent-rules` via `space-master` if long-term operational constraints changed, or proceed with commit/delivery).

## What a DESIGN Document Owns

| Belongs in DESIGN | Belongs elsewhere |
|---|---|
| System/module positioning, capability bounds, user-observable behavior | Unimplemented decisions, alternatives, approval → Proposal (`proposals/proposed/<class>/...`) |
| Thin main map, module ownership, core interactions | Shipped decision history & consequences → Proposal (`proposals/implemented/<class>/...`) |
| Verified interface contracts, state ownership, active business rules, failure bounds | Complex task breakdown, write-set coordination → Plan (optional, via `dev-flow`) |
| Concise shipped decision summaries (with Proposal links) & tech rationale | Agent commands, gates, test workflows → `AGENTS.md` / `rules/testing.md` |
| Deployment mechanics (topology, state layout, rollback semantics) | Deploy runbooks and branch gates → `AGENTS.md` |

## Distinguishing Product Intent from Project Present-State Facts

- **Project / Module Present-State DESIGN**: Records verified code and runtime facts only. Unbuilt modules or planned flags never appear as live capabilities; gated surfaces must state their feature/module switch condition rather than looking unconditionally active; external symlinks or submodules must name their real backing location.
- **Product DESIGN**: Directional intent belongs in `Capability Roadmap` and architectural vision sections, while concrete repository references must match actual code. Report directional divergences rather than silently inventing product decisions.
