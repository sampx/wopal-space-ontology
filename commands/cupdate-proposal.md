---
description: Create, approve, migrate, or archive Proposals
---

# Create, Approve, Migrate, or Archive a Proposal

Create or maintain one business/product Proposal through its lifecycle, or triage a change to an already-implemented Proposal. This command is a thin entry: the contract lives in the `dev-proposal` skill.

**Input**: `$ARGUMENTS`

**Parameter Notes**: A proposal path, a topic to look up, or a short request. When the target is not named, locate the owning `proposals/` root by matching `docs/products/*/proposals/` and `projects/*/docs/proposals/`; ask the user when the owner is unclear.

---

## Core Principles

- A Proposal records a decision, not progress. No `implementing` / `verifying` / `done` states, no task tables.
- Only the user approves and only the user chooses `Delivery: direct | plan`; a passing format check never proves approval.
- Never rewrite an `implemented/` decision in place. Facts sync in place; a decision change needs a new `proposed/` proposal.

## Step 1: Load the contract

Load the `dev-proposal` skill and follow its workflow. Do not restate the layout, state machine, or skeleton rules here.

**Output**: The loaded contract for this task.

## Step 2: Establish the ownership and the starting point

Find the owning root (`docs/products/{product}/proposals/` or `projects/{project}/docs/proposals/`) and audit for existing proposals on the same topic. If a matching `implemented/` record exists, decide between fact-only sync, partial supersession, and full replacement before writing anything.

**Output**: The target path and the triage outcome.

## Step 3: Do the work

Draft, record approval, migrate, reject, archive, or triage, using the skill's skeleton templates.

**Output**: The proposal file changed as the requested step requires.

## Step 4: Verify

```bash
python3 <dev-proposal-skill-dir>/scripts/verify-proposals.py <proposals-root> --link-scope <docs-root>
```

Exit 0 before reporting done. A non-zero exit lists each problem with a fix hint.

**Output**: Verifier result.
