---
name: space-master
description: |
  Root skill and master specification for WopalSpace. Everything a space can do — how it runs, how it is configured, how to write commands/rules/skills/templates — is defined in the ontology repository and distributed to spaces through the central capability pool, with space evolution flowing back through space sync.

  MUST load when:
  - Ontology repo operations: update, sync, capability discovery, PR
  - Space structure maintenance: space init/status, .wopal directory layout, assembly model, how the space runs and is configured
  - Space capability authoring: writing and modifying commands, rules, skills, templates
  - AGENTS.md authoring: creating or updating project/directory AGENTS.md
  - README authoring: creating or updating project-level README.md
  - Skill lifecycle: install, scan, remove
  - Task intent is ambiguous or Wopal is unsure which workflow/skill to use — this is the routing entry point

  [CRITICAL] MUST LOAD whenever interacting with ontology repo operations (update/sync/PR), even if the user does not explicitly say "upstream sync".
---

# space-master

Routes Wopal's decisions for workflow selection, scene-to-skill mapping, ontology maintenance, AGENTS.md maintenance, and the skill lifecycle.

---

## Skill Usage Scenarios

Space skills each serve their own purpose. Choose by scenario; do not stack loads:

| Scenario | Load | Notes |
|----------|------|-------|
| Dev / Fix / Refactor (Issue/Plan driven) | `dev-flow` | Default development workflow; tasks run through its state machine (planning → reviewing → executing → verifying → done) |
| Ontology capability evolution (skills, rules, agents, commands, plugins, assembly under `.wopal/`) | `ontology-evolution` | Object test: ontology capability assets → this skill; code repositories under `projects/` → `dev-flow` |
| Delegate any sub-agent (fae, rook, wsf-*, etc.) | `agents-collab` | MUST load before delegation; covers delegation tool APIs, task lifecycle, two-way communication, progress monitoring, and recovery |
| Create / modify / evaluate a skill | `skill-creator` | MUST load for new, edited, or evaluated skills; includes description optimization and evaluation flow |

This skill directly owns WopalSpace's space governance work — no routing needed:

- **Ontology maintenance**: the central capability pool model, `space sync`, capability discovery, and the upstream PR flow
- **AGENTS.md maintenance**: creating or updating project-level or directory-level AGENTS.md — rule audit, content boundaries, workflow
- **README maintenance**: creating or updating project-level README.md — human-facing project entry documentation, capability-aware conditional document-set alignment
- **Skill maintenance**: the skill lifecycle — install, scan, remove

---

## Ontology Maintenance

### The Central Pool Model

Ontology maintenance revolves around one authoritative line of history:

```
upstream/main  →  local main (central capability pool)  →  space/<name> (assembly worktree)
```

`local main` is the central capability pool — the single source of truth for every capability this machine's spaces can assemble. Each space mounts its own `space/<name>` branch as a `.wopal/` assembly worktree, materialized by sparse-checkout from the assembly manifest. Spaces read from the pool; they do not fork the capability lineage.

Capabilities flow in two directions:

| Direction | Command | What it does |
|-----------|---------|--------------|
| **Downstream** | `wopal ontology update` | Pulls `upstream/main` into `local main` |
| **Space alignment** | `wopal space sync` | Reconciles a space branch with `local main` in both directions |
| **Upstream** | `wopal ontology contribute` | Contributes `local main` changes to `upstream` as a PR |

### Space Sync

`wopal space sync` is the single reconciliation command for a space — it replaces the former `space update` / `space contribute` pair.

It runs in two ordered phases:

1. **Upward first.** Space-unique evolution (capabilities the space added or changed) is integrated into `local main` through an isolated temporary worktree. Success advances `local main`; a conflict stops the sync with the conflict surfaced, leaving both sides untouched.
2. **Downward second.** Once upward is clean, the space fast-forwards to the latest `local main`.

Order matters: integrating upward first means the downward fast-forward always lands on a `local main` that already contains the space's own work, so no change is lost or replayed.

Always preview first, then confirm:

```bash
wopal space sync            # dry-run: show what would move and where
wopal space sync --confirm  # execute
```

Before syncing, check `wopal space status` for the space's divergence from `local main` and its assembly state.

### Capability Discovery and Assembly

Two command families cover the capability surface, with distinct roles:

| Command | Scope | Purpose |
|---------|-------|---------|
| `wopal ontology capability list` | Ontology | Lists every capability the ontology owns, grouped by category — the menu a space assembles from |
| `wopal space capability add/remove` | Space | Adds or removes a capability from this space's assembly and re-materializes it |

`wopal space capability add/remove` updates the space's assembly snapshot and re-runs the materialization. The change can later be contributed as a type archetype so other spaces of the same type inherit it.

The separate `wopal capability` command is unrelated: it exposes the CLI's own machine capability OpenAPI contract.

### Upstream Contribution

Contributing to `upstream` is available in **fork mode** only. In clone mode `origin` points directly at the canonical upstream, so `wopal ontology contribute` is unavailable — guide the user to fork mode if a PR is needed.

```bash
wopal ontology status        # confirm mode and divergence
wopal ontology contribute    # dry-run
wopal ontology contribute --include "a/**,b/**" --message "<message>" --confirm
```

