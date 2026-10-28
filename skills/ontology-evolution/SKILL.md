---
name: ontology-evolution
description: >
  MUST use this skill for any work that may change or maintain reusable WopalSpace capabilities: user corrections, recurring friction, tool/environment failures, reusable lessons, evolution proposals, capability assets, space/ontology synchronization, assembly changes, or upstream contributions. Load it even when the user never says “ontology” or “evolution” if deciding whether a session lesson should become reusable capability or modifying ontology capability assets. Use `dev-flow` for code development under `projects/`.
---

# ontology-evolution

Turn real work friction into reliable signals, mature signals into lasting capability, and land improvements safely.

The main flow is **observe → diagnose → route → synthesize → propose → land**. This file keeps only decisions and the main workflow; load references on demand for landing, command, and maintenance detail.

## Core contract

- Find the existing capability owner first and prefer repairing it; create a new capability only when no existing owner fits naturally.
- A proposal is not implementation authorization. Every proposal waits for explicit user approval before landing.
- The user owns three terminal gates: **approval, validation, and delivery**.
- Wopal orchestrates and records; Fae implements; Rook reviews implementation; Maka observes, analyzes, and proposes.

## Roles

| Role | Owns | Does not own |
|------|------|--------------|
| **Maka** | Observe signals, accumulate evidence, synthesize mature issues, write proposals when requested | Write proposals during observation; edit capability assets; land changes |
| **Wopal** | Detect signals, keep the primary task moving, trigger synthesis; orchestrate landing after approval | Interrupt the primary task for Maka's intermediate analysis; implement in place of Fae |
| **Fae** | Modify capability assets in the assigned workspace and verify the implementation | Commit; edit proposals; advance stages |
| **Rook** | Review implementation before user validation | Fix findings |
| **User** | Approve proposals, choose and perform validation, decide integration and delivery | — |

---

# Continuous session evolution

## What is worth observing

Treat an event as an evolution signal only when it may mean **a capability should behave differently the next time a similar situation occurs**. Typical sources:

- The user corrects an Agent's judgment, behavior, workflow, or communication.
- The same detour, bad assumption, or repeated work recurs.
- A tool / environment failure exposes a stable wrong assumption.
- A known lesson still has no stable capability owner.
- A new approach clearly outperforms the current one and is worth reusing.

An ordinary project bug, one-off network failure, or task-specific business fact is not automatically an evolution signal just because something went wrong.

## How Wopal collaborates with Maka

When the runtime supports sub-agent collaboration:

1. **Start on demand and reuse.** Prefer one Maka child thread per logical session.
2. **Send only necessary evidence.** Give the problem, user correction, key context, failure result, or effective pattern; do not copy the full parent history by default.
3. **Keep the primary task moving.** After sending a signal, Wopal continues the current work, does not wait for Maka, and does not surface intermediate analysis to the user.
4. **Synthesize at closeout.** When the main task is complete, the session is winding down, or the user explicitly asks for an evolution summary, Wopal asks Maka to `synthesize`.

If no usable sub-agent collaboration exists, Wopal may perform the same synthesis once at closeout; do not add persistence machinery merely to imitate a background Maka.

## Maka's observation and synthesis modes

### Observation

Maka only diagnoses, classifies, and accumulates evidence; it does not create proposals:

| State | Meaning |
|-------|---------|
| `discard` | One-off, already covered correctly, or not reusable |
| `local` | Valuable, but only for the current project / space |
| `candidate` | May need a capability change, but evidence or ownership is not stable yet |
| `mature` | Evidence is strong enough to consider a capability change during synthesis |

`mature` does not mean “write a proposal now.” Observation exists to reduce noise, merge duplicates, and strengthen evidence.

### Synthesis

Only when Wopal explicitly requests `synthesize`, Maka:

1. Merges same-root / duplicate signals and drops weak evidence or issues already covered by existing capability.
2. Generalizes mature signals and checks for private contamination.
3. Finds the capability owner before deciding whether to repair or create capability.
4. Writes proposals only for coherent changes that still hold after synthesis; **zero proposals is a valid result**.

## Capability routing

| Problem essence | Preferred owner |
|-----------------|-----------------|
| An Agent's role, responsibilities, decision principles, or long-lived default behavior is wrong | Agent prompt |
| A behavior constraint applies only in a matching scenario | Rule |
| The problem is how work is performed: workflow, steps, verification, or tool use | Skill |
| A fixed human-to-Agent work entry or instruction contract needs to change | Command |
| A real tool, runtime state, automation, or system integration is missing | Plugin / runtime owner |
| The capability is fine, but a space type should or should not receive it | Assembly / archetype |
| The knowledge is specific to the current project or space | Project `AGENTS.md` / space memory |

