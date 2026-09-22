#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# repo.py - Resolve the ontology repository that contains the skill.
#
# The scripts live nested inside the skill directory but operate on the
# ontology repository around them. The root is discovered, never
# hard-coded, so the same script works from a sparse assembly worktree
# (`.wopal`) and from an isolated implementation worktree alike.

import os
import subprocess
from pathlib import Path

ENV_OVERRIDE = "WOPAL_EVOLUTION_REPO_ROOT"
EVOLUTIONS_DIR = "docs/evolutions"


class RepoRootError(Exception):
    """Raised when the ontology repository root cannot be located."""


def _git_toplevel(start: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    candidate = result.stdout.strip()
    return Path(candidate) if candidate else None


def _marker_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / EVOLUTIONS_DIR).is_dir():
            return candidate
    return None


def resolve_repo_root(start: str | os.PathLike) -> Path:
    """Return the ontology repository root containing ``start``.

    Resolution order: explicit environment override, git toplevel, then a
    directory-tree marker. The override lets callers (and tests) point the
    scripts at an isolated repository.
    """
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(override).resolve()

    start_path = Path(start).resolve()
    toplevel = _git_toplevel(start_path)
    if toplevel is not None:
        return toplevel.resolve()

    marker = _marker_root(start_path)
    if marker is not None:
        return marker.resolve()

    raise RepoRootError(
        f"cannot locate the ontology repository containing {start_path}; "
        f"set {ENV_OVERRIDE} to point at it explicitly"
    )


def evolutions_root(repo_root: Path) -> Path:
    return repo_root / EVOLUTIONS_DIR


def archived_root(repo_root: Path) -> Path:
    return evolutions_root(repo_root) / "archived"
