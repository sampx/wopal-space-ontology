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
                          ┌──── Direct delivery (skip dev-flow) ────┐
                          │                                                       ▼
                          └─ Explicit Issue Plan or approved Proposal Delivery: plan (dev-flow Plans + Graph)
                                                                                  │
                                                                                  ▼
                                     df-implement (code + tests → present-state DESIGN → rules at all affected tiers)
                                                                                  │
                                                                                  ▼
                                 df-implement-review (independent review: Proposal target, code/tests, DESIGN, rules)
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
| Create, maintain, or check business/product Proposal lifecycle (`proposals/{proposed,implemented,rejected,archived}/{class}/`) | `dev-proposal` (`/cupdate-proposal`) | Owns approved target, decisions, scope, acceptance and `Delivery: direct \| plan`; maintain explicit user-authorized adjustments in the current Proposal before acceptance; routine bugs use Issues |
| Independent pre-execution review of Proposals or Plans | `df-proposal-review` | Read-only review of decisions, feasibility, Plan coverage of the authorized source, and document quality by document kind; follow df-proposal-review, never edit or substitute for user approval |
| Implementation Plan explicitly chosen for an Issue within settled design, or approved Proposal with `Delivery: plan`; lifecycle of those Plans | `dev-flow` | Only these two Plan routes. Standalone Issue operations, direct delivery, proposal writing and independent reviews do not trigger dev-flow. Complexity or parallelism alone does not authorize a Plan. |
| Execute implementation, automated tests, and delivery sync | `df-implement` + `rules/testing.md` | Respect authorized targets; `direct` starts in an isolated worktree unless the user or controller specifies otherwise. Follow `df-implement`: implement and verify code, synchronize affected present-state DESIGN via `dev-doc-master`, then audit/sync all affected rule tiers via `space-master`; verify applicable delivery gates |
| Independent post-implementation code/test/doc review | `df-implement-review` | Read-only review across the full delivery baseline: target fidelity, code/tests, DESIGN and all affected rules. Apply the severity and concise report contract in `df-implement-review`; never edits files |
| Create, audit, or maintain space/project/docs/module `AGENTS.md`, project `README.md`, or install/scan/remove external skills | `space-master` (`/cupdate-agent-rules`, `/cupdate-readme`) | Generates the unbypassable harness-injected `AGENTS.md` hierarchy (`<project>/AGENTS.md` wiring `Doc sync` + `DESIGN` sync, thin `<project>/docs/AGENTS.md` guardrail card, and on-demand `<dir>/AGENTS.md`); enforces zero parent-child duplication, non-empty +/- gate verification, and read-only legacy `BUSINESS_RULES.md`; does not author PRDs or DESIGNs |
| Modify ontology capability assets (skills, rules, agents, commands, plugins, assembly) | `ontology-evolution` | **Mandatory split**: ontology changes always run through `ontology-evolution`, never `dev-flow` or business Proposals |

## Cross-Layer Hard Constraints

1. **Load on demand, never duplicate rules**: Workflow skills invoke `dev-doc-master`, `space-master`, and `rules/testing.md` when authoring or reviewing docs/rules instead of copying templates or checklists.
2. **One authoritative owner per fact**: PRDs own product intent, Proposals own the authorized implementation target, decisions, scope, acceptance and lifecycle, Issues own work within settled decisions, optional `dev-flow`/Plans own complex execution breakdown, Graph owns cross-Plan dependencies, Project/Module DESIGNs own shipped reality and active business rules, and rules at each applicable tier own durable working constraints and gates. Partial Proposal work never claims full completion, and one finished Plan does not auto-mark its Proposal `implemented`.
3. **Parallel-safe documentation discipline**: Main `DESIGN.md` headers (Product and Project alike) omit `Sub-DESIGNs` lists; project main `DESIGN.md` stays a thin map with default `DESIGN-<module>.md` splitting; routine module work edits only owned sub-DESIGNs in the authorized write set, reporting out-of-scope drift to the coordinator instead of editing shared docs; never hand-copy volatile code inventories, verify claims against real code/tests/runs, and label untested items explicitly.
