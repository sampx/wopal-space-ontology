---
name: df-implement
description: >
  General code implementation skill. Use when the current task requires changing code or tests to implement
  settled requirements, an approved Plan, existing design, or a bug fix; applies to direct or delegated implementation.
---

# df-implement — Implementation Discipline

You are doing **implementation work**. Deliver the requested change with the smallest reliable, verifiable implementation that stays inside the existing design and task boundaries.

For project/phase work: **DESIGN defines the target, the approved Plan defines this delivery scope, implementation realizes it.**

## Read before writing

Before editing, understand:

- the current task and acceptance criteria;
- the Task's `Design Source` when present, confirming every cited DESIGN is `Status: Active`;
- the Task's `Pre-read`, `Interface`, and `Constraints` when present;
- the relevant call path and callers;
- the current and parent `AGENTS.md` rules.

If you still cannot explain why the proposed change fits the current code, design, and task, keep investigating instead of guessing.

## Minimum implementation order

While preserving design, Plan, correctness, and tests, prefer the simplest option in this order:

1. If the task and acceptance do not require it, do not add it.
2. Reuse an existing repository capability when one already fits.
3. Prefer the standard library when it fits.
4. Prefer native platform capability when it fits.
5. Reuse already-installed dependencies when appropriate.
6. Prefer simple code over new abstraction or dependencies.
7. Add new implementation structure only when the earlier options are insufficient.

A new dependency needs a clear reason existing options are insufficient. “Minimum” means removing unnecessary code after all requirements are satisfied, not doing less than required.

## Do not drift from design or task

Do not autonomously change:

- the target or architecture constraints defined by DESIGN / `Design Source`;
- the behavior, scope, boundaries, contracts, or acceptance of an approved Plan;
- anything the user explicitly required.

You may decide:

- file layout, internal APIs, and helper decomposition inside the stated boundaries;
- concrete implementation technique;
- test implementation details.

Do not expand scope, ride along with unrelated refactors, fix unrelated bugs, or weaken acceptance to make tests pass.

A few easy-to-misjudge boundaries:

- A pre-existing bug unrelated to the current task: record it in `Notes/deviations`; do not fix it opportunistically.
- The root cause belongs to the current problem, but the fix would exceed approved scope: stop and return the scope decision.
- The Plan did not name a test, but the code reveals a real edge case: add the test and report it.
- Adding or upgrading a dependency: first explain why existing capability is insufficient, and surface it explicitly in the report.

### Stop on conflict

If a DESIGN cited by `Design Source` is not `Active`, or the Plan, Active DESIGN, and code reality cannot all hold, do not redesign on the fly and do not edit the Plan/design to make implementation fit.

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

Whether an approved Plan or DESIGN should change is not an implementation-level decision under this skill.

## TDD

Use TDD only when it actually helps define behavior, not mechanically because code changes.

With `TDD: true`, follow RED → GREEN → REFACTOR: first write a failing test that precisely expresses the new/fixed behavior, then implement the minimum needed to pass, then clean up while tests stay green. Every new test must have lasting regression value; do not create a test only to manufacture one RED cycle.

With `TDD: false`, do not invent a failing test. Choose verification that fits the change: existing regression tests, characterization tests, build/typecheck/static checks, integration tests, or smoke checks.

- When deleting obsolete behavior/code, remove tests whose only purpose was to assert that deleted behavior. Keep or update tests that still protect surviving contracts. If deletion creates a new external behavior, test that new behavior instead.
- For pure behavior-preserving refactors, keep existing tests green. If the legacy area lacks a safety net, add characterization/regression tests for current behavior before refactoring; do not manufacture a fake RED.
- Config/build/CI/metadata/dependency work, move/rename/import cleanup, UI layout/style, exploratory work, and glue/wiring usually do not require TDD, but still need risk-appropriate Verify evidence.

For a dev-flow Plan, determine the real verification commands for relevant ACs during implementation/Verify and return them in the completion report; the implementer does not write them into the Plan directly.

## Bugs: fix the root cause

A bug report usually names a symptom. Inspect the relevant callers and shared paths, then fix the point that corrects all affected paths once.

Do not scatter local patches over callers to hide a shared root cause. If the root-cause fix exceeds the current task boundary, stop and return the scope decision to the controller.

## Never remove these for brevity

A smaller diff does not justify weakening:

- input validation at trust boundaries;
- error handling that prevents data loss;
- security controls;
- behavior explicitly required by DESIGN, Plan, or the user.

Correct first, simplify second.

## Mark deliberate temporary simplifications

If a deliberately simplified solution has a known ceiling but is reasonable for the current scope, leave one searchable upgrade note:

```text
// simplified: <current simplification> — <when/how to upgrade>
```

Use this only for a real known ceiling, not as a label for ordinary implementation.

## Work in small batches

For long tasks, work by Task or cohesive behavior group: **implement → verify → report → next batch**. Each batch should be independently verifiable. Capture real evidence immediately instead of reconstructing it from memory later. When an outer controlling workflow owns commits and progress records, do not write those states yourself.

## Reports must be verifiable

Return a short report to the controller/requester:

```text
Done: <what was completed>
Touched: <actual files changed>
Verified: <real command> → <real result>
AC Commands: <real commands for relevant ACs>     # for dev-flow Plan Tasks
Skipped: <explicitly skipped work and why>        # only when applicable
Notes/deviations: <boundary notes or deviations>  # only when applicable
```

Do not replace commands and results with “should be fine” or “tests are green.” Report failures as failures.

## Decisions outside implementation

Do not decide product intent, expand approved scope, rewrite an approved Plan/DESIGN, or issue the final implementation-review verdict while acting under this skill. When delegated by a controlling workflow, also do not commit code or update Plan/progress records; return the implementation and evidence to the controller. Stop and return higher-level decisions to the controlling workflow.
