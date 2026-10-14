# Plan Authoring Guide

A Plan has two kinds of readers: **the human reviewer** (must understand what you want) and **the implementing agent** (must be able to build it).

So a Plan's job is to state three things: **what is wanted (behavior)**, **what counts as done (acceptance)**, and **what must not be touched (contracts and boundaries)**. Which files to change and how to organize code internally are decisions that can only be made well during implementation, against the real code — written into a Plan they become straitjackets and guesses.

One line: **pin the contract surface, open up the implementation surface.**

## A Plan must come from formal design

For project/phase work, use only DESIGN/sub-DESIGN documents with `Status: Active` as design facts before splitting Tasks. Every Task uses **Design Source** to point to the concrete section, decision, or contract it implements; list multiple sources when needed. `N/A` is only for simple work with no project and no design basis.

`Draft` / `Proposed` designs may appear only in Research Findings / References as explicitly unsettled forward-looking material. They never belong in Design Source and must not define Behavior, Key Interfaces, ACs, or implementation targets.

Before approval, fix the Plan when it disagrees with Active DESIGN; if no Active design basis can be found, the Plan is not ready to submit. If the Active DESIGN itself conflicts with the user's goal, do not edit design on your own — ask the user to decide the design target. After approval, substantive changes to either the Plan or design require user confirmation.

## How to define contracts: Key Interfaces

`Technical Context > Key Interfaces` is the external-contract section. **Entry is a red line.**

**What belongs**: interfaces that cross modules, cross projects, or face outward — CLI commands, API endpoints, events, schemas, exported types. **What does not**: module-private functions and internal helper types. Let those in and the section degenerates into another file-by-file manifest — the rigidity returns.

**How precise**: signature + error codes + key semantics (idempotency, versioning, failure behavior). Write them in the project's own language — TS interface, Python type, JSON Schema all work, as code blocks.

**One criterion**: if a downstream consumer could write their calling code and compatibility tests from this section alone, the contract is defined. If not, it isn't finished.

**Binding force**: if implementation reveals that a signature, error code, or key semantic must change, stop and return to the controlling workflow. Continue only if the issue can be resolved inside the existing DESIGN + approved Plan; a Plan or design change requires user confirmation through the controller. Write N/A when the Plan has no external contract.

**Example**:

```typescript
/** Registers a Plan execution. Repeated calls with the same execution ID
 *  return the same result; no double execution. */
interface BeginExecution {
  request:  { executionId: string; planId: string }
  response: { status: 'started' | 'already-running'; revision: string }
  errors:
    | 'APPROVAL_EXPIRED'   // approval no longer valid, re-review needed
    | 'DEPENDENCY_PENDING' // upstream not delivered
}
```

## How to pin outcomes: the two-beat AC

You cannot write future test commands at Plan time (the test files do not exist yet) — that is reality, not a defect. The two-beat scheme pins outcomes by separating the *right to define* from the *right to prove*:

**Beat 1 (at Plan-writing time)**: each AC = behavioral criterion + pass standard. Write "what observable behavior the system shows, and what you see when it passes". Criterion-style entries are legal — no guessing future file names.

There is exactly one standard for a good beat-1 entry: **can this AC catch a bad implementation?** Ask yourself: if the agent cuts corners or gets it wrong, will this criterion fail? An AC that passes no matter what ("feature works", "build passes") is decoration — beyond submit validation, df-proposal-review watches for these too.

**Beat 2 (during implementation and controller acceptance)**: the implementer determines the real command for each AC during RED/Verify and reports the command and result to the controller; after the Task passes controller acceptance, the controller **writes it back into the Plan in place**. The implementer does not edit the Plan.

**complete hard gate**: the script enforces it — a checked AC must carry a real command; a criterion-style AC cannot pass complete checked. Definition lives in the Plan (the behavior list is reviewable); proof lives in the tests (all green is the only pass). No gap in between.

**Evolution example**:

```markdown
Beat 1 (at Plan-writing time):
1. [ ] Runner consistency tests all green, no interactive hang in the background
2. [ ] Repeated begin with the same execution ID returns the same result, no double execution

Beat 2 (after controller acceptance of the Task):
1. [ ] `python -m pytest tests/runner/consistency/ -v` all green (interactive hang covered by test_no_stdin_hang)
2. [ ] `python -m pytest tests/runner/test_idempotent_begin.py -v` all green

During final Agent Verification, the controller re-runs these commands and ticks them only after they pass.
```

## How to split Tasks: behavior groups, not files

**One Task = one cohesive Behavior set + a full RED→GREEN→REFACTOR + an independently runnable Verify.**

Three granularity questions:

1. Do these Behaviors share the same test set? (share → same Task)
2. Does it fit in one implementation context? (no → split)
3. Can the Verify run independently? (no → the boundary is drawn wrong, re-split)

