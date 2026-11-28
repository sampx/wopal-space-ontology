---
name: df-implement-review
description: >
  Independent review and verification of delivered code, tests, design documents and
  engineering rules across the full change or delivery baseline. Use for
  implementation, commit, PR, delivery quality or repository debt reviews.
  Pre-implementation proposal and Plan review belongs to df-proposal-review.
---

# Implementation Review

## Authority and review scope

A Proposal-driven delivery is judged against the current user-approved Proposal: its goals, design decisions, authorized scope, acceptance criteria, and unchanged governing design constraints. The Plan organizes execution within that scope. An Issue authorizes work within a settled design; legacy in-flight Plans retain their original contract. Confirm explicit user decisions made during testing or validation, even when the Proposal has not yet been updated. A present-state DESIGN is a delivered artifact, not a substitute for the Proposal target.

Review and verify independently without modifying delivery artifacts. Find the actual authorization, applicable rules, delivery baseline, governing architecture, affected DESIGNs and glossary/companion contracts before judging. Use these sources and explicit user decisions to understand the product's purpose, target users, deployment and usage scale, trust boundaries and current stage; do not assume requirements from other products or future scenarios.

Align review with the minimal implementation principle in `df-implement`: deliver reliably within the settled design and real usage scenarios. Prioritize whether users can complete their tasks, important behavior is correct, and necessary risk controls work. Accept reasonable simplifications within the current scope. Do not use correctness, security, performance or testing to justify unauthorized requirements, excessive defenses, abstractions or low-value fixes. Findings themselves must follow the minimalism principle: explain their practical value and prefer the smallest direct, reliable correction; refer necessary changes to settled design to the user.

- **Delivery review:** check all authorized behavior across the whole delivery.
- **Change review:** check the requested diff, governing decisions and affected contracts; do not enlarge its scope.
- **Repo audit:** when asked for whole-repository debt rather than a delivery, use the Q4 debt sweep in the rubric, with ranked actionable cuts.

Use the supplied `delivery_base` or recorded branch-start baseline; inspect the full diff `git diff <delivery-base>...HEAD` and any explicitly included uncommitted changes. A single working-tree change may use its diff directly. Never substitute the latest commit for a multi-commit delivery. If the baseline is missing, resolve it with the controller; if unavailable, disclose coverage limits.

## Review method

Read the full diff within the review scope once, list claims, changed contracts and suspicious paths, then trace callers and probe targeted evidence. Open `references/review-rubric.md` for detailed checks. Choose review depth by real business impact and risk, not by exhaustively enumerating defect patterns; complete all four checks before issuing a verdict or disclose what could not be completed. When a problem is found, trace its common root cause, affected similar operations and direct call chains in the same round; merge findings to cover the full repair boundary and key acceptance scenarios. Do not stop at the first defect or expand scope to increase the finding count.

| Question | Check |
|---|---|
| Q1 — Is the target delivered? | Compare current authorization with real behavior in both directions: missing or unwired features, scope additions, exclusions, placeholders and false completion claims. |
| Q2 — Does existing behavior still work? | Trace affected public/internal contracts, callers outside the diff, shared data and test fixtures. Identify concrete regressions, not hypothetical redesigns. |
| Q3 — Is the implementation correct? | Follow real inputs and state transitions, including errors, concurrency, lifecycle, validation, authorization, privacy and resource cleanup. |
| Q4 — Do tests and delivery artifacts substantiate the result? | Check meaningful assertions, required coverage, actual gate evidence, documentation and rules, and newly orphaned code/dependencies. |

Prefer verifying delivery through observable behavior, then use code review to explain or locate defects. Choose the lowest-cost verification sufficient to prove the behavior under the authorized acceptance criteria and `rules/testing.md`: verify existing evidence and actually run applicable targeted tests, replays, CLI/API or UI checks for key behavior and suspicious or missing evidence. Verify public operations from real entry points to observable outcomes, meaningful failures and state-safety invariants; mocked internals alone are not end-to-end proof. Reuse existing project tests and isolated environments; respect user authorization and project environment constraints, keep temporary verification artifacts out of delivery source, and do not access unauthorized real accounts, data or production services. A regression test must fail if the protected behavior breaks. Do not rerun all gates just to repeat CI. Record actual execution, observations and unverified items; distinguish not verified, environment blockers and product failures.

### Verify the delivery artifacts in order

1. **Proposal → implementation.** Compare approved design decisions, governing unchanged constraints, goals, behavior, scope and acceptance criteria with code and tests in both directions; trace material ownership, dependencies, interfaces, state, defaults, failures and risk controls to real behavior and proof; account for explicit user-authorized adjustments. Report target deviations and identify whether code or Proposal needs correction. Do not authorize an unapproved change by rewriting the Proposal to match code.
2. **Code → present-state DESIGN.** Verify affected project/module DESIGNs accurately describe delivered interfaces, business rules, responsibilities and failure behavior. Check any affected glossary, including missing required synchronization, under `dev-doc-master/references/glossary.md`; compare canonical terminology and definitions against the authorized target and actual delivered design, without requiring vocabulary-only churn. Load `dev-doc-master` for its actual SOP, required semantic coverage, newcomer readability, evidence and Slop Checklist. Verify the full-baseline doc gate and any `--pure-refactor` claim against actual changes.
3. **DESIGN → engineering rules.** Load `space-master` and its AGENTS.md maintenance standards. Inspect all affected tiers (project, module, directory, docs, scripts and other applicable rules), including unchanged rules invalidated by the delivery. Check rules against implementation, DESIGN and each other, as well as scope, ownership, references, executable gates, durable constraints, required language versions and all applicable SOP/quality requirements. Check omitted necessary updates as well as changed files. Respect parallel write sets and report shared-document conflicts to the controller.

