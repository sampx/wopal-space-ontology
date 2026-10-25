# Native Git/GitHub Contribution Workflow

## Ownership and Authorization

Use native `git` and GitHub CLI `gh` to create, revise, and close out upstream PRs. Add no scripts, contribution ledger, or recovery state machine: Git branches/worktrees hold the work; GitHub holds the PR. `ontology status` only inspects and reminds; `ontology sync` only synchronizes main. A merged status is not deletion clearance.

The user decides each upstream publication. Authorization to create a PR does not authorize later review-fix publication, merging, or deletion. An explicit request to synchronize and clean up that PR includes its closeout; ordinary sync does not. Do not add/change remotes without authorization or switch the host ontology repository's branch. Use `wopal space` operations for sparse assembly and private-content protection.

## Branch and Worktree

- New contributions use `contribute/<slug>`. Use a short English topic of 2–4 words, at most 24 characters, such as `plan-lookup`; lowercase letters, digits, and single hyphens only, with no leading/trailing hyphen.
- Do not truncate full commit titles or long proposal names into branch names. No dates, timestamps, random strings, `tmp`, `v2`, or accumulating fix suffixes.
- Keep the worktree at `<space-root>/.worktrees/ontology-contribute-<slug>/`, fully checked out from upstream/main. It is the PR's continuing workspace, not disposable `.tmp/` or system-temp content.
- One topic, one PR, one branch/worktree pair. Reuse it through review until the PR is finished and authorized cleanup completes. Do not release it after publishing or create another branch per revision.
- Before creation, inspect local/remote branches, `git worktree list --porcelain`, and PRs with that head. Resolve an occupied name: reuse the same contribution; for a different topic choose another meaningful short name. Never overwrite or append random suffixes.
- Keep existing long-named contributions under their current identity; do not rename open PR branches to satisfy the new naming rule. Touch only this contribution's identified resources, not unrelated leftovers.

## Inspect Before Creating the Workspace

These are command examples, not an unchecked batch script. Fill variables from verified current-space and registry facts with absolute paths and exact repository identities; never run placeholder values. `R` is the host ontology repository, `S` the space root, and `W` this PR's worktree. Stop on any failed command and preserve the original error and workspace.

```bash
R='<verified-absolute-ontology-repo>'
S='<verified-absolute-space-root>'
SLUG='plan-lookup'
B="contribute/$SLUG"
W="$S/.worktrees/ontology-contribute-$SLUG"
UPSTREAM='<verified-upstream-owner/repo>'
FORK_OWNER='<verified-origin-owner>'
git -C "$R" status --short
git -C "$R" log --oneline -5
git -C "$R" remote -v
git -C "$R" worktree list --porcelain
git -C "$R" branch --list 'contribute/*'
git -C "$R" ls-remote --heads origin "refs/heads/$B"
gh pr list --repo "$UPSTREAM" --state all --head "$FORK_OWNER:$B" \
  --json number,url,state,baseRefName,headRefName,headRepository,headRepositoryOwner
```

Verify origin is the intended fork and upstream the intended repository; match the full head repository and branch identity and base main. Clone mode needs a fork: explain that, do not silently change topology. Report uncommitted changes before proceeding; never stash, reset, or clean someone else's work.

Inspect `wopal space status` and `wopal ontology status`. Within the user's authorization, run `wopal space sync --confirm` to integrate source Space changes, then `wopal ontology sync --confirm` to align the source chain. Stop on failed synchronization instead of publishing from stale facts.

Verify current upstream/main is an ancestor of source main, then examine `git diff --name-status upstream/main...main` by topic. Exclude private, space-only, and unrelated changes; matching a directory does not establish ownership, and unrelated changes within the same file must also stay out.

Create only after confirming the branch/path are unused, the repository is clean, and ownership is established. Inspect existing directories rather than overwriting them. This command is only for a new contribution:

```bash
git -C "$R" merge-base --is-ancestor upstream/main main
git -C "$R" worktree add -b "$B" "$W" upstream/main
```

If the known local branch exists but its worktree is missing, verify the branch/PR identity and restore the same workspace with `git -C "$R" worktree add "$W" "$B"`. For a remote-only branch, fetch and verify its head, then create the local branch/worktree from that remote branch; do not restart at upstream/main and replace the PR's work.

## Select Changes, Commit, and Create the PR

Prefer verified topic-only commits, applied in order. Never import a whole interval of main containing unrelated work. Confirm the contribution worktree is clean before each application:

```bash
git -C "$W" status --short
git -C "$W" cherry-pick --no-commit <verified-topic-commit>
git -C "$W" diff --cached --name-status
git -C "$W" diff --cached --stat
git -C "$W" diff --cached --check
```

