---
name: dev-proposal
description: >
  Author and maintain business/project Proposal records: decide whether a change
  needs one, write it, record user approval with `Delivery: direct | plan`, move
  it through proposed/implemented/rejected/archived, and handle later changes to
  an already-implemented decision. Use when asked to create, revise, approve,
  migrate, archive, or evolve a Proposal. Do not use for routine bugs inside a
  settled design (use df-implement), independent read-only review of a
  Proposal/Plan/DESIGN (use df-proposal-review), PRD/DESIGN authoring (use
  dev-doc-master), ontology capability evolution proposals (use
  ontology-evolution), or Plan orchestration (use dev-flow).
---

# dev-proposal — Business Proposal Lifecycle

**You do one thing: make an important design decision traceable, ownable, and bounded in time.**

A Proposal records a **decision**: why it was needed, which path was chosen, what was given up, what counts as done, and what it costs. It does not record execution progress, and it is not a present-state document. Progress lives in Plans and Issues; delivered system behavior lives in the project/module present-state DESIGN.

## When a Proposal is required

Write one when any of these holds:

- Several viable paths exist and the reason for the choice cannot be read out of the code.
- An active default, boundary, permission, failure semantic, or external contract changes.
- A decision already sitting in `implemented/` is overturned, wholly or partly.
- Several projects or modules share the convention, or the user must re-decide the scope.

Skip the Proposal only when all of these hold:

- The work is a clear task or defect inside an existing decision.
- One Issue or one direct implementation can state both scope and acceptance.
- No design-level choice is left for the user to make.

Ordinary bugs, style tweaks, mechanical renames, and pure internal refactors go through an Issue or direct implementation. **A Proposal is not a ritual attached to development work**: wrapping every change in a Proposal just to look disciplined produces files nobody reads.

When a Proposal already covers the topic, audit before writing: sync facts in place if nothing changed, or write a new one and cross-link if the decision changed — see "Evolving an implemented proposal" below.

## Layout and state machine

### Layout

The Proposal root follows ownership:

- Product level: `docs/products/{product}/proposals/`
- Project level: `projects/{project}/docs/proposals/`

Under that root, the path has two axes, `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md`:

```
proposals/
├── proposed/<class>/
├── implemented/<class>/
├── rejected/<class>/
└── archived/<class>/
```

- `lifecycle` is the closed set `proposed | implemented | rejected | archived`. `archived/` has **no** `implemented` level.
- `class` is a closed set of six, and you cannot invent one: `feature | bug-fix | simplification | architecture | process | testing`.
  - `feature`: a new user- or model-facing capability.
  - `bug-fix`: corrects a defect, or closes a gap a review surfaced.
  - `simplification`: removes code, behavior, or surface without adding a capability.
  - `architecture`: a structural decision about shipped source — how modules relate, what the runtime vocabulary is.
  - `process`: tooling, policy, or workflow around the code, not runtime behavior.
  - `testing`: test infrastructure and strategy.
- Filename `yyyy-mm-dd-<slug>.md` uses the date the topic was **first proposed** (per Git history) and a lowercase kebab-case slug of 2–4 words.
- **Forbidden**: a singular `proposal/` directory, an unknown class directory, and a centralized `INDEX.md`. The paths are the index; an `INDEX.md` puts every unrelated change in contention over one file.
- Existing pre-format files stay read-only compatible: cite them, read them, do not force a migration, and do not reformat them to the new rules.

### State machine

```text
proposed ──user approves──▶ approved ──all delivered and accepted──▶ implemented ──mission complete──▶ archived
    │                            │
    └────user rejects────────────┴──▶ rejected
```

| State | Location | Meaning |
|---|---|---|
| `proposed` | `proposed/<class>/` | Written and waiting for the user; no authorization yet |
| `approved` | `proposed/<class>/` | The user approved and authorized a scope; **the file stays in `proposed/`** so Plans and inbound links do not break mid-delivery |
| `implemented` | `implemented/<class>/` | The approved scope is fully delivered and the user has accepted it |
| `rejected` | `rejected/<class>/` | Declined, with a one-line reason on the status line |
| (frozen) | `archived/<class>/` | A finished `implemented/` record that no longer guides daily work; `Status` stays `implemented` and gains `Archived: YYYY-MM-DD` |

