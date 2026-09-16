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

**Your question is not "is this Plan well-formed" — it is "if the Plan were executed literally, by whoever implements it, would it work, and would it deliver the stated goal".**

## Position: what the script owns vs what you own

`flow.sh plan check` already gates determinate form: field presence, placeholder text, TDD↔Behavior pairing, checkbox shape, AC command presence, User Validation structure, status and Project Path validity. Re-checking any of that is waste and produces noise.

Your scope is **closure**: the things a regex cannot compute — whether the parts of this Plan actually fit together and fit reality.

| The script decides | You decide |
|---|---|
| Fields exist and are shaped right | The parts **reference each other correctly** (every consumer has a producer) |
| A command string is present | The claim behind the command is **true against the real repo** |
| The Plan is internally parseable | The Plan is **consistent with its design docs and project rules** |
| ACs exist | Every AC is **owned by a task**, and the plan is **executable by whoever implements it** |
| — | Executing it **achieves the Goal**, not a shadow of it |

If the Plan is fine, say so quickly and stop. This review is invoked deliberately, not for ceremony.

## Cost discipline

Plan review has a reputation for burning time and returning noise. Guard against both.

- **Read once, then probe.** Read the Plan top to bottom with line numbers. Extract claims into a checklist. Only then run targeted commands — never re-read the Plan repeatedly between probes.
- **Probe, do not survey.** Every check below names the probe pattern that settles it. Prefer `rg`, `sed -n 'Np'`, `test -e`, `git cat-file` over opening files. Do not read source files beyond the specific lines a claim concerns.
- **Never read whole large documents.** To confirm a section exists, `rg -n '^## Section Name' doc.md`. To confirm a line, `sed -n 'Np' file`. That is the entire need.
- **Cap the probing.** Roughly 15–25 targeted commands covers a normal Plan. Multi-module High-complexity plans may need more; a small Plan needs fewer.
- **Say what you did not verify.** An unverified claim is not a defect. List it under `Unverified` and move on. Never convert "I didn't check" into a finding.
- **Do not do the implementer's job.** No designing missing pieces, no writing the fix — point at the gap and state what would close it.

## Input contract

You need: the Plan path, and the workspace root. Everything else you can discover.

- If the prompt carries `review_type: plan`, the Plan path, a Base Commit or reference revision, and a focus list — use them.
- If the prompt omits context, still proceed: read the Plan, resolve the target project from its Metadata (`Project Path`), and state any assumption you had to make in the report.
- **If the Plan has a Worktree** (field present in Metadata), the activity copy of the Plan lives *inside the worktree*, not on the integration branch — read status and checkboxes there. Code probes must respect the declared revision.

## The Six Checks

Run all six. Each closes a specific failure class that survives `plan check`.

---

### C1 — Artifact Closure

**Question**: Do the Plan's file lists agree with each other — Tasks ↔ `Affected Files` — with no gaps in either direction?

**Why**: The `Files` field is what the implementer is allowed to touch; the `Affected Files` table is the plan's scope contract. When they disagree, either work happens off-contract, or declared scope is never delivered.

**Probe**: Build the two sets mechanically, then diff them:
- files named in each Task's `**Changes**` and `**Files**`
- file paths in the `## Affected Files` table
- cross-check each row's declared operation against reality: a row declaring a newly created file that already exists, or a row declaring deletion of a file that is absent

