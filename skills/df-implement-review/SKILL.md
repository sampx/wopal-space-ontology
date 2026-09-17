---
name: df-implement-review
description: >
  Review code changes and implementation work — decide whether the delivered
  result really delivers what it claims, breaks anything that already
  worked, and is sound code. Use when the user asks to review, check, or
  verify code changes, a commit, a pull request, or a finished
  implementation — typically at sign-off before commit or merge, for example
  "review this change", "check whether this implementation is correct",
  "review my PR". Do not use for reviewing a Plan (use `df-plan-review`),
  re-running tests or lint, running builds, or fixing code.
---

# df-implement-review — Implementation Review

## The review answers four questions

Every failure that slips past tests, lint, typecheck, and CI belongs to one of these four.

| | Question | Catches |
|---|----------|---------|
| Q1 | Does the change really deliver what it claims? | stubs, empty shells, unwired code, reduced scope |
| Q2 | Does the change break anything that already worked? | silent behavior changes, broken call sites, drifted contracts |
| Q3 | Are the new code paths correct under real inputs and states? | concurrency bugs, leaks, boundary errors, bad error handling, security holes |
| Q4 | Does the evidence hold up, and what debt does the change leave? | fake tests, untested branches, drifted duplication, wrong abstractions |

## What you own vs what the mechanical gates own

The gates (tests, lint, typecheck, CI) already decided the change compiles, passes, and is formatted. Re-checking any of that is waste. There is exactly one test question you may ask: **does the test actually prove what it claims to protect** (Q4) — never "do the tests pass".

Your scope is what the gates cannot see:

- the change is **real, complete, and reachable**
- the change did not **silently break existing behavior**
- the changed code is **correct under the scenarios its users will hit**

If the change is sound, say so briefly and stop. This review is invoked deliberately, not for ceremony.

## Review mode

Decide once, at the start:

- **Plan-backed** — the prompt includes a Plan path, explicit truths, or acceptance criteria. Verify against those truths, then run all four questions. Explicit constraints in the design docs (DESIGN.md, `docs/`, `AGENTS.md`) count as truths for the pieces they govern.
- **Planless diff** — the prompt only carries a change (file list, working tree, commit, range). Run Q1–Q4 using the change's own stated intent (description, commit message) as the Q1 spec.

In planless mode, do **not** invent product requirements. Business logic belongs to the change owner unless the prompt says `business_logic_review: requested`. Gaps you spot that hinge on product intent go under `Requirement Questions`.

If the prompt omits context entirely, review the narrowest defensible scope — working tree changes under the stated project path — and say so in the report.

Input fields the prompt may carry: `review_type: implementation`, `project_path`, `change_scope: working_tree`, `commit: <hash>`, `commit_range: <A>..<B>`, `background`, Plan path, `design_docs: <path>`, `business_logic_review: requested`.

## How to work: read once, then probe

Efficiency is part of review quality — a review that burns time returns noise. Work in two phases:

**Phase 1 — one read, three lists.** Read the diff and the changed files once. While reading, fill three lists you will probe from later:

