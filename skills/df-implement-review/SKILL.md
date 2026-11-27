---
name: df-implement-review
description: >
  Independent read-only review of delivered code, tests, design documents and
  engineering rules across the full change or delivery baseline. Use for
  implementation, commit, PR, delivery quality or repository debt reviews.
  Pre-implementation proposal and Plan review belongs to df-proposal-review.
---

# Implementation Review

## Authority and review scope

A Proposal-driven delivery is judged against the current user-approved Proposal: its goals, design decisions, authorized scope and acceptance criteria. The Plan organizes execution within that scope. An Issue authorizes work within a settled design; legacy in-flight Plans retain their original contract. Confirm explicit user decisions made during testing or validation, even when the Proposal has not yet been updated. A present-state DESIGN is a delivered artifact, not a substitute for the Proposal target.

Review independently and read-only. Find the actual authorization, applicable rules, delivery baseline and affected DESIGNs before judging. Do not invent product requirements or treat a personal preference or a conventional technical choice as a defect.

- **Delivery review:** check all authorized behavior across the whole delivery.
- **Change review:** check the requested diff, governing decisions and affected contracts; do not enlarge its scope.
- **Repo audit:** when asked for whole-repository debt rather than a delivery, use the Q4 debt sweep in the rubric, with ranked actionable cuts.

Use the supplied `delivery_base` or recorded branch-start baseline; inspect the full diff `git diff <delivery-base>...HEAD` and any explicitly included uncommitted changes. A single working-tree change may use its diff directly. Never substitute the latest commit for a multi-commit delivery. If the baseline is missing, resolve it with the controller; if unavailable, disclose coverage limits.

## Review method

Read the full diff once, list claims, changed contracts and suspicious paths, then trace callers and probe targeted evidence. Open `references/review-rubric.md` for detailed checks. Scale depth to change size; attempt all four questions before issuing a verdict.

| Question | Check |
|---|---|
| Q1 — Is the target delivered? | Compare current authorization with real behavior in both directions: missing or unwired features, scope additions, exclusions, placeholders and false completion claims. |
| Q2 — Does existing behavior still work? | Trace affected public/internal contracts, callers outside the diff, shared data and test fixtures. Identify concrete regressions, not hypothetical redesigns. |
| Q3 — Is the implementation correct? | Follow real inputs and state transitions, including errors, concurrency, lifecycle, validation, authorization, privacy and resource cleanup. |
| Q4 — Do tests and delivery artifacts substantiate the result? | Check meaningful assertions, required coverage, actual gate evidence, documentation and rules, and newly orphaned code/dependencies. |

Do not rerun every compiler, formatter or test gate just to repeat CI. Verify reported results and spot-check suspicious or missing evidence; distinguish not verified from failed. For public workflows, follow the real entry point to an observable outcome, meaningful failures and state-safety invariants; mocked internals alone are not end-to-end proof. A regression test must fail if the protected behavior breaks.

### Verify the delivery artifacts in order

1. **Proposal → implementation.** Compare current approved goals, behavior, scope and acceptance criteria with the code and tests; account for explicit user-authorized adjustments. Report target deviations and identify whether code or Proposal needs correction. Do not authorize an unapproved change by rewriting the Proposal to match code.
2. **Code → present-state DESIGN.** Verify affected project/module DESIGNs accurately describe delivered interfaces, business rules, responsibilities and failure behavior. Load `dev-doc-master` for its actual SOP, required semantic coverage, newcomer readability, evidence and Slop Checklist. Verify the full-baseline doc gate and any `--pure-refactor` claim against actual changes.
3. **DESIGN → engineering rules.** Load `space-master` and its AGENTS.md maintenance standards. Inspect all affected tiers (project, module, directory, docs, scripts and other applicable rules), including unchanged rules invalidated by the delivery. Check rules against implementation, DESIGN and each other, as well as scope, ownership, references, executable gates, durable constraints, required language versions and all applicable SOP/quality requirements. Check omitted necessary updates as well as changed files. Respect parallel write sets and report shared-document conflicts to the controller.

For Proposal lifecycle, use `dev-proposal`: update an approved, unaccepted Proposal in place for explicit user-authorized adjustments. Verify the current document incorporates decisions coherently. Keep historical protection: full delivery and user acceptance before migration; required supersession links/disposal; never demote implemented decisions or edit frozen archives.

For ontology capability deliveries, also check applicable asset standards: required frontmatter, trigger scope, workflow clarity, reference integrity, localized consistency and capability-specific rules. Use the governing SOP rather than duplicating its checklist.

## Severity

Classify each finding once by its actual nature and impact. A source location, concrete evidence and reason are required; do not require a Proposal clause to prove a real bug.

- **Blocker:** a demonstrated functional defect, broken promised behavior due to a code bug, regression, security/privacy defect, fake implementation/test/verification evidence or false completion; any inconsistency between code and present-state DESIGN, between DESIGN and affected rules, or among affected rules; any failure of affected DESIGNs or rules at any tier to satisfy their governing skill SOP or quality requirements (including omitted required sync); unauthorized edits to protected historical records, false lifecycle claims or write-set violations. A minor-looking mandatory document/rule violation is still a Blocker.
- **Warning:** a discrepancy between Proposal target and implementation, without an independently established Blocker. This includes a user-authorized change not yet incorporated into the Proposal and unauthorized target drift; the latter remains unapproved and must be corrected or explicitly decided by the user. Also report actionable non-blocking maintenance or test-coverage gaps that do not violate mandatory quality rules. If a discrepancy independently causes a bug or artifact inconsistency, classify that actual defect as Blocker instead of duplicating it.
- **Info / suggestion:** useful technical tradeoffs, selection alternatives or design concerns that are not defects. Omit noise and unsupported suspicions. Accepted limitations and ordinary correct technical behavior are not findings.

Do not inflate a target discrepancy into a code defect, or downgrade a real documentation/rule quality failure because the code works. Confirm conventional semantics before flagging them (e.g. severity thresholds intentionally suppress lower-level logs). A question of product intent is a question for the user, not a proven bug. An unresolved potentially serious risk must be clearly qualified, not presented as a verified defect.

## Report

Write in the user's preferred language for a human decision first, with enough file/line evidence for the implementer. Use plain, concrete wording: what happens, why it matters, what needs correcting and how to prove it. Merge findings with the same root cause. Do not prescribe a new architecture when a small correction suffices.

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

## Other notes
{only necessary user decisions, human validation, unverified scope or limitations}
```

Omit empty sections. Info, positive findings and technical suggestions together take at most one or two sentences; on PASS briefly state what was verified. Explicitly disclose uncompleted checks; never imply exhaustive coverage or a verified pass when material scope was not reviewed. No internal reasoning trace, process history, or superseded findings.

PASS: no Blocker or Warning in the covered scope. REVISE: Warning(s) but no Blocker. BLOCK: at least one Blocker. Neither technical suggestions nor unresolved human-only checks are automatically defects; state any remaining acceptance limitations. For repo audit, provide ranked concise findings and realistic net reduction when supported.

## After review

The reviewer does not edit or approve delivery. Return findings to the controller/implementer. Re-review fixes and their direct impact against the same authority; aim for convergence in two rounds without withholding grounded findings or reopening accepted choices. The controlling workflow owns user acceptance and integration.

## References

- `references/review-rubric.md` — detailed probes, evidence, tests, documentation and debt review.
- `dev-proposal` — Proposal authorization and lifecycle.
- `dev-doc-master`, `space-master` — governing documentation and rule quality standards.
