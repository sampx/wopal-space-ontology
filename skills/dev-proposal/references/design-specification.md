# Target design specification

A Proposal is the target authority for the approved change, not a research report or implementation task list. Determine the design, leave implementation free: independent implementers should derive materially equivalent designs from the Proposal and its referenced constraints without choosing unauthorized product or architectural alternatives.

## Design basis and target

In Design Basis, reference applicable authoritative documents and relevant sections, summarize inherited constraints and explicitly identify changed existing decisions if any; do not copy their text. If no higher-level design exists, state that fact and the current constraints relied upon. A new target differing from current behavior is expected; design outside the approved change remains binding. Applicable engineering rules remain in force after approval.

Organize the Proposal around actual domain concepts, using bespoke sections rather than a fixed technical outline. State scope, user scenarios, and material design constraints. Reference unchanged contracts; define new or changed contracts and how they fit the existing system. File lists, class names, and task lists are not design substitutes.

## Contract coverage

Reuse the five-point coverage method in dev-doc-master's design-project-guide.md, describing the target rather than claiming delivery. For every important capability or flow, determine applicable aspects:

- Actors, triggers, inputs, and preconditions.
- Module responsibilities, collaboration sequence, interface inputs/outputs, and dependency direction.
- Permissions, business rules, defaults, limits, invariants, and material branches.
- Data, state ownership, lifecycle, and side effects.
- Complete failure outcomes, partial success, recovery, and compatibility behavior.

For non-behavioral design, select relevant guidance in design-practices.md. Do not require irrelevant headings or exhaustive code details. Use terms consistently with existing DESIGN and any glossary; define new or changed terms in the target design.

## Important design decisions and risks

Design Decisions is optional: record final choices and reasons only for important product, architecture, business, or interaction decisions that need lasting context (for example, hard-to-reverse choices with non-obvious rationale and genuine tradeoffs). Mention rejected alternatives only when they explain the decision or prevent repeating a tempting mistake; they are not target design options. Do not duplicate the specification or the entire discussion.

Resolve risks during discussion: fix avoidable risks in the design; make mitigations concrete design contracts covered by acceptance; verify critical feasibility; explicitly document material residual risks, costs, and controls in the design or decision rationale for user acceptance. Omit resolved analysis that no longer informs future judgment. No separate risk section is required.

## Acceptance and self-check

Cover every important new or changed contract and affected existing invariant, including real entry points, successful behavior, material failures, state effects, and architectural constraints. Each criterion is observable or inspectable and lets a third party judge met or unmet. Exact test commands need not all be settled at proposal time; file existence or a restatement of the goal does not prove behavior.

Compare the finished specification against every settled material decision and discussion record: no omissions, weakened requirements, unauthorized expansion, or invented decisions. Simulate an independent implementer: would they still need to decide important responsibilities, interfaces, state, or behavior? If so, return to discussion. Check the design basis, terminology, completeness, risk controls, and acceptance coverage; resolve contradictions before independent review. Self-check is not independent review or user approval.