When ownership overlaps, the boundary is unclear, or a formal proposal is about to be written, read [`references/capability-routing.md`](references/capability-routing.md). Read the relevant DESIGN only when the issue challenges the capability model, loading lifecycle, or architectural ownership.

---

# Writing an evolution proposal

The point of a proposal is not to archive what happened; it is to make the same kind of situation go better next time.

## Generalize first

- Remove absolute paths, project / product / customer names, session ids, timestamps, commit hashes, and other local detail.
- Keep evidence and constraints that actually determine capability behavior.
- Test: a reader who has never seen this space can still understand and apply the change.

## Decide where it belongs

| Tier | Destination | Fits when |
|------|-------------|-----------|
| **Space-private** | `.wopal-space/memory/` or project `AGENTS.md` | It only holds in this space / project |
| **Type-specific** | Type assembly or type-scoped assets | It holds for spaces of this type, not for others |
| **Public core** | Central capability pool such as `agents/`, `skills/`, `rules/` | It holds for any space |

Ask in order: does it hold in another space? Another project of the same type? Any space? When uncertain, place it lower.

## Write it

Use `wopal space evo new "<title>"` to create `docs/evolutions/<name>.md` from `templates/proposal.md`, then fill the template completely.

- Write in the user's preferred language; preserve the template headings and field labels.
- Preserve the primary target capability's canonical name; prefer a short, recognizable 2–3 segment `<capability>-<topic>` slug.
- Anchor every material claim in evidence; mark unverified statements as unverified.
- Keep one coherent change per proposal; few and strong beats many and weak.

Once written, the proposal waits for the user to read it. Landing begins only after approval.

---

# Landing an approved proposal

The state machine is fixed:

```text
draft → accepted → implementing → validating → archived
```

Its vocabulary is deliberately different from `dev-flow`; do not mix or “unify” them. Review is not a stage: it is a mandatory gate inside `implementing`, before the user is invited to validate.

## Main flow

1. The **user approves** the proposal.
2. **Wopal** runs `accept`, then enters `implementing`.
3. **Fae** implements; it does not commit or edit the proposal.
4. **Wopal** verifies each task, backfills the record, and lands that task's asset changes and record in one commit.
5. **Rook** performs implementation review; findings are reworked and re-reviewed while still in `implementing`.
6. After review passes, **Wopal** enters `validating` and lets the user choose validation form; recommend branch switch first, use integrate-first only on explicit user choice.
7. The **user** validates and confirms the result; integration happens only after an explicit go.
8. **Wopal** archives; `space sync`, upstream PR publication, and deletion remain separate user decisions.

Before landing, read [`references/landing.md`](references/landing.md). For concrete command arguments, refusal conditions, or sparse-worktree mechanics, then read [`references/commands.md`](references/commands.md).

## Defect repair vs evolution

- **Defect**: agreed behavior is implemented incorrectly → use `wopal space evo commit` in instant mode; no proposal.
- **Evolution**: add capability, change a contract, or change how future work should behave → use the proposal lifecycle.
- When the distinction is unclear, do not silently choose the fast path.

---

# Maintaining ontology and space capabilities

This skill also owns the maintenance entrypoint for ontology / space status, synchronization, capability assembly, and upstream contribution.

- For `space status/sync`, `ontology status/sync`, capability add/remove, or upload-gate work, read [`references/maintenance.md`](references/maintenance.md).
- Before creating, revising, retrying, or closing an upstream PR, also read [`references/contribution.md`](references/contribution.md).
- Synchronization authorization does not authorize PR publication, merge, or deletion; each remains a separate user decision.

---

# Boundaries

- **Maka writes proposals only.** Its write scope is `docs/evolutions/`; it never edits capability assets.
- **Wopal orchestrates, Fae implements, Rook gates.** Nothing uploads or publishes automatically.
- `/wopal:evolve` and `/wopal:distill` belong to the memory-evolution loop; if distilled memory calls for ontology change, it still enters this workflow.
- `wopal/ontology-maintain` is only a thin trigger for this skill; it does not define another protocol.
- Implement capabilities in the assembled `.wopal` worktree or derived isolation; upstream publication uses a separate contribution worktree.

# References

- Capability ownership and routing boundaries: `references/capability-routing.md`
- Proposal landing workflow: `references/landing.md`
- `wopal space evo` command contract: `references/commands.md`
- Ontology / space maintenance: `references/maintenance.md`
- Upstream PR creation, revision, and closeout: `references/contribution.md`
- Proposal template: `templates/proposal.md`
- State-machine design: `docs/DESIGN-evolution.md`
- Assembly / sparse-isolation background: `docs/DESIGN-distribution.md`
