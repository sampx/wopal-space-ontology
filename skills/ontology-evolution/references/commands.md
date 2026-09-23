# Command Reference

All commands run from the skill root:

```bash
cd <repo>/skills/ontology-evolution
bash scripts/evo.sh <command> [args]
```

`WOPAL_EVOLUTION_REPO_ROOT` overrides root discovery; it exists for tests and
for driving the script against a non-default repository.

Three rules every command obeys:

- **Refuse before writing.** Safety checks run before the first mutation, so a
  rejected command leaves the repository exactly as it found it.
- **Never stage wholesale.** On a checkout whose sparse range has drifted,
  `git add -A` records every out-of-range path as a deletion. Staging is always
  by name, and the range is widened before anything is staged.
- **Guards come from one table.** The stage precondition of every mutating
  command derives from a single guard table; a refusal names the current
  stage, the requirement, and the copyable next command.

## `evo.sh new "<title>"`

Creates `docs/evolutions/<name>.md` at `Stage: draft` from
`templates/proposal.md` — the external skeleton with per-section authoring
comments — and prints the path.

- `<name>` is derived from the title: lowercased, non-alphanumerics collapsed
  to hyphens, a leading `type(scope):` prefix dropped.
- Refuses if the target file already exists; refuses an empty title.
- Options: `--type <type>` (default `enhance`) sets the `Type` metadata field.

The template is the single source of the proposal shape; the placeholder scan
in `check` derives from the same file, so the two cannot drift apart.

## `evo.sh status <name|path>`

Prints the current stage, the resolved file path, the recorded mode, the
isolation metadata (Worktree / Branch / Base Commit / Final Commit once
recorded), and the next command. Accepts a bare proposal name
(`add-keywords-to-memory-rule`), an explicit path, or the bare name of an
archived proposal (resolved against the dated `YYYYMMDD-` form).

```text
Proposal : /space/.wopal/docs/evolutions/add-keywords-to-memory-rule.md
Stage    : implementing
Mode     : isolated
Worktree : .worktrees/ontology-add-keywords-to-memory-rule
Branch   : ontology-add-keywords-to-memory-rule
Base Com : 1a47d0f
Next     : evo.sh advance add-keywords-to-memory-rule --to validating
```

At the terminal stage it prints `none (terminal)` and the `archive` command.

## `evo.sh advance <name> --to <state>`

Moves the proposal to `<state>` after validating the transition.

| From | Legal `--to` |
|------|--------------|
| `draft` | `accepted` |
| `accepted` | `implementing` |
| `implementing` | `validating` |
| `validating` | `archived` |
| `archived` | — (terminal) |

- Re-advancing to the current stage is legal and leaves the file unmodified.
- Any other target (skip, rewind, unknown state) exits non-zero, prints the
  legal successor to stderr, and leaves the file byte-for-byte unmodified.
- A proposal with no `- **Stage**:` field cannot be advanced; recreate it with
  `evo.sh new`.

## `evo.sh accept <name> [--no-worktree]`

Accepts the proposal for implementation and records the mode. Requires the
proposal at `draft`, `accepted`, or `implementing` (the last one exists so a
worktree lost mid-implementation can be re-attached).

**The gate first.** `accept` is where the proposal is read and judged: it
refuses unreplaced placeholders and a missing structure contract (required
sections + the Task six elements) — a proposal that was never actually
written cannot be accepted into implementation.

**Isolated mode (default)** is transactional — every check runs before the
first write, in this order:

1. The space worktree's sparse state is coherent (a corrupted source spawns
   corrupted children; refuse before deriving anything).
2. The isolated worktree is derived from the space branch — or, when the
   branch exists but its worktree directory was lost, **re-attached** to the
   surviving branch (its commits are work, not garbage; recovery never
   suggests deleting it).
3. The isolation assertion: the worktree still sees every pattern the space
   has (a superset is fine), and its bits and range agree.
4. Only then is the metadata (`Mode`, `Worktree`, `Branch`, `Base Commit`,
   `Stage: accepted`) written and committed.

A failure before step 4 removes only the artifacts that run created; a failure
at step 4 restores the proposal file byte-for-byte. `Base Commit` is the
worktree's actual fork point — the derive start commit, or the merge base for
an adopted or re-attached worktree.

**Quick mode** (`--no-worktree`) records `Mode: quick` and creates nothing.
Use it for typo fixes, bug fixes in existing assets, and small changes the
user explicitly scoped — the space branch is itself the isolation boundary
against `local main`.

Re-running `accept` is safe: an existing worktree is adopted when it carries
the expected branch and fast-forwarded onto the space branch head (a worktree
with its own commits is left alone — the squash at integrate reconciles), and
its range is widened back over any pattern the space adopted in the meantime.

## `evo.sh commit <name> -m <message>`

Commits working changes at stage `implementing`, and is the command that
keeps a corrupted sparse checkout from destroying the capability pool.

Checks, in order, before anything is staged:

| Check | Refusal reason |
|-------|----------------|
| Stage is `implementing` | The guard table: committing belongs to implementation only. |
| `core.sparseCheckout` is enabled | A checkout with the range switched off cannot tell an intentional off-disk entry from a deleted one. `disable` writes `false` rather than unsetting the key, so the value is checked, not just its presence. |
| The pattern list is non-empty | An empty range cannot be verified. |
| Nothing is mid-merge | An unresolved merge state cannot be committed coherently. |
| No entry sits outside the range without a skip-worktree bit | The range and the bits disagree. Harmless-looking on its own — `git add -A` still stages nothing while the range is on — but combined with a switched-off range these entries become recorded deletions. |
| No in-range path carries a stray skip-worktree bit | The index and the range disagree; the remedy is `git sparse-checkout reapply`, not a commit. |

