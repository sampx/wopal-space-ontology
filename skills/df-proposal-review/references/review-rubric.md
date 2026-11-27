# Proposal Review Rubric — Procedures by Mode

Detail behind the questions, per mode. Load this when a question needs its full method, the command cookbook, or a worked example.

**Purpose reminder**: this review answers "will this work if executed or adopted as written". Form is owned elsewhere — `flow.sh plan check` for dev-flow Plans, `wopal space evo check` for evolution proposals, `dev-proposal/scripts/verify-proposals.py` for business Proposals, `scripts/verify-docset.py` for the doc-master document set.

Contents:
1. [Reading the artifact](#1-reading-the-artifact)
2. [Plan mode — Q1](#2-plan-mode--q1-do-the-parts-fit-together)
3. [Plan mode — Q2](#3-plan-mode--q2-are-its-statements-about-the-repo-true)
4. [Plan mode — Q3](#4-plan-mode--q3-will-executing-it-deliver-the-goal)
5. [Plan mode — Q4 Lean](#5-plan-mode--q4-lean)
6. [Business Proposal mode — P1–P5](#6-business-proposal-mode--p1p5)
7. [Document mode — D1–D4](#7-document-mode--d1d4)
8. [Severity calibration](#8-severity-calibration)
9. [Worked examples](#9-worked-examples)

---

## 1. Reading the artifact

Read the whole artifact once, with line numbers, before running any command. Build the three lists as you read:

1. **Facts** — every concrete claim about the repo, the system, or other documents (counts, paths, line anchors, doc sections, IDs, commands, flags).
2. **Symbols** — Plan mode: every code-like backticked name, with the Task that uses it and the Task that creates it. Document mode: every named component, capability, or contract, with where the document gives it an owner.
3. **Files** — every file path mentioned anywhere, with where it was mentioned.

Then run commands. Do not alternate between reading and verifying — each return costs more than the command saved. Keep the artifact's declared execution mode in mind from the start (sequential waves tolerate same-wave file overlap; claimed parallel waves require file-disjointness).

---

## 2. Plan mode — Q1: Do the parts fit together?

Start with the artifact, then verify producers provided by existing code, dependencies and interfaces where needed.

### 2.1 Expected file scope (no audit)

The `## Affected Files` table is the expected footprint, not a contract; the implementing agent backfills actuals at Done. **Do not diff task-level file lists against the table.** Two things remain checkable:

1. **Stale operation premises**: a row declaring "create" for a file that exists, or "delete" for a file that is absent — the implementer hits a wrong turn on a false premise (WARNING).
2. **Parallel overlap**: files overlapping between waves under declared parallel execution (BLOCKER). Under declared sequential layers, overlap is the Plan's design — not a finding.

**Common false positive**: rows naming artifacts the code creates at runtime, not files the Plan writes — a generated artifact needs no producer.

### 2.2 Symbols have producers

1. Walk the Tasks in order. Collect code-like backticked names a task *uses*: function calls, upper-snake constants, exported types, fixtures, CLI flags, env vars.
2. Collect the names each task *declares*: "register X", "create Y", "export Z".
3. Match each used name to an existing source or producer Task: spelling matches, and any required new producer Task precedes the consumer.
4. When a task registers a *set* of names, verify every name used elsewhere appears in that set.

| Condition | Severity |
|---|---|
| New symbol with neither an existing source nor a producer Task | BLOCKER |
| Producer name differs from the consumer's expected name | BLOCKER |
| Producer sits in a later wave than its consumer | BLOCKER |
| Producer exists but its export/registration site is unstated and matters to wiring | WARNING |

### 2.3 Every AC has an owner, in the right bucket

1. List every AC in `### Agent Verification`.
2. Collect the referenced set from every Task's `**Verification Intent**`.
3. Diff them. Unreferenced ACs have no owner. Cross-task ACs must be marked as such.
4. Check the bucket: tests, lint, typecheck, scriptable assertions belong in Agent Verification; only human observation belongs in User Validation.

**Plain-text AC before coding**: before implementation starts, an AC may state the pass/fail rule in plain text when the exact test command will be filled in during the RED stage. Never flag a plain-text rule just for lacking a shell command yet; flag only rules that cannot catch a broken implementation.

### 2.4 Order matches dependencies

- Declared wave/dependency order must match the dependency table: no consumer before its producer.
- Declared execution mode must match reality: sequential waves tolerate same-wave overlap; claimed parallel waves require disjoint files.
- A required artifact already exists, has a viable acquisition path, or is produced by an earlier Task.

---

## 3. Plan mode — Q2: Are its statements about the repo true?

The repository is evidence of current facts; current user authorization governs the target. Verify material factual claims, not the old present-state DESIGN as a new Proposal target.

### 3.1 Command cookbook

| Claim class | Command | Notes |
|---|---|---|
| Counts ("36 capabilities") | count them in the source of truth | the count motivates work — get it right |
| Paths / filenames | `test -e`, `ls`, `rg --files` | |
| Line anchors ("`file.ts:619-669`") | `sed -n 'Np' file` at the target revision | see anchor-drift judgement |
| Document sections cited | `rg -n '^#{2,3} Section' doc.md` | the Plan's authority citation |
| Decision / issue IDs | `rg -n` the ID in its source of truth | |
| Commands and flags named in ACs | check the command exists and accepts the arguments | |
| Menu of "new" vs existing files | `test -e` | |

**Content-snapshot discipline**: state which content snapshot every check ran against — current working tree (which may include uncommitted changes), Base Commit, worktree HEAD, or integration HEAD. When the review target lives in the current working tree, check that current content by default; use a declared worktree HEAD when the review target is specifically that committed worktree state.

Content-snapshot discipline says **what was reviewed**; it is not a Git-hygiene gate. When a design / Plan / proposal is uncommitted, unpushed, unmerged, or untracked and the review target is the current working-tree content, **those Git states are never findings**. Do not infer a future worktree failure merely because an older HEAD, Base Commit, or Integration Branch does not yet contain the current change; that is a later dev-flow execution gate, not proposal quality.

### 3.2 Anchor-drift judgement

Line anchors locate code; they are not contracts. Probe the anchor and read a few lines around it:

- Lands on the described construct, or nearby with the construct clearly identifiable → pass
- Lands on unrelated code, or the construct is elsewhere → WARNING
- Construct does not exist at the stated revision → BLOCKER if the premise leans on it, else WARNING

### 3.3 Agreement with authorities

1. From Technical Context and `Pre-read`, list the design docs, rule files, and interfaces the artifact names as its basis.
2. Confirm the cited sections exist and say what is claimed.
3. For each decision, find the governing statement in the authorities and compare.
4. Classify divergence: **Acknowledged** (stated and justified → not a finding), **Deferred** (explicitly out of scope with a reason → not a finding), **Silent** (→ finding).

For Proposal-driven Plans, the current authorized Proposal governs the target; present-state DESIGN describes the system before the change. An authorized new target differing from current DESIGN is expected. Legacy Plans and Issues retain their contract. Plans cannot autonomously override genuine safety/engineering rules; necessary rule maintenance follows implementation and DESIGN sync.

---

## 4. Plan mode — Q3: Will executing it deliver the goal?

Trace current authorized goals through real entry points, call paths, failures and acceptance; do not trust the artifact’s own coverage claims alone.

### 4.1 Goal covered

Split `## Goal` into independently meaningful parts; find the Task(s) delivering each. A part with no task is an intention, not a plan (BLOCKER).

### 4.2 Decisions delivered

1. For each `D-xx`, find the task(s) implementing it.
2. Confirm the delivery matches the decision's scope.
3. Scan task text for shrink words: `v1`, `simplified`, `static for now`, `hardcoded`, `placeholder`, `basic version`, `minimal`, `stub`, `not wired to`, `for now`.
4. Adjudicate, two questions in order: does the shrink contradict the Goal or a `D-xx`? Does a `D-xx` or scope statement **sanction** it? A sanctioned shrink is phased delivery — not a finding.

**Why a silent shrink is BLOCKER**: a reduced deliverable that reaches `verify` has already spent the execution budget. Phased delivery is fine when the artifact *says* it is a phase.

### 4.3 ACs that can fail

For each AC: if the feature were broken, would this check catch it? An AC asserting file existence where behavior is the claim proves nothing; one that merely repeats the task title proves less. A critical AC that cannot catch a broken implementation is BLOCKER; noncritical verification gaps are WARNING — `plan check` checks whether a command is filled in; you check whether the AC actually proves anything.

### 4.4 Handoff possible

For each Task: knowing only the artifact and the declared `Pre-read`, could a competent implementer start?

- Interfaces, types, and outputs of earlier Tasks are **named**, not implied ("uses the shape from Task 2" is weak; "calls `parseConfig(path)` returning a `ParsedConfig`" is ready).
- The Task's own output is defined well enough for the next Task to consume.
- `Pre-read` files exist.

Flag only where the missing information would cause a wrong turn.

---

## 5. Plan mode — Q4: Lean

For every new item the Plan creates — module, class, interface, config surface, dependency, extension point — climb the ladder. Stop at the first rung that holds; the item must land at that rung.

### The ladder

1. **Does it need to exist at all?** One-implementation interfaces, one-product factories, config for values that never change, extension points with no consumer, layers with one caller. Speculative need = cut it, name the trigger that would justify it later.
2. **Already in this repo?** The Plan builds what a few files over already ships. Probe with `rg <pattern>` before flagging — the finding must name the existing implementation (`file:line`), or it is at most Info.
3. **Stdlib does it?** The Plan adds a dependency whose job the standard library already does. Name the stdlib function in the finding.
4. **Native platform covers it?** Code or a dependency doing what the platform ships (CSS over a JS polyfill, a DB constraint over app-side checks, built-in CLI flags over hand-rolled parsing).
5. **Shortest direct form?** The same logic a shorter, more direct form delivers. Show the shorter form in the finding.
6. **Cleans up what it replaces?** When the Plan replaces an existing module, helper, or dependency, check whether a task deletes the obsolete code, its old tests, and the unused dependency entry. Leaving replaced code behind turns it into dead code immediately.

### Dependency admission

Any new third-party dependency in the Plan needs a stated reason the ladder cannot satisfy: why stdlib, native platform, and every already-installed dependency fall short. A Plan that adds a dependency with no reason → WARNING. A Plan adding a dependency while rungs 3–4 hold → WARNING, and the finding names what it should have used.

### Severity

| Condition | Severity |
|---|---|
| Speculative abstraction or extension point | WARNING |
| Re-implementation of existing repo infrastructure (named `file:line`) | WARNING |
| New dependency while stdlib / installed packages cover it | WARNING |
| Replacement that leaves the old code, old tests, or old dependency behind | WARNING |
| Same logic in a shorter form | INFO |
| Style or naming preference | not a finding |

Leanness alone never blocks; report evidenced needless cost as Warning and technical preferences only as useful suggestions. No mandatory line or dependency reduction estimates.

### Evolution-proposal capability gate

On top of Q1–Q4, an ontology evolution proposal's deliverable must satisfy the platform's own capability standards:

- frontmatter `name` + `description`; triggering conditions live in the description
- body = workflow, output, notes; long content offloaded to `references/`
- scripts/ holds only deterministic, reusable logic
- no invented structure beyond the platform's asset anatomy

A proposal explicitly requiring a deliverable that violates a mandatory standard → BLOCKER. Unspecified implementation details are not findings. This gate checks the stated deliverable; implementation review checks landed files.

---

## 6. Business Proposal mode — P1–P5

A business Proposal records a decision, so the review is about the decision's soundness, not its prose. Read the proposal once, then read the `implemented/` records it touches before forming any verdict: a supersession claim can only be judged against the record being superseded.

### 6.1 P1 — Is the decision actually decided?

Locate the sentence that chooses. Then test it two ways:

1. **State the choice from memory.** Close the proposal. Can you say what was chosen and what was excluded? If not, the reader will invent the answer during implementation.
2. **Test the boundary.** Does the proposal say what it will not do? An empty boundary is not a scope; it is a blank cheque.

Approval trail:

| Signal | Reading |
|---|---|
| `Status: approved`, plus `Approved` with a date and a person | plausible authorization; still confirm the conversation, never the file alone |
| `Authorized scope` names concrete inclusions **and** exclusions | usable scope |
| `Authorized scope` says "everything", repeats the title, or names a topic with no edge | scope absent → WARNING, or BLOCKER when a Task depends on the missing edge |
| Substantive adjustment after approval lacks user authorization | unapproved new scope → BLOCKER; explicit user authorization not yet integrated into current Proposal → WARNING |
| `Status: approved` with no approval block | the verifier catches the shape; report it as unauthorized content, not a formatting nit |

**Do not accept a valid format as proof of approval.** The verifier checks that the fields exist and read correctly. Only the conversation establishes that a human granted them. When the authorization evidence is unavailable, disclose it in other notes rather than assuming either way. Before acceptance, integrate explicit user-authorized adjustments under dev-proposal without duplicate approval.

### 6.2 P2 — Do the stated facts hold?

Same command cookbook and revision discipline as §3. A proposal usually makes fewer, heavier claims than a Plan: file paths, current defaults, error strings, counts, and "today the system does X". Each one is a premise for the decision, so a false one is expensive.

### 6.3 P3 — Are the alternatives real?

For each alternative, ask whether a reasonable author would genuinely have weighed it, and whether the stated reason actually defeats it. Then check the supersession ledger:

| Situation | Verdict |
|---|---|
| New proposal changes a default/boundary/decision and names the superseded and surviving parts of the older `implemented/` record, with a relative link | fine |
| `implemented/` decision edited in place, no new proposal | BLOCKER — a historical decision was rewritten |
| Former `implemented/` proposal moved back to `proposed/` | BLOCKER — the transaction record is gone |
| Old `implemented/` record edited before the new scope is fully delivered | BLOCKER — unshipped change presented as current fact |
| Full replacement with the old record left active and contradictory | BLOCKER |
| Full replacement with the old rationale absorbed, or the old record archived | fine |
| Paths, names, or implementation details synced, decision unchanged | fine — required behavior |

The mechanical part (does the file's `Status` match its directory, is the skeleton right, do links resolve) belongs to `verify-proposals.py`. Do not repeat it; use its output as the starting fact base.

### 6.4 P4 — Can it be falsified?

Apply the "if it were broken, would this catch it" test to every acceptance criterion. Then check the risk section: verify the impact, necessary controls and observation for material risks; do not demand fabricated numeric thresholds or revisit signals for every risk.

Partial-delivery discipline: a proposal in `proposed/` with `Status: approved` may be unimplemented, partially delivered or awaiting acceptance. The finding is the opposite — claiming the approved scope is complete when the evidence shows a subset, or presenting a partial scope in the wording of full delivery.

### 6.5 P5 — Is this the lean decision?

Same ladder as §5, applied to the decision:

1. Does the decision need to exist — is current behavior actually a problem?
2. Is it already settled by an `implemented/` record or an active rule? Name the file.
3. Is a smaller decision enough?
4. Does it clean up the decision it replaces?

### 6.6 Reviewing the Plan derived from an approved Proposal

The decision is closed; this review is about execution. Check:

- **Scope fidelity** — every Task maps to a slice of the authorized scope, and no Task exceeds it.
- **Coverage** — every part of the authorized scope has a Task; nothing is quietly dropped.
- **Ordering and handoff** — normal Plan-mode Q1/Q3 concerns, unchanged.
- **No second approval** — a Task that merely chooses a different internal approach, uses another library, or splits the work differently is not a finding, as long as the approved behavior and boundary hold.

A Task outside the approved scope → BLOCKER (unapproved work). A silently dropped part of the scope, presented as complete → BLOCKER. If the Plan shows the approved scope cannot be delivered as written, raise a Requirement Question for the user; do not redesign during review.

---

## 7. Document mode — D1–D4

No tasks to schedule, so the questions reshape. Q4's name and severity cap carry over.

### D1 — Does the document cohere?

Read for: contradictions between sections; terms used before definition or used two ways; components, states, or contracts the document introduces without an owner; sections that depend on context the document never provides.

**Structure conformance**: when the document belongs to the `dev-doc-master` set, structural rules (header zones, naming, field vocabulary, sub-DESIGN discovery) are governed by `dev-doc-master/references/consistency.md`. The mechanical part is already scanned by its quality gate (`scripts/verify-docset.py`) — run it when available and spend your review on what the script cannot see: whether the *content* honors the structure (a link pointing at a document that no longer governs this one, a companion misclassified as a sub-design).

**No header sub-DESIGN index.** Main DESIGNs — product and project alike — deliberately omit a `Sub-DESIGNs` enumeration. Sub-documents are discovered by `DESIGN-*.md` filename plus their `Parent` header link, and the main document links them from its body, usually the `## Module Architecture` map. Reporting "the main DESIGN header lists no sub-DESIGNs" is a false positive. The real defect is the opposite: a sub-DESIGN reachable only from the header, which `verify-docset.py` reports as an orphan.

| Condition | Severity |
|---|---|
| Internal contradiction on a load-bearing statement | BLOCKER |
| Undefined term with real ambiguity | WARNING |
| Component or state introduced without an owner | WARNING |
| Applicable DESIGN or rule fails mandatory structure/quality gate | BLOCKER; reuse actual results and avoid duplicate findings |

### D2 — Are its statements about reality true?

Same mechanical probes as Q2 (command cookbook, revision discipline, anchor drift). Additional checks in document mode:

- **Sibling-document conflicts**: two documents describing the same system differently. Apply the authority rule from 3.3 first; a silent divergence is a finding.
- **Present-state vs product intent** (doc-master set): the line depends on the document kind.
  - *Project and module present-state DESIGNs* (`DESIGN.md`, `DESIGN-<module>.md`) describe shipped, verified reality. "deprecated", "legacy", "moved from", "no longer", "已废弃" narration is a finding, and so is unbuilt proposal content presented as a live capability.
  - *Product PRDs and product DESIGNs* own product intent and may plan ahead of implementation. Forward-looking content is legitimate. What remains a finding is process narration — how the plan changed, what was tried and dropped — and any claim that something ships when it does not.
  - Name the document kind in the finding. Applying the present-state rule to a product DESIGN, or tolerating history narration in a module DESIGN, is a mis-scoped finding.

| Condition | Severity |
|---|---|
| Claim the code contradicts on a load-bearing path | BLOCKER |
| Stale fact in present-state DESIGN or conflict with applicable rules | BLOCKER; noncritical Proposal fact drift is graded by impact |
| Module DESIGN violates governing present-state writing requirements | BLOCKER |
| Cosmetic drift | INFO |

### D3 — Is the goal sound?

- **Decidable goal**: an observer can tell whether the goal was met. "Make the system more robust" is not decidable; "submits with zero schema errors" is.
- **Stated boundary**: the document says what it does not cover, or points where the boundary lives. A missing boundary is a blank check the implementer will cash.
- **Requirement gaps**: a user problem stated with no requirement answering it. The consumer of this document fills the hole silently, with their own guess.
- **Silent decisions**: choices a reader must make are stated or flagged, not buried in prose.

| Condition | Severity |
|---|---|
| Goal that cannot be judged met or unmet | BLOCKER |
| Missing boundary on a load-bearing area | WARNING |
| Requirement gap (problem without an answer) | WARNING |
| Silent decision the reader must make | WARNING |

### D4 — Is it lean?

Every feature, section, and abstraction earns its place against the goal:

- features answering no stated problem
- extension points for phases that may never come
- boilerplate structure the template suggested but the content does not need
- configuration surfaces with no reader

Template conformance is not a goal — structure serves the document's content, not the other way around. Pure leanness follows Q4; violations of mandatory DESIGN or rule quality standards → BLOCKER. No mandatory reduction counts.

### Writing style gate (all modes)

The artifact's language is part of its quality: plain, concrete, one idea per sentence, affirmative over negative, ownership over exclusion. This gate flags:

- jargon or invented abstractions a reader must decode twice
- machine-sounding prose (nominalization stacks, passive voice chains)
- negative definitions ("X does not do Y") where ownership ("Y is owned by Z") says it better

Severity: material writing defects impairing proposal comprehension → **WARNING**; isolated phrasing → **INFO**. A reviewed present-state DESIGN or rule violating governing skill quality requirements → **BLOCKER**. For skill deliverables in evolution proposals, the bar is explicit: description and body must be plain and precise enough that an agent knows what to do after one read.

---

## 8. Severity calibration

Four classes, defined by what the reader should do:

| Class | Meaning | Test to apply |
|---|---|---|
| **BLOCKER** | Wrong design, missing key goal/acceptance, unauthorized planned scope, false evidence, historical tampering, present-state DESIGN/rule inconsistency or mandatory quality violation | Apply SKILL.md to the actual defect |
| **WARNING** | Correct delivery is feasible, but noncritical ambiguity, verification gaps or evidenced unnecessary cost remain | Apply SKILL.md; real security defects and mandatory quality violations do not downgrade |
| **INFO** | Improvement worth knowing, no action required | "Would a reasonable author shrug?" |
| **Unverified** | Claim could not be settled from the workspace | "Could I not check this?" |

Blockers and Warnings require concrete evidence and impact; a mandatory document/rule quality violation is itself blocking evidence and needs no invented runtime failure. “It is not ready yet,” “it is not committed yet,” or “the final environment is not provisioned yet” is insufficient by itself.

Deliberately absent: **size/count thresholds**. Task count, file count, wave count, document length are never defects. Context budget is managed per task; a large cohesive artifact is normal.

### Calibration drills

| Situation | Correct verdict |
|---|---|
| Task references a nonexistent function with no viable producer | BLOCKER (Q1) |
| Task registers 5 error codes, a later task uses a 6th | BLOCKER (Q1) |
| Anchor `file.ts:964` lands at 967 on the described function | no finding |
| A DESIGN / Plan change is uncommitted, unpushed, or unmerged during review, while current working-tree content is available | no finding; review the current content |
| Current DESIGN changes are not in HEAD, so a future approve-created worktree would not see them yet | no finding; later lifecycle execution gate, not a proposal defect |
| An AC requires final validation on a real Linux host and explicitly remains unchecked without that evidence; the current development machine has no Linux host | no finding (Execution dependency) |
| Plan contradicts a key behavior or authorization of the current approved Proposal | BLOCKER (pre-implementation target/scope error) |
| Authorized new Proposal target differs from existing present-state DESIGN | no finding; synchronize artifacts after implementation |
| Reduction to "v1" where `D-04` sanctions the static layer | no finding (Q3) |
| Reduction to "v1" where `D-04` says "config displays calculated costs" | BLOCKER (Q3) |
| Plan adds `fast-xml-parser` while stdlib ships no XML parser and none is installed | no finding (Q4 — rung 5 legitimately holds) |
| Plan adds a new utility module duplicating `src/lib/hash.ts:12` | WARNING (Q4 — rung 2) |
| Plan creates `AbstractStore` with a single `FileStore` implementation | WARNING (Q4 — rung 1) |
| Design doc's §2 says the scheduler owns retries; §5 hand-wires a retry loop in the worker | BLOCKER (D1 — load-bearing contradiction) |
| Module DESIGN violates governing present-state writing requirements | BLOCKER (D2 — document quality) |
| Product DESIGN describes a planned capability as future work, clearly marked as not yet shipped | no finding (product intent) |
| Main DESIGN has no `Sub-DESIGNs` header, sub-DESIGNs link back via `Parent` and are reachable from the module map | no finding (correct structure) |
| Sub-DESIGN exists on disk but only the header names it | BLOCKER (D1 — mandatory structure gate) |
| Business Proposal changes a shipped default and opens a new `proposed/` record naming the superseded decision | no finding (correct partial supersession) |
| Business Proposal edits an `implemented/` record in place to change a default | BLOCKER (P3 — decision rewritten) |
| Business Proposal claims the approved scope is complete while a Task-level AC shows a subset | BLOCKER (P4 — partial presented as complete) |
| Plan derived from an approved Proposal splits work differently than the Proposal sketched, same behavior and boundary | no finding (no second design approval) |
| Plan derived from an approved Proposal includes a Task outside the authorized scope | BLOCKER (scope exceedance) |
| Business Proposal has `Status: approved` and a well-formed approval block; the conversation granting it was not available to the reviewer | `Unverified`, not a finding |
| Design doc's goal is "improve developer experience" with no observable outcome | BLOCKER (D3 — undecidable goal) |
| Proposal explicitly requires mandatory triggers buried in the skill body rather than description | BLOCKER (mandatory capability standard) |
| Proposal body uses "leverage synergistic alignment layers" | WARNING (style gate) |
| A concern you could not check for lack of a sandbox | `Unverified`, never a finding |

---

## 9. Worked examples

### Example A — Symbol with no producer (Q1, Plan mode)

Task 2 registers five error codes: `A_MISSING`, `A_INVALID`, `S_MISSING`, `S_INVALID`, `C_UNRESOLVED`. Task 4 describes a failure branch "fail fast with `TEMPLATE_MISSING`".

```yaml
check: Q1_symbols
severity: blocker
location: "{plan}.md:{line of Task 4 branch}"
reality: "registered set at {plan}.md:{line of Task 2}; TEMPLATE_MISSING absent"
impact: "Task 4's failure branch cannot be implemented as written; the implementer improvises a second registration site"
fix: "add TEMPLATE_MISSING to the registration task, or reference an existing code"
```

### Example B — False premise (Q2, Plan mode)

Technical Context asserts "the legacy schema path is gone, so initialization always fails". Task 4 removes the reader for that path; AC#7 asserts a repo-wide search returns zero hits.

At the stated revision, the reader still has one live call site the Plan never names.

```yaml
check: Q2_facts
severity: blocker
location: "{plan}.md:{line of the premise}"
reality: "{file}:{line} still imports and calls the old reader; the search list omits that call site"
revision: "{commit}"
impact: "the premise is false; the repo-wide AC cannot pass — discovered at verify time, after the budget is spent"
fix: "name the remaining call site in a task's scope, or add it to the removal task"
```

### Example C — Re-invented infrastructure (Q4, Plan mode)

Task 3 creates `src/lib/retry.ts` with a backoff-retry helper. `rg 'retry|backoff' src/` shows `src/lib/http.ts:88` already ships one, used by four call sites.

```yaml
check: Q4_ladder
severity: warning
location: "{plan}.md:{line of Task 3}"
reality: "src/lib/http.ts:88 already provides backoff retry; 4 existing call sites"
impact: "two retry implementations diverge on edge cases; the shorter diff reuses the existing helper"
fix: "reuse the existing helper; delete Task 3, or reduce it to extending the existing one"
```

### Example D — Undecidable goal (D3, Document mode)

A product DESIGN's Goal reads: "improve the developer experience of the CLI".

```yaml
check: D3_goal
severity: blocker
location: "{doc}.md:{line of Goal}"
reality: "no observable outcome anywhere in the document; an observer cannot tell whether this was met"
impact: "every implementation choice can claim success; the goal cannot fail, so it governs nothing"
fix: "state the outcome the change produces, e.g. 'first-run setup completes in under one minute with zero manual edits'"
```

### Example E — Silent rewrite of a shipped decision (P3, Business Proposal mode)

A proposal sits in `proposed/architecture/` with `Status: proposed`. It changes the loader's default-merge behaviour. Reading it, you notice the linked `implemented/architecture/2026-10-02-single-loader.md` has been edited in place: its `## Decision` now describes the new merge ownership, while its `Status` still reads `implemented` and its date is unchanged.

```yaml
check: P3_supersession
severity: blocker
location: "{proposal}.md:{line of the change}"
reality: "implemented/architecture/2026-10-02-single-loader.md:{line}: the Decision text is the new behaviour, but the file is still Status: implemented and predates the proposal"
impact: "a reader of the implemented record believes the new behaviour already shipped; the historical decision is unrecoverable from the record"
fix: "revert the in-place edit; state the supersession in the new proposed/ record, and cross-link both ways when the new scope is fully delivered"
```

### Example F — Partial delivery presented as complete (P4)

A proposal's `## Risks` says two of five consumer modules will be migrated first. Its `## Proposal` says "all consumers read the schema defaults". The `## Consequences`/delivery evidence lists only two modules migrated.

```yaml
check: P4_falsifiability
severity: blocker
location: "{proposal}.md:{line of the full-scope claim}"
reality: "{proposal}.md:{line of the risks note}; delivery evidence names two of five modules"
impact: "if moved to implemented/ on this evidence, the record claims a migration that did not happen; downstream readers trust a false premise"
fix: "keep it in proposed/ with Status: approved until every consumer is migrated, or narrow the proposal's stated scope with user confirmation"
```

### Example G — Correctly NOT reporting a finding (Plan derived from an approved Proposal)

An approved Proposal authorizes "scheduled CSV export for two reporting tables, `Delivery: plan`". The derived Plan splits the work into four Tasks, uses a different scheduler library than the Proposal sketched, and adds a lock file the Proposal never mentioned.

**Correct handling**: no finding on the library choice (internal approach) and no finding on the lock file (it protects the approved behaviour). The review checks only that every Task stays inside the two-table scope and that the scope is fully covered. Emit `PASS` with a brief statement of both checks.

### Example H — Correctly NOT reporting a finding (size and dependency admission)

Six tasks, 11 Affected Files rows, four waves; a `D-10` states "single-Plan delivery, not split by task count; tasks are mutually dependent; context budget is managed per task". The Plan also adds a new dependency, with a paragraph naming the stdlib options it considered and why each falls short.

**Correct handling**: no finding on size (size is not a defect), and no finding on the dependency (rung admission was explicitly satisfied). Report both briefly in other notes if useful.
