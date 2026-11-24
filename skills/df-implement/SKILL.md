---
name: df-implement
description: >
  Write or update code and tests to deliver an approved Proposal (direct
  delivery), an explicit Issue, or an approved Plan task as a real delivery,
  syncing the owning module present-state DESIGN, business Proposal, and
  mechanical gate evidence in the same delivery. Load when writing code,
  fixing bugs, adding tests, implementing in an isolated worktree, or acting
  as a delegated implementation agent. Pre-implementation design review does
  not belong here.
---

# df-implement — Implementation Discipline

You are doing **implementation work**. Deliver the requested change with the smallest reliable, verifiable code change that stays inside the design and task boundaries, keeping code, tests, and the owning module present-state DESIGN consistent within one delivery.

## Authorized input sources

This skill accepts exactly one of three authorized sources and binds to no Plan state machine:

| Source | What you receive | Scope authority |
|---|---|---|
| Approved Proposal (`Delivery: direct`) | The proposal path, its `Status: approved`, and its recorded `Authorized scope` | The scope the proposal's approval covers |
| Explicit Issue | An issue describing a defect or task inside a settled design | The issue description itself |
| Plan Task (optional) | A task inside an approved Plan, with its `Design Source`, ACs, and constraints | The Plan task definition |

Route by the authorization you actually hold — the proposal's recorded metadata, the issue text, or the Plan task definition — never by guessing from file or document names. If you cannot say which authorization covers this change, stop and ask the controller before writing code.

**Plans already in flight** keep their existing contract: DESIGN defines the target, the approved Plan defines the delivery scope, implementation builds it. Do not retroactively rewrite an in-flight Plan or its tasks to the present-state documentation rules; apply the new sync discipline to a Plan only when that Plan itself asks for it.

## direct mode starts in an isolated worktree

When implementing an approved Proposal (`Delivery: direct`) or a standalone Issue, **load the `git-worktrees` skill and create an isolated worktree and feature branch before writing any code**. Never implement directly on the main (integration) branch by default — isolation keeps half-finished work off the main branch and out of parallel agents' way.

Skip creating a new worktree in exactly two cases:

1. The user explicitly asked for the change on the main/current branch;
2. The controller (such as `dev-flow`) already created and assigned an isolated worktree — reuse it, do not nest another one.

The isolation branch's starting point is the delivery baseline; record it as `<delivery-base>` in your report and hand it to the delivery gate and the implementation review.

## Sync the owning module DESIGN at delivery

Project and module present-state DESIGNs (`DESIGN.md` / `DESIGN-<module>.md`) describe only behavior that is really delivered in code. When your change alters externally visible behavior, public interfaces, effective business rules, defaults, or failure boundaries — or you find an existing DESIGN written wrong — **load `dev-doc-master` on demand** and sync the owning module's `DESIGN-<module>.md` in the same delivery; never document features not yet delivered. Pure internal refactors change no external behavior and touch no DESIGN.

**Parallel write-set discipline**: in parallel tasks or branches, edit only the `DESIGN-<module>.md` files inside your authorized write set; never cross into the shared main `DESIGN.md` or another agent's module docs. When you find out-of-scope docs stale or wrong during implementation, do not touch them — report them in the delivery report's `DESIGN Sync` block for the controller to coordinate.

## Mechanical gates at the delivery exit

Before closing a delivery, run the checkers that match what you actually changed and put the real output into the `DESIGN Sync` block:

**Doc gate** — when the project's docs directory exists and is governed by `dev-doc-master`, run from the **project worktree root**:

```bash
python3 <skill-dir>/dev-doc-master/scripts/verify-docset.py <docs-dir> --main DESIGN.md --check-sync --base <delivery-base>
```

`<skill-dir>` is the directory where skills are actually installed (resolved by the space assembly), and `<docs-dir>` is the project docs directory relative to the project root — both must resolve; never copy the example path verbatim.

