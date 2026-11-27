# Design analysis and discussion

A request to write a Proposal does not mean the design is ready. Resolve important design questions before writing the formal Proposal. When the design is already clear, verify it without repeating questions.

## Investigate the design basis

- Start from the user's goal and current problem. Distinguish the requirement from the user's initial suggested solution.
- Read applicable AGENTS.md, product PRD and architecture DESIGN, project main DESIGN, affected module DESIGNs, companion contracts, and existing glossary if present. Follow binding document relationships upward. Read relevant implemented Proposals, code, and tests to verify material current facts. Scale scope to the impact; do not traverse unrelated modules.
- Identify responsibilities, dependency directions, interfaces, business rules, and invariants that must survive. If the target changes an existing design, name the decision, reason, impact, and surviving constraints for the user to decide. Report evidence of disagreement between implementation and settled design and resolve conflicts material to the target; neither current code nor local convenience authorizes overturning architecture.
- Reuse project design standards and terminology; investigate facts and perform necessary feasibility probes yourself. Mark unverified premises; do not claim design readiness while critical feasibility remains unknown.

## Domain modeling

Identify material concepts, meanings, relationships, responsibilities, state owners, and business constraints for the actual design. Use consistent terms. Challenge ambiguous or competing terms, overlapping responsibilities, and conflicts with code or documents. Test the model with concrete happy, failure, and boundary scenarios; explore conditions that would change the design. A simple change needs no separate domain model.

Record new or changed term definitions in the target design first. Do not pre-write undelivered changes into present-state DESIGN or an existing glossary.

## Discuss in dependency-ordered rounds

1. Identify decisions affecting product behavior, architecture, interfaces, state, material constraints, or delivery boundaries. Order by dependencies; resolve decisions that govern downstream branches first.
2. Ask only questions whose prerequisites are settled and which are independent of each other. Batch independent questions in one round. For each, state the decision, viable tradeoffs, recommended answer, and reason. Resolve facts from evidence or settled authorization yourself; leave code-level choices to implementers.
3. After each round, update decisions and revisit downstream questions, edge cases, and contradictions. Do not re-ask settled questions. Test the user's suggested solution against evidence, scenarios, and existing architecture too.
4. Record settled decisions, necessary reasons, related terms, and remaining questions each round. For long discussions, maintain a permitted temporary note or unapproved draft to prevent context loss. Notes are not approval or implementation authority; do not carry discussion logs into the final Proposal.
5. Stop discussing and write the specification when all decisions materially affecting target design are settled, critical feasibility is verified, and major risks are converted into constraints or explicitly accepted. Resolve remaining material questions with the user rather than substituting guessed defaults or vague prose.

Inspired by [grill-with-docs](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs): decision dependencies, discussion rounds, and domain modeling. This skill remains the owner of formal Proposal writing and approval recording.
