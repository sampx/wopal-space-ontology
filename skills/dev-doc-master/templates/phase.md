# <Phase Name>

> **Product**: `<product>`
> **Phase ID**: `<phase-id>`
> **Status**: Planned | Active | Completed
> **Updated**: YYYY-MM-DD
> **Product PRD** (mandatory): `<prd-path>` — the PRD this Phase follows  
> **Product DESIGN** (mandatory): `<design-path>` — the DESIGN contract this Phase follows

---

## Goal

One sentence describing the product capability to be delivered in this phase (cross-project perspective).

## Current State

Describe the current state for each project or subsystem in concise narrative prose. Cover both existing capabilities and what is missing — present the full gap between current state and the phase goal.

## Scope

A concise summary list of product capabilities to be delivered in this phase, so humans and agents can grasp the full scope at a glance. One line per scope area with Owner. Example:

- **CLI 分发** — Node SEA release packaging → public release carrier → installer one-click install. Owner: wopal-cli
- **ellamaka 分发** — artifact branding + 4-platform matrix + GitHub Release. Owner: ellamaka

## Out of Scope

- Capabilities or projects explicitly excluded from this product phase

## Targets and Gaps

Each scope area from Scope gets a detailed gap analysis here. Organized by `###` for each scope area, with `#### Gaps` and `#####` for individual gaps.

Gap structure:

- **Current**: current state (what is missing)
- **Target**: the target state after the gap is closed
- **Design**: where the solution is documented (project DESIGN or DISTRIBUTION path)
- **Exit**: checkbox-format exit criteria — one line when single, multi-line `- [ ]` when multiple. Each gap must have at least one exit criterion. Exit criteria checkboxes collectively define the phase's completion.

```
### <Scope Area>
Owner: <project>

#### Gaps

##### <Gap Title>
- **Current**: ...
- **Target**: ...
- **Design**: ...
- **Exit**:
  - [ ] exit criterion
  - [ ] exit criterion
```

Writing rules for gaps:

- A gap without a design solution does not belong here — it belongs in Risks.
- Exit criteria describe delivery facts, not implementation steps.
- Each scope area should have ≥1 gap.
- Each gap should be independently verifiable via its exit criteria.

## Related Plans

<!-- Maintained automatically or manually after Plans are linked -->

| Project | Plan | Status |
|---------|------|--------|

## Risks

Only items without a design solution go here. Gaps with design solutions are managed in Targets and Gaps.

| Risk / Dependency | Impact | Why no design solution |
|-------------------|--------|------------------------|

## References

Reference-only documents: project DESIGNs and other relevant auxiliary material. Do not repeat the PRD or DESIGN listed in the header.

- Project DESIGN: `<project-design-path>`
