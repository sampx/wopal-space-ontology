#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# sparse.py - Sparse-checkout primitives for the ontology-evolution skill.
#
# A sparse assembly worktree (`space/.wopal`) and any worktree derived from it
# carry three pieces of state that must agree with each other:
#
#   1. `core.sparseCheckout` - the switch that turns the range on
#   2. the pattern list      - the range itself
#   3. the skip-worktree bit - per-path derived state: "in the index, not on
#                              disk, and that is intentional"
#
# Disagreement between them is what destroys a capability pool, so every read
# and every write goes through this module instead of ad-hoc git calls.
#
# Empirical basis (probes run against temp repositories mirroring the real
# layout: host repo on `main`, `.wopal` on `space/<name>`, non-cone patterns):
#
#   - `git sparse-checkout disable` is the one command that clears BOTH the
#     config and every skip-worktree bit. `reapply` / `set` / `checkout` /
#     `reset --hard` / `add -A` all preserve both. Crucially, `disable` writes
#     `core.sparseCheckout=false` (it does not unset the key), so "the key is
#     missing" is NOT the corruption signature a reader would expect; "the
#     value is false" is.
#   - With the config and the bits gone, out-of-range entries (which have no
#     on-disk copy by design) read as "should exist, is missing". That is the
#     only state in which a plain `git add -A` records deletions of paths the
#     user never touched. Measured precisely: clearing the bit while the range
#     is still ON makes `git status` report ` D`, but `git add -A` still stages
#     nothing and git prints that the checkout is sparse; it is the range
#     being switched OFF that turns the same state into a staged deletion.
#     The guard therefore treats the two checks separately — the bit drift is
#     the warning, the missing range is the point of no return.
#   - `git add` / `git mv` refuse out-of-range paths unless `--sparse` is
#     passed, but `--sparse` only forces the entry into the index: it does NOT
#     widen the range, and the next range recompute (`reapply`, or the CLI's
#     `applySparsePatterns`) sweeps the file off disk. The correct move is to
#     widen the range first, then use plain git commands.
#   - A directory pattern must be added WITHOUT a duplicated trailing slash:
#     `sparse-checkout add "/skills/x//"` is accepted silently but matches
#     nothing, and the following `git add` then reports the file as being
#     outside the sparse definition.
#   - `git status --porcelain` collapses an untracked directory to a single
#     `?? dir/` entry without `-uall`; `git ls-files --others` reports the
#     real file paths regardless, which is what widening needs.

import subprocess
from pathlib import Path


class SparseError(Exception):
    """Raised when sparse state is missing, corrupt, or would be damaged."""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


def _clean(path: str) -> str:
    """Normalize a reported path: drop quotes and any trailing slash."""
    return path.strip().strip('"').strip("/")


# ── reads ───────────────────────────────────────────────────────────────


def is_enabled(repo: Path) -> bool:
    """True only when `core.sparseCheckout` is present AND set to true.

    `git sparse-checkout disable` leaves the key in place with the value
    `false`, so a presence-only test would read a disabled checkout as an
    enabled one.
    """
    result = _git(repo, "config", "--get", "core.sparseCheckout")
    if result.returncode != 0:
        return False
    return result.stdout.strip().lower() == "true"


def read_patterns(repo: Path) -> list[str]:
    """Return the non-cone sparse patterns, in applied order."""
    result = _git(repo, "sparse-checkout", "list")
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def path_in_range(path: str, patterns: list[str]) -> bool:
    """Whether a repository-relative path is covered by the sparse patterns.

    A pattern ending in `/` covers everything beneath it; any other pattern
    covers exactly one path. A bare `/` covers everything.
    """
    normalized = _clean(path)
    for pattern in patterns:
        candidate = pattern.strip()
        if not candidate:
            continue
        if candidate.strip("/") == "":
            return True
        if candidate.endswith("/"):
            prefix = candidate.strip("/")
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif normalized == _clean(candidate):
            return True
    return False


def _index_entries(repo: Path) -> list[tuple[str, bool]]:
    """Parse `git ls-files --debug` into (path, has_skip_worktree) pairs.

    The raw `flags` field is used rather than the `-t` tag letter: measured,
    `ls-files -t` reports `H` for an in-range entry whose flags are `0x4000`,
    so the tag letter does not track the bit. CE_SKIP_WORKTREE is `0x4000`,
    and out-of-range entries additionally carry `0x40000000` (`40004000`),
    which is why the test is a mask rather than an equality.
    """
    result = _git(repo, "ls-files", "--debug")
    entries: list[tuple[str, bool]] = []
    path: str | None = None
    for line in result.stdout.splitlines():
        if not line.startswith((" ", "\t")):
            path = line.strip()
            continue
        if path is None or "flags:" not in line:
            continue
        raw = line.split("flags:", 1)[1].strip()
        try:
            flags = int(raw, 16)
        except ValueError:
            path = None
            continue
        entries.append((path, bool(flags & 0x4000)))
        path = None
    return entries


