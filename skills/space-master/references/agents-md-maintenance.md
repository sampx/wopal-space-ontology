# AGENTS.md Maintenance

Authoritative spec for creating or updating a project- or directory-level `AGENTS.md`.

> 中文版：[agents-md-maintenance.zh-CN.md](./agents-md-maintenance.zh-CN.md)

## 1. When to Update

Update only when a completed change leaves a long-lived agent behavior boundary that code, tests, config, and existing docs cannot carry. **Not updating is a normal outcome**; never add rules just to close a process step.

### Document ownership

| Document | Owns | Does not own |
|---|---|---|
| DESIGN | Architecture, behavior contracts, state model, business flow | Coding style, CLI output format, logging fields, test runner details |
| AGENTS.md | Rules an agent follows while implementing, testing, and verifying | History, one-off decisions, architecture prose copied from DESIGN |
| README.md | Human install, usage, capability entry | Agent rules, internal validation flows, implementation constraints |

AGENTS.md is the first operational document an agent loads. It must let the agent start work without reading source to rediscover commands, style, error model, output contract, logging sink, or test fixtures.

### Project standards discovery

For a new project, or one whose AGENTS.md lacks operational standards, inspect the toolchain first:

1. Package, build, typecheck, formatter, and lint config: actual commands and enforced rules.
2. Canonical error type, stable fields, side-effect uncertainty model.
3. Output contract: CLI stdout/stderr and exit codes; service config and lifecycle errors; library exports and import-time side effects.
4. Logging implementation, location, rotation, recorded fields, prohibited content.
5. Unit and integration commands, test layers, fixtures, contract helpers, cleanup; confirm new tests are picked up by an existing entry.
6. Concrete commands, paths, symbols, formats. No generic advice such as “search before coding” or “reuse existing helpers” without naming the target.

Industry practice is the baseline only when the project has no settled convention; the actual stack, config, and public contract win.

### Quality gates come before the rulebook

A gate is a check an agent can run without interpreting code. Scaffold every standard check the stack supports before documenting it:

1. Pick the mainstream formatter, linter or static analyzer, type checker, unit runner, and integration runner for the language and framework.
2. Wire them into the existing command surface (`package.json`, `Makefile`, build script). A gate must be executable.
3. Put each exact command in the Quality Gates table with its blocking condition and the log or artifact to inspect on failure.
4. Automate everything mechanically decidable; reserve manual verification for humans, external systems, or runtime observation.

AGENTS.md then names installed tools and commands. Build a missing scaffold before writing the rule that depends on it.

### Standards by project type

| Project type | Make explicit |
|---|---|
| CLI | Success and failure streams, JSON/text format, indentation and trailing newline, exit codes, help/version exceptions, secret redaction |
| Service / daemon | Config ownership, startup and shutdown errors, health/readiness reporting, log sink and rotation, graceful failure |
| Library | Public exports, error contract, import purity, dependency boundaries, compatibility policy |
| UI / application | Loading, empty, error, and disabled states; user-visible error wording; accessibility and output consistency |

Use only the applicable rows and record project-specific choices.

## 2. Language Version and Naming Rules

- Non-English preference: write `AGENTS.<locale>.md` first for review; translate into `AGENTS.md` only after approval.
- `<locale>` is an IETF BCP 47 / RFC 5646 tag.
- The formal English file has no suffix; never create `AGENTS.en-US.md`.
- English preference: update `AGENTS.md` directly.
- The preferred-language version copies every heading from the English template; translate only body text, table cells, examples, and explanatory prose. Never translate or rename a heading.
- Markdown heading levels only; no chapter numbers such as `## 1.`.
- Structure comes from `templates/agent-rules.md`, the single source of truth.

## 3. Content Boundary Rules

`AGENTS.md` is the operating rulebook for implementing, testing, and verifying.

A rule belongs only if all hold:

- Long-lived across future tasks and refactors.
- Restricts agent permissions, responsibilities, behavior, or decision boundaries.
- Needed during work — logging, output and routing, deployment and release limits, testing and verification, coding discipline — even when DESIGN details the topic.
- A concise operating rule, not DESIGN prose restated; link DESIGN for detail.
- Names the concrete command, path, symbol, format, or boundary.
- Backed by an existing tool, script, or command when the check is mechanical.

**“A DESIGN also describes it” is not a reason to omit.** An agent will not open every DESIGN on every task, so day-to-day constraints must be reachable from the rulebook: summarize here, link DESIGN. Delete a rule only when it adds nothing the agent must act on.

