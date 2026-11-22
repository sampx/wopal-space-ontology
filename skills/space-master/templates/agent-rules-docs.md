---
name: <Project> DOCS AGENT RULES
description: Documentation guardrails auto-injected whenever an agent reads or edits files under docs/
maintenance: Update only when project-local doc scripts, glossary terms, target reader conventions, or doc gates change; never copy dev-doc-master templates or guides verbatim here
---

# Documentation Agent Rules

Supplements `../AGENTS.md` with unbypassable documentation rules injected whenever any agent works inside `docs/`.

## Authority and Skill Routing

- Load **`dev-doc-master`** before creating, updating, module-splitting, or reviewing `DESIGN*.md` or `PRD*.md`.
- Load **`dev-proposal`** before creating, approving, moving, or archiving files under `proposals/{proposed,implemented,rejected,archived}/{class}/`.
- Even if a harness or subagent enters `docs/` without loading those skills, every rule below applies unconditionally.

## Non-Negotiable Documentation Rules

- **Present-state truth & active business rules**: `DESIGN.md` and `DESIGN-<module>.md` describe shipped, code/test-verified behavior only. Unbuilt plans belong in `proposals/proposed/<class>/yyyy-mm-dd-<slug>.md`. Fold active business rules, invariants, known limitations, and complete failure outcomes directly into `## Business Rules and Failure Boundaries` (never create standalone `BUSINESS_RULES.md`).
- **Anti-conflict layout**: Keep main `DESIGN.md` thin with a `## Module Architecture` table (`Source Carrier` path prefixes + sub-DESIGN links) and **zero `Sub-DESIGNs` header enumeration**. Every `DESIGN-*.md` carries `Parent: ./DESIGN.md` and must be linked from main body outside `## Reference Documents` (zero orphan sub-DESIGNs). During parallel work, edit only owned module sub-DESIGNs and report out-of-scope drift to the coordinator.
- **Universal coverage & human readability**: Sub-DESIGNs use fixed entry/exit anchors + `1..N` bespoke domain `##` sections satisfying all 5 required elements (actor/trigger, component sequence, `must`/`may`/`must not`, state side effects, complete failure/rollback & recovery). Open with 3–5 plain-language sentences; use concrete facts over abstract buzzwords; never copy file trees or full CLI/API tables; strip AI reasoning transcripts, `WIP`/`deprecated`, and 5+ line paragraph walls.
- **Fact-check honesty**: Verify commands, defaults, paths, and error codes against live code or executed runs; explicitly label any unverifiable claim as untested with its verification condition.

## Verification Gate

Run before reporting any documentation task done and require `RESULT: PASS`:

- Docs consistency: `<resolved command, e.g. python3 <dev-doc-master>/scripts/verify-docset.py docs --main DESIGN.md>`
- Code + docs sync (when accompanying code changes): `<resolved command with --check-sync --base <ref>>`

## Project-Specific Documentation Conventions

<!-- Keep only durable conventions unique to this project (fixed domain glossary, target reader profile, local doc generators, or user-calibrated style rules). Delete this section if none apply yet. -->

- <project-specific terminology, reader audience, or local doc script rule>

## User-Supplied Rules

- <user-supplied rules; commands must not modify this section>
