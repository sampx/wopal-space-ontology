# Design practices by domain

Select relevant domains for the actual change; combine them when needed. This table gives the minimum considerations for analysis and target specification, not a mandatory outline. Omit inapplicable aspects. Project-specific standards and higher-level design take precedence; general requirements are in design-specification.md.

| Design object | At least consider and specify applicable aspects |
|---|---|
| Product feature | Users, goals, end-to-end scenarios, feature boundaries, business rules, defaults, failure feedback, and observable outcomes |
| UI / UX | Information architecture, page or component ownership, interaction and navigation, loading/empty/error/success states, accessibility, responsiveness, and existing design system where applicable |
| Backend service | Module ownership, call/data flow, interfaces, state owners, concurrency and consistency, authorization, failures, and observable behavior |
| API / SDK | Callers, interface semantics, inputs/outputs and constraints, defaults, authentication/authorization, errors, lifecycle, retries or idempotency, compatibility and versioning |
| CLI | Command purpose, arguments and defaults, input sources, output and exit codes, state side effects, noninteractive behavior, failure and recovery |
| Architecture refactor | Current and target responsibilities and dependencies, key collaboration, migration boundaries, preserved behavior and contracts, replacement cleanup, and transition risks |
| Data and storage | Data model and ownership, uniqueness and invariants, reads/writes and transactions, concurrency, retention/deletion, migration, recovery, and consistency |
| Workflow | Roles and permissions, inputs/outputs, states and transition conditions, step order, approval ownership, failure/interruption/reentry, and recovery |
| Testing | Behaviors and risks to prove, verification boundaries, test layers, environment/data isolation, quality gates, and failure diagnosis |
| Agent or automation capability (within a project) | Triggers, responsibilities and authority, inputs/outputs, decision rules, tools and state, failures and recovery, verification scenarios |

Choose details that materially affect behavior or architecture. For example, CLI design defines error exits and failure state, not just command names; UI design defines feedback after actions, not just pages; refactoring defines preserved behavior and ownership transfer, not just a module diagram. Use concrete scenarios and inspectable constraints to remove ambiguity without designing hypothetical future extensions.
