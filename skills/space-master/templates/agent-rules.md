---
name: <Project or Module(dir)> AGENT RULES
description: <One-line stable description of the current project or directory module responsibility>
---

# Agent Development Rules

## Canonical References

Canonical references:

<!-- List only documents that actually exist and are directly relevant to this scope. Do not write N/A placeholders. -->
- PRD: `<path-when-relevant>`
- DESIGN: `<path-when-relevant>`
- Business Rules: `<path-when-relevant>`
- Referral Rules: `<path-when-relevant>`

## Architecture and Directories

<Brief current architecture description; may include a concise runtime flow>

| Directory | Responsibility |
|---|---|
| | |

<!-- The directory table lists only paths that currently exist. Durable target-structure constraints belong in Implementation Rules, not as current directory facts. -->

## Development Commands (build format test)

| Scenario | Command | When |
|---|---|------|

## Implementation Rules

- <technical implementation rule>
- <project-specific UI/UX or output rule if applicable>

## Testing

- <For testable pure logic, follow TDD: write a failing test first, then implement code to make it pass>
- <state which project logic must be covered by automated tests and which host APIs, external systems, or real runtime boundaries require manual verification>

## User-Supplied Rules

- <user-supplied rules; commands must not modify this section>
- <when updating: original rules that do not fit the sections above should be preserved here verbatim>
