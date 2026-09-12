# Phase Reference — Phase / Roadmap Authoring

Guide product phase discussions and produce phase definition and tracking documents. Template: `templates/phase.md`.

## Overview

Starting from the product DESIGN Evolution Roadmap section, guide the user through per-phase discussion of goals, current state, scope, targets and gaps (with design updates), and holistic review to surface residual risks.

**Input**: `<name> [phase-id]`. When not provided, infer the product name from `docs/products/`; confirm if unclear. `phase-id` defaults to the current Active phase.

## Core Principles

- Help the user clarify phase goals, analyze current state, define scope, analyze gaps and their design solutions, and surface/resolve residual risks.
- Discussion uses the product DESIGN Evolution Roadmap as the skeleton and the product PRD as the vision baseline.
- The Phase document is written continuously during discussion — each step's output is written directly into the living document.
- Phase documents provide reliable input for the next step: splitting into Plans.
- User-confirmed design decisions are promptly updated in the corresponding PRD and DESIGN documents per the design reference.
- Present the plan and obtain explicit user confirmation before any write.

## Workflow

1. **Identify the current phase**: read the product DESIGN Evolution Roadmap and PRD; list phases and statuses; default to Active.
2. **Discuss phase goal**: verifiable product capability statement ≥20 characters; no placeholders; refine until consensus. Write the Goal section.
3. **Analyze current state**: concise narrative prose per project/subsystem showing the gap to the goal. Write Current State.
4. **Discuss scope**: Scope = one-line-per-area summary with Owner; Out of Scope = explicit exclusions. Write both sections.
5. **Discuss targets, gaps, and design** (critical): for each scope area, define Current / Target / Design solution / Exit criteria (checkbox format). Each scope area is an `###` heading; gaps grouped under `#### Gaps`; each gap a `#####` heading. A gap without a design solution is a residual risk → step 6.
6. **Review and surface residual risks**: holistic review; write risks to the Risks section with explicit "why no design solution" explanation. Iterate until resolved or user accepts remaining risks.

## Document-Update Discipline

- User-confirmed design decisions → update corresponding project DESIGNs, PRD, product DESIGN as needed (per design reference).
- Phase document follows the phase template.

**Document-set consistency**: the Phase update is never isolated. After the Phase settles, review the whole set — PRD, product DESIGN, project DESIGNs, sub-DESIGNs — and align every affected document. The Phase Goal must trace to the DESIGN Evolution Roadmap entry; the DESIGN Roadmap and PRD story must not contradict the settled Phase.

## File Naming and Location

- File placed in the `phases/` directory sibling to the product DESIGN.
- Naming: `{product}-{phase-id}-{slug}.md` — slug from title: lowercase → remove non-alphanumeric → spaces to `-` → strip trailing status markers (`[-—].*$`) → trim hyphens → truncate ≤40 characters.

## Quality Checklist

- [ ] Uses the phase template structure
- [ ] File in `phases/` sibling to the product DESIGN; naming per spec
- [ ] Current State uses narrative prose showing the gap
- [ ] Scope is a one-glance summary list
- [ ] Targets and Gaps: each scope area has ≥1 gap; each gap has Current / Target / Design / Exit
- [ ] Every gap has a design solution with a design document reference
- [ ] Risks only contains items without a design solution, each with explicit why
- [ ] References does not repeat header documents
- [ ] Associated design documents updated per design reference
- [ ] Whole document set reviewed and aligned (PRD, DESIGNs, sub-DESIGNs)

## Guide Plan Decomposition

Once the Phase document is ready, guide the user to create Plans for each scope area, following dev-flow skill standards.

## Response After Completion

Respond in the user's language with: phase document path; key summary (Goal, Scope areas, Gap count, Residual risk count); design documents updated; quality gate result; suggested next step (create Plans per scope area).
