---
name: ontology-evolution
description: |
  Ontology capability evolution workflow. Covers both halves of the work: writing evolution proposals out of lived experience — session errors, user corrections, lessons and fixes recalled from memory — and landing an approved proposal into the ontology safely (isolated implementation, validation, archive). Proposals are usually drafted by Maka, whose core mission is that analysis; Wopal may write them too, and Wopal orchestrates the landing process. Fae lands the change, Rook audits it; approval, validation, and delivery belong to the user.

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
---
# ontology-evolution

Turn lived experience into lasting capability — and land that improvement without corrupting the ontology.

Everything meets at one artifact: **the evolution proposal** — a file under `docs/evolutions/` that states what should change, why, and how it will be verified. Writing proposals and landing them are the two parts of this workflow; landing always waits on explicit user approval.

## Who does what

| Role | Does | Never does |
|------|------|------------|
| **Maka** | Core mission: analyzes session errors, user corrections, and lessons/fixes remembered from memory; writes and refines evolution proposals under `docs/evolutions/` | Touch a capability asset, run the landing workflow |
| **Wopal** | May also write proposals. Orchestrates the landing process end to end: reads the proposal with the user, accepts it, plans and delegates the work, drives the stage transitions, verifies the result through to archive | Implement assets by hand |
| **Fae** | Lands the change — edits the assets and commits on the space branch | Move the proposal's stage |
| **Rook** | Audits the deliverable before it moves on | Fix anything |
| **User** | Approves a proposal before landing starts; validates the landed change; decides delivery | — |

A proposal is never its own implementation authorization: every proposal, from whoever, waits for the user's approval. Past that gate, safety comes from mechanics — isolation, named staging, visibility checks — not from trust.

---

# Writing a proposal

The point is not to archive what happened; it is to change the capability so the same situation goes better next time.

## Sources worth watching

| Signal | Looks like | Usually means |
|--------|------------|---------------|
| Session error | A failure exposes a wrong assumption | A guardrail is missing |
| Repeated correction | The user corrects the same behavior more than once | A rule is missing or unclear |
| Remembered lesson | Memory holds a lesson, workaround, or fix that no capability carries yet | It deserves to live in an asset |
| Wasted effort | The same helper or approach gets rebuilt | A capability should be extracted |
| Effective pattern | Something worked notably well | Worth preserving so it recurs |

Routine completion is not a lesson. Look for the moment where the behavior should have been different.

## Strip the specifics first

- Absolute paths, project / product / client names, business terms that only matter here → generic wording or nothing
- Session ids, timestamps, commit hashes → gone

The test: a reader who has never seen this space can still understand and apply the lesson.

## Decide where it belongs

| Tier | Destination | Fits when |
|------|-------------|-----------|
| **Space-private** | `.wopal-space/memory/` or the project's `AGENTS.md` | It only holds in this space / this project |
| **Type-specific** | `config/types/<type>.yaml` assembly, or type-scoped assets | It holds for every space of this type, not for others |
| **Public core** | The central pool (`agents/`, `skills/`, `rules/`) | It is true for any space of any type |

Ask in order: does it hold in a different space? For a different project of the same type? For any space at all? A "maybe" is not a "yes" — when unsure, place it lower. A local lesson can be promoted later; a polluted pool is hard to clean.

## Write it

`wopal space evo new "<title>"` creates `docs/evolutions/<name>.md` from `templates/proposal.md` at `Stage: draft`. The template is the single source of the proposal's shape — fill every section; unreplaced placeholders are refused at `accept`.

- Write the proposal document in the user's preferred language; the template's headings and field labels stay as they are.
- Anchor every claim in evidence: a session fact, an error, a user correction, a code location (`file:line`). Mark unverified statements as unverified.
- Few and strong beats many and weak. One analysis may yield several candidates — one proposal per coherent change.

## Handoff

A proposal on disk is waiting for the user to read it; its author may keep refining it while it stays a proposal. The user's approval starts the landing stage, which Wopal orchestrates.

---

# Landing an approved proposal

The wopal CLI enforces the landing discipline — refusal before the first write, named staging, isolation and visibility checks. What follows records what the CLI cannot enforce: the roles, the user decision points, and the validation philosophy. All landing operations run through the `wopal space evo` command family.

## State machine

```
draft → accepted → implementing → validating → archived
```

| Stage | Meaning |
|-------|---------|
| `draft` | Proposal is on disk under `docs/evolutions/`, waiting for the user to read it |
| `accepted` | User approved; the isolated worktree exists and the mode is recorded |
| `implementing` | The change is being landed: commits in the isolated worktree (or quick-mode commits on the space branch) |
| `validating` | The change is integrated onto the space branch; the user restarts and observes |
| `archived` | User confirmed; the proposal is filed away |

