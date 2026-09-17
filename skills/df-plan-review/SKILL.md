---
name: df-plan-review
description: >
  Review a Plan before it is executed — if someone follows it literally,
  will it work, and will it deliver the stated goal? Use when the user asks
  to review, check, or verify a Plan or implementation plan before
  execution — especially risky work such as migration, refactoring,
  cross-module changes, or destructive operations, for example "review this
  plan", "check whether this plan will work", "verify the implementation
  plan". Do not use for routine Plans that are already auto-checked on
  submission, for reviewing code (use `df-implement-review`), or for
  writing plans.
---

# df-plan-review — Plan Correctness Review

**You judge one thing: if someone follows this Plan as written, will the work succeed and deliver the stated goal?**

## What you own vs what the script owns

`flow.sh plan check` already gates form: field presence, placeholder text, TDD↔Behavior pairing, checkbox shape, AC command presence, User Validation structure, status validity. Re-checking any of that is waste and produces noise.

Your scope is what a regex cannot compute — whether the parts of this Plan fit together, fit reality, and add up to the goal.

If the Plan is fine, say so quickly and stop. This review is invoked deliberately, not for ceremony.

## The three questions

Every failure that survives `plan check` belongs to one of these:

| | Question | Catches |
|---|---|---|
| Q1 | Do the parts of the Plan fit together? | files nobody produces, symbols nobody creates, ACs nobody owns, order contradicting dependencies |
| Q2 | Are the Plan's statements about the repo true? | stale paths, wrong anchors, false counts, silent clashes with design docs, commands that can't run |
| Q3 | Will executing it deliver the goal? | goal parts without tasks, decisions quietly shrunk, ACs that prove nothing |

A verdict requires all three questions attempted. A Blocker on one question is not permission to skip the others.

## Input

You need the Plan path and the workspace root; everything else you can discover.

- If the prompt carries `review_type: plan`, a Plan path, a Base Commit, and a focus list — use them.
- If the prompt omits context, still proceed: read the Plan, resolve the target project from its `Project Path` metadata, and state the assumptions you had to make in the report.
- **If the Plan declares a Worktree**, the live copy lives inside that worktree, not on the integration branch — read status and checkboxes there, and probe code at the worktree's HEAD.

## How to work: read once, three lists, then verify

Efficiency is part of review quality — a review that burns time returns noise. Work in two passes:

**Pass 1 — read the Plan once, with line numbers.** While reading, fill three lists you will work from later:

1. **Facts** — every concrete claim about the repo: counts, paths, line ranges, doc sections, IDs, commands, flags, "file is new", "file is removed".
2. **Symbols** — every code-like name in backticks, with the task that uses it and the task that should create it.
3. **Files** — every path mentioned anywhere, and where: `## Affected Files` row, `Pre-read`, `Changes`, test path.

**Pass 2 — answer the questions from the lists.** Q1 and Q3 need nothing but the Plan itself. Only Q2 touches the repo; batch its commands and run them together. Do not re-read the Plan between checks — each return to the Plan costs more than it saves.

Verify, don't survey: `test -e` for paths, `sed -n 'Np'` for line anchors, `rg -n` for sections and symbols, `git cat-file` for revisions. Never read a whole design doc to confirm one section. A normal Plan should settle in roughly 15–25 commands; a multi-module Plan may need more, a small one fewer.

Claims you cannot settle go under `Unverified` — never inflated into findings.

## Q1 — Do the parts of the Plan fit together?

Four checks, all from the Plan itself.

1. **Behaviors are owned.** Every entry in Agent Verification must be referenced by some Task's `Verification Intent` — or explicitly marked cross-task. A criterion no task owns is never proven. Also check placement: anything an agent can verify mechanically (tests, lint, typecheck, scriptable checks) belongs in Agent Verification; sitting in User Validation means the Plan pushes automatable work onto the user.
2. **Symbols have producers.** Every code-like name a task *uses* must be created by an earlier task, spelled exactly the same. Cross-task plans break at the seams: Task 2 "registers five error codes A–E", Task 4 "fails fast with `TEMPLATE_MISSING`" — a name nobody ever declared. This is the highest-yield check in the whole review: purely mechanical, done in one pass right after reading, and invisible to form validators.
3. **Behavior specs are real.** For every TDD task, each Behavior must be testable as written — an implementing agent could turn it into a failing test without guessing. Vague descriptions ("works correctly") are unspecified behavior: the implementation agent gets no spec to build against and the RED stage has nothing to fail on. Changes entry 1 must be the RED step (Behaviors → failing tests).
4. **Order matches dependencies.** Every consumer comes after its producer in the declared order. Overlapping work between tasks is a conflict only under declared parallel execution; if the Plan states waves are sequential dependency layers, overlap is the Plan's own design, not a defect.

**Files are expected scope, not a contract.** The `Files` field may hold estimates or N/A, backfilled with actuals at Done; the `Affected Files` table is the expected footprint. Do NOT audit these lists for exact agreement — file-level precision belongs to implementation time, and the Plan intentionally does not pretend to know it. Only flag: an `Affected Files` row declaring an operation that is already false (a "new" file that exists, a "delete" of a file that is absent) — stale premises worth a WARNING — and declared parallel execution that overlaps files (BLOCKER).