- When the delivery spans multiple commits or lives on a standalone working branch, **pass `--base` pointing at the Git baseline that covers the whole delivery** (the `git-worktrees` isolation branch start or the `Delivery Base Commit`). Omitting `--base` makes the script check only the last commit and lets earlier out-of-sync commits slip through — the most common failure shape of multi-commit deliveries. Only a single uncommitted working-tree change may omit `--base`.
- `--check-sync` is the doc gate's switch: every governed delivery carries it, including pure internal refactors. `--pure-refactor` is recognized by the checker only when `--check-sync` is on — passing it alone runs no gate at all. For a pure internal refactor that touches no docs, run `--check-sync --base <delivery-base> --pure-refactor "<reason>"`: the gate executes as usual, and `--pure-refactor` only exempts the code change from the DESIGN-sync requirement while putting the reason on record for review. Using it to wave through a delivery that actually changed external behavior is treated as a contract violation in review.
- Do not modify `verify-docset.py` itself and do not build a substitute; when the check fails, go back and fix the docs — not the script.

**Proposal gate** — when the delivery touches business Proposal lifecycle, **load `dev-proposal` on demand** and run:

```bash
python3 <skill-dir>/dev-proposal/scripts/verify-proposals.py <proposals-root> [--link-scope <docs-dir>]...
```

`<skill-dir>` resolves the same way; `<proposals-root>` is the business's actual proposals root (product-level `docs/products/<product>/proposals/` or project-level `projects/<project>/docs/proposals/`), not wherever happens to be convenient. When a Proposal move, deletion, or rename can break links from external docs, pass each affected docs directory to `--link-scope` (repeatable), sized to the real reference scope.

**Proposal lifecycle sync rules** (the `dev-proposal` skill owns the detail; these bound what an implementer may do):

- Only **after the approved scope is fully delivered and user-accepted**, migrate the Proposal from `proposals/proposed/<class>/` into `implemented/<class>/` in the same delivery, rewriting it to the present-tense `## Decision` / `## Consequences` (planning-time headings removed). A partial delivery stays `Status: approved` — never impersonate full delivery.
- **Partial supersession** of an existing `implemented/` proposal: at full-scope delivery, add the cross-links both ways in the same commit; never touch the old proposal before full delivery.
- **Full replacement** of an existing `implemented/` proposal: at full-scope delivery, absorb its unique rationale/alternatives/costs/verification and repair inbound links, then delete the old file, or move it to `archived/<class>/` (inserting `Archived: YYYY-MM-DD`) permanently frozen.
- Ordinary code changes that drift paths/symbols/defaults without changing the decision: sync the affected fact references inside `implemented/` in place, in the same delivery.
- **Never** demote `implemented/` back to `proposed/`, never unfreeze or modify `archived/`. Those moves belong to a new proposal through the formal flow.

**AGENTS maintenance** — when the delivery leaves a new durable engineering constraint (operating commands, verification entries, directory discipline), **load `space-master` on demand** to audit or update the corresponding `AGENTS.md` tier; one-off implementation details do not belong there. Testing follows the resident `rules/testing.md`; this skill adds no testing rules of its own.

## Read before writing

Before editing, understand:

- the current task and acceptance criteria;
- the Task's `Design Source` when present, confirming every cited DESIGN is `Status: Active`;
- for a direct Proposal or Issue: the proposal's `Authorized scope` and the DESIGNs and constraints it cites;
- the Task's `Pre-read`, `Interface`, and `Constraints` when present;
- the relevant call path and callers;
- the current and parent `AGENTS.md` rules.

If you still cannot explain why the proposed change fits the current code, design, and task, keep investigating instead of guessing.

## Minimum implementation order

While preserving design, Plan, correctness, and tests, prefer the simplest option in this order:

1. If the task and acceptance do not require it, do not add it.
2. Reuse an existing function, module, or pattern in this repo when one already fits.
3. Prefer the language standard library when it fits.
4. Prefer built-in platform or runtime features when they fit.
5. Reuse already-installed dependencies when appropriate.
6. Prefer simple direct code over new abstractions, wrappers, or dependencies.
7. Add new structure only when the earlier options are not enough.

