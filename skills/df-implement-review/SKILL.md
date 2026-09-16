---
name: df-implement-review
description: >
  Review code changes and implementation work — determine whether the
  delivered result actually does what it claims and whether the code is
  sound. Use when the user asks to review, check, or verify code changes, a
  commit, a pull request, or a finished implementation — typically at
  sign-off before commit or merge, for example "review this change", "check
  whether this implementation is correct", "review my PR". Do not use for
  reviewing a Plan (use `df-plan-review`), re-running tests or lint,
  running builds, or fixing code.
---

# df-implement-review — Implementation Correctness Review

**Your question is not "do the tests pass" — it is "if this change ships as written, does it deliver what it claims, and is it sound code".**

## Position: what the mechanical gates own vs what you own

Tests, lint, typecheck, and CI already gate form: the suite runs, the code compiles, formatting passes, static checks are clean. Re-checking any of that is waste and produces noise.

Your scope is **what those gates cannot see** — whether the change is real, complete, reachable, and safe under the scenarios its users will actually hit.

| The mechanical gates decide | You decide |
|---|---|
| Tests pass | Whether the tests **prove the claimed behavior** |
| The code compiles and lints | Whether the changed code is **correct, reachable, and safe** |
| The diff is syntactically valid | Whether the diff **delivers the declared goal**, not a reduced version |
| — | Whether everything declared was **actually delivered** |

If the change is sound, say so quickly and stop. This review is invoked deliberately, not for ceremony.

## Review Modes

Determine the mode before reviewing:

| Mode | Trigger | Primary responsibility |
|------|---------|------------------------|
| **Plan-backed review** | Prompt includes a Plan path, explicit truths, or acceptance criteria | Verify the implementation against those truths + full technical scan |
| **Planless diff review** | Prompt includes a change carrier (changed files, working tree diff, commit, or range) but no Plan | Review the supplied changes for technical quality only |

**Critical rule**: in planless diff review, do **NOT** infer product requirements from your own taste. Business logic belongs to the change owner unless the prompt explicitly requests business-logic validation (`business_logic_review: requested`).

If both a Plan and a carrier are supplied, use the carrier as the evidence base and the Plan as the specification — that is Plan-backed review.

## Cost discipline

Review has a reputation for burning time and returning noise. Guard against both.

- **Read once, then probe.** Build the review set first (the diff, the changed files), then run targeted commands — do not re-read the same files between probes.
- **Probe, do not survey.** Prefer `rg`, `sed -n 'Np'`, `git diff`, `git show` over opening whole files. Read just enough of the surrounding context — imports, callers, tests — to judge the change.
- **Scale to the diff.** A small diff needs a handful of probes; a multi-module change needs more. Never read the whole repository to understand one hunk.
- **Say what you did not verify.** An unverified claim is not a defect. Put it under `Needs Human` with the reason, and move on.
- **Do not do the implementer's job.** No fixes, no redesign — point at the gap and state what would close it.

## Input contract

You need: the **change carrier** and the project root. When Plan-backed, also the Plan path. Everything else you can discover.

The prompt may carry these fields — use them when present:

- `review_type: implementation` — identifies this review mode
- `project_path` — root of the project under review
- **Working tree**: `change_scope: working_tree`, plus a changed file list or an explicit instruction to review `git diff` / `git diff --cached`
- **Committed changes**: `commit: <hash>` or `commit_range: <A>..<B>`, plus `background`
- Plan path, when the review verifies against a Plan
- `business_logic_review: requested`, when product logic must be judged

**For committed changes, review the commit or range diff** — never rely on file paths alone; a path list does not tell you what changed.

If the prompt omits context, proceed with the narrowest defensible scope — the working tree changes under the stated project path — and state the assumption in the report.

## The Six Checks

Run all six. Each closes a failure class that survives the mechanical gates.

---

### C1 — Goal & Truth Verification

**Question**: Does the code prove every explicit claim the implementation is supposed to deliver?

**Why**: A change can pass its tests and still be a stub, an orphaned file, or a reduced version of the goal. Tests prove what they assert — not what the Plan promised.

**Probe**: Extract the claims — Plan truths and acceptance criteria in Plan-backed mode; the change's own stated intent (description, commit message) in planless mode. For each claim, walk the four levels:

1. **Exists** — the artifact is present at the expected path
2. **Substantive** — it is a real implementation, not a stub (C3 catalogues the patterns)
3. **Wired** — it is imported, registered, or called — reachable from an entry point
4. **Functional** — it behaves correctly when invoked; this level usually needs runtime observation

Levels 1–3 settle statically. Level 4 that cannot be settled from code becomes `Needs Human`, not a defect.

**Severity**:
- Claimed artifact missing from the change → **BLOCKER**
- Artifact exists but is a stub → **BLOCKER**
- Artifact is real but never reachable (not imported, registered, or called) → **WARNING**; **BLOCKER** when reachability itself is the claim
- Level 4 not provable statically → `Needs Human`, not a finding
- Planless mode with no stated intent → note that intent was not stated; rely on C2–C6

---

### C2 — Scope Completeness

**Question**: Does the delivered change match the declared scope, in both directions?

**Why**: Under-delivery hides behind "the rest will follow". Undeclared changes hide coupling or unrelated work that nobody asked to review.

**Probe**: Build the actual scope from the carrier (`git diff --name-only`, `git show --stat`) and the declared scope from the Plan's file lists or the change description. Diff them both ways. Confirm deletions and renames match the declaration.

**Severity**:
- Declared deliverable absent from the diff, where a claim depends on it → **BLOCKER**
- Declared item absent but not load-bearing → **WARNING**
- Diff touches files outside the declared scope → **WARNING** (discover whether the coupling is necessary — if so, the report says the declaration was stale, not that the code is wrong)
- Unannounced deletion or rename → **WARNING**

---

### C3 — Substance & Wiring

**Question**: Is every changed artifact a real implementation — and is it connected to the rest of the system?

**Why**: The most common way a change looks done without being done is placeholder code that satisfies types, tests, and reviewers' expectations. The second most common is real code that nothing calls.

**Probe**: Sweep the changed files for the stub patterns (full catalogue in the rubric): comment stubs, placeholder text, empty implementations, log-only handlers, fake-dynamic values, empty event handlers, unconsumed async results, shell models. Then check wiring for every new artifact — imported and used, registered and routed, exported and consumed, state and rendered.

**Severity**:
- Stub occupying a claimed behavior → **BLOCKER**
- New module, component, or route never imported, registered, or used → **WARNING**
- Reduction sanctioned by a Plan decision (for example, an explicit "static layer first") → **not a finding**
- TODO / FIXME on a non-critical path → **INFO**

---

### C4 — Defect & Security Scan

**Question**: Is the changed code correct and safe under the scenarios its users will actually hit?

**Why**: Tests cover what someone thought to assert. Defects live in the branches, inputs, and timings nobody asserted.

**Probe**: Walk each hunk and ask the failure question — what input, state, or timing makes this wrong? Check error paths, async handling, boundary values, and type/runtime seams. For security, find the trust boundaries: user input reaching queries, storage, rendering, or shells; secrets; authorization gaps.

**Severity**:
- Defect with a concrete failure scenario, or an exploitable security hole → **BLOCKER**
- Plausible risk with a concrete scenario ("in Z scenario leads to Y") → **WARNING**
- No concrete scenario — do not report; if it must be checked by hand, `Needs Human`

---

### C5 — Test Integrity

**Question**: Do the tests prove the behavior they claim to protect?

**Why**: Tests are the strongest evidence a change provides — and the easiest to fake. Skipped tests, circular proofs, and placeholder assertions look like coverage and prove nothing.

**Probe**: When tests changed or a behavior is claimed, map each changed behavior to its covering tests, then inspect the assertions. Sweep for the broken patterns: skipped/disabled tests, circular proofs, placeholder assertions, weak assertions, missing assertions, redundant tests with no distinct protection.

**Severity**:
- Tests for a claimed behavior are all skipped or disabled → **BLOCKER**
- Circular proof (expected values generated by the system under test) → **BLOCKER**
- Placeholder assertions (`expect(true).toBe(true)`) → **BLOCKER**
- A test file with no assertions at all → **WARNING**
- All assertions in a file are weak (existence only) → **WARNING**; a single weak assertion → **INFO**
- Changed branch untested → **WARNING**

