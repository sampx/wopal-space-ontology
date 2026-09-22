---
name: ontology-evolution
description: |
  Ontology capability evolution workflow, in two lanes. Semantic lane (Maka, proposal-only): friction detection, de-contextualization, the generalization gate, three-tier triage (space-private / type-specific / public core), and the Evolution Plan output format. Mechanism lane (Wopal orchestrating, Fae implementing, Rook gating): proposal state machine via `evo.sh`, sparse-isolation implementation discipline, runtime validation, and user-owned delivery.

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

The mechanism lane lands an approved plan. It is deliberately thin: one script plus a markdown status field — no issue layer, no worktree-manager layer. Isolation is done with git primitives under discipline; the script only moves state.

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
| `accepted` | User accepted; implementation may begin |
| `implementing` | Change is being landed on the space assembly worktree |
| `validating` | Change is committed; waiting for the user to confirm in the running system |
| `archived` | User confirmed; proposal is filed away |

`accepted → implementing` and `validating → archived` are the only forward edges. Review does not occupy a stage: it happens when the user asks for it, and it does not invent a state. There is no backward edge — if a landed change must be reworked, the fix is a new commit, not a stage rewind.

**The vocabulary is deliberate.** `planning / reviewing / approved / executing / verifying / done` belongs to `dev-flow`; this workflow uses its own five words so an agent cannot mistake one workflow for the other. Never "unify" the two.

## Proposal script

Run from the skill root: `bash scripts/evo.sh <command> [args]`.

| Command | Does |
|---------|------|
| `evo.sh new "<title>"` | Creates `docs/evolutions/<name>.md` with `Stage: draft` |
| `evo.sh status <name\|path>` | Prints current stage, file path, mode, and the next command |
| `evo.sh accept <name> [--no-worktree]` | Records the mode and derives the isolated worktree |
| `evo.sh advance <name> --to <state>` | Advances the state machine; refuses illegal transitions |
| `evo.sh commit <name> -m <msg>` | Sparse-safe commit; the only command that writes the working tree |
| `evo.sh integrate <name>` | Squashes the isolated work into the space branch inside `.wopal` |
| `evo.sh check <name>` | Reports proposal and sparse-state problems |
| `evo.sh archive <name>` | Moves an `archived` proposal to `docs/evolutions/archived/` |

Rules that make this safe to rely on:

- **Stage is written only by the script.** Never hand-edit `- **Stage**:` in a proposal. A hand-edited stage defeats the point of a script-owned state machine, and the script will refuse to advance a proposal whose field it cannot find.
- **Illegal transitions exit non-zero and change nothing.** A skip (`draft → archived`) or a rewind (`validating → implementing`) prints the legal successor to stderr and leaves the file byte-for-byte untouched — so a mistaken command has no recovery cost.
- **Refusal happens before the first write.** Every safety check runs before any mutation, so a rejected `commit` or `integrate` leaves the repository exactly as it found it.
- **Nothing is ever staged wholesale.** Staging is by name, and the sparse range is widened first. `git add -A` over a drifted range is the one instruction that records a whole capability pool as deleted; no command in this skill issues it.
- **Re-running is safe.** Re-advancing to the current stage is a no-op; re-running `accept` adopts the existing worktree and fast-forwards it rather than fighting it.
- **`commit` and `integrate` share one preflight.** Both refuse on a disabled range, an empty pattern list, an unresolved merge, an out-of-range entry missing its skip-worktree bit, or an in-range path carrying a stray one.
- **The repository root is discovered from the script's own location**, so the same script works from `.wopal` and from an isolated worktree, with no hard-coded path.

Command-level detail lives in `references/commands.md`.

## Sparse isolation discipline

Default implementation mode: **derive a worktree from `.wopal`**. The derived worktree inherits the space's sparse assembly patterns, so the implementation boundary equals the capability set the space is entitled to — and the host repository never switches branches.

Seven hard constraints:

