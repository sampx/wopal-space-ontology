# <Project Name>

> **Status**: Active  
> **Updated**: YYYY-MM-DD  
> **Parent Architecture** (mandatory): `<parent-design-path or N/A>` — the architecture contract this DESIGN follows  
> **Parent Product** (mandatory): `<parent-product-prd-path or N/A>` — the product PRD this DESIGN follows  
> **Sub-DESIGNs** (mandatory when they exist): list every `DESIGN-<topic>.md` under this main document

---

## Project Role

The project's positioning within the parent product, its responsibilities, and explicit boundaries.

- Standard flow (`Parent Product` is not N/A): one-line core responsibility + technical positioning + boundary table (what it owns, what it does not own)
- Simplified flow (`Parent Product: N/A`): describe the project's own positioning and value proposition; define responsibility boundaries independently

## Capability Scope

The project's target-state capability groups and their boundaries.

- List target capabilities and explicitly excluded areas
- Standard flow: derive product capabilities from the parent PRD; simplified flow: define independently
- Describe design-state capability boundaries; do not include phase timing or implementation progress

## Key Decisions

Key architecture decisions for this project and their rationale.

| Decision | Rationale |
|----------|-----------|
| | |

## Module Architecture

Internal module decomposition and ownership.

| Module | Responsibility | Carrier |
|--------|---------------|---------|
| | | |

## Technical Stack Choices

Technology choices and integration selections. Each entry includes: choice, rationale, explicit boundary.

| Domain | Choice | Rationale | Boundary |
|--------|--------|-----------|----------|
| | | | |

## Interfaces and Contracts

External surfaces, described at specification level. Covers: CLI commands, APIs, events, file formats, schemas, protocols, integration contracts, consumed templates, and configuration.

- List each interface with name, consumer, and input/output conventions
- File formats / schemas: define fields, constraints, generation rules
- Configuration contracts: describe layering relationships and defaults
- Templates: list template name, render target, responsibility

If the project includes frontend UI, this section serves as the UI design contract:

- **Tech stack**: framework, UI library, build tooling
- **Design tokens**: color system, spacing scale, typography hierarchy, responsive breakpoints
- **Component conventions**: component library source and extension rules, controlled/uncontrolled conventions
- **Page/route structure**: page inventory, route hierarchy, layout templates
- **Interaction conventions**: unified handling for loading, empty, and error states

## Data and State Model

Project-owned state, persistence, configuration, caches, generated files. Clarify data ownership, migration rules, and idempotent behavior.

| State | Location | Owner | Rules |
|-------|----------|-------|-------|
| | | | |

## Related Documents

Reference-only documents: business rules, architecture references, project specs, and auxiliary material. Do not repeat the parent PRD/DESIGN listed in the header.
