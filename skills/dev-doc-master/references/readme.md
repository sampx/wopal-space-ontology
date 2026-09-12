# README Reference — Project README Authoring

Create or update project `README.md`. Template is inline below.

## Document Paths and Naming

- Project-level: `<project>/README.md`.
- If the user's preferred language is not English, first create `README.<locale>.md` in the same directory for review; after confirmation, update `README.md`.
- `<locale>` uses an IETF BCP 47 / RFC 5646 tag (e.g. `README.zh-CN.md`).
- The formal English version keeps the unmodified filename `README.md`. Do not generate English variants like `README.en-US.md`.

## Purpose

`README.md` is a human-facing project entry document. It explains what the project is, how to install and run it, what it can do, and where to find durable references. It is not an Agent rule file, not an implementation checklist, and not a design specification.

## Preconditions

Before generating, prefer reading: existing `README.md`, related PRD, related DESIGN, project `package.json` / build / run configuration, main entry files or CLI command definitions, license file or package metadata.

## Core Rules

- Write for human readers in a user-friendly tone.
- Place quick-start and core capabilities first; development commands and reference links later.
- List modules and core entry commands; do not enumerate every subcommand. Point to `--help` for complete usage.
- Do not dive into internal implementation details or Agent-specific implementation rules.
- Technology stack and project structure belong in DESIGN / AGENTS.md; do not duplicate them in README.
- All commands must be verified from package / config files. Never guess.
- Technical References at the end carry reference-only documents (design, product docs, durable references). They are informational links, never mandatory-follow links. Do not repeat a document in both the body and Technical References.

## README Template

```markdown
# <Project Name>

<One-paragraph human-facing description.>

## Quick Start

```bash
<install command>
<run command>
```

## Core Capabilities

| Module | Entry Commands | Purpose |
|---|---|---|

## Development

| Scenario | Command |
|---|---|

## Technical References

| Document | Description |
|---|---|

## License

<license>
```

## Writing Quality Bar

- Explain the project's value in one clear opening paragraph.
- Quick start: executable install and run commands.
- Core capabilities: by module, without implementation detail.
- Development commands: concise table, sources verified.
- Technical references: link durable documents without duplicating content.
- User-preferred language versions use target-language titles.

Forbidden: Agent implementation rules; deep architecture explanations; PRD roadmap duplication; internal task lists or TODOs; unverified commands or guessed package managers; backlog / task plan / command transcript links by default.

## Update Mode

1. Preserve accurate user-facing content.
2. Remove stale commands and obsolete links.
3. Add or correct the module and core command list.
4. Link design and product details; do not duplicate sections.

**Document-set consistency**: the README update is never isolated. The module list and core commands must match the actual project code and stay consistent with the project DESIGN and AGENTS.md. When the README changes what the project is or does, check DESIGN and AGENTS.md for stale claims and align them when affected.

## Confirmation Policy

Before writing or overwriting `README.md`, present the full optimization plan and get explicit user confirmation. The plan must include: target file path; one-sentence project description; module / core command overview; sections to add/modify/remove; canonical documents to reference. Before confirmation, do not write, overwrite, or reorder the formal English `README.md`. If a user-preferred language version was generated first, update it first, then translate the formal English version, keeping semantics aligned.

## Quality Checklist

- [ ] Target project root explicit or safely inferred
- [ ] README is project-level, not directory-level
- [ ] Lists modules and core entry commands, not every subcommand
- [ ] Install / run / development commands verified from project files
- [ ] Capabilities user-facing
- [ ] Technology stack and project structure not duplicated
- [ ] Durable references linked
- [ ] No Agent rule content
- [ ] User-preferred language version generated first (when not English)
- [ ] User-preferred language titles use the target language
- [ ] Full optimization plan shown and confirmed before writing
- [ ] Formal English version updated after confirmation when applicable

## Response After Completion

Respond in the user's language with: updated file path; summary of changes; commands verified or missing; any assumptions or missing durable references.
