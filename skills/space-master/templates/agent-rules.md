---
name: <Project Name> AGENT RULES
description: <One-line stable description of the current project responsibility>
maintenance: <When this file should change; prohibit one-off tasks, implementation facts and bug records>
---

# Agent Development Rules

## Canonical References

Canonical references:

<!-- List only documents that actually exist and are directly relevant to this scope. Do not write N/A placeholders. Active business rules live in DESIGN; never add a standalone BUSINESS_RULES.md entry here (if a legacy one exists, treat it as read-only historical reference). -->
- PRD: `<path-when-relevant>`
- DESIGN: `<path-when-relevant>`
- Docs Rules: `./docs/AGENTS.md`
- Referral Rules: `<path-when-relevant>`

## Architecture and Directories

<Brief current architecture description; may include a concise runtime flow>

| Directory | Responsibility | Local Rules |
|---|---|---|
| | | `<./subdir/AGENTS.md when present, otherwise —>` |

<!-- The directory table lists only paths that currently exist. Durable target-structure constraints belong in Implementation Rules, not as current directory facts. Reference subdirectory AGENTS.md files here rather than duplicating their rules. -->

## Development Commands (build format test)

| Scenario | Command | When |
|---|---|------|

<!-- Record actual entry commands. When reusable project scripts, fixtures or contract helpers exist, name them here or under Testing so agents do not rebuild equivalents. -->

## Quality Gates

<!-- Every gate must be an existing executable command. Do not list a manual review as a quality gate. Wire Doc sync whenever this project maintains docs/DESIGN.md. -->

| Gate | Command | Blocks work when |
|---|---|---|
| Format / lint / type check | `<command>` | `<failure condition>` |
| Unit tests | `<command>` | `<failure condition>` |
| Integration tests | `<command>` | `<failure condition>` |
| Build / package | `<command>` | `<failure condition>` |
| Doc sync / consistency | `<doc-check command, e.g. python3 <dev-doc-master>/scripts/verify-docset.py docs --main DESIGN.md --check-sync>` | `<broken links, orphan sub-DESIGNs, placeholders, missing boundaries, or unsynced Source Carrier code changes>` |

## Implementation Rules

- **Present-state DESIGN sync (unbypassable)**: Read `docs/DESIGN.md` and the owning `docs/DESIGN-<module>.md` before changing module contracts. Whenever observable behavior, public interfaces, config defaults, active business rules, or failure outcomes change, load `dev-doc-master` (and follow `docs/AGENTS.md`) to sync the owning `docs/DESIGN-<module>.md` in the same change and pass the `Doc sync / consistency` gate; skip DESIGN edits on pure internal refactors. During parallel work, edit only authorized module sub-DESIGNs and report cross-module drift to the coordinator instead of touching shared `docs/DESIGN.md`.
- <module ownership and coding-style rule; name the formatter/linter/typecheck entry when applicable>
- <canonical error type, stable fields and side-effect uncertainty rule>
<!-- For CLI/service projects, add concrete rules for success/failure streams, output format, exit codes, log sink, rotated files, recorded fields and forbidden content. For libraries or UI, replace these with the applicable public-contract or user-visible-state rules. -->

## Testing

- <State explicitly that this project inherits the space's canonical testing/TDD rule. If this project has behavior boundaries where TDD is required, name those boundaries here; do not restate the general RED/GREEN decision theory. Add project-specific runners, layers, fixtures/helpers, or host/protocol verification constraints.>
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

- Verify code ↔ tests ↔ owning `docs/DESIGN-<module>.md` (and `proposals/implemented/` when completing a Proposal) stay synchronized; treat missing DESIGN sync on observable contract changes or false "pure-refactor" claims as a blocker.
- <repository-specific checks that complement, not replace, CI and tests>

## User-Supplied Rules

- <user-supplied rules; commands must not modify this section>
- <when updating: original rules that do not fit the sections above should be preserved here verbatim>
