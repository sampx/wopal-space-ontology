# Proposal Lifecycle, Fields, and Migration

`SKILL.md` gives the state-machine outline; this file supplies the complete fields, migration checklists, and judgement rules for each step. Read it when you need the exact move.

## 1. Root and ownership

A Proposal belongs to **one** root:

| Owner | Root | Applies when |
|---|---|---|
| Product | `docs/products/{product}/proposals/` | The decision shapes product positioning, capability boundaries, or a convention shared across projects |
| Project | `projects/{project}/docs/proposals/` | The decision affects a single project or some of its modules |

One decision, one home. A cross-project decision with a clear owner lives in the leading project's `proposals/`, and other projects link to it relatively. Never keep two copies.

Ontology capability-evolution proposals are not in scope: they live in the ontology repository's `docs/evolutions/` and belong to `ontology-evolution`.

## 2. Paths

```text
<proposals-root>/{lifecycle}/{class}/yyyy-mm-dd-<slug>.md
```

- `lifecycle ∈ {proposed, implemented, rejected, archived}`
- `class ∈ {feature, bug-fix, simplification, architecture, process, testing}`
- The date is the **first-proposed** date. Migration and archiving never rename the file.
- The slug is lowercase kebab-case, 2–4 words, naming the decision rather than the document type.
- No status or version suffix (`-v2`, `-approved`, `-final`).

### Forbidden

| Forbidden | Why |
|---|---|
| Singular `proposal/` directory | Sitting next to `proposals/` creates two sources of truth |
| Unknown class directories (`refactor/`, `misc/`, `other/`) | Classification is enforced by a closed set; invented classes make search unreliable |
| Centralized `INDEX.md` | It duplicates the path metadata and makes every unrelated change contend over one file |
| `.i18n.yaml` bilingual triplets | This space does not pair languages; one decision, one language |
| `archived/implemented/` nesting | Only implemented records are archived; the level is implied |

Existing pre-format files stay read-only compatible: read them, cite them, copy their structure if useful, but do not rewrite them to "unify the format", and do not treat them as failures of the current check.

## 3. Header

```markdown
# <Title>

Status: proposed

- **Class**: architecture
- **Created**: 2026-11-22
- **Updated**: 2026-11-22
```

`Status` stands on its own line before the first body section, prefixed exactly `Status: `, and a file carries exactly one: two status lines mean two claims about the same record, which the verifier rejects. The verifier uses that line to cross-check lifecycle against directory. `Class` and `Created` are required on every formatted file — without `Class` the class-versus-directory check has nothing to compare, and `Created` is the date the topic was first proposed.

### Allowed values per directory

| Directory | Allowed `Status` |
|---|---|
| `proposed/` | `proposed`, `approved` |
| `implemented/` | `implemented` |
| `rejected/` | `rejected — <one-line reason>` |
| `archived/` | `implemented` (plus `Archived: YYYY-MM-DD`) |

An `archived/` record is **not** rewritten to `Status: archived`: archiving adds a date line only and freezes the body and status as they were.

### Approval fields

A file with `Status: approved` needs all three, and a missing one means it is not authorized:

```markdown
- **Approved**: 2026-11-22 — <approver>
- **Authorized scope**: <approved scope, including explicit exclusions>
- **Delivery**: direct
```

- `Approved`: the date and who made the call, written `YYYY-MM-DD — <approver>`. A date-looking word that is not a real calendar date, or a signature with no name, fails the check.
- `Authorized scope`: one sentence that answers what was approved and what was not. "Everything" with no boundary is not a scope.
- `Delivery`: `direct` or `plan` only, and it must be the user's choice.

The script can check that all three exist and are well-formed, but **a passing check does not mean anyone approved**. Approval is a human act; an agent never fills it in.

### Archive fields

```markdown
Status: implemented
Archived: 2026-11-22
```

`Archived` sits immediately below `Status: implemented` — the next line, not merely somewhere in the header — fixed at `YYYY-MM-DD`. It is the only content archiving may write.

## 4. Body skeleton

### `proposed/` (including `approved`) — future tense

Required sections, in this order:

```markdown
## Problem
## Proposal
…(0..N bespoke sections)…
## Alternatives considered
## Acceptance criteria
## Risks
```

- `## Problem`: why this has to happen now. It must stand without the solution — a reader understands the pain before reading the proposal.
- `## Proposal`: what changes. Future tense, migration steps, and open questions are all legitimate here because nothing has shipped.
- `## Alternatives considered`: the other paths genuinely considered and why each lost.
- `## Acceptance criteria`: the observable state that means done. Each entry must let a third party judge met or unmet.
- `## Risks`: what could go wrong and what this knowingly gives up.

Bespoke sections go between `## Proposal` and `## Alternatives considered` — interface contracts, data migration, staged strategy.

### `implemented/` — present tense

Required sections, in this order:

```markdown
## Problem
## Decision
…(0..N bespoke sections)…
## Alternatives considered
## Consequences
```

Forbidden headings (their presence is a format error):

- `## Proposal`
- `## Plan`
- `## Migration plan`
- `## Acceptance criteria`

These are planning-era words. An implemented record describes the present system, not the original plan. Fold the former `## Acceptance criteria` and `## Risks` content into `## Consequences`: what the decision bought and what it cost.

### `rejected/`

Keep the proposal-time structure (a `## Acceptance criteria` or `## Plan` is fine); the verdict is on the status line. When the rejection is retained for its guardrail value, the body should explain why the idea was tempting and why it ultimately fails.

### `archived/`

