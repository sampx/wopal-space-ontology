#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# worktree.py - Isolated worktree derivation and integration.
#
# The isolation model (docs/DESIGN-evolution.md, Isolation Discipline):
#   - Derive from `.wopal` so the new worktree inherits the sparse assembly
#     range. Deriving from the full host repository does NOT inherit it.
#   - The host repository is never touched. It is not even discoverable from
#     here: the host path is machine-local (`~/.wopal/ontologies/<source>`),
#     so the skill must not depend on it.
#   - Integration back into the space branch happens INSIDE `.wopal` (which
#     holds that branch), as a single squash merge after the user validates.
#
# Empirical basis:
#   - `git worktree add` run from `.wopal` inherits core.sparseCheckout, the
#     pattern list and the skip-worktree bits verbatim.
#   - `git push . HEAD:space/<branch>` is REFUSED by Git: the target branch is
#     checked out in `.wopal`.
#   - `git update-ref` moves the ref but leaves `.wopal` immediately
#     inconsistent (D/M entries appear) — the same signature as the
#     2026-09-20 corruption. Never use it.
#   - One squash merge at validation time reproduces the feature tree exactly.
#     Squashing after every commit does not: squash creates new commit ids, so
#     the next squash loses the merge base and fails with add/add conflicts.

import hashlib
import re
import subprocess
from pathlib import Path

WORKTREE_DIR = ".worktrees"
BRANCH_PREFIX = "ontology-"

# Git branch names have no hard length limit, but commit-msg hooks and
# readability do; past this many characters a slug truncates with a 4-hex
# digest suffix (deterministic: the same name always truncates the same way).
SLUG_LIMIT = 55


class WorktreeError(Exception):
    """Raised when derivation or integration cannot complete safely."""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=str(cwd), capture_output=True, text=True)


def _zlines(result: subprocess.CompletedProcess) -> list[str]:
    return [token for token in result.stdout.split("\0") if token]


def slugify(name: str) -> str:
    """Turn a proposal name into a git-safe slug.

    Slashes are the reason this exists: git cannot create a branch that has
    both `ontology-a/b` and `ontology-a` as prefixes, so a proposal named
    after a path would produce a worktree that can never be integrated.

    Slugs longer than SLUG_LIMIT truncate to it with a 4-hex digest of the
    full name appended, keeping distinct long names distinct.
    """
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-._").lower()
    if len(slug) <= SLUG_LIMIT:
        return slug
    digest = hashlib.sha1(name.encode()).hexdigest()[:4]
    return f"{slug[:SLUG_LIMIT]}-{digest}"


def space_worktree_path(space_root: Path) -> Path:
    """The `.wopal` assembly worktree inside a space."""
    return space_root / ".wopal"


def derive_path(space_root: Path, slug: str) -> Path:
    return space_root / WORKTREE_DIR / f"{BRANCH_PREFIX}{slug}"


def branch_name(slug: str) -> str:
    return f"{BRANCH_PREFIX}{slug}"


def current_branch(repo: Path) -> str:
    result = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else ""


def worktree_exists(path: Path) -> bool:
    return (path / ".git").exists()


def reference_exists(repo: Path, ref: str) -> bool:
    result = _git(repo, "rev-parse", "--verify", "--quiet", ref)
    return result.returncode == 0


def derive(space_root: Path, slug: str, base_branch: str) -> Path:
    """Create an isolated worktree derived from `.wopal`.

    Returns the worktree path. Raises when the target already exists, the
    space worktree is missing, or the branch name is already taken.
    """
    wopal = space_worktree_path(space_root)
    if not wopal.is_dir():
        raise WorktreeError(
            f"space assembly worktree not found at {wopal}; cannot derive an "
            "isolated worktree"
        )

    target = derive_path(space_root, slug)
    if worktree_exists(target):
        raise WorktreeError(f"worktree already exists at {target}")

    branch = branch_name(slug)
    if reference_exists(wopal, f"refs/heads/{branch}"):
        raise WorktreeError(
            f"branch {branch!r} already exists; remove the stale branch or "
            "pick a different proposal name"
        )

    target.parent.mkdir(parents=True, exist_ok=True)

    # Run from `.wopal` so the sparse configuration and patterns are inherited.
    result = _run(
        wopal, "git", "worktree", "add", str(target), "-b", branch, base_branch
    )
    if result.returncode != 0:
        raise WorktreeError(
            f"failed to derive worktree at {target}: {result.stderr.strip()}"
        )
    return target


