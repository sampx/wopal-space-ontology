---
name: space-master
description: |
  Root skill and master specification for WopalSpace. Everything a space can do — how it runs, how it is configured, how to write commands/rules/skills/templates — is defined in the ontology repository and distributed, propagated, and optimized across spaces through the ontology update/contribute/promote flows.

  MUST load when:
  - Ontology repo operations: update, sync, contribute, promote, PR
  - Space structure maintenance: space init/status, .wopal directory layout, how the space runs and is configured
  - Space capability authoring: writing and modifying commands, rules, skills, templates
  - Skill lifecycle: install, scan, remove
  - Task intent is ambiguous or Wopal is unsure which workflow/skill to use — this is the routing entry point

  [CRITICAL] MUST LOAD whenever interacting with ontology repo operations (update/sync/contribute/promote/PR), even if the user does not explicitly say "upstream sync".
---

# space-master

Routes Wopal's decisions for workflows, scene-to-skill mapping, ontology maintenance, and skills lifecycle.

---

## 1. When to Use

| Scene | Load | Notes |
|-------|------|-------|
| Dev / Fix / Refactor (Issue/Plan) | `dev-flow` + `agents-collab` | agents-collab first |
| Delegate any sub-agent | `agents-collab` | MUST load before delegation |
| Ontology ops (sync, contribute, promote) | `space-master` only | Do NOT load dev-flow or agents-collab |
| Create or modify a skill | `skill-creator` | Independent skill |

`dev-flow` is the default development workflow. Tasks must be driven through its state machine: `planning → reviewing → executing → verifying → done`.

---

## 2. Ontology Maintenance

### 2.1 Mode Contract

Before any ontology operation, check the mode:

| Mode | Capability | Origin |
|------|-----------|--------|
| **clone** | `update` (downstream sync) only | upstream repo directly |
| **fork** | `update` + `contribute` (upstream PR) + `promote` | user's fork → upstream |

Command: `wopal ontology status`

### 2.1.1 Capability Tiers: Daily Sync vs Advanced Promote/Contribute

Ontology interaction splits into two tiers with different capability boundaries and confirmation requirements:

