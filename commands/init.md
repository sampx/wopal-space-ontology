---
description: calibrate space runtime structure
---

# Calibrate Space Runtime Structure

Maintenance command for existing spaces: consume `wopal space scan` to obtain repo / module fact list, generate an update plan against the `STRUCTURE.md` compact schema, verify the runtime skeleton and template diffs, and write changes after user confirmation.

**Input**: `$ARGUMENTS`

**Parameter Notes**: Optional focus area or constraints; full calibration when not provided.

---

## Core Principles

- `/init` is a maintenance entry for existing spaces, not a replacement for `wopal space init`; initialization goes through the CLI.
- Call `wopal space scan` to obtain the fact list of repos / worktrees and `AGENTS.md` module rules; `/init` performs no recursive scanning of its own.
- **Module-level agent rules from scan are a primary input to the managed table** — every project sub-module that owns an `AGENTS.md` must be declared in the managed table.
- **Scan output must be read in full** — never use `head`/`tail` to truncate. When output is long (>200 lines), classify and extract by section (Repositories vs Module-level agent rules) or paginate via `tail -n +N | head -n 100`. Truncation silently drops module entries and produces incomplete calibration.
- Generate frontmatter / table diffs against the compact schema: the managed block may be rewritten by `/init`; the user block is never modified; non-pinned assets deleted by the user from the managed table must not be silently restored.
- The runtime `.wopal-space/` is checked only for the existence of fixed directories and files; do not deep-scan runtime content or write runtime into the table.
- Every write operation must be preceded by a structured report and explicit user confirmation; do not touch any file before confirmation.
- Label each finding: **missing** (does not exist), **drift** (exists but differs from declared structure), **stale** (declared but no longer in scan), or **template-diff** (instance differs from template).

## Declaration Scope — Who Goes Into the Managed Table

| Asset class | In managed table? | Reason |
|---|---|---|
| `.wopal/*` modules (skills, agents, rules, commands, plugins) | Yes | Ontology worktree — space core |
| `projects/<name>/` repo root | Yes | Top-level managed project |
| `projects/<name>/<sub-path>/` with own `AGENTS.md` | **Yes** | Sub-module with own rules — must be indexed |
| `contents/<name>/` | Yes | Top-level content module |
| `scripts/` | Yes | Space-level utility |
| `labs/ref-repos/<name>/` repo root | Ask user | User-decided per repo; typical: only frequently consulted refs |
| `labs/ref-repos/<name>/<sub-path>/` internal | **No** | Internal structure of reference code; belongs to that repo's own docs |
| `labs/research/*`, `labs/fork/*`, `labs/tests/*` | No | Experimental / throwaway code |
| `.wopal-space/backup/`, `.wopal-space/INBOX/` | No | Transient staging |

**Description generation priority for new entries**:

1. `AGENTS.md` frontmatter `description` field (preferred — concise, agent-authored)
2. `package.json` `description` (for npm packages without AGENTS.md)
3. AGENTS.md body first non-empty paragraph (when no frontmatter)
4. Directory name + nearest parent's description as fallback

## Step 1: Collect Context

Read the following sources to build a space state snapshot:

1. `.wopal-space/STRUCTURE.md` — extract frontmatter, managed table, and user table.
2. `wopal space scan` output (text or JSON, whatever the CLI provides). **Read the entire output**; classify by the two sections (`Repositories` and `Module-level agent rules`). If output exceeds 200 lines, use paginated reads (`tail -n +N | head -n 100` or equivalent) — never truncate with bare `head -N`.
3. `.wopal-space/` — verify existence of fixed dirs and files; no deep scanning.
4. Space root — check whether `AGENTS.md` and `.gitignore` exist.
5. `.wopal/templates/` — reference templates for diff comparison.
6. `.wopal/templates/wopalspace-schema.yaml` — canonical layout reference.

If `STRUCTURE.md` does not exist, report and prompt to run `wopal space init` first, then stop.

**Output**: Structure declaration snapshot, scan fact list, runtime existence check results, template diff candidates.

## Step 2: Generate Calibration Plan

1. **Classify scan Module-level agent rules** using the Declaration Scope table. For each entry:
   - Top-level module already in managed table → check description drift
   - `projects/<X>/<sub-path>` with own AGENTS.md → must add to managed table
   - `labs/<*>/<sub-path>` internal → not added (internal to lab repo)
   - Generate description per the priority order above

2. **Frontmatter / managed-table diffs** against the compact schema. For each asset, classify:
   - **missing** — scan fact not declared in managed table (default: add)
   - **drift** — declared but description / type / level mismatch (default: update)
   - **stale** — declared in managed table but no longer in scan (confirm removal with user)

3. **Runtime template-diffs** for files with corresponding templates: summarize user-authored content vs template baseline; never overwrite user content.

4. **Root files (`AGENTS.md`, `.gitignore`) template-diff**: compare against templates; recommend additions only.

**Output**: Structured diff report, each item labeled (missing / drift / stale / template-diff) with handling recommendation.

## Step 3: Report and Confirm

1. Present the full structured report organized by layer: frontmatter → managed table → runtime → root files.
2. Ask questions **only** in these specific cases:
   - Asset exists in managed table but no longer in scan (**stale**) — confirm removal
   - New `labs/ref-repos/<X>` not previously declared — confirm whether to declare (user-decided per the scope table)
   - Description cannot be auto-generated unambiguously (no AGENTS.md and no package.json, or multiple conflicting descriptions) — ask for description
   - Frontmatter `repos` field and managed table disagree on whether to include an asset — ask which is authoritative
3. Wait for explicit user approval before proceeding to write.

**Output**: Change plan waiting for user confirmation.

## Step 4: Write After Confirmation

Execute only the user-approved changes:

1. Create missing directories / files.
2. Update `STRUCTURE.md` managed frontmatter and managed table.
3. Preserve all user-authored content; never overwrite the user block.

**Output**: Updated file paths and change summary.

## Response After Completion

Respond in the user's language with:

1. Updated file paths
2. Change summary (frontmatter / table / runtime layers)
3. Template diffs requiring manual handling
4. Undeclared scan findings with recommendations
