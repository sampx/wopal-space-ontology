# project.py - Project path resolution
#
# Unified project path resolution, replacing scattered _find_project_path
# copies in archive.py and approve.py.
#
# Resolution priority:
#   1. Target Project Path from Plan metadata (declared path)
#   2. Fallback: projects/<project_name> (backward compat)
#   3. Fallback: search workspace root children for directory matching
#      <project_name>, then walk up to find the git root

from pathlib import Path

from dev_flow.domain.plan.metadata import get_plan_field


def resolve_project_path(
    plan_path: str,
    project_name: str,
    workspace_root: Path,
) -> Path | None:
    """Resolve project's git root directory path.

    Resolution order:
      1. Read `Target Project Path` from Plan metadata → find git root → return
      2. Fallback `projects/<project_name>` → return if it's a git repo
      3. Search workspace children for dir named `<project_name>`,
         walk up to git root → return

    Returns the directory containing .git (repo root or worktree root),
    not necessarily the project source directory.

    Args:
        plan_path: Path to Plan markdown file
        project_name: Project name from Plan metadata (for fallback)
        workspace_root: Workspace root path

    Returns:
        Absolute path to git root directory, or None
    """
    # Step 1: Plan-declared path
    declared = get_plan_field(plan_path, "Target Project Path")
    if declared:
        candidate = workspace_root / declared
        git_root = _find_git_root(candidate)
        if git_root:
            return git_root

    # Step 2: Backward compat fallback
    if project_name:
        candidate = workspace_root / "projects" / project_name
        git_root = _find_git_root(candidate)
        if git_root:
            return git_root

    # Step 3: Search workspace children for matching directory
    if project_name:
        for entry in workspace_root.iterdir():
            if entry.is_dir():
                candidate = entry / project_name
                git_root = _find_git_root(candidate)
                if git_root:
                    return git_root

    return None


def _find_git_root(path: Path) -> Path | None:
    """Find git root by checking path/.git, then parent/.git.

    Only checks the given path and its immediate parent, not
    walking up to filesystem root. Prevents accidentally matching
    a workspace-level .git when the project is not a git repo.
    """
    if not path.exists():
        return None
    if (path / ".git").exists():
        return path
    parent = path.parent
    if (parent / ".git").exists():
        return parent
    return None


def _is_git_repo(project_path: Path) -> bool:
    """Check if path is inside a git repository.

    Shortcut for _find_git_root() is not None.
    """
    return _find_git_root(project_path) is not None