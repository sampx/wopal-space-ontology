---
name: df-proposal-review
description: >
  Independent read-only review of business/project Proposals, Plans, ontology
  evolution proposals, PRDs, DESIGN documents, and domain glossaries. Use to assess design
  correctness, feasibility, acceptance and unnecessary complexity.
  Proposal authoring and maintenance belong to dev-proposal or
  ontology-evolution; review of delivered implementations belongs to
  df-implement-review.
---

# Proposal Review

## Review object and authority

Judge whether the proposal can achieve the user's goal correctly, completely and simply, and whether it is implementable and verifiable. Review substance before facts and format. Stay independent and read-only; do not decide product direction or edit for the author.

Choose the mode from the actual object:

| Mode | Object | Authority and objective |
|---|---|---|
| Business Proposal | Business or project Proposal | User goal, higher-level design and rules, existing code, relevant decisions and terminology; assess target specification and acceptance |
| Plan | dev-flow Plan, ontology evolution proposal | Current authorized source, task dependencies and real implementation paths; assess complete goal coverage |
| Document | PRD, product DESIGN, project/module present-state DESIGN, GLOSSARY | Document kind and its governing skill standards; assess correctness, completeness and quality of intent or current facts |

For mixed objects, apply the relevant modes and merge findings sharing a cause. A business Proposal needs no Tasks; a Plan does not reopen approved design decisions. For a Proposal-driven delivery, the current approved Proposal is the sole target authority for the authorized change; unchanged governing design constraints remain binding and the Plan organizes execution. Issues and legacy in-flight Plans retain their existing contract. Present-state DESIGN is a delivery artifact and a reference for existing system facts, not an advance specification of a new target. Product PRDs and product DESIGNs retain their forward-looking role.

## Verification method

Read the entire review object, identify its goal, decisions, behavioral boundaries, key paths and acceptance, then list facts, symbols, files and dependencies to verify against actual code, applicable documents and rules. First establish the target-to-behavior-to-acceptance evidence chain; a complete checklist alone is not proof. For detailed procedures, commands and examples, use `references/review-rubric.md`.

Review the actual working-tree content (including uncommitted changes) or specified revision; state the checked scope. Uncommitted, unpushed or unmerged content, normal draft states, pending installation/build steps and unavailable final-validation environments are not defects by themselves. Report only false premises or a missing viable path to obtain a required resource when needed.

Reuse applicable mechanical gates (`flow.sh plan check`, `wopal space evo check`, `verify-proposals.py`, `verify-docset.py`) and actual results. Do not manually repeat proven checks or treat a future gate as a current failure. When reviewing documents or rules, load the owning skills (`dev-doc-master`, `dev-proposal`, `space-master`, as applicable) and use their actual SOP and quality requirements. Disclose unverified claims rather than presenting them as defects.

## Business Proposal: five checks

| Check | Focus |
|---|---|
| P1 Determinate design and contracts | Settled material decisions, consistent domain model, scope and exclusions, complete applicable contracts; no material choice left to the implementer |
| P2 Design basis and feasibility | Applicable architecture and terminology, inherited or explicitly changed decisions, verified facts and viable paths |
| P3 Decisions and historical integrity | Final choices and material rationale; discarded options are not implementation alternatives; use dev-proposal for supersession and historical protection |
| P4 Acceptance and risk resolution | Each material contract and affected invariant has falsifiable acceptance at a sufficient boundary; mitigations are contractual, residual risks explicitly addressed |
| P5 Leanness | Avoid needless features, abstractions, configuration, dependencies or workflow costs; recommend simplification only with evidence |

Load `dev-proposal` and its `references/design-specification.md` and relevant `references/design-practices.md`, plus the applicable `dev-doc-master` contract and glossary standards. Follow rubric §6; independently discover governing documents rather than trusting the Design Basis list. Check confirmed discussion decisions when available. Apply the current skeleton to every non-archived Proposal. Do not require a separate Design Decisions, Alternatives considered or Risks section just to fill a template.

An unapproved draft may identify open decisions; a material unresolved choice prevents a readiness PASS even if honestly disclosed. For approved Proposals, actual user decisions establish authorization, not valid formatting. Before acceptance, integrate explicit user-authorized decisions (including expanded scope or a change of direction) into the existing Proposal without duplicate approval. Undecided substantive changes still require the user's decision; disclose unavailable authorization evidence instead of assuming a violation. Protect historical `implemented/` decisions and frozen archives under `dev-proposal`.

Use the user's preferred language and clear, concise, affirmative target-state prose. Replace superseded statements, maintain coherent scope, design basis, target contracts, acceptance and material rationale/residual risks, and avoid appended process history or invented alternatives.

## Plan: four checks

| Check | Focus |
|---|---|
| Q1 Coherence | Task ordering and dependencies agree; symbols, data and interfaces have real producers; parallel write sets do not conflict; acceptance has an owner |
| Q2 Facts | Material premises about paths, symbols, commands, interfaces and existing behavior hold; citations identify current applicable authority |
| Q3 Coverage and acceptance | Every key authorized behavior has implementation coverage and observable acceptance, including real entry points, significant failures and preserved behavior |
| Q4 Leanness | Reuse existing capabilities, standard libraries and native mechanisms; avoid needless abstractions or dependencies; remove debt created by replacements |

