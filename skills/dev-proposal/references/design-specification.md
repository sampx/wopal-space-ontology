# Target design specification

A Proposal is the target authority for the approved change, not a research report or implementation task list. Determine the design, leave implementation free: independent implementers should derive materially equivalent designs from the Proposal and its referenced constraints without choosing unauthorized product or architectural alternatives.

## Design basis and target

In Design Basis, reference applicable authoritative documents and relevant sections, summarize inherited constraints and explicitly identify changed existing decisions if any; do not copy their text. If no higher-level design exists, state that fact and the current constraints relied upon. A new target differing from current behavior is expected; design outside the approved change remains binding. Applicable engineering rules remain in force after approval.

State the problem and target outcome from the user's perspective: who needs to accomplish what, why it matters, and what success looks like. Enumerate affected usage scenarios with actor, goal, prerequisites, normal path, variants, and material failure paths; cover every materially distinct user need rather than a couple of representative examples. Use role-goal-value stories or Given/When/Then when they expose omissions; no separate stories heading is required.

Organize the Proposal around actual domain concepts with bespoke sections rather than a fixed technical outline. State delivery boundaries, deliberate exclusions, and preserved behavior. Reference unchanged contracts; specify new or changed contracts and their system relationships, including settled modules, interfaces, architecture, data structures, interactions, and rules. Keep technical details only where they determine the design: source paths locate evidence or authority, not a fixed target file inventory; class, function, and task lists cannot replace design. If a state diagram, data shape, interface signature, or short prototype fragment expresses a contract more precisely than prose, include just the decision-bearing part and identify its origin; the prototype is not the implementation.

## Contract coverage

Load the five-point coverage standard in `dev-doc-master/references/design-project-guide.md` and apply it to each material target capability and flow without claiming delivery. Use `design-practices.md` for applicable domain-specific details, not mandatory headings. Follow existing DESIGN and glossary vocabulary; define changed terms in the target.

## Important design decisions and risks

Design Decisions is optional. Record separate rationale only when all three conditions hold: changing the choice has meaningful cost; a future reader would find it puzzling without context; real alternatives were weighed. State context, final choice, and reason in one to three sentences. Include discarded options only when they explain the choice or prevent a tempting mistake, and consequences only when material and non-obvious. The choice itself belongs in the target design; omitting an ADR-style record never omits a material contract.

Resolve risks during discussion: fix avoidable risks in the design; make mitigations concrete design contracts covered by acceptance; verify critical feasibility; explicitly document material residual risks, costs, and controls in the design or decision rationale for user acceptance. Omit resolved analysis that no longer informs future judgment. No separate risk section is required.

## Verification design

Before finalizing the specification, determine where and through what observable results to verify the target. Inspect existing test entry points and precedent for similar scenarios; prefer established interfaces, fixtures, and test mechanisms. Choose the lowest-cost test layer that fully proves the contract, favoring behavior observable through actual public interfaces over private call counts or implementation structure. Local mocks alone cannot establish a contract requiring real cross-module collaboration. Follow applicable testing rules rather than mechanically equating highest-layer testing with the best test. Confirm with the user only verification choices that themselves affect product, architecture, delivery cost, or user acceptance; implementation can settle concrete test files and commands.

Cover every important new or changed contract and affected existing invariant, including real entry points, successful behavior, material failures, state effects, and architectural constraints. Each criterion is observable or inspectable and lets a third party judge met or unmet. Ask whether an implementation violating the contract would reliably fail this check. Criteria need not map one-to-one to test functions, but every material behavior needs a way to prove it. File existence or a restatement of the goal does not prove behavior.

## Specification self-check

Writing synthesizes settled conclusions, not new design choices. Reconcile the specification against confirmed decisions and discussion notes: every material decision has an explicit location in the body or a valid authority reference; every critical contract has acceptance coverage; unchanged architectural constraints and deliberate exclusions remain intact. Use determinate, affirmative, concrete target-state prose: who owns what, under which conditions, with what result. Use examples or condition tables where abstract phrasing admits different interpretations.

Simulate an independent implementer who was not in the discussion: reading only the Proposal and referenced documents, can they derive materially equivalent responsibilities, interfaces, state, and behavior? If an answer affecting the design still needs guessing, return to discussion rather than inventing a default. Resolve omissions, weakened requirements, unauthorized expansion, terminology conflicts, risk controls, and unfalsifiable acceptance before independent review. Self-check is not independent review or user approval.
