# Plan Review Rubric — Detailed Procedures

Procedures for the three questions. Load this when a question needs its full method, the command cookbook, or a worked example.

**Purpose reminder**: this review answers "will this Plan work if executed literally". It does not audit form — `flow.sh plan check` owns form and has already passed.

Contents:
1. [Reading the Plan](#1-reading-the-plan)
2. [Q1 — parts fit together](#2-q1--do-the-parts-fit-together)
3. [Q2 — statements about the repo](#3-q2--are-the-plans-statements-about-the-repo-true)
4. [Q3 — delivering the goal](#4-q3--will-executing-it-deliver-the-goal)
5. [Severity calibration](#5-severity-calibration)
6. [Worked Examples](#6-worked-examples)

---

## 1. Reading the Plan

Read the whole Plan once, with line numbers, before running any command. Build the three lists as you read:

1. **Facts** — every concrete claim about the repo (counts, paths, line anchors, document sections, IDs, commands, flags).
2. **Symbols** — every code-like name in backticks, with the Task that uses it and the Task that should create it.
3. **Files** — every file path mentioned anywhere, with where it was mentioned (Task `Files`, `Changes`, `Affected Files` row, `Pre-read`, test path).

Then run commands. Do not alternate between reading and verifying — each return to the Plan costs more than the command saved.

Keep the Plan's own declared execution mode in mind from the start: a Plan may declare that "waves are dependency layers, not parallel batches", executed sequentially in one shared worktree. That one sentence changes how file overlap is judged in Q1.

---

## 2. Q1 — Do the parts fit together?

Needs the Plan only. Run it right after reading — pure mechanics, and it catches the most common cross-task defect class.

### 2.1 Expected file scope (no audit)

Tasks no longer carry a Files field. The `## Affected Files` table is the expected footprint, not a contract: the implementing agent adjusts file choices on the real code and backfills actuals at Done. **Do not diff task-level file lists against the table — that audit is retired.** Two things remain checkable:

1. **Stale operation premises**: a table row declaring "create" for a file that already exists, or "delete" for a file that is absent — the implementer will hit a wrong turn on a false premise (WARNING).
2. **Parallel overlap**: when the Plan declares parallel execution, files overlapping between waves are a conflict (BLOCKER). When the Plan states waves are sequential dependency layers, overlap is the Plan's design — not a finding.

**Common false positive**: table rows sometimes name artifacts the code creates at runtime, not files the Plan writes — a row documenting a generated artifact needs no producer.

| Condition | Severity |
|---|---|
| Affected Files row with a stale operation premise (create-but-exists / delete-but-missing) | WARNING |
| File overlap under declared parallel execution | BLOCKER |
| File overlap under declared sequential layers | not a finding |
| Task-level file list disagrees with the table | not a finding (audit retired) |

### 2.2 Symbols have producers

1. Walk the Tasks in order. Collect code-like backticked names that a task *uses*: function and method calls, upper-snake constants, exported types, fixtures, CLI flags, env vars.
2. Collect the names each task *declares*: "register X", "create Y", "export Z", new files that will hold them.
3. Match each used name to a producer. Confirm:
   - a producer exists somewhere in the Plan
   - the spelling matches exactly
   - the producer's Task precedes the consumer's Task
4. When a task registers a *set* of names ("registers the five codes: A, B, C, D, E"), verify every name used elsewhere in the Plan appears in that set — and that no task registers into a file the Plan never lists.

| Condition | Severity |
|---|---|
| Used name with no producer anywhere in the Plan | BLOCKER |
| Producer name differs from the consumer's expected name | BLOCKER |
| Producer sits in a later wave than its consumer | BLOCKER |
| Producer exists but where it is exported/registered is unstated and matters to wiring | WARNING |
| Producer's file missing from `Affected Files` | report under 2.1 instead |

### 2.3 Every AC has an owner, in the right bucket

1. List every AC in `### Agent Verification`, by number.
2. Collect the referenced set from every Task's `**Verification Intent**`.
3. Diff them. Unreferenced ACs have no owner.
4. ACs that genuinely span tasks must be explicitly marked as cross-task.
5. Check the bucket: tests, lint, typecheck, static checks, scriptable assertions belong in Agent Verification; only human observation belongs in User Validation. A criterion in the wrong bucket wastes the responsible party's effort.

**Two-beat context**: beat-1 entries are criterion-style (behavioral pass criteria) — legal by design; the real command is written back at the RED stage (beat 2), and the complete gate enforces commands on checked entries. Never flag a criterion-style entry itself as a defect — flag only criteria that cannot catch a bad implementation (no observable outcome, restates the change).

| Condition | Severity |
|---|---|
| AC owned by no task | WARNING |
| Automatable verification sitting in User Validation | WARNING |
| Human-observation-only criterion claimed as agent-verifiable | WARNING |
| Criterion-style AC (legal beat-1 form) | not a finding |

### 2.4 Order matches dependencies

- Declared wave/dependency order must match the dependency table: no consumer before its producer.
- The declared execution mode must match reality: sequential waves tolerate same-wave file overlap; claimed parallel waves require file-disjointness.
- No task depends on an artifact whose creation the Plan never schedules.

| Condition | Severity |
|---|---|
| Declared order contradicts declared dependencies | BLOCKER |

---

## 3. Q2 — Are the Plan's statements about the repo true?

The repo is the only authority. Check each claim mechanically — never wave one through because it looks right.

### 3.1 Command cookbook

| Claim class | Command | Notes |
|---|---|---|
| Counts ("36 capabilities", "8 skills") | count them in the source of truth | the count motivates work — get it right |
| Paths / filenames | `test -e`, `ls`, `rg --files` | |
| Line anchors ("`file.ts:619-669`") | `sed -n 'Np' file` at the target revision | see anchor-drift judgement below |
| Document sections cited | `rg -n '^#{2,3} Section' doc.md` | it is the Plan's authority citation |
| Decision / issue IDs (`D-xx`, gap IDs) | `rg -n` the ID in its source of truth | |
| Commands and flags named in ACs | check the command exists and accepts the arguments | |
| Menu of "new" vs existing files | `test -e` | |
| Environment state claims ("the symlinks exist") | inspect the live environment | only when it justifies work |

**Revision discipline**: state which revision every check ran against — the Plan's `Base Commit`, the worktree HEAD, or the integration HEAD. Facts drift with commits; an unanchored finding is untrustworthy the moment anyone commits. When a Plan declares a worktree, facts must be probed **at that worktree's HEAD**, not on the integration branch.

### 3.2 Anchor-drift judgement

Line anchors exist to locate code, not to be exact. Probe the anchor and read a few lines around it:

- Lands on the described construct → pass
- Lands nearby, construct clearly identifiable → pass
- Lands on unrelated code, or the construct is elsewhere → WARNING
- Construct does not exist at the stated revision → BLOCKER if the premise leans on it, else WARNING

### 3.3 Agreement with authorities

1. From Technical Context and `Pre-read`, list the design docs, rule files, and interfaces the Plan names as its basis.
2. Confirm the cited sections actually exist and say what the Plan claims they say.
3. For each decision the Plan makes, find the governing statement in those authorities and compare.
4. Classify any divergence:
   - **Acknowledged** — the Plan states the divergence and justifies it, or states it updates the doc → not a finding
   - **Deferred** — the Plan explicitly excludes it (Out of Scope with a reason) → not a finding
   - **Silent** — neither acknowledged nor justified → finding

Judgement note: not every document statement is binding. Older documents may describe a superseded model while the Plan implements the current one. Establish which document is authoritative *for the model this Plan implements* before calling a conflict.

| Condition | Severity |
|---|---|
| False premise the Plan leans on | BLOCKER |
| False claim a task would wrongly build on | BLOCKER |
| Divergence breaking a stated safety or security constraint | BLOCKER |
| AC command cannot run as written in the declared environment | BLOCKER |
| Citation of a document section that does not exist or does not say what is claimed | WARNING |
| Silent divergence from a design doc or project rule | WARNING |
| Descriptive drift with no effect on the work (anchor slightly off) | WARNING |
| Cosmetic drift (imprecise count, ordering difference) | INFO |
| Claim not settleable from the workspace | `Unverified` — not a finding |

---

## 4. Q3 — Will executing it deliver the goal?

Needs the Plan only (plus the goal decomposition — zero repo commands). Catches what structural checks cannot: a Plan that passes and still under-delivers.

### 4.1 Goal covered

1. Split `## Goal` into its independently meaningful parts.
2. For each part, find the Task(s) that deliver it.
3. A part with no task is an intention, not a plan.

### 4.2 Decisions delivered

1. For each `D-xx` in Key Decisions, find the task(s) that implement it.
2. Confirm the delivery matches the decision's scope.
3. Scan task text for shrink words: `v1`, `v2`, `simplified`, `static for now`, `hardcoded`, `placeholder`, `basic version`, `minimal`, `NOT wired to`, `NOT connected to`, `stub`, `future enhancement`, `will be wired later`, `skip for now`, `for now`.
4. Adjudicate each hit, two questions in order:
   - Does the shrink contradict the Goal or a `D-xx`? If not → not a finding.
   - Does a `D-xx` or scope statement **sanction** the shrink? If yes → not a finding. Plans legitimately deliver phased work when the Plan says so.

### 4.3 ACs that can fail

For each AC, ask: if the feature were broken, would this check catch it?

- An AC that asserts existence where behavior is the claim ("the file exists") proves nothing about the behavior.
- An AC that restates the change ("the function is added") proves nothing at all.
- An AC that passes whether or not the feature works is decoration.

The strongest AC names a failure it would detect. Weak falsifiability is WARNING, not BLOCKER — `plan check` owns command presence; you own whether the command proves anything.

### 4.4 Handoff possible

For each Task, ask whether whoever implements it, knowing only the Plan and the declared `Pre-read`, could start work:

- Are the interfaces, types, and outputs of earlier Tasks **named**, not implied ("uses the response shape from Task 2" is weak; "calls `parseConfig(path)` returning a `ParsedConfig`" is ready)?
- Is the Task's own output defined well enough that the *next* Task can consume it?
- Does `Pre-read` list the right files — and do those files exist?

Resist flagging Tasks that are one step of an obvious sequence. The bar is "could a competent implementer proceed". Flag only where the missing information would cause a wrong turn — an interface that must be guessed, an output shape that is ambiguous, or a dependency the implementer cannot discover.

| Condition | Severity |
|---|---|
| Goal part with no covering task | BLOCKER |
| Decision reduced without the Plan acknowledging it | BLOCKER |
| Shrink language sanctioned by a `D-xx` or scope statement | not a finding |
| AC that cannot fail | WARNING |
| Task not startable from Plan + declared `Pre-read` alone | WARNING |
| `Pre-read` names a file that does not exist | WARNING |

**Why a silent decision shrink is BLOCKER**: a reduced deliverable that reaches `verify` has already spent the execution budget. Catching it before execution is the whole value of this review. Phased delivery is fine when the Plan *says* it is a phase — adjust the Goal or split an explicit follow-up. A silent shrink is not.

---

## 5. Severity calibration

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
| Plan has 12 tasks, all mutually dependent; the Plan states it will not split and why | no finding (size is not a defect) |
| Plan declares a file as newly created, but the file already exists | WARNING (stale premise; the implementer will improvise) |
| Task references a function no other task creates | BLOCKER |
| Task registers 5 error codes, a later task uses a 6th | BLOCKER |
| Anchor `file.ts:964` lands at 967 on the described function | no finding |
| Anchor `file.ts:964` lands in an unrelated block; the function is at 1200 | WARNING |
| Plan contradicts a design doc it also cites, without acknowledgement | WARNING |
| Plan contradicts a design doc and states "this supersedes §X of doc Y" | no finding |
| AC is `rg -c 'pattern' file ≥ 1` for a behavior the file could contain while the feature is broken | WARNING (weak falsifiability) |
| Reduction to "v1" where `D-04` says "start with static data, dynamic later — this Plan delivers the static layer" | no finding |
| Reduction to "v1" where `D-04` says "config displays calculated costs" | BLOCKER |
| A concern you could not check for lack of a sandbox | `Unverified`, never a finding |

---

## 6. Worked Examples

### Example A — Symbol with no producer (Q1)

**Plan shape**: Task 2 creates an error-code module and registers five codes: `A_MISSING`, `A_INVALID`, `S_MISSING`, `S_INVALID`, `C_UNRESOLVED`. Task 4 describes a failure branch "fail fast with `TEMPLATE_MISSING`".

**Check**: list the registered set, list every upper-snake name used across the Plan, diff.

```yaml
check: Q1_symbols
severity: blocker
plan_location: "{plan}.md:{line of Task 4 branch}"
reality: "registered set at {plan}.md:{line of Task 2 statement}; TEMPLATE_MISSING absent"
impact: "Task 4's failure branch cannot be implemented as written; the implementer will improvise a second registration site or reuse a wrong code"
fix: "add TEMPLATE_MISSING to the registration task, or reference an existing code"
```

### Example B — File drift on both sides (Q1)

**Plan shape**: Task 2 `Changes` includes "step 3: register five error codes in `src/lib/errors.ts`". Task 3 includes "step 2: register `SYNC_APPLY_FAILED` in `src/lib/errors.ts`". The `Affected Files` table has rows for ten components; `src/lib/errors.ts` is not among them.

```yaml
check: Q1_files
severity: warning
plan_location: "{plan}.md:{line of Task 2 step 3}"
reality: "Affected Files table at {plan}.md:{line range} lists no row for src/lib/errors.ts"
impact: "the file is edited by two tasks but sits outside the Plan's declared file scope"
fix: "add an Affected Files row naming the file and the tasks that touch it"
```

### Example C — False premise (Q2)

**Plan shape**: Technical Context asserts "the legacy schema path is gone from the ontology, so initialization necessarily fails". Task 4 removes the reader for that path, and AC#7 asserts a repo-wide search returns zero hits for the old identifiers.

**Check**: at the stated revision, search the repo for the old path and for callers of the reader.

```yaml
check: Q2_facts
severity: blocker
plan_location: "{plan}.md:{line of the premise}"
reality: "{file}:{line} still imports and calls the old reader; the Plan's search list does not include that call site"
revision: "{commit}"
impact: "the premise 'no other callers exist' is false; the repo-wide AC cannot pass because an unnamed call site remains"
fix: "name the remaining call site in a task's scope, or add it to the removal task"
```

Note how the AC itself reveals the defect once the premise is checked: the Plan's own acceptance criterion would fail at verify time, after the whole execution budget was spent. That is exactly what Q2 exists to prevent.

### Example D — Correctly NOT reporting a finding

**Plan shape**: six tasks, 11 `Affected Files` rows, four waves; a `D-10` states "single-Plan delivery, not split by task count; tasks are mutually dependent; context budget is managed per task".

**Correct handling**: no finding on size, task count, or file count. `D-10` is the author's explicit, justified decision. Report under Positive Findings if useful ("single-plan decision is explicit and its rationale is stated"). If the review form tempts you to flag "6 tasks exceeds the recommended 2–3", that form is gone — it does not exist here.

### Example E — Unowned acceptance criterion (Q1)

**Plan shape**: 13 Agent Verification ACs. Six tasks declare `Verification Intent`; the referenced set covers ACs 1–6, 8, 10, 12, 13. ACs 7, 9, 11 are referenced by no task; only AC#10 carries an explicit "(cross-task)" marker.

```yaml
check: Q1_acs
severity: warning
plan_location: "{plan}.md:{line range of ACs 7,9,11}"
reality: "no Verification Intent references these; only AC#10 is marked cross-task"
impact: "three acceptance criteria have no owner, so nothing in the execution plan is responsible for proving them"
fix: "assign each AC to a task's Verification Intent, or mark it cross-task explicitly"
```

### Example F — AC that cannot fail (Q3)

**Plan shape**: Task 3's behavior claim is "invalid state input is rejected cleanly". Its AC reads `test -e src/lib/state.ts` — existence of the file, not the behavior.

```yaml
check: Q3_acs
severity: warning
plan_location: "{plan}.md:{line of the AC}"
reality: "the AC asserts file existence; a broken rejection path changes nothing about the file's existence"
impact: "the claimed behavior is never actually verified; a regression passes silently"
fix: "replace with a command that exercises the rejection path and asserts the error, e.g. run the script with a bad state and check the exit code"
```