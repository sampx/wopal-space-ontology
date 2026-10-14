# {plan_name}

<!-- Keep structural headings/field names from this English template. Write Plan content in the user's preferred language and prefer plain language; use technical terms only where precision requires them. -->

## Metadata

- **Issue**: {issue}
- **Type**: {type}
- **Target Project**: {project}
- **Product**: {product}
- **Phase**: {phase}
- **Project Path**: {path}
- **Project Type**: {ptype}
- **Created**: {date}
- **Status**: planning
- **Base Commit**: (recorded automatically at approve; integration-branch HEAD)
- **Final Commit**: (recorded automatically at verify; integration-branch HEAD)

## Scope Assessment

- **Complexity**: Low|Medium|High
- **Confidence**: High|Medium|Low

## Goal

<Describe the Plan goal in one sentence.>

## Technical Context

<!-- All four subsections are optional; fill at least one. For simple work, Architecture Context alone is enough. -->

### Architecture Context

<!-- Current architecture, affected modules, and why the change is needed. -->
<Current architecture, affected modules, and reason for change>

### Research Findings

<!-- Summarize prior research. References are context documents only; do not list this project's DESIGN, source files, or config files here. -->
<Research summary>

**References**:
- `<context document path>`

### Key Decisions

<!-- Plan-level implementation decisions must follow upstream DESIGN; never override or rewrite design truth here. Use D-NN numbering. -->
- D-01: <decision and rationale>

### Key Interfaces

<!--
  Shared/cross-Task contract section (hard constraint). Include interfaces that
  multiple Tasks or external consumers must share: CLI commands, API endpoints,
  events, schemas, exported types. Task-local contracts belong in that Task's
  Interface. Do not include module-private helpers.

  Define enough detail for downstream consumers: signature + error codes + key
  semantics (idempotency/version/failure behavior), using the project's own
  notation (TS interface / Python type / JSON Schema, etc.).

  Criterion: a downstream consumer should be able to write calling code and
  compatibility tests from this section alone.

  Once listed, the contract is a red line. If implementation requires changing
  a signature or error code, report it back before changing the Plan. Write N/A
  when there is no external contract.
-->
<Contract definition, or N/A>

## In Scope

<List the concrete outcomes included in this Plan.>

- <item 1>
- <item 2>

## Out of Scope

<List what this Plan intentionally does not include and why.>

- <excluded item and reason>

## Affected Files

<!--
  Expected area of impact, not a construction checklist. The implementer may
  adjust file choices as reality requires; after controller acceptance, record
  the actual touched files in each Task's Done section.
-->
| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| <component> | `file1`, `file2` | modify/create/delete | <role in this change> |

## Acceptance Criteria

<!-- Review success criteria before implementation details. See plan-guide.md for AV/UV rules. -->

### Agent Verification

<!--
  Two-beat AC:
  Beat 1 (Plan time): each item = behavioral criterion + pass standard. Describe
  observable behavior and what counts as passing; do not guess future test paths.
  The criterion must be able to catch a bad implementation.

  Beat 2 (implementation + controller acceptance): the implementer determines
  the real verification command for each AC and reports it; after accepting the
  Task, the controller updates this section in place. The implementer does not edit
  the Plan. During final Agent Verification, the controller runs the real checks
  and ticks ACs only after they pass.

  Every AC must map back from a Task's Verification Intent.
-->
1. [ ] <behavioral criterion + pass standard>
2. [ ] <behavioral criterion + pass standard>

### User Validation

<!--
  User Validation boundary:
  1. Include only behavior an agent cannot verify automatically and the user must
     execute/observe manually. Tests, lint, typecheck, static checks, and scriptable
     assertions belong in Agent Verification.
  2. Give the user enough setup, command/action, and observable pass criteria to
     perform the check without guessing. This is an authoring/review rule, not a
     semantic regex gate in plan check.
-->

#### Scenario 1: <user-visible behavior affected by this change>
- Goal: <what the user is validating>
- Validation environment: <project spec section, README, or script entry>
- Precondition: <setup condition and command>
- Launch command: <one real copy-paste command, including required environment variables>
- User Actions:
  1. <action 1>
  2. <action 2>
- Pass criteria: <specific observable result>
- Failure feedback: <logs, diff, screenshot, or other evidence to provide on failure>

- [ ] <user-validation confirmation>

## Implementation

<!--
  Split Tasks by cohesive behavior/outcome, not by files. Each Task must have an independently runnable Verify.
  Keep ordinary prose readable to human reviewers. Put exact technical contracts in Interface and hard implementation limits in Constraints only when needed.
-->

### Task 1: Task Title

**Verification Intent**: <Agent Verification entries, e.g. AC#1, AC#3>

**Design Source**: <required for project/phase Plans: cite only authoritative `Status: Active` DESIGN as `space-relative-path#heading` + decision/contract; Draft/Proposed are invalid; use N/A only for simple work with no project/design basis>

**Behavior**:
- <observable outcome in plain language>
- <important boundary/failure outcome>

**Pre-read**: <files/docs the Plan author found important to read before implementation, or N/A>

**Interface**: <optional: task-local contract added/changed/removed; reference top-level Key Interfaces instead of duplicating them>

**Constraints**: <optional: hard implementation limits not already stated by Design Source/Behavior/Interface>

**TDD**: true|false — <brief reason when false>

<!--
  true only when the Task adds/fixes/intentionally changes observable behavior that can be specified before implementation and the resulting test has lasting regression value.
  false for pure behavior-preserving refactors, obsolete-code deletion, move/rename/import cleanup, config/build/CI/metadata changes, or other work where fake RED tests add no value. false still requires real verification.
-->

**Verify**:
<executable command(s); implementer runs and reports them, controller independently re-runs them>

**Done**:
<!-- Controller-only after Task acceptance. -->
Actually touched files: <backfilled by the controller after acceptance>
- [ ] <controller accepted this Task after Verify passed>

---

## Delegation Strategy

<!-- Required for 2+ Tasks or Complexity = High. Assign every Task to a specific currently available agent. -->

| Wave | Task | Actor | Dependencies | Rationale |
|------|------|-------|--------------|-----------|
| 1 | Task 1 | <specific agent name> | None | <assignment rationale> |
