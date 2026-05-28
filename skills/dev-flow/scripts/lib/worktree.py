#!/usr/bin/env python3
# worktree.py - Git worktree operations for dev-flow
#
# Replaces worktree.sh with pure Python implementation using subprocess git.
# Uses lib/workspace.py for workspace detection (not .workspace.md).
#
# Provides:
#   - scan_projects: Scan workspace for git projects
#   - create_worktree: Create a git worktree
#   - list_worktrees: List worktrees filtered by base path
#   - remove_worktree: Remove a git worktree (with --force fallback)
#   - delete_branch: Delete a local branch (with -D fallback)
#   - clean_worktree: One-stop cleanup (remove_worktree + delete_branch)

import os
import subprocess
from pathlib import Path


def scan_projects(workspace_root: Path) -> list[str]:
    """Scan workspace root for git project directories.

    Uses os.listdir to scan subdirectories, detecting those containing .git.
    Does not depend on .workspace.md.

    Args:
        workspace_root: Workspace root path

    Returns:
        List of project directory names (not full paths)
    """
    projects = []
    if not workspace_root.is_dir():
        return projects

    for entry in os.listdir(workspace_root):
        entry_path = workspace_root / entry
        if entry_path.is_dir():
            git_path = entry_path / ".git"
            if git_path.exists():
                projects.append(entry)

    return sorted(projects)


def create_worktree(project_dir: Path, branch: str, worktree_base: Path) -> Path:
    """Create a git worktree for a project.

    Args:
        project_dir: Path to the project's git root directory
        branch: Branch name for the worktree
        worktree_base: Base directory where worktrees are stored

    Returns:
        Path to the created worktree directory

    Raises:
        RuntimeError: If worktree creation fails
    """
    project_name = project_dir.name
    worktree_path = worktree_base / f"{project_name}-{branch}"

    # Ensure worktree_base exists
    worktree_base.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path), branch],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Try with HEAD if branch doesn't exist yet — create new branch
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(worktree_path), "HEAD"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to create worktree at {worktree_path}: {result.stderr.strip()}"
            )

    return worktree_path


def list_worktrees(worktree_base: Path, project: str | None = None) -> list[str]:
    """List worktrees filtered by base path.

    Args:
        worktree_base: Base directory where worktrees are stored
        project: Optional project name to filter by

    Returns:
        List of worktree paths (as strings)
    """
    # Find a git repo to run 'git worktree list' from
    # walk up from worktree_base to find a git repo
    search_dir = worktree_base
    git_dir = None
    for parent in [search_dir] + list(search_dir.parents):
        if (parent / ".git").exists():
            git_dir = parent
            break

    if git_dir is None:
        return []

    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=str(git_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    # Parse porcelain output: each worktree is separated by blank lines
    # Lines start with "worktree " followed by the path
    worktrees = []
    for line in result.stdout.strip().split('\n'):
        if line.startswith("worktree "):
            wt_path = line[len("worktree "):]
            # Filter by worktree_base prefix
            try:
                wt = Path(wt_path)
                if wt.is_relative_to(worktree_base) or str(wt).startswith(str(worktree_base)):
                    if project is None or project in wt.name:
                        worktrees.append(wt_path)
            except (ValueError, OSError):
                pass

    return worktrees


def remove_worktree(project_dir: Path, branch: str, worktree_base: Path) -> None:
    """Remove a git worktree (equivalent to worktree.sh cmd_remove).

    Tries git worktree remove, then --force on failure.
    Always runs git worktree prune afterwards.

    Args:
        project_dir: Path to the project's git root directory
        branch: Branch name of the worktree
        worktree_base: Base directory where worktrees are stored
    """
    project_name = project_dir.name
    worktree_path = worktree_base / f"{project_name}-{branch}"

    if worktree_path.exists():
        # Try normal remove
        result = subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Force remove on failure
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
            )

    # Always prune (whether remove succeeded or path didn't exist)
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )


def delete_branch(git_dir: Path, branch: str) -> bool:
    """Delete a local branch (git branch -d, then -D on failure).

    Skips if branch is the current branch.

    Args:
        git_dir: Path to git repository root
        branch: Branch name to delete

    Returns:
        True if branch was deleted, False if skipped or failed
    """
    # Check current branch — skip if it's the branch to delete
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(git_dir),
        capture_output=True,
        text=True,
    )
    current = result.stdout.strip()
    if current == branch:
        return False

    # Try soft delete (-d)
    result = subprocess.run(
        ["git", "branch", "-d", branch],
        cwd=str(git_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return True

    # Force delete (-D) on failure
    result = subprocess.run(
        ["git", "branch", "-D", branch],
        cwd=str(git_dir),
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def clean_worktree(project_dir: Path, branch: str, worktree_base: Path) -> dict:
    """One-stop cleanup for archive.py (equivalent to worktree.sh remove).

    Performs: remove_worktree + delete_branch
    Returns a result dict for callers to report.

    Args:
        project_dir: Path to the project's git root directory
        branch: Branch name of the worktree
        worktree_base: Base directory where worktrees are stored

    Returns:
        {"removed": bool, "branch_deleted": bool, "errors": list[str]}
    """
    errors = []

    # 1. Remove worktree
    removed = False
    try:
        remove_worktree(project_dir, branch, worktree_base)
        removed = True
    except Exception as e:
        errors.append(f"Failed to remove worktree: {e}")

    # 2. Delete branch
    branch_deleted = False
    try:
        branch_deleted = delete_branch(project_dir, branch)
        if not branch_deleted:
            # Branch might not exist or is current — not an error
            pass
    except Exception as e:
        errors.append(f"Failed to delete branch: {e}")

    return {
        "removed": removed,
        "branch_deleted": branch_deleted,
        "errors": errors,
    }
