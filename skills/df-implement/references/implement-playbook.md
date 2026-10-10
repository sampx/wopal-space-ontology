# Implementation Playbook

The method lives in `SKILL.md`; this file holds the boundary cases, worked
examples, and wiring details you need when a situation is not routine.

## Contents

1. Plan fidelity boundary cases — what is yours, what needs a report line, what stops the task
2. Worked ladder climbs
3. TDD wiring inside a dev-flow Plan Task
4. The deviation protocol — stop-and-report format
5. How your evidence report feeds the review

---

## 1. Plan fidelity boundary cases

Three verdicts exist: **OK** (implementation freedom — just do it),
**REPORT** (do it or note it, but the report must surface it),
**STOP** (halt the task, hand the decision back to the delegator).
Anything labeled forbidden means: doing it silently is the failure, not
the act itself.

| Situation | Verdict | Why |
|---|---|---|
| Plan says "add input validation"; the natural shape needs a small helper | OK | Internal decomposition is rung-7 freedom |
| Plan's Design names module A; the code would sit more naturally in module B | STOP | Module ownership is a stated constraint. If the boundary itself looks wrong, that is a Plan revision, not your call |
| A helper you need already exists in the repo, but the Plan never mentions reusing it | OK, reuse | Ladder rung 2 overrides Plan silence; note it in the report |
| You find a pre-existing bug adjacent to your task | REPORT | Note it in `Notes/deviations`; do not fix unless asked — scope belongs to the delegator |
| The task's own bug has its root cause outside the declared files | REPORT, then fix with consent | Root-cause rule applies, but crossing the declared file boundary is a scope change → get a one-line go-ahead |
| The Verify command fails after two honest attempts | STOP | Two failures means the design or the environment is wrong, not your effort. Report with both outputs |
| The Design assumes an API capability the code does not have | STOP | The Plan cannot hold as written; improvising a substitute is "the spirit of the Plan" |
| Two acceptance criteria contradict each other | STOP | Contradiction is unresolvable at implementation level |
| The data model cannot carry the planned behavior | STOP | Schema-level gap → Plan revision |
| A dependency upgrade would satisfy the requirement cleanly | REPORT | Allowed with a written rung-5 justification; upgrades change the lockfile — surface it |
| Performance shortcut with a known ceiling (global lock, O(n²) scan) | OK with marker | `// simplified:` one-liner with the upgrade path |
| Cutting validation, error handling, or security for brevity | Forbidden | Never simplify away — no marker makes it legal |
| Loosening an acceptance criterion so the test passes | Forbidden | A passing test that asserts less than the Plan asked is a failed delivery wearing green |
| Refactoring adjacent code "while you're here" | Forbidden | Riding-along refactors pollute the review diff; propose it as a follow-up |
| Test implementation detail (fixture style, assertion form) | OK | Tests must exist first and pin behavior; their style is yours |
| Adding a test the Plan did not list, because the code revealed an edge | OK | Tests guarding real behavior are never scope creep — add to the report |

**The pattern behind the table**: constraints the Plan *stated* are walls;
everything the Plan *did not state* is yours; anything that makes the Plan
*not hold as written* is a stop.

---

## 2. Worked ladder climbs

Each example: the ask → the climb → where it lands → the report line.

**"Add rate limiting to this endpoint."**
Climb: rung 1 — is a rate limit in the Plan's acceptance criteria? Yes →
not skippable. Rung 2 — `rg -il "rate.?limit"` finds the gateway already
has a throttling middleware with per-route config. Land: register the
route in the existing limiter's config, ~3 lines. Report:
`Done: rate limit via existing gateway throttle middleware (config-only, 3 lines). Skipped: nothing — rung 2 reuse.`

**"Parse the uploaded YAML config and validate required fields."**
Climb: rung 3 — the language's stdlib YAML parser handles parsing. Rung 1
on validation — required-field checks are trust-boundary input validation
(never simplify away), so they get written even though no library does
domain-specific required fields. Land: stdlib parse + 10 lines of explicit
required-field checks. Report:
`Done: stdlib yaml parse + explicit required-field validation. Skipped: config schema library — 10 lines did not justify a dependency.`

**"Cache these API responses."**
Climb: rung 1 first — is a cache in the Plan? If the Plan says "add a
cache", it exists. Rung 5 — the HTTP layer already installed has response
caching with TTL options. Land: enable it with a TTL, ~2 lines of config.
Rung 7 (a hand-rolled cache class) never gets reached. Report:
`Done: response cache via <installed layer>, TTL 60s. Skipped: custom cache class — add if the installed cache measurably falls short.`