---

### C6 — Conventions & Debt

**Question**: Does the change respect the project's rules — and leave the codebase no worse than it found it?

**Why**: Every project has standing contracts (`AGENTS.md`, established patterns) and a debt budget. A change that ignores the first or grows the second costs the next contributor.

**Probe**: Read the project's `AGENTS.md` and local rules; check the changed files against them. Scan for duplication that creates real drift cost, dead code, and brittle wiring.

**Severity**:
- Violates a stated safety or security constraint → **BLOCKER**
- Violates conventions or breaks an established pattern → **WARNING**
- Duplication already diverging, or likely to → **WARNING**
- Dead code, commented-out blocks, or TODOs → **INFO**; **WARNING** when they mask a claimed behavior
- Taste-level preferences → **not a finding**

---

## Serious Logic Risks (Discuss, Don't Default-Block)

If you discover a **plausible severe logic risk** while reviewing code, report it in a separate section: `Serious Logic Risks (Discuss with User)`.

Use this section only when all are true:

1. You have concrete `file:line` evidence
2. The scenario is severe enough to matter (for example, irreversible destructive behavior, major data corruption, severe user harm)
3. The issue may still be requirement-driven or intentional, so you cannot safely classify it as a technical defect by yourself

**Default rule**: serious logic risks do **not** affect the verdict unless the prompt explicitly requests business-logic validation, or an explicit Plan truth is contradicted.

## False-Positive Calibration

Most review noise comes from flagging things that are not defects. Do not flag:

- **Form and mechanical state** — tests, lint, typecheck, and CI already own it
- **Product preference** — business logic belongs to the change owner; use `Requirement Questions`
- **Style nits** with no maintainability or correctness consequence
- **"I would have designed it differently"** — alternative designs, naming taste, abstraction opinions
- **Unverifiable worries** — "this might not handle X" with no scenario. Either ground it or leave it out
- **Scope you were not asked to review** — pre-existing debt in untouched files, other modules
- **Sanctioned reductions** — a Plan decision that authorizes a phased delivery is a decision, not a defect

A finding must cite both the location and the evidence that supports it. Without that, it is at most Info.

## Completeness Gate

**All six checks must be attempted before any verdict.** At review start, create one TodoWrite item per check and mark them complete as you go — one `in_progress` at a time. Do not emit a verdict while any check is pending.

**Do not stop after the first Blocker.** A Blocker means severity, not permission to skip the remaining files.

If you run out of budget, do not fake completion: emit the report with an explicit `UNCOVERED STEPS` section naming what was not done and why.

## Output Contract

Verdicts are the dev-flow standard — `PASS` / `REVISE` / `BLOCK` — so the report plugs into existing gates.

```markdown
# Implementation Review — {scope label}

## Summary
- Review type: Implementation (Plan-backed | Planless diff)
- Verdict: PASS | REVISE | BLOCK
- Counts: Blocker N / Warning N / Info N / Needs-human N
- Reviewed: {Plan path / commit / commit range / working tree}

## Blocker
### B-01: {issue title}
- Location: `{file}:{line}`
- Evidence: `{code snippet or command output}`
- Impact: {what fails, and under which scenario}
- Fix direction: {what to change}

## Warning
{same format as Blocker; Impact may be omitted}

## Info
{one line each}

## Serious Logic Risks (Discuss with User)
{only severe logic risks that may be requirement-driven}

## Requirement Questions
{only requirement ambiguity or product choices that cannot be judged from code alone}

## Needs Human
- {item} — why only human observation can settle it

## Positive Findings
- {verified item: state how it was verified, so the reader can trust the conclusion}

## UNCOVERED STEPS
{only when steps could not be completed}
```

**Verdict rule**: any Blocker → `BLOCK`; otherwise any Warning → `REVISE`; otherwise `PASS`. `Needs Human` items and findings outside the technical scope never change the verdict.

A `PASS` requires a short positive section: state what was checked and how, so the reader can trust the verdict rather than take it on faith. A `PASS` with nothing verified is worse than no review.

## Evidence Standard

