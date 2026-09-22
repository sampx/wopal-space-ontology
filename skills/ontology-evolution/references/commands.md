# Command Reference

All commands run from the skill root:

```bash
cd <repo>/skills/ontology-evolution
bash scripts/evo.sh <command> [args]
```

`WOPAL_EVOLUTION_REPO_ROOT` overrides root discovery; it exists for tests and
for driving the script against a non-default repository.

Two rules every command obeys:

- **Refuse before writing.** Safety checks run before the first mutation, so a
  rejected command leaves the repository exactly as it found it.
- **Never stage wholesale.** On a checkout whose sparse range has drifted,
  `git add -A` records every out-of-range path as a deletion. Staging is always
  by name, and the range is widened before anything is staged.

## `evo.sh new "<title>"`

Creates `docs/evolutions/<name>.md` at `Stage: draft` and prints the path.

- `<name>` is derived from the title: lowercased, non-alphanumerics collapsed
  to hyphens, a leading `type(scope):` prefix dropped.
- Refuses if the target file already exists; refuses an empty title.
- Options: `--type <type>` (default `enhance`) sets the `Type` metadata field.

```bash
bash scripts/evo.sh new "Add keywords to memory rule"
# -> docs/evolutions/add-keywords-to-memory-rule.md
```

## `evo.sh status <name|path>`

Prints the current stage, the resolved file path, the recorded mode, and the
next command. Accepts a bare proposal name (`add-keywords-to-memory-rule`) or
an explicit path (`docs/evolutions/add-keywords-to-memory-rule.md`).

