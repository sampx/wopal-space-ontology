---
name: <Module or Directory> AGENT RULES
description: Local engineering rules auto-injected whenever an agent works inside <relative-dir-path>
maintenance: Keep only durable constraints unique to this directory; delete this file if no local constraints remain beyond the parent AGENTS.md
---

# Agent Rules — <Module or Directory>

Supplements `<relative-path-to-parent>/AGENTS.md` (e.g. `../AGENTS.md` or `../../AGENTS.md`; never repeat rules already governed by parent `AGENTS.md` files).

## Scope and Owning Design

- **Directory scope**: `<relative-dir-path>` — `<one-sentence responsibility>`
- **Owning DESIGN**: `[DESIGN-<module>.md](<relative-path-to-docs>/DESIGN-<module>.md)` (adjust `../` depth for nested dirs; update in the same change whenever observable behavior, config defaults, business rules, or failure outcomes change; skip on pure internal refactors)

## Local Constraints and Traps

<!-- List only durable local invariants, concurrency/isolation boundaries, or failure traps unique to this directory. Never paste DESIGN architecture prose or one-off bug stories. -->

- <local engineering invariant or runtime trap with concrete paths/symbols>
- <local gate/script scope rule, e.g. non-empty corpus + positive/negative verification for check scripts>

## Local Verification

Run the minimal targeted check covering this directory before claiming done:

- Targeted tests / gate: `<exact local test or check command>`
- Doc sync (when observable contracts change): `<exact verify-docset.py --check-sync command>`

## User-Supplied Rules

- <user-supplied rules; commands must not modify this section>