Hard constraints:

- **Never introduce `implementing` / `verifying` / `done`.** A Proposal has no execution progress; progress belongs to Plans and Issues.
- Partial delivery **does not** move into `implemented/`. The file stays in `proposed/` with `Status: approved`; delivery evidence says what is done, and the state does not pretend to guess.
- A completed or archived Plan **never** flips its Proposal to `implemented`. Only a fully delivered, user-accepted scope does, and the agent moves it in the same delivery.
- No `approved` without explicit user approval; no `implemented` without acceptance. **A format check cannot forge approval** — a passing script means the shape is valid, not that anyone approved it.

### Header contract

```markdown
# <Title>

Status: proposed

- **Class**: architecture
- **Created**: 2026-11-22
```

`Status` is the third line and takes `proposed`, `approved`, `implemented`, or `rejected — <one-line reason>`. The status line carries no date and no parenthetical; the date lives in the filename and `Created`, and everything else lives in Git.

Approval adds three fields, all required:

```markdown
- **Approved**: 2026-11-22 — <approver>
- **Authorized scope**: <one sentence: what was approved, including explicit exclusions>
- **Delivery**: direct | plan
```

Archiving inserts `Archived: YYYY-MM-DD` immediately below `Status: implemented`; that line is the only content change archiving may make.

### Body skeleton

`proposed/` (including `approved`) uses the future-tense skeleton:

```markdown
## Problem
## Proposal
…(bespoke sections as needed: interfaces, migration, trade-off analysis)…
## Alternatives considered
## Acceptance criteria
## Risks
```

`implemented/` uses the present-tense skeleton:

```markdown
## Problem
## Decision
…(bespoke sections as needed)…
## Alternatives considered
## Consequences
```

Moving into `implemented/` **rewrites the skeleton mechanically in the same delivery**: `## Proposal` becomes `## Decision`, and `## Acceptance criteria` plus `## Risks` fold into `## Consequences` (both the cost and the gain). These planning-era headings are **forbidden** in `implemented/`: `## Proposal`, `## Plan`, `## Migration plan`, `## Acceptance criteria`.

`rejected/` keeps its proposal-time body and sections (including `## Acceptance criteria` if present); the verdict lives only on the status line.

`## Alternatives considered` is required in all four lifecycles. Each entry states what the alternative was and why it lost. **Record only alternatives that were genuinely considered**; never invent one, and do not backfill pre-format files.

Expression standards — clarity, term consistency, no AI slop, `Source Carrier`, evidence-backed claims — come from `dev-doc-master` (including `references/design-project-guide.md`). This skill does not copy them. A Proposal **does not touch present-state DESIGN**: unbuilt design is never pre-written into `DESIGN.md` or `DESIGN-<module>.md`.

## Delivery mode: the user decides

`Delivery` has exactly two values and **the user chooses**, never the agent:

- **`direct`** — skip the `dev-flow` Plan split. `df-implement` calls `git-worktrees` to create an isolated worktree by default, and **never works directly on the main/integration branch by default**. Fits a clear, single-point scope with no parallel tasks.
- **`plan`** — enable the optional `dev-flow` Plan/Task split; `dev-flow` owns the isolated worktree and shared Delivery. Fits cross-project, multi-deliverable, or parallel write-set work.

The agent may lay **objective facts** in front of the user: how many repositories are involved, whether parallel work is needed, whether staged acceptance is required. **Never** substitute a subjective judgement ("this model is strong/weak enough", "this task is complex/simple") for the user's choice of path.

A new decision or a material change to the authorized scope requires fresh user confirmation; an old approval does not cover a new scope.

## Workflow

