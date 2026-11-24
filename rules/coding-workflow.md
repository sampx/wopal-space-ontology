---
trigger: model_decision
description: Follow this rule in coding spaces to route product/project development, present-state documentation authoring/review, proposal lifecycle, optional Plan orchestration, AGENTS.md/README governance, and implementation/review without overlapping skill scopes.
keywords:
  - 'coding workflow'
  - 'dev-doc-master'
  - 'space-master'
  - 'dev-proposal'
  - 'dev-flow'
  - 'df-implement'
  - 'df-implement-review'
  - 'df-proposal-review'
  - 'proposal'
  - 'DESIGN'
  - 'PRD'
  - 'AGENTS.md'
  - 'cupdate-design'
  - 'cupdate-prd'
  - 'cupdate-proposal'
  - 'cupdate-agent-rules'
  - '开发流程'
  - '现状设计'
  - '设计文档'
  - '提案'
  - '工作流规则'
---

# Coding Space Skill Collaboration and Routing Rules

This rule defines the cross-project orchestration and skill-routing boundaries for coding spaces. Rather than hardcoding any single repository layout or stack, it separates shared capability bases from workflow skills so any project can establish disciplined proposals, sharded present-state DESIGNs, tiered `AGENTS.md`, automated testing gates, and independent reviews.

## Development Workflow and Skill Layering

### End-to-End Development Flow (`dev-flow` as Optional Orchestration Layer)

```text
PRD (Product Goals, dev-doc-master)
    ├─ Issue (Defect/Task within settled design) ────────┐
    └─ Proposal (Substantial decision, dev-proposal)     │
           └─ Proposal Review (df-proposal-review) → User Approval ┤
                                                         ▼
                          ┌──── Simple / bounded work (direct, skip dev-flow) ────┐
                          │                                                       ▼
                          └─ Complex / multi-task / parallel (optional: dev-flow Plans + Graph)
                                                                                  │
                                                                                  ▼
                                     df-implement (code + tests + on-demand DESIGN/Proposal/AGENTS sync)
                                                                                  │
                                                                                  ▼
                                 df-implement-review (independent read-only review: code↔tests↔DESIGN/Proposal)
                                                                                  │
                                                                                  ▼
                                                            User Validation → Authorized Delivery
```

### Capability Bases vs Workflow Skills

```text
Capability Bases (single sources of truth; load on demand, never duplicate):
  • dev-doc-master   ── Product PRDs, Product DESIGNs, Project/Module Present-State DESIGNs
                        (authoring, anti-conflict sharding, fact-checking, Slop Checklist)
  • space-master     ── Space governance, tiered AGENTS.md (hierarchy, non-empty gates, Rule Audit) & README.md
  • rules/testing.md ── Automated testing layers and TDD decision policy

Workflow Skills (own phase advancement and gates; call capability bases explicitly when authoring/auditing docs or rules):
  • dev-proposal ──▶ df-proposal-review ──▶ [Optional: dev-flow] ──▶ df-implement ──▶ df-implement-review
        │                                                                │   │               │
        └─ Prose aligns with dev-doc-master (keeps present-state clean)  │   │               └─ Doc & slop audit via dev-doc-master
                                                                         │   └─ Durable constraint change → space-master
                                                                         └─ Observable contract change → dev-doc-master module DESIGN sync
```

## Scenario Routing and Exclusion Boundaries

| Task / Intent | Load | Boundaries & Exclusions |
|---|---|---|
| Author, update, module-split, or audit a Product PRD, Product DESIGN, or Project/Module Present-State DESIGN | `dev-doc-master` (`/cupdate-prd`, `/cupdate-design`) | Project/module DESIGNs document verified shipped reality only; Product DESIGNs plan ahead of implementation; never intercepts `/cupdate-agent-rules` or `/cupdate-readme` |
| Create, maintain, or check business/product Proposal lifecycle (`proposals/{proposed,implemented,rejected,archived}/{class}/`) | `dev-proposal` (`/cupdate-proposal`) | Owns major design rationale, alternatives, user approval & `Delivery: direct \| plan`; routine bugs use Issues; never replaces DESIGN or Plan |
| Independent pre-execution review of Proposals or Plans | `df-proposal-review` | Read-only review of problem, alternatives, scope boundaries, and verifiability; never rewrites docs on the author's behalf or substitutes for user approval |
| Complex work orchestration: direct vs Plan triage, Plan/Task split, parallel write-set coordination, and Plan Graph | `dev-flow` | **Optional orchestration layer**: use only for multi-project, multi-deliverable, or parallel work; bounded tasks go straight to `df-implement`, but a `Delivery` choice already recorded in an approved Proposal outranks this heuristic; never duplicates Proposal approval or doc rules |
| Execute implementation, automated tests, and delivery sync | `df-implement` + `rules/testing.md` | Must respect approved design bounds; `direct` deliveries (approved Proposal or standalone Issue) start in a `git-worktrees` isolation worktree unless the user requested the main branch or a controller assigned one; call `dev-doc-master` to sync module sub-DESIGN & Proposals on visible behavior changes (skip DESIGN on pure internal refactors); run the full-delivery `verify-docset.py --check-sync --base <delivery-base>` gate; call `space-master` when durable constraints change |
| Independent post-implementation code/test/doc review | `df-implement-review` | Read-only check across the full delivery-baseline diff (code ↔ tests ↔ authorization ↔ DESIGN/Proposal sync), using `dev-doc-master` semantic & Slop Checklist; never edits files |
| Create, audit, or maintain space/project/docs/module `AGENTS.md`, project `README.md`, or install/scan/remove external skills | `space-master` (`/cupdate-agent-rules`, `/cupdate-readme`) | Generates the unbypassable harness-injected `AGENTS.md` hierarchy (`<project>/AGENTS.md` wiring `Doc sync` + `DESIGN` sync, thin `<project>/docs/AGENTS.md` guardrail card, and on-demand `<dir>/AGENTS.md`); enforces zero parent-child duplication, non-empty +/- gate verification, and read-only legacy `BUSINESS_RULES.md`; does not author PRDs or DESIGNs |
| Modify ontology capability assets (skills, rules, agents, commands, plugins, assembly) | `ontology-evolution` | **Mandatory split**: ontology changes always run through `ontology-evolution`, never `dev-flow` or business Proposals |

## Cross-Layer Hard Constraints

1. **Load on demand, never duplicate rules**: Workflow skills invoke `dev-doc-master`, `space-master`, and `rules/testing.md` when authoring or reviewing docs/rules instead of copying templates or checklists.
2. **One authoritative owner per fact**: PRDs own product intent, Proposals own major decisions & evolution lifecycle, Issues own work within settled decisions, optional `dev-flow`/Plans own complex execution breakdown, Graph owns cross-Plan dependencies, Project/Module DESIGNs own shipped reality and active business rules, and `AGENTS.md` owns operating commands and gates. Partial Proposal work never claims full completion, and one finished Plan does not auto-mark its Proposal `implemented`.
3. **Parallel-safe documentation discipline**: Main `DESIGN.md` headers (Product and Project alike) omit `Sub-DESIGNs` lists; project main `DESIGN.md` stays a thin map with default `DESIGN-<module>.md` splitting; routine module work edits only owned sub-DESIGNs in the authorized write set, reporting out-of-scope drift to the coordinator instead of editing shared docs; never hand-copy volatile code inventories, verify claims against real code/tests/runs, and label untested items explicitly.