A new dependency needs a clear reason why existing options fall short. “Minimum” means leaving no unnecessary code or structure behind after all requirements are met—never doing less than required.

## Clean up orphans your change creates

When your change replaces or removes a function call, a module import, or a package usage, check with `rg` whether the old function, file, or dependency now has **zero references** in production code. If nothing in production uses it anymore, delete the dead function or file, delete tests that only covered that dead code, and remove the unused package from the dependency manifest in the same change. Cleaning up orphans created by your own edit is finishing the job, not scope creep.

## Do not drift from design or task

Do not autonomously change:

- the target or architecture constraints defined by DESIGN / `Design Source`;
- the behavior, scope, boundaries, interfaces, or acceptance criteria of an approved Plan;
- anything the user explicitly required.

You may decide:

- file layout, internal APIs, and helper decomposition inside the stated boundaries;
- concrete implementation technique;
- test implementation details.

Do not expand scope, bundle unrelated refactors, fix unrelated bugs, or weaken acceptance criteria to make tests pass.

A few easy-to-misjudge boundaries:

- A pre-existing bug unrelated to the current task: record it in `Notes/deviations`; do not fix it on the side.
- The root cause belongs to the current problem, but the fix would exceed approved scope: stop and return the scope decision.
- The Plan did not name a test, but the code reveals a real edge case: add the test and report it.
- Adding or upgrading a dependency: first explain why existing capability is not enough, and list it explicitly in the report.

### Stop on conflict

If a DESIGN cited by `Design Source` is not `Active`, or the authorized source (Proposal/Issue/Plan), Active DESIGN, and actual code conflict with each other, do not redesign on the fly and do not edit the Plan, Proposal, or design documents to make implementation fit. Missing scope authorization or a change that would cross the approved boundary is the same: stop and return the decision instead of expanding or filling in on your own.

Stop with the relevant Plan text, design basis, and `file:line` evidence, then return the decision to the **controller/delegator**:

- if there is a delegator, report it and wait;
- if you are also the controller, switch back to the controlling workflow and decide there.

Use this minimal report format:

```text
STOP
Task: <task>
Found: <conflict + file:line evidence>
Impact: <why the current task cannot continue>
Awaiting: <controller/delegator decision>
```

Whether an approved Plan, Proposal, or DESIGN should change is not an implementation-level decision under this skill. A proposal's `Authorized scope`, planning-time headings, and approval decisions stay read-only throughout implementation.

## TDD

For changes to public commands or user-facing workflows, read the applicable project `AGENTS.md` acceptance contract first. Map each new or changed user behavior to an observable outcome, meaningful failure case, and state-safety invariant; check whether existing tests actually prove those outcomes. Internal unit or mocked collaboration tests prove only their own boundary. When they cannot prove a user can complete the task through the real public entry point, add E2E verification of the complete journey, using isolated resources or real external services as the task requires. Report the test layer, executed commands, observed result, and CI ownership to the controller; a green suite or test filename alone is not acceptance evidence.

Use TDD only when it actually helps define behavior, not mechanically every time a file changes.

With `TDD: true`, follow RED → GREEN → REFACTOR: first write a failing test that checks the new or fixed behavior, then write the smallest implementation that passes, then clean up while tests stay green. Every new test must protect real behavior over time; do not write a throwaway test just to produce one red-green cycle.

With `TDD: false`, do not force a fake failing test. Pick verification that actually proves the change works: existing tests, tests that lock in current behavior, build/typecheck/static checks, integration tests, or smoke checks.

