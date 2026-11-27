---
name: space-master
description: >
  WopalSpace governance and setup skill for space init/layout/config,
  authoring or auditing project/directory AGENTS.md and project README.md,
  and installing/scanning/removing external skills. Use when asked to manage
  space layout or config, run /cupdate-agent-rules or /cupdate-readme, audit
  AGENTS.md quality gates, install/remove skills, or clarify unclear space
  routing. Do not use for authoring PRDs or present-state DESIGNs (use
  dev-doc-master), coding or post-implementation reviews (use df-implement /
  df-implement-review), Plan orchestration (use dev-flow), or ontology repo
  sync and evolutions (load ontology-evolution directly).
---

# space-master

Routes Wopal's decisions for workflow selection, scene-to-skill mapping, ontology maintenance, AGENTS.md maintenance, and the skill lifecycle.

---

## Skill Usage Scenarios

Space skills each serve their own purpose. Choose by scenario; do not stack loads:

| Scenario | Load | Notes |
|----------|------|-------|
| Dev / Fix / Refactor (Issue/Plan driven) | `dev-flow` | Default development workflow; tasks run through its state machine (planning → reviewing → executing → verifying → done). Ontology Issues are the exception — see "Issues: which project, which workflow" below |
| Ontology maintenance (instance updates, space alignment, capability assembly, contribution) | `ontology-evolution` | Load it directly for any ontology repo operation; this skill only routes |
| Ontology capability evolution (skills, rules, agents, commands, plugins, assembly under `.wopal/`) | `ontology-evolution` | Object test: ontology capability assets → this skill; code repositories under `projects/` → `dev-flow` |
| Delegate any sub-agent (fae, rook, wsf-*, etc.) | `agents-collab` | MUST load before delegation; covers delegation tool APIs, task lifecycle, two-way communication, progress monitoring, and recovery |
| Create / modify / evaluate a skill | `skill-creator` | MUST load for new, edited, or evaluated skills; includes description optimization and evaluation flow |

This skill directly owns WopalSpace's space governance work — no routing needed:

- **AGENTS.md maintenance**: creating or updating project-level or directory-level AGENTS.md — rule audit, content boundaries, workflow
- **README maintenance**: creating or updating project-level README.md — human-facing project entry documentation, capability-aware conditional document-set alignment
- **Skill maintenance**: the skill lifecycle — install, scan, remove

---

## Issues: which project, which workflow

Every Issue names the space component it will change through its `--project` / `project/<name>` label. That label decides both where the work lives and which workflow owns it, so choose it by the object being changed, never by the topic.

Choose the label the same way `STRUCTURE.md` names components:

| The Issue changes | `--project` | Workflow |
|---|---|---|
| An ontology component — the ontology worktree itself (`skills/`, `rules/`, `agents/`, `commands/`, `plugins/`, `assembly/`) | That component's project name, read from `STRUCTURE.md` | `ontology-evolution` |
| A repository under `projects/` | That repository's name, read from `STRUCTURE.md` | `dev-flow` |

Read the name from `STRUCTURE.md` rather than assuming it: the ontology project name and the repository set differ per space, and a name that does not match the component sends the Plan or proposal into a directory nothing else points at.

An Issue whose project is the ontology component is ontology work: it goes to a proposal under `docs/evolutions/` and the `wopal space evo` lifecycle. It never takes the dev-flow path — no Plan, no feature branch, no worktree. The Issue remains the record of the demand; the proposal is the implementation authority.

The component path answers the question when the label is ambiguous: if the change lands in the ontology worktree, it is ontology work; if it lands in a repository under `projects/`, it is repository work.

---

## Ontology Maintenance

Ontology maintenance and capability evolution are executed by the **`ontology-evolution` skill** — load it directly for any ontology repo operation: instance updates, space alignment, capability assembly, and upstream contribution all follow its Maintenance Protocols. Loading this skill as well is not required.

It is the single specification point for commands, status, channels/upload gates, execution stance, scope, and native contributions. For upstream PR creation, fixes, or closeout, read that skill's `references/contribution.md`; it owns short branch names, fixed worktree paths, retention through review, and authorized cleanup. Do not duplicate the runbook here.

## AGENTS.md Maintenance

Because agent harnesses automatically inject `AGENTS.md` whenever an agent reads or edits files in that directory tree, tiered `AGENTS.md` files are the **unbypassable ignition switch** for engineering gates and documentation governance. When creating or updating project-, docs-, or directory-level `AGENTS.md`, work by these rules:

1. **Scope by hierarchy, pick the tier template, and audit rules first**: place each rule at the narrowest appropriate level (**space → project → docs / module directory**) with zero cross-tier duplication, selecting the matching template:
   - **Project root (`<project>/AGENTS.md`)** → `templates/agent-rules.md` (wires `Doc sync / consistency` gate & standing present-state `DESIGN` sync rule when `docs/DESIGN.md` exists; when `<project>/docs/` exists in a space assembling `dev-doc-master` and lacks `<project>/docs/AGENTS.md`, proactively propose bootstrapping it in the same confirmation plan)
   - **Docs directory (`<project>/docs/AGENTS.md`)** → `templates/agent-rules-docs.md` (thin 25–45 line harness guardrail card routing to `dev-doc-master` / `dev-proposal`, enforcing present-state, anti-conflict, readability, and fact-check honesty redlines plus the exact `verify-docset.py` gate, and project-local glossary/style conventions; never copies full `dev-doc-master` guides)
   - **Module / subdirectory (`<project>/<dir>/AGENTS.md`)** → `templates/agent-rules-subdir.md` (15–45 lines, created **only** when the directory adds durable local constraints beyond its parent; links parent `AGENTS.md` and owning `docs/DESIGN-<module>.md`)
   Audit every existing rule before editing (criteria in reference Rule Audit):
   - **Delete**: referenced code no longer exists / structure or CI guarantees it / pure design detail with no actionable constraint (a long-lived *working constraint* stays summarized even when DESIGN documents the topic) / pure implementation fact
   - **Keep**: safety boundaries (deletion scope, single credential write path), behavior constraints, long-lived working constraints (logging, output/routing, deployment/release limits, testing and verification, coding discipline), the `Code Review Rules` section (heading kept verbatim, content audited normally), User-Supplied Rules
   - **Fix**: directory descriptions outdated, conflicts with a newer authoritative DESIGN, language versions drifted