Behavior groups are a **requirements-side** concept — clear at Plan time. Files are an **implementation-side** concept — unclear at Plan time. That mismatch was the root of the old format's rigidity; change the splitting dimension and the rigidity disappears.

Tasks no longer carry a Files field. Where to start → Pre-read (points at files that actually exist); step rhythm → Changes; actually touched → backfilled in Done (the single source of truth); coarse-grained scope → the Plan-level Affected Files table. Small tasks with enumerable footprints (bug fixes, single-point adjustments) need no premature file list either — write the real paths in the Affected Files table.

## How to write TDD

### Behavior is a spec, not a description

Behavior (required when TDD=true) is a testable behavior spec; format is free: input→output mappings, Given/When/Then, all fine. The criterion: **the implementing agent can turn each Behavior into a failing test without guessing.** A Behavior you cannot write a test for is not yet specified — fix the Behavior, not the standard.

```markdown
**Behavior**:
- valid_email("user@example.com") → true
- valid_email("") → false
- valid_email("no-at-sign") → false
```

### With TDD=true, Changes entry 1 is RED

Changes use a numbered list (no checkboxes). With `TDD: true`, entry 1 is RED: turn all Behaviors into failing tests. With `TDD: false`, write the actual implementation steps instead of inventing a RED stage.

```markdown
**Changes**:
1. RED: turn the Behaviors above into failing tests and confirm they fail
2. GREEN: implement the email validator until all tests pass
3. REFACTOR: extract the regex constant (if needed)
```

### Full TDD Task example

```markdown
**Verification Intent**: AC#1, AC#2

**Design Source**: `projects/example/docs/DESIGN.md#validation-contract` → Email validation contract

**Behavior**:
- valid_email("user@example.com") → true
- valid_email("") → false
- valid_email("no-at-sign") → false

**Pre-read**: `src/validators/pattern.py`

**Design**:
Add an email validator, reusing the regex style of pattern.py.
Errors return false instead of throwing (callers render; exception flow does not fit).

**TDD**: true

**Changes**:
1. RED: turn the Behaviors above into failing tests and confirm they fail
2. GREEN: implement valid_email() until all tests pass
3. REFACTOR: extract the EMAIL_REGEX constant (if needed)

**Verify**: `python -m pytest tests/ -v` all passing

**Done**:
Task output: email validation function + 3 test cases
Actually touched files: (backfilled after controller acceptance)
- [ ] The controller has inspected this Task's implementation and confirmed Verify passes.
```

### When to use TDD

**Core heuristic**: can you describe the behavior as `expect(fn(input)).toBe(output)` before writing `fn`? Yes → TDD; no → standard Task, add tests afterwards as needed.

- **Fits**: business logic with clear input/output, API endpoints, data transforms, validation rules, algorithms, state machines
- **Does not fit**: UI layout/styling, config changes, glue code, exploratory prototypes, simple CRUD with no business logic

### TDD stage discipline

| Stage | Problem | Handling |
|------|------|------|
| RED | Test did not fail | Feature may already exist or the test is wrong — investigate before continuing |
| GREEN | Test did not pass | Debug the implementation, iterate until green; do not jump to refactoring |
| REFACTOR | Test failed | Undo the refactor, retry with smaller steps |

**A RED that does not fail is the most common trap**: it means the test does not actually cover the intended behavior — fix it before continuing.

### Commit rhythm

RED→GREEN→REFACTOR is the implementation rhythm inside one Task; it does not require separate commits. The implementer reports completion but does not commit. The controller inspects the diff and independently runs Task Verify: on failure, return the work for repair with **no commit and no Plan update**; on pass, the controller writes back AC/Done evidence and creates the Task's single implementation commit. Failed attempts therefore do not pollute history, while commit boundaries still align with Plan Task boundaries.

## Task field quick reference

| Field | Required | Notes |
|------|------|------|
| **Verification Intent** | yes | AC#N; which acceptance entries this behavior group answers for |
| **Design Source** | yes for project/phase Plans | Authoritative DESIGN `path#heading` + decision/contract; N/A only for a simple Plan with no project/design carrier |
| **Behavior** | yes when TDD=true | Testable spec, directly translatable into a failing test |
| **Pre-read** | yes | Files to read before implementing; N/A if unneeded |
| **Design** | yes | Approach, key ideas, constraints — intent stated clearly, not file-by-file dictates |
| **TDD** | yes | true/false; false needs a reason |
| **Changes** | yes | Numbered list; entry 1 is RED when TDD=true, otherwise write the actual steps |
| **Verify** | yes | Executable command; exit 0 required before ticking Done |
| **Done** | yes | Output summary + actually-touched files + checkbox |