`accepted → implementing` and `validating → archived` are the only forward edges. Review does not occupy a stage: it happens when the user asks for it, and it does not invent a state. There is no backward edge — rework on a landed change is a new commit, not a stage rewind.

**The stage vocabulary is deliberately disjoint from dev-flow's** (`planning / reviewing / approved / executing / verifying / done`). Mixing the two vocabularies is how an agent mistakes one workflow for the other — never "unify" them.

## Commands

Run from the space root: `wopal space evo <command> [args]`.

| Command | Does |
|---------|------|
| `wopal space evo new "<title>"` | Creates `docs/evolutions/<name>.md` from `templates/proposal.md` at `Stage: draft`; the template's naming contract governs the title |
| `wopal space evo status [name]` | Lists the active proposals, or shows one proposal's stage and recorded metadata |
| `wopal space evo check <name\|path>` | Diagnoses the proposal (metadata, placeholders, structure) and the space worktree's sparse shape |
| `wopal space evo advance <name> --to <state>` | Advances the state machine; refuses illegal transitions |
| `wopal space evo accept <name> [--no-worktree]` | Gates the proposal (placeholders + structure), then derives or re-attaches the isolated worktree transactionally |
| `wopal space evo commit [<name>]` | Sparse-safe commit at `implementing`: widens the range first, stages by name. Without a name: instant mode, the defect-repair path |
| `wopal space evo integrate [name]` | Squashes the isolated work into the space branch; refuses content that would land invisible |
| `wopal space evo archive <name> [--keep-worktree]` | Moves an `archived` proposal to `docs/evolutions/archived/YYYYMMDD-<name>.md`, cleans up isolation artifacts |

Guarantees of the command family (enforced by the CLI, not by prose):

- **Stage is written only by commands.** Never hand-edit `- **Stage**:`; a proposal whose field cannot be found cannot be advanced.
- **Refusal precedes any write.** A rejected command leaves the repository exactly as it found it.
- **Nothing is staged wholesale.** Staging is by name and the sparse range widens first; no command runs `git add -A`.
- **Re-running is safe.** Re-advancing is a no-op; re-accept adopts or re-attaches instead of fighting existing state.

Command-level detail — including the shared `commit`/`integrate` preflight — lives in `references/commands.md`.

## Isolation discipline

Default implementation mode: **derive a worktree from `.wopal`**. The derived worktree inherits the space's sparse assembly patterns, so its visible boundary equals the capability set the space is entitled to — and the host repository never switches branches.

Seven constraints:

1. **Isolate by default.** The worktree derives from `.wopal`; `accept` verifies the derivation is a faithful sparse copy of the space.
2. **The host repository never switches branches.** It carries the base capabilities other spaces depend on and stays on `main`.
3. **Merge on the space branch.** The merge happens inside `.wopal`, on the space branch, as a single squash after validation.
4. **Assemble before staging.** New capability directories join the space range first (the range widens before anything is staged), and `integrate` refuses any path that would land invisible — a committed file the runtime cannot see (the visibility check; "corpus assertion" in the CLI contract).
5. **Never clear the skip-worktree bits in bulk.** They are derived state of the assembly range; adjust the visible scope only by widening assembly, and let the preflight verify the range instead of trusting discipline.
6. **Validation means restarting and observing.** Anything on the load path is judged by what the user sees after restarting ellamaka; a green test is not a substitute.
7. **Delivery is the user's terminal decision.** `space sync` and `ontology contribute` run one at a time, at the user's word. The skill contains no automatic upstream path — by design, not by omission.

### Quick mode

Typo fixes, bug fixes in existing assets, and small changes the user explicitly scopes may be committed in small steps directly on the `.wopal` space branch — the branch is itself the isolation boundary against `local main`. When the judgment is unclear, use isolated mode. Widening scope is the user's decision, not an agent's convenience.

### Defect repair is immediate

A **defect** — existing, agreed behavior that is wrong — is repaired right away, without a proposal. The review a proposal exists to provide is already settled for agreed behavior; the record that matters is the commit.

The path is `wopal space evo commit` in **instant mode** — no proposal name, with `-m <message>` and exactly one of `--paths <p>...` / `--all`:

- Commits directly on the space branch — the isolation boundary against `local main`, same as quick mode.
- The safety contract still applies: refuse on an incoherent sparse state, widen the range first, stage by name. The fast path skips process, never safety.
- No proposal artifact is created and no stage moves.

There is no separate `fix` command — that is the design, not a gap; do not add one, an alias, or a shim. Shadow-registration duty belongs to `capability remove --local`.