For Proposal lifecycle, use `dev-proposal`: update an approved, unaccepted Proposal in place for explicit user-authorized adjustments. Verify the current document incorporates decisions coherently. Keep historical protection: full delivery and user acceptance before migration; required supersession links/disposal; never demote implemented decisions or edit frozen archives.

For ontology capability deliveries, also check applicable asset standards: required frontmatter, trigger scope, workflow clarity, reference integrity, localized consistency and capability-specific rules. Use the governing SOP rather than duplicating its checklist.

## Severity

Classify each finding once by its actual nature and impact. Require a source location, concrete evidence, reachable triggering conditions, affected user behavior or constraint, and actual consequences; do not require a Proposal clause to prove a real bug. Proving a defect exists is not the same as proving it should block delivery. Judge against actual deployment, input sources, likelihood, consequences, existing safeguards and repair cost; do not dismiss real high-consequence security risks because they are unlikely. Do not demand fixes for merely extreme assumptions, issues without practical impact, or issues with insufficient repair benefit.

- **Blocker:** evidence shows a defect prevents reliable completion of important current promised behavior, causes a material business regression or serious stability, data, security or privacy consequences, or involves fake implementation/test/verification evidence or false completion; for business Proposal-driven delivery, material unauthorized departure from approved design decisions or unchanged governing architectural constraints, whether or not the code works; confirmed violations of affected DESIGN, glossary or rule consistency or their governing mandatory quality standards (including omitted required sync), failure of a required gate; unauthorized edits to protected historical records, false lifecycle claims or write-set violations. Explain why the issue cannot ship. Do not present wording preferences, internal implementation details or theoretical risks as mandatory standards.
- **Warning:** a defect with clear practical impact worth correcting but not severe enough to block delivery; a noncritical target discrepancy, a user-authorized change not yet incorporated into the Proposal, or a maintenance or test-coverage issue with practical value. Noncritical unauthorized drift still requires correction or explicit user decision; ordinary implementation freedom is not drift. Explain the benefit of correcting a Warning; the controller may accept it and record follow-up under the owning workflow. Do not list low-value issues as Warnings or duplicate an independently established Blocker.
- **Info / suggestion:** useful technical tradeoffs, selection alternatives or design concerns that are not defects. Omit noise and unsupported suspicions. Accepted limitations and ordinary correct technical behavior are not findings.

Do not inflate a target discrepancy into a code defect, or overlook a confirmed violation of mandatory standards because the code works. Confirm conventional semantics before flagging them (e.g. severity thresholds intentionally suppress lower-level logs). A question of product intent is a question for the user, not a proven bug. Clearly qualify unverified serious risks. Do not report limitations allowed by the design; if the current design's risk controls are clearly inadequate, refer that as design feedback to the user rather than unilaterally raising implementation review standards.

## Report

Write in the user's preferred language for a human decision first. Explain plainly what the user will encounter, why it is worth fixing now and whether it affects delivery, then provide file/line evidence for the implementer. State the minimum repair outcome and observable acceptance criteria. Merge findings with the same root cause; do not prescribe a new architecture when a small correction suffices.

```markdown
# Implementation review
Scope: {baseline and authority}
Verdict: PASS | REVISE | BLOCK ({N} Blocker / {N} Warning)

## Blocker
### B-01: {plain-language problem}
- Location: {file:line}
- Problem: {evidence, governing basis if applicable, concrete impact}
- Fix: {required outcome}
- Acceptance: {observable check}

## Warning
### W-01: {problem}
{same information, compactly}

## Verification results
{key behavior, actual verification methods and outcomes; explicitly mark items not executed}

## Other notes
{only necessary user decisions, human validation, unverified scope or limitations}
```

Omit empty sections. Info, positive findings and technical suggestions together take at most one or two sentences; on PASS briefly state what was verified. Explicitly disclose uncompleted checks; never imply exhaustive coverage or a verified pass when material scope was not reviewed. No internal reasoning trace, process history, or superseded findings.

PASS: no Blocker or Warning in the covered scope; non-blocking suggestions are allowed. REVISE: Warning(s) worth revising but no Blocker; the controller may record accepted Warnings and conditionally pass under the owning workflow. BLOCK: at least one Blocker. Technical suggestions, accepted limitations and pending human-only checks are not defects by themselves; state remaining acceptance limitations. For repo audit, provide ranked concise findings and realistic net reduction when supported.

## After review

The reviewer does not edit or approve delivery. Return findings to the controller/implementer. Complete all applicable checks and report all issues of practical value in the first round. In the second round verify only reported issues and the direct impact of fixes against the same authority, prioritizing agreed acceptance criteria; do not restart the full review. Aim for convergence within two rounds. If not converged, distinguish unresolved original defects, new regressions and first-round omissions; consolidate remaining material issues for the controller. Follow round limits in the owning workflow (e.g. `dev-flow`); if none applies, let the controller decide whether to continue after two rounds. At the limit, stop automatic review cycles and refer the decision to the user. Do not conceal material risks or reopen review for minor issues. The controlling workflow owns user acceptance and integration.

## References

- `references/review-rubric.md` — detailed probes, evidence, tests, documentation and debt review.
- `df-implement`, `rules/testing.md` — minimal implementation and risk-proportionate verification.
- `dev-proposal` — Proposal authorization and lifecycle.
- `dev-doc-master`, `space-master` — governing documentation and rule quality standards.