Never write:

- One-off design decisions, structures, or data models from the current change, including its files, functions, config values, UI structure, and test assertions.
- Single-bug records, or rules whose only purpose is preventing that bug's recurrence — make it a test.
- Exhaustive directory, API, command, field, or architecture inventories.
- “Check”, “inspect”, or “review” without an installed command or tool.
- Facts already carried by code, config, scripts, Plans, or docs with no operating instruction.
- Experience notes that constrain no decision; those belong to long-term memory.

**Two failure modes.** Over-stuffing pastes one-off decisions, bug stories, or DESIGN text verbatim, so later agents cannot tell a durable rule from history. Over-trimming deletes a working constraint because “DESIGN also describes it”, leaving the agent without the rule it must follow. When unsure, keep the summarized constraint.

Merge duplicate and stale rules before adding. One sentence when one suffices. All links are relative: these files are committed and shared across machines. Canonical References lists only mandatory documents (PRD, DESIGN, business rules). Research, tutorials, and auxiliary specs are references.

### The Code Review Rules Section

- Code projects must include `## Code Review Rules`; documentation-only directories may omit it.
- New projects generate it from the template; updates preserve it permanently — never delete, rename, or translate the heading.
- Content is a direction-level skeleton: the review process this project actually uses, the defect-report boundary, and project-specific checkpoints written in each project's own file.

## 3.5 Document-Set Consistency

- Audit rules against code and authoritative documents (see Rule Audit); delete or fix rules whose code is gone or whose constraint structure now enforces.
- When DESIGN or PRD changes, align stale `AGENTS.md` constraints that contradict it.
- The architecture/directory section lists only existing paths; target structures belong in Implementation Rules.

## 4. Rule Audit (Before Any Update)

Start with the audit, not with translation or polish. Classify every rule keep, delete, or fix, with evidence, and put the result in the confirmation plan.

### Delete (any one suffices)

1. The referenced module, file, or command is gone. Verify with `rg "<name>" <project>/src/` and `git log --all --oneline --diff-filter=D -- <path>`.
2. Structure already guarantees it: shared constants, generated types, or a CI check. A structure-enforced rule is noise.
3. It is a design detail, not a working constraint: it restates a DESIGN structure, flow, or model and changes no agent action. Narrower than “DESIGN mentions it” — logging, output and routing, deployment and release limits, testing and verification, and coding discipline stay summarized.
4. It is a pure implementation fact: it describes what the code does without constraining choice. Read the code instead.

### Keep

- Safety boundaries: deletion scope, single credential write path, protected content.
- Behavior constraints: thin handlers, output through a single service, error-code conventions.
- Operating constraints even when DESIGN covers them (see Delete 3).
- `Code Review Rules`: heading verbatim, content audited like any other rule.
- `User-Supplied Rules`: never touched.

### Fix

- Directory or command lists no longer match reality.
- Conflict with a newer authoritative document or design mechanism.
- EN/CN drift: merge both directions onto the correct content.

### Evidence

`rg` or `ls` for existence, `git log --oneline` for moved or deleted modules, comparison against DESIGN and protocol docs for duplication, and reading the referenced module for decision boundaries.

## 5. Workflow

### Step 1: Resolve Target

1. Path given: use it.
2. Project name given: locate the repository and confirm the inferred path.
3. One match: confirm with the user. Several: list candidates and let the user choose.
4. Project-level: `<project>/AGENTS.md`; directory-level: `<target-directory>/AGENTS.md`.

**Output**: target directory, target path, assumptions needing confirmation.

### Step 2: Collect Context

Read the target `AGENTS.md` and nearest parent; related DESIGN (PRD only if it exists and is not merged into DESIGN; `BUSINESS_RULES.md` only if present); package/build/test/typecheck/lint config including gate commands; the code owning style, errors, CLI output, logging, and fixtures — extract commands and hard constraints, not source encyclopedias; `rules-context` when provided. Then run the Rule Audit on every existing rule.

Typical locations:

```text
<project>/docs/PRD*.md
<project>/docs/DESIGN*.md
<project>/AGENTS.md
```

**Output**: canonical document list, audit classification, implementation facts, missing or unconfirmed information.

### Step 3: Draft Confirmation Plan

Get explicit confirmation before writing. The plan includes:

