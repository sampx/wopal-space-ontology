---
name: ontology-evolution
description: |
  Ontology capability evolution workflow, in two lanes. Semantic lane (Maka, proposal-only): friction detection, de-contextualization, the generalization gate, three-tier triage (space-private / type-specific / public core), and the Evolution Plan output format. Mechanism lane (Wopal orchestrating, Fae implementing, Rook gating): proposal state machine via the CLI `wopal space evo` command family, sparse-isolation implementation discipline, runtime validation, and user-owned delivery.

  MUST load when:
  - Distilling a session's lessons, errors, or user corrections into lasting capability
  - Deciding where a piece of knowledge belongs (space memory vs type assembly vs central pool)
  - Producing an evolution proposal for user approval
  - Auditing a candidate capability for project-specific contamination before it enters the pool
  - Advancing an evolution proposal through its stage machine, or checking an evolution's status
  - Implementing a change to the ontology's own capabilities (skills, rules, agents, commands, plugins, assembly)
  - Creating, updating, distributing, or contributing ontology capability assets in a space
  - Any "evolution proposal / 进化提案 / evolution stage / capability evolution" request

  Object test: ontology capability assets (this space's own skills, rules, agents, commands, plugins, assembly, docs/evolutions) -> this skill. Code repositories under `projects/` -> dev-flow, never this one.

  The semantic lane is Maka-exclusive. This skill defines how the evolution heart does its work; the maka agent file defines who Maka is.
---
# ontology-evolution

The workflow that turns runtime facts into living capability — and the machinery that lands that capability in the ontology without corrupting the pool.

Two lanes, non-overlapping, meeting at one artifact:

| Lane | Owner | Produces |
|------|-------|----------|
| **Semantic** | Maka (proposal-only) | Friction detection, de-contextualization, generalization gate, three-tier triage → an **Evolution Plan** |
| **Mechanism** | Wopal (orchestration), Fae (implementation), Rook (gate) | Proposal on disk, stage transitions, isolated implementation, runtime validation, delivery decision |

The Evolution Plan is the mechanism lane's input — it is not a code task.

---

# Semantic Lane (Maka)

The semantic lane decides *what deserves to survive and where it belongs*. It ends at a proposal: Maka may write and refine proposals under `docs/evolutions/`, and touches no capability asset.

## The Evolution Loop

```
Runtime facts (session events / errors / user corrections)
  → Detect friction worth distilling
  → De-contextualize: strip the specific, keep the general
  → Generalization gate: does this hold beyond this space?
  → Three-tier triage: space-private / type-specific / public core
  → Emit Evolution Plan for user approval
```

You stop at the Evolution Plan. Landing it belongs to the mechanism lane.

## Step 1: Detect Friction

| Signal | What it looks like | Why it matters |
|--------|-------------------|----------------|
| Repeated correction | User corrects the same behavior more than once | A rule is missing or unclear |
| Error with a lesson | A failure exposes a wrong assumption | A guardrail should exist |
| Unclear instruction | A workflow step needed clarification | Documentation or routing gap |
| Wasted effort | The same helper or approach rebuilt repeatedly | A capability should be extracted |
| Effective pattern | Something worked notably well | Worth preserving so it recurs |

Not every event is evolution material. Routine task completion is not a lesson. Look for the moment where behavior should have been different.

## Step 2: De-Contextualize

- Absolute paths (`/Users/<name>/...`, `/Volumes/...`) → abstract placeholders or nothing
- Project names, product names, client names → generic terms
- Business domain words that only matter here → removed
- Session-specific IDs, timestamps, commits → removed

The test: could a reader who has never seen this space understand and apply the lesson? If not, it is not yet de-contextualized.

## Step 3: The Generalization Gate

1. **Does this hold in a different space?** If it only holds here, it is space-private.
2. **Does it hold for a different project of the same type?** If yes, it is type-specific.
3. **Is it true for any space of any type?** If yes, it may be public core.

A "maybe" is not a "yes". When uncertain, place it lower in the hierarchy. A local lesson that later proves general can be promoted; a polluted pool is hard to clean.

## Step 4: Three-Tier Triage

| Tier | Destination | Owner | Examples |
|------|-------------|-------|----------|
| **Space-private** | `.wopal-space/memory/` or project `AGENTS.md` | The space | Project-specific architecture rules, local conventions |
| **Type-specific** | `config/types/<type>.yaml` assembly or type-scoped assets | The type | Rules that hold for every coding space but not content spaces |
| **Public core** | Central pool (`agents/`, `skills/`, `rules/`) | The pool | Cross-space principles, general workflows |

Misplacement is the main failure mode. A coding convention placed in public core pollutes content spaces. A general principle buried in one space's memory never benefits anyone else.

## Step 5: Emit the Evolution Plan

Your only output is a plan for user approval:

```markdown
# Evolution Plan

## Summary
<one paragraph: what was observed, what should change>

## Candidates

### Candidate N: <short title>
- **Tier**: space-private | type-specific | public core
- **Evidence**: <session fact, error, or correction, with concrete detail>
- **De-contextualized form**: <the generalized statement>
- **Proposed change**: <what asset changes, and how>
- **Generalization basis**: <why this tier, not a lower one>

## Risks
<anything that could make this proposal wrong or premature>

## Recommended Next Steps
<if approved: which asset, in which space, to be implemented by Fae>
```

Keep candidates few and well-argued. Three strong proposals beat ten weak ones.

---

# Mechanism Lane

The mechanism lane lands an approved plan. Its discipline is enforced by the CLI mechanism, not by prose: refusing before the first write, staging by name, the guard table, the isolation assertion, and the integrate corpus assertion. This document records what the mechanism cannot enforce: roles, user decision points, and the validation philosophy.

The lane's operation surface is the `wopal space evo` command family; its contract is `projects/wopal-cli/docs/DESIGN-evolution.md`.

## Roles

| Role | Does | Does not |
|------|------|----------|
| **Maka** | Detects friction, emits the Evolution Plan, refines it under `docs/evolutions/` | Touch capability assets, run the state machine |
| **Wopal** | Accepts the plan, decides the mode, orchestrates, owns delivery decision | Implement assets by hand |
| **Fae** | Lands the change, commits on the space branch | Move the proposal's stage |
| **Rook** | Audits the deliverable before it moves on | Fix anything |

## State machine

```
draft → accepted → implementing → validating → archived
```

| Stage | Meaning |
|-------|---------|
| `draft` | Proposal is on disk under `docs/evolutions/`, waiting for the user to read it |
| `accepted` | User accepted; the isolated worktree exists and the mode is recorded |
| `implementing` | Work is being landed: implementation commits in the isolated worktree (or quick-mode commits on the space branch) |
| `validating` | The change is integrated onto the space branch; the user restarts and observes |
| `archived` | User confirmed; the proposal is filed away |

`accepted → implementing` and `validating → archived` are the only forward edges. Review does not occupy a stage: it happens when the user asks for it, and it does not invent a state. There is no backward edge — if a landed change must be reworked, the fix is a new commit, not a stage rewind.

**The vocabulary is deliberate.** `planning / reviewing / approved / executing / verifying / done` belongs to `dev-flow`; this workflow uses its own five words so an agent cannot mistake one workflow for the other. Never "unify" the two.

## Proposal commands

Run from the space root: `wopal space evo <command> [args]`.

| Command | Does |
|---------|------|
| `wopal space evo new "<title>"` | Creates `docs/evolutions/<name>.md` from `templates/proposal.md` at `Stage: draft`; the naming contract in that template governs the title |
| `wopal space evo status [name]` | Lists the active proposals, or shows one proposal's stage and recorded metadata |
| `wopal space evo check <name\|path>` | Diagnoses the proposal (metadata, placeholders, structure) and the space worktree's sparse shape |
| `wopal space evo advance <name> --to <state>` | Advances the state machine; refuses illegal transitions |
| `wopal space evo accept <name> [--no-worktree]` | Gates the proposal (placeholders + structure), then derives or re-attaches the isolated worktree transactionally |
| `wopal space evo commit [<name>]` | Sparse-safe commit at `implementing`; widens the range first, stages by name. Without a name: instant mode, the defect repair path |
| `wopal space evo integrate [name]` | Squashes the isolated work into the space branch; refuses invisible content (corpus assertion) |
| `wopal space evo archive <name> [--keep-worktree]` | Moves an `archived` proposal to `docs/evolutions/archived/YYYYMMDD-<name>.md`, cleans up isolation artifacts |

Properties the command family guarantees — enforced by the CLI mechanism, not by prose:

- **Stage is written only by commands.** Never hand-edit `- **Stage**:`; a proposal whose field cannot be found cannot be advanced.
- **Refusal precedes mutation.** Every safety check runs before any write; a rejected command leaves the repository exactly as it found it.
- **Nothing is ever staged wholesale.** Staging is by name and the range widens first; no command stages `git add -A`.
- **Re-running is safe.** Re-advancing is a no-op; re-accept adopts or re-attaches instead of fighting existing state.

Command-level detail — including the shared `commit`/`integrate` preflight — lives in `references/commands.md`.

## Sparse isolation discipline

Default implementation mode: **derive a worktree from `.wopal`**. The derived worktree inherits the space's sparse assembly patterns, so the implementation boundary equals the capability set the space is entitled to — and the host repository never switches branches.

Seven hard constraints:

1. **Isolate by default.** Derive the worktree from `.wopal` (the sparse source); `accept` asserts the derivation is a faithful sparse copy of the space.
2. **The host repository never switches branches.** It carries the base capabilities other spaces depend on and stays on `main`.
3. **Merge on the space branch.** The merge happens inside `.wopal`, on the space branch, as a single squash after validation.
4. **New capability directories are assembled first.** Widening happens before staging, and the space range adopts the feature's range at integrate — verified by the corpus assertion, which refuses any path that would land invisible.
5. **Never clear the `S` bits in bulk.** skip-worktree is derived state of the assembly range; adjust visible scope only by widening assembly. The commit/integrate preflight verifies the range instead of trusting discipline.
6. **Validation means restarting and observing.** For anything touching the load path, the verdict is what the user sees after restarting ellamaka. A green test is not a substitute for observing the loaded behavior.
7. **Delivery is the user's terminal decision.** `space sync` and `ontology contribute` are called one at a time, at the user's word. The skill contains no automatic upstream path — by design, not by omission.

### Quick mode

Typo fixes, bug fixes in existing assets, and small changes the user explicitly scopes may be committed in small steps directly on the `.wopal` space branch — the space branch is itself the isolation boundary against `local main`. When the judgment is unclear, use isolated mode. Widening scope is a user decision, not an agent's convenience.

### Defect repair is immediate

A **defect** is existing, already-agreed behavior that is wrong. Repairing it restores the intent that was already approved — it adds no design surface, so it does not go through the proposal lifecycle. Routing a defect through `new → accept → … → archive` costs a full design review for a change nobody needs to review; the record that matters is the commit.

The fast path is `wopal space evo commit` in **instant mode** — no proposal name, with `-m <message>` and exactly one of `--paths <p>...` / `--all`:

- It commits **directly on the space branch** — the branch is the isolation boundary against `local main`, exactly as in quick mode.
- It still refuses on an incoherent sparse state, widens the range before staging, and stages by name. The fix path is a shortcut past the *process*, never past the *safety*.
- It leaves no proposal artifact and moves no stage. The commit is the record.

Instant mode is the **designed** repair path — chosen by decision, not a gap. A separate `fix` command was retired on purpose: do not reintroduce it, and do not add an alias or a shim. That retirement also moved `fix`'s shadow-registration duty to `capability remove --local`.

The distinction matters: a defect **fixes** agreed behavior; anything that **changes** behavior — a new capability, a contract change, a workflow step that should behave differently — is an evolution and follows the proposal lifecycle. When you cannot tell which you have, ask. Choosing the fast path for a change that deserved review is worse than a slow path for a fix.

## Landing an evolution

```
Evolution Plan (approved)
  → wopal space evo new "<title>"                    # draft from the external template
  → user reads the proposal
  → wopal space evo accept <name>                    # gate + isolated worktree
  → wopal space evo advance <name> --to implementing
  → implement, then wopal space evo commit <name>    # sparse-safe, per task
  → wopal space evo integrate <name>                 # squash onto the space branch
  → wopal space evo advance <name> --to validating
  → user restarts ellamaka and confirms
  → wopal space evo advance <name> --to archived
  → wopal space evo archive <name>                   # dated name + isolation cleanup
  → delivery decision (space sync / ontology contribute) — user only
```

In quick mode, skip `integrate`: `wopal space evo commit <name>` lands directly
on the space branch, which is itself the isolation boundary.

`integrate` runs once, after implementation. Squashing after every commit does
not work: squash creates new commit ids, so the next squash loses its merge
base and fails with add/add conflicts. Rework after integrate is a new commit
on the space branch, not a second squash.

---

# Maintenance Protocols

Beyond the evolution lifecycle, this skill owns the ontology's maintenance
surface: instance updates, space alignment, and capability assembly. These
commands share one command surface with the evolution mechanism.

## Command surface

| Command | Direction | Responsibility |
|---------|-----------|----------------|
| `wopal space status` | — | Read-only: space branch vs `local main` (to contribute / behind), remote delta, assembly snapshot health, local state lists (added / shadowed / unregistered) |
| `wopal space sync [--confirm]` | both | Align with `local main`: integrate space-unique evolution upward (isolated worktree, stops on conflict), then fast-forward down |
| `wopal space capability add/remove <kind>:<name> [--local]` | manifest / local | Shared channel: edit the archetype manifest and re-materialize; accepts only a capability the pool already owns (a pool-absent name is refused before the manifest is touched) and creates **no Git commit** — committing the manifest is a separate, explicit step. `--local`: hold or drop as space-private state — zero commits, never syncs |
| `wopal ontology capability list` | — | Read-only: what the pool owns — the pick-list for `space capability add` |
| `wopal ontology update [--confirm]` | downstream | `upstream/main` → `local main` |
| `wopal ontology contribute --message <msg> [--include/--exclude <glob>] [--confirm]` | upstream | `local main` → upstream PR (fork mode; squash-merge in an isolated worktree; `--resume` / `--abort` for a conflict) |

## Reading status

`wopal ontology status` reports both flows: **Downstream**
(`upstream → origin → local main`) and **Upstream**
(`local main → origin → upstream`), the latter as the pending file set.

`wopal space status` reports the space link: **to contribute** vs **behind
local main**, the assembly snapshot state, and the **local state lists** —
`added` / `shadowed` / unregistered untracked files. Local-state paths are
space-private by construction: they never travel to `local main`.

## Channels and the upload gate

`space capability` has two channels. Without `--local` the change edits the
assembly manifest and re-materializes — but it creates no commit by itself, and
it only accepts a capability the pool already owns, so committing the manifest
is a separate step. With `--local` it only writes the space's `localState`
(`added` / `shadowed`) and adjusts the sparse range — zero commits,
structurally unable to sync up; `add --local` on a shadowed capability is also
the recovery exit.

Before integrating upward, `space sync` checks the **upload gate**: no
space-unique commit may touch a `localState` path (added ∪ shadowed). A hit
refuses the sync and names the remedy — withdraw the commit or drop the
registration. The gate is the backstop for a manual `git add`/`commit` of
local-state content: local isolation does not depend on the operator
remembering.

## Execution stance

The CLI defaults to dry-run preview; `--confirm` executes. Per the settled
stance: the agent acts on the user's intent directly and passes `--confirm` —
no extra approval gate is layered on top. `--dry-run` is a diagnostic, not a
precondition. Safety comes from mechanics: isolated integration, fast-forward
only, stop-on-conflict, worktree checks — the worst case is a change not
happening, not a broken worktree. `ontology contribute` is the single
exception: each contribution is the user's call, one at a time (Delivery
Terminal).

