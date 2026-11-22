# Project & Module Present-State DESIGN Authoring and Review Guide

This guide governs authoring, daily synchronization, and pre-delivery semantic review for project and module **present-state DESIGNs** (`DESIGN.md` and `DESIGN-<module>.md`), and serves as the shared quality baseline for `df-implement` and `df-implement-review`.

## Core Principle: A Verified System Manual First-Time Readers Can Trust

A project present-state DESIGN is neither a speculative blueprint nor a transcribed file tree. It is an accurate manual written so a reader can understand the live system without reading source code:

1. **Audience-Oriented Progressive Depth**:
   - **Layer 1 (User-observable behavior)**: What problem the system or module currently solves, what real capabilities it exposes, how to invoke/use it, observable outputs, and critical prerequisites or limits.
   - **Layer 2 (Conceptual architecture)**: Module decomposition, control/data flow, and state/data ownership (who creates, mutates, stores, and expires each state).
   - **Layer 3 (Developer contract details)**: Key interfaces, configuration defaults/constraints, active business rules, error semantics & complete failure outcomes, plus relative links to owning source files.
   - **Never open with a directory tree or internal class inventory** — orient readers around what the system does and its boundaries before diving into internals.

2. **Present-State Truth, Business Rules, and Lightweight Key Decisions**:
   - **Describe shipped, verified reality only**. Never present unbuilt proposals, planned interfaces, or TODO items as live capabilities.
   - **Fold active business rules into DESIGN**: Projects do not create standalone `BUSINESS_RULES.md`. Express active validation rules, permission checks, quotas, and invariants directly in the owning main/sub DESIGN contract or a `## Business Rules & Failure Boundaries` section (pending rule changes belong in Proposals; legacy `BUSINESS_RULES.md` files stay read-only historical reference).
   - **Keep `## Key Decisions` lightweight**: Keep 1–3 concise sentences on *what* settled rule applies and *why*, linked via a **relative Markdown link** (`[<yyyy-mm-dd-slug>](./proposals/implemented/<class>/<yyyy-mm-dd-slug>.md)` or `[<yyyy-mm-dd-slug>](./proposals/archived/<class>/<yyyy-mm-dd-slug>.md)` for sealed snapshots; `N/A` when predating proposals) rather than a bare backticked path — never copy multi-page proposal deliberations.

3. **Complete Behavioral Contracts and Universal Sub-DESIGN Skeleton**:
   - Sub-DESIGNs use **Fixed Entry/Exit Anchors + Flexible `1..N` Domain-Concept `##` Sections** (`templates/design-sub.md`) so the template never forces plugin/extension specifics onto standard software projects while guaranteeing architectural completeness:
     - Fixed entry anchors (`## Overview and Scope`, `## Usage and Interface Contracts`) + `1..N` bespoke `##` domain sections named after the module's real concepts + fixed state/boundary/exit anchors (`## Data and State Model`, `## Business Rules and Failure Boundaries`, `## Reference Documents`).
   - Across those sections, every important capability or flow must satisfy the **5-Point Required Coverage Checklist**:
     1. **Actor & trigger preconditions** (who invokes it and under what preconditions)
     2. **Component collaboration & ordered sequence** (step-by-step execution or ASCII flow/state diagram)
     3. **Permissions, obligations & invariants** (`must` / `may` / `must not` and conditional branches)
     4. **Side effects & state writes** (durable state, files, caches, or events mutated)
     5. **Complete failure outcomes & recovery** (error contract, partial-failure rollback vs persisted residue, recovery path)
   - **Never copy-paste volatile code inventories**: Never transcribe full source directory trees, exhaustive CLI option tables, full API field schemas, or per-function lists. Summarize contract bounds and link to the defining source file.
   - **Record `Source Carrier` paths in main `## Module Architecture`**: List project- or repo-relative path prefixes (such as `src/auth/`) against each module's sub-DESIGN so `--check-sync` can map code changes automatically to the owning document.

## Anti-Conflict Structure for Parallel Agent Execution