1. **Isolate by default.** Derive the worktree from `.wopal` (the sparse source). After deriving, assert that it can still see every pattern `.wopal` has (a superset is fine — the worktree widens its own range as it adds capabilities) and that its bits and range agree. Deriving from the full host repository does *not* inherit the patterns.
2. **The host repository never switches branches.** It carries the base capabilities other spaces depend on and stays on `main` — `~/.wopal/ontologies/<source>/` must be found on `main` before and after any work.
3. **Merge on the space branch.** The merge happens inside the worktree or `.wopal`, on the space branch. Afterwards the space branch holds the complete tree.
4. **New capability directories must be assembled first.** To write a brand-new capability directory, widen the implementation-side assembly range before writing content; after merging, widen `.wopal`'s assembly and re-materialize, or the validator cannot see the new capability.
5. **Never clear the `S` bits in bulk.** skip-worktree is derived state of the assembly range: a path inside the range is materialized, so the bit is always wrong there, and a path outside it must have one. Adjust visible scope only by widening assembly. Two states matter, and they are not equally bad. An out-of-range entry with a *cleared* bit makes `git status` report a deletion, but `git add -A` still stages nothing while the range is on — git refuses. Switch the range *off* in that same state (which `git sparse-checkout disable` does, clearing the config and the bits together) and the same `git add -A` stages the deletion for real. That is the 2026-09-20 shape, and it is why `commit` / `integrate` verify the range instead of trusting discipline.
6. **Validation means restarting and observing.** For anything touching the load path, the verdict is what the user sees after restarting ellamaka. A green test is not a substitute for observing the loaded behavior.
7. **Delivery is the user's terminal decision.** `space sync` (into `local main`) and `ontology contribute` (upstream) are called one at a time, at the user's word. The skill contains no automatic upstream path — by design, not by omission.

### Quick mode

Typo fixes, bug fixes in existing assets, and small changes the user explicitly scopes may be committed in small steps directly on the `.wopal` space branch — the space branch is itself the isolation boundary against `local main`. When the judgment is unclear, use isolated mode. Widening scope is a user decision, not an agent's convenience.

## Landing an evolution

```
Evolution Plan (approved)
  → evo.sh new "<title>"                    # draft
  → user reads the proposal
  → evo.sh accept <name>                    # accepted + isolated worktree
  → implement in the worktree
  → evo.sh commit <name> -m "<message>"     # sparse-safe, widens the range first
  → evo.sh advance <name> --to implementing
  → user restarts ellamaka and observes     # validating
  → evo.sh advance <name> --to validating
  → evo.sh integrate <name>                 # squash onto the space branch
  → user confirms
  → evo.sh advance <name> --to archived
  → evo.sh archive <name>
  → delivery decision (space sync / ontology contribute) — user only
```

In quick mode, skip `integrate`: `commit --paths <path>...` lands directly on
the space branch, which is itself the isolation boundary.

`integrate` runs once, after validation. Squashing after every commit does not
work: squash creates new commit ids, so the next squash loses its merge base
and fails with add/add conflicts.

## Boundary

The boundary is per lane, and the two are not the same.

- **Semantic lane — Propose Only.** In this lane you write and refine proposals under `docs/evolutions/`; you never touch a capability asset, never commit, and never implement changes. Every proposal waits for explicit user approval. When evidence is thin, say so: a speculative proposal presented as fact is worse than no proposal. Violating this = **CRITICAL FAILURE**.
- **Mechanism lane — propose, land, gate.** Wopal decides and orchestrates; Fae implements and commits on the space branch; Rook audits. The lane touches files *only* through those roles, and *never* ships upstream on its own.

The separation exists because a proposal that its own author can silently implement is no longer a proposal. It constrains the semantic lane; it is not a description of the mechanism lane.

---

# References

- State machine and delivery terminal: `docs/DESIGN-evolution.md` (Capability Evolution Workflow)
- Command contract and stage semantics: `references/commands.md`
- Sparse isolation background: `docs/DESIGN-distribution.md`
- Development and test conventions for this skill: `AGENTS.md`
