# <Phase Name>

> **Product**: `<product>`
> **Phase ID**: `<phase-id>`
> **Status**: Planned | Active | Completed
> **Updated**: YYYY-MM-DD
> **Product PRD** (mandatory): `<prd-path>` — the PRD this Phase follows  
> **Product DESIGN** (mandatory): `<design-path>` — the DESIGN contract this Phase follows

---

## Goal

One sentence describing the product capability to be delivered in this phase (cross-project perspective). The goal names the capability this phase delivers, not a list of activities.

## Scope

A concise summary list of product capabilities to be delivered in this phase, so humans and agents can grasp the full scope at a glance. One line per scope area with Owner. Example:

- **CLI distribution** — Node SEA release packaging → public release carrier → installer one-click install. Owner: wopal-cli
- **ellamaka distribution** — artifact branding + 4-platform matrix + GitHub Release. Owner: ellamaka

## Gap Inventory

The gaps this phase closes, grouped by scope area. Each scope area is a `###` heading with its Owner and a table.

The gap detail lives in each project's `GAPS.md` — that is the single source of truth. This document lists which gaps belong to the phase, not a restatement of them. A gap entry carries only its identifier, title, priority, and the design document it points at.

```
### <Scope Area>

Owner: <project>

| Gap | Title | Priority | Design |
|-----|-------|----------|--------|
| <GAP-ID> | <gap title> | P0 | <design document> |
```

Writing rules for the gap inventory:

- Every gap listed must exist in a project `GAPS.md`. The identifier is the link between the two.
- Do not restate Current / Target / Exit here — those live in `GAPS.md` and duplicate descriptions drift.
- A gap with no design solution does not appear in the inventory — it belongs in Risks.
- Group by scope area; each scope area should have ≥1 gap.

## Completion Criteria

The phase-level exit criteria: delivery facts that span multiple gaps and belong to no single one. Checkbox format.

```
- [ ] cross-gap delivery fact
- [ ] cross-gap delivery fact
```

Individual gap exit criteria are carried by each gap in `GAPS.md`. This section carries only what closes the phase as a whole.

## Execution Order

Include this section only when the phase's scope areas have hard dependencies on each other — where the output of one area is the input another cannot start without. The section names the order and the reason each step must precede the next.

```
<scope area>（<owner>）
  ← <ordering reason>
      → <scope area>（<owner>）
          → <scope area>（<owner>）
```

When the scope areas can proceed independently, omit this section. It describes dependency between capability lines, never a task list or a schedule.

## Related Plans

The tracking surface for this phase. Plans are created per scope area through dev-flow; their status is owned by the dev-flow state machine and updated by `archive`, never maintained by hand here.

Each row registers one Plan against its slot; the row label carries the plan linkage so `archive` can update the row automatically:

```
| Plan | Range | Gaps | Project | Status |
|------|-------|------|---------|--------|
| <slot>: <scope area> · <plan-name> | <what this plan delivers, one line> | <gaps closed by this plan> | <owner project> | |
```

- `<slot>`: phase slot identifier (e.g. `P-A`), matching the `Execution Order` naming.
- ` · <plan-name>`: appended when the Plan is created and registered against the slot. Before registration the row label is `<slot>: <scope area>` only.
- `Range`: one-line statement of what the Plan delivers (scope slice).
- `Gaps`: the gap identifiers this Plan closes.
- `Status`: filled automatically by dev-flow `archive` on Plan archive; keep it empty by hand.

## Risks

Only items without a design solution go here. Gaps with design solutions are managed in the gap inventory.

| Risk / Dependency | Impact | Why no design solution |
|-------------------|--------|------------------------|

## Reference Documents

Reference-only documents: project DESIGNs and other relevant auxiliary material. Do not repeat the PRD or DESIGN listed in the header.

- Project DESIGN: `<project-design-path>`