1. Target path.
2. Canonical documents to reference.
3. frontmatter `name` and `description` to write or preserve.
4. Rules to keep, add, remove, or compress, with their audit classification.
5. Original rules moved to `User-Supplied Rules`, plus proposed deletions with justification.
6. Architecture/directory plan.
7. Quality Gates and dev/test standards: commands, failure conditions, fixtures and helpers, error handling, CLI output, logging.
8. Where `rules-context` merges.
9. Compression or split strategy if the result may exceed 300 lines.
10. Confirmation that `User-Supplied Rules` stays unchanged.
11. Low-information content to drop: `N/A` placeholders, text duplicated from DESIGN, frontmatter, or global regulations, long catalogs.
12. Per structure item: current fact, durable target constraint, or temporary plan.
13. Per deleted rule: why it does not constrain agent work — never “DESIGN also covers it”.
14. `Code Review Rules` handling (keep, generate, fill checkpoints), or confirmation that omission is intentional.

Existing rules are immutable after initial creation: every add, change, or delete appears in the plan and waits for explicit confirmation.

A small update (no frontmatter, path, or scope change; 1–2 sections) may compress the plan to: target, affected sections, preserved rules, additions/deletions/merges, unchanged `User-Supplied Rules`, and structure classification.

**Output**: plan awaiting confirmation.

### Step 4: Write After Confirmation

1. Non-English preference: update `AGENTS.<locale>.md` first.
2. After the review version is approved, translate into `AGENTS.md`, keeping the semantics aligned.
3. English preference: write `AGENTS.md` directly; no `AGENTS.en-US.md`.
4. Never write, overwrite, or reorder `AGENTS.md` before confirmation.

**Output**: updated review and/or formal path.

## 6. Quality Checklist

- [ ] Target path explicit or safely inferred
- [ ] Every existing rule audited against code and authoritative documents; result shown in the plan
- [ ] frontmatter `name` and `description` present; body does not repeat them
- [ ] `description` is single-line, stable, and suitable for automated discovery
- [ ] Target and parent `AGENTS.md` considered when present
- [ ] PRD, DESIGN, and `BUSINESS_RULES.md` referenced when present
- [ ] No `N/A` placeholders for documents that do not exist
- [ ] Body summarizes long-lived operating constraints; DESIGN is linked for detail
- [ ] All long-lived operating constraints present: logging, output/routing, deployment and release limits, testing and verification, coding discipline
- [ ] Style, error contract, CLI/output, log sink, and forbidden content stated with concrete commands, paths, types, or formats
- [ ] Every Quality Gates row has an existing command and a blocking condition; nothing mechanical left to prose
- [ ] Test commands, layers, fixtures, helpers, and runner registration explicit
- [ ] Agent can implement without reopening source to rediscover conventions; no unnamed generic reminders
- [ ] README has no agent rules; DESIGN has no duplicated coding or test policy
- [ ] No one-off design decision or single-bug record
- [ ] No architecture diagram, API catalog, command catalog, or directory encyclopedia
- [ ] Architecture lists only existing paths; target structures not presented as facts
- [ ] Project-level document references subdirectory `AGENTS.md` instead of copying details
- [ ] 80–150 lines targeted, 300 hard limit
- [ ] Basic development and test commands preserved
- [ ] Rules focus on implementation, testing, and verification
- [ ] Preferred-language version generated first when applicable
- [ ] Canonical documents referenced, not copied
- [ ] No rules extracted from `BUSINESS_RULES.md` into the body
- [ ] Testing section follows the space's canonical testing rule instead of restating general TDD/test philosophy; it records only project-specific commands, layers, fixtures/helpers, runner registration, and host/manual verification boundaries
- [ ] Preferred-language headings identical to the English template
- [ ] `User-Supplied Rules` unchanged: no additions, modifications, deletions, or reordering, except original specification migrations
- [ ] Non-obsolete original rules preserved; deletions justified in the plan
- [ ] Full plan shown and confirmed before writing
- [ ] Code projects include `Code Review Rules`; heading untouched
- [ ] The review process cited in `Code Review Rules` actually exists for this project
- [ ] Formal English version updated after confirmation when applicable

## 7. Response After Completion

Report in the user's language:

1. Updated file path and scope.
2. Key added or changed rules.
3. Which documents (DESIGN, PRD, README) were checked or aligned.
4. Ignored `rules-context` content and why.
5. Missing canonical references or assumptions.