**Severity**:
- File edited by a Task but absent from that Task's `Files` → **WARNING**
- File in a Task's `Files` but absent from `Affected Files` → **WARNING**
- Row in `Affected Files` with no task producing it → **BLOCKER**
- Same-wave file overlap where the Plan claims parallel execution → **BLOCKER**; where the Plan explicitly says waves are dependency layers, not parallel batches → **INFO** (read the Plan's own statement about what waves mean before judging this)

---

### C2 — Symbol Closure

**Question**: Does every symbol a later Task consumes have a producer in an earlier Task — and is that producer actually declared?

**Why**: Cross-task plans fail most often at the seams: a task calls a function, error code, interface, flag, constant, fixture, or env var that no earlier task creates. The plan reads fine; execution hits an undefined symbol.

**Probe**: Extract the identifiers each Task consumes (names in backticks that are code-like: function and method calls, constants in upper snake case, exported types, CLI flags, env vars), then locate the producing declaration. Confirm the exact spelling matches on both sides.

**Severity**:
- Consumed symbol with no declared producer anywhere in the Plan → **BLOCKER**
- Producer declared but with a different name/spelling than the consumer expects → **BLOCKER**
- Symbol produced by a Task in a later wave than its consumer → **BLOCKER**
- Producer exists but the Plan never states where it is registered/exported, and that matters for wiring → **WARNING**

---

### C3 — Fact Verification

**Question**: Are the Plan's factual claims about the repository actually true at the revision it targets?

**Why**: Plans are written against a mental model of the code. When that model is stale, every task built on it inherits the error — and the error surfaces only mid-execution, after context is spent.

**Probe**: Treat every concrete assertion as a claim to be checked. Mechanical claims must be checked mechanically:
- **Counts** ("36 capabilities", "8 skills") → count them in the source of truth
- **Paths / filenames** → `test -e` / `ls`
- **Line anchors** ("`file.ts:619-669`") → `sed -n 'Np' file` at the target revision
- **Document sections cited** → `rg -n '^#{2,3} Section' doc.md`
- **Referenced IDs** (decision markers such as `D-xx`, project gap or issue IDs) → confirm they exist in their source of truth
- **Commands and flags** named in ACs → confirm the command exists and accepts those arguments
- **Existing-vs-new** classifications → confirm files declared as newly created do not already exist, and files declared for deletion do

**Quote the revision you verified against** (Base Commit, worktree HEAD, or integration HEAD). A finding without a revision rots the moment anyone commits.

**Severity**:
- Load-bearing claim that is false — the change is justified *because* of it → **BLOCKER**
- Descriptive drift that does not change the work (anchor off by a few lines in a large file) → **WARNING**
- Cosmetic drift (a count stated loosely, ordering difference with no effect) → **INFO**
- Claim you could not settle from the workspace → `Unverified`, **not** a finding

---

### C4 — Agreement Consistency

**Question**: Does the Plan respect the authoritative documents it sits under — or does it silently diverge from them?

**Why**: A Plan executes against design docs, project rules, and existing conventions. Silent divergence means the deliverable contradicts a contract nobody re-negotiated.

**Probe**:
1. Collect the authorities the Plan names in Technical Context / Pre-read (design docs, `AGENTS.md`, existing interfaces).
2. For each design decision the Plan makes, locate the corresponding statement in those authorities.
3. Where they disagree, decide the class: **updated** (Plan says it changes the doc), **deferred** (Plan explicitly declares it out of scope with a reason), or **silent** — a divergence neither acknowledged nor justified.

**Severity**:
- Silent divergence from a design doc or project rule → **WARNING** (needs explicit adoption: update the doc, defer with reason, or justify the deviation)
- Divergence that would break a stated safety or security constraint → **BLOCKER**
- Divergence where the Plan explicitly acknowledges and justifies it → **not a finding** (that is a decision, not a defect)

---

### C5 — Executability & Handoff

**Question**: Can each Task actually be executed — by whoever implements it, working only from the Plan — and is every AC owned?

**Why**: The Plan is what the implementer receives; whoever executes a Task sees the Plan and the files it names, not the author's unwritten context. A Task that only makes sense with that unwritten context will stall, improvise, or drift.

**Probe**:
- **AC ownership**: every AC in `### Agent Verification` is referenced by at least one Task's `Verification Intent`. Cross-task ACs are marked as such. ACs that no task owns are unverified acceptance criteria.
- **AC placement**: each criterion sits in the right bucket. Anything an agent can verify mechanically (test, lint, typecheck, static check, scriptable behavior) belongs in Agent Verification — if it appears under User Validation, the Plan is pushing automatable work onto the user. Anything needing human observation must not sit in Agent Verification as a bare claim.
- **Handoff readiness**: for each Task, ask whether whoever implements it, knowing only this Plan + declared `Pre-read`, can start. Check that referenced interfaces/types/outputs of earlier tasks are named, not implied.
- **Ordering**: declared dependency order matches the wave/dependency table; no consumer precedes its producer; the declared execution mode (shared worktree sequential, or parallel) matches the file-conflict reality.
- **Runnability**: AC commands can execute in the environment the Plan declares (right project root, right script names, right tooling), and any setup they need is itself a step in the Plan.

**Severity**:
- AC owned by no task → **WARNING** (state which ones; cross-task ACs must be marked)
- AC command cannot run as written in the declared environment → **BLOCKER**
- Automatable verification placed in User Validation → **WARNING** (it will waste the user's time on what an agent should prove)
- Human-observation-only criterion claimed as agent-verifiable → **WARNING**
- Task not startable from Plan + declared Pre-read alone (undefined dependency on author context) → **WARNING**
- Declared order contradicts declared dependencies (consumer before producer) → **BLOCKER**

---

### C6 — Goal Fidelity

**Question**: If this executes as written, does it deliver the Goal — or a reduced version of it?

**Why**: The most expensive failure is a Plan that passes every check and still under-delivers: goal components without tasks, decisions quietly shrunk to "v1", ACs that cannot falsify anything.

**Probe**:
1. Decompose `## Goal` into components; confirm each has covering task(s).
2. For each `D-xx` in Key Decisions, confirm the tasks deliver what the decision states — not a shadow version with reduction language (`v1`, "simplified", "static for now", "NOT wired to", "placeholder", "for now").
3. For each AC, ask what failure it would catch. An AC that passes whether or not the feature works is decoration.

**Severity**:
- Goal component with no covering task → **BLOCKER**
- Decision reduced without the Plan saying so → **BLOCKER** (either deliver it, or split it out explicitly)
- Reduction language that is **sanctioned by the Plan's own decision text** → **not a finding**
- AC that cannot fail (asserts existence rather than behavior, or restates the change) → **WARNING**
- Missing falsifiability where `plan check` already required a command → **WARNING**, not BLOCKER (the script owns command presence; you own whether it proves anything)

---

## Split Assessment (replaces size thresholds)

Plan count thresholds do not exist here, because context budget is managed **per Task**, not per Plan — a large cohesive Plan is normal. Size alone is never a blocker.

Recommend splitting only when the deliverable genuinely decomposes — at least two of:
- Two or more groups of deliverables with **no dependency** between the groups
- Each group could be **verified independently** (its own acceptance story)
- Tasks cannot be handed off cleanly because they share too much in-flight state

A large-but-cohesive Plan is correct. If the Plan itself documents a single-plan decision (e.g. a `D-xx` explaining why it is not split), that call has been made — do not re-litigate it. **Never raise size as a Blocker.**

## False-Positive Calibration

Most review noise comes from flagging things that are not defects. Do not flag:

- **Form** — field shape, formatting, placeholder style, checkbox layout. That is `plan check`'s job and it already passed.
- **Sanctioned decisions** — anything a `D-xx` or an explicit scope statement authorizes. Disagreeing with a decision is not a finding.
- **Product intent** — business logic belongs to the user and the agent orchestrating this work, not to the reviewer. If a requirement looks wrong, put it in `Requirement Questions`, not Blocker/Warning.
- **Preference** — "I would have structured it differently", alternative designs, naming taste, or abstraction opinions.
- **Unverifiable concerns** — "this might not handle X" with no evidence from the Plan or the repo. Either verify it or leave it out.
- **Scope you were not asked to cover** — codebase-wide quality, other projects' debt, existing conventions you were not reviewing.

A finding must cite both sides: the Plan location and the reality that contradicts it. Without that, it is at most Info.

## Completeness Gate

**All six checks must be attempted before any verdict.** At review start, create one TodoWrite item per check and mark them complete as you go — one `in_progress` at a time. Do not emit a verdict while any check is pending.

If you run out of budget, do not fake completion: emit the report with an explicit `UNCOVERED CHECKS` section naming what was not done and why.

## Output Contract

Verdicts are the dev-flow standard — `PASS` / `REVISE` / `BLOCK` — so the report plugs into existing gates.

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
- Reality: `{file}:{line}` / `{command output}` — {why this contradicts the Plan}
- Impact: {how execution fails}
- Fix direction: {what to add or change}

## Warning
{same format as Blocker; Impact may be omitted}

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

**Verdict rule**: any Blocker → `BLOCK`; only Warnings → `REVISE`; no findings → `PASS`. `Unverified` items never change the verdict.

`PASS` requires a short positive section: state what was verified and how, so the reader can trust the verdict rather than take it on faith. A `PASS` with nothing verified is worse than no review.

## Evidence Standard

- Blocker / Warning must carry a locatable citation: Plan line + the reality it conflicts with (file:line, command output, or document line).
- Info may be a single line.
- Claims you could not settle go under `Unverified` — never inflate them into findings, never hide them.

## After the Verdict

- **`REVISE` / `BLOCK`**: the revised Plan must be re-reviewed before it is treated as clean — a fix applied without re-verification is not a fix. Reuse the same review session (reply), so prior findings and their resolutions stay in context; opening a fresh reviewer loses that.
- **`PASS`**: this is an input to whoever requested the review, not an automatic gate. It does not authorize `approve`, it does not replace `plan check`, and it does not change the execution status of a Plan mid-flight.
- **Scope note**: reviewing a Plan does not authorize editing it. Findings go back to the owner.

## Anti-patterns

**Do NOT**:
- Re-run or duplicate `plan check`'s form validation
- Read source files broadly, or read whole design docs — probe them
- Flag size, count, or file-number thresholds
- Re-litigate decisions the Plan explicitly made and justified
- Treat "I would design it differently" as a defect
- Emit a finding without citing both the Plan and the reality
- Do the fixing, designing, or implementing
- Reach a verdict with checks still pending

**DO**:
- Read the Plan once, fully, with line numbers
- Check every concrete claim against the repo at the stated revision
- Follow every cross-task symbol to its producer
- Diff the Plan's own file lists against each other
- Ask what each AC would catch if the feature were broken
- State the revision you verified against, and what you could not verify

## References

Load the rubric when the check needs its detailed procedure, probe cookbook, or a worked example:

- `references/review-rubric.md` — per-check procedures, probe cookbook, severity calibration, worked examples (including real defect shapes to recognize)

## Examples

### Example 1 — Symbol closure (Blocker)

A Plan's Task 4 states a failure branch "fails fast with `TEMPLATE_MISSING`". Task 2 lists the five error codes it registers; the name is not among them. Nothing in the Plan ever declares that code.

```yaml
finding:
  check: C2_symbol_closure
  severity: blocker
  plan_line: "{plan}.md:{line}"
  reality: "error codes registered at {plan}.md:{line}; TEMPLATE_MISSING absent from that list"
  fix: "add the code to the registration task, or reference an existing code"
```

### Example 2 — Fact verification (Blocker, load-bearing)

A Plan's premise is "the schema path no longer exists in the ontology, so initialization always fails". Probing the cited file at the stated revision shows the path is still read by one call site the Plan does not mention — the premise is incomplete, and a task built on it would leave that path live.

```yaml
finding:
  check: C3_fact_verification
  severity: blocker
  plan_line: "{plan}.md:{line}"
  reality: "{file}:{line} still reads the old path"
  revision: "{commit}"
  fix: "name the remaining call site in scope, or remove it in a task"
```

### Example 3 — Not a finding (calibration)

A Plan declares six tasks and states in a decision that it will not split, because the tasks are mutually dependent and context is managed per task. Task count is high.

**Correct handling**: no finding. The decision is explicit and the rationale is sound — size is not a defect, and the single-plan call belongs to the Plan author. Record it as a Positive Finding if useful.
