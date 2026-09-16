# Implementation Review Rubric — Detailed Procedures

Procedures for the six correctness checks. Load this when a check needs its full method, a pattern catalogue, or severity calibration.

**Purpose reminder**: this review answers "does this change really deliver, and is it sound code". It does not audit form — tests, lint, typecheck, and CI own form and have already passed.

Contents:
1. [Reading the Change](#1-reading-the-change)
2. [C1 Goal & Truth Verification](#2-c1--goal--truth-verification)
3. [C2 Scope Completeness](#3-c2--scope-completeness)
4. [C3 Substance & Wiring](#4-c3--substance--wiring)
5. [C4 Defect & Security Scan](#5-c4--defect--security-scan)
6. [C5 Test Integrity](#6-c5--test-integrity)
7. [C6 Conventions & Debt](#7-c6--conventions--debt)
8. [Severity Calibration](#8-severity-calibration)
9. [Worked Examples](#9-worked-examples)
10. [Report Skeleton](#10-report-skeleton)

---

## 1. Reading the Change

Build the review set first: the diff (`git diff`, `git diff --cached`, `git show <hash>`, or `git diff <A>..<B>`), the changed file list, and — when Plan-backed — the Plan's claims. Read once; then probe.

Keep three working lists as you read:

1. **Claims** — every explicit deliverable or acceptance criterion the change is supposed to satisfy.
2. **Artifacts** — every new or modified file, symbol, route, component, or schema element, with where it is consumed.
3. **Flags** — anything that smells of a stub, a wiring gap, or a missing test, to verify in the sweeps.

Do not alternate between reading and probing; each return to a file costs more than the probe saved.

Note the review mode from the start. In planless mode, the change's own stated intent (description, commit message) is the only spec — everything else belongs to C2–C6.

---

## 2. C1 — Goal & Truth Verification

### Why the check exists

Tests prove what they assert, not what was promised. A change can be green and still be a stub, an orphaned file, or a reduced version of the goal. This check compares the promise against the artifact, level by level.

### Procedure

1. **Extract claims.**
   - Plan-backed: every truth in the Plan, every acceptance criterion, and the stated Goal.
   - Planless: the change's stated intent — description, commit message, or an explicit instruction in the review prompt. If none exists, say so and skip to C2.
2. **Locate each artifact** the claim depends on: the file, function, route, component, or schema element.
3. **Walk the four levels** for each:

| Level | Question | How to settle |
|---|---|---|
| 1. Exists | Is the artifact present at the expected path? | `ls`, `rg --files`, `git show --stat` |
| 2. Substantive | Is it a real implementation, not a stub? | read the code; C3 catalogues the patterns |
| 3. Wired | Is it imported, registered, or called — reachable from an entry point? | trace call sites: `rg <symbol>` across the project |
| 4. Functional | Does it behave correctly when invoked? | static reasoning where possible; otherwise `Needs Human` |

4. **Adjudicate reductions.** When the artifact delivers less than the claim (reduced scope, deferred branch, a `v1` of the stated goal), check whether a Plan decision sanctions it. Sanctioned → note it, not a finding. Silent → BLOCKER.

### Severity

| Condition | Severity |
|---|---|
| Claimed artifact missing from the change | BLOCKER |
| Artifact is a stub | BLOCKER |
| Artifact real but never reachable | WARNING; BLOCKER when reachability is the claim |
| Silent reduction of a claimed deliverable | BLOCKER |
| Reduction sanctioned by a Plan decision | not a finding |
| Level 4 not provable statically | `Needs Human` — not a finding |
| Planless mode, no stated intent | note intent was not stated; proceed with C2–C6 |

### Level-4 discipline

Level 4 is "it actually works when invoked". Do not claim it from static reading. What static reading can settle: obviously correct logic over the inputs the claim names. What it cannot: runtime behavior, timing, rendering, external integrations, real data. Those go under `Needs Human` with the exact observation a human should make.

Level-4 items typically needing human observation:

- Visual appearance and layout
- End-to-end user flow usability
- Real-time behavior (WebSocket / SSE / streaming)
- External service integrations (payments, mail, third-party APIs)
- Error message clarity and helpfulness
- Responsive / mobile behavior
- Accessibility

---

## 3. C2 — Scope Completeness

### Why the check exists

Declared scope and delivered scope are written at different moments and drift. Under-delivery hides behind "the rest will follow". Over-delivery hides unrelated work and undeclared coupling.

### Procedure

1. **Build the delivered set** from the carrier: `git diff --name-status`, `git show --stat`.
2. **Build the declared set** from the Plan's file lists or the change description.
3. **Diff both directions:**
   - `declared − delivered` → promised work that is missing
   - `delivered − declared` → work performed outside the declaration
4. **Sanity-check operations.** Deletions and renames must match what was declared; unexpected deletions are how entire features disappear quietly.
5. **Judge each diff item.** A declared item missing is BLOCKER only when a claim depends on it. An extra file is WARNING unless the coupling is necessary — if it is, the finding is that the declaration was stale, not that the code is wrong.

### Severity

| Condition | Severity |
|---|---|
| Declared deliverable absent, and a claim depends on it | BLOCKER |
| Declared item absent, not load-bearing | WARNING |
| Changed files outside the declared scope | WARNING |
| Unannounced deletion or rename | WARNING |

---

## 4. C3 — Substance & Wiring

### Why the check exists

The most common way a change looks done without being done is placeholder code that satisfies types and expectations. The second most common is real code nothing calls.

### Part A — Stub sweep

Sweep the changed files for these patterns. Presence is a signal, not a verdict: classify with the surrounding context.

**Comment stubs**

```javascript
// TODO: implement later
// FIXME: this is broken
// HACK: temporary
// PLACEHOLDER
// ... (an empty body where logic belongs)
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

Probe: `rg -n 'return null|return undefined|return \{\}|return \[\]' <changed files>`

Caution: honest empty returns exist. Classify by whether a caller or claim depends on real content.

**Log-only handlers**

```javascript
function handler(data) {
  console.log(data)          // logs, does nothing
}
```

Probe: read each handler body; a body that only logs or only forwards has no behavior.

**Fake-dynamic values**

```jsx
// Should come from state/props, hardcoded instead
<div>Message 1</div>
const id = "fixed-id"        // should be generated
const count = 3              // should be computed
const price = "$9.99"        // should be formatted
```

Classify by the claim: if the behavior must be dynamic and the value is fixed, BLOCKER; if the value is legitimately fixed, not a finding.

**Frontend shells**

```jsx
return <div>Component</div>
return <p>Coming soon</p>
return <div>{/* TODO */}</div>
return null
return <></>

onClick={() => {}}                       // empty handler
onChange={() => console.log('clicked')}  // log-only handler
onSubmit={(e) => e.preventDefault()}     // only blocks default
```

Check that the component renders substantive elements — dynamic expressions, state or prop usage, wired handlers.

**API route shells**

```typescript
export async function GET() {
  return Response.json([])              // static empty, no data source
}
export async function POST() {
  return new Response()                 // empty body
}
export async function POST(req) {
  console.log(await req.json())
  return Response.json({ ok: true })    // logs and acknowledges, never processes
}
```

**Database schema stubs**

```prisma
model Message {
  id      String @id
  content String
  // missing: createdAt, userId, chatId and the relations that use them
}
```

Check every model against the claim: the fields and relations the behavior needs must exist.

**Hook / utility stubs**

```typescript
export function useAuth() {
  return { user: null, login: () => {}, logout: () => {} }
}
export function useUser() {
  return { name: "Test User", email: "test@example.com" }   // hardcoded
}
```

Check that the returned functions and values do real work — call APIs, touch state, produce effects.

### Part B — Wiring checks

For every new artifact, verify all three links of its chain:

1. **Declared → imported**: `rg <symbol>` — is it imported where it is used?
2. **Imported → used**: is the import actually referenced, not merely present?
3. **Used → reachable**: does some entry point (route, render tree, CLI, job runner) lead to it?

Pattern-specific checks:

**Component → data source.** Data-fetching calls must be awaited, consumed, and rendered (or otherwise used):

```jsx
// Consumed
useEffect(() => { fetch('/api/messages').then(r => r.json()).then(setMessages) }, [])

// Not consumed: no await, no .then, no assignment
fetch('/api/messages')

// Commented out
// fetch('/api/messages').then(r => r.json()).then(setMessages)
```

**State → render.** A state variable that should drive output must actually appear in the output:

```jsx
const [messages, setMessages] = useState([])
return <div>No messages</div>            // renders a constant, not the state
return <div>{otherData.map(...)}</div>   // renders the wrong variable
```

**API → storage.** A query must be awaited and its result returned, not discarded:

```typescript
const messages = await prisma.message.findMany()
return Response.json(messages)           // correct

await prisma.message.findMany()
return Response.json({ ok: true })       // queries, then discards

const messages = prisma.message.findMany()
return Response.json(messages)           // returns the promise, not the data
```

**Route → registration.** A new route, command, or job must be registered where the framework or runner discovers it.

### Severity

| Condition | Severity |
|---|---|
| Stub occupying a claimed behavior | BLOCKER |
| New module, component, or route never imported, registered, or used | WARNING |
| Real artifact reachable only through dead code | WARNING |
| Empty return that the claim depends on | BLOCKER |
| Empty return that is honest (no dependency) | not a finding |
| TODO / FIXME on a non-critical path | INFO |

---

## 5. C4 — Defect & Security Scan

### Why the check exists

Tests cover what someone thought to assert. Defects live in the branches, inputs, and timings nobody asserted. Security holes live at trust boundaries the tests never cross.

### Part A — Defect sweep

Walk each hunk and ask the failure question: **what input, state, or timing makes this wrong?**

High-yield areas:

- **Error paths** — failures swallowed, errors logged but not propagated, cleanup skipped on the error branch
- **Async handling** — missing `await`, floating promises, race conditions, unhandled rejections, ordering assumptions
- **Boundary values** — empty collections, zero, negative, very large, off-by-one in ranges and slices
- **Type/runtime seams** — parsed input trusted as typed, `as` casts over unvalidated data, nullability assumptions
- **State transitions** — re-entrancy, double-submission, partially applied updates, rollback on failure
- **Comparison logic** — `==` vs `===` semantics, falsy checks over values that can legitimately be falsy

Report only findings with a concrete scenario. "Could be wrong" is not a finding.

### Part B — Security sweep

Find the trust boundaries and check each:

- **Injection** — user input reaching queries, shell commands, or templates unparameterized
- **XSS** — unescaped interpolation into rendered output, `dangerouslySetInnerHTML` equivalents
- **Unsafe deserialization** — untrusted payloads passed to parsers with code-execution surface
- **Missing validation** — request bodies used before validation; schema validation present but bypassed
- **Authorization gaps** — new routes or handlers missing the auth check their siblings have
- **Secret exposure** — credentials in code, committed files, logs, or error messages

Probe: `rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' <changed files>`; check every new POST/PUT handler for validation before use.

### Severity

| Condition | Severity |
|---|---|
| Defect with a concrete failure scenario | BLOCKER |
| Exploitable security hole (injection, XSS, missing auth, leaked secret) | BLOCKER |
| Plausible risk with a concrete scenario ("in Z scenario leads to Y") | WARNING |
| Missing input validation on a public surface | WARNING |
| Concern with no concrete scenario | do not report |

---

## 6. C5 — Test Integrity

### Why the check exists

Tests are the strongest evidence a change provides — and the easiest to fake. A green suite proves nothing if the tests that matter are skipped, circular, or vacuous.

### Procedure

1. **Map behavior to tests.** For each behavior the change claims, find the test(s) that cover it. A claimed behavior with no covering test → WARNING (BLOCKER when the Plan requires tests).
2. **Inspect the assertions.** Read what each test actually asserts, not what its name says.
3. **Sweep for broken patterns** (below).

### Broken patterns

**Skipped / disabled tests**

```typescript
it.skip('sends a message', () => { ... })
xit('loads data')
xdescribe('Messages')
describe.skip('Chat', () => { ... })
```

```python
@pytest.mark.skip
def test_send(): ...
```

```go
t.Skip("not implemented")
```

Probe: `rg -n 'skip\(|xit|xdescribe|\.skip|@pytest\.mark\.skip|t\.Skip' <changed test files>`
Verdict: a claimed behavior whose only tests are skipped → BLOCKER.

**Circular proofs**

The system generates the expected value and the same system verifies it:

```typescript
const expected = generateOutput(input)   // the function under test
const actual = generateOutput(input)     // same function
expect(actual).toEqual(expected)         // proves nothing
```

Verdict: BLOCKER.

**Placeholder assertions**

```typescript
expect(true).toBe(true)
expect(false).toBe(false)
expect(1).toBe(1)
```

Probe: `rg -n 'expect\(true\)|expect\(false\)|expect\(1\)|expect\("test"\)' <changed test files>`
Verdict: BLOCKER.

**Weak assertions**

```typescript
expect(result).toBeDefined()
expect(component).toBeTruthy()
expect(data).not.toBeNull()
```

They check existence, not value:

```typescript
// weak
expect(result).toBeDefined()
// strong — asserts the actual behavior
expect(result).toEqual({ id: 1, name: 'test' })
expect(result.items).toHaveLength(3)
```

Probe: `rg -n 'toBeDefined|toBeTruthy|toBeFalsy|not\.toBeNull' <changed test files>`
Verdict: a single weak assertion → INFO; every assertion in a file weak → WARNING.

**Missing assertions**

A test file or test case with no `expect` / `assert` at all — the shell runs and reports green.

Probe: `rg -c 'expect|assert' <test file>` — zero → WARNING.

**Redundant tests**

Many tests repeating the same happy path while distinct branches remain untested. Read the changed tests and check whether each protects a different behavior.

Verdict: WARNING when key branches are untested; otherwise none.

### Judgement note

The bar is "does the test fail when the behavior breaks". A test that would still pass with the feature removed is decoration, regardless of how thorough it looks. When coverage exists but you cannot tell whether a test would catch a regression, read the assertion and the code path it exercises — do not count test names.

---

## 7. C6 — Conventions & Debt

### Why the check exists

Projects have standing contracts — `AGENTS.md`, established patterns, safety rules — and a debt budget. A change that ignores the first or grows the second costs the next contributor.

### Procedure

1. **Read the project's rules.** `AGENTS.md` at the project root (and directory-level ones if present). Check the changed files against every applicable rule.
2. **Check pattern consistency.** Does the change follow the established pattern for its kind — error handling, logging, configuration, typing, module structure?
3. **Scan for growth of debt.**

### Duplication / extraction

Flag duplication only when it creates real maintenance cost or drift risk:

- The same validation / parsing / retry / branching logic appears in multiple places in the reviewed scope
- The duplicated logic is already diverging or likely to diverge
- A shared helper would clearly reduce bug risk or future edit cost

Do **not** flag tiny repetition with no meaningful cost, or straight-line sequences that would become less readable if abstracted.

### Dead code / brittle wiring

- Code unreachable from any entry point → WARNING when it masks a claimed behavior, else INFO
- Commented-out blocks left behind → INFO
- Config or wiring that silently disagrees with what the code reads → WARNING

### Severity

| Condition | Severity |
|---|---|
| Violates a stated safety or security constraint | BLOCKER |
| Violates conventions or breaks an established pattern | WARNING |
| Duplication already diverging, or likely to | WARNING |
| Dead code masking a claimed behavior | WARNING |
| Commented-out blocks, stale TODOs | INFO |
| Taste-level preferences | not a finding |

---

## 8. Severity Calibration

Four classes, defined by what the reader should do:

| Class | Meaning | Test to apply |
|---|---|---|
| **BLOCKER** | The change cannot ship as written | "If this ships, is it broken or dishonest?" |
| **WARNING** | It ships, but with risk, a gap, or unproven claims | "Will this cost rework or hide a defect?" |
| **INFO** | Improvement worth knowing, no action required | "Would a reasonable author shrug?" |
| **Needs Human** | Only runtime or human observation can settle it | "Can I not verify this statically?" |

Deliberately absent: **warning-count thresholds**. A verdict follows from severity, not from counting: any Blocker → BLOCK, else any Warning → REVISE, else PASS.

### Calibration drills

| Situation | Correct verdict |
|---|---|
| Handler logs the payload but the claim is "processes the message" | BLOCKER (stub occupying a claim) |
| Function exists, correctly written, but no call site anywhere | WARNING (unwired) |
| The only test of a claimed behavior is skipped | BLOCKER |
| Test asserts `expect(true).toBe(true)` | BLOCKER |
| A test checks `toBeDefined` plus two strong value assertions | no finding (single weak assertion inside a strong test is INFO at most) |
| Four-line input normalization duplicated, rules expected to stay identical | no finding |
| Duplicated validation that has already diverged between two call sites | WARNING |
| Query executed, result discarded, static `{ ok: true }` returned | BLOCKER (the claim depends on the data) |
| Deletion of a helper that turns out to still be imported (build would catch it) | no finding — CI owns build breakage |
| Concern about visual appearance of a changed component | `Needs Human`, not a finding |
| "I would have structured this module differently" | no finding |

---

## 9. Worked Examples

### Example A — Stub caught by the level walk

**Plan claim**: "Messages are fetched from the database". The route exists:

```typescript
// api/messages/route.ts:8
export async function GET() {
  return Response.json([])
}
```

**Probe**: level 2 — read the body; no query. Level 3 would pass (the route is registered), level 4 could pass for an empty system.

**Finding**:
```yaml
check: C1_goal_verification
severity: blocker
location: "api/messages/route.ts:8-10"
reality: "the handler returns a constant; no data source is consulted"
impact: "the claim 'fetched from the database' is false at level 2; the endpoint cannot serve real data"
fix: "query the store and return its result, as the claim requires"
```

### Example B — Wiring gap caught at level 3

**Change**: a new `MarkdownRenderer` component, fully implemented, with tests.

**Probe**: `rg MarkdownRenderer src/` — it appears only in its own file and its test. The message list still renders plain text.

**Finding**:
```yaml
check: C3_wiring
severity: warning
location: "components/MarkdownRenderer.tsx:1"
reality: "no import or usage outside its own module and test"
impact: "the component is unreachable from the app; the rendering improvement is not actually delivered to users"
fix: "render messages through the new component in the message list, or remove the component if premature"
```

### Example C — Circular proof in tests

**Change**: a parser plus tests.

**Probe**: read the assertions.

```typescript
const expected = parse(input)
const actual = parse(input)
expect(actual).toEqual(expected)
```

**Finding**:
```yaml
check: C5_test_integrity
severity: blocker
location: "tests/parser.test.ts:14-16"
reality: "expected and actual both come from the parser under test; any output, correct or not, compares equal"
impact: "the test cannot fail for the behavior it claims to protect"
fix: "assert against independent expected values written by hand"
```

### Example D — Duplication, correctly NOT reported

**Change**: two new handlers each trim and normalize an email before validating it. The rules are four lines and stable.

**Correct handling**: no finding. The extraction would not measurably reduce bug risk. If the reviewer is tempted to flag it, the rubric says: flag duplication only when it creates real maintenance cost or drift risk.

### Example E — Defect with a concrete scenario

**Change**: an update endpoint.

**Probe**: check the boundary values.

```typescript
// api/profile/route.ts:22
const { name } = await req.json()
await db.updateUser(userId, name)     // name may be undefined; no validation
```

**Finding**:
```yaml
check: C4_defect_scan
severity: warning
location: "api/profile/route.ts:22-23"
reality: "name is read from the body with no validation and written directly; a request without name writes undefined over the stored value"
impact: "in the scenario 'client omits the field', the user's stored name is corrupted"
fix: "validate the body before writing, and reject requests missing required fields"
```

### Example F — Serious logic risk, discussion only

**Change**: a purge job.

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

**Finding**: severe and irreversible, but whether it is correct depends on a product policy not stated in the prompt — report under `Serious Logic Risks (Discuss with User)`; it does not change the verdict.

---

## 10. Report Skeleton

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
- Evidence: `{snippet}` / {output}
- Impact: {failure mode}
- Fix direction: {what to change}

## Warning
{as above}

## Info
{one line each}

## Serious Logic Risks (Discuss with User)
{severe risks that may be requirement-driven}

## Requirement Questions
{requirement ambiguity only}

## Needs Human
- {item} — observation needed: {what to look at}

## Positive Findings
- {verified item — state how it was verified}

## UNCOVERED STEPS
{only when steps could not be completed}
```

### Verdict decision

- Any Blocker → `BLOCK`
- No Blocker, at least one Warning → `REVISE`
- Nothing but Info (or nothing) → `PASS`
- `Needs Human`, `Serious Logic Risks`, and `Requirement Questions` never change the verdict by default

### Positive Findings is mandatory on PASS

A `PASS` must say what was checked and how — for example: "diffed delivered scope against declared scope both ways; walked every claimed behavior through exists/substantive/wired; swept changed files for stub patterns; audited changed tests for skipped/circular/placeholder assertions". A bare `PASS` asks the reader to take your word for it, which defeats the purpose of a review.
