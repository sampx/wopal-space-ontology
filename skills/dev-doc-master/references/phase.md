# Phase Reference — Phase Authoring

Guide product phase discussions and produce phase definition and tracking documents. Template: `templates/phase.md`.

## Overview

A phase is cut from the product DESIGN's Capability Roadmap: a batch of capability steps that can be verified together. Starting from that map and the project-level GAPS, guide the user through per-phase discussion of goals, scope, the gap inventory, and completion criteria.

**Input**: `<name> [phase-id]`. When not provided, infer the product name from `docs/products/`; confirm if unclear. `phase-id` defaults to the current Active phase.

## Core Principles

- A phase is a capability-batch, not an activity list. Its Goal names the capability steps this phase advances; it does not name a list of tasks.
- The phase explicitly declares which Capability Roadmap rows it advances (the `Advancing` section). The phase-to-map trace must be a checkable fact, not an implicit claim.
- Phases are registered, not predicted. Register a phase when a line of evolution starts to converge — do not pre-declare future phases to fill out a roadmap.
- The phase document is an **index and a tracking surface**, not a second gap tracker. Gap detail lives in the project `GAPS.md`; the phase lists which gaps it closes by identifier, title, priority, and design pointer.
- The phase document does not track execution status. Plan status is owned by the dev-flow state machine and surfaced through the `Related Plans` table.
- The Phase document is written continuously during discussion — each step's output is written directly into the living document.
- Phase documents provide reliable input for the next step: splitting into Plans.
- User-confirmed design decisions are promptly updated in the corresponding PRD and DESIGN documents per the design reference.
- Present the plan and obtain explicit user confirmation before any write.

## Workflow

1. **Identify the phase**: read the product DESIGN Capability Roadmap and the project GAPS. List registered phases and statuses; default to Active. If the phase is not yet registered, help the user decide the capability rows it covers and register it in the map first.
2. **Discuss phase goal and advancing rows**: a verifiable product capability statement ≥20 characters. Then name exactly which Capability Roadmap rows the phase advances and to which step. Write Goal and Advancing.
3. **Discuss scope**: Scope = one-line-per-area summary with Owner. Out of Scope = explicit exclusions. Write both sections.
4. **Build the gap inventory** (critical): for each scope area, select the gaps from the project `GAPS.md` that this phase closes. Record identifier, title, priority, and the design document each gap points at. Do not restate Current / Target / Exit — those stay in `GAPS.md`. A gap with no design solution does not enter the inventory; it becomes a risk.
5. **Define completion criteria**: the delivery facts that span multiple gaps and belong to no single one. These are the phase's own exit criteria; individual gap exit criteria stay in `GAPS.md`.
6. **Review and surface residual risks**: holistic review; write risks to the Risks section with explicit "why no design solution" explanation. Iterate until resolved or user accepts remaining risks.

## Document-Update Discipline

- User-confirmed design decisions → update corresponding project DESIGNs, PRD, product DESIGN as needed (per design reference).
- Phase document follows the phase template.
- When the phase covers capability rows not yet in the Capability Roadmap, register them there first.
- When a gap listed in the inventory is closed, remove it from the project `GAPS.md`; the inventory entry then drops from the phase. A phase completes when its gap inventory is empty and its completion criteria are met.

**Document-set consistency**: the Phase update is never isolated. After the Phase settles, review the whole set — PRD, product DESIGN, project DESIGNs, sub-DESIGNs — and align every affected document. The Phase Goal must trace to the Capability Roadmap entry; the Capability Roadmap and PRD story must not contradict the settled Phase.

## File Naming and Location

- Active and planned phases live in the `phases/` directory sibling to the product DESIGN.
- Completed phases move to `phases/done/`. A phase is complete when its gap inventory is empty and its completion criteria are met. Moving it keeps `phases/` a view of what is still in flight.
- Naming: `{product}-{phase-id}-{slug}.md` — slug from title: lowercase → remove non-alphanumeric → spaces to `-` → strip trailing status markers (`[-—].*$`) → trim hyphens → truncate ≤40 characters.
- The Capability Roadmap's phase entries link to the phase document wherever it lives, `phases/` or `phases/done/`.

## Quality Checklist

- [ ] Uses the phase template structure
- [ ] Active phase in `phases/`, completed phase in `phases/done/`; naming per spec
- [ ] Goal traces to a Capability Roadmap row and target step; no placeholder
- [ ] `Advancing` names the Capability Roadmap rows and target steps explicitly
- [ ] Scope is a one-glance summary list with Owner per area
- [ ] Gap Inventory: each scope area has ≥1 gap; each entry carries identifier, title, priority, and design pointer
- [ ] Every gap listed exists in a project `GAPS.md`; no Current / Target / Exit restated here
- [ ] Completion Criteria carries only cross-gap delivery facts
- [ ] Related Plans table has no hand-maintained status beyond what dev-flow owns
- [ ] Risks only contains items without a design solution, each with explicit why
- [ ] References does not repeat header documents
- [ ] Associated design documents updated per design reference
- [ ] Whole document set reviewed and aligned (PRD, DESIGNs, sub-DESIGNs)

## Guide Plan Decomposition

Once the Phase document is ready, guide the user to create Plans for each scope area, following dev-flow skill standards. A Plan names the phase it belongs to in its own body; the phase's `Related Plans` table is the aggregate view. The phase document does not track execution status itself — Plan status is tracked by the dev-flow state machine.

## Response After Completion

Respond in the user's language with: phase document path; key summary (Goal, Advancing rows, Scope areas, Gap count, Completion criteria count); design documents updated; quality gate result; suggested next step (create Plans per scope area).