Four hard rules eliminate multi-agent merge hotspots structurally:

| Rule | Practice | Why It Works |
|---|---|---|
| **1. Keep main `DESIGN.md` thin** | Retain only project role, capability summary, cross-module flows, global state ownership, and the `## Module Architecture` map linking sub-DESIGNs | A thin, stable map rarely needs edits during feature or bug work |
| **2. Split multi-module projects by default** | Whenever distinct modules or domains exist, split out `DESIGN-<module>.md` **up front** (do not wait for 500 lines); keep small tightly coupled single-module projects in one `DESIGN.md` | Isolates parallel work into separate physical files; keep tightly coupled contracts together rather than slicing mechanically |
| **3. Omit `Sub-DESIGNs` from project main headers** | Project main `DESIGN.md` headers **omit** a `Sub-DESIGNs` list; sub-DESIGNs keep `> **Parent**: ./DESIGN.md` pointing back, and the body module map links down | Eliminates centralized header-index collisions when parallel tasks add or edit module docs |
| **4. Respect write sets & leave main `DESIGN.md` untouched** | Single-module changes and bug fixes touch only `DESIGN-<module>.md`; parallel workers never cross write-set bounds into main `DESIGN.md` or another module's doc — report out-of-scope drift in `DESIGN Sync` for the coordinator | Centralizes shared-map reconciliation in the coordinator instead of creating race conflicts |

## Fact-Check Procedure and Honesty Discipline

Never author or update present-state claims from memory or unverified assumptions:

1. **Inspect code and configs**: Confirm referenced paths, command names, switches, default config values, status enums, and error strings against actual repository files.
2. **Execute live verification**: Run relevant tests, CLI invocations, or checks for newly described or changed behavior and compare claims with real outputs.
3. **Mark untested claims explicitly**: When environment constraints or scope bounds prevent live execution, **explicitly label the claim as untested along with the condition required to verify it** — never report code-inspection-only inferences as passed runs.

## Dual-Scenario Sync SOP

### Scenario A: Feature / Architecture Changes Driven by a Proposal

1. While a Proposal is in `proposals/proposed/<class>/yyyy-mm-dd-<slug>.md`, **never pre-write unbuilt design specs into present-state DESIGN**.
2. Upon implementation and verification, update all parts in the **same delivery**:
   - Update affected `DESIGN-<module>.md` (or single-module `DESIGN.md`) from real code, tests, and live outputs;
   - Only if module ownership, module existence, or cross-module boundaries changed, have the coordinator update thin main `DESIGN.md` and `## Key Decisions`;
   - When the entire approved Proposal scope finishes, move the Proposal from `proposed/<class>/` to `implemented/<class>/` in the same change and convert it to present-tense `Decision`/`Consequences`.

### Scenario B: Routine Bug Fixes, Minor Adjustments, and Internal Refactoring (No Proposal)

| Nature of Change | DESIGN Action | Execution Boundary |
|---|---|---|
| **Changes observable behavior, interfaces, business rules, defaults, limits, or failure outcomes**, or **fixes stale/wrong DESIGN claims** | **Update in the same delivery** | Update only the affected module `DESIGN-<module>.md` (do not touch main `DESIGN.md` for single-module fixes); if code renames/path changes affect an existing `proposals/implemented/` record, update factual paths there in place without altering the decision |
| **Pure internal refactoring** (observable behavior, contracts, bounds, limits, ownership, and existing docs remain accurate) | **Do not edit DESIGN** | Avoid documentation churn with no semantic change |
| **Out-of-scope drift noticed during parallel work** | **Never edit outside write set** | Keep edits strictly inside authorized files; record exact drift and suggested fix in `DESIGN Sync` for the coordinator |

## Unified Semantic Review Checklist and Slop Checklist

Used by `dev-doc-master` for self-review and reused directly by `df-implement-review` for code ↔ DESIGN verification (never duplicate a separate doc standard elsewhere):