Keep the body and sections as they stood at archiving, plus the `Archived` line. Once frozen it need not satisfy any active skeleton rule, and its outbound links are not checked.

### The `## Alternatives considered` requirement

All four lifecycles require this section. Without the rejected paths recorded, someone will certainly propose them again.

- Start each entry with a bolded alternative name, then why it lost.
- Record only **real** alternatives that were discussed; never invent one.
- Do not backfill pre-format files; leave them as they are.

## 5. Migration checklists

### `proposed` → `approved`

1. Confirm the user explicitly agreed, and what scope they agreed to.
2. Add `Approved`, `Authorized scope`, `Delivery`.
3. Set `Status` to `approved`.
4. **Keep the location**: it stays in `proposed/<class>/`.
5. **Commit the approved Proposal before creating the delivery branch or worktree.** Commit it on the integration branch so it becomes part of the delivery baseline.

Staying in `proposed/` is deliberate: during delivery, Plans and sibling proposals point at the original path, and moving it breaks them. Present-state `DESIGN.md` / `DESIGN-<module>.md` (including `## Reference Documents`) must never back-link to a proposal while it sits in `proposed/` or `rejected/`; DESIGN documents link only after it moves into `implemented/` (or sealed `archived/`).

### `approved` → `implemented`

Preconditions: the approved scope is **fully** delivered and the user has accepted it.

1. Move to `implemented/<class>/` without renaming.
2. Set `Status` to `implemented`.
3. In the same change, rewrite the skeleton: `## Proposal` to `## Decision`; fold `## Acceptance criteria` and `## Risks` into `## Consequences`; delete the planning-era headings.
4. Convert the prose to the present tense; remove "planned", "pending", "v1 for now".
5. Sync the affected present-state DESIGN (`DESIGN.md` / `DESIGN-<module>.md`) in the same delivery and add the relative link under `## Key Decisions`.
6. Repair every inbound link pointing at the old path.

Partial delivery does not migrate: it stays in `proposed/` with `Status: approved`, and delivery evidence states which part is done.

### `proposed` / `approved` → `rejected`

Decide retention first:

- **Keep**: the rejection prevents someone from repeating a genuinely tempting mistake → move to `rejected/<class>/` with `Status: rejected — <one-line reason>`.
- **Delete**: the idea is obsolete, absorbed by a later decision, or clearly will not return → delete the file and repair every inbound link.

### `implemented` → `archived`

Preconditions: the mission is complete and the record no longer guides daily work.

1. Move to `archived/<class>/` (no `implemented` level).
2. Insert `Archived: YYYY-MM-DD` below `Status: implemented`.
3. Change **nothing else**: no translation, no reordering, no fact updates, no link repair out of the record.
4. Repair or delete inbound links from active documents. Active prose may intentionally cite the archive as history, but the archive is not present-state authority.

Small UI adjustments and purely mechanical changes are **not** archived; delete them and repair inbound links. Archiving is not a trash can.

### `implemented` → delete

Only when the whole decision has been fully absorbed by a new proposal, with every unique rationale, alternative, cost, verification method, and known gap carried over and every inbound link repaired. Check item by item; never rely on Git history as the only copy.

## 6. Inbound link maintenance

Scan for inbound links on every move, rename, and delete:

```bash
rg -n "<old filename or path fragment>" <docs-root>

# then let the verifier check the referring files as well
python3 scripts/verify-proposals.py <proposals-root> --link-scope <docs-root>
```

Handle three cases:

1. Links into present-state documents — retarget to the new path;
2. Links citing history — retarget into `archived/`, or drop;
3. Proposal-to-proposal links — repair in the same change.

The verifier checks relative outbound links in non-frozen directories and local inbound links inside the same tree. `--link-scope <docs-dir>` extends the scan to the documents that cite proposals — pass it once per directory (repeatable) so a move or deletion is caught at the caller instead of waiting for a human to notice. Archived records are excluded from link checking in both directions, and cross-repository references stay a manual check.

## 7. Verifier boundaries

`scripts/verify-proposals.py` performs **single-snapshot static determinism checks** only:

- Directory tree, six-class closed set, path naming with a real calendar date, no `proposal/` and no `INDEX.md`;
- A parent-directory entry point also rejects a competing singular `proposal/` beside `proposals/`;
- `{lifecycle}` matches the header `Status`, and the header carries exactly one status line;
- The identity fields every formatted file needs (`Class`, `Created`) and their values;
- Required and forbidden skeleton headings;
- The three authorization fields, a real `Approved` date with a named approver, and the `Delivery` value for `Status: approved`;
- `archived/` requires `Status: implemented` with `Archived: YYYY-MM-DD` on the line directly below it, and its outbound links are not checked;
- Non-frozen relative outbound links resolve, no local absolute paths (a segment inside an HTTP(S) URL is not a local path), local inbound links are not broken.

It does **not** do: a history database, a frozen-content hash manifest, Git history rollback comparison, or cross-repository full scans. Cross-commit state rewind (for example moving a former `implemented/` file back to `proposed/`) and archived-body tampering are guarded by the agent rules and normal review.

Filename slug length and section order are writing conventions, not structural invariants: the script checks presence, not shape.

A Markdown file sitting at the tree root, outside every lifecycle directory, is reported as skipped (`outside-lifecycle-layout`) instead of being silently ignored.

A file with neither a `Status:` line nor a `**Class**` field is treated as pre-format: it is reported as skipped, never judged. `--strict` turns the presence of such files into a failure when a project has finished migrating.
