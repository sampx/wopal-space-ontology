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

The mechanism lane lands an approved plan. Its discipline lives in `scripts/` — enforced by the script, not by prose: refusing before the first write, staging by name, the guard table, the isolation assertion, and the integrate corpus assertion. This document records what the script cannot enforce: roles, user decision points, and the validation philosophy.

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

## Proposal script

Run from the skill root: `bash scripts/evo.sh <command> [args]`.

| Command | Does |
|---------|------|
| `evo.sh new "<title>"` | Creates `docs/evolutions/<name>.md` from `templates/proposal.md` at `Stage: draft` |
| `evo.sh status <name\|path>` | Prints stage, path, mode, isolation metadata, and the next command |
| `evo.sh accept <name> [--no-worktree]` | Gates the proposal (placeholders + structure), then derives or re-attaches the isolated worktree transactionally |
| `evo.sh advance <name> --to <state>` | Advances the state machine; refuses illegal transitions |
| `evo.sh commit <name> -m <msg>` | Sparse-safe commit at `implementing`; widens the range first, stages by name |
| `evo.sh integrate <name>` | Squashes the isolated work into the space branch; refuses invisible content (corpus assertion) |
| `evo.sh check <name>` | Reports proposal, sparse-state, structure, and corpus problems |
| `evo.sh archive <name> [--keep-worktree]` | Moves an `archived` proposal to `docs/evolutions/archived/YYYYMMDD-<name>.md`, cleans up isolation artifacts |

Properties the commands guarantee — each has a named test, so this is a claim about the suite, not a hope:

- **Stage is written only by the script.** Never hand-edit `- **Stage**:`; the script refuses a proposal whose field it cannot find.
- **Refusal precedes mutation.** Every safety check runs before any write; a rejected command leaves the repository exactly as it found it.
- **Nothing is ever staged wholesale.** Staging is by name and the range widens first; no command in this skill issues `git add -A`.
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

## Landing an evolution

```
Evolution Plan (approved)
  → evo.sh new "<title>"                    # draft from the external template
  → user reads the proposal
  → evo.sh accept <name>                    # gate + isolated worktree
  → evo.sh advance <name> --to implementing
  → implement, then evo.sh commit <name> -m "..."   # sparse-safe, per task
  → evo.sh integrate <name>                 # squash onto the space branch
  → evo.sh advance <name> --to validating
  → user restarts ellamaka and confirms
  → evo.sh advance <name> --to archived
  → evo.sh archive <name>                   # dated name + isolation cleanup
  → delivery decision (space sync / ontology contribute) — user only
```

In quick mode, skip `integrate`: `commit --paths <path>...` lands directly on
the space branch, which is itself the isolation boundary.

`integrate` runs once, after implementation. Squashing after every commit does
not work: squash creates new commit ids, so the next squash loses its merge
base and fails with add/add conflicts. Rework after integrate is a new commit
on the space branch, not a second squash.

## Boundary

The lane boundary, and the boundary against neighboring entry points:

- **Semantic lane — propose only.** Proposals under `docs/evolutions/`; never touch a capability asset, never commit, never implement. Every proposal waits for explicit user approval. A speculative proposal presented as fact is worse than no proposal. Violating this = **CRITICAL FAILURE**.
- **Mechanism lane — propose, land, gate.** Wopal decides and orchestrates; Fae implements; Rook audits. The lane never ships upstream on its own.
- **`/wopal:evolve` and `/wopal:distill`** are user-facing entry commands that arrive at this skill's mechanism lane; they do not bypass the state machine or the user decision points.
- **`wopal/ontology-maintain`** covers maintenance operations on the ontology (sync, hygiene) outside an evolution's lifecycle; it is not a proposal path.
- **Assembly overlay**: assets here are assembled per space via the overlay mechanism (`docs/DESIGN-distribution.md`); the skill operates on the assembled worktree (`.wopal`), never on the central pool directly.

The separation exists because a proposal that its own author can silently implement is no longer a proposal.

---

# References

- State machine and delivery terminal: `docs/DESIGN-evolution.md` (Capability Evolution Workflow)
- Command contract and stage semantics: `references/commands.md`
- Sparse isolation background: `docs/DESIGN-distribution.md`
- Development and test conventions for this skill: `AGENTS.md`
