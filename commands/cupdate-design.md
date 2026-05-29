---
description: Create or update a product DESIGN or project DESIGN
---

# Create or Update DESIGN

Guide users through discussion to clarify product system architecture (product DESIGN) or project internal design (project DESIGN). The core responsibility is helping users define design boundaries and reach design decisions until conditions are met for the next work phase.

Simple projects may skip product DESIGN and follow the simplified flow: project DESIGN (with self-defined product-level design) → Plan.

**Input**: `$1` `$2`

**Parameter Notes**: `<name> [product|project]`. When not provided, infer from `docs/products/` and `projects/*/docs/` directory matching; confirm with the user if unclear.

---

## Core Principles

### Two Design Flows

| Flow | Use Case | Chain |
|---|---|---|
| Standard | Multi-project product requiring cross-project architecture coordination | PRD → Product DESIGN → Roadmap → Project DESIGN → Plan |
| Simplified | Standalone project with no associated product | Project DESIGN (with product-level design) → Plan |

In the standard flow, the product DESIGN is used for phase decomposition and architecture contract definition; the project DESIGN focuses on single-project internal architecture. In the simplified flow, the project DESIGN also assumes product-level design responsibility (Header `Parent Product: N/A`).

### Discussion Rules

- The command's core role is guiding users to discuss and clarify design decisions. Product DESIGN uses the `design-product.md` template; project DESIGN uses the `design-project.md` template.
- Product DESIGN discussion focus: system layering and subsystem boundaries, runtime model, end-to-end flows, phase decomposition (at minimum, clarify the current phase's overall goal; detail is deferred to `/cupdate-roadmap`).
- Project DESIGN discussion focus: project role and boundaries, capability scope, module architecture, technology choices, interface contracts, data model.
- Preserve accurate existing content. Revise or remove outdated information when evidence is sufficient. Mark unresolved items as needing confirmation.
- Present the full content and obtain explicit user confirmation before any write operation.

## Step 1: Gather Context

**Standard flow**:
- Product DESIGN: read the product PRD
- Project DESIGN: read the parent product PRD + parent product DESIGN

**Simplified flow** (Header `Parent Product: N/A`):
- Read the project's own code and documents for existing design decisions

**Update**:
- Read the existing DESIGN, user decisions from the current conversation, and implementation facts from code and documents

**Output**: Context inventory, items needing confirmation

## Step 2: Guide Design Discussion

Guide the user through each template section in order.

**Product DESIGN discussion points**:
1. System layering and architecture overview
2. Core subsystem roles, boundaries, and interaction contracts
3. Runtime model (state locations, configuration layers, lifecycle)
4. Key end-to-end flows
5. Phase decomposition: break the product vision into deliverable phases; at minimum, clarify the current phase's overall goal

**Project DESIGN discussion points**:
1. Project positioning and responsibility boundary within the parent product (simplified flow: self-defined positioning and value proposition)
2. Target capability scope and explicitly excluded areas
3. Key architecture decisions and rationale
4. Internal module decomposition and ownership
5. Technology stack choices and rationale
6. External interfaces and integration contracts. If the project includes frontend UI: tech stack selection, design tokens, component conventions, page structure
7. Data and state model

**Output**: Discussion conclusions for each section

## Step 3: Write DESIGN

Produce the DESIGN document from the discussion conclusions using the template. When updating an existing document:

1. Preserve existing paths and titles
2. Update the `Updated` date
3. Align discussion conclusions with existing content
4. Fill in missing sections
5. Revise or remove outdated content
6. Append a Change Log entry (record design intent, architecture, boundary, or contract changes)
7. Mark unresolved items as needing confirmation

Present the full content and wait for user confirmation before writing.

**Output**: Complete DESIGN content, awaiting confirmation

## Step 4: Verify

After writing, check template section completeness and design language quality.

---

## Completion Standard

The command is complete when the following conditions are met:

- Product DESIGN: system architecture boundaries are clear, the current phase's overall goal is defined, and the work is ready for `/cupdate-roadmap` phase refinement
- Project DESIGN (standard flow): internal architecture decisions are clear, ready for `/cupdate-agent-rules` or Plan creation
- Project DESIGN (simplified flow): design decisions are sufficiently clear to proceed directly to Plan

---

## Response After Completion

Respond in the user's preferred language with:

1. File path
2. Creation/update summary (additions, revisions, removals/deprecations, items needing confirmation)
3. Suggested next step: product DESIGN → `/cupdate-roadmap`; standard project DESIGN → `/cupdate-agent-rules`; simplified project DESIGN → create Plan