Severity: symbol used with no producer → **BLOCKER**; producer spelled differently → **BLOCKER**; producer in a later wave → **BLOCKER**; file overlap under claimed parallel execution → **BLOCKER**. AC owned by nobody → **WARNING**; untestable Behavior claimed as spec → **WARNING**; automatable check sitting in User Validation → **WARNING**; human-observation check claimed as agent-verifiable → **WARNING**; stale file-operation premise → **WARNING**.

## Q2 — Are the Plan's statements about the repo true?

Plans are written against a mental model of the code. When that model is stale, every task built on it inherits the error — and it surfaces mid-execution, after the budget is spent. The repo is the only authority.

Settle each fact claim mechanically. Never wave a claim through because it "looks right":

| Claim | Check |
|---|---|
| "36 capabilities" | count them in the source of truth |
| "`src/x.ts` exists" | `test -e` / `ls` |
| "`file.ts:619-669`" | `sed -n '619p'` at the stated revision — small drift is fine, landing on the wrong construct is not |
| "§3 of DESIGN.md says X" | `rg -n '^#{2,3} ' doc` |
| "D-12" / "issue #45" | find the ID in its source of truth |
| "run `flow.sh verify`" | does the command exist, does it take that flag |
| "create new file F" | does F already exist |
| "delete file F" | does F exist |

**State the revision you checked against** — Base Commit, worktree HEAD, or integration HEAD. A finding without a revision rots the moment anyone commits. If the Plan declares a worktree, check facts at the worktree's HEAD, not the integration branch.

Then check agreement: the Plan cites design docs, `AGENTS.md`, existing interfaces as its basis. For each decision the Plan makes, find what the authority says and compare. Three classes of divergence:

- **Acknowledged** — the Plan says it changes the doc, defers with a reason, or justifies the deviation → a decision, not a defect.
- **Silent** — diverges without saying so → a contract broken without negotiation.

Establish which document is authoritative *for the model this Plan implements* before calling a conflict — older docs sometimes describe a superseded state.

Severity: a false premise the Plan leans on → **BLOCKER**; a false claim a task would wrongly build on → **BLOCKER**; divergence breaking a stated safety/security constraint → **BLOCKER**; an AC command that cannot run in the stated environment → **BLOCKER**. Drift with no effect on the work → **WARNING**; silent divergence from a doc or rule → **WARNING**; cosmetic drift (loose count, ordering) → **INFO**; couldn't settle → `Unverified`, never a finding.

## Q3 — Will executing it deliver the goal?

The expensive failure: a Plan that passes every check and still under-delivers. Four angles.

1. **Goal covered.** Split the Goal into its parts. Each part needs a task. A part with no task is an intention, not a plan.
2. **Decisions delivered.** For each `D-xx`, the tasks deliver what the decision states — not a shadow of it. Watch for shrink words: "v1", "simplified", "static for now", "hardcoded", "placeholder", "stub", "not wired to", "for now". Two tests, in order: does the shrink contradict the Goal or a decision, and is the shrink explicitly sanctioned by a `D-xx` or scope statement (e.g. "this Plan delivers the static layer, dynamic later")? Only a *silent* shrink is a finding — phased delivery is legitimate when the Plan says so.
3. **ACs that can fail.** Under the two-beat scheme, beat-1 entries are criterion-style — that is legal (the real command is written back at the RED stage). What you own: if the feature were broken, would the criterion catch it? An AC that passes either way — "file exists" for a behavior claim, or one that restates the change — is decoration, not verification. A criterion-style AC missing a behavioral pass standard (no observable outcome stated) cannot catch anything.
4. **Handoff possible.** Could the implementer start from this Plan + declared `Pre-read` alone? Interfaces and outputs of earlier tasks must be named, not implied ("calls `parseConfig()` returning `ParsedConfig`" is ready; "uses the shape from Task 2" is not). The bar is "can a competent implementer proceed" — flag only where the missing information would cause a wrong turn.

Severity: goal part with no task → **BLOCKER**; decision quietly reduced → **BLOCKER** (deliver it, or state the phase explicitly); AC that can't fail → **WARNING**; task not startable from Plan alone → **WARNING**. Shrink sanctioned by the Plan's own words → not a finding.

## Don't flag these

- **Form** — field shape, formatting, placeholder style, checkbox layout. `plan check` owns it and it passed.
- **Sanctioned decisions** — anything a `D-xx` or scope statement authorizes. Disagreeing is not a finding.
- **Product intent** — business choices belong to the Plan owner. A requirement that looks wrong goes under `Requirement Questions`, not Blocker/Warning.
- **Taste** — "I would have structured it differently", naming opinions, alternative designs.
- **Unverifiable worries** — "might not handle X" with no evidence from the Plan or repo. Verify it or drop it.
- **Plan size** — task count, file count, wave count are never defects. Context budget is managed per task; a large cohesive Plan is normal. Recommend splitting only when deliverable groups have no dependencies and could be verified independently — and never as a Blocker.