### 1. Newcomer Test
Reading only main `DESIGN.md` and the relevant `DESIGN-<module>.md` without reading code, can a newcomer accurately answer:
- What real capabilities the system/module offers today and how it is used?
- How responsibilities divide across modules and how control/data flows between them?
- What active business rules, preconditions, limits, and complete failure consequences apply?
- Which sub-DESIGN or source path to inspect next?

### 2. Evidence Review
- Does every documented behavior, command, config default, route, and failure mode match actual code, tests, or executed outputs?
- Are unbuilt Proposal plans, speculative endpoints, or "planned/coming" claims kept out of present-state DESIGN?
- Were file-tree listings or full flag/field inventories used as filler instead of real behavioral contracts?
- Are unverified claims clearly labeled as untested rather than passed off as verified?

### 3. Slop Checklist (AI Slop and Doc-Rot Prevention)
Check and strip all five patterns:
- [ ] **CoT / conversation leakage**: Phrases like "after researching...", "per our earlier discussion", "in this refactor we changed...", or agent session logs leaked into permanent system docs.
- [ ] **Implementation status labels & process narration**: `WIP`, `Done`, `Pending`, `In Progress`, `TBD`, progress checkboxes, or history phrases like `deprecated`, `moved from`, `used to`, `已废弃`.
- [ ] **Rule bloat**: Repeated warning/callout boxes overstating trivial local details; state each constraint once cleanly.
- [ ] **Bold abuse**: Excessive `**bold**` spans across normal prose sentences creating visual noise; reserve bold for table keys, key terms, or critical stop conditions.
- [ ] **Cross-level duplication**: Copy-pasting main `DESIGN.md` text into sub-DESIGNs, or pasting `AGENTS.md` operational commands / full Proposals into DESIGN; link across tiers instead.
- [ ] **Paragraph walls & abstract buzzword filler**: Dense 5+ line walls packing multiple rules and parenthetical asides, or vague umbrella nouns (`shape`, `surface`, `seam`, `boundary`) hiding concrete fields, commands, or error rules.

## Readability Calibration, Examples, and Learning Loop

Accuracy without readability fails human readers. Apply these redlines and calibrate against the examples below before finishing any DESIGN.

### Human-Readability Redlines

1. **Plain-language opening (3–5 sentences)**: Open `## Capability Scope` or `## Overview and Scope` by stating what problem the unit solves, who uses it, observable behavior, and the most important limit — zero internal class names, helper functions, or directory trees in the opener.
2. **One stable term per concept**: Use the exact same term for a domain concept throughout the doc; never rotate synonyms for stylistic variety.
3. **Concrete facts over abstract buzzwords**: Treat `shape`, `surface`, `seam`, `boundary`, and `contract` as yellow-flag words — whenever naming the exact config key, CLI command, validation rule, or HTTP/exit code is clearer, state the concrete fact instead.
4. **No paragraph walls**: Break any dense 5+ line block carrying multiple conditions or caveats into short active-voice sentences, bullet lists, tables, or ASCII diagrams.

### Five Calibrated Prose Examples (Over-Trimmed vs AI Code-Talk vs Human-Friendly Balanced)

