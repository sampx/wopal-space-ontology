---
trigger: model_decision
description: Follow this rule when performing Git, branch, merge, commit, or Issue operations in WopalSpace repositories.
keywords:
  - 'git'
  - 'commit'
  - 'branch'
  - 'merge'
  - 'issue'
  - 'pull request'
  - 'pr'
---

# Git and Issue Engineering Rules

This rule defines shared execution standards for Git and Issue operations in WopalSpace repositories. Load it only when the task actually performs Git, branch, merge, commit, or Issue work.

An owning workflow takes precedence over this shared rule. When `dev-flow`, `ontology-evolution`, or another capability defines branch naming, commit ownership, integration, publication, or Issue routing, follow that workflow rather than inventing or imposing a second Git process here.

---

## 1. Issue Rules

### Title format

`<type>(<scope>): <description>`

- **type** is required; use the label mapping below.
- **scope** is optional, lowercase, concise, and wrapped in parentheses.
- **description** is an English imperative phrase, starts lowercase, has no trailing period, is at most 70 characters after the type prefix, and keeps the full first line at most 100 characters.

**Label mapping**:
- `feat` / `enhance` → `type/feature`
- `fix` → `type/bug`
- `refactor` → `type/refactor`
- `docs` → `type/docs`
- `test` → `type/test`
- `chore` → `type/chore`
- `perf` → no type label

### Project ownership and workflow routing

`--project` names the component being changed. It determines the `project/<name>` label and the owning workflow:

| Change target | `--project` | Owning workflow |
|---|---|---|
| Reusable capability assets under `.wopal/` (`skills`, `rules`, `agents`, `commands`, `plugins`, `assembly`) | `wopal-space-ontology` | `ontology-evolution` |
| A code repository under `projects/` | That repository name | `dev-flow` |

- Ontology work uses the canonical project name `wopal-space-ontology`; do not substitute aliases such as `ontology` or `space`.
- For ontology work, let `ontology-evolution` decide the path: an implementation defect in already-agreed behavior uses its instant repair path; a capability or contract change uses the proposal lifecycle.
- Do not route ontology capability work through a `dev-flow` Plan, and do not route project code work through an ontology proposal unless the owning workflow explicitly says otherwise.
- `--project` selects ownership and routing; it does not authorize moving records between repositories or bypassing the owning workflow.

---

## 2. Git Workflow

### Base rules

- **Name the target repository explicitly**: use `git -C <path>` for direct Git inspection or manual Git operations. The space root is a separate repository; never rely on the current working directory to target a nested project implicitly.
- **Respect workflow-owned mutations**: when the active workflow owns commits, integration, PR publication, or cleanup, use that workflow's commands and gates instead of replacing them with raw Git.
- **Before manual mutation**:
  1. inspect `git status` and preserve unrelated work;
  2. inspect `git log --oneline -5` and report unexpected local-only history;
  3. never use reset, stash, clean, force-push, or branch deletion to reshape someone else's work unless the owning workflow and user authorization explicitly permit that exact action.
- **Before a manual commit**:
  1. inspect `git status` and `git diff --staged --name-only` to confirm scope;
  2. inspect `git log --oneline -5`;
  3. confirm HEAD is attached to the intended branch.
- **Commit language**: use English commit messages in every repository in the space, including the space root, `projects/*`, and ontology worktrees. Git history language does not follow the document body language.
- **Repository ownership**: commit a change in the repository that owns it. Do not stage project-repository content through the space-root repository or bypass the workflow that owns `.wopal` capability changes.

### Commit format

`<type>(scope): <description> [#ref]`

- `type` is required; `scope` is optional, lowercase, and concise.
- `description` is an English imperative phrase, starts lowercase, has no trailing period, is at most 70 characters (60 when an Issue ref is appended), and keeps the full first line at most 100 characters.
- Optional body text is separated by a blank line, explains what/why rather than how, and keeps lines at most 72 characters. Breaking changes start with `BREAKING CHANGE:`.
- Keep commits atomic: combine one coherent change and split unrelated changes so history remains reversible and bisectable.

| Type | Use | Version | Type | Use | Version |
|------|-----|---------|------|-----|---------|
| `feat` | new capability | MINOR | `enhance` | capability enhancement | MINOR |
| `fix` | bug fix | PATCH | `perf` | performance | — |
| `refactor` | behavior-preserving refactor | — | `ci` | CI/CD | — |
| `docs` | documentation | — | `build` | build system | — |
| `test` | tests | — | `revert` | revert | — |
| `chore` | tooling/maintenance | — | `style` | formatting only | — |

### Branch ownership

- Do not impose a universal `feature/*`, `bugfix/*`, `hotfix/*`, or `refactor/*` convention on workflow-owned branches.
- `dev-flow` owns its Work Branch and Integration Branch semantics; `ontology-evolution` owns ontology isolation and `contribute/<slug>` contribution branches.
- For manual repository work that is genuinely outside an owning workflow, choose a short, meaningful branch name and follow that repository's own rules.

### Manual merge verification for structural changes

When a merge is manual and not already owned by a workflow, structural changes such as renames, directory moves, file merges, or file splits require explicit verification; “no Git conflict” does not prove the result is lossless.

Before the manual merge:
1. find the merge base;
2. list the target branch's new commits;
3. classify structural changes by file (a 1:1 rename may be auto-merged but still requires verification; merge/split transformations require explicit porting);
4. report the classification and obtain the user decision required by the owning process before mutating history.

---

## 3. Commit Prohibitions

Never commit credentials or temporary/generated workspace artifacts such as `.env`, private keys, `__pycache__/`, `node_modules/`, `.ruff_cache/`, or IDE-local configuration unless the repository explicitly defines a safe tracked exception.
