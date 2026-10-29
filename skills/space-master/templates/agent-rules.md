---
name: <Project or Module(dir)> AGENT RULES
description: <One-line stable description of the current project or directory module responsibility>
maintenance: <When this file should change; prohibit one-off tasks, implementation facts and bug records>
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

<!-- Record actual entry commands. When reusable project scripts, fixtures or contract helpers exist, name them here or under Testing so agents do not rebuild equivalents. -->

## Quality Gates

<!-- Every gate must be an existing executable command. Do not list a manual review as a quality gate. -->

| Gate | Command | Blocks work when |
|---|---|---|
| Format / lint / type check | `<command>` | `<failure condition>` |
| Unit tests | `<command>` | `<failure condition>` |
| Integration tests | `<command>` | `<failure condition>` |
| Build / package | `<command>` | `<failure condition>` |

## Implementation Rules

- <module ownership and coding-style rule; name the formatter/linter/typecheck entry when applicable>
- <canonical error type, stable fields and side-effect uncertainty rule>
<!-- For CLI/service projects, add concrete rules for success/failure streams, output format, exit codes, log sink, rotated files, recorded fields and forbidden content. For libraries or UI, replace these with the applicable public-contract or user-visible-state rules. -->

## Testing

- <For testable pure logic, follow TDD: write a failing test first, then implement code to make it pass>
- <unit test directory and command; integration test directory and command; which project logic belongs to each layer>
- <reusable fixtures, contract helpers and isolation/cleanup rules; how new tests are registered so they cannot be silently omitted>
- <which host APIs, external systems, or real runtime boundaries require manual verification; state why no automated gate can cover them>

## Code Review Rules

<!-- Keep this heading verbatim in English — review tooling locates this
     section by the heading. Never translate, rename, or remove it. -->

<!-- Direction-level skeleton only. Each project fills in its own
     project-specific checkpoints below; never bake any single project's
     rules into this template. -->

Use the review process configured for this project. Reference the
actual review skill, command, or checklist instead of restating it.

Report a defect only when the diff introduces it and the finding names a
concrete trigger, the affected behavior, and evidence in the changed code.
Omit pre-existing problems, style preferences, and anything CI already
enforces.

### <Project-specific review checkpoints>

- <repository-specific checks that complement, not replace, CI and tests>

## User-Supplied Rules

- <user-supplied rules; commands must not modify this section>
- <when updating: original rules that do not fit the sections above should be preserved here verbatim>
