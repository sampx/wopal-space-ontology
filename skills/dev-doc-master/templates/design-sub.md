# DESIGN — <Topic or Module>

> **Status**: Draft | Proposed | Active
> **Updated**: YYYY-MM-DD
> **Parent**: `./DESIGN.md` — the main DESIGN this sub-document decomposes
> **Parent Architecture**: `<product-design-path or N/A>` — the product architecture DESIGN this project follows (or `N/A` if this IS a product sub-DESIGN)
> **Parent Product**: `<product-prd-path or N/A>` — the product PRD this follows

Choose the contract that matches the parent tier:
- **Product Sub-DESIGN** (decomposing a product main `DESIGN.md`): follows product-design rules (`references/design.md`). Allowed and expected to plan target product architecture, cross-project subsystem roles, and unbuilt capabilities before project implementation (verify any existing repo paths referenced).
- **Project / Module Sub-DESIGN** (decomposing a project main `DESIGN.md`): follows present-state rules (`references/design-project-guide.md`, typically `Status: Active`). Document only shipped, code-verified capabilities, active business rules, and full failure outcomes; explicitly label untested items with their verification condition and never write unbuilt plans as live behavior.

---

## Overview and Scope

Fixed entry anchor: orient a first-time reader immediately without code-diving:
- What problem this module or topic solves and what observable capabilities it exposes today (for Project Sub-DESIGN, verified live behavior only; for Product Sub-DESIGN, planned cross-project/subsystem behavior)
- Target callers/users, critical prerequisites, and explicit ownership boundaries (`Owned Here` vs handled by main `DESIGN.md` or sibling modules)
- Owning `Source Carrier` code paths mapped back to `## Module Architecture` in `./DESIGN.md` (relative links)

## Usage and Interface Contracts

Fixed entry anchor: how callers, operators, or sibling modules invoke, configure, or integrate with this unit:
- Entry points, invocation patterns, key configuration switches, defaults, and explicit constraints/limits
- Behavioral contracts (actor, trigger preconditions, `must` / `may` / `must not`) with relative links to owning source definitions
- Never transcribe full source directory trees, exhaustive CLI flag tables, or complete API field inventories here

## <Domain Concept or Core Mechanism 1..N>

Flexible domain sections — replace this placeholder with **1..N bespoke `##` headings** named after the module's genuine domain concepts (for example: `## Request Routing Pipeline`, `## Scheduling State Machine`, `## Storage Codec`, or `## Extension Points` *only* if this module actually exposes plugin/hook points).

Across these bespoke domain sections and the anchors below, ensure the module satisfies all **5 Required Coverage Elements**:
1. **Actor & trigger preconditions**: who invokes each major path and under what state/input preconditions
2. **Component collaboration & ordered sequence**: step-by-step execution or ASCII flow/state diagram showing how internal parts interact
3. **Permissions, obligations & invariants**: explicit `must` / `may` / `must not` guarantees and branching rules
4. **Side effects & state writes**: durable files, database records, caches, or events mutated along the path
5. **Complete failure outcomes & recovery**: concrete error semantics, rollback vs persisted partial-failure residue, and operator/caller recovery steps

## Data and State Model

Fixed state anchor: document durable/runtime state owned by this module (or explicitly state `"Stateless: holds no durable state outside caller inputs"` if none).

| State | Location | Owner | Lifecycle & Rules |
|---|---|---|---|
| | | | |

## Business Rules and Failure Boundaries

Fixed boundary and limitations anchor (required on active Project Module Sub-DESIGNs): active business rules, quotas, invariants, feature flags/switches, error semantics, partial-failure residue vs rollback guarantees, recovery steps, and known limitations owned by this module (do not create a separate `BUSINESS_RULES.md`).

## Reference Documents

| Document | Purpose |
|---|---|
| `<path>` | `<reference-only material; never repeat Parent, Parent Architecture, or Parent Product>` |