def assert_isolated(space_root: Path, worktree: Path) -> list[str]:
    """Return the invariant violations for a derived worktree.

    Empty list means the worktree is a faithful sparse copy of `.wopal`: it
    can still see everything the space can, its switch is on, and its bits
    are coherent.

    The range is compared as a **superset**, not for equality: the derived
    worktree widens its own range as it adds new capability directories, and
    a worktree that can see more than the space is exactly what an evolution
    looks like mid-flight. Losing a pattern is the failure, because that is
    the worktree no longer being able to see part of the space it was derived
    from.
    """
    from lib import sparse

    problems: list[str] = []
    wopal = space_worktree_path(space_root)

    space_patterns = sparse.read_patterns(wopal)
    derived_patterns = sparse.read_patterns(worktree)
    missing = [item for item in space_patterns if item not in derived_patterns]
    if missing:
        problems.append(
            f"derived worktree is missing {len(missing)} pattern(s) the space "
            f"has ({', '.join(missing[:5])}); it cannot see part of the space "
            "it was derived from"
        )

    if not sparse.is_enabled(worktree):
        problems.append("derived worktree has sparse checkout disabled")

    stranded = sparse.stranded_paths(worktree)
    if stranded:
        problems.append(
            f"{len(stranded)} index entr(ies) in the derived worktree sit "
            f"outside the range without a skip-worktree bit "
            f"({', '.join(stranded[:5])})"
        )

    drifted = sparse.drifted_paths(worktree)
    if drifted:
        problems.append(
            f"{len(drifted)} in-range path(s) in the derived worktree carry a "
            f"stray skip-worktree bit ({', '.join(drifted[:5])})"
        )

    return problems


