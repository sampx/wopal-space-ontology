# zh-CN Localization Review Directory — Agent Development Rules

## 1. Project Positioning

Chinese (zh-CN) localization review directory for the ontology product. Holds review versions of agent souls, commands, rules, and templates.

## 2. Architecture and Directories

Review version → human confirmation → sync to corresponding English runtime source under `.wopal/`.

| Directory | Runtime Source | Content |
|---|---|---|
| `agents/` | `.wopal/agents/` | Agent soul Chinese review versions (wopal, fae, rook) |
| `commands/` | `.wopal/commands/` | Command Chinese review versions, including `wopal/` subdirectory |
| `rules/` | `.wopal/rules/` | Rule Chinese review versions, including `fae/`, `wopal/` subdirectories |
| `templates/` | `.wopal/templates/` | Template Chinese review versions |