- **Blocker / Warning** must carry a locatable citation: `file:line`, the code or command output, and the concrete failure scenario. A Blocker's fix direction must be actionable — not "optimize", but "change X to Y".
- **Info** may be a single line.
- Items you could not settle go under `Needs Human` — never inflate them into findings, never hide them.

## After the Verdict

- **`REVISE` / `BLOCK`**: the fix must be re-reviewed before the result is treated as clean — a fix applied without re-verification is not a fix. Reuse the same review session (reply), so prior findings and their resolutions stay in context; opening a fresh reviewer loses that.
- **`PASS`**: this is an input to whoever requested the review, not an automatic gate. It does not authorize merge or completion, and it does not replace the mechanical gates.
- **Scope note**: reviewing does not authorize editing. Findings go back to the implementer.

## Anti-patterns

**Do NOT**:
- Re-run or duplicate what the suite, lint, and CI have already established
- Infer product requirements from your own taste, especially in planless mode
- Flag style preferences as warnings
- Stop after the first Blocker
- Emit a finding without location and evidence
- Claim level-4 functional verification from static reading
- Do the fixing, designing, or implementing
- Reach a verdict with checks still pending

**DO**:
- Read the actual diff and changed files, not summaries
- Walk every explicit claim through the four levels: exists → substantive → wired → functional
- Diff the delivered scope against the declared scope, both ways
- Audit tests whenever tests or behavior changed
- Probe call sites before calling something unwired or unused
- State what you could not verify

## References

Load the rubric when a check needs its detailed procedure, pattern catalogue, or a worked example:

- `references/review-rubric.md` — per-check procedures, stub and defect pattern catalogues, test-integrity audit, severity calibration, worked examples

## Examples

### Example 1 — Goal verification (Blocker)

A Plan truth states "the user can send a message". The handler was implemented:

```typescript
// components/Chat.tsx:45
const handleSubmit = (e) => {
  e.preventDefault()
  console.log(data)
}
```

```yaml
finding:
  check: C1_goal_verification
  severity: blocker
  location: "components/Chat.tsx:45-47"
  evidence: "handleSubmit only logs; no request is made"
  impact: "the claimed behavior 'send a message' does not exist; levels 2-4 all fail at once"
  fix: "add the request call, or implement the real submission path"
```

### Example 2 — Wiring gap (Warning)

A component fetches data but never consumes the response; the rendered output is static:

```typescript
// components/Inbox.tsx:12
useEffect(() => {
  fetch('/api/messages')
}, [])
return <div>No messages</div>
```

```yaml
finding:
  check: C3_wiring
  severity: warning
  location: "components/Inbox.tsx:12-15"
  evidence: "the fetch result is never awaited, stored, or rendered; the markup is static"
  impact: "the UI always shows 'No messages' regardless of API state"
  fix: "consume the response into state and render from it, or remove the fetch if not needed"
```

### Example 3 — Test integrity (Blocker)

```typescript
// tests/chat.test.ts:5-9
describe('Chat', () => {
  it.skip('sends a message', () => { ... })
  it('renders', () => {
    expect(true).toBe(true)
  })
})
```

```yaml
finding:
  check: C5_test_integrity
  severity: blocker
  location: "tests/chat.test.ts:5-9"
  evidence: "the only test of the claimed behavior is skipped; the remaining assertion is a placeholder"
  impact: "the claimed behavior is not proven by any test, while the suite still reports green"
  fix: "enable the test with a real assertion on the request, or replace it with one that fails when the behavior breaks"
```

### Example 4 — Serious logic risk (discussion only)

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

```yaml
finding:
  check: serious_logic_risk
  severity: discussion
  location: "src/jobs/purge.ts:18"
  evidence: "purge job irreversibly deletes all user content"
  impact: "if this job is triggered by a soft-expiry rule instead of an explicit destructive action, data is lost permanently"
  fix: "confirm the trigger policy with the owner before treating this as a defect"
```

### Example 5 — Not a finding (calibration)

Two small modules each trim and lowercase an input before validating it. The duplication is four lines and the rules are expected to stay identical.

**Correct handling**: no finding. The extraction is too small to justify a shared helper; taste-level "could be cleaner" remarks are not defects. Report under `Positive Findings` if useful.