Measured, on a temp repository reproducing the layout:

| range | bit | on disk | `git status` | `git add -A` |
|-------|-----|---------|--------------|--------------|
| on | set | no | clean | clean |
| on | clear | no | ` D` | stages nothing (git refuses) |
| off | clear | no | ` D` | **stages the deletion** |

Then it widens the range to cover every changed path **before** staging, and
stages named paths only — never `-A`.

**Isolated mode** commits in the derived worktree (everything the evolution
touched, minus transient build output) and prints the `integrate` command.

**Quick mode** commits into the live space worktree and therefore requires
`--paths <path>...`: an explicit list is the only thing standing between a
stray file and the space branch. The proposal file is added to that list
automatically.

### Why widening is not `--sparse`

`git add --sparse` forces an out-of-range entry into the index but does **not**
widen the range. The next range recompute (`reapply`, or the CLI's
`applySparsePatterns`) then sweeps the file off disk, leaving a committed file
that is invisible to the runtime. Widening first puts the path genuinely inside
the assembly range, where it survives recomputation.

## `evo.sh integrate <name>`

Squashes the isolated work into the space branch inside `.wopal` at stage
`implementing`, and is the only integration path that leaves the space
worktree coherent.

Refusals, all before any mutation:

- Stage is not `implementing`, or `Mode` is not `isolated`.
- The recorded worktree is missing (recovery: re-run `evo.sh accept <name>`;
  it re-attaches the branch — its commits are not lost, do not delete it).
- The recorded worktree sits on a foreign branch.
- The isolation assertion fails on the worktree (re-run as defense in depth —
  accept checked once, drift happens).
- The worktree is dirty, or the space worktree is dirty / incoherent.

Then, in order: the space range is widened to match the feature branch **and
the content it carries**, the squash is staged, and — before anything is
committed — the **corpus assertion** runs: every staged path must fall inside
the final range. A path that would land outside it is the silent-poison shape
(committed, listed, invisible to the runtime, and no later guard can see it);
the integration is rolled back and refused with the offending paths named.
Widening sources can miss (a raw `git add --sparse` path the worktree's range
never declared); the assertion cannot.

After the squash commits, the range is recomputed so newly covered paths are
materialized on disk, and `Final Commit` is recorded in the space-branch copy
of the proposal. Running integrate again with nothing outstanding prints
`no-op` and exits 0.

Why not `git push .` or `git update-ref`: pushing to a branch checked out in
`.wopal` is refused by git, and moving the ref directly leaves `.wopal` in the
same inconsistent `D`/`M` state as the 2026-09-20 incident.

## `evo.sh check <name>`

Reports problems with the proposal and the sparse state as a classified list,
exiting non-zero when anything is wrong.

| Group | Checks |
|-------|--------|
| `metadata:` | `Stage` present and known; `Type`, `Project Path`, `Created` present; `Created` is an ISO date; `Mode` valid once the proposal leaves `draft` |
| `content:` | No unreplaced `<...>` placeholders once the proposal leaves `draft` (code spans excluded) |
| `structure:` | The proposal format contract — required sections and the Task six elements; **notes** in `draft`, problems from `accepted` onward. Also: the space worktree sits on a `space/*` branch |
| `sparse:` | The `commit` preflight, run in whichever directory the mode commits into |
| `isolation:` | The derived worktree still sees every pattern the space has, and its bits are coherent |
| `note:` | Non-fatal observations: content not integrated yet, a branch with nothing committed, placeholders expected in a draft, and **corpus lint** — archived files that lack the `YYYYMMDD-` prefix |

The integration notice compares **content**, not commit counts: the space
branch legitimately carries the accept and stage records the derived worktree
does not.

## `evo.sh archive <name> [--keep-worktree]`

Moves a proposal at stage `archived` into `docs/evolutions/archived/` under
its **dated name** — `YYYYMMDD-<name>.md` (a pure function of date + name;
refuses to overwrite an existing target). Bare names still resolve against
the dated form.

Transactional preflight, all before the first mutation: the space worktree is
coherent and clean, and — when isolation cleanup would run — the feature
branch carries no unintegrated content (deleting a branch that still holds
work destroys it).

The mutation sequence: move → record the move on the space branch (the
undated deletion is staged alongside the dated addition) → mirror into the
worktree. Cleanup runs **last**, only in isolated mode and only without
`--keep-worktree`: the recorded worktree is removed and the feature branch
deleted (`-D`, safe because the content guard proved it integrated). Quick
mode touches no isolation artifacts. Cleanup failure is loud but does not
undo the archive: the residue is reported for manual removal.

## State writes are script-only

`Stage` is written only through `advance` and `accept`. Do not hand-edit the
field: the script refuses to advance a proposal whose field is missing, and a
hand-edited stage bypasses the transition guarantee the state machine exists to
provide.

## Delivery is not a command here

`space sync` and `ontology contribute` are not exposed by this skill. They are
the user's terminal decision (`docs/DESIGN-evolution.md`, Delivery Terminal)
and are invoked by the user, one at a time.