- When deleting obsolete behavior or code, delete tests that only existed to check that deleted behavior. Keep or update tests that still protect remaining behavior. If deletion creates a new external behavior, test that new behavior instead.
- For refactors that keep behavior unchanged, existing tests must stay green. If the old code has no test coverage, first add tests that lock in its current behavior before refactoring; do not manufacture a fake failing test.
- Config, build/CI, metadata, dependency updates, file moves/renames, import cleanup, UI styling, exploratory work, and simple wiring usually do not need TDD, but still need verification that matches the risk.

For a dev-flow Plan, determine the real verification commands for relevant ACs during implementation/Verify and return them in the completion report; the implementer does not write them into the Plan directly. For the direct/Issue route, return the verification commands and results in the report's `DESIGN Sync` block (see below) for the controller to re-verify.

## Bugs: fix the root cause

A bug report usually names a visible symptom. Trace all callers and shared code paths, then fix the single place where the problem actually starts so every caller is fixed at once.

Do not scatter workarounds across callers to hide a shared bug. If fixing the root cause exceeds the current task scope, stop and return the scope decision to the controller.

## Never remove these for brevity

A smaller diff never justifies cutting:

- input validation at trust boundaries;
- error handling that prevents data loss;
- security checks;
- behavior explicitly required by DESIGN, Plan, or the user.

Correct first, simple second.

## Mark deliberate temporary simplifications

If a deliberately simple solution has a known limit (such as in-memory storage or a full scan) that is fine for the current scope, leave one searchable comment:

```text
// simplified: <what was simplified> — <when and how to upgrade>
```

Use this only when there is a real known limit, not on ordinary code.

## Work in small batches

For long tasks, work one Task or one small feature at a time: **implement → verify → report → next batch**. Each batch must be independently verifiable. Record real command outputs right away instead of reconstructing them from memory at the end. When an outer workflow owns git commits and progress files, do not write those states yourself.

## Reports must be verifiable

Return a short report to the controller/requester:

```text
Done: <what was completed>
Touched: <actual files changed>
Verified: <real command> → <real result>
DESIGN Sync: <required, see rules below>
AC Commands: <real commands for relevant ACs>     # for dev-flow Plan Tasks
Skipped: <explicitly skipped work and why>        # only when applicable
Notes/deviations: <boundary notes or deviations>  # only when applicable
```

Do not replace commands and results with “should be fine” or “tests are green.” Report failures as failures.

**`DESIGN Sync` is a required block** the controller uses to close out the delivery; a report missing it, or with it empty, comes back as incomplete. Fill it to match what actually happened, every line backed by real evidence:

```text
DESIGN Sync:
  Worktree: <worktree and branch used; the default isolation tree for direct, the controller-assigned tree for Plan>
  Delivery base: <Git baseline covering the whole delivery (isolation branch start or Delivery Base Commit); a single uncommitted change says working tree>
  Gates: <verify-docset.py --check-sync --base <base> real result (pure refactors add the --pure-refactor reason); plus verify-proposals.py real result when a Proposal was touched>
  Docs synced: <updated owning DESIGN-<module>.md files and the code facts they now carry; for pure internal refactors say none (the reason is already recorded with --pure-refactor in Gates)>
  Drift report: <documentation drift found outside the write set, reported not edited; none if nothing found>
```

Three typical fills: a direct isolated delivery records the worktree, the branch-start baseline, and both gate outputs; a Plan Task records the controller-assigned worktree and the Task scope (AC Commands still listed separately per the Plan); a STOP conflict records only the conflict evidence and the decision being awaited, no gate results. For in-flight legacy Plans, record ownership stays with the Plan itself — this block does not reassign Plan Done.

## Decisions outside implementation

Do not decide product requirements, expand approved scope, rewrite an approved Plan/DESIGN/Proposal, or issue the final review verdict while acting under this skill. When delegated by a controlling workflow, also do not commit code or update Plan/progress records; return the implementation and evidence to the controller. Stop and return higher-level decisions to the controlling workflow. A delegated implementation agent submits code, tests, documentation changes inside the authorized write set, and verification evidence — never approvals, never a self-signed task completion, never Plan Done records; the controller verifies and writes those back.
