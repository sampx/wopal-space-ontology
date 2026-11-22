# <Project Name>

> **Status**: Active
> **Updated**: YYYY-MM-DD
> **Parent Architecture**: `<parent-design-path or N/A>` — the product architecture DESIGN this project follows
> **Parent Product**: `<parent-product-prd-path or N/A>` — the product PRD this project follows

Keep this main `DESIGN.md` thin as a conceptual overview and module map. When the project has multiple modules or distinct domains, split module details into `DESIGN-<module>.md` by default using `templates/design-sub.md` (with `Parent: ./DESIGN.md`), and link them from `## Module Architecture` below rather than adding a `Sub-DESIGNs` list in the header. Only small, tightly coupled single-module projects keep all contracts here.

---

## Project Role

What this project currently owns within the parent product (inherits the `Core Projects` boundary from `Parent Architecture`, or defines standalone scope), its user-facing purpose, and explicit ownership boundaries.

- Standard flow (`Parent Product` is not `N/A`): concise core positioning + boundary table (`Owned Here` vs `External / Sibling`)
- Simplified flow (`Parent Product: N/A`): standalone purpose, target audience, and explicit boundaries

## Capability Scope

Delivered, verifiable capabilities actually running in code today, written first for readers who have not read the source code (Layer 1 observable view).

- Summarize what the system currently enables, how users or callers invoke it, observable outcomes, and critical prerequisites/limits
- Record only shipped facts verified against code, tests, or live runs (explicitly mark any untested claim with its verification condition); unbuilt plans belong in `proposals/proposed/<class>/...`

## Key Decisions

Settled architecture decisions currently in effect — concise conclusion, rationale, and a relative Markdown link to the originating implemented/archived Proposal (`N/A` if predating proposals; do not copy full proposal deliberations here).

| Decision | Summary & Rationale | Proposal |
|---|---|---|
| `<decision>` | `<settled conclusion and concise rationale>` | [<yyyy-mm-dd-slug>](./proposals/implemented/<class>/<yyyy-mm-dd-slug>.md) |

## Module Architecture

Thin module map, inter-module collaboration overview, and entry points into module sub-DESIGNs. Never copy-paste full source trees here.

| Module | Responsibility | Source Carrier | Sub-DESIGN |
|---|---|---|---|
| | | `<path>` | `[DESIGN-<module>.md](./DESIGN-<module>.md)` |

- **Source Carrier mapping**: Record repo-relative or project-relative path prefixes (e.g., `src/auth/`) so `verify-docset.py --check-sync` can map code changes to their owning `DESIGN-<module>.md`.
- **Zero orphan sub-DESIGNs**: Every `DESIGN-*.md` file in this directory must be linked here in the main document body (not in `## Reference Documents`).

### Inter-Module Collaboration and Core Flows

Show how the modules collaborate end-to-end (an ASCII topology/sequence diagram or numbered core flows covering control flow and data flow) so a first-time reader grasps the system architecture before opening any `DESIGN-<module>.md`.

> **Optional domain-specific section**: If the project relies on a distinctive cross-cutting mechanism (such as a unified processing pipeline, plugin/extension runtime, or concurrency model), add a dedicated `## <Cross-Cutting Mechanism>` section without copying plugin-specific structure onto projects that do not use one.

## Technical Stack Choices

Technology and integration selections currently shipped in code.

| Domain | Choice | Rationale | Boundary |
|---|---|---|---|
| | | | |

## Interfaces and Contracts

Cross-module contracts (or single-module contracts for small projects); push per-module interface details into each `DESIGN-<module>.md`. Never copy-paste exhaustive CLI option tables or full API field inventories — express behavioral contracts (actor, triggers, sequence, `must`/`may`/`must not`, side effects, failure outcomes) and link to source definitions.

If the project includes shipped frontend UI, document:

- **Tech stack**: framework, UI library, build tooling
- **Design tokens**: color system, spacing scale, typography hierarchy, responsive breakpoints
- **Component conventions**: component library source and extension rules, controlled/uncontrolled conventions
- **Page/route structure**: key page flows, layout conventions (link to route config)
- **Interaction conventions**: unified loading, empty, and error states

## Data and State Model

Project-owned durable/runtime state, persistence, caches, and generated artifacts (aligning with the parent product `Runtime Model` when applicable), clarifying ownership, mutation lifecycle, and failure recovery.

| State | Location | Owner | Lifecycle & Rules |
|---|---|---|---|
| | | | |

## Business Rules and Failure Boundaries

Mandatory boundary and limitations anchor: active project-wide business rules, invariants, access/quota boundaries, known limitations, and complete failure consequences (error semantics, partial-failure rollback vs persisted residue, and recovery behavior). Module-specific rules live in `DESIGN-<module>.md`; never create a separate `BUSINESS_RULES.md`.

## Reference Documents

Reference-only background material: research notes, external specifications, or read-only historical references. Never repeat the header's `Parent Architecture` or `Parent Product`, and never list local `DESIGN-*.md` sub-documents here.
