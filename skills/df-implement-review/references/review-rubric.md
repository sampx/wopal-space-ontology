# Implementation Review Rubric — Pattern Catalogues & Procedures

Detail behind the four questions. Load this when a check needs its full method, a pattern catalogue, or a worked example.

Contents:
1. [Building the three lists](#1-building-the-three-lists)
2. [Q1 stub patterns & probes](#2-q1--stub-patterns--probes)
3. [Q2 contract-surface procedure](#3-q2--contract-surface-procedure)
4. [Q3 defect catalogue](#4-q3--defect-catalogue)
5. [Q4 test-evidence & debt signals](#5-q4--test-evidence--debt-signals)
6. [Probe bundle](#6-probe-bundle)
7. [Severity calibration](#7-severity-calibration)
8. [Worked examples](#8-worked-examples)

---

## 1. Building the three lists

Read the diff once (`git diff`, `git diff --cached`, `git show <hash>`, or `git diff <A>..<B>`) plus the changed files. Do not alternate between reading and probing — every return to a file costs more than the probe it saves. Fill three lists while reading:

1. **Claims** — every deliverable or acceptance criterion (Plan truths, or the change's stated intent).
2. **Contract surface** — every exported symbol, signature, schema, shared type, or config the diff modifies, plus functions whose logic changed but signature didn't.
3. **Flags** — possible stubs, wiring gaps, suspicious tests, to resolve in the sweeps.

After this, all four questions consume the lists with targeted probes. Never re-scan what you already read.

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

The mechanical gates miss this most. Type checks catch compile breaks; existing tests catch what they cover. What slips through: silent behavior changes and untested-behavior breaks.

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

- Diff-outside call site broken with a concrete scenario → **BLOCKER**
- Semantic change that may be intentional (Plan decision) → **WARNING** or `Serious Logic Risks`
- Consumers not fully checked → `UNCOVERED STEPS`, never fake coverage

## 4. Q3 — Defect catalogue

Walk the changed hunks against these patterns. Report only findings with a concrete scenario.

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

## 5. Q4 — Test-evidence & debt signals

### Test integrity — broken patterns

| Pattern | Probe | Verdict |
|---|---|---|
| Skipped/disabled tests | `rg -n 'it\.skip|xdescribe|xit|@pytest\.mark\.skip|t\.Skip' <test files>` | BLOCKER for claimed behavior |
| Circular proof | expected value generated by the code under test | BLOCKER |
| Placeholder assertions | `rg -n 'expect\(true\)|expect\(false\)|expect\(1\)'` | BLOCKER |
| Weak assertions (existence-only) | `rg -n 'toBeDefined|toBeTruthy|not\.toBeNull'` | all-weak file WARNING; one weak INFO |
| No assertions | `rg -c 'expect\|assert' <file>` → zero | WARNING |
| Redundant happy-path tests while real branches untested | read the tests | WARNING for untested key branches |

The bar: **would this test fail if the behavior broke?** A test that would still pass with the feature removed is decoration.

### Documentation drift

A change that alters an external contract without updating the docs that describe it ships with a lie. Reuse the Q2 contract surface; for each changed contract (API, schema, CLI flag, config key, behavior semantics):

1. Find where it is documented — `rg '<symbol>' docs/ README* AGENTS.md` and public docstrings.
2. Check whether the diff updated those spots. Docs untouched while behavior changed → WARNING (REVISE: update docs).
3. A project rule requiring docs to ship with code (stated in `AGENTS.md`) → violating it is BLOCKER, same as any stated constraint.

Pure internal refactors with no contract change trigger nothing. Docs outside the repo you can see → `Needs Human`.

### Debt signals

Flag only when it creates real maintenance cost or risk.

- **Wrong abstraction layer** — a helper/module that doesn't actually abstract anything, or abstracts the wrong axis (calling through four layers to add one line)
- **Circular module dependencies** — A imports B imports A
- **God module** — a file growing to handle unrelated concerns every change feeds
- **Asymmetric APIs** — `open` without `close`, `get` without `set`, `start` without `stop`; callers cannot clean up
- **Copy-paste already diverged** — same logic in two places where one side has already drifted; or sort/normalize/validate logic repeated with each copy subtly different
- **Magic numbers / hardcoded environment assumptions** — paths, ports, timestamps, limits inline where they will rot silently
- **Over-engineering** — abstraction, plugin system, or config surface built for requirements that don't exist
- **Dead code / commented-out blocks** — INFO unless masking a claimed behavior
- Project's `AGENTS.md` rules and established patterns always apply.

## 6. Probe bundle

Run these once, after reading the diff, against the changed files (fill in the paths):

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

For each exported symbol touched by the diff: `rg -l '<symbol>' <project>` to find consumers, including outside the diff.

## 7. Severity calibration

| Situation | Correct verdict |
|---|---|
| Handler logs the payload but the claim is "processes the message" | BLOCKER (Q1 stub) |
| Function correctly written but no call site anywhere | WARNING (Q1 unwired) |
| Diff changes a helper's return from `[]` to `null`; a diff-outside caller does `.map()` directly | BLOCKER (Q2) |
| Endpoint now returns 200 with an error body where callers keyed on 4xx | WARNING/BLOCKER by severity (Q2) |
| The only test of a claimed behavior is skipped | BLOCKER (Q4) |
| `expect(true).toBe(true)` | BLOCKER (Q4) |
| A test checks `toBeDefined` plus two strong value assertions | no finding |
| Four-line input normalization duplicated, rules stable | no finding |
| Duplicated validation already diverged between two call sites | WARNING (Q4 debt) |
| Query executed, result discarded, static `{ ok: true }` returned | BLOCKER (Q1) |
| Deletion of a helper that turns out to still be imported (build would catch) | no finding — CI owns build breakage |
| Race between two async writes with a concrete interleaving | BLOCKER (Q3) |
| Implementation works but violates a stated design constraint (module boundary, API contract written as "must") | BLOCKER (Q1 design conformance) |
| Change alters an API the docs describe, docs untouched in the diff | WARNING (Q4 documentation drift) |
| Concern about visual appearance of a changed component | `Needs Human` |
| "I would have structured this module differently" | no finding |

Judgement note: any Blocker → BLOCK, else any Warning → REVISE, else PASS. Counting warnings is not the mechanism.

## 8. Worked examples

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

**Correct handling**: extract the *contract* — signature, accepted inputs, output format, timezone behavior. Diff the contract against the old version. `rg -l` the consumers, read 3–5 representative call sites across categories (props rendering, API serialization, cache keys — anything that might hold a format assumption). Report the remainder under `UNCOVERED STEPS` or `Needs Human` with the reason.

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

### Example E — Serious logic risk, discussion only

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

Severe, irreversible, but possibly requirement-driven. Report under `Serious Logic Risks (Discuss with User)`; it does not change the verdict.