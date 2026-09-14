# BUSINESS_RULES Reference — Business Rule Authoring

Create or update a project-level `BUSINESS_RULES.md`: the single source of truth for a product's business rules. Template: `templates/business-rules.md`.

## What a Business Rule Is

A business rule is a stable, testable domain constraint that holds independent of implementation details. Requirements say "what to do"; rules say "how to compute it correctly".

**A business rule**: "a password must be at least 6 characters". **A technical rule**: "hash passwords with bcryptjs". Technical rules belong in `AGENTS.md`.

Content that is not a business rule:

- Coding conventions, naming conventions, indentation style.
- Architectural constraints and tech stack choices.
- Test isolation strategy and CI/CD configuration.
- Log formats and error-handling patterns.

## Document Scope

`BUSINESS_RULES.md` lives at `projects/<project-name>/docs/BUSINESS_RULES.md` — one per project. It is a **companion document**, not a sub-design: it does not decompose a main DESIGN chapter, so it carries no `Parent` link and is declared in the main design's `Companion Documents` field.

## Header

```
# Business Rules — <Product Name>

> **Status**: Active
> **Updated**: YYYY-MM-DD
> **Companion**: `./DESIGN.md`（业务规则所属的设计文档集）
> **Scope**: 业务规则的单一真相源。技术规则归 `<AGENTS.md 路径>`。
```

`Status` and `Updated` follow the universal document rules. `Companion` names the design document set this file belongs to — the field asserts membership, not a parent-child lineage, which is why a companion document uses it instead of `Parent`.

## Body Format

Rules are grouped by domain under `##` headings. Each rule is a `###` heading in the form `BR-NNN Rule Name \`status\``, followed by a 1-3 line description in business language.

```markdown
## <Domain>

### BR-001 <Rule Name> `active`
<1-3 line rule description, in business language. Not bound to code paths.>

### BR-002 <Rule Name> `planned`
<same as above>
```

Hard requirements:

- One `###` heading per rule, formatted `BR-NNN Rule Name \`status\``.
- Status values: `active` (implemented), `planned` (in design), `deprecated` (retired).
- Description is 1-3 lines, in business language, not bound to code paths.
- Numbering is continuous across domains and globally incrementing; deprecated numbers are never recycled.
- Domain information lives in the `##` heading grouping, never encoded into the BR identifier.

Headings stay English (the universal language rule); rule names and descriptions follow the document language.

## Creating a Document

1. Confirm the target project and read its `DESIGN.md`, data model documentation, and service-layer code. Never invent rules.
2. Extract candidate rules: which constraints must hold true, and which judgments can be tested independently?
3. Atomicize — one rule carries one constraint. Merge duplicates and split composite rules.
4. De-technicalize — remove implementation details such as function names and file paths, keeping the business semantics.
5. Mark status: implemented in code → `active`; described only in documentation → `planned`.
6. Group by domain and write the document from the template.

### Source Priority

| Priority | Source | Extraction Strategy |
|---|---|---|
| 1 | `PRD.md` / `DESIGN.md` | Extract atomic rules from system positioning and functional constraints |
| 2 | Data model documentation | Extract from field constraints, relationship rules, and state machines |
| 3 | Service-layer code | Reverse-infer from constants, branching conditions, and guard conditions |
| 4 | Shared constants | Extract from enum definitions and comments |

### Common Code Patterns

| Code Pattern | Corresponding Business Rule |
|---|---|
| Constants `MAX_*`, `LIMIT_*` | Numeric upper bound constraint |
| `if (status === "completed") return error` | State-machine transition constraint |
| `role >= ROLE.ADMIN` | Permission judgment rule |
| `score >= 6 ? correct : incorrect` | Scoring threshold rule |
| `.split(/[、，]/)` | Data format or splitting rule |

## Updating a Document

1. Refresh `Updated`.
2. Add a new rule under its domain with the next free number, always at the end of the global sequence.
3. Revise a rule's description in place when the business semantics change; keep its number.
4. Retire a rule by marking it `deprecated` rather than deleting it — the number stays reserved and code comments referencing it stay resolvable.
5. Promote a `planned` rule to `active` once the implementation exists, and verify the description still matches what the code does.
6. Re-check the document set: a rule change driven by a DESIGN change means the DESIGN is the source of that change, so confirm the two still agree.

## Code Reference Convention

Mark rule references in code with `@BR-NNN` comments:

```typescript
// @BR-003 评级升降判定
if (correctCount >= thresholdUp) {
  newLevel = Math.min(currentLevel + 1, 8);
}
```

- Place the comment above the code block where the rule takes effect.
- One comment per reference.
- Mark core rules; auxiliary code stays unannotated.

## Quality Checklist

- [ ] Header uses `Companion`, not `Parent`
- [ ] `Updated` date is current
- [ ] One `###` heading per rule, in the `BR-NNN Rule Name \`status\`` form
- [ ] Every status is one of `active` / `planned` / `deprecated`
- [ ] Numbering is globally continuous; no number is reused
- [ ] Descriptions are 1-3 lines of business language, free of code paths and function names
- [ ] Domains are expressed as `##` groups, never embedded in the BR identifier
- [ ] Headings are English; body follows the document language
- [ ] Technical rules live in `AGENTS.md`, not here

## End Section

The document closes with a `## Reference Documents` section carrying reference-only material — typically the `AGENTS.md` that owns the technical rules, and the design documents the rules were extracted from. Header links and end links stay disjoint.