## The Agent Verification / User Validation boundary

### Agent Verification (everything automatable)

Everything verifiable automatically goes here: tests, lint, typecheck, static checks, scriptable behavior assertions. Two-beat scheme above. Cross-Task verifications go at the end of the list, marked "(cross-Task)".

Purely descriptive entries are forbidden: ❌ "build passes" / "feature works" / "no errors" — criteria must be able to catch a bad implementation.

### User Validation (only what the user can verify)

Carries only items **the user must execute and observe by hand**: UI/UX, interaction feel, business flows, visual confirmation.

**Mandatory double question before writing into UV**:

1. Can an agent verify this automatically? → Yes: **UV forbidden**; put it in Agent Verification
2. Must the user execute and observe it manually? → No: **UV forbidden**

**Four mandatory elements per scenario**:

| Element | Requirement | Bad example (fails) |
|---|---|---|
| Validation environment | Reference the mechanism section in project specs or the script entry | Just "start the app" |
| Launch command | One real command the user can copy-paste, env vars included | "Run the command and observe" |
| Pass criteria | A specific, assertable observable result | "Confirm behavior is correct" |
| Failure feedback | What the user provides on failure (log path, diff output) | Missing |

If a mechanism the validation depends on is not yet documented in the project's AGENTS.md, add it to the project spec first, then reference it — never let it appear once in a Plan and be lost.

**Correct scenario example**:

```markdown
#### Scenario 1: onboarding flow regression-free
- Goal: Confirm each wizard step behaves as before the change
- 验证环境: AGENTS.md "validation mechanisms" section (ELLAMAKA_TEST_ONBOARDING sandbox mode)
- Precondition: sandbox mode (WOPAL_HOME=/tmp/wopal-onboarding-sandbox), no build needed
- Launch command: `ELLAMAKA_TEST_ONBOARDING=1 ./scripts/dev.sh desktop`
- User Actions:
  1. Walk the onboarding flow: system check → install CLI → configure AI provider
  2. Watch prompts and status at each step
- Pass criteria: steps advance normally, no new errors, no `[object Object]` text in the UI
- Failure feedback: attach `logs/dev/<scope>/ellamaka-dev-desktop.log` and `git diff -w` output

- [ ] The user has completed the validation above and confirmed the results
```

## Metadata rules

`Product` and `Phase` items are always present in a Plan — creation renders both lines even when empty. The pair is atomic: a phase-linked plan declares both values, an unlinked plan leaves both empty. Values come from the Issue body or the `--product`/`--phase` flags at creation (flags override the body); a half-declared pair is rejected at creation, and `check_doc_plan` gates item presence and pair atomicity at submit/approve. Declaring them only when truly linked matters: archive locates the plan's row in the phase's `Related Plans` table by the `Phase` value — a missing item or half-declared pair silences that sync.

`Project Path`, `Project Type`, `Target Project` are looked up from the space's `STRUCTURE.md`:

1. Determine the domain from the code paths involved (projects / contents / ...)
2. Match path/type/repo in `STRUCTURE.md` frontmatter or tables
3. Fill in the mapping:

| STRUCTURE.md type | Project Type | Project Path example |
|---|---|---|
| `projects` | projects | `projects/<name>/` |
| `contents` | contents | `contents/<name>/` |

Common mistakes: treating a subdirectory (e.g. `projects/<name>/packages/app/`) as the project root — use the repo root.

## Plans, phases, and Gaps

Plans add no Gap-related metadata fields. The phase–Gap relationship is carried naturally by product phase documents; a Plan only states its phase in Goal or Context.

- **Plan phase**: the `Phase` metadata field (declared at creation from the Issue body or `--product`/`--phase`). A phase splits into multiple Plans by scope area; the phase's `Related Plans` table is the aggregate view.
- **Phase table registration**: only Plans linked to a phase (metadata carrying `Product` + `Phase`) trigger phase-doc sync at archive — `archive` locates the row by the ` · <plan-name>` suffix of the slot label and writes `done`. Format spec in dev-doc-master skill `references/phase.md`.
- **Unlinked Plans** get no phase-doc handling at archive (skipped silently, no warnings, no errors). Ordinary feature/fix/refactor Plans leave `Product`/`Phase` empty and never invent rows in phase tables.
- **Gaps**: the single source of truth is the project's `GAPS.md`. Plans reference the Gap identifier they close (e.g. `CLI-G3`) in Goal or Context without copying the description. When a Plan reaches `done` and its Exit criteria hold, the entry is removed from `GAPS.md` (the number retires, never reused).

## Implementation handoff

The controller may implement directly or delegate. Whoever implements should load `df-implement`; do not duplicate that skill inside a handoff prompt.

