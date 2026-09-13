---
name: ontology-evolution
description: |
  Evolver's quarantine and distillation workflow for turning runtime experience into living capability. Covers friction detection, de-contextualization, the generalization gate, three-tier triage (space-private / type-specific / public core), and the Evolution Plan output format.

  MUST load when:
  - Distilling a session's lessons, errors, or user corrections into lasting capability
  - Deciding where a piece of knowledge belongs (space memory vs type assembly vs central pool)
  - Producing an evolution proposal for user approval
  - Auditing a candidate capability for project-specific contamination before it enters the pool

  This skill is Evolver-exclusive (only the evolver agent can load it). It defines how the evolution heart does its work; the evolver agent file defines who Evolver is.
---

# ontology-evolution

Evolver's workflow for distilling runtime facts into capability, and for guarding the central ability pool against contamination.

The core tension this skill resolves: useful lessons and project-specific noise arrive together. Separating them is the whole job. A lesson that stays local is cheap; a lesson that leaks its context into the pool poisons every space that consumes it.

---

## The Evolution Loop

```
Runtime facts (session events / errors / user corrections)
  → Detect friction worth distilling
  → De-contextualize: strip the specific, keep the general
  → Generalization gate: does this hold beyond this space?
  → Three-tier triage: space-private / type-specific / public core
  → Emit Evolution Plan for user approval
```

You stop at the Evolution Plan. Implementation belongs to Fae, orchestration to Wopal, audit to Rook.

---

## Step 1: Detect Friction

Scan the current session and any supplied runtime facts for signals worth keeping:

| Signal | What it looks like | Why it matters |
|--------|-------------------|----------------|
| Repeated correction | User corrects the same behavior more than once | A rule is missing or unclear |
| Error with a lesson | A failure exposes a wrong assumption | A guardrail should exist |
| Unclear instruction | A workflow step needed clarification | Documentation or routing gap |
| Wasted effort | The same helper or approach rebuilt repeatedly | A capability should be extracted |
| Effective pattern | Something worked notably well | Worth preserving so it recurs |

Not every event is evolution material. Routine task completion is not a lesson. Look for the moment where behavior should have been different.

## Step 2: De-Contextualize

Before a candidate moves toward the pool, strip everything that ties it to this space:

- Absolute paths (`/Users/<name>/...`, `/Volumes/...`) → abstract placeholders or nothing
- Project names, product names, client names → generic terms
- Business domain words that only matter here → removed
- Session-specific IDs, timestamps, commits → removed

The test: could a reader who has never seen this space understand and apply the lesson? If not, it is not yet de-contextualized.

## Step 3: The Generalization Gate

Ask the three questions:

1. **Does this hold in a different space?** If it only holds here, it is space-private.
2. **Does it hold for a different project of the same type?** If yes, it is type-specific.
3. **Is it true for any space of any type?** If yes, it may be public core.

A "maybe" is not a "yes". When uncertain, place it lower in the hierarchy. A local lesson that later proves general can be promoted; a polluted pool is hard to clean.

## Step 4: Three-Tier Triage

| Tier | Destination | Owner | Examples |
|------|-------------|-------|----------|
| **Space-private** | `.wopal-space/memory/` or project `AGENTS.md` | The space | Project-specific architecture rules, local conventions |
| **Type-specific** | `config/types/<type>.yaml` assembly or type-scoped assets | The type | Rules that hold for every coding space but not content spaces |
| **Public core** | Central pool (`agents/`, `skills/`, `rules/`) | The pool | Cross-space principles, general workflows |

Misplacement is the main failure mode. A coding convention placed in public core pollutes content spaces. A general principle buried in one space's memory never benefits anyone else.

---

## Step 5: Emit the Evolution Plan

Your only output is a plan for user approval. Use this structure:

```markdown
# Evolution Plan

## Summary
<one paragraph: what was observed, what should change>

## Candidates

### Candidate N: <short title>
- **Tier**: space-private | type-specific | public core
- **Evidence**: <session fact, error, or correction, with concrete detail>
- **De-contextualized form**: <the generalized statement>
- **Proposed change**: <what asset changes, and how>
- **Generalization basis**: <why this tier, not a lower one>

## Risks
<anything that could make this proposal wrong or premature>

## Recommended Next Steps
<if approved: which asset, in which space, to be implemented by Fae>
```

Keep candidates few and well-argued. Three strong proposals beat ten weak ones.

---

## Boundary

**Read & Propose Only.** You never edit files, commit, run mutating commands, or implement changes. Every proposal waits for explicit user approval. After approval, Wopal orchestrates and Fae implements.

When evidence is thin, say so. A speculative proposal presented as fact is worse than no proposal.

Violating this boundary = **CRITICAL FAILURE**.
