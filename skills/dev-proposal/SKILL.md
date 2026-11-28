---
name: dev-proposal
description: >
  Analyze, discuss, write, and maintain business/project Proposals. Use when
  asked to discuss a proposed change, settle its requirements and decisions,
  create or revise a Proposal, record approval, migrate, archive, or supersede
  an implemented Proposal. Use df-implement for routine work within settled
  design, df-proposal-review for independent reviews, dev-doc-master for
  PRD/DESIGN authoring, ontology-evolution for capability evolution, and
  dev-flow for Plan orchestration.
---

# dev-proposal — Business Proposals

A Proposal records the **determinate target solution, important decisions, and acceptance criteria** of a change. Settle the solution before writing the Proposal specification. The user owns product and architectural decisions; the agent investigates facts, analyzes options, recommends, and records accurately.

## Responsibility and authority

| Object | Responsibility |
|---|---|
| PRD / product DESIGN | Product intent, governing architecture, and capability boundaries |
| Project/module DESIGN | Verified delivered behavior, responsibilities, and contracts |
| GLOSSARY | Canonical domain terminology and definitions |
| Proposal | Target solution for a proposed change; authority for the change once approved |
| Issue / Plan / Task | Work within settled decisions or delivery organization, progress, and evidence |

Design is an activity; DESIGN is a formal document. During proposal work, read applicable DESIGNs and GLOSSARY, analyze constraints, and settle the target solution. **Record undelivered target contracts and changed terminology in the Proposal only.** Do not pre-write project/module present-state DESIGN or link back from it to unimplemented or rejected Proposals. After verified implementation, `df-implement` synchronizes present-state documents under `dev-doc-master`.

An approved Proposal owns the target only for the authorized change; unchanged architecture, contracts, and engineering rules remain binding. Settle design decisions and leave internal implementation free.

## When a Proposal is required

Write a Proposal when any of these holds:

- Several viable paths exist and a material decision cannot be derived from code or settled authorization.
- An active default, boundary, permission, failure semantic, or external contract changes.
- An implemented decision is partly or wholly overturned.
- A shared convention across projects or modules changes, or the user needs to re-decide scope.

Skip the Proposal when all three hold:

- The task or defect is within an existing decision.
- One Issue or direct implementation can state scope and acceptance.
- No design-level decision needs to be made by the user.

Routine bugs, style tweaks, mechanical renames, and internal refactors preserving contracts go through an Issue or direct implementation; do not manufacture records for every change. Search active and implemented Proposals on the topic first; sync factual drift in place, create a new Proposal for changed decisions.

## Workflow overview

Enter at the stage the user requests; simple approval, migration, or fact maintenance need not repeat solution discussion.

| Stage | Core work | Output or completion |
|---|---|---|
| 1. Investigate | Determine need and ownership; verify facts, decisions, governing constraints | Problem and design basis understood |
| 2. Discuss | Model domain, discuss decision dependencies in rounds, test scenarios and risks | All material decisions settled |
| 3. Write | Synthesize Proposal specification, acceptance and verification boundaries; self-check | `Status: proposed` |
| 4. Review | Independent `df-proposal-review`; resolve material findings | Ready for user decision |
| 5. Approve | User approves scope and selects Delivery; commit approved record | `Status: approved` |
| 6. Deliver | Route implementation; maintain explicitly authorized adjustments | Evidence matches authorization |
| 7. Close | Migrate after full delivery and user acceptance; handle supersession | `Status: implemented` |

Rejection and archiving follow the lifecycle rules. A Proposal does not carry Plan/Task execution states, and the agent never approves on the user's behalf.

## Investigate and discuss the solution

For a new Proposal investigation or discussion, read `references/discussion.md`; select applicable domains from `references/practices.md`. Verify an already settled solution without repeating the interview.

### Investigate the basis

- Establish user goal, actual problem, and affected scope; distinguish the need from the user's initial suggested solution.
- Read applicable AGENTS.md, product PRD/architecture DESIGN, project main DESIGN, affected module DESIGNs, companion contracts, and any glossary; follow binding document relationships upward.
- Inspect relevant active and implemented Proposals, real code, and tests. Scale investigation to impact; the agent verifies facts.
- Identify responsibilities, dependencies, interfaces, rules, and invariants to preserve. Name changed existing decisions, reasons, impact, and surviving constraints for the user to decide. Expose conflicts between settled design and code with evidence.
- Verify critical technical feasibility; do not claim readiness on an unverified material premise.

