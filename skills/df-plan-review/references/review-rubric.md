# Plan Review Rubric — Detailed Procedures

Procedures for the six correctness checks. Load this when a check needs its full method, a probe recipe, or severity calibration.

**Purpose reminder**: this review answers "will this Plan work if executed literally". It does not audit form — `flow.sh plan check` owns form and has already passed.

Contents:
1. [Reading the Plan](#1-reading-the-plan)
2. [C1 Artifact Closure](#2-c1--artifact-closure)
3. [C2 Symbol Closure](#3-c2--symbol-closure)
4. [C3 Fact Verification](#4-c3--fact-verification)
5. [C4 Agreement Consistency](#5-c4--agreement-consistency)
6. [C5 Executability & Handoff](#6-c5--executability--handoff)
7. [C6 Goal Fidelity](#7-c6--goal-fidelity)
8. [Severity Calibration](#8-severity-calibration)
9. [Worked Examples](#9-worked-examples)
10. [Report Skeleton](#10-report-skeleton)

---

## 1. Reading the Plan

Read the whole Plan once, with line numbers, before running any probe. Build three working lists as you read:

1. **Claims** — every concrete factual assertion (counts, paths, line anchors, document sections, IDs, commands, flags).
2. **Symbols** — every code-like identifier in backticks, with the Task that consumes it and the Task that should produce it.
3. **Files** — every file path mentioned anywhere, with its mention context (Task `Files`, `Changes`, `Affected Files` row, `Pre-read`, test path).

Then probe. Do not alternate between reading and probing — each return to the Plan costs more than the probe saved.

Keep the Plan's own declared execution mode in mind from the start: a Plan may declare that "waves are dependency layers, not parallel batches", executed sequentially in one shared worktree. That single sentence changes how C1's overlap finding and C5's ordering finding should be judged.

---

## 2. C1 — Artifact Closure

### Why the check exists

Two independent lists describe the same work: each Task's `Files`/`Changes`, and the plan-level `Affected Files` table. They are written at different moments and drift. Drift means either unauthorized edits or undelivered scope.

### Procedure

1. **Extract per-task files.** For each Task, collect paths from `**Files**` and `**Changes**`.
2. **Extract table files.** Collect paths from the `## Affected Files` table rows.
3. **Diff both directions.**
   - `task_files − table_files` → work not covered by the scope contract
   - `table_files − task_files` → declared scope with no producer
4. **Sanity-check operations.** For every file declared as created, confirm it does not already exist; for every file declared for deletion, confirm it does. For files declared as modified, confirm they exist.
5. **Check same-wave overlap.** List files per wave. Intersection inside a wave is a conflict *only* if the Plan claims parallel execution. If the Plan states waves are dependency layers executed sequentially, overlap is expected — do not report it.

### Severity

| Condition | Severity |
|---|---|
| Table row with no producing task | BLOCKER |
| Task edits a file absent from its own `Files` field | WARNING |
| Task `Files` includes a path absent from `Affected Files` | WARNING |
| File declared as created already exists / file declared for deletion is missing | WARNING |
| Same-wave file overlap under declared parallel execution | BLOCKER |
| Same-wave file overlap under declared sequential execution | not a finding |

### Common false positive

Table rows sometimes carry narrative paths that are not files (e.g. a generated runtime artifact name produced by code, not by the Plan). Check the `Role` column before reporting a missing producer — if the row documents an artifact the code creates, it needs no task.

---

## 3. C2 — Symbol Closure

### Why the check exists

Cross-task plans break at the seams. A later task calls a function, error code, exported type, constant, fixture, env var, or CLI flag that no earlier task creates — or creates under a different spelling. The Plan reads coherently; execution hits an undefined identifier.

### Procedure

1. **Harvest consumers.** Walk the Tasks in order. Collect code-like backticked identifiers that a task *uses*: function and method calls, constants in upper snake case, exported types, fixtures, CLI flags, env vars, and file exports.
2. **Harvest producers.** Collect identifiers each task *declares*: "register X", "create Y", "export Z", new file paths that will hold them.
3. **Match each consumer to a producer.** Confirm:
   - a producer exists somewhere in the Plan
   - the spelling matches exactly on both sides
   - the producer's Task precedes the consumer's Task in the declared order
4. **Check registration completeness.** When a task says it registers a *set* of symbols ("registers the five codes: A, B, C, D, E"), verify every symbol used elsewhere in the Plan appears in that set — and that no task registers into a file the Plan never lists.

### Severity

| Condition | Severity |
|---|---|
| Consumed symbol with no producer anywhere in the Plan | BLOCKER |
| Producer name differs from consumer's expected name | BLOCKER |
| Producer sits in a later wave than its consumer | BLOCKER |
| Producer exists but its export/registration location is unstated and matters to wiring | WARNING |
| Producer's file is not in `Affected Files` | report under C1 instead |

### Efficiency note

This check is fully static — it needs the Plan only, not the repo. Do it in one pass right after reading. It is the highest-yield check per unit of effort, because seam failures are both common and invisible to form validators.

---

## 4. C3 — Fact Verification

### Why the check exists

Plans are written against a mental model of the code, often assembled from earlier reading. When that model is stale, every task inherits the error, and it surfaces mid-execution after context is already spent. The repo is the only authority.

### Procedure

Check each claim class mechanically. Never "look plausible" a claim away.

| Claim class | Probe | Load-bearing? |
|---|---|---|
| Counts ("36 capabilities", "8 skills") | count them in the source of truth | yes — the count motivates work |
| Paths / filenames | `test -e`, `ls`, `rg --files` | yes |
| Line anchors ("`file.ts:619-669`") | `sed -n 'Np' file` at the target revision | depends — verify the *statement*, tolerate small drift |
| Document sections cited | `rg -n '^#{2,3} Section' doc.md` | yes — it is the Plan's authority citation |
| Decision / Gap IDs (`D-xx`, project gap or issue IDs) | `rg -n` the ID in its source of truth | yes |
| Commands and flags named in ACs | check the command exists and accepts the argument | yes |
| Existing vs created file | `test -e` | yes |
| Existing vs deleted file | `test -e` | yes |
| Environment state claims ("the symlinks exist") | inspect the live environment | yes — if it justifies work |

### Revision discipline

State the revision every fact check ran against: the Plan's `Base Commit`, the worktree HEAD, or the integration HEAD. Facts drift with commits; an unanchored finding is untrustworthy the moment anyone commits.

When a Plan declares a worktree, code facts must be probed **at that worktree's HEAD** — not on the integration branch, which may be behind or ahead.

### Severity

| Condition | Severity |
|---|---|
| Load-bearing claim is false — the change is justified *because* of it | BLOCKER |
| Claim is false and a task built on it would do the wrong thing | BLOCKER |
| Descriptive drift with no effect on the work (anchor slightly off in a large file) | WARNING |
| Cosmetic drift (imprecise count, ordering difference) | INFO |
| Claim not settleable from the workspace | `Unverified` — not a finding |

### Anchor-drift judgement

Line anchors exist to locate code, not to be exact. Probe the anchor and read a few lines around it:
- Lands on the described construct → pass
- Lands nearby, construct clearly identifiable → pass
- Lands on unrelated code, or the construct is elsewhere → WARNING
- Construct does not exist at the stated revision → BLOCKER if load-bearing, else WARNING

---

## 5. C4 — Agreement Consistency

### Why the check exists

A Plan executes inside a web of contracts: design documents, project `AGENTS.md`, established interfaces, sibling conventions. Where the Plan contradicts one of them without saying so, the deliverable violates a contract nobody renegotiated.

### Procedure

1. **Collect declared authorities.** From Technical Context and `Pre-read`, list the design docs, rule files, and interfaces the Plan names as its basis.
2. **Locate each claimed basis.** Confirm the cited sections actually exist and say what the Plan claims they say.
3. **For each Plan decision, find the governing statement.** Where the Plan makes a choice that a document also addresses, compare them.
4. **Classify any divergence:**
   - **Acknowledged** — the Plan states the divergence and justifies it, or states it updates the doc → not a finding
   - **Deferred** — the Plan explicitly excludes it (e.g. Out of Scope with a reason) → not a finding
   - **Silent** — divergence neither acknowledged nor justified → finding

### Severity

| Condition | Severity |
|---|---|
| Silent divergence from a design doc or project rule | WARNING |
| Divergence breaks a stated safety or security constraint | BLOCKER |
| Plan cites a document section that does not exist or does not say what is claimed | WARNING (report under C3 if the citation is load-bearing) |
| Divergence acknowledged and justified by the Plan | not a finding |

### Judgement note

Not every document statement is binding. Older documents may describe a superseded model while the Plan implements the current one. Establish which document is authoritative *for the model this Plan implements* before calling a conflict. If the Plan targets a newer model and an older doc still describes the old one, the question is whether the Plan acknowledged it — not which is "right".

---

## 6. C5 — Executability & Handoff

### Why the check exists

The Plan is what the implementer receives. Whoever executes a Task works from the Plan and the files it names, not from the author's unwritten context — a Task that only makes sense with that context will stall, improvise, or drift. Separately, an acceptance criterion that no task owns is never proven.

### Procedure

**Step 1 — AC ownership.**
1. List every AC in `### Agent Verification`, by number.
2. Collect the referenced set from every Task's `**Verification Intent**`.
3. Diff them. Unreferenced ACs have no owner.
4. For ACs that genuinely span tasks, confirm they are explicitly marked as spanning multiple tasks rather than silently unowned.
5. Check bucket placement: automatable verification (tests, lint, typecheck, static checks, scriptable assertions) must live in Agent Verification; only criteria requiring human observation belong in User Validation. A criterion in the wrong bucket wastes the responsible party's effort.

**Step 2 — Handoff readiness.**
For each Task, ask whether whoever implements it, knowing only the Plan and the declared `Pre-read`, could start work:
- Are the interfaces, types, and outputs of earlier Tasks **named**, not implied ("uses the response shape from Task 2" is weak; "calls `parseConfig(path)` returning a `ParsedConfig`" is ready)?
- Is the Task's own output defined well enough that the *next* Task can consume it?
- Does `Pre-read` list the right files — and do those files exist?

**Step 3 — Ordering.**
- Declared wave/dependency order matches the dependency table (no consumer before its producer).
- The declared execution mode matches reality: if the Plan says "waves are dependency layers, sequential in one worktree", do not penalize same-wave file overlap; if it claims parallel waves, verify file-disjointness.
- No task depends on an artifact whose creation the Plan never schedules.

**Step 4 — Runnability.**
- Each AC command runs in the environment the Plan declares: correct project root, script names that exist, tooling that is available, and any required setup present as a step.
- ACs requiring a stateful precondition (a running server, a built artifact, a temporary home) state that precondition or include the step that establishes it.
- Commands whose failure mode is inverted (negated assertions) state the expected exit code correctly.

### Severity

| Condition | Severity |
|---|---|
| AC owned by no task | WARNING |
| AC command cannot run as written in the declared environment | BLOCKER |
| Automatable verification placed in User Validation | WARNING |
| Human-observation-only criterion claimed as agent-verifiable | WARNING |
| Task not startable from Plan + declared `Pre-read` alone | WARNING |
| Declared order contradicts declared dependencies | BLOCKER |
| `Pre-read` names a file that does not exist | WARNING |
| Undeclared precondition needed before an AC can run | WARNING |

### Judgement note

Resist flagging handoff gaps for Tasks that are one step of an obvious sequence. The bar is "could a competent implementer proceed". Only flag where the missing information would cause a wrong turn — an interface that must be guessed, an output shape that is ambiguous, or a dependency the implementer cannot discover.

---

## 7. C6 — Goal Fidelity

### Why the check exists

The costliest failure is a Plan that passes every structural check and still under-delivers: a goal component with no task, a decision quietly reduced to a first version, acceptance criteria that cannot fail.

### Procedure

1. **Decompose the Goal.** Split `## Goal` into its independently meaningful components. For each, find the Task(s) that deliver it.
2. **Trace decisions to delivery.** For each `D-xx` in Key Decisions, find the task(s) that implement it and confirm the delivery matches the decision's scope.
3. **Scan for reduction language.** Search task text for `v1`, `v2`, `simplified`, `static for now`, `hardcoded`, `placeholder`, `basic version`, `minimal`, `NOT wired to`, `NOT connected to`, `stub`, `future enhancement`, `will be wired later`, `skip for now`, `for now`.
4. **Adjudicate each hit.** Two questions, in order:
   - Does the reduction contradict the Goal or a `D-xx`? If not → not a finding.
   - Does a `D-xx` or scope statement **sanction** the reduction? If yes → not a finding. Plans legitimately deliver phased work when the Plan says so.
5. **Test each AC's falsifiability.** Ask: if the feature were broken, would this command fail? An AC that passes regardless — asserting existence where behavior is the claim, or restating the change — is decoration.

### Severity

| Condition | Severity |
|---|---|
| Goal component with no covering task | BLOCKER |
| Decision reduced without the Plan acknowledging it | BLOCKER |
| Reduction language sanctioned by a `D-xx` or scope statement | not a finding |
| AC owned by no task | WARNING |
| AC that cannot fail | WARNING |
| Goal referenced but never stated in a checkable form | WARNING |

### Why reduced decisions are BLOCKER, not WARNING

A reduced deliverable that reaches `verify` has already spent the execution budget. Catching it before execution is the whole value of this review. If the Plan wants to deliver a phase, the correct move is to *say so* — phrase it as the deliverable, adjust the Goal, or split it into an explicit follow-up. What cannot pass is a silent shrink.

---

## 8. Severity Calibration

Four classes, defined by what the reader should do:

| Class | Meaning | Test to apply |
|---|---|---|
| **BLOCKER** | Executing as written will fail, violate a contract, or under-deliver the Goal | "If this ships, is it broken or dishonest?" |
| **WARNING** | Execution succeeds but the Plan is unsafe, ambiguous, or unverified where it should be verified | "Will this cost rework or hide a gap?" |
| **INFO** | Improvement worth knowing, no action required | "Would a reasonable author shrug?" |
| **Unverified** | Claim could not be settled from the workspace | "Could I not check this?" |

Deliberately absent: **size/count thresholds**. Context budget is managed per Task, not per Plan; a large cohesive Plan is normal. Never report task count, file count, or wave count as a finding.

### Calibration drills

| Situation | Correct verdict |
|---|---|
| Plan has 12 tasks, all mutually dependent, Plan states it will not split and why | no finding (size is not a defect) |
| Plan declares a file as newly created, but the file already exists | WARNING (stale premise; the implementer will improvise) |
| Task references a function no other task creates | BLOCKER |
| Task registers 5 error codes, a later task uses a 6th | BLOCKER |
| Anchor `file.ts:964` lands at 967 on the described function | no finding |
| Anchor `file.ts:964` lands in an unrelated block, function is at 1200 | WARNING |
| Plan contradicts a design doc it also cites, without acknowledgement | WARNING |
| Plan contradicts a design doc and states "this supersedes §X of doc Y" | no finding |
| AC is `rg -c 'pattern' file ≥ 1` for a behavior that the file could contain while the feature is broken | WARNING (weak falsifiability) |
| Reduction to `v1` where `D-04` says "start with static data, dynamic later — this Plan delivers the static layer" | no finding |
| Reduction to `v1` where `D-04` says "config displays calculated costs" | BLOCKER |
| A concern you could not check for lack of a sandbox | `Unverified`, never a finding |

---

## 9. Worked Examples

### Example A — Symbol closure catches an unregistered code

**Plan shape**: Task 2 creates an error-code module and registers five codes: `A_MISSING`, `A_INVALID`, `S_MISSING`, `S_INVALID`, `C_UNRESOLVED`. Task 4 describes a failure branch "fail fast with `TEMPLATE_MISSING`".

**Probe**: list the registered set, list every `UPPER_SNAKE` code used across the Plan, diff.

**Finding**:
```yaml
check: C2_symbol_closure
severity: blocker
plan_location: "{plan}.md:{line of Task 4 branch}"
reality: "registered set at {plan}.md:{line of Task 2 statement}; TEMPLATE_MISSING absent"
impact: "Task 4's failure branch cannot be implemented as written; the implementer will improvise a second registration site or reuse a wrong code"
fix: "add TEMPLATE_MISSING to the registration task, or reference an existing code"
```

### Example B — Artifact closure catches drift on both sides

**Plan shape**: Task 2 `Changes` includes "step 3: register five error codes in `src/lib/errors.ts`". Task 3 includes "step 2: register `SYNC_APPLY_FAILED` in `src/lib/errors.ts`". The `Affected Files` table has rows for ten components; `src/lib/errors.ts` is not among them.

**Finding**:
```yaml
check: C1_artifact_closure
severity: warning
plan_location: "{plan}.md:{line of Task 2 step 3}"
reality: "Affected Files table at {plan}.md:{line range} lists no row for src/lib/errors.ts"
impact: "the file is edited by two tasks but sits outside the Plan's declared file scope"
fix: "add an Affected Files row naming the file and the tasks that touch it"
```

### Example C — Fact verification with a load-bearing premise

**Plan shape**: Technical Context asserts "the legacy schema path is gone from the ontology, so initialization necessarily fails". Task 4 removes the reader for that path, and AC#7 asserts a repo-wide search returns zero hits for the old identifiers.

**Probe**: at the stated revision, search the repo for the old path and for callers of the reader.

**Finding**:
```yaml
check: C3_fact_verification
severity: blocker
plan_location: "{plan}.md:{line of the premise}"
reality: "{file}:{line} still imports and calls the old reader; the Plan's search list does not include that call site"
revision: "{commit}"
impact: "the premise 'no other callers exist' is false; the repo-wide AC cannot pass because an unnamed call site remains"
fix: "name the remaining call site in a task's scope, or add it to the removal task"
```

Note how the AC itself reveals the defect once the premise is checked: the Plan's own acceptance criterion would fail at verify time, after the whole execution budget was spent. That is exactly what C3 exists to prevent.

### Example D — Correctly NOT reporting a finding

**Plan shape**: six tasks, 11 `Affected Files` rows, four waves; a `D-10` states "single-Plan delivery, not split by task count; tasks are mutually dependent; context budget is managed per task".

**Correct handling**: no finding on size, task count, or file count. `D-10` is the author's explicit, justified decision. Report under Positive Findings if useful ("single-plan decision is explicit and its rationale is stated"). If the review form tempts you to flag "6 tasks exceeds the recommended 2–3", that form is gone — it does not exist here.

### Example E — Executability catches an unowned acceptance criterion

**Plan shape**: 13 Agent Verification ACs. Six tasks declare `Verification Intent`; the referenced set covers ACs 1–6, 8, 10, 12, 13. ACs 7, 9, 11 are referenced by no task; only AC#10 carries an explicit "(cross-task)" marker.

**Finding**:
```yaml
check: C5_executability
severity: warning
plan_location: "{plan}.md:{line range of ACs 7,9,11}"
reality: "no Verification Intent references these; only AC#10 is marked cross-task"
impact: "three acceptance criteria have no owner, so nothing in the execution plan is responsible for proving them"
fix: "assign each AC to a task's Verification Intent, or mark it cross-task explicitly"
```

---

## 10. Report Skeleton

```markdown
# Plan Review — {plan-name}

## Summary
- Review type: Plan
- Verdict: PASS | REVISE | BLOCK
- Counts: Blocker N / Warning N / Info N / Unverified N
- Verified against: {revision}

## Blocker
### B-01: {title}
- Plan location: `{plan}.md:{line}`
- Reality: `{file}:{line}` / `{output}` — {conflict}
- Impact: {failure mode at execution}
- Fix direction: {what to add/change}

## Warning
{as above}

## Info
{one line each}

## Unverified
- {claim} — reason not verified: {why it could not be checked}

## Requirement Questions
{only when the requirement itself is ambiguous}

## Positive Findings
- {verified item — state how it was verified}

## UNCOVERED CHECKS
{only when a check could not be completed}
```

### Verdict decision

- Any Blocker → `BLOCK`
- No Blocker, at least one Warning → `REVISE`
- Nothing but Info (or nothing) → `PASS`
- `Unverified` never changes the verdict; it only informs the reader

### Positive Findings is mandatory on PASS

A `PASS` must say what was checked and how — e.g. "counts in Technical Context verified against their source of truth; cited file paths all exist at the stated revision; cited design sections all present; every AC is referenced by a Task's Verification Intent". A bare `PASS` asks the reader to take your word for it, which defeats the purpose of a review.
