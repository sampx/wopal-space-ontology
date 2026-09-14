# Ontology Maintenance & Architecture Reference Manual

This manual provides technical reference for Wopal's central capability pool model, Clone vs Fork distribution mode contracts, signal interpretation, conflict resolution, and remote cleanup operations.

---

## 1. Central Pool Architecture & Mode Contracts

Wopal Ontology employs a single authoritative lineage with a per-space assembly layer:

```
┌─────────────────────────────────────────────────────────┐
│ upstream/main                                           │
│ Canonical source repository (fork or clone source)      │
└─────────────────────────────────────────────────────────┘
                            │ ontology update (downstream)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ local main                                              │
│ Central capability pool — the machine's single source   │
│ of truth for every capability spaces can assemble       │
└─────────────────────────────────────────────────────────┘
                            │ space sync (both directions)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ space/<name> (e.g., space/wopal-workspace)              │
│ Assembly worktree — sparse-checkout of the manifest     │
└─────────────────────────────────────────────────────────┘
```

A space branch is an **assembly worktree**, not a divergent fork of the capability lineage. It materializes the capabilities its archetype selects and holds the space's own evolution until `space sync` integrates it back into `local main`.

### Distribution Mode Contracts (Clone vs Fork Mode)

| Feature / Capability | Clone Mode (`clone`) | Fork Mode (`fork`) |
|----------------------|----------------------|--------------------|
| **Repository Setup** | `origin` points directly to canonical upstream | `origin` points to user's Fork; `upstream` points to canonical upstream |
| **Primary Purpose** | Personal local usage & downstream updates | Contribution, custom releases, and PR workflows |
| **Downstream Sync (`ontology update`)** | Supported (`origin/main` → `main`) | Supported (`upstream/main` → `main`) |
| **Space Alignment (`space sync`)** | Supported (space branch ↔ `local main`) | Supported (space branch ↔ `local main`) |
| **Upstream PR (`ontology contribute`)** | **STRICTLY UNSUPPORTED** | Supported (branch push + PR) |

**Agent Operational Rule**: When `wopal ontology status` reports `Mode: clone`, Agents MUST NOT invoke `wopal ontology contribute`. If the user asks to contribute a PR, explain that Clone mode is read-only for upstream contributions and guide the user to convert to Fork mode first.

### Capability Classification

- **Shared capabilities**: meaningful to every space type — these live on `local main` and are the default eligible set for upstream contribution.
- **Type-specific capabilities**: meaningful only to one space type — these are carried by that type's archetype and assembly, and stay out of the generic set unless the user explicitly wants them shared.

---

## 2. Status Signal Interpretation Matrix

When executing `wopal ontology status`, interpret the analysis sections as follows:

### Section A: Downstream (`upstream → origin → local`)

| Signal | Status | Required Action |
|--------|--------|-----------------|
| `Up to date` | Clean | No downstream action required. |
| `Behind (upstream)` | Local is out of date | Execute `wopal ontology update --confirm` to pull upstream changes. |
| `Pushed: no / partial` | Push to origin failed | Inspect credentials or run `git push origin main` manually. |

### Section B: Space Divergence (`space/<name> vs local main`)

| Signal | Status | Required Action |
|--------|--------|-----------------|
| `Up to date` | Aligned | No action required. |
| `Behind (local main)` | Space is behind the pool | Run `wopal space sync --confirm` to fast-forward. |
| `Ahead (space evolution)` | Space carries unsynced evolution | Run `wopal space sync` — the upward phase integrates it into `local main`. |
| `Diverged` | Both sides moved | Run `wopal space sync`; the upward phase runs in an isolated worktree and stops on conflict. |

### Section C: Upstream (`origin/main → upstream/main`)

| Signal | Status | Required Action |
|--------|--------|-----------------|
| `0 changes` | Fully aligned | No PR required. |
| `Pending changes` | Local/origin has unmerged PRs | Package changes with comma-separated `--include` and run `wopal ontology contribute`. |

---

## 3. Space Sync Execution Model

`wopal space sync` replaces the former `space update` / `space contribute` pair with a single ordered reconciliation:

1. **Upward phase** — space-unique evolution is integrated into `local main` inside an isolated temporary worktree. Success advances `local main`; a conflict stops the sync and surfaces the conflict, leaving both `local main` and the space branch untouched.
2. **Downward phase** — with upward clean, the space fast-forwards to the latest `local main`.

Ordering guarantees the downward fast-forward lands on a `local main` that already includes the space's own work — nothing is lost or replayed.

```bash
wopal space sync             # dry-run preview
wopal space sync --confirm   # execute
```

---

## 4. Conflict Resolution Matrix

When merge conflicts occur during `space sync`, `ontology update`, or a contribution:

| File Type | Conflict Cause | Resolution Strategy |
|-----------|----------------|---------------------|
| `settings.jsonc` | Concurrent config block edits | Keep BOTH configuration blocks. Re-parse JSONC to ensure valid syntax. |
| `AGENTS.md` | Concurrent rule additions | Preserve both sets of rules in hierarchy. |
| `SKILL.md` | Concurrent instruction edits | Keep imperative workflow instructions. Ensure valid frontmatter YAML. |
| `assembly/archetypes/*.yaml` | Concurrent manifest edits | Merge the capability lists; keep the `schema` field consistent with the skeleton actually referenced. |
| Code files | Concurrent implementation edits | Resolve in the isolated worktree, run tests, `git add <file>`, and complete the merge. |

---

## 5. Remote Branch Cleanup & Recovery

* **Automatic Cleanup**: Execution of `wopal ontology update --confirm` automatically detects and deletes merged temporary head branches on `origin`.
* **Manual Fallback**: If remote deletion fails due to network glitches:
  ```bash
  git -C <WOPAL_HOME>/ontologies/wopal-space-ontology push origin --delete <branch-name>
  ```

---

## 6. Contribution Scope Determination

Detailed step-by-step procedure for the SKILL.md section of the same name (the body states the hard rules; this is the how-to).

**Step 1 — Present the full menu first.** Run `git diff --name-status <base>...<target>` to enumerate EVERY pending file. Group by directory/feature area and label each group's classification (shared / type-specific). Show this complete inventory to the user BEFORE asking anything.

**Step 2 — Classify by STRUCTURAL criterion, not intuition.** Shared capabilities = capabilities meaningful to every space type — they belong on `local main`. Type-specific = capabilities meaningful only to one space type (e.g. platform-specific skills, integration scripts). Do NOT classify from memory or gut feeling — when unsure whether a file is generic, read the ontology design (`docs/DESIGN.md`) and check whether the capability already exists on `local main` / `upstream/main`. Space-specific customizations stay in the space and are NOT contributed upstream until the user explicitly wants them shared.

**Step 3 — The user circles the scope.** Present the classified inventory and let the user: (a) decide which groups to contribute, (b) which to exclude, (c) which stay space-only. The agent proposes, the user disposes. Never execute `space sync` / `ontology contribute` until the user has explicitly confirmed the scope.

**Step 4 — Space-only assets stay out.** Skills kept only in the space (e.g. unverified or space-specific skills) must NOT enter `local main` or upstream. If the user says "keep X in the space only", X never appears in any contribution.

---

## 7. Topic-Based PR Splitting (Worked Example)

When `origin/main → upstream/main` shows these pending files:

| File | Topic |
|------|-------|
| `plugins/plugin-a/src/feature-x.ts` | plugin-a new features |
| `plugins/plugin-a/src/feature-y.ts` | plugin-a new features |
| `skills/skill-a/SKILL.md` | skill-a rewrite |
| `skills/skill-b/scripts/helper.py` | skill-b script improvement |

Split into **3 independent PRs**:

```bash
# PR 1: plugin-a feature X and Y
wopal ontology contribute \
  --include "plugins/plugin-a/**" \
  --message "feat(plugin-a): JWT auth and rate limiting for public API"

# PR 2: skill-a rewrite
wopal ontology contribute \
  --include "skills/skill-a/**" \
  --message "feat(skill-a): step-by-step deployment guide with rollback"

# PR 3: skill-b script improvement
wopal ontology contribute \
  --include "skills/skill-b/scripts/helper.py" \
  --message "feat(skill-b): skip empty inputs and dedupe output paths"
```

The message describes WHAT the change delivers (result state), not the mechanical action.