| Scenario | Over-Trimmed (loses facts) | AI Code-Talk / Wall (hard to read) | Human-Friendly Balanced (target) |
|---|---|---|---|
| **1. Module Opening** | "Handles authentication." | "The `AuthService` registers `JwtMiddleware` in `src/auth/mw.ts`, invokes `decodeToken()`, and emits `auth:verified` on the event bus." | "Verifies bearer tokens on incoming HTTP requests before handlers run. Callers send `Authorization: Bearer <token>`; invalid or expired tokens stop at the gateway with HTTP 401 and never touch downstream handlers." |
| **2. Failure & Rollback** | "Writes session events to disk." | "Calls `appendFile()` inside a `try/catch` and uses `truncateSync()` if `fsync()` throws." | "Each batch flushes and `fsync`s before returning. If writing or syncing fails, the store truncates the file back to its previous byte length so no half-written event remains on disk." |
| **3. Concrete vs Buzzwords** | "Enforces the input shape boundary." | "Validates incoming payload surfaces against the runtime contract seam before entering the persistence layer." | "Rejects requests when `timeoutMs` is not an integer between `100` and `60000`, returning `ERR_INVALID_TIMEOUT` before creating a job record." |
| **4. Config Bounds vs Inventory** | "Configurable via YAML." | *(Pastes a 35-row table duplicating every flag and JSDoc comment from `src/config.ts`)* | "`root` is required with no default (falling back to `cwd` would scatter logs across invocations). `compression` defaults to `'zstd'` (or `'none'` for line-readable plain text); see `src/config.ts` for the full schema." |
| **5. Actor, Order & State Ownership** | "Tasks are cancelled on shutdown." | "During teardown, shutdown orchestration propagates cancellation signals across provider surfaces and resolves asynchronously." | "On shutdown, the coordinator requests provider cancellation before releasing the child scope; each provider must wait for its worker tasks to exit before `dispose()` resolves." |

### Feedback Calibration and Learning Loop

When a user or reviewer flags a passage as unclear, robotic, or missing essential context and settles a preferred wording:

1. **Apply immediately across the current scope**: Rewrite all analogous passages in the same document set using the settled principle.
2. **Project-specific rule** (local terminology, target audience context, project-local doc checks) → record concisely in `<project>/docs/AGENTS.md` or `<project>/AGENTS.md` via `space-master` (only when it adds durable local constraints).
3. **Cross-project recurring flaw** → distill the anonymized bad-vs-good example into this calibration table (via `ontology-evolution`, or `/learn` for cross-session persistence), and promote any mechanically detectable pattern into `scripts/verify-docset.py` so future runs catch it automatically.

## Four-Stage Quality Inspection and Enforcement Loop

Documentation standards only work when backed by mechanical gates and adversarial inspection across the entire delivery lifecycle rather than Agent self-discipline alone:

1. **Stage 1 — Implementation Exit & Change-Scope Mapping (`verify-docset.py --check-sync`)**:
   - Reads the `Source Carrier` prefixes from main `DESIGN.md` → `## Module Architecture` and maps changed non-test code paths (`--base <git-ref>` or current working tree) to their owning `DESIGN-<module>.md` (or single-module `DESIGN.md`).
   - Fails mechanically if module code changed without updating the owning DESIGN in the same delivery — catching "should have written/updated but didn't" before handoff unless `--pure-refactor "<reason>"` is explicitly declared for reviewer audit.
2. **Stage 2 — Deterministic Structural & Boundary Gate (`verify-docset.py`)**:
   - Enforces Checks 1–11 on disk: `Parent` lineage on every sub-doc, **zero orphan sub-DESIGNs** (every `DESIGN-*.md` must be linked from main body outside `Reference Documents`), **zero unreplaced template placeholders or empty table rows**, **non-empty `##` sections**, **mandatory `## Business Rules and Failure Boundaries`** on Project main and Active Module DESIGNs, relative link validity, zero absolute paths, zero process-state narration, fixed English header fields, and valid `Status`.
3. **Stage 3 — Structured Handoff Gate (`DESIGN Sync` in `df-implement` / `dev-flow`)**:
   - Implementation handoff reports require a non-empty `DESIGN Sync` field attaching either (a) the `verify-docset.py --check-sync` output, updated `DESIGN-<module>.md` sections, and live verification evidence, or (b) an explicit `--pure-refactor` justification and any out-of-scope drift escalated to the coordinator. Coordinators reject handoffs lacking this block.
4. **Stage 4 — Adversarial Read-Only Review (`df-implement-review`)**:
   - The isolated read-only reviewer inspects the actual `git diff` against owning DESIGNs: missing DESIGN updates for observable contract/config/error changes or false "pure-refactor" claims raise a **Blocker**.
   - Every updated DESIGN is audited against the **5-Point Required Coverage Checklist**, **Newcomer Test**, **Evidence Review** (checking claimed commands/defaults/paths against real code and test runs), and **Slop Checklist**.
