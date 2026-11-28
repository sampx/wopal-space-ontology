---
name: dev-proposal
description: >
  Analyze, discuss, write, and maintain business/project Proposals. Use when
  asked to design or discuss a change intended for a Proposal, clarify its
  requirements and decisions, create or revise the target specification,
  approve, migrate, archive, or evolve a Proposal. Do not use for routine bugs inside a
  settled design (use df-implement), independent read-only review of a
  Proposal/Plan/DESIGN (use df-proposal-review), PRD/DESIGN authoring (use
  dev-doc-master), ontology capability evolution proposals (use
  ontology-evolution), or Plan orchestration (use dev-flow).
---

# dev-proposal — Business Proposal Lifecycle

A Proposal is the **target design specification and record of important decisions** for a change. Resolve the design first, then write a determinate, complete, implementable, and verifiable specification. Progress lives in Plans and Issues; delivered system behavior lives in the project/module present-state DESIGN.

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

## Design analysis and specification

When asked to discuss or write a Proposal, first read `references/design-discussion.md` and the relevant parts of `references/design-practices.md`. Investigate higher-level design, current decisions, code, and terminology; actively model the domain and work the decision tree in rounds until every material branch is settled. Do not repeat settled questions. Record decisions each round.

After discussion closes, read `references/design-specification.md`, determine verification boundaries, and synthesize every confirmed design decision into the target specification. Writing is synthesis, not a new round of selection. Return to discussion if a material decision is missing.

Existing architecture and contracts not explicitly changed by the approved scope remain binding. For proposed changes, identify scope, reasons, impact, and surviving constraints for the user to decide. Determine the design, leave implementation free. After self-check, send for independent review; do not implement before user approval.

## Layout and state machine

Read `references/lifecycle.md` for the authoritative layout, fields, body skeletons, state transitions, migration and link maintenance.

`proposed` → user approves → `approved` (same path) → fully delivered and user-accepted → `implemented` → archive when no longer guiding work. Rejection may end a proposed or approved record. Archived records remain frozen. No execution states or independent progress tracking belong in a Proposal.

Use the current templates. Keep target design separate from present-state DESIGN; apply `dev-doc-master` for document ownership and synchronization.

## Delivery mode: the user decides

`Delivery` has exactly two values and **the user chooses**, never the agent:

- **`direct`** — skip the `dev-flow` Plan split. `df-implement` calls `git-worktrees` to create an isolated worktree by default, and **never works directly on the main/integration branch by default**. Fits a clear, single-point scope with no parallel tasks.
- **`plan`** — enable the optional `dev-flow` Plan/Task split; `dev-flow` owns the isolated worktree and shared Delivery. Fits cross-project, multi-deliverable, or parallel write-set work.

The agent may lay **objective facts** in front of the user: how many repositories are involved, whether parallel work is needed, whether staged acceptance is required. **Never** substitute a subjective judgement ("this model is strong/weak enough", "this task is complex/simple") for the user's choice of path.

## Maintain the approved Proposal before acceptance

The current user-approved Proposal is the sole target authority for the approved change in a Proposal-driven delivery: design decisions, authorized scope and acceptance criteria. Existing design constraints not explicitly changed remain binding. Automated implementation may not change them autonomously. An explicit user decision during post-implementation testing or validation, including added features, expanded scope or a changed direction, authorizes that adjustment. Resolve undecided questions with the user; do not ask for approval again when the decision is explicit.

Integrate the decision into the existing scope, design basis, target design, acceptance criteria, and affected decision rationale and residual risks, preferably before changing code; if already implemented, synchronize before delivery. Keep the file path, `Status: approved` and delivery baseline. The controller coordinates shared files and Plan write sets. Once accepted and moved to `implemented/`, the historical-decision rules below apply.

Write in the user's preferred language, for the user, in concise, clear, affirmative target-state prose. Replace superseded statements in their existing sections; maintain a coherent proposal rather than appending amendments, parallel old/new designs or a change log. Git retains the editing history.

## Workflow

1. **Decide whether it is needed** using the three thresholds above. If not, route to an Issue or direct implementation and say why.
2. **Analyze and discuss the design**: investigate higher-level design, current facts, and active and implemented records on the same topic using the design method above; resolve material open questions. Handle hits per "Evolving an implemented proposal".
3. **Write the specification and self-check**: copy `templates/proposal-proposed.md` to `proposed/<class>/yyyy-mm-dd-<slug>.md` and fill it using the target specification standard. Reconcile all confirmed decisions, architecture inheritance, contracts, and acceptance; return to discussion when necessary.
4. **Independent review and user reading**: send to `df-proposal-review` and resolve material findings. The file stays `Status: proposed`; you do not advance it yourself.
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

Read `references/evolution-triage.md` before changing an implemented decision: distinguish fact-only synchronization, partial supersession and full replacement. Preserve historical decisions and complete the appropriate link repair, absorption or archive in the same accepted delivery.

## Honest boundaries

- This skill owns writing, approval recording, migration, and freezing of Proposals. It **does not implement** and does not approve on the user's behalf.
- Independent review belongs to `df-proposal-review`. This skill writes; that one reviews. Do not issue your own pass.

## References

- Design analysis and discussion rounds: `references/design-discussion.md`
- Target design specification and self-check: `references/design-specification.md`
- Design practices by domain: `references/design-practices.md`
- State machine, fields, and migration detail: `references/lifecycle.md`
- Follow-up triage and supersession judgement: `references/evolution-triage.md`
- Skeleton templates: `templates/proposal-proposed.md`, `templates/proposal-implemented.md`
- Static verifier: `scripts/verify-proposals.py`
- Expression standards: `dev-doc-master` (`references/consistency.md`, `references/design-project-guide.md`)
