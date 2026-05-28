# Ontology Product Documentation Workspace — Agent Development Rules

## 1. Positioning

Documentation workspace for the ontology product. Holds PRD, DESIGN, localization reviews, plans, research, and reference materials.

## 2. Directories

| Directory | Responsibility |
|---|---|
| `LANG/<locale>/` | Localization review versions; organized by locale, with internal agents/commands/rules/templates aligned to `.wopal/` runtime directories; see subdirectory AGENTS.md for rules |
| `plans/` | Development plan archive |
| `backlogs/` | Product-level pending decision records |
| `research/` | Technical research records |
| `research/memory/` | Agent memory skill research (external memory solution comparison, LanceDB selection) |
| `research/claude-code/` | Claude Code sub-agent role references |
| `references/` | External reference specs and feature references |
| `references/agentskills/` | Agent Skills open format spec (SKILL.md format, directory structure conventions) |
| `references/openspec/` | OpenSpec SDD guide (spec-driven development workflow spec) |