```text
Proposal : /space/.wopal/docs/evolutions/add-keywords-to-memory-rule.md
Stage    : draft
Mode     : isolated
Next     : evo.sh advance add-keywords-to-memory-rule --to accepted
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

```text
ERROR: illegal transition draft -> archived; legal next state: accepted
state machine: draft -> accepted -> implementing -> validating -> archived
```

## `evo.sh accept <name> [--no-worktree]`

Accepts the proposal for implementation and records the mode. Requires the
proposal to be at `draft` or `accepted`.

**Isolated mode (default)** derives `<space>/.worktrees/ontology-<slug>` on
branch `ontology-<slug>` from the space branch, then asserts that the derived
worktree can still see every pattern the space worktree has — a superset is
expected, since the worktree widens its own range as it adds capabilities —
and that its range and index agree. The host repository is not touched.

**Quick mode** (`--no-worktree`) records `Mode: quick` and creates nothing. Use
it for typo fixes, bug fixes in existing assets, and small changes the user
explicitly scoped — the space branch is itself the isolation boundary against
`local main`.

In both modes the metadata (`Mode`, `Worktree`, `Branch`, `Base Commit`, plus
`Stage: accepted`) is written and committed to the space branch **before** the
worktree is derived, so the derived copy starts from a tree that already
carries it. Committing it afterwards would leave both copies dirty and make the
squash merge conflict on the proposal file itself.

`Base Commit` is read before that metadata commit, so it names the commit the
work contains and not an annotation about it. `Worktree` is stored relative to
the space root (`.worktrees/ontology-<slug>`), so the record survives the space
being moved.

Re-running `accept` on an already-accepted proposal is a no-op: an existing
worktree is adopted when it carries the expected branch and fast-forwarded onto
the space branch head, so a space branch that moved in the meantime does not
leave the worktree on a stale base.

```text
/space/.wopal/docs/evolutions/add-keywords-to-memory-rule.md
Mode    : isolated
Worktree: .worktrees/ontology-add-keywords-to-memory-rule
Branch  : ontology-add-keywords-to-memory-rule
Stage   : accepted
```

## `evo.sh commit <name> -m <message>`

The only command that writes to the working tree, and the one that keeps a
corrupted sparse checkout from destroying the capability pool.

Checks, in order, before anything is staged:

| Check | Refusal reason |
|-------|----------------|
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

The guard refuses the second row as a warning and the third as the state it
becomes. The tool cannot see a bare `git add -A` typed by hand; it can only
refuse to run one itself, which it does.

Then it widens the range to cover every changed path **before** staging, and
stages named paths only — never `-A`.

**Isolated mode** commits in the derived worktree and prints the `integrate`
command that follows.

**Quick mode** commits into the live space worktree and therefore requires
`--paths <path>...`: an explicit list is the only thing standing between a
stray file and the space branch. The proposal file is added to that list
automatically.

```bash
bash scripts/evo.sh commit add-keywords -m "add keyword list to memory rule"
# commit  : 4f2a91c (2 path(s))
#           skills/memory/SKILL.md
#           docs/evolutions/add-keywords.md
# widened : /skills/memory/
# next    : evo.sh integrate add-keywords
```

An empty change set prints `nothing to commit` and exits 0.

### Why widening is not `--sparse`

`git add --sparse` forces an out-of-range entry into the index but does **not**
widen the range. The next range recompute (`reapply`, or the CLI's
`applySparsePatterns`) then sweeps the file off disk, leaving a committed file
that is invisible to the runtime. Widening first puts the path genuinely inside
the assembly range, where it survives recomputation.

## `evo.sh integrate <name>`

Squashes the isolated work into the space branch inside `.wopal`, and is the
only integration path that leaves the space worktree coherent.

- Refuses unless `Mode: isolated`.
- Refuses when the space worktree is dirty or its sparse state is incoherent.
- Refuses when the derived worktree still has uncommitted changes.
- **Widens the space worktree's range to match the feature branch before
  merging.** Without this the squash records a brand-new capability directory
  as an off-disk skip-worktree entry: committed, listed, and invisible to the
  runtime — an evolution that silently does not load.
- After the squash it recomputes the range (`sparse-checkout reapply`) so the
  newly covered paths are materialized on disk.
- Records `Final Commit` in the space-branch copy of the proposal as a
  follow-up commit. That annotation cannot exist before the squash does.
- Running it again with nothing outstanding prints
  `the space branch already contains every change (no-op)` and exits 0.

Why not `git push .` or `git update-ref`: pushing to a branch checked out in
`.wopal` is refused by git, and moving the ref directly leaves `.wopal` in the
same inconsistent `D`/`M` state as the 2026-09-20 incident.

## `evo.sh check <name>`

Reports problems with the proposal and the sparse state as a classified list,
exiting non-zero when anything is wrong.

| Group | Checks |
|-------|--------|
| `metadata:` | `Stage` present and known; `Type`, `Project Path`, `Created` present; `Created` is an ISO date; `Mode` valid once the proposal leaves `draft` |
| `content:` | No unreplaced `<...>` placeholders once the proposal leaves `draft` |
| `structure:` | The space worktree sits on a `space/*` branch |
| `sparse:` | The `commit` preflight, run in whichever directory the mode commits into |
| `isolation:` | The derived worktree still sees every pattern the space has, and its bits are coherent |
| `note:` | Non-fatal observations: content that is not integrated yet, a branch with nothing committed, or placeholders that are expected because the proposal is still a draft |

A fresh draft is *supposed* to be full of placeholders, so `check` reports them
as a note rather than a failure; from `accepted` onward they are problems.

The integration notice compares **content**, not commit counts. The space
branch legitimately carries the accept and stage records the derived worktree
does not, so a commit-count comparison would fire forever; what matters is
whether any file content is missing from the space branch.

```text
/space/.wopal/docs/evolutions/add-keywords.md: 1 problem(s)
  - sparse: 3 index entr(ies) outside the sparse range carry no skip-worktree bit (skills/ontology-evolution/SKILL.md); the range and the bits disagree, and if the range is switched off these become recorded deletions — commit refused (run `git sparse-checkout reapply` to restore the bits)
  note: 2 path(s) on ontology-add-keywords are not integrated into the space branch yet (skills/memory/SKILL.md)
```

## `evo.sh archive <name>`

Moves a proposal whose stage is `archived` into `docs/evolutions/archived/`
and prints the new path. Refuses a proposal that is not yet `archived`, or one
already inside `archived/`.

## State writes are script-only

`Stage` is written only through `advance` and `accept`. Do not hand-edit the
field: the script refuses to advance a proposal whose field is missing, and a
hand-edited stage bypasses the transition guarantee the state machine exists to
provide.

## Delivery is not a command here

`space sync` and `ontology contribute` are not exposed by this skill. They are
the user's terminal decision (`docs/DESIGN-evolution.md`, Delivery Terminal)
and are invoked by the user, one at a time.