def integrate(
    space_root: Path,
    feature_branch: str,
    message: str,
    worktree_path: Path | None = None,
) -> str | None:
    """Squash the feature branch into the space branch inside `.wopal`.

    The space worktree already has the space branch checked out, so the merge
    happens there and the host repository is untouched. This is the only
    integration path that leaves `.wopal` coherent.

    `worktree_path` is the isolated worktree the proposal recorded. When it
    is known it must exist and sit on `feature_branch`: the worktree's range
    is the widening source, so a missing or foreign worktree is refused —
    merging without it silently commits brand-new capabilities as off-disk
    skip-worktree entries (measured 2026-09-23: status clean, runtime
    invisible, every existing guard blind to it).

    Returns the resulting commit id, or None when the space branch was
    already up to date (nothing to integrate).
    """
    from lib import sparse

    wopal = space_worktree_path(space_root)
    current = current_branch(wopal)
    if not current.startswith("space/"):
        raise WorktreeError(
            f"space worktree is on '{current}', expected a 'space/*' branch; "
            "integration must not run from another branch"
        )

    if worktree_path is not None:
        if not worktree_exists(worktree_path):
            raise WorktreeError(
                f"the recorded worktree {worktree_path} is missing; re-run "
                "`evo.sh accept <name>` to re-attach a worktree to the "
                f"recorded branch (its commits are NOT lost — do not delete "
                f"{feature_branch!r})"
            )
        landed = current_branch(worktree_path)
        if landed != feature_branch:
            raise WorktreeError(
                f"the recorded worktree {worktree_path} is on {landed!r}, "
                f"not {feature_branch!r}; bring it back on the recorded "
                "branch before integrating (its commits are NOT lost)"
            )
        isolation = assert_isolated(space_root, worktree_path)
        if isolation:
            raise WorktreeError(
                "refusing to integrate: the isolated worktree failed the "
                "isolation checks: " + "; ".join(isolation)
            )

    problems = sparse.preflight(wopal)
    if problems:
        raise WorktreeError(
            "refusing to integrate while the space worktree is not coherent: "
            + "; ".join(problems)
        )

    status = _git(wopal, "status", "--porcelain")
    if status.stdout.strip():
        raise WorktreeError(
            "space worktree has uncommitted changes; commit or resolve them "
            "before integrating"
        )

    # New capability directories arrive on the feature branch, but the space
    # range is still the old one. `merge --squash` would then record them as
    # skip-worktree entries with no on-disk copy: committed, listed, and
    # invisible to the runtime — a brand-new capability that never loads.
    # Adopt the feature branch's range first, then merge.
    space_patterns = sparse.read_patterns(wopal)
    feature_patterns = _branch_patterns(wopal, feature_branch)
    additions = [item for item in feature_patterns if item not in space_patterns]
    if additions:
        result = _git(wopal, "sparse-checkout", "add", *additions)
        if result.returncode != 0:
            raise WorktreeError(
                f"failed to widen the space range with {additions}: "
                f"{result.stderr.strip()}"
            )

    staged = _run(wopal, "git", "merge", "--squash", feature_branch)
    if staged.returncode != 0:
        # Leave nothing half-merged, then report.
        _reset(wopal)
        raise WorktreeError(
            f"squash merge of '{feature_branch}' failed: {staged.stderr.strip()}"
        )

    # `merge --squash` stages its result but does not commit it. An empty
    # index means the space branch already has every change.
    staged_paths = _zlines(_git(wopal, "diff", "--cached", "--name-only", "-z"))
    if not staged_paths:
        return None

    # The poison-killer (2026-09-23): every path this integration is about
    # to commit must be visible to the runtime after the range is final. A
    # staged path outside the (already widened) range would be committed as
    # an off-disk skip-worktree entry — status clean, listed in the tree,
    # never materialized, never loaded. That is the silent capability-pool
    # poisoning the 2026-09-20 incident was made of, and no later guard can
    # see it. Widening sources can miss (a worktree range that never
    # declared a raw `git add --sparse` path); this assertion cannot.
    final_patterns = sparse.read_patterns(wopal)
    invisible = [
        path
        for path in staged_paths
        if not sparse.path_in_range(path, final_patterns)
    ]
    if invisible:
        _reset(wopal)
        raise WorktreeError(
            f"refusing to integrate: {len(invisible)} staged path(s) would "
            "be committed invisible to the runtime (outside the sparse "
            "range, so never materialized): "
            + ", ".join(invisible[:10])
            + "; widen the isolated worktree's range over them and commit "
            "again (evo.sh commit)"
        )

    # The range must be final before this runs: `reapply` materializes
    # whatever the range covers, so a widened-then-reapplied range is what
    # puts the new capability on disk.
    _git(wopal, "sparse-checkout", "reapply")

    committed = _run(wopal, "git", "commit", "-m", message)
    if committed.returncode != 0:
        _reset(wopal)
        raise WorktreeError(
            f"failed to commit the squash into the space branch: "
            f"{committed.stderr.strip()}"
        )

    head = _git(wopal, "rev-parse", "HEAD")
    return head.stdout.strip()


def _reset(repo: Path) -> None:
    """Undo a half-finished squash merge in the space worktree."""
    _git(repo, "reset", "--hard", "HEAD")
    _git(repo, "clean", "-fd", "--", ".")


def _branch_patterns(repo: Path, ref: str) -> list[str]:
    """The sparse patterns of the worktree that has `ref` checked out.

    The feature branch's own worktree is the authority on what the change
    needs: it widened its range as it added capability directories. An empty
    list means the branch has no worktree on disk, in which case the caller
    simply widens nothing — the merged content still lands, and the next
    `reapply` in that worktree will materialize it.
    """
    result = _git(repo, "worktree", "list", "--porcelain")
    current: Path | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current = Path(line.split(" ", 1)[1].strip())
        elif line.startswith("branch ") and current is not None:
            if line.split(" ", 1)[1].strip() == f"refs/heads/{ref}":
                from lib import sparse

                return sparse.read_patterns(current)
    return []
