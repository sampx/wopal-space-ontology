---
description: maintain ontology instance and collaboration
---

# Maintain Ontology Instance

Maintain the ontology instance and its collaboration surface: instance updates, space alignment, capability assembly, and contribution.

**Input**: `$ARGUMENTS`

**Parameter Notes**: Optional focus — `update` | `contribute` | `sync` | `status`. When not provided, assess every maintenance surface.

---

## How to Work

This command is an entry point only — the authoritative specification lives in the `ontology-evolution` skill.

1. Load the `ontology-evolution` skill.
2. Treat `$ARGUMENTS` as the focus and follow the skill's **Maintenance Protocols** for the full workflow: command surface, status reading, channels and the upload gate, execution stance, and contribution scope.
3. Carry no protocol of your own — decisions, gates, and CLI usage come from the skill.
