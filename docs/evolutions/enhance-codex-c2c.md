# enhance-codex-c2c


## Metadata


- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-10-28
- **Stage**: implementing
- **Mode**: quick
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

Promote `codex-with-chatgpt` into the shared ontology skill pool and make it a default capability of coding spaces.

## Technical Context


### Architecture Context

The skill has completed its test phase and already exposes the stable C2C session protocol, runtime scripts, references, bilingual review copy, and unit tests. The ontology currently has no shared `skills/codex-with-chatgpt/` asset and the coding archetype does not declare it, so a tested capability cannot survive assembly or be reused by other coding spaces. The canonical runtime contract is the skill itself (`skills/codex-with-chatgpt/SKILL.md`) and the coding-space selection is owned by `assembly/archetypes/coding.yaml`.

### Research Findings

The tested skill is self-contained, uses the standard skill layout, and preserves the stable `.codex/skills/codex-with-chatgpt` runtime entrypoint through assembly rather than embedding a workspace-specific source location. Its existing 13 unit tests pass after promotion. A security scan reported zero critical findings; the single warning is caused by test fixtures containing an executable path / ChatGPT URL rather than a download-and-execute behavior.

**References**:
- `skills/codex-with-chatgpt/docs/DESIGN.md`
- `skills/codex-with-chatgpt/references/protocol.md`

### Key Decisions

- D-01: `codex-with-chatgpt` belongs in the shared skill pool because its C2C protocol is reusable across coding spaces rather than being tied to one project.
- D-02: Coding spaces receive the skill by default through the coding archetype so re-assembly preserves the capability and its runtime link.
- D-03: Promotion changes ownership and assembly only; the tested skill content is not redesigned during this evolution.

### Key Interfaces

The runtime skill name remains `codex-with-chatgpt`; consumers continue to use the assembled `.codex/skills/codex-with-chatgpt` entrypoint. The C2C session/request protocol defined by the skill is unchanged.

## In Scope

- Add the complete `codex-with-chatgpt` skill asset to the shared ontology pool.
- Register `skill:codex-with-chatgpt` as a coding type default.
- Verify the promoted copy with its existing unit tests, security scan evidence, assembly discovery, and runtime-link resolution.

## Out of Scope

- Redesigning the C2C protocol or changing its request/session semantics; promotion preserves the already tested behavior.
- Publishing or merging the upstream contribution; those remain explicit delivery actions after the space change is synchronized.

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Skill pool | `skills/codex-with-chatgpt/` | create | Canonical shared C2C skill asset |
| Coding assembly | `assembly/archetypes/coding.yaml` | modify | Mount the skill by default in coding spaces |

## Assembly Intent


| Ref | Scope | 理由 |
|-----|-------|------|
| skill:codex-with-chatgpt | type-default | C2C is a reusable coding-space capability and must survive assembly/rebuild |

## Acceptance Criteria

### Agent Verification

1. [x] The promoted skill's unit tests pass: all 13 session-protocol tests succeed. Evidence: `python3 -m unittest discover -s .wopal/skills/codex-with-chatgpt/tests -v` → `Ran 13 tests ... OK`.
2. [x] The ontology capability view reports `codex-with-chatgpt` from the shared space skill pool. Evidence: `wopal space capability list --json` reports the skill with `source: space` and the canonical `skills/codex-with-chatgpt/SKILL.md` location.
3. [x] The coding archetype declares `codex-with-chatgpt`, and the assembled runtime entry resolves to the canonical ontology skill directory. Evidence: the archetype contains the skill entry and `.codex/skills/codex-with-chatgpt` resolves to `.wopal/skills/codex-with-chatgpt`.

Security evidence: the OpenClaw scanner completed 13 checks with 0 critical findings, 1 warning, and 12 clean checks; the warning is confined to test fixtures and does not represent download-and-execute behavior.

### User Validation

No manual-only validation is required for this promotion. Runtime discovery, assembly registration, link resolution, and protocol tests are agent-verifiable; the user explicitly authorized committing, synchronizing, and publishing this promoted capability.

## Implementation


### Task 1: Promote and register the C2C skill

**Verification Intent**: Agent Verification 1-3

**Behavior**:
- Given a coding space assembled from the ontology, `codex-with-chatgpt` is present as a shared skill, its runtime entry resolves to that canonical asset, and its existing session protocol tests continue to pass.

**Pre-read**: `skills/codex-with-chatgpt/SKILL.md`, `assembly/archetypes/coding.yaml`, `skills/codex-with-chatgpt/docs/DESIGN.md`

**Design**: Preserve the tested skill tree unchanged as a shared ontology asset, add one coding-archetype skill reference, and rely on assembly to provide runtime links. Do not encode any workspace-specific source path in the skill.

**TDD**: false — this is promotion/assembly work with no new behavior; reuse the existing 13 protocol tests.

**Changes**:
1. Add the tested `skills/codex-with-chatgpt/` asset to the ontology pool.
2. Add `codex-with-chatgpt` to the coding archetype's `skills` list.

**Verify**: `python3 -m unittest discover -s .wopal/skills/codex-with-chatgpt/tests -v && wopal space capability list --json`

**Done**:
Task output: Promoted the tested C2C skill into the shared ontology pool and registered it as a coding-space default.
Files touched: `skills/codex-with-chatgpt/`, `assembly/archetypes/coding.yaml`
- [x] The implementation agent has completed all development and verification steps above.

---

## Delegation Strategy

N/A — one low-complexity promotion task; the current execution environment has no sub-agent delegation surface.

## Delivery

`space sync` and native Git/GitHub PR publication are the user's call — the skill never uploads on its own.
