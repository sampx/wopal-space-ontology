# Domain glossary

## Role and scope

Use `GLOSSARY.md` in the owning product or project's documentation directory when recurring domain vocabulary has cross-document value or ambiguity. It is optional; a small design can define its local terms in its owning DESIGN. Declare an existing glossary as a binding companion in the owning main DESIGN or PRD's `Companion Documents` header. A product-level term is inherited by projects; a project glossary adds only local concepts or explicitly scoped meanings. Do not create a duplicate dictionary per module.

## Definition quality

- One canonical name per concept within its context. Use the domain's language, not generic programming vocabulary. If the same word legitimately means different things in different contexts, qualify each scope and name the distinction.
- Define what the concept is in one or two concrete sentences. Use other canonical terms to express necessary conceptual relationships and cardinalities; use a relative link to the owning contract for behavior, permissions, state transitions or algorithms.
- Record confusing aliases only when they actually occur; mark the preferred name. Do not invent prohibited synonyms, force translation of identifiers, or confuse a code type with a domain concept.
- Example: **Subscription** — A customer's agreement for access to a plan during a defined period. A subscription belongs to one customer. Avoid **Account** when referring to the agreement. Billing, renewals, and cancellation behavior belong in the owning DESIGN.

## Maintenance and verification

Read existing vocabulary, owning design, applicable higher-level glossary, and relevant code/tests before defining terms. Expose competing meanings and resolve actual product decisions with the user; do not silently rewrite domain semantics. Keep target definitions in the Proposal until corresponding behavior is delivered and verified; clarify an existing meaning directly when evidence supports it. Product documents may describe product intent, but do not present proposed project meanings as active definitions. Update affected glossary entries, references and consuming DESIGN prose in the same authorized delivery. The coordinator owns shared vocabulary changes and any new companion header in parallel work. Never link to transient proposed/rejected records from the glossary.

Review canonical names, scope, definition uniqueness, consistency with inherited vocabulary and owning design, evidence for active meanings, and absence of duplicated behavior contracts. Use the existing docset gate for structural checks; semantic review determines whether terms are accurate and necessary. A glossary does not require DESIGN-specific sections or five-point behavior coverage. See `templates/glossary.md`.