Start with Q3 and Q1, then Q2 and Q4. Judge the Plan against current authorization, not an imagined ideal implementation. For a Proposal-derived Plan, internal approaches differing from the Proposal sketch are fine when approved design decisions, behavior, and unchanged governing constraints hold. Existing present-state DESIGN differing from an authorized new target is expected; synchronize DESIGN and rules after implementation under `df-implement`, not by writing future behavior into current docs. A Plan organizes implementation and necessary artifact sync, not a second design approval. Legacy DESIGN-driven Plans retain their original contract.

For public commands and user journeys, check applicable acceptance rules from the real public entry to observable outcomes, material failures and state-safety invariants. Automatable behavior belongs in Agent Verification. Exact test commands may be resolved during implementation when the pass/fail criterion is already decidable. Symbols supplied by existing code or dependencies need no new producer Task.

## Document: four checks

| Check | Focus |
|---|---|
| D1 Coherence | Sections, terms, ownership, boundaries and related documents agree |
| D2 Facts | Code, paths, defaults, interfaces, state and failure behavior match actual evidence |
| D3 Correctness and coverage | For product documents, assess goals, requirements, architecture and feasibility; for present-state DESIGNs, assess actual behavior, responsibilities and contract coverage without inventing future goals |
| D4 Quality and leanness | Apply the owning skill's structure, semantic coverage, readability, evidence and applicable quality rules; do not duplicate checklists |

For GLOSSARY, apply `dev-doc-master/references/glossary.md`: check canonical terms, scopes, inherited definitions and agreement with owning contracts; do not impose runtime behavior sections on definitions. Product PRDs and product DESIGNs may describe future plans. Project/module present-state DESIGNs must accurately describe the implemented system. Check current documents against code, applicable rules and related documents, not unimplemented Proposal targets. Use `dev-doc-master` SOP and quality standards. When project, module, directory, documentation or other applicable engineering rules are in scope, check their governing skill standards and consistency.

## Severity

Classify each finding once with a concrete basis, evidence and impact. First distinguish faulty decisions, execution plans, acceptance and current artifact quality; identify the artifact requiring correction.

- **Blocker:** following the proposal would fail to deliver the goal, break real behavior, introduce a security risk, implement an incorrect design or take an infeasible path; a Business Proposal leaves a material design choice unresolved, omits a critical contract or silently violates an applicable architecture constraint; a Plan materially exceeds current authorization or omits a key goal; critical acceptance cannot prove the outcome; false authorization/completion evidence or tampering with protected historical decisions; factual or mutual inconsistencies in reviewed present-state DESIGNs, active glossary definitions or applicable rules at any tier, or failure to meet their governing skill SOP or quality requirements. A proposal explicitly requiring a deliverable that violates mandatory quality rules also blocks.
- **Warning:** a noncritical ambiguity or verification gap, stale Proposal wording, or evidenced unnecessary complexity or maintenance cost that does not prevent correct core delivery. An authorized adjustment not yet integrated into the current Proposal is a maintenance warning, not an unauthorized decision.
- **Info / suggestion:** worthwhile technical alternatives, tradeoffs or simpler approaches that do not require a fix. Omit conventional correct behavior, accepted tradeoffs and personal preferences.

Do not block because a future step is unfinished; do not downgrade mandatory document/rule quality violations. Leanness alone never blocks without a separate severe defect. Recommend the smallest effective correction, not new workflow or architecture. Unresolved product intent belongs to the user; disclose unverified matters.

## Report

Use the user's preferred language for human decision-making first, with enough evidence for the author to locate the issue. Order by actual impact, merge shared causes, omit internal reasoning.

```markdown
# Proposal review
Scope: {object, mode, authority/revision}
Verdict: PASS | REVISE | BLOCK ({N} Blocker / {N} Warning)

## Blocker
### B-01: {plain-language title}
- Location: {file:line}
- Problem: {evidence, actual problem and consequence}
- Fix: {proposal, task or document correction needed}
- Acceptance: {how to verify the correction}

## Warning
### W-01: {plain-language title}
{same information, compactly}

## Other notes
{only necessary user decisions, unverified matters or uncovered scope}
```

Omit empty sections. Info, positive findings and technical suggestions together take at most one or two sentences; on PASS briefly state what was actually checked. No mandatory line-count estimates, task counts or process statistics. Attempt all applicable checks before a verdict; disclose incomplete checks and their reasons rather than claiming full coverage.

PASS: no Blocker or Warning in covered scope. REVISE: Warning(s), no Blocker. BLOCK: at least one Blocker. Unverified items are not defects by themselves, but material unverified checks cannot be represented as passed.

## After review

Review does not authorize implementation, approval or status changes. Return findings to the document owner. Re-review fixes and their direct impact; aim to converge in two rounds without hiding grounded findings or reopening accepted choices. The controlling workflow handles approval, implementation and acceptance.

## References

- `references/review-rubric.md` — detailed checks, evidence probes and examples by mode.
- `dev-proposal`, `dev-doc-master`, `space-master` — governing document and rule standards.
