# <Product Name>

> **Status**: Draft | Proposed | Active
> **Updated**: YYYY-MM-DD
> **Product Intent**: `<prd-path>` — the PRD this DESIGN follows
> **Sibling DESIGNs**: list the project DESIGNs of this product's core subsystems — their contracts bind this design, so they belong in the header even when they live in another repository
> **Sub-DESIGNs**: list every `DESIGN-<topic>.md` under this main document

A sub-DESIGN uses `templates/design-sub.md`, which carries `Parent: ./DESIGN.md` plus the same `Parent Architecture` / `Parent Product` lines as its main document.

---

## Architecture Design

Overall product architecture diagram (ASCII preferred) and layer table. The diagram covers all core subsystems and their interaction relationships.

```text
<ASCII architecture diagram>
```

### Layers

| Layer | Location | Owner | Responsibility |
|---|---|---|---|
| | | | |

## Core Projects

Each core subsystem's role, boundary, and interaction contract.

- One subsection per subsystem: responsibility, design principles, external contract
- Link to the corresponding project DESIGN document — those documents are the `Sibling DESIGNs` in the header, not reference material
- Inter-subsystem interaction relationships are traceable

## Runtime Model

Runtime structure, state locations, data ownership, configuration layers, lifecycle, persistence boundaries.

- Clarify each subsystem's state ownership scope
- Configuration layer relationships are clear (global → space → project)

## End-to-End Flows

Key cross-project flows, from a system perspective.

- Cover critical user paths (installation, daily use, failure recovery)
- Use numbered steps, focus on system behavior

## Capability Roadmap

The capability map: what capability dimensions the product has, and which maturity step each one is at. Rows are capability dimensions; columns are current shape / next milestone / target shape with an owning project. It describes direction, not dates.

```markdown
| 能力维度 | 当前形态 | 下一里程碑 | 目标形态 | 主责 |
|---|---|---|---|---|
| <capability dimension> | <current shape> | <next milestone> | <target shape> | <project> |
```

Phases are cut from this map. Each phase entry keeps only the title, Goal, and phase document link. The Goal traces to a capability row and its target step.

```markdown
### Phase <N>: <Title>

- **Goal**: Product capability target for this phase (one line, ≥20 characters, verifiable product capability statement, traceable to a capability row)

> Phase doc: [phases/<product>-p<N>-<slug>.md]
```

## Reference Documents

Reference-only documents: research, external specifications, auxiliary material that informs without binding. Do not repeat the PRD, the sibling DESIGNs, or the sub-DESIGNs listed in the header — a document whose contract this design follows belongs in the header, not here.
