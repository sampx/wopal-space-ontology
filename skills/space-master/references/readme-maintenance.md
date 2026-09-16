# README Maintenance

The authoritative specification for creating and updating a project-level `README.md`. This is a public documentation workflow for space content — every space owns projects, and every project can carry a human-facing README. The SKILL.md body only routes to this document; all details live here.

## 1. When to Use

Create or update a project's `README.md`. The README is a human-facing project entry document: what the project is, how to install and run it, what it can do, and where durable references live. It is not an Agent rule file, not an implementation checklist, and not a design specification.

## 2. Capability Awareness

This skill is assembled into every space; the documentation ecosystem around it varies by space type. Before updating a README, check what the space actually has — never assume.

- Read the space metadata at `.wopal-space/space-meta.json`.
- Use `type` to know the space kind and `capabilities.skills` for the installed skill set. When the metadata file is missing, probe the filesystem instead: does `docs/` exist next to the project? Are there `DESIGN.md` / `AGENTS.md` files?
- **Document-set alignment is conditional.** When the space assembles documentation-set skills (e.g. `dev-doc-master` or `dev-flow`, or a `docs/products/` tree exists), the README must stay consistent with the design documents they own. When the space does not assemble those skills, skip document-set alignment entirely — a README in a skill-less space only needs to be self-consistent and match the actual project code.
- A missing skill is a legitimate state, not an error. If a related skill is absent, ignore the rules it would have contributed and proceed with the self-contained rules below.

## 3. Language Version and Naming Rules

- Project-level README: `<project>/README.md`.
- If the user's preferred language is not English, first create `README.<locale>.md` in the same directory for review; after confirmation, update `README.md`.
- `<locale>` uses an IETF BCP 47 / RFC 5646 tag (e.g. `README.zh-CN.md`).
- The formal English version keeps the unmodified filename `README.md`. Do not generate English variants like `README.en-US.md`.
- Preferred-language version titles use the target language.

## 4. Preconditions

Before generating, prefer reading: existing `README.md`, related project docs, project `package.json` / build / run configuration, main entry files or CLI command definitions, license file or package metadata.

## 5. Core Rules

- Write for human readers in a user-friendly tone.
- Place quick-start and core capabilities first; development commands and reference links later.
- List modules and core entry commands; do not enumerate every subcommand. Point to `--help` for complete usage.
- Do not dive into internal implementation details or Agent-specific implementation rules.
- Technology stack and project structure belong in the project spec (e.g. `AGENTS.md`) and design documents when those exist; do not duplicate them in README.
- All commands must be verified from package / config files. Never guess.
- Technical References at the end carry reference-only documents (design doc, product docs, durable references). They are informational links, never mandatory-follow links. Do not repeat a document in both the body and Technical References.

## 6. README Template

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

## 7. Writing Quality Bar

- Explain the project's value in one clear opening paragraph.
- Quick start: executable install and run commands.
- Core capabilities: by module, without implementation detail.
- Development commands: concise table, sources verified.
- Technical references: link durable documents without duplicating content.

Forbidden: Agent implementation rules; deep architecture explanations; roadmap duplication; internal task lists or TODOs; unverified commands or guessed package managers; backlog / task plan / command transcript links by default.

## 8. Update Mode

1. Preserve accurate user-facing content.
2. Remove stale commands and obsolete links.
3. Add or correct the module and core command list.
4. Link design and product details; do not duplicate sections.

**Document-set consistency** (only when the space assembles the relevant skills, per §2): the README update is never isolated. The module list and core commands must match the actual project code and stay consistent with the project `AGENTS.md` and design docs when they exist. When the README changes what the project is or does, check them for stale claims and align when affected.

## 9. Confirmation Policy

Before writing or overwriting `README.md`, present the full optimization plan and get explicit user confirmation. The plan must include: target file path; one-sentence project description; module / core command overview; sections to add/modify/remove; canonical documents to reference. Before confirmation, do not write, overwrite, or reorder the formal English `README.md`. If a user-preferred language version was generated first, update it first, then translate the formal English version, keeping semantics aligned.

## 10. Quality Checklist

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
- [ ] Document-set alignment applied only when the space assembles the relevant skills (metadata check per §2)

## 11. Response After Completion

Respond in the user's language with: updated file path; summary of changes; commands verified or missing; any assumptions or missing durable references; which document-set alignment steps were applied or skipped (and why, when skipped).