2. **Establish executable quality gates with non-empty & +/- evidence**: wire standard formatter, linter/static analysis, type checker, unit runner, integration runner, and (when `docs/DESIGN.md` exists) `Doc sync / consistency` (`verify-docset.py --check-sync` or wrapper) into real project commands with clear failure conditions; when adding or updating a mechanical gate/script, prove it **covers a non-empty real target set and verify at least 1 positive (pass) and 1 negative (fail) case** (preventing silent zero-match passes); leave semantic judgment to independent review rather than fragile regex checks
3. **Run the rules gate after every rules edit**: any created or updated rules file (`AGENTS.md`) must pass `python3 <skill-dir>/space-master/scripts/verify-agents.py <project>/AGENTS.md --base <delivery-base>`. It mechanically checks frontmatter, placeholders, chapter numbering, tier line limits, referenced paths, localized heading/rule/inline-identifier parity, `User-Supplied Rules` immutability, and nested duplication. It cannot judge whether a rule should exist — that stays with semantic review. Projects record it in their `Quality Gates` table
3. **Collect applicable rules by change path**: when acting on a change, gather constraints bottom-up along affected paths and run the minimal sufficient checks; update the rules only when long-lived engineering commands, gates, or hard boundaries change (existing `BUSINESS_RULES.md` files stay read-only historical reference; active rules live in DESIGN)
4. **Plan before writing**: present the audit classification (keep / delete / fix with reasons) plus the proposed change list, and wait for user confirmation
5. **Review version first, formal version second**: update `AGENTS.<locale>.md` first, keeping every heading identical to the English template and translating only the body; after approval, update the formal English `AGENTS.md`
6. **Code Review Rules section**: code projects' root `AGENTS.md` must include a `## Code Review Rules` section — new projects generate it per the template, updates preserve it verbatim (never delete, rename, or translate the heading; documentation-only directories and lightweight module subdirectories inheriting from the project rules omit it). The section carries a direction-level skeleton only: a reference to the review process the project uses, the defect-report boundary, and project-specific checkpoints. The reusable template must not carry any single project's concrete rules
7. Not updating is the default and legitimate outcome — update only when code, tests, config, and existing docs cannot carry the boundary

**Full specification**: `references/agents-md-maintenance.md`.

## README Maintenance

When creating or updating a project-level `README.md` (or a thin consumer `README.md` for an independently published monorepo package — never for ordinary internal source directories whose contracts live in `docs/DESIGN-<module>.md`), work by these rules:

1. **Capability awareness first**: read `.wopal-space/space-meta.json` for the space `type` and the installed skills (`capabilities.skills`); when the metadata is missing, probe the filesystem (does `docs/`, `DESIGN.md`, or `AGENTS.md` exist?). Document-set alignment runs only when the space assembles the relevant documentation-set skills — when it does not, skip alignment and never assume.
2. **Plan before writing**: present the full optimization plan (target file path, one-sentence project description, module / core command overview, sections to add/modify/remove, canonical documents to reference) and wait for explicit user confirmation
3. **Review version first, formal version second**: when the user's preferred language is not English, create `README.<locale>.md` for review first; update the formal English `README.md` after confirmation
4. **Verify commands**: install / run / development commands are always verified from package and config files — never guess

**Full specification**: `references/readme-maintenance.md`.

---

## Skill Maintenance

### Lifecycle

```
find → download → scan → install → evaluate → remove
```

```bash
wopal skills find "<query>"              # Search registries
wopal skills download owner/repo@name    # Download to review inbox
wopal skills scan <name>                 # Security scan (MANDATORY)
wopal skills install /path --force       # Install to runtime
wopal skills remove <name> --force       # Remove from space
```

### Skill Rules

1. **Scan before install.** `wopal skills scan` is mandatory — it checks for malicious code, data exfiltration, and invalid triggers. Never skip it.
2. **Verify after change.** After install or edit: `ls -la .wopal/skills/<name>/SKILL.md` and `wopal skills list`.
3. **Create or modify via `skill-creator`.** Load the `skill-creator` skill for any new skill or edit.

---

## References

The skill body covers the essentials. When troubleshooting or encountering edge cases, **read the reference documents** — they contain the full protocol:

| Document | What you'll find |
|----------|------------------|
| `references/skills-maintenance.md` | Full lifecycle details, security scan checks, quality evaluation criteria |
| `references/agents-md-maintenance.md` | Full AGENTS.md maintenance specification: quality gates, content boundaries, rule audit criteria, workflow, quality checklist |
| `references/readme-maintenance.md` | Full README maintenance specification: capability awareness, language version rules, template, quality checklist |