**"Fix: users sometimes see stale totals after a purchase."**
Climb: symptom is "stale totals"; root cause candidates are the read path,
the write path, or a cache layer. `rg` the totals function's callers before
touching anything → the write path skips invalidating one cache key. Land:
add the one invalidation line where all purchase paths route through —
not a refresh band-aid on the totals read path. Report names the root
cause with `file:line` of both the gap and the fix.

The reflex to internalize: every climb starts at rung 1 with the Plan's
acceptance criteria in hand, and every landing is describable in one line.

---

## 3. TDD wiring inside a dev-flow Plan Task

A dev-flow Task arrives pre-structured for TDD. The Changes list's first
entry is always RED. The full loop:

```text
1. RED    — write the failing test from the Behavior spec. Run it.
           Confirm it fails for the RIGHT reason (assertion fails,
           not import error / typo).
2. Write-back — at RED stage, turn the Task's acceptance criteria
           into real commands and write them back into the Plan in
           place (the two-beat AC contract: criterion-style ACs
           cannot pass `complete` later; the command must exist now).
3. GREEN  — minimum code that passes. Climb the ladder while writing
           it; the test does not move.
4. REFACTOR — clean up with tests green; adjust tests in step if the
           refactor changes what they pin.
5. Verify — run the Task's Verify command. It must pass.
6. Done   — tick the Task's Done checkbox, backfill the
           actually-touched files, commit (one commit per Task).
```

Rules that bite in practice:

- **RED must fail for the right reason.** A test that errors on an import
  is not a failing test; it is a broken test. Fix the harness first, then
  watch the assertion fail.
- **No implementation before RED is red.** Writing the fix first and the
  test after is how tests become tautologies.
- **`TDD: false` still leaves one runnable check** — an assert-based
  self-check or one small test. Trivial one-liners are the only full
  exemption.
- **The AC write-back is not optional.** Forgetting it means `complete`
  hard-gates later and someone must come back to do RED-stage work after
  the code is green — the most expensive possible order.

---

## 4. The deviation protocol — stop-and-report format

Three things trigger a stop: the Plan cannot hold as written (design gap,
contradiction, missing capability), the root-cause fix exceeds the
declared scope, or you have failed the same Verify twice. Anything else
fits in the report's `Notes/deviations` line.

When you stop, use this format so the delegator can decide in one read:

```text
STOP — Plan deviation

Task: <task name / behavior group>
Found: <what contradicts the Plan, with file:line evidence>
Why the Plan can't hold: <one short paragraph — the mechanism, not a story>
Options:
  A. <path> — cost: <diff size / what changes>
  B. <path> — cost: <...>
Awaiting: plan revision or a chosen option.
```

What you must **not** do instead: improvise a substitute design, quietly
implement "the spirit" of the requirement, inflate the diff to force the
Plan to work, or keep coding past the discovery "to have something to
show". A stopped task with a crisp deviation report is a successful task —
the failure mode is the deviation nobody heard about until review.

Boundary cases worth noting but not worth stopping for go in the report:

```text
Notes/deviations: reused existing <X> (Plan silent on reuse); found
pre-existing bug in <Y> at file:line — not fixed, out of scope.
```

---

## 5. How your evidence report feeds the review

The reviewer (rook, via df-implement-review) works from what you hand
back. Each line of your report has a consumer:

| Your line | Review consumer | What goes wrong if you fake or skip it |
|---|---|---|
| `Touched` | Q1 scope check (`git diff --name-status` vs declared) | Files you touched but omit → "undeclared change" WARNING |
| `Verified` | Q4 test integrity — commands are re-runnable evidence | A green claim without a command is treated as unverified |
| RED-stage AC write-back | `complete` hard gate + Agent Verification | Missing commands block the whole Plan later |
| `// simplified:` markers | Lean sweep — become sanctioned INFO, not bloat findings | Unmarked shortcuts read as unflagged debt → REVISE |
| `Skipped` line | Lean count (`net: -N lines possible`) | Nothing — it is upside; omit only when nothing was skipped |
| Deviation notes | Requirement Questions / context | Undisclosed deviations found by review → BLOCK, not WARNING |

The one-test floor is protected on both sides: the review never flags
your single smoke test as bloat, and you never skip it. Zero tests on
non-trivial logic is a WARNING with your name on it.

Write the report as you go — after each batch — not from memory at the
end. The report written from memory is where files get omitted and
commands get invented.