def stranded_paths(repo: Path) -> list[str]:
    """Index entries outside the range that lack the skip-worktree bit.

    Measured behaviour, three states:

    | range | bit | on disk | `git status` | `git add -A` |
    |---|---|---|---|---|
    | on | set | no | clean | clean |
    | on | clear | no | ` D` | stages nothing (git refuses) |
    | off | clear | no | ` D` | **stages the deletion** |

    So a cleared bit alone is a warning, not yet the disaster: git still
    holds the line while the range is on. It becomes destructive the moment
    the range is switched off — which is what `git sparse-checkout disable`
    does — because nothing is left to tell git that the missing on-disk copy
    is intentional. This is the 2026-09-20 shape: entries outside the range
    with flags at 0, and the file removal waiting to be recorded.
    """
    patterns = read_patterns(repo)
    if not patterns:
        return []
    return [
        path
        for path, skip in _index_entries(repo)
        if not skip and not path_in_range(path, patterns)
    ]


def drifted_paths(repo: Path) -> list[str]:
    """Paths inside the range that nevertheless carry a skip-worktree bit.

    The mirror image of `stranded_paths`, and equally a sign that the index
    and the range no longer describe the same tree. The remedy is a range
    recompute (`git sparse-checkout reapply`), not a commit.
    """
    patterns = read_patterns(repo)
    if not patterns:
        return []
    return [
        path
        for path, skip in _index_entries(repo)
        if skip and path_in_range(path, patterns)
    ]


def unmerged_paths(repo: Path) -> list[str]:
    """Paths left in a conflicted state by an incomplete merge."""
    result = _git(repo, "diff", "--name-only", "-z", "--diff-filter=U")
    return [path for path in result.stdout.split("\0") if path]


def untracked_paths(repo: Path) -> list[str]:
    """New paths on disk that git does not track yet.

    Reported per file, including files inside out-of-range directories —
    which is exactly what a widening decision has to see.

    Ignored paths are excluded (`--exclude-standard`), so a repository that
    ignores its build output never sees it here.
    """
    result = _git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    return [path for path in result.stdout.split("\0") if path]


# Byte-code caches, dependency trees and test caches are transient build
# output. They must never enter a commit (the space constitution forbids it),
# and a repository that simply forgot to ignore them would otherwise have
# them swept in by the next `evo.sh commit`.
TRANSIENT_SEGMENTS = frozenset(
    {
        "__pycache__",
        "node_modules",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        ".tox",
        "dist",
        "build",
    }
)


def is_transient(path: str) -> bool:
    """Whether a path is build output rather than authored content."""
    return any(segment in TRANSIENT_SEGMENTS for segment in path.split("/"))


# ── writes ──────────────────────────────────────────────────────────────


def _pattern_for(path: str) -> str | None:
    """The range addition that covers `path`, at directory granularity.

    A new capability arrives as a directory (`/skills/<name>/`), so the parent
    directory is the natural unit; for a file sitting directly in the
    repository root there is no narrower form than the exact path. The
    trailing slash is applied exactly once — a doubled slash is accepted by
    git and silently matches nothing.
    """
    cleaned = _clean(path)
    if not cleaned:
        return None
    parent = str(Path(cleaned).parent).strip("/")
    if parent in ("", "."):
        return f"/{cleaned}"
    return f"/{parent}/"


def widen(repo: Path, paths: list[str]) -> list[str]:
    """Widen the sparse range to cover `paths`; return the patterns added.

    Widening is additive: the range only grows, and no skip-worktree bit is
    ever cleared. `git sparse-checkout add` inherits the existing non-cone
    mode, so no mode flag is passed.
    """
    patterns = read_patterns(repo)
    additions: list[str] = []
    for path in paths:
        if path_in_range(path, patterns):
            continue
        pattern = _pattern_for(path)
        if pattern is None or pattern in additions:
            continue
        additions.append(pattern)

    if not additions:
        return []

    result = _git(repo, "sparse-checkout", "add", *additions)
    if result.returncode != 0:
        raise SparseError(
            f"failed to widen the sparse range with {additions}: "
            f"{result.stderr.strip()}"
        )
    return additions


# ── preflight ───────────────────────────────────────────────────────────


def preflight(repo: Path) -> list[str]:
    """Return the problems that make a commit unsafe; empty list means safe.

    Callers must refuse to write when this returns anything: each entry is a
    state in which staging "all changes" would record files the user never
    touched.
    """
    problems: list[str] = []

    if not is_enabled(repo):
        problems.append(
            "sparse checkout is not enabled (core.sparseCheckout is unset or "
            "false); commit refused, because out-of-range files would be "
            "staged as deletions"
        )
        return problems

    patterns = read_patterns(repo)
    if not patterns:
        problems.append(
            "the sparse pattern list is empty; commit refused, because the "
            "range cannot be verified and out-of-range files would be staged "
            "as deletions"
        )
        return problems

    unmerged = unmerged_paths(repo)
    if unmerged:
        problems.append(
            f"{len(unmerged)} path(s) are in an unresolved merge state "
            f"({', '.join(unmerged[:5])}); finish the merge before committing"
        )

    stranded = stranded_paths(repo)
    if stranded:
        problems.append(
            f"{len(stranded)} index entr(ies) outside the sparse range carry "
            f"no skip-worktree bit ({', '.join(stranded[:5])}); the range and "
            "the bits disagree, and if the range is switched off these become "
            "recorded deletions — commit refused (run "
            "`git sparse-checkout reapply` to restore the bits)"
        )

    drifted = drifted_paths(repo)
    if drifted:
        problems.append(
            f"{len(drifted)} in-range path(s) carry a stray skip-worktree bit "
            f"({', '.join(drifted[:5])}); the range and the index disagree — "
            "commit refused (run `git sparse-checkout reapply` to restore them)"
        )

    return problems