1. **Decide whether it is needed** using the three thresholds above. If not, route to an Issue or direct implementation and say why.
2. **Audit before drafting**: search the matching `proposals/` root for active and implemented records on the same topic. Handle hits per "Evolving an implemented proposal".
3. **Write the file**: copy `templates/proposal-proposed.md` to `proposed/<class>/yyyy-mm-dd-<slug>.md` and fill `## Problem`, `## Proposal`, `## Alternatives considered`, `## Acceptance criteria`, `## Risks`. Acceptance criteria must let a third party judge met or unmet.
4. **Wait for the user to read it.** The file stays `Status: proposed`; you do not advance it yourself.
5. **Record approval**: once the user explicitly agrees, add `Approved`, `Authorized scope`, and `Delivery`, set `Status: approved`, and leave the path alone.
6. **Commit the approved Proposal before creating the delivery branch or worktree.** Commit it on the integration branch, then start delivery from that commit so the approved record is part of the delivery baseline. Keep this commit limited to the Proposal change.
7. **Deliver** along the `Delivery` route. Keep the evidence chain — source, related Plan, actual commits, review acceptance — inside the Proposal as links; do not copy a progress table.
8. **After full delivery and user acceptance, migrate**: move to `implemented/<class>/`, set `Status: implemented`, rewrite the skeleton into the present tense (`Decision` / `Consequences`) in the same delivery, and sync the affected present-state DESIGN.
9. **On rejection**: ask whether the reason prevents someone from repeating a **tempting** mistake later. If yes, move to `rejected/<class>/` with the reason on the status line; if not, delete the file and repair every inbound link.
10. **Archive and prune**: move `implemented/` records that finished their mission and no longer guide daily work into `archived/<class>/`, insert `Archived: YYYY-MM-DD`, and freeze them. Small UI adjustments and purely mechanical changes are not archived — delete them and repair inbound links.

Run the check after each step (path relative to this skill directory):

```bash
python3 scripts/verify-proposals.py <proposals-root>
```

Exit code 0 means the shape is valid; the script only checks single-snapshot static facts, and design quality still belongs to review and the user.

## Evolving an implemented proposal

This is the part most likely to go wrong, and the part most worth remembering. **An `implemented/` record is a historical decision: facts may change, the decision may not.**

Classify the change first:

| Class | Test | Action |
|---|---|---|
| **Fact-only drift** | Decision, boundary, and defaults are unchanged; only a path moved, a name changed, or a local implementation detail differs | **Update in place** inside `implemented/<class>/` in the same delivery. Write the current fact, create no proposal, append no change log. |
| **Design adjustment / optimization / partial overturn** | The decision, a core default, or a boundary changes; the user must re-decide (even when it is called an "optimization" or "local enhancement") | **Create** `proposed/<class>/yyyy-mm-dd-<slug>.md` and run it through independent review and user approval. |
| **Full replacement / capability removal** | The decision as a whole no longer holds and a new one replaces it | **Create** a proposal and dispose of the old one when the new scope is fully delivered (below). |

Hard constraints for the second class:

- **Never** move an `implemented/` proposal back to `proposed/`, and never rewrite it in place into a different decision. Rewriting a historical decision erases why it was chosen.
- A new proposal **must not modify the old `implemented/` record before it is fully delivered.**
- When the new proposal moves into `implemented/`, **cross-link both ways in the same delivery**: the new one names which of the old decisions it partly supersedes and which stay valid; the old one states the superseded part as current and links to the new one.

Hard constraints for the third class: dispose of the old record **at delivery time**, not in a later cleanup. Two options:

- **Absorb, then delete** — carry every unique rationale, alternative, cost, verification method, and known gap from the old proposal into the new one, repair all inbound links, then delete the old file.
- **Move to `archived/<class>/` and freeze** — when the old proposal still has independent historical value.

**`archived/` is permanently read-only**: no unfreezing, no rewrite, no translation, no reformatting, no move, no delete, and no outbound-link checking. Later evolution only ever creates active proposals, citing the archive as background when useful.

## Honest boundaries

- This skill owns writing, approval recording, migration, and freezing of Proposals. It **does not implement** and does not approve on the user's behalf.
- The workflow engine cannot yet derive a Plan/Task set from a Proposal. Until `dev-flow` supports it, **do not pretend to call, or automatically call, a Proposal→Plan command that does not exist**; `Delivery: plan` is a recorded user decision, and the user arranges the split.
- Independent review belongs to `df-proposal-review`. This skill writes; that one reviews. Do not issue your own pass.

## References

- State machine, fields, and migration detail: `references/lifecycle.md`
- Follow-up triage and supersession judgement: `references/evolution-triage.md`
- Skeleton templates: `templates/proposal-proposed.md`, `templates/proposal-implemented.md`
- Static verifier: `scripts/verify-proposals.py`
- Expression standards: `dev-doc-master` (`references/consistency.md`, `references/design-project-guide.md`)
