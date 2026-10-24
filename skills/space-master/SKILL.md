---
name: space-master
description: |
  Root skill and master specification for WopalSpace. Everything a space can do — how it runs, how it is configured, how to write commands/rules/skills/templates — is defined in the ontology repository and distributed to spaces through the central capability pool, with space evolution flowing back through space sync.

  MUST load when:
  - Space structure maintenance: space init/status, .wopal directory layout, assembly model, how the space runs and is configured
  - Space capability authoring: writing and modifying commands, rules, skills, templates
  - AGENTS.md authoring: creating or updating project/directory AGENTS.md
  - README authoring: creating or updating project-level README.md
  - Skill lifecycle: install, scan, remove
  - Task intent is ambiguous or Wopal is unsure which workflow/skill to use — this is the routing entry point

  Ontology maintenance and evolution are executed by the `ontology-evolution` skill, not this one: for ontology repo operations (update, sync, capability discovery, contribution, PR), load `ontology-evolution` directly — this skill only routes; loading both is not required.

  [CRITICAL] Load `ontology-evolution` whenever ontology repo operations (update/sync/PR) appear, even if the user does not explicitly say "upstream sync".
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

It is the single specification point — command surface, status reading, channels and the upload gate, execution stance, contribution scope, and **Updating and Returning the Same PR**. For fixes to a published contribution or PR tracking, follow that section to update the original PR; retain its contribution branch until the merged change has returned successfully.

## AGENTS.md Maintenance

When creating or updating a project-level or directory-level `AGENTS.md`, work by these rules:

1. **Audit existing rules first**: before updating an existing `AGENTS.md`, audit every current rule (per the Rule Audit criteria in the reference):
   - **Delete**: code no longer exists / structure guarantees it (single source of truth) / it is a design detail with no actionable constraint (a long-lived *working constraint* stays summarized even when DESIGN documents the topic) / pure implementation fact
   - **Keep**: safety boundaries (deletion scope, single credential write path), behavior constraints, long-lived working constraints (logging, output/routing, host/release/DSH, testing and verification, coding discipline), the `Code Review Rules` section (heading kept verbatim, content audited normally), User-Supplied Rules
   - **Fix**: directory descriptions outdated, conflicts with a newer design mechanism, language versions drifted
2. **Plan before writing**: present the audit classification (keep / delete / fix with reasons) plus the proposed change list, and wait for user confirmation
3. **Review version first, formal version second**: update `AGENTS.<locale>.md` first, then the formal English `AGENTS.md` after approval
4. **Code Review Rules section**: code projects' `AGENTS.md` must include a `## Code Review Rules` section — new projects generate it per the template, updates preserve it verbatim (never delete, rename, or translate the heading; documentation-only directories may omit it). The section carries a direction-level skeleton only: a reference to the space's assembled review skills, the defect-report boundary, and project-specific checkpoints. Only the reusable template must not
   carry any single project's concrete rules
5. Not updating is the default and legitimate outcome — update only when code, tests, config, and existing docs cannot carry the boundary

**Full specification** (content boundaries, workflow, quality checklist) lives in `references/agents-md-maintenance.md`. The `/cupdate-agent-rules` command is an entry point only and carries no specification.

## README Maintenance

When creating or updating a project-level `README.md`, work by these rules:

1. **Capability awareness first**: read `.wopal-space/space-meta.json` for the space `type` and the installed skills (`capabilities.skills`); when the metadata is missing, probe the filesystem (does `docs/`, `DESIGN.md`, or `AGENTS.md` exist?). Document-set alignment runs only when the space assembles the relevant documentation-set skills — when it does not, skip alignment and never assume.
2. **Plan before writing**: present the full optimization plan (target file path, one-sentence project description, module / core command overview, sections to add/modify/remove, canonical documents to reference) and wait for explicit user confirmation
3. **Review version first, formal version second**: when the user's preferred language is not English, create `README.<locale>.md` for review first; update the formal English `README.md` after confirmation
4. **Verify commands**: install / run / development commands are always verified from package and config files — never guess

**Full specification** (capability awareness, template, quality checklist) lives in `references/readme-maintenance.md`. The `/cupdate-readme` command is an entry point only and carries no specification.

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
| `references/agents-md-maintenance.md` | Full AGENTS.md maintenance specification: content boundaries, rule audit criteria, workflow, quality checklist |
| `references/readme-maintenance.md` | Full README maintenance specification: capability awareness, language version rules, template, quality checklist |
