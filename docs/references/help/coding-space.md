# How This Space Works — Coding Type

This file covers usage specific to coding-type spaces. It builds on top of the common reference; only delta is listed here.

---

## What This Space Is Optimized For

This space is tuned for software development. The primary working directory is `projects/`, where code repos live. Most tasks here will involve reading, writing, reviewing, or managing code.

---

## Coding Workflow

Day-to-day work follows an Issue/Plan-driven flow:

```
create issue → write plan → approve → implement → review → verify → archive
```

- **Complex tasks** automatically enter the dev-flow lifecycle (agent decides when)
- **Simple changes** (typo fix, config tweak, single-file edit) can be handled directly
- **All code changes** go through review before completion

You don't need to learn the full pipeline. Just say "处理这个 Issue" or "改这个" and I'll take it from there.

---

## Project-Level Rules

Each project in `projects/` may have its own `AGENTS.md` file. This file defines project-specific development rules:

- Language and framework conventions
- Testing requirements
- Commit style guidance
- Agent behavior specific to that project

**Always check the project's own `AGENTS.md` before starting work there.** Space-level rules are the baseline; project-level rules are more specific and override the baseline when they conflict.

---

## Coding-Specific Commands and Skills

In a coding space, these are the most frequently used capabilities:

| Command/Skill | Why It Matters Here |
|---------------|-------------------|
| `dev-flow` | Main workflow for Issue/Plan tasks; loads automatically |
| `agents-collab` | Complex code tasks are split into Wopal→Fae→Rook pipeline |
| `/review` | Used more frequently here — all non-trivial code goes through review |
| `/commit` | Ensures commit messages follow the space's format conventions |

**How delegation works in coding tasks:**

1. Wopal understands the requirement and creates a plan
2. Fae implements the code and runs tests
3. Rook reviews the implementation for quality
4. If issues found, fae fixes and rook re-reviews (max 3 rounds)
5. When all pass, Wopal presents the result for your confirmation

You don't need to manage this process — just tell me what needs to be done.