## Contribution scope and themed PRs

Scope is determined with the user, from evidence:

1. Enumerate every pending path first (`git diff --name-status
   <base>...<target>`), grouped by directory / feature area, each group
   labelled shared or type-specific — show the full inventory before asking
   anything.
2. Classify structurally, not by feel: shared = meaningful to every space
   type; type-specific = meaningful to one type only. When unsure, check the
   pool (`ontology capability list`) and the ontology design instead of
   guessing.
3. The user circles the scope: which groups travel upstream, which are
   excluded, which stay space-only.
4. Space-only assets never appear in any contribution.

One PR per topic: `--include` / `--exclude` carve a coherent contribution out
of the pending set, and `--message` states what the change delivers (result
state), not the mechanical action. Split unrelated work; never bundle it.

---

# Boundary

The lane boundary, and the boundary against neighboring entry points:

- **Semantic lane — propose only.** Proposals under `docs/evolutions/`; never touch a capability asset, never commit, never implement. Every proposal waits for explicit user approval. A speculative proposal presented as fact is worse than no proposal. Violating this = **CRITICAL FAILURE**.
- **Mechanism lane — propose, land, gate.** Wopal decides and orchestrates; Fae implements; Rook audits. The lane never ships upstream on its own.
- **`/wopal:evolve` and `/wopal:distill`** are user-facing entry commands that arrive at this skill's mechanism lane; they do not bypass the state machine or the user decision points.
- **`wopal/ontology-maintain`** is a thin trigger: it loads this skill with a focus argument and carries no protocol of its own — maintenance operations are defined by the **Maintenance Protocols** above.
- **The mechanics belong to the CLI.** Maintenance runs through the `wopal space` / `wopal ontology` commands, and the mechanism lane's operation surface is the `wopal space evo` family (contract: `projects/wopal-cli/docs/DESIGN-evolution.md`); a defect is repaired with `wopal space evo commit` in instant mode.
- **Assembly overlay**: assets here are assembled per space via the overlay mechanism (`docs/DESIGN-distribution.md`); the skill operates on the assembled worktree (`.wopal`), never on the central pool directly.

The separation exists because a proposal that its own author can silently implement is no longer a proposal.

---

# References

- State machine and delivery terminal: `docs/DESIGN-evolution.md` (Capability Evolution Workflow)
- Command contract and stage semantics: `references/commands.md`
- Sparse isolation background: `docs/DESIGN-distribution.md`
- Development and test conventions for this skill: `AGENTS.md`