### Domain modeling and decision discussion

- Clarify domain concepts, canonical terms, relationships, responsibilities, state ownership, and business rules. Surface ambiguity, overlap, and conflicting definitions.
- Test the solution against concrete normal, failure, and boundary scenarios; probe conditions that would change outcomes.
- Build a decision tree and settle upstream decisions first. Ask only mutually independent questions whose prerequisites are settled in each round; batch them where useful.
- Number questions, state the decision, meaningful tradeoffs, recommended answer, and reason. Prefer questions a simple "yes" can confirm; investigate verifiable facts yourself.
- Wait for answers after each round, establish which decisions are actually settled, and recompute downstream questions. Unanswered or ambiguous decisions remain open. Capture decisions, necessary rationale, terms, and unresolved questions as they emerge.
- Use permitted temporary records for long discussions; notes are not formal Proposals or implementation authority.

Completion: every material target decision is settled; key scenarios and boundaries have answers; critical feasibility has evidence; major risks have contractual controls or explicit user acceptance. Recap the solution to confirm shared understanding; do not repeat explicit confirmation already given. Return to discussion for any material unresolved decision rather than inventing one while writing.

## Write the Proposal specification

Before writing, read `references/specification.md` and `references/lifecycle.md`; use `templates/proposal-proposed.md`. Writing synthesizes settled decisions, not a new selection exercise.

### Body structure

| Section | Requirement |
|---|---|
| Problem | Problem, impact, and change goal |
| Design Basis | Applicable design authorities, inherited constraints, explicitly changed decisions |
| Proposal | Determinate target solution, scope, and new or changed contracts |
| Bespoke sections | Organize by actual domain; elaborate interfaces, state, migration, etc. where needed |
| Design Decisions (optional) | Final choices and rationale with lasting value |
| Acceptance criteria | Observable or inspectable completion conditions |

Keep fixed headings in English and body prose in the user's preferred language. Organize by user scenarios and domain concepts, not a mechanical technical outline. File inventories and implementation tasks are not a solution. State exclusions and preserved behavior, reference unchanged contracts.

### Contracts and decisions

Use the five-point coverage standard in `dev-doc-master/references/design-project-guide.md` for material capabilities and flows: actor/trigger, collaboration/sequence, permissions/invariants, state/side effects, complete failure outcomes/recovery. Apply relevant aspects without requiring unrelated headings; use domain practices for specific coverage.

Record the choice itself in the target solution. Separate rationale is useful when a choice is costly to reverse, puzzling without context, and involved real tradeoffs. Rejected alternatives are not implementation options. Eliminate avoidable risks, make mitigations verifiable contracts, and explicitly seek user acceptance of material residual risks and costs. Omit resolved discussion that adds no lasting value.

### Acceptance and self-check

- Every material changed contract and affected existing invariant needs falsifiable acceptance, including real entry points, normal behavior, material failures, and state effects.
- Specify the entry point and observable outcome that prove the contract; choose the lowest-cost sufficient verification layer under applicable testing rules. Do not lock every test command prematurely.
- Reconcile the specification with confirmed decisions; detect omissions, weakening, unauthorized expansion, terminology conflicts, and architectural drift.
- Simulate an implementer absent from discussion: can the Proposal and its authority references determine materially equivalent responsibilities, interfaces, state, and behavior? Return to discussion if a material choice still requires guessing.

After self-check, send for independent review. Keep `Status: proposed`; a review pass is not user approval.

## Ownership, path, and lifecycle

Read `references/lifecycle.md` for creation, approval, migration, or link maintenance; it owns complete fields and operational details.

- Product: `docs/products/{product}/proposals/`; project: `projects/{project}/docs/proposals/`. One decision, one home; a cross-project decision with a clear owner belongs to the leading project.
- Path: `<proposals-root>/{lifecycle}/{class}/yyyy-mm-dd-<slug>.md`. Use the first-proposed date, lowercase kebab-case slug (2–4 words), and retain the filename on migration.
- Closed classes: `feature`, `bug-fix`, `simplification`, `architecture`, `process`, `testing`.
- A new Proposal requires a title, standalone `Status: proposed` line, `Class`, and `Created`; no centralized index or separate execution progress fields.

