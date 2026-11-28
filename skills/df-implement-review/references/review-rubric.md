# Implementation Review Rubric — Pattern Catalogues & Procedures

Detail behind the four questions. Load this when a check needs its full method, a pattern catalogue, or a worked example.

The patterns below are evidence-gathering clues, not a mandatory exhaustive checklist or independent severity rules. Follow the minimalism principles in `SKILL.md` and `df-implement`: select applicable checks using the product's actual purpose, users, deployment, trust boundaries, approved design and real consequences; classify by practical value and risk. Edge cases without demonstrable impact or repair benefit do not belong in the repair list. Explicit mandatory contracts and substantial real risks still require checking.

Contents:
1. [Building the three lists](#1-building-the-three-lists)
2. [Q1 stub patterns & probes](#2-q1--stub-patterns--probes)
3. [Q2 contract-surface procedure](#3-q2--contract-surface-procedure)
4. [Q3 defect catalogue](#4-q3--defect-catalogue)
5. [Q4 test integrity & documentation drift](#5-q4--test-integrity--documentation-drift)
6. [Q4 orphan tags](#6-q4--orphan-tags-change-review-diff-created-orphans-only)
7. [Probe bundle](#7-probe-bundle)
8. [Capability standards gate (evolution proposals)](#8-capability-standards-gate-evolution-proposals)
9. [Severity calibration](#9-severity-calibration)
10. [Worked examples](#10-worked-examples)
11. [Delivery-baseline scope & adversarial DESIGN/Proposal verification](#11-delivery-baseline-scope--adversarial-designproposal-verification)

---

## 1. Building the three lists

Read the diff once (`git diff`, `git diff --cached`, `git show <hash>`, or `git diff <A>..<B>`) plus the changed files. Do not alternate between reading and probing — every return to a file costs more than the probe it saves. Fill three lists while reading:

1. **Claims** — every deliverable or acceptance criterion, sourced from Plan tasks, design clauses, `AGENTS.md` rules, or decisions recorded in the conversation. Collect these before judging anything.
2. **Contract surface** — every exported symbol, signature, schema, shared type, or config the diff modifies, plus functions whose logic changed but signature didn't.
3. **Flags** — possible stubs, wiring gaps, suspicious tests, orphans the diff may leave, to resolve in the sweeps.

After this, use the three lists for targeted checks across all four questions; do not repeat aimless scans. Trace common implementations, similar operations and affected callers for same-root defects in the same round; merge key counterexamples and acceptance criteria. Prefer observable behavior evidence to confirm impact.

If authorization or design evidence is missing, disclose which Q1 completeness claims cannot be judged. Continue Q2–Q4 checks for real defects, artifact quality and applicable debt; repo audits may identify grounded maintenance cuts without inventing product intent.

## 2. Q1 — Stub patterns & probes

A pattern's presence is a signal, not a verdict — classify by whether a claim or caller depends on real behavior.

**Comment stubs**
```javascript
// TODO: implement later
// FIXME: this is broken
// HACK: temporary
// PLACEHOLDER
// ... (empty body where logic belongs)
```
Probe: `rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' <changed files>`

**Placeholder text**
```
"placeholder"   "lorem ipsum"   "coming soon"   "under construction"
"TBD"           "Not implemented"
```
Probe: `rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' <changed files>`

**Empty implementations**
```javascript
return null   return undefined   return {}   return []
```
```python
pass   return None   return {}   return []
```
Probe: `rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' <changed files>` — honest empty returns exist; classify by whether a caller or claim depends on real content.

**Log-only handlers** — a body that only logs or forwards has no behavior. Read each handler body.

**Fake-dynamic values**
```jsx
<div>Message 1</div>        // should come from state/props
const id = "fixed-id"       // should be generated
const count = 3             // should be computed
```
Classify against the claim: if the behavior must be dynamic and the value is fixed, BLOCKER.

**Frontend shells**
```jsx
return <div>Component</div>
return <p>Coming soon</p>
return null
onClick={() => {}}
onSubmit={(e) => e.preventDefault()}
```

**API route shells**
```typescript
export async function GET() { return Response.json([]) }   // static, no data source
export async function POST() { return new Response() }     // empty body
```

**Database schema stubs** — model missing fields/relations the claimed behavior needs.

**Hook / utility stubs**
```typescript
export function useAuth() { return { user: null, login: () => {}, logout: () => {} } }
```

**Wiring checks for every new artifact:**
- Declared → imported (`rg <symbol>`)
- Imported → used (referenced, not merely present)
- Used → reachable from an entry point (route, render tree, CLI, job runner)
- Component → data source: fetch awaited, consumed, rendered
- State → render: state variables actually appear in rendered output
- API → storage: query awaited and its result returned, not discarded
- Route → registration: new route/command/job registered where the framework discovers it

## 3. Q2 — Contract-surface procedure

The mechanical gates miss this most. What slips through: silent behavior changes and untested-behavior breaks.

### Step 1 — extract the contract surface

From the diff, list every artifact other code can depend on:

- exported functions/classes — signature, return type, thrown errors
- data shapes — schema fields, JSON response structure, enum values, DB columns
- shared types / constants / config keys
- **functions whose logic changed but signature didn't** — the most dangerous class
- test infrastructure — fixtures, mocks, helpers (their changes alter what existing tests prove)

### Step 2 — find all consumers

`rg <symbol>` across the project, including files outside the diff. For many consumers: `rg -l <symbol>`, read a representative sample, and state what you did not cover.

### Step 3 — classify the break type

| Break type | What to look for |
|---|---|
| Signature change | Added/removed params, narrowed/widened types, changed return type. Type systems catch most — but `any`, `as` casts, and dynamic languages do not |
| Nullability change | Was `never null` (or empty), now `null`; or opposite. Callers indexing or chaining off the old guarantee break |
| Sync → async | Now returns a Promise; callers awaiting nothing break silently in dynamic languages |
| Ordering change | Array order, event order, iteration order that callers rely on |
| Idempotency change | Retried calls now double-apply (or no longer do) |
| Side-effect change | Pure function now writes global state; or side effect removed that callers depended on |
| Error contract change | Different error codes, HTTP statuses, or error message format — callers often parse messages |
| Default/behavior branch change | The path for a realistic input now returns different data than before |
| Performance cliff | O(n) → O(n²) on a hot path is a break |
| Schema drift | Field renamed/removed without migrating all readers; enum value removed |

For each consumer, ask: which assumption from this table does it hold, and is it still true?

### Severity

- Diff-outside call site suffers a material regression or violates an important contract in a real usage scenario → **BLOCKER**; classify minor issues worth correcting under SKILL.md and do not demand low-value fixes
- Behavior changed, but the design may have sanctioned it → check the design first; a sanctioned change is not a finding. When authorization is uncertain, disclose it; report independently demonstrated defects at their actual severity
- Consumers not fully checked → Other notes, never fake coverage

## 4. Q3 — Defect catalogue

Select applicable patterns based on real usage paths, changed contracts and actual risks. **Report only real problems with evidence, reachable triggering conditions and practical impact.** Judge performance and security controls by the current design, trust boundaries and reasonable load; do not demand defenses against every theoretical edge case. Do not dismiss real risks with major consequences because they are unlikely. A pattern alone does not determine severity.

**Concurrency & state**
- race between async operations over shared state
- non-atomic read-modify-write (check-then-act) on shared counters/flags
- re-entrancy: handler re-entered before finishing (double submission)
- partial update: multi-step mutation where step 2 can fail after step 1 committed, with no rollback
- stale closure over loop variables or props

**Resource lifecycle**
- opened handle/connection/stream not closed on all paths
- cleanup skipped on the error branch (the happy path closes, the catch doesn't)
- pooled connections not returned (leak under load)
- file/timer/subscription created per render or per call without teardown

**Boundaries & numerics**
- off-by-one in ranges, slices, pagination
- empty collection / missing key / undefined before access
- zero, negative, very large values flowing into division, allocation, indexing
- overflow/size limits: sum, counter, buffer

**Async**
- missing `await` (fire-and-forget where the result matters)
- floating promise: rejection never handled
- ordering assumptions: responses arriving out of order overwrite newer state
- timeout missing on external calls; caller hangs forever

**Error handling**
- swallowed exception, then continuing with invalid state
- log-and-continue where the operation must abort
- failure reported as success (HTTP 200 with an error payload the client can't see)
- inconsistent state after partial failure; no compensation or rollback

**Type/runtime seams**
- `as`/unsafe cast over data the code did not validate
- parsed input trusted as typed without a validation step
- nullability assumed from a key that can legitimately be absent
- JSON.parse / environment / query param treated as typed

**Security**
- user input reaching SQL, shell, or templates unparameterized
- `innerHTML` / `dangerouslySetInnerHTML` with anything user-influenced
- unsafe deserialization (`eval`, unpickling untrusted payloads)
- request body used before validation; validation present but bypassable
- new route/handler missing the auth check its siblings have
- secrets in code, committed files, logs, or error messages

Probes: `rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' <changed files>`; check every new POST/PUT handler for validation before use; check new routes for auth middleware.

## 5. Q4 — Test integrity & documentation drift

### Test integrity — broken patterns

| Pattern | Probe | Verdict |
|---|---|---|
| Skipped/disabled tests | `rg -n 'it\.skip|xdescribe|xit|@pytest\.mark\.skip|t\.Skip' <test files>` | Classify under required gates when mandatory verification is skipped without equivalent evidence; disclose legitimate environment limits |
| Circular proof | expected value generated by the code under test | BLOCKER when presented as valid verification evidence |
| Placeholder assertions | `rg -n 'expect\(true\)|expect\(false\)|expect\(1\)'` | BLOCKER when presented as valid verification evidence |
| Weak assertions (existence-only) | `rg -n 'toBeDefined|toBeTruthy|not\.toBeNull'` | Judge whether a meaningful coverage gap exists using actual behavior and other verification evidence |
| No assertions | `rg -c 'expect\|assert' <file>` → zero | Clue only; check the runner, exit status and actual outcomes, then classify the verification gap |
| A behavior the design explicitly promises has no test | map the claims list to tests or other valid verification | Classify insufficient required verification under SKILL.md; do not demand redundant equivalent tests |

The bar: **would this test fail if the behavior broke?** A test that would still pass with the feature removed is decoration.

Scope this to behaviors the design promises. An internal branch the design never mentions, in a shape you did not expect, is implementation freedom, not a coverage gap. Treating "every changed branch needs a test" as the standard turns the reviewer's imagination into requirements.

Reuse existing entry points and isolated test environments for actual verification; select the lowest-cost effective level under `rules/testing.md`. Record commands or operations, observed outcomes and unverified items. When a code counterexample proves a defect, do not demand a complex extra test; perform targeted verification when key behavior lacks evidence. Do not modify delivery code or tests to obtain passing results.

### Documentation drift

A change that alters an external contract without updating the docs that describe it ships with a lie. Reuse the Q2 contract surface; for each changed contract (API, schema, CLI flag, config key, behavior the design pins down):

1. Find where it is documented — `rg '<symbol>' docs/ README* AGENTS.md` and public docstrings.
2. Check whether the diff updated those spots.
3. Inconsistency between code and present-state DESIGN, DESIGN and rules, or affected rule tiers, or failure of their governing quality standards → BLOCKER. For business Proposal-driven delivery, material unauthorized design drift or violation of an unchanged governing architectural constraint → BLOCKER; noncritical target discrepancy or authorized-but-unsynced Proposal adjustment → WARNING. Affected glossary consistency is a mandatory document check under dev-doc-master. Unrequired internal implementation detail need not be documented.
4. A project rule requiring docs to ship with code (stated in `AGENTS.md`) → violating it is BLOCKER, same as any stated constraint.

Pure internal refactors with no contract change trigger nothing. Docs outside the repo you can see → Other notes.

## 6. Q4 — Orphan tags (change review: diff-created orphans only)

A change review checks only the orphans and duplication **this diff** creates. Whole-repo slimming belongs to Repo audit mode.

One line per finding: location, what to cut, what replaces it. **A finding without a replacement is a complaint, not a finding.**

| Tag | Catches | Replacement |
|---|---|---|
| `delete:` | code, files, exports, or dependencies the diff orphaned by switching callers; dead code the diff introduced | nothing |
| `shrink:` | duplication the diff introduced when an existing helper or a shorter form would do | name the existing helper or the shorter form |

`stdlib:`, `native:`, and `yagni:` belong to Repo audit. Raising them in a change review means re-picking the implementer's technical choices — do not report them unless a design clause required that choice.

### What to hunt (change review)

- **orphans left behind by the diff**: for every `import` or function call removed in the diff, check (`rg <symbol-or-module>`) whether any production caller still references the old module or function. If production references drop to zero (or only its own test file imports it), flag `delete:` on both the orphaned production code and its orphaned test file.
- dead code the diff itself wrote, commented-out blocks it left, exports it added with no caller

Leave out of a change review (these are Repo audit work): pre-existing dead code, whole-repo unused dependencies, whether an existing implementation should use the standard library, whether existing interfaces are over-abstracted. None of them came from this diff, and raising them turns a small fix into a refactor.

### Runtime & platform check for `stdlib:` and `native:` (Repo audit only)

Before recommending a `stdlib:` or `native:` replacement, verify:
1. **Runtime version**: check `engines` in `package.json`, `requires-python` in `pyproject.toml`, `go.mod`, or `rust-version` to confirm the builtin API exists in the project's minimum supported runtime.
2. **Target OS**: if a `native:` replacement shells out to a system CLI (e.g., `zip`, `tar`, `sed`), confirm the tool and flags exist on every OS the project supports (macOS, Linux, Windows).

### Never flag

- the smallest check that would fail if the logic broke — a smoke test, one `assert`-based self-check, one small test file. That is the lean minimum, not bloat.
- deliberate simplifications with valid `simplified:` comments that explicitly name their ceiling and upgrade path (flag only if missing an upgrade trigger).
- input validation at trust boundaries, error handling that prevents data loss, security measures — never simplified away, never flagged for deletion.
- tradeoffs the design explicitly accepted: polling instead of events, a fixed throttle window, sequential execution instead of concurrency, one retry instead of exponential backoff. These are decisions, not bloat.
- taste ("I would have structured it differently"), naming, style preferences.

### Severity

| Condition | Severity |
|---|---|
| Diff switches callers away from old code/tests, leaving zero production references (orphan created by this diff) | **WARNING** under the cleanup obligation in `df-implement` |
| Duplication this diff introduced where the repo already ships applicable logic, finding names `file:line` | **WARNING** when there is practical maintenance benefit; do not report small, simple, stable duplication |
| Pre-existing dead code / unused dependency, stdlib/native replacement ideas, single-implementation interfaces (Repo audit mode) | INFO (dead code WARNING when it masks a claimed behavior) |
| Optional simplification without a demonstrated defect or new duplication | INFO |

Satisfy the actual design and necessary safety constraints first, then seek leanness. Do not weaken necessary safeguards to save lines or require extra defenses against unproven risks. For overdesign introduced by this diff, identify the unnecessary structure, real maintenance cost and a more direct replacement; do not treat ordinary implementation choices as defects.

### The metric (Repo audit only)

End of report: `net: -N lines, -M dependencies possible` — sum the realistic cut across all findings. Nothing to cut → `Lean already. Ship.`

A change review does not owe a line-count target. Hunting deletions during a change review is how a small fix becomes an unrequested refactor.

## 7. Probe bundle

### Diff review probes (Modes 1 & 2)

After reading the diff, select useful probes from these commands by applicable language, changed contract and risk, and run them together against the changed files (fill in the paths):

```bash
FILES='<changed files>'
rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' $FILES
rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' $FILES
rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' $FILES
rg -n 'console\.log|print\(' $FILES
rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' $FILES
rg -n 'it\.skip|xdescribe|xit|describe\.skip|@pytest\.mark\.skip|t\.Skip' $FILES
rg -n 'expect\(true\)|expect\(false\)|expect\(1\)' $FILES
rg -n 'toBeDefined|toBeTruthy|toBeFalsy|not\.toBeNull' $FILES
```

- **Consumer check (Q2)**: for each exported symbol touched by the diff, run `rg -l '<symbol>' <project>` to find consumers, including outside the diff.
- **Orphan check (Q4)**: for each `import` or helper call *removed* by the diff, run `rg -l '<old-module-or-symbol>' <project>` to verify whether the old target now has zero production callers (and whether its test file is now testing dead code).
- **New-duplication check (Q4)**: `rg -n '<distinctive snippet from the new code>' <project>` to see whether an existing helper already does this. Report only duplication this diff introduced; abstract-class and factory scans belong to Repo audit.
- **Project rules check**: only when the diff touches an `AGENTS.md` with a localized sibling (`AGENTS.<locale>.md`). Headings and inline code must match across versions:

```bash
diff <(grep '^#' AGENTS.md) <(grep '^#' AGENTS.<locale>.md)
diff <(grep -o '`[^`]*`' AGENTS.md | sort -u) <(grep -o '`[^`]*`' AGENTS.<locale>.md | sort -u)
```

A non-empty diff means drift; whether it is a defect follows the severity rules in `SKILL.md` (`## Project rules review`). Semantic differences that survive this check still need a read.

### Repo audit probes (Mode 3 — whole-repo or directory lean audit)

When running in **Repo audit** mode (no diff; scanning an existing project or directory for bloat), run these static scans first so you don't miss unreferenced files or miscount dynamic imports:

1. **Manifest & dependency usage**:
   - Read `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`.
   - For each production dependency, count references across `src/` (`rg '<pkg>' src/`), checking static imports, dynamic `await import('<pkg>')`, and side-effect `import '<pkg>'`.
   - Flag dependencies with 0 references as `delete:`, and single-call-site dependencies replaceable by stdlib as `stdlib:` / `native:`.
2. **Orphaned files (0 production importers)**:
   - List all non-entry source files under `src/` and check whether each file's stem is imported anywhere in `src/`.
   - Files imported only by `tests/` (0 hits in `src/`) are dead production modules with orphaned test files — flag both with `delete:`.
3. **Unused exports (0 external references)**:
   - Scan exported symbols (`export function|const|class|type|interface`) across `src/`.
   - Any exported symbol referenced only inside its own file (or only in `tests/`) is dead export surface — flag `delete:` (or drop `export` if used internally).
4. **Single-implementation abstractions & wrappers**:
   - Run `rg -n 'interface |abstract class |Factory|Manager|Adapter' src/` and inspect the largest files (`wc -l`).
5. **Lingering debt markers, skipped tests & stale docs (when analyzing technical debt)**:
   - Run `rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER|simplified:' src/` and `rg -n 'it\.skip|xdescribe|xit|describe\.skip|@pytest\.mark\.skip|t\.Skip' tests/` to surface half-finished work and disabled tests alongside structural bloat. For `simplified:` comments, verify each names an upgrade trigger (flag any without a trigger as an unanchored shortcut risk).
   - Group findings by impact in the report: **Dependencies to cut** → **Dead files & exports (`delete:`)** → **Stdlib / native replacements** → **Abstractions & duplication (`yagni:` / `shrink:`)** (plus **Debt markers & test/doc gaps** if present), ending with `net: -N lines, -M dependencies possible`.

## 8. Capability standards gate (evolution proposals)

When the prompt carries an evolution proposal path, the change lands capability assets. Check the landed files against the platform's own standards:

| Standard | Check |
|---|---|
| frontmatter `name` + `description` | read the file header |
| Triggering conditions in the description | the description states when to use it; the body does not bury trigger info in a late section |
| Body = workflow + output + notes | no essays, no feature tours; long content offloaded to `references/` |
| `scripts/` only deterministic, reusable logic | one-off snippets do not live in scripts/ |
| No invented structure | asset anatomy matches the platform's other assets (no rogue subdirs, no novel file types) |
| Plain, precise language | an agent knows what to do after one read; jargon and machine prose are findings |

Use the severity rules in SKILL.md. Affected engineering rules violating their governing SOP or quality standards → **BLOCKER**; other capability assets violating mandatory standards or unable to work as landed → **BLOCKER**.

This gate complements df-proposal-review, which checked the *stated* deliverable; this review checks the *landed* files.

## 9. Severity calibration

| Situation | Correct verdict |
|---|---|
| Handler logs the payload but the claim is "processes the message" | BLOCKER (Q1 stub) |
| Function correctly written but no call site anywhere | WARNING (Q1 unwired) |
| Diff changes a helper's return from `[]` to `null`; a diff-outside caller does `.map()` directly | BLOCKER (Q2) |
| Endpoint now returns 200 with an error body where callers keyed on 4xx | WARNING/BLOCKER by severity (Q2) |
| Required verification of core behavior is skipped but claimed to have passed | BLOCKER (Q4 false verification); disclose legitimate environment limitations without presenting them as product failures |
| `expect(true).toBe(true)` | BLOCKER (Q4) |
| A test checks `toBeDefined` plus two strong value assertions | no finding |
| Four-line input normalization duplicated, rules stable | no finding |
| Duplicated validation already diverged between two call sites | WARNING (Q4) |
| Query executed, result discarded, static `{ ok: true }` returned | BLOCKER (Q1) |
| Deletion of a helper that turns out to still be imported (build would catch) | no finding — CI owns build breakage |
| Two writes can actually run concurrently with a concrete interleaving that causes user data loss | BLOCKER (Q3 race) |
| Implementation works but changes an approved material design decision or unchanged architecture without authorization | BLOCKER (Q1 design drift); noncritical discrepancies or authorized-but-unsynced Proposal adjustments are WARNING |
| Implementation matches a tradeoff the design explicitly accepted (fixed short cache window, sequential execution, polling) and violates no clause | no finding — the design decided |
| Implementation chose a shape the reviewer dislikes, but the design neither requires nor forbids it | no finding (Info at most, and usually stays in your notes) |
| Change alters a documented API, owning DESIGN left stale | BLOCKER (Q4 DESIGN sync) |
| Early commit in a multi-commit delivery changes a public contract, owning DESIGN untouched across the delivery window, last commit clean | BLOCKER (doc-sync miss visible only against the full delivery baseline) |
| Two places in the same DESIGN or rule contradict each other | BLOCKER (Q4 artifact consistency) |
| New `retry.ts` added by this diff duplicates `src/lib/http.ts:88` backoff already in use | WARNING (Q4 — duplication introduced by the diff) |
| Diff switches command from `lib/doctor.ts` to `lib/inspect.ts`; `lib/doctor.ts` and `tests/lib/doctor.test.ts` now have zero production callers | WARNING (Q4 `delete:` orphan created by diff) |
| `package.json` lists `eventsource`; `rg 'eventsource' src/` finds zero imports (pre-existing, untouched) | INFO in Repo audit only; not in a change review |
| `AbstractStore` with a single `FileStore` implementation (pre-existing, untouched) | INFO in Repo audit only; not in a change review |
| Landed skill buries required trigger conditions in body | BLOCKER (mandatory capability standard) |
| Landed skill's frontmatter lacks `description` | BLOCKER (capability gate) |
| Design says unconfirmed quota exhaustion is transient rate limiting; implementation does that, but the reviewer thinks it should disable the account | design concern in Other notes, no verdict change |
| Design never mentions an internal branch; implementation picked its own approach and left it untested | no finding — the design never promised that behavior |
| Concern about visual appearance of a changed component | Other notes |
| "I would have structured this module differently" | no finding |
| An administrator's configured rule can interrupt service for other users with real reachable input | BLOCKER (Q3 substantial stability risk); verify the common root cause and key boundaries, and require the smallest reliable fix |
| Requests are rejected slightly early only near resource limits under rare combinations of operations, within a conservative limit allowed by current design | no finding; if there is a noncritical contract discrepancy worth correcting, classify by impact or ask the user; do not add complex mechanisms for byte-level precision |
| Defenses needed only if the product is hypothetically opened to the public, load grows or trust boundaries change | no finding; if there is practical design value, offer separate non-blocking design feedback |

Judgement note: any Blocker → BLOCK, else any Warning worth revising → REVISE, else PASS. The controller may record accepted Warnings and conditionally pass under the owning workflow. Judge by practical impact and mandatory contracts, not finding counts; do not prolong re-review for low-value issues.

## 10. Worked examples

### Example A — Stub caught by Q1

**Claim**: "Messages are fetched from the database". The route exists:

```typescript
// api/messages/route.ts:8
export async function GET() {
  return Response.json([])
}
```

```yaml
finding:
  check: Q1_stub
  severity: blocker
  location: "api/messages/route.ts:8-10"
  evidence: "handler returns a constant; no data source is consulted"
  impact: "the endpoint cannot serve real data; the claim is false at the substantive level"
  fix: "query the store and return its result, as the claim requires"
```

### Example B — Silent behavior change caught by Q2

**Diff**: a utility's empty-input return changed from `[]` to `null` to satisfy a new caller. No existing tests assert the empty case.

```typescript
// utils/filter.ts:12  (changed line)
if (!list.length) return null          // was: return list
```

```yaml
finding:
  check: Q2_regression
  severity: blocker
  location: "utils/filter.ts:12"
  evidence: "rg 'filter\(' src/ finds 14 call sites, 9 outside the diff; 3 call .map()/.length directly on the result"
  impact: "any of those 3 call sites receiving an empty input now throws a TypeError at runtime, while the suite is green"
  fix: "return an empty array for empty input and add a null-handling adapter at the one caller that wants null, or update all 14 call sites and audit their empty cases"
```

### Example C — Contract surface too large: honest scoping

A diff rewrites the shared `formatDate` used in 60 files. Reading all 60 is not review — it's a survey.

**Correct handling**: extract the *contract* — signature, accepted inputs, output format, timezone behavior. Diff the contract against the old version. `rg -l` the consumers, read 3–5 representative call sites across categories (props rendering, API serialization, cache keys — anything that might hold a format assumption). Report the remainder under Other notes with the reason.

### Example D — Circular proof caught by Q4

```typescript
// tests/parser.test.ts:14-16
const expected = parse(input)
const actual = parse(input)
expect(actual).toEqual(expected)
```

```yaml
finding:
  check: Q4_test_integrity
  severity: blocker
  location: "tests/parser.test.ts:14-16"
  evidence: "expected and actual both come from the parser under test"
  impact: "the test cannot fail for the behavior it claims to protect; any output, correct or not, compares equal"
  fix: "assert against independent expected values written by hand"
```

### Example E — Duplication this diff introduced (reportable in a change review)

**Diff**: this change adds `src/lib/slug.ts` (18 lines) hand-rolling slugification. `rg "kebabCase" src/` shows `package.json` already lists `lodash`, and two existing files already import `kebabCase`.

```
src/lib/slug.ts:L1-18: delete/shrink: 18 new lines duplicating lodash.kebabCase, already imported in 2 files. Replacement: delete the file, import kebabCase.
```

Reported as WARNING (duplication introduced by this change).

Watch the boundary: only duplication **this diff wrote** counts. If two old files hand-rolled slugification while `lodash` sat in `package.json`, that is pre-existing debt — Repo audit territory, not a finding against this change.

### Example F — Serious logic risk only when it contradicts the design

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

A demonstrated violation of a required safety or design contract is a Blocker, irrespective of whether the effect is reversible (e.g., the design requires soft delete but code deletes permanently).

If the design calls for a hard delete, this is conformance, not risk. When the reviewer believes the design is wrong, that is one design concern in Other notes item — "hard delete is irreversible; consider soft delete with retention" — so the user changes the design first instead of blocking this delivery.

## 11. Delivery-baseline scope & adversarial DESIGN/Proposal verification

### Establish the full delivery diff

```bash
# with a delivery base (preferred for multi-commit or branch deliveries):
git diff --name-status <delivery_base>...HEAD
# single uncommitted change only:
git diff --name-status
```

The early-miss shape to hunt specifically: `git log --oneline <delivery_base>..HEAD` each commit that touched non-test code under a Source Carrier prefix, then check whether the owning `DESIGN-<module>.md` was modified **in the same delivery window**. A module whose code changed early but whose DESIGN doc has no commit touching it after `<delivery_base>` is the exact miss `--check-sync --base` fails on — report it even when the last commit is clean.

### Adversarial checklist — authorization → code (Chain 1)

| Check | Method |
|---|---|
| Every authorized item delivered | Map each `Authorized scope` / Issue item / Plan task bullet to diff hunks; an unmapped item is a Q1 missing-deliverable finding |
| Nothing beyond the approved scope | `git diff --name-status <base>...HEAD` vs the declared file/behavior scope; undeclared file changes or behavior shifts are findings |
| Design fidelity | Trace each material changed contract and unchanged governing architectural constraint through actual code, callers and tests; cite the approved target/authority and concrete divergence. Internal choices preserving these contracts are not findings. |
| Explicit exclusions respected | The proposal's exclusion list (e.g., "excludes layout changes") crossed by any hunk → Q1 scope violation |

### Adversarial checklist — code → DESIGN (Chain 2)

| Check | Method |
|---|---|
| Owning DESIGN updated for every contract change | For each changed export/default/failure boundary, `rg '<symbol or behavior>' docs/` then confirm the owning `DESIGN-<module>.md` diff contains the updated statement |
| Glossary fidelity and sync | For new or changed domain meanings, compare approved target and verified behavior with affected glossary definitions and consumers; missing required sync or contradictory active definitions → BLOCKER. Use the glossary guide; no mandatory glossary for simple projects. |
| DESIGN statements match real behavior | Read the updated DESIGN text against the code hunk; invented behavior or planned-but-unbuilt features → BLOCKER (fact distortion) |
| `DESIGN Sync` block claims verified | Re-run or spot-check the claimed gate (`verify-docset.py --check-sync --base`); compare baseline, environment and inputs; a reproduced mandatory gate failure blocks delivery, an inconclusive result is disclosed, and fabrication requires evidence |
| `--pure-refactor` reason honest | Diff the claimed-refactor files for any externally visible change (export surface, defaults, error contract); a visible change hidden behind the flag → BLOCKER |
| Parallel write-set respected | Confirm the diff touches only authorized `DESIGN-<module>.md` files; any shared main `DESIGN.md` edit from a module worker → BLOCKER (violation of the stated write-set rule) |

### DESIGN → engineering rules (Chain 3)

Use the actual `space-master` and `dev-doc-master` quality standards. Inspect affected rules at project, module, directory, documentation and other applicable tiers, including unchanged rules invalidated by the delivery. Check agreement with code, present-state DESIGN, parent/child rules and all applicable mandatory SOP, language, reference and gate requirements. Any noncompliance is BLOCKER. Pure internal changes need no artificial document edits.

### Proposal lifecycle verification checklist

| Check | Method |
|---|---|
| Migration only after full delivery + acceptance | `proposals/implemented/` contains the proposal only when the diff covers the whole `Authorized scope` and the record carries user-acceptance evidence; partial delivery sitting in `implemented/` → BLOCKER |
| Partial supersession cross-links | At full delivery, the new proposal names which old decisions it supersedes and the old record links back; missing either direction at full delivery → WARNING |
| Full replacement disposal | Old record absorbed-and-deleted or moved to `archived/<class>/` with `Archived: YYYY-MM-DD` in the same delivery; neither → WARNING |
| Current approved Proposal maintained before acceptance | Integrate explicit user-authorized changes into the current Proposal; missing sync alone → WARNING. Premature changes to the superseded historical `implemented/` record remain BLOCKER |
| No demotion, no archive tampering | Any `implemented/` → `proposed/` move, or any content change under `archived/` → BLOCKER |

### Severity calibration for sync failures

| Situation | Verdict |
|---|---|
| Public behavior changed in an early commit, owning DESIGN never updated in the delivery window | BLOCKER (fact distortion, caught by the full-baseline diff) |
| Genuine pure internal refactor with `--pure-refactor` reason, no visible contract change | no finding — verify the reason is honest and move on |
| `--pure-refactor` claimed but the diff changes an export, default, or error contract | BLOCKER (invalid pure-refactor claim) |
| Parallel worker edited the shared main `DESIGN.md` | BLOCKER (write-set violation) |
| New proposal migrated into `implemented/` while scope is partially delivered | BLOCKER (impersonated full delivery) |
| Bidirectional cross-link missing at full-scope partial supersession | WARNING (Proposal maintenance gap; independent DESIGN/rule quality violation is BLOCKER) |
| Wording in the synced DESIGN slightly imprecise but factually correct and quality-compliant | INFO |
