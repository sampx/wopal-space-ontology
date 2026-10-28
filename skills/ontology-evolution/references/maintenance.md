# Ontology and Space Maintenance Reference

Read this file for status inspection, space / ontology synchronization, capability assembly, or local capability selection. For upstream GitHub PR creation, revision, and closeout, read [`contribution.md`](contribution.md).

## Command surface

| Command | Responsibility |
|---------|----------------|
| `wopal space status` | Show space branch vs `local main`, assembly state, sparse consistency, local include / exclude / private selections, and unregistered files |
| `wopal space sync [--confirm]` | Align the space branch with `local main`: integrate space-unique evolution upward, then fast-forward downward |
| `wopal space capability add/remove <kind>:<name> [--local]` | Without `--local`, change shared assembly; with `--local`, change only this space's include / exclude / private selection |
| `wopal ontology capability list` | Show capabilities owned by the central pool |
| `wopal ontology status` | Show ontology downstream / upstream deltas and contribution status |
| `wopal ontology sync [--confirm]` | Align the `upstream ⇄ origin ⇄ local main` source chain; clone mode collapses to the applicable topology |

## Reading status

`wopal space status` distinguishes:

- **to contribute**: the space branch has shared changes not yet in `local main`.
- **behind local main**: the space needs ontology-main changes.
- **include**: an extra shared capability mounted only in this space.
- **exclude**: a type-default capability disabled in this space.
- **private**: local-only capability content that must not travel through shared synchronization.

`wopal ontology status` reports:

- **Downstream**: `upstream → origin → local main`.
- **Upstream**: the pending `local main → origin → upstream` file set.
- Local / remote `contribute/*` branches, worktrees, and PR state.

“Merged, awaiting closeout” is a reminder, not deletion authorization.

## Shared assembly vs local selection

`space capability` has two channels:

- **Shared channel** (without `--local`): edit archetype / assembly and re-materialize; only capabilities already owned by the pool are accepted. The command creates no Git commit; committing the manifest is a separate action.
- **Local channel** (with `--local`): record only this space's include / exclude / private selection and adjust the sparse range. When state changes, the CLI commits only that space-root state record; capability content is not uploaded as part of local-selection state.

Assembly selection and content propagation are separate concerns. include / exclude decide whether the space mounts shared capability; they do not decide whether shared content can upload. private is the upload-protection boundary.

## Upload gate

Before `space sync` integrates upward, it checks private capability roots. Any space-unique commit that touches a private-registered capability root must be refused.

This gate backstops manual `git add` / `commit`: local isolation must not depend on the operator remembering which content may not upload.

## Execution stance

- The CLI may provide dry-run preview by default; when the user has already authorized execution, use `--confirm` directly rather than adding another approval ritual.
- Synchronization authorization covers synchronization only; it does not authorize PR creation, review-fix push, merge, or deletion.
- On conflict, unclear scope, or inconsistent state, stop rather than using reset / stash / force to reshape the scene.

## Preparing an upstream contribution

Before creating a PR:

1. Enumerate every pending path and group it by topic / capability.
2. Separate genuinely shared capability changes from space-only or type-specific changes.
3. Let the user choose which groups belong in this contribution.
4. Use one PR per topic and exclude unrelated hunks even inside shared files.

Once creating, revising, retrying, or closing out a contribution, switch to [`contribution.md`](contribution.md); do not improvise Git/GitHub flow here.
