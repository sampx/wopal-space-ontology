# <Project Name>

> **Status**: Active  
> **Updated**: YYYY-MM-DD  
> **Parent Architecture**: `<parent-design-path>`  
> **Parent Product**: `<parent-product-prd-path>`

## 0. Change Log

| Date | Type | Summary |
|---|---|---|
| YYYY-MM-DD | Created / Updated | One-line summary |

## 1. Project Role

State where the project fits, what it owns, and what it explicitly does not own. Include one sentence on the core responsibility this project carries for the parent product. Keep this concise and technical.

## 2. Capability Scope

List target-state capability groups owned by the project. Describe boundaries only: owned target capabilities, explicit out-of-scope areas, and delegation boundaries. Do not include phase timing, implementation status, or delivery progress here.

## 3. Design Principles

List the principles that guide technical choices inside this project. Keep them specific enough to resolve design tradeoffs.

## 4. Module Architecture

Describe internal modules and responsibilities in design-state language. Avoid implementation-state labels such as "current location". Code paths may appear as implementation carriers, but the primary columns should be design module, responsibility, and owner / target carrier.

## 5. Technical Stack Choices

Document the technical stack and integration choices: runtime, framework, build / package tools, filesystem / state handling, external binaries, security scanners, protocol / client choices, output model, and configuration format. For each choice, explain why it fits this project and what boundary it must not cross.

## 6. Interfaces and Contracts

Define external surfaces: CLI commands, APIs, events, file formats, schemas, protocols, or integration contracts. Keep this at specification level, not code walkthrough level.

## 7. Data and State Model

Describe owned state, persistence, configuration, caches, generated files, and migration or idempotency rules.

## 8. Evolution Roadmap

Describe how the project matures across product phases. Use structured headings so tooling can parse phase definitions:

### Phase N: Title

- **Target**: the PRD capability target for this phase
- **Landed**: what has been implemented
- **Remaining**: what is still needed

Mark each phase as completed, current, planned, or deprecated when known. Focus on product outcomes and capability maturity, not task lists. This section is the primary input for `/cupdate-roadmap`.

## 9. Related Documents

Link only durable product / design references: parent PRD / DESIGN, business rules, architecture references, research summaries, and project specs.