Inspect the actual staged diff and run applicable verification before committing. For a mixed-topic commit, extract and inspect topic hunks instead of cherry-picking it whole or checking out complete files from main. Native commands can apply a patch between explicit revisions and paths (`PATCH` belongs in the space's `.wopal-space/.tmp/`; still inspect hunks within shared files):

```bash
git -C "$R" diff --binary --full-index --no-renames <from> <to> -- <exact-paths> > "$PATCH"
git -C "$W" apply --3way --index "$PATCH"
```

Preserve additions, modifications, deletions, and both sides of renames. Whole-file copying can import concurrent changes or erase this PR's upstream adaptations; it is not the default. Preserve conflicts for manual inspection and named staging; never automatically choose ours/theirs or reset/clean. Commit only after verifying the scope:

```bash
git -C "$W" commit -m 'fix: resolve plan lookup'
git -C "$W" diff --name-status upstream/main...HEAD
git -C "$W" diff --stat upstream/main...HEAD
git -C "$W" push -u origin "$B"
```

Before creating, query again for an existing PR with the same upstream, fork, head, and base. Continue a unique matching PR; report closed/merged or ambiguous matches rather than creating another automatically. If push succeeds but creation fails, retain branch/worktree and query before retrying.

Write an informative PR body from actual work, not a fixed “merge main to upstream” sentence. Include:

- Background and motivation: the problem and why this contribution is needed.
- Main changes and affected capabilities.
- Final file inventory, additions/deletions, and scope provenance: which verified commits/hunks were selected and what was excluded. Do not invent line counts for binary files.
- Actual verification commands/results; explicitly state verification not performed.

Derive statistics from the final contribution branch relative to current base, not all source-main changes. Store the body in the space temporary directory and pass it as a file:

```bash
gh pr create --repo "$UPSTREAM" --base main --head "$FORK_OWNER:$B" \
  --title 'fix: resolve plan lookup' --body-file "$BODY"
```

Report PR URL, branch, absolute worktree path, verification results, and next step. Keep the workspace for review.

## Review Fixes and Interrupted Work

Verify PR identity/open state, worktree path/branch/cleanliness, and remote head first. Prefer fixing and verifying in the source Space, synchronizing with authorization, then transferring only this revision's topic changes into the original worktree. Fixes made directly in the contribution worktree must also return to the source Space. Preserve the PR's existing conflict resolutions.

Review may add or remove files; there is no lifetime scope lock. Inspect the final diff before publishing and update affected body/verification information:

```bash
git -C "$W" push origin "HEAD:refs/heads/$B"
gh pr edit <pr-number> --repo "$UPSTREAM" --body-file "$BODY"
```

Use ordinary push only. If rejected, stop and inspect divergence; never force push. After interrupted push/PR creation, continue the original branch from current Git/GitHub facts; do not re-copy commits, change branches, or open another PR merely to retry. Retain open PR workspaces and conflict scenes.

## Return and Authorized Cleanup

The user decides merging; review approval alone does not authorize the Agent to merge. On the user's return request, run `wopal ontology sync --confirm`, then `wopal space sync --confirm`. Neither command owns contribution-resource deletion.

Obtain explicit deletion authorization for this PR, then check each condition:

1. GitHub repository, fork/head branch, and base main match this PR; state is MERGED; obtain `headRefOid` and `mergeCommit.oid`. Keep everything if queries fail or required facts are missing.
2. mergeCommit is an ancestor of local main; origin/main matches local main; source Space synchronization succeeded. Content equivalence alone does not prove return.
3. The exact worktree path belongs to this branch. Inspect tracked, untracked, and ignored content. Report any outstanding work; never force-remove or empty it.
4. Local branch head equals the PR's final head; the remote head, if present, must match too. Preserve extra commits or occupancy by another worktree, even after merge.

```bash
gh pr view <pr-number> --repo "$UPSTREAM" \
  --json state,baseRefName,headRefName,headRepository,headRepositoryOwner,headRefOid,mergeCommit
git -C "$R" merge-base --is-ancestor <verified-merge-sha> main
git -C "$W" status --short --untracked-files=all --ignored
git -C "$R" rev-parse "refs/heads/$B"
git -C "$R" ls-remote --heads origin "refs/heads/$B"
```

With all evidence and deletion authorization, normally remove this PR's worktree, delete its remote branch if present, then delete its local branch. Continue only after each step succeeds. Report partial cleanup and residue instead of claiming completion:

```bash
git -C "${R:?}" worktree remove "${W:?}"
git -C "${R:?}" push origin --delete "${B:?}"
git -C "${R:?}" branch -d "${B:?}"
```

Skip already-absent worktree/remote steps after checking the remaining resources. Squash/rebase can make `branch -d` refuse; only with all the evidence above and explicit user deletion authorization may `git branch -D` delete this one verified branch. Never force-remove worktrees, delete by wildcard, or globally prune another task's worktrees.

For CLOSED-unmerged PRs, retain the workspace and ask the user how to preserve/withdraw the undelivered work; closing is not deletion authorization. Report removed resources, retained resources, and reasons.
