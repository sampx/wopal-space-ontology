---
name: ontology-evolution
description: Ontology capability evolution — semantic lane (Maka) plus mechanism lane (state machine, sparse isolation, delivery terminal)
---

# Agent Development Rules

## 1. Canonical References

- Parent Rules: `.wopal/AGENTS.md`
- Skill entry: `SKILL.md`
- Command contract: `references/commands.md`
- Design source of truth: `docs/DESIGN-evolution.md`

## 2. Architecture and Directories

| Directory | Responsibility |
|---|---|
| `templates/proposal.md` | The proposal skeleton with authoring comments; the single source of the proposal format |
| `references/` | Command reference and background |

Sparse state is written **only** through the `wopal space` command family. A
direct `git add -A`, `git checkout`, or `git sparse-checkout` call is how the
range and the index drift apart unnoticed.

## 3. Implementation Rules

### State Machine

`draft -> accepted -> implementing -> validating -> archived`

The vocabulary deliberately shares no words with `dev-flow`'s
(`planning / reviewing / approved / executing / verifying / done`). Changing a
state name is a contract change: it must be updated here, in
`docs/DESIGN-evolution.md`, and in `references/commands.md` together.

`Stage` is written only by the `wopal space evo` commands — never hand-edit
the field; a proposal whose field cannot be found cannot be advanced. Command
preconditions and refusal semantics belong to the CLI mechanism
(`projects/wopal-cli/docs/DESIGN-evolution.md`).

### Defect Repairs Are Immediate

A defect — existing, already-agreed behavior that is wrong — is repaired
directly with `wopal space evo commit` in **instant mode** (no proposal name),
committed on the space branch. It does not go through the proposal lifecycle:
the review a proposal exists to provide is already settled for behavior that
was agreed. The safety contract (sparse preflight, widen-then-stage, named
staging) still applies. Instant mode is the designed repair path — a separate
`fix` command was retired on purpose and must not be reintroduced, not even as
an alias or a shim. Anything that changes agreed behavior is an evolution and
uses the proposal lifecycle.

### No Automatic Delivery

`space sync` and `ontology contribute` are the user's terminal decision
(`docs/DESIGN-evolution.md`, Delivery Terminal). No part of this skill may
invoke a delivery CLI, add a remote, or push — the absence of an automatic
upstream path is by design, not by omission.

### Test Discipline

These rules apply to tests for whatever implementation owns the behavior
(the CLI mechanism today):

**R1 Behavior assertions only.** A test asserts an input to output mapping:
exit code, file content, printed result. Asserting internal call sequences,
which branch ran, or searching source text for strings is forbidden — the
implementation must stay rewritable without breaking the test.

**R2 Filesystem isolation.** A test that touches the filesystem works in a
temporary directory — never inside the shipped skill directory or the live
ontology; a test's footprint ends with it.

**R3 One case per behavior.** Same-shaped cases are parametrized or looped —
never copy-pasted.

**R4 Red-green law.** A new test must first fail against the missing behavior.
A test that cannot fail is decoration.

**R5 No implementation coincidence.** Assert the contract, not incidental
detail such as internal function names.

## 4. User-Supplied Rules

(None)