A finding must cite both sides — where the Plan says it, and the reality that contradicts it. Without that, it is at most Info.

## Review budget — at most 2 rounds

Every review session has a hard budget: **the initial review plus at most one re-review (2 verdicts total), then the review closes.** Reviews burn real subscription tokens on both sides — a salami-slicing review cycle that dribbles out one or two findings per round is the most expensive way to reach the same verdict, and it is prohibited.

To make 2 rounds enough:

1. **First review must be exhaustive.** Run all three questions (Q1/Q2/Q3) to completion and report *every* finding you have in one report, including borderline ones you would otherwise "save for later". A report that holds back findings to drip-feed in later rounds is defective service, not thoroughness. Depth per finding matters; withholding findings does not.
2. **On re-review, sweep for regressions AND leftovers, then close.** The re-review verifies the fixes and simultaneously checks the whole Plan again — anything you find in this round is final. There is no round 3 to raise what you missed.
3. **Owner-side duty (Wopal)**: when delegating a review or a re-review, state this budget explicitly in the prompt (e.g. "review budget: 2 rounds max — list ALL findings in this round; no further rounds will occur"). A re-review prompt that does not carry the budget notice invites the drip-feed failure.

If the second round still ends at BLOCK, the review closes with the findings reported — do not keep cycling. The Plan owner decides: fix and re-delegate a *fresh* review (new session), or accept the documented risk. Re-delegating a fresh review after closure is legitimate; silently extending the same session to round 3+ is not.

## Verdict and report

```
PASS   — no Blocker, no Warning
REVISE — no Blocker, at least one Warning
BLOCK  — at least one Blocker
```

`Unverified` never changes the verdict.

At review start, build one todo item per question (Q1/Q2/Q3) and mark them off as you go. All three must be done before any verdict. Out of budget, do not fake completion: emit the report with an explicit `UNCOVERED CHECKS` section naming what was not done and why.

```markdown
# Plan Review — {plan-name}

## Summary
- Review type: Plan
- Verdict: PASS | REVISE | BLOCK
- Counts: Blocker N / Warning N / Info N / Unverified N
- Verified against: {Base Commit | worktree HEAD | integration HEAD}

## Blocker
### B-01: {issue title}
- Plan location: `{plan}.md:{line}`
- Reality: `{file}:{line}` or `{command output}` — {why this contradicts the Plan}
- Impact: {how execution fails}
- Fix direction: {what to add or change}

## Warning
{same format; Impact may be omitted}

## Info
{one line each}

## Unverified
- {claim} — reason not verified: {reason}

## Requirement Questions
{only when the requirement itself is ambiguous and cannot be settled from the Plan and the code}

## Positive Findings
- {verified item: state how it was verified, so the reader can trust the conclusion}

## UNCOVERED CHECKS
{only when a check could not be completed}
```

`PASS` requires a short `Positive Findings` section — what was checked and how. A bare PASS asks the reader to take the verdict on faith, which defeats the purpose of a review.

## After the verdict

- **`REVISE` / `BLOCK`**: the revised Plan must be re-reviewed before it is treated as clean — a fix applied without re-verification is not a fix. Reuse the same review session (reply), so prior findings stay in context.
- **`PASS`**: input to whoever requested the review, not an automatic gate. It does not authorize `approve`, does not replace `plan check`, and does not change the execution status of a Plan mid-flight.
- Reviewing does not authorize editing. Findings go back to the owner.

## References

Load the rubric when a question needs its full procedure, the severity table, or a worked example:

- `references/review-rubric.md` — three-list building, per-question procedures, command cookbook, severity calibration, worked examples (real defect shapes to recognize)

## Examples

### Example 1 — Symbol with no producer (Blocker)

A Plan's Task 4 states a failure branch "fails fast with `TEMPLATE_MISSING`". Task 2 lists the five error codes it registers; the name is not among them. Nothing in the Plan ever declares that code.

```yaml
finding:
  check: Q1_symbols
  severity: blocker
  plan_location: "{plan}.md:{line}"
  reality: "error codes registered at {plan}.md:{line}; TEMPLATE_MISSING absent from that list"
  fix: "add the code to the registration task, or reference an existing code"
```

### Example 2 — False premise (Blocker)

A Plan's premise is "the schema path no longer exists in the ontology, so initialization always fails". Probing the cited file at the stated revision shows the path is still read by one call site the Plan does not mention — the premise is incomplete, and a task built on it would leave that path live.

```yaml
finding:
  check: Q2_facts
  severity: blocker
  plan_location: "{plan}.md:{line}"
  reality: "{file}:{line} still reads the old path"
  revision: "{commit}"
  fix: "name the remaining call site in scope, or remove it in a task"
```

### Example 3 — Not a finding (calibration)

A Plan declares six tasks and states in a decision that it will not split, because the tasks are mutually dependent and context is managed per task. Task count is high.

**Correct handling**: no finding. The decision is explicit and the rationale is sound — size is not a defect, and the single-plan call belongs to the Plan author. Record it as a Positive Finding if useful.