# Proposal analysis and discussion

A request to write a Proposal does not mean the target solution is ready. Resolve important design questions before writing the formal Proposal. When the design is already clear, verify it without repeating questions.

## Investigate the design basis

- Start from the user's goal and current problem. Distinguish the requirement from the user's initial suggested solution.
- Read applicable AGENTS.md, product PRD and architecture DESIGN, project main DESIGN, affected module DESIGNs, companion contracts, and existing glossary if present. Follow binding document relationships upward. Read relevant implemented Proposals, code, and tests to verify material current facts. Scale scope to the impact; do not traverse unrelated modules.
- Identify responsibilities, dependency directions, interfaces, business rules, and invariants that must survive. If the target changes an existing design, name the decision, reason, impact, and surviving constraints for the user to decide. Report evidence of disagreement between implementation and settled design and resolve conflicts material to the target; neither current code nor local convenience authorizes overturning architecture.
- Reuse project design standards and terminology; investigate facts and perform necessary feasibility probes yourself. Mark unverified premises; do not claim design readiness while critical feasibility remains unknown.

## Domain modeling

Domain modeling actively clarifies concepts and rules rather than merely reading vocabulary. As the discussion progresses:

- When a term conflicts with an existing definition, cite that definition, expose the difference immediately, and ask the user to settle its meaning. For an overloaded word, propose precise candidate terms. Does "account" mean a customer identity, a login principal, or a service credential?
- Choose one canonical term per domain concept; note confusing aliases when useful. Define what the concept is in one or two sentences, expressing relationships through other canonical terms. Behavior and implementation belong in design contracts. Focus on project-specific concepts. If multiple domain contexts exist, identify the relevant context and respect existing glossary organization.
- Stress-test relationships, responsibilities, cardinality, state, and lifecycle with concrete scenarios. For example, who determines the valid invoice amount after partial order cancellation? Probe counterexamples until definitions distinguish actual cases rather than merely sounding plausible.
- Check claims about current behavior against code and tests. Surface contradictions explicitly: if code supports only whole-order cancellation but the user describes partial cancellation, distinguish current facts from the intended change.

Capture terms and important decisions as soon as they are settled, rather than waiting for the final synthesis. New definitions and future changes belong in the Proposal specification; maintain present-state DESIGN and any existing glossary under delivery rules. A simple change only needs its relevant concepts clarified, not a separate model file.

## Discuss in dependency-ordered rounds

Build a decision tree: different answers to one decision create, remove, or change downstream questions. Pursue the design until it is settled, rather than finishing a predetermined interview checklist.

1. Identify unresolved decisions affecting product behavior, architecture, interfaces, state, material constraints, or delivery boundaries, and their dependencies. In each round, ask all ready, mutually independent questions whose prerequisites are settled. Questions depending on answers in this round belong to a later round. For larger designs group by topic while preserving dependencies.
2. The agent investigates facts; the user makes design decisions. When a question needs a fact, inspect code, documents, or run a necessary probe. Where delegation is supported, investigate in parallel while discussing independent ready questions. Do not guess at a dependent decision before evidence arrives.
3. Number each question and state its context, real tradeoffs, recommended answer, and reason. Where possible phrase it so that a simple "yes" confirms the recommendation; the user can correct it or choose another path. Only list alternatives when meaningful.

Example round:

> **Q1 — Credential ownership**: Should the account-management module own credentials while callers use account identifiers?
>
> **Recommendation**: Yes. Central ownership keeps permission and update rules consistent.
>
> **Q2 — Historical records**: Should usage history survive account deletion?
>
> **Recommendation**: Yes, retain necessary audit records but revoke active credentials for auditability and safety.

This round assumes the prerequisites are known and the answers are independent. If Q2 depends on Q1, defer Q2.

4. Wait for the user's answers after each round. Identify which decisions are actually resolved; unanswered or ambiguous decisions stay open. Recompute ready questions from the answers, adding newly exposed branches and counterexamples. Test the user's suggested solution against evidence, scenarios, and existing architecture too.
5. Maintain concise design notes each round: settled decisions and necessary rationale, new terminology, open questions and dependencies. For long discussions use a permitted temporary record; write the formal Proposal after discussion closes. Notes are synthesis inputs, not approval or implementation authority.

**Completion criterion**: every decision materially affecting the target is settled; key scenarios and boundaries for each relevant domain have determinate answers; critical feasibility has evidence; material risks have contractual controls or explicit acceptance; no material branch rests on an unstated assumption. Recap the complete design to confirm shared understanding with the user; if they already explicitly confirmed the same conclusions, do not ask again. Then synthesize the specification without making new decisions during writing.

Inspired by [grill-with-docs](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs): decision dependencies, discussion rounds, and domain modeling. This skill remains the owner of formal Proposal writing and approval recording.