For a delegated Plan Task, pass only the context needed to do the work:

    ## Plan
    Read the Plan and execute Task <N>:
    <absolute path to the Plan document>

    ## Context
    - Working path: <project/worktree absolute path>
    - Baseline: <Base Commit from Plan Metadata>
    - Follow project/module AGENTS.md

    ## Report
    Return: Goal / Accomplished / Files / Verified / AC Commands / Status

The Plan already carries `Design Source`, Behavior, boundaries, and Verify. A delegated implementer returns only implementation evidence: actual touched files, Verify commands/results, and the real commands corresponding to relevant ACs; **do not commit code, edit the Plan, or tick Done/AC**. The controller then inspects the actual diff and independently runs Task Verify; failure goes straight back for repair, while success is the point at which the controller updates Plan evidence and creates the Task's implementation commit.

If the implementer is also the controller, keep the same order: implementation → controller check → Plan update/commit. Conflicts return to dev-flow handling. With delegated implementation, conflicts return to the delegator. `df-implement` owns STOP/report format; dev-flow owns acceptance and any escalation to the user.

## Common errors

| Error | Cause | Fix |
|-------|------|-----|
| `missing Design Source` | Project/phase Task is not mapped to upstream design | Add authoritative DESIGN `path#heading` + decision/contract |
| `missing Design` | Skipped the Design field | Add `**Design**:` + implementation design |
| `TDD=true requires Behavior` | TDD flag set but no Behavior | Add the testable behavior spec |
| `Changes must not use checkbox` | Changes used `- [ ] Step N:` | Use a numbered list `1. 2. 3.`; with TDD=true, entry 1 is RED |
| `AC checked but carries no executable command` | Criterion-style AC checked straight through complete | After controller acceptance, write back the real command first; tick only after final Agent Verification passes |
| `placeholder: 'TBD'` | Leftover placeholder | Replace with real content or delete the line |

## Validation and advancement

- `submit` / `approve` run `plan check` automatically; do not repeat it manually.
- `submit` moves the Plan into `reviewing`; only then ask the user to review it.
- Run `approve --confirm` only after the user explicitly approves the current Plan; if validation blocks it, fix the Plan and retry.

## Plan naming rules

The Plan name is the authoritative identifier used to derive feature branches. Names must be lean — Issue titles are free text; Plan names and branch names must be short.

### Naming structure

```
<issue_number>-<type>-<slug>     # Issue-driven
<type>-<slug>                    # no Issue
```

- `type` uses standard values (feature/fix/enhance/refactor/docs/test/chore/perf), fully spelled
- No `scope` segment — scope already shows up in `--project` and the slug

### Slug rules

- slug = **1-2 core nouns**, kebab-case, **≤ 20 chars**
- Drop verb phrases and articles; keep the noun core
- Truncate or rewrite when too long; never copy the issue title

| Verbose (forbidden) | Lean (target) |
|--------------|--------------|
| `implement-multi-space-chat-projector-sync` | `chat-projector-sync` |
| `add-skills-remove-command` | `skills-remove` |
| `support-handling-expired-tokens` | `token-expiry` |

### Plan directory rules

- New Plans must be created or located via `flow.sh plan ...`; never hand-write files
- `--project` is a required parameter
- All projects live under `.wopal-space/plans/<project>/`

## Branch naming rules

Feature branches derive from the Plan name and must be bounded — no unbounded concatenation:

```
<project>-<issue>-<type>-<slug-truncated>
```

Past 55 chars total, truncate the slug and append a 4-char hash:

```
<project>-<issue>-<type>-<slug-head>-<hash4>
```

Worktree directory = branch. The branch name carries "unique and mappable back to the Plan" — it is not a full-text copy of the Plan name.

## Branch ownership

| Stage | Branch | Plan status | Notes |
|------|---------|----------|------|
| `planning` | integration branch (main or space/<name>) | `planning` | Plan baseline committed on the integration branch |
| `approve --confirm` | integration branch → create feature branch | `executing` | Commit executing + Worktree metadata on the integration branch first, then create the worktree |
| Implementation (executing) | feature branch | `executing` | Implementation happens in the feature branch's worktree |
| `complete` | feature branch | `verifying` | Plan-only commit of the active Plan (dirty implementation tree aborts) |
| User validation | feature branch | `verifying` | The user validates on the feature branch |
| `verify --confirm` | integration branch | `done` | Plan-only commit to the integration branch |
| `archive` | integration branch | archived | Moved to done/, worktree cleaned up |

**Plan-only commit principle**: lifecycle scripts commit only Plan status changes, never implementation code. The controller creates each Task's implementation commit only after controller acceptance; delegated implementers do not commit. Scripts abort on a dirty implementation tree rather than committing implementation code themselves.