| Tier | Operations | Requires | Audience |
|------|-----------|----------|----------|
| **Daily sync (base)** | `update` (downstream), `space contribute` → `ontology contribute` (type PR) | all fork/clone users | ordinary wopalspace product users |
| **Cross-type promote/contribute (advanced)** | `promote` (type/* → main) + subsequent `main` contribution PR | fork mode + upstream repo maintainer | upstream `wopal-space-ontology` maintainer |

**Decision rules**:
- **Complete the regular update and contribution flow first**, then consider promote/contribute. Order: daily sync (`update` + type contribution) → done → then assess whether cross-type promotion is needed.
- **Promote/contribute is an advanced feature that must be explicitly confirmed with the user**: after completing the regular update and contribution, ask the user whether to execute cross-type capability promotion and contribution. Only run `promote` after explicit user agreement. Never default to running it automatically.
- **Ordinary users may only need daily sync**: if the user is an ordinary wopalspace product user (not an upstream maintainer), daily sync suffices — no promote/contribute needed. The agent must not impose promote/contribute as a default flow.

### 2.2 What "Sync Ontology" Means

"Sync ontology" covers both directions — neither is optional:

| Direction | Meaning | Command |
|-----------|---------|---------|
| **Downstream** | Pull latest upstream changes to local | `wopal ontology update --confirm` |
| **Upstream** | Contribute local changes back to upstream | `wopal space contribute` → `wopal ontology contribute` / `wopal ontology promote` |

Sync is not one fixed command sequence. Run downstream updates before starting a contribution batch and after PR merges. Upstream contribution always follows this layer order:

```
space/<name> → local type/* → origin/type/* → upstream PR
```

Use `space status` to identify the files to contribute. When selected files still exist on the space branch, run `space contribute` first. Run `ontology contribute` only after those files have entered local type/*. Do not insert `ontology update` between `space contribute` and the type PR.

### 2.3 Two Contribution Paths

Not all changes follow the same pipeline. Ontology has a three-layer architecture (main → type/* → space/*), and files fall into two status categories:

| Status | Meaning | Examples | Path |
|--------|---------|----------|------|
| **A-status** | Type-specific, exists only in type/* | Domain-specific skills, workflows, integration scripts | **Short path**: 4 steps |
| **M-status** | Generic capability, ultimately lands in main for all spaces | Generic skills, dev workflows, templates | **Long path**: 7 steps |

#### Short Path (A-status, type-specific)

```
space → type → upstream(type) → ✓ done
```

```
0. ontology update      complete pending downstream sync before this batch
1. space contribute     space/* → local type/* → origin/type/*
2. ontology contribute  type/* → upstream(type) (topic PR)
3. ontology update      downstream sync after upstream merge
```

> Type-specific capabilities follow this path. No promote to main needed.

#### Long Path (M-status, generic)

```
space → type → upstream(type) → promote → upstream(main) → ✓ done
```

```
0. ontology update      complete pending downstream sync before this batch
1. space contribute     space/* → local type/* → origin/type/*
2. ontology contribute  type/* → upstream(type) (topic PR)
3. ontology update      downstream sync after type PR merge
4. ontology promote     type/* → main (discuss scope with user first)
5. ontology contribute  main → upstream(main) (topic PR, split per §2.5)
6. ontology update      downstream sync again after main PR merge
```

> Generic capabilities (e.g., generic skills, dev workflows, templates) follow this path. After promote, main branch has new divergence — must contribute to upstream(main) at step 6.

**Key difference**: The long path has 3 extra steps (promote → contribute main → update). It's easy to forget the main PR after promote.

**Post-promote completeness check** (mandatory after step 4): The promote classifier can misclassify newly added files as A-status and exclude them (observed: new test files under `skills/dev-flow/tests/` were missed). Compare the `promote --confirm` output's promote list against the type PR file set item by item; re-add missing files with `--include <files>`.

**Promote backfill timing**: After promote, main is ahead of type/*; another promote errors with `type branch is behind main`. Run `ontology update --confirm` first to sync main → type/*, then retry promote. The backfill `--include` only adds new files; it does not re-promote existing content.

### 2.4 Contribution Scope Determination

Contribution scope is decided by the USER, never assumed or delegated back. Three hard rules:

1. **Present the full menu first.** Enumerate EVERY pending file (`git diff --name-status`), group by directory/feature area, classify each group (M-status / A-status), and show the complete inventory to the user BEFORE asking anything. Never ask "what do you want to contribute" before showing what is contributable.
2. **Classify by structure, not intuition.** M-status (promotable to `main`) = shared by ALL space types; A-status (type-specific) = meaningful to one space type. When unsure whether a file is generic, read `docs/DESIGN.md` and check whether the capability already exists on `main`. Do not classify from memory or gut feeling.
3. **User circles the scope, then confirm.** Let the user pick which groups contribute, which exclude, which stay space-only. Space-only assets (e.g. unverified or space-specific skills) never enter type/* or upstream. No `--confirm` until the user has explicitly confirmed the file scope.

Full procedure and classification detail: `references/ontology-maintenance.md` §Contribution Scope Determination.

### 2.5 Topic-Based PR Splitting

**One PR, one topic.** Changes from different directories or feature areas must be split into separate PRs. This applies to both the type PR and the main PR — promote pushes multiple M-status topics into main at once; re-split them by file directory when contributing.

**Multi-round changes ship in ONE PR.** All accumulated changes to the same topic (from multiple prior contribute commits) are contributed together in a single PR — do NOT split them and do NOT ask the user whether to split them.

#### PR message rules

**The message describes WHAT the change delivers, not the action taken.** Write it as the resulting state the reader gets after merge, not the mechanical operation that produced it. Ask: **"What does the reader gain after this merges?"** — answer that, not "what did I do".

- ❌ Action + path: `docs(space-master): add agents-md maintenance guide` (says "I added a guide", not what it contains)
- ✅ Content: `docs(space-master): AGENTS.md maintenance rules and update guidance`
- ❌ Empty action: `docs: sync templates and rules to main` (nothing about content)
- ✅ Content: `docs(templates): concurrency safety protection and sensitive-file read prohibition`

Format: `<type>(<scope>): <content-described-as-result-state>`, a noun phrase describing the delivered capability.

#### Splitting rules

1. **Isolate by file path**: Changes under the same directory tree usually belong to the same topic
2. **Isolate by feature area**: Changes from different feature areas must not be bundled together
3. **Batch order**: Contribute dependent PRs first; independent topics in any order
4. **Repeat full gates for each batch**: Every PR goes through sync analysis and pre-flight gates independently

Worked example: `references/ontology-maintenance.md` §Topic-Based PR Splitting.

### 2.6 Sync Gates

Every sync operation (`contribute`, `update`, `promote`) must pass through two gates in order:

#### Gate 1: Sync Analysis

Never auto-sync. The agent must understand the full picture first:

1. `wopal space status` — space-layer divergence
2. `wopal ontology status` — ontology-layer divergence (ahead/behind, file-level diff)
3. Present the FULL contributable inventory to the user (per §2.4): every pending file grouped and classified (M/A-status), with a proposed exclusion strategy and PR batches
4. Let the user circle the scope — which groups to contribute, which to exclude, which stay space-only
5. Proceed only after the user has EXPLICITLY confirmed the scope. Scope confirmation is the gate: `--confirm` on any operation is forbidden before the user confirms the file scope.

> Do not run `space contribute --confirm` / `ontology contribute --confirm` / `promote --confirm` until the user has explicitly confirmed the contribution scope. A dry-run inspection is never a substitute for user scope approval.

**Mandatory pre-promote report** (reinforced requirement of this gate):

- **Analyze proactively, don't wait to be asked**: once `wopal ontology status` shows promotable items, the agent must proactively classify them (M-status promotable / A-status type-specific), decide which should be promoted and which should stay in type/*, justify each decision, and present a clear recommendation to the user. Never stay silent or decide autonomously.
- **Promotion boundary must be confirmed with the user**: the full file scope (`--include`/`--exclude` boundaries) and any forced re-inclusion of misclassified files must be listed and confirmed item by item. `promote --confirm` is forbidden before user approval.
- **Explicit PR count and messages**: the analysis must estimate how many PRs the promoted changes will split into (per §2.5 topic splitting), listing each PR's file scope, commit message (`--message`), and order. Only after the user confirms the PR count and messages may the agent run promote and the subsequent main contribution.

#### Gate 2: Pre-Flight

Always inspect before pushing:

1. Run **without `--confirm`** first (dry-run)
2. Verify only your changed files appear in the list
3. If wrong, adjust `--include` globs and re-dry-run
4. Only then: re-run with `--confirm`

> Omitting `--include` pushes everything from the branch — all accumulated changes by everyone. There is no undo.
> Eyeball the `exclude` list in dry-run output — excluded files never enter the PR. If a file that should be contributed shows up there, the glob is wrong.

### 2.7 Ontology Rules

1. **Never auto-sync.** Determine the contribution scope per §2.4 (present full inventory → user circles scope → confirm) and get explicit user confirmation before ANY `--confirm` operation.
2. **Separate multiple patterns with commas — never chain `--include`.** `--include` is a single-value flag; chaining (`--include A --include B`) keeps only the last one (verified empirically), overriding the others — which pushes the uncovered changes out too (irreversible). Write multiple patterns as `--include "a/**,b/**,c"` (comma-separated, spaces optional). Same for `--exclude`.
3. **Promote requires user discussion.** M-status capabilities (shared across spaces) are eligible for promotion; A-status (type-specific) are not. The agent must not decide promote scope autonomously.
4. **Clone mode blocks `contribute`.** Guide the user to fork mode if a PR is needed.
5. **Deletion-risk requires `reconcile`.** When `update` warns about files unique to `type/*` being at risk, run `wopal ontology reconcile --type <type> --theirs --confirm` to preserve them, then retry `update`.
6. **Verify after every operation.** Run `wopal ontology status` and `git diff --stat upstream/main origin/main`.

---

## 3. Skills Maintenance

### 3.1 Lifecycle

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

### 3.2 Skills Rules

1. **Scan before install.** `wopal skills scan` is mandatory — it checks for malicious code, data exfiltration, and invalid triggers. Never skip it.
2. **Verify after change.** After install or edit: `ls -la .wopal/skills/<name>/SKILL.md` and `wopal skills list`.
3. **Create or modify via `skill-creator`.** Load the `skill-creator` skill for any new skill or edit.

---

## 4. AGENTS.md Maintenance

When deciding whether to update a project's `AGENTS.md` after a change, or when following language-version/content-boundary rules for such updates, **read `references/agents-md-maintenance.md`**. Key principle: not updating is the default and legitimate outcome.

---

## 5. References

The skill body covers the essentials. When troubleshooting or encountering edge cases, **read the reference documents** — they contain the full protocol:

| Document | What you'll find |
|----------|------------------|
| `references/ontology-maintenance.md` | Three-layer architecture (main → type/* → space/*), status signal interpretation matrix, conflict resolution by file type, remote branch cleanup |
| `references/skills-maintenance.md` | Full lifecycle details, security scan checks, quality evaluation criteria |
| `references/agents-md-maintenance.md` | When/how to update project AGENTS.md: update triggers, language version rules, content boundary rules |
