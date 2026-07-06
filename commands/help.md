---
description: show how to use this space
---

# Help — Space Usage Guide

Explain how this space works to the user. Reads reference documents and current space runtime state, then synthesizes a practical answer in the user's language.

**Input**: `$ARGUMENTS`

**Parameter Notes**: Optional topic to filter the output. When not provided, output a full overview. Valid topics: `space`, `commands`, `skills`, `rules`, `workflow`.

---

## Core Principles

- Read reference files and current runtime state; do not dump raw content.
- Synthesize: understand the structure, then explain in your own words.
- When a topic filter is given, extract only the relevant sections.
- Output must be practical and actionable: tell the user where things are, how to use them, and when to use each.

## Step 1: Read Common Reference

Read `docs/references/help/common.md`. This is the baseline usage guide that applies to all spaces.

## Step 2: Read Type-Specific Reference (If Available)

If a file matching `docs/references/help/*-space.md` exists in the current worktree, read it. This contains type-specific usage guidance. Currently known: `coding-space.md`.

## Step 3: Read Current Space Runtime State

Read the following files for localized context:

- `.wopal-space/STRUCTURE.md` — current space projects and contents
- `.wopal-space/REGULATIONS.md` — current space regulations
- `AGENTS.md` — user custom rules entry

## Step 4: Synthesize and Output

| Input | Output |
|-------|--------|
| `/help` (no topic) | Full overview: how to work here + important files + commands + skills + rules |
| `/help space` | Space overview with current structure and type |
| `/help commands` | Command list with usage scenarios |
| `/help skills` | Skill list with trigger conditions |
| `/help rules` | Where rules live and how to customize |
| `/help workflow` | Workflow guidance (type-dependent; common spaces stay general) |

Use the user's communication language. Keep explanations concise and actionable.