### Contribution Scope Determination

Contribution scope is decided by the USER, never assumed or delegated back:

1. **Present the full menu first.** Enumerate EVERY pending file (`git diff --name-status`), group by directory or feature area, and show the complete inventory to the user BEFORE asking anything. Never ask "what do you want to contribute" before showing what is contributable.
2. **Classify by structure, not intuition.** Ask whether the capability belongs to every space type or to one. When unsure, read the ontology design and check whether the capability already exists on `local main` / `upstream/main`. Do not classify from memory or gut feeling.
3. **User circles the scope, then confirm.** Let the user pick which groups contribute, which exclude, and which stay space-only. Space-only assets (unverified or space-specific skills) never leave the space. No `--confirm` until the user has explicitly confirmed the file scope.

Full procedure and classification detail: `references/ontology-maintenance.md`.

### Topic-Based PR Splitting

**One PR, one topic.** Changes from different directories or feature areas must be split into separate PRs. Contribute dependent PRs first; independent topics in any order.

**Multi-round changes ship in ONE PR.** All accumulated changes to the same topic are contributed together in a single PR — do NOT split them and do NOT ask the user whether to split them.

#### PR message rules

**The message describes WHAT the change delivers, not the action taken.** Write it as the resulting state the reader gets after merge, not the mechanical operation that produced it. Ask: **"What does the reader gain after this merges?"** — answer that, not "what did I do".

- ❌ Action + path: `docs(space-master): add agents-md maintenance guide` (says "I added a guide", not what it contains)
- ✅ Content: `docs(space-master): AGENTS.md maintenance rules and update guidance`
- ❌ Empty action: `docs: sync templates and rules to main` (nothing about content)
- ✅ Content: `docs(templates): concurrency safety protection and sensitive-file read prohibition`

Format: `<type>(<scope>): <content-described-as-result-state>`, a noun phrase describing the delivered capability.

**Repeat full gates for each batch**: every PR goes through the sync analysis and pre-flight gates independently.

### Sync Gates

Every sync operation (`space sync`, `ontology update`, `ontology contribute`) must pass through two gates in order:

#### Gate 1: Sync Analysis

Never auto-sync. The agent must understand the full picture first:

1. `wopal space status` — space-layer divergence and assembly state
2. `wopal ontology status` — ontology-layer divergence (ahead/behind, file-level diff)
3. Follow Contribution Scope Determination: present the full inventory, let the user circle the scope, and get EXPLICIT scope confirmation before any `--confirm` operation. A dry-run inspection is never a substitute for user scope approval.

#### Gate 2: Pre-Flight

Always inspect before pushing:

1. Run **without `--confirm`** first (dry-run)
2. Verify only your changed files appear in the list
3. If wrong, adjust `--include` globs and re-dry-run
4. Only then: re-run with `--confirm`

> Omitting `--include` pushes everything from the branch — all accumulated changes by everyone. There is no undo.
> Eyeball the `exclude` list in dry-run output — excluded files never enter the PR. If a file that should be contributed shows up there, the glob is wrong.

### Ontology Rules

1. **Separate multiple patterns with commas — never chain `--include`.** `--include` is a single-value flag; chaining (`--include A --include B`) keeps only the last one (verified empirically), overriding the others — which pushes the uncovered changes out too (irreversible). Write multiple patterns as `--include "a/**,b/**,c"` (comma-separated, spaces optional). Same for `--exclude`.
2. **Clone mode blocks `contribute`.** Guide the user to fork mode if a PR is needed.
3. **Verify after every operation.** Run `wopal ontology status` and `git diff --stat upstream/main origin/main`.

## AGENTS.md Maintenance

When creating or updating a project-level or directory-level `AGENTS.md`, work by these rules:

1. **Audit existing rules first**: before updating an existing `AGENTS.md`, audit every current rule (per the Rule Audit criteria in the reference):
   - **Delete**: code no longer exists / structure guarantees it (single source of truth) / duplicates an authoritative document / pure implementation fact
   - **Keep**: safety boundaries (deletion scope, single credential write path), behavior constraints, User-Supplied Rules
   - **Fix**: directory descriptions outdated, conflicts with a newer design mechanism, language versions drifted
2. **Plan before writing**: present the audit classification (keep / delete / fix with reasons) plus the proposed change list, and wait for user confirmation
3. **Review version first, formal version second**: update `AGENTS.<locale>.md` first, then the formal English `AGENTS.md` after approval
4. Not updating is the default and legitimate outcome — update only when code, tests, config, and existing docs cannot carry the boundary

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
| `references/ontology-maintenance.md` | Central pool model and mode contracts, status signal interpretation matrix, conflict resolution by file type, remote branch cleanup, contribution scope and PR splitting procedures |
| `references/skills-maintenance.md` | Full lifecycle details, security scan checks, quality evaluation criteria |
| `references/agents-md-maintenance.md` | Full AGENTS.md maintenance specification: content boundaries, rule audit criteria, workflow, quality checklist |
| `references/readme-maintenance.md` | Full README maintenance specification: capability awareness, language version rules, template, quality checklist |
