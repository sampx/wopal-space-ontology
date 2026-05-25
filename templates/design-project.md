# <Project Name>

> **Status**: Active  
> **Updated**: YYYY-MM-DD  
> **Parent Architecture**: `<parent-design-path>`  
> **Product Intent**: `<prd-path>`

## 0. Change Log

| Date | Type | Summary |
|---|---|---|
| YYYY-MM-DD | Created / Updated | One-line summary |

## 1. Project Role

State where the project fits, what it owns, and what it explicitly delegates to other projects. Keep this concise and technical: role position, responsibility boundary, and target responsibility only.

## 2. Design Principles

List the principles that guide technical choices inside this project. Keep them specific enough to resolve design tradeoffs.

## 3. Module Architecture

Describe internal modules and responsibilities in design-state language. Avoid implementation-state labels such as "current location". Code paths may appear as implementation carriers, but the primary columns should be design module, responsibility, and owner / target carrier.

## 4. Technical Stack Choices

Document the technical stack and integration choices: runtime, framework, build / package tools, filesystem / state handling, external binaries, security scanners, protocol / client choices, output model, and configuration format. For each choice, explain why it fits this project and what boundary it must not cross.

## 5. Interfaces and Contracts

Define external surfaces: CLI commands, APIs, events, file formats, schemas, protocols, or integration contracts. Keep this at specification level, not code walkthrough level.

## 6. Data and State Model

Describe owned state, persistence, configuration, caches, generated files, and migration or idempotency rules.

## 7. Implementation Status

Summarize current implementation against the related PRD roadmap or phases, not as a flat module inventory. For each phase, state the PRD target, what has landed, what remains, and what is deferred. Use implementation evidence, but write this as product-design progress rather than a code checklist.

## 8. Related Documents

Link only durable product / design references: parent PRD / DESIGN, project PRD, business rules, architecture references, and project specs.
