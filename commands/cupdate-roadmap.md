---
description: Guide product phase discussions and produce phase definition and tracking documents
---

# Create or Update Roadmap

Starting from the product DESIGN §5 Evolution Roadmap, guide the user through per-phase discussion of goals, scope, involved projects, exit criteria, and risks. Produce Phase documents and write back references to the product DESIGN and project DESIGNs.

**Input**: `$1` `$2`

**Parameter Notes**: `<name> [phase-id]`. When not provided, infer the product name from `docs/products/`; confirm with the user if unclear. `phase-id` is optional; when omitted, default to the current Active phase.

---

## Core Principles

- The core responsibility is helping the user clarify phase goals, scope, involved projects, and exit criteria.
- Discussion uses the product DESIGN §5 Evolution Roadmap as the skeleton and the product PRD as the vision baseline.
- Discussion output is a Phase document (phase definition and acceptance criteria), with references written back to the product DESIGN and corresponding project DESIGNs.
- Phase documents provide reliable input for the next step: splitting into Plans.
- Phase documents use the `.wopal/templates/phase.md` template.
- Present the plan and obtain explicit user confirmation before any write operation.

## Step 1: Identify the Current Phase

Read the product DESIGN §5 and product PRD. List all phases and their current status (Active / Completed / Planned).

Guide the user to select the phase to discuss. Default to the current Active phase; the user may specify a completed phase for retrospective adjustment or a planned phase for early discussion.

**Output**: Selected phase ID, title, and existing Goal description from the product DESIGN

## Step 2: Discuss Phase Goal

Discuss the product capability goal for this phase with the user, anchoring on the product PRD vision and product DESIGN architecture contracts.

- Present the existing Goal description from the product DESIGN and ask whether to keep or adjust it.
- The goal must be a verifiable product capability statement, ≥20 characters. Placeholders are forbidden.
- Allow goal refinement during discussion until consensus is reached.

**Output**: Confirmed phase Goal

## Step 3: Discuss Phase Scope

Clarify the product capability boundaries for this phase:

- **Scope**: the product capabilities to be delivered in this phase; summarize the subsystems or projects involved.
- **Out of Scope**: capabilities or projects explicitly excluded from this phase.

**Output**: Scope and Out of Scope lists

## Step 4: Identify Involved Projects

Determine which projects participate in this phase and what role each plays.

For each project, discuss:
- Project role (core delivery / tooling / enablement)
- The project's design objectives for this phase — what architecture decisions, interface definitions, or capability building must be completed

**Output**: Involved Projects table (project, role, phase design objectives)

## Step 5: Determine Exit Criteria

Define Exit Criteria for each involved project, one by one.

- Group by project (`### Project Name`), 1–6 items per group.
- Each item in `- [ ]` checkbox format, independently verifiable.
- Exit criteria describe delivery facts, not implementation steps.

**Output**: Exit Criteria grouped by project

## Step 6: Discuss Risks and Dependencies

Identify cross-project dependencies and coordination risks. Discuss mitigation measures.

**Output**: Risk/dependency table (risk, impact, mitigation)

## Step 7: Generate the Phase Document

Use the `.wopal/templates/phase.md` template to produce the Phase document from the discussion results.

Generation rules:
- Status: completed → `Completed`, current phase → `Active`, others → `Planned`
- File naming: `{product}-{phase-id}-{slug}.md`, placed in the `phases/` directory sibling to the product DESIGN
- Slug: title → lowercase → remove non-alphanumeric → replace spaces with `-` → strip trailing status markers with regex `[-—].*$` → trim leading/trailing hyphens → truncate ≤40 characters

Present the full document content and file path. Wait for user confirmation.

**Output**: Phase document content, awaiting confirmation

## Step 8: Write and Back-Reference DESIGNs

After user confirmation:

1. Create the `phases/` directory (if it does not exist)
2. Write the Phase document
3. Insert a Phase doc reference link below the corresponding phase heading in product DESIGN §5
4. Write this phase's project delivery target references into the corresponding project DESIGNs

**Output**: Written file paths, DESIGN reference changes

## Step 9: Guide Plan Decomposition

Once the Phase document is ready, guide the user to create Plans for each project's Involved Project, decomposing phase exit criteria into executable development tasks.

---

## Completion Standard

Discussion guidance is complete when all of the following are satisfied:

1. Phase goal is clarified and design decisions needed to achieve it are agreed upon
2. Involved projects and their phase design objectives are clear
3. Exit Criteria are determined per project, each independently verifiable
4. Identified core risks have mitigation plans
5. The phase is ready for decomposition into per-project Issues and Plans

The phase outputs and updated documents (Phase document, product DESIGN, project DESIGNs) are solidified in a single commit.

---

## Response After Completion

Respond in the user's preferred language with:

1. Created/updated Phase document
2. Key phase decision summary (Goal, Involved Projects, Exit Criteria)
3. Product DESIGN and project DESIGN reference changes
4. Reminder to commit all changes in a single commit to solidify results