| Directory | Status | Entry condition |
|---|---|---|
| proposed/ | proposed | Proposal written |
| proposed/ | approved | Explicit user approval; authorization fields recorded |
| implemented/ | implemented | Full delivery and user acceptance |
| rejected/ | rejected — reason | Explicit rejection with lasting guardrail value |
| archived/ | implemented | No longer guides daily work; add Archived date and freeze |

Archiving does not introduce another Status. Handle rejected or obsolete records under retention and deletion authorization rules, repairing inbound links. Frozen bodies are not edited, fact-synced, or checked for outbound links.

## Approval and delivery

Once the user approves, add `Approved: YYYY-MM-DD — <approver>`, `Authorized scope` (including explicit exclusions), and `Delivery`. Set approved and retain the proposed path.

The user must choose `Delivery`:

- `direct`: no Plan split; `df-implement` uses `git-worktrees` for an isolated worktree by default.
- `plan`: `dev-flow` organizes Plan/Task, isolated worktree, and shared delivery.

Help the user choose with objective facts such as repo count, parallel work, and staged acceptance; never choose on their behalf. Before creating a delivery branch or worktree, commit the approved Proposal alone on the integration branch as the delivery baseline. Link related Plans, commits, review and acceptance evidence; do not copy progress tables.

### Maintain before acceptance

The current approved Proposal governs the authorized change; implementation must not autonomously change decisions, scope, or acceptance. Explicit user decisions during testing or validation authorize adjustments without repeated approval.

Integrate changes into the existing scope, design basis, target solution, acceptance, and affected rationale and residual risks, preferably before code changes or before delivery if already implemented. Keep the path, approved status, and delivery baseline; the controller coordinates Plans and shared files. Replace superseded content rather than appending parallel designs or a process log.

### Migrate after acceptance

Only after full approved delivery and user acceptance, move to implemented, change Status and use `templates/proposal-implemented.md`: Proposal → Decision, actual acceptance results and residual costs → Consequences, preserving Design Basis and important rationale. Remove planning-era headings and prose.

In the same delivery, synchronize affected present-state DESIGNs and glossary, link the implemented record from DESIGN's Key Decisions, and repair inbound links. Partial delivery stays approved. Completing one Plan cannot migrate the entire Proposal.

## Maintain and supersede implemented Proposals

Read `references/supersession.md` when an implemented decision is involved.

- Fact-only drift: decision, defaults and boundaries unchanged; synchronize facts and links in place in the same delivery.
- Partial supersession: create a new Proposal and link the old record from Problem; keep old decisions intact until full delivery and acceptance, then cross-link both ways and state superseded and surviving parts.
- Full replacement: create a new Proposal; at full delivery, absorb unique rationale, costs, verification and other lasting content before deletion, or archive and freeze when independent historical value remains.
- An implemented decision cannot move back to proposed or be rewritten into a different decision. Archiving adds only the Archived date and repairs external inbound links; the archived body is permanently frozen.

Retain rejections only for lasting guardrail value; otherwise delete under deletion authorization and repair inbound links. Small UI or mechanical changes are not archived merely to accumulate history.

## Verification and handoff

After each write or state transition, run (path relative to this skill):

```bash
python3 scripts/verify-proposals.py <proposals-root>
```

For moves or deletions, search inbound links as described in lifecycle and use repeatable `--link-scope <docs-dir>` to check consumers; manually inspect cross-repository references. Exit 0 proves snapshot format and link validity, not design correctness, historical integrity, or human approval.

Independent review belongs to `df-proposal-review`; route delivery through `df-implement` or `dev-flow`. This skill owns Proposal discussion, writing, authorization records, and lifecycle maintenance only.

## Reference index

| File | When to load |
|---|---|
| `references/discussion.md` | Solution investigation/discussion; decision tree, domain modeling, discussion technique |
| `references/practices.md` | Select applicable domain-specific contract coverage |
| `references/specification.md` | Author or materially revise a Proposal; specification, risk, acceptance, self-check |
| `references/lifecycle.md` | Creation, approval, migration, rejection, archiving, link maintenance |
| `references/supersession.md` | Fact synchronization, partial or full supersession of implemented Proposals |
| `templates/proposal-proposed.md` / `templates/proposal-implemented.md` | Creation and post-acceptance migration |
