# Maintaining and superseding implemented Proposals

Use this guide when an implemented Proposal needs factual maintenance or its decision is partly or wholly superseded.

## 1. Separate "changing facts" from "changing the decision"

| | Changing facts | Changing the decision |
|---|---|---|
| Typical move | A file moved, a package was renamed, a config key changed, a default moved elsewhere in code but kept its value | A default changed, a boundary narrowed or widened, failure semantics changed, a different path was chosen |
| Test | "Would a reader who trusts the old document misread the current code?" | "If the original author re-decided today, would they choose the same thing?" |
| Action | Update `implemented/<class>/` in place | Create a `proposed/` proposal |

Both answers being "yes" is rare; as soon as the second is "no", a new proposal is mandatory and in-place rewriting is not an option.

**"Optimization", "enhancement", and "just tidying" are not classification criteria.** They describe how the author feels about the change, not whether the decision moved. If a core default, boundary, or external contract changes, it is a design adjustment.

## 2. Three cases

### 2.1 Fact-only drift — sync in place

Code moved a path, renamed a package, or relocated a structure, and **the decision itself is untouched**.

Action:

1. Update the facts in `implemented/<class>/` in the same delivery (paths, symbol names, config keys, module ownership).
2. Leave `Status` alone; add no change log, no `## History`, no "this update changed…".
3. Repair any inbound link that broke.

Why in place: `implemented/` owns "what this decision looks like now". It follows the code, or the reader gets a stale map.

Why no change log: present-state documents describe the present, not the editing process. The process is in Git.

### 2.2 Design adjustment / optimization / partial overturn — create a proposal

Whenever the decision, a core default, or a boundary changes, or the user must re-decide, create a new proposal.

Action:

1. Create `proposed/<class>/yyyy-mm-dd-<slug>.md` and run it through independent review and user approval.
2. Its `## Problem` must say which earlier proposal it adjusts, with a relative link to it.
3. **Do not modify the old `implemented/` proposal before the new scope is fully delivered.** The old proposal still represents an in-force historical decision; editing it early makes readers believe the change already shipped.
4. When the new proposal is fully delivered and moves into `implemented/<class>/`, **cross-link both ways in the same delivery**:
   - The new one states which decisions of the old one it partly supersedes and which remain valid;
   - The old one states the superseded passage as current and links to the new one.
5. Leave the non-superseded parts of the old proposal intact — they are still in force.

**Two things are forbidden:**

- Moving an `implemented/` proposal back to `proposed/` for re-approval. The transaction record disappears, and no reader can tell which decision actually closed.
- Rewriting an `implemented/` proposal in place into a different decision. Same filename, same status, different claim — the most invisible form of record rot, because nothing appears to have changed.

### 2.3 Full replacement / capability removal — complete supersession

The old decision no longer holds as a whole, and a new one replaces it.

Action: create a proposal (as in 2.2), then dispose of the old one **at delivery time**, not in a later cleanup. Two options:

**A. Absorb, then delete**

Precondition: the new proposal already preserves everything still unique in the old one:

- The original problem statement and motivation;
- The alternatives and why each failed;
- Known costs and remaining gaps;
- The verification method and any observation conditions it needs.

Then repair every inbound link and delete the old file.

**B. Move to `archived/<class>/` and freeze**

Precondition: the old proposal still has independent historical value (it is the source of a long-lived constraint, or external documents cite it) but no longer guides daily work.

Then add `Archived: YYYY-MM-DD` per the archive flow, freeze the body, and repair or delete inbound links from active documents.

There is no acceptable third option: leaving the old proposal in `implemented/` next to a new one that contradicts it makes readers see two claims with no clue which one holds.

## 3. After archiving

`archived/` is **permanently read-only**:

| Forbidden | Note |
|---|---|
| Unfreezing to edit | Including "just updating a path" — fact drift does not apply to archive records |
| Changing status | `Status: implemented` is terminal; archiving introduces no new state |
| Adding metadata beyond the archive date | Only the `Archived: YYYY-MM-DD` line |
| Translating / reordering / renaming | Frozen means byte-stable |
| Checking its outbound links | A broken link is a normal property of a historical snapshot |

Later evolution only creates active proposals. When history matters, the new proposal can link relatively into the archive.

## 4. Decision flow

```text
Found an implemented/ proposal covering the same topic
        │
        ├─ Decision, defaults, boundary unchanged?
        │      └─ yes → sync facts in place, stop
        │
        ├─ Only part of the decision changes, the rest stays valid?
        │      └─ yes → create proposed/ proposal ──full delivery──▶ cross-link both ways
        │
        └─ The whole decision fails, a new one replaces it?
               └─ yes → create proposed/ proposal ──full delivery──▶ absorb+delete or archive+freeze
```

## 5. Common misjudgements

| Claim | Why it is wrong | Correct action |
|---|---|---|
| "It is only a small optimization, I will edit the implemented file directly" | An optimization that moves a default or boundary is a design adjustment | Create a proposal |
| "The new proposal is not finished, but I will make the old one consistent first" | The old proposal still represents the in-force decision; undelivered work must not rewrite history early | Cross-link both ways when the new scope is fully delivered |
| "I will move the old proposal back to proposed and re-approve it" | The historical decision leaves the closed record | Create a new proposal; keep or archive the old one |
| "It is archived, but I will fix the stale path while I am here" | Frozen records accept no content change | Leave it; the new proposal carries the current state |
| "The old proposal is useless, just delete it" | Deletion requires its unique rationale to be carried over first | Absorb, then delete |
| "Both proposals are in implemented, readers can work it out" | Readers have no basis for choosing | Cross-link both ways, or absorb and delete |