A defect **fixes** agreed behavior; anything that **changes** behavior — a new capability, a contract change, a workflow step that should behave differently — is an evolution and follows the proposal lifecycle. When you cannot tell which you have, ask. Choosing the fast path for a change that deserved review is worse than a slow path for a fix.

## Landing flow

```
Proposal (approved)
  → wopal space evo new "<title>"                    # draft from templates/proposal.md
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

In quick mode skip integrate: `wopal space evo commit <name>` lands directly on the space branch, which is itself the isolation boundary.

`integrate` runs once, after implementation. Squashing after every commit does not work: squash creates new commit ids, so the next squash loses its merge base and fails with add/add conflicts. Rework after integrate is a new commit on the space branch, not a second squash.

---

# Maintenance

Beyond the evolution lifecycle, this skill owns the ontology's maintenance surface: instance updates, space alignment, and capability assembly.

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

`wopal ontology status` reports both flows: **Downstream** (`upstream → origin → local main`) and **Upstream** (`local main → origin → upstream`), the latter as the pending file set.

`wopal space status` reports the space link: **to contribute** vs **behind local main**, the assembly snapshot state, and the **local state lists** — `added` / `shadowed` / unregistered untracked files. Local-state paths are space-private by construction: they never travel to `local main`.

## Channels and the upload gate

`space capability` has two channels. Without `--local`, the change edits the assembly manifest and re-materializes — but creates no commit by itself, and only accepts a capability the pool already owns, so committing the manifest is a separate step. With `--local`, it writes only the space's `localState` (`added` / `shadowed`) and adjusts the sparse range — zero commits, structurally unable to sync up; `add --local` on a shadowed capability is also the recovery exit.

Before integrating upward, `space sync` checks the **upload gate**: no space-unique commit may touch a `localState` path (added ∪ shadowed). A hit refuses the sync and names the remedy — withdraw the commit, or drop the registration. The gate backstops a manual `git add`/`commit` of local-state content: local isolation does not depend on the operator remembering.

## Execution stance

The CLI defaults to dry-run preview; `--confirm` executes. The settled stance: the agent acts on the user's intent directly and passes `--confirm` — no extra approval gate is layered on top; `--dry-run` is a diagnostic, not a precondition. Safety comes from mechanics: isolated integration, fast-forward only, stop-on-conflict, worktree checks — the worst case is a change not happening, not a broken worktree. `ontology contribute` is the single exception: each contribution is the user's call, one at a time.

## Contribution scope and themed PRs

Scope is determined with the user, from evidence:

1. Enumerate every pending path first (`git diff --name-status <base>...<target>`), grouped by directory / feature area, each group labelled shared or type-specific — show the full inventory before asking anything.
2. Classify structurally, not by feel: shared = meaningful to every space type; type-specific = meaningful to one type only. When unsure, check the pool (`ontology capability list`) and the ontology design instead of guessing.
3. The user circles the scope: which groups travel upstream, which are excluded, which stay space-only.
4. Space-only assets never appear in any contribution.

One PR per topic: `--include` / `--exclude` carve a coherent contribution out of the pending set, and `--message` states what the change delivers (result state), not the mechanical action. Split unrelated work; never bundle it.

---

# Boundaries

- **A proposal waits for the user.** Whoever wrote it, it lands only after the user approves — an author never silently implements their own proposal.
- **Maka writes only.** Maka's edit scope is `docs/evolutions/`; touching a capability asset is a CRITICAL FAILURE. Speculation presented as fact is worse than no proposal.
- **Landing: Wopal orchestrates, Fae lands, Rook gates.** The workflow never ships upstream on its own.
- **`/wopal:evolve` and `/wopal:distill`** belong to the memory-evolution loop (diaries → long-term memory files / the memory database), not to this workflow. If distilled experience calls for an ontology change, it still goes through this skill's proposal lifecycle.
- **`wopal/ontology-maintain`** is a thin trigger: it loads this skill with a focus argument and carries no protocol of its own — the Maintenance protocols above are the protocol.
- **The skill carries the rules; wopal-cli does the work.** The skill ships only documents and the proposal template — no scripts. Every maintenance and landing step runs through wopal-cli commands (command details in the Maintenance and Landing sections above).
- **Assembly overlay**: assets are assembled per space via the overlay mechanism (`docs/DESIGN-distribution.md`); the skill operates on the assembled worktree (`.wopal`), never on the central pool directly.

---

# References

- State machine and delivery terminal: `docs/DESIGN-evolution.md` (Capability Evolution Workflow)
- Command contract and stage semantics: `references/commands.md`
- Proposal skeleton: `templates/proposal.md`
- Sparse isolation background: `docs/DESIGN-distribution.md`
- Development conventions for this skill: `AGENTS.md`