1. **Claims** — every deliverable or acceptance criterion the change must satisfy (Plan truths, or the change's own stated intent).
2. **Contract surface** — every exported symbol, signature, schema, shared type, or config the diff modifies, plus every function whose logic changed but signature didn't.
3. **Flags** — anything suspicious to verify in the sweeps (possible stub, possible wiring gap, suspicious test).

**Phase 2 — probe from the lists, never re-read.** Each question below consumes these lists with targeted commands (`rg`, `git diff`, `git show`, `sed -n`). Do not re-scan files you already read. Do not read files outside the change unless a claim or contract edge points there. Mechanical sweeps (stub patterns, skipped tests, dangerous APIs) run as one batch of probes — see the probe bundle in the rubric.

## The four questions

### Q1 — Does the change really deliver what it claims?

Highest-priority check. Most "done but not done" changes die here.

- **Stub sweep.** Scan changed files for placeholder patterns: comment stubs (`TODO: implement`, `HACK:`), placeholder text ("coming soon", "TBD"), empty returns (`return null`, `return {}`, `pass`), log-only handlers, hardcoded fake values, empty event handlers, unconsumed async results, model shells missing the fields the claim needs. Full catalogue with probes: rubric §2.
- **Wiring check.** For every new artifact: is it imported where used, actually referenced, and reachable from an entry point? Component → data source consumed? State → actually rendered? Query result → returned, not discarded? New route → registered?
- **Scope both ways.** Declared scope vs delivered scope (`git diff --name-status`): things promised but absent, things present but undeclared, unannounced deletions.
- **Design conformance.** In Plan-backed mode: check the change against written constraints for the touched area — architecture boundaries, module ownership, API contracts stated as "must"/"shall". A delivery that works but violates a stated constraint has not delivered the design. Narrative descriptions that the change legitimately supersedes are not constraints; when the change supersedes a written decision, it should rewrite that decision (Q4 documentation drift).

Severity: stub occupying a claimed behavior → **BLOCKER**; claimed artifact missing → **BLOCKER**; violation of an explicit Plan truth or design constraint → **BLOCKER**; real but unreachable → **WARNING** (BLOCKER if reachability itself is the claim); undeclared deletion → **WARNING**. Reductions sanctioned by an explicit Plan decision are decisions, not defects.

### Q2 — Does the change break anything that already worked?

This is the check the mechanical gates miss most often. Type checks catch compile breaks; existing tests catch what they cover. What slips through: **silent behavior changes** — same signature, same types, green suite, but different semantics — and breaks in behavior no test covers.

- **Extract the contract surface.** From Phase-1 list 2: every signature, return type, enum value, schema field, shared type, exported constant, config key the diff touches. Include functions whose *logic* changed even though the signature didn't — those are the dangerous ones.
- **Find all consumers.** `rg <symbol>` across the project, **including files outside the diff**. For each consumer, ask: does the change break an assumption this caller holds? Changed return nullability? Changed ordering? Synchronous call made async? Validated input now unvalidated? Behavior-dependent branch rewritten?
- **Check test infrastructure.** If the diff changes a shared fixture, mock, or helper, check whether existing tests that use it now assert something weaker or different.

Scale rule: if a contract symbol has many consumers, list them (`rg -l`), read a representative sample, and state clearly what you did not cover.

Severity: a diff-outside call site broken with a concrete scenario → **BLOCKER**; a semantic change that may be intentional → **WARNING** (or `Serious Logic Risks` when severe); consumers not fully checked → say so under `UNCOVERED STEPS`, don't fake coverage.

### Q3 — Are the new code paths correct under real inputs and states?

Defects live in the branches, inputs, and timings nobody asserted. Walk the changed hunks against the defect pattern catalogue (rubric §4) instead of trusting intuition:

- **Concurrency & state** — races, shared mutable state, non-atomic read-modify-write, re-entrancy, double submission, partial updates without rollback
- **Resource lifecycle** — unclosed handles, cleanup skipped on error paths, connections not returned to the pool
- **Boundaries & numerics** — off-by-one, empty collections, zero/negative inputs, overflow
- **Async** — missing await, floating promises, unhandled rejections, ordering assumptions
- **Error handling** — swallowed exceptions, log-and-continue, errors reported as success, inconsistent state after partial failure
- **Type/runtime seams** — unsafe casts, trusting unvalidated input, nullability assumptions
- **Security** — user input reaching queries/shells/templates unparameterized, `innerHTML`/`dangerouslySetInnerHTML`, unsafe deserialization, missing validation, missing auth on new routes, secrets in code or logs

Report only findings with a concrete failure scenario — "in situation Z this returns Y". Vague worries ("might not handle X") are not findings; ground them or drop them.

Severity: defect with a concrete scenario → **BLOCKER**; exploitable security hole → **BLOCKER**; plausible risk with a concrete scenario → **WARNING**; missing input validation on a public surface → **WARNING**.

### Q4 — Does the evidence hold up, and what debt does the change leave?

Two parts.

- **Test integrity.** When tests changed or a behavior is claimed: map each claimed behavior to its covering tests, then read what they actually assert. Broken patterns: skipped/disabled tests, circular proofs (expected value produced by the code under test), placeholder assertions (`expect(true).toBe(true)`), existence-only assertions, files with no assertions, redundant happy-path tests while real branches stay untested. Severity: skipped/disabled/circular/placeholder for a claimed behavior → **BLOCKER**; no assertions in a file or all-weak → **WARNING**; untested changed branch → **WARNING**.
- **Documentation drift.** Reuse the Q2 contract surface: for every changed external contract (API, schema, CLI flag, config key, behavior semantics), find where docs describe it (`docs/`, `README`, `AGENTS.md`, public docstrings) and check whether the change updated them. The change makes documentation stale or false → **WARNING** (REVISE — the fix is updating docs); violating a stated docs-sync rule in `AGENTS.md` → **BLOCKER**. If the project's docs are outside the repo you can see, note it under `Needs Human`. Pure internal refactors with no contract change trigger nothing.
- **Debt.** Check the change against the project's `AGENTS.md` and established patterns. Real debt signals (rubric §5): wrong abstraction layer, circular module dependencies, god modules, asymmetric APIs (get without set, open without close), copy-paste that already diverged, magic numbers or hardcoded environment assumptions, over-engineering for requirements that don't exist, dead code, commented-out blocks. Severity: violates a stated safety/security constraint → **BLOCKER**; convention breaks and real debt growth → **WARNING**; dead code / TODOs → **INFO** (WARNING when they mask a claimed behavior). Taste preferences are not findings.

## Scale: Quick vs Full review

- **Quick** — the diff is small (roughly ≤ 50 lines, one file, local change): run all four questions but with a few probes each, skipping rubric lookups; build one todo item; emit the short report form.
- **Full** — everything else: one todo item per question, rubric open when a question hits unfamiliar territory, full report.

Never skip Q2 even on small diffs — a 10-line signature change can break a hundred call sites.

## False-positive calibration

Review noise is flagging things that aren't defects. Do not flag: what the gates already own; product preferences (use `Requirement Questions` when it matters); style nits without a correctness or maintenance consequence; "I would have designed it differently"; unverifiable worries without a scenario; scope you were not asked to review; sanctioned reductions. Every finding must cite a location and the evidence that supports it — otherwise it is at most Info.

## Yardstick for severe logic risks

If you find a plausible severe logic risk (irreversible destruction, major data corruption, user harm) with concrete `file:line` evidence that could still be requirement-driven or intentional, do not silently classify it as a bug. Report it under `Serious Logic Risks (Discuss with User)`. It does not change the verdict unless the prompt requested business-logic validation or an explicit Plan truth is contradicted.

## Verdict and report

Verdicts follow the dev-flow standard, so the report plugs into existing gates:

```
PASS   — no Blocker, no Warning
REVISE — no Blocker, at least one Warning
BLOCK  — at least one Blocker
```

`Needs Human`, `Serious Logic Risks`, and `Requirement Questions` never change the verdict by default.

All four questions must be attempted before any verdict — do not stop at the first Blocker; a Blocker is a severity, not permission to skip the rest. If budget runs out, do not fake completion: emit the report with an explicit `UNCOVERED STEPS` section naming what was not done and why.

## Review budget — at most 2 reviews per change

Rook reviews each change (or each Plan) at most **twice**: the initial review plus at most one re-review; the re-review report is final.

1. **First review must be exhaustive**: run all four questions (Q1–Q4) and report every finding in one report, including borderline ones. Withholding findings is defective service.
2. **Re-review = verify fixes + full re-sweep**: anything found this round is final — there is no further round to raise what was missed.

**Full report:**

```markdown
# Implementation Review — {scope label}

## Summary
- Review type: Implementation (Plan-backed | Planless diff)
- Verdict: PASS | REVISE | BLOCK
- Counts: Blocker N / Warning N / Info N / Needs-human N
- Reviewed: {Plan path / commit / commit range / working tree}

## Blocker
### B-01: {title}
- Location: `{file}:{line}`
- Evidence: {code snippet or command output}
- Impact: {what fails, under which scenario}
- Fix direction: {what to change — concrete, not "improve it"}

## Warning
{same format as Blocker; Impact may be omitted}

## Info
{one line each}

## Serious Logic Risks (Discuss with User)
{only severe risks that may be requirement-driven}

## Requirement Questions
{only ambiguity or product choices code alone cannot judge}

## Needs Human
- {item} — why only human observation can settle it

## Positive Findings
- {verified item: state how it was verified}

## UNCOVERED STEPS
{only when steps could not be completed}
```

**Quick report:** `Summary` (same fields) + one merged `Findings` list (B/W/I labelled) + `Positive Findings`.

A `PASS` requires the `Positive Findings` section to state what was checked and how — a bare PASS asks the reader to take the verdict on faith.

## After the verdict

- **REVISE / BLOCK**: the fix must be re-reviewed before the result counts as clean — a fix applied without re-verification is not a fix. Reuse the same review session (reply), so prior findings and their resolutions stay in context; a fresh reviewer loses them.
- **PASS**: this is an input to whoever requested the review, not an automatic gate. It does not authorize merge or completion, and it does not replace the mechanical gates.
- Reviewing does not authorize editing. Findings go back to the implementer.

## References

Load the rubric when a question needs its detailed method, a pattern catalogue, or a worked example:

- `references/review-rubric.md` — phase-1 list building, stub patterns with probes, Q2 contract-surface procedure, Q3 defect catalogue, Q4 debt signals, the probe bundle (one paste, all mechanical sweeps), severity calibration, worked examples