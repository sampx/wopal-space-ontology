# project.py - Project path/type/repo resolution
#
# Unified project resolution, replacing scattered _find_project_path copies
# in archive.py and approve.py. All repo and base branch info is dynamically
# inferred from git — no hardcoded GitHub org/repo/branch.
#
# Resolution priority for path:
#   1. Project Path from Plan metadata (declared path)
#   2. Fallback: projects/<project_name> (backward compat)
#   3. Fallback: search workspace root children for directory matching
#      <project_name>, then walk up to find the git root

import re
from enum import Enum
from pathlib import Path
import subprocess

from dev_flow.domain.plan.metadata import get_plan_field


class ProjectType(Enum):
    """Project type enumeration."""
    STANDARD = "standard"
    ONTOLOGY_WORKTREE = "ontology-worktree"


def _get_wopal_repo_name(workspace_root: Path) -> str | None:
    """Get the GitHub repo short name from .wopal's origin remote.

    Returns the repo name after the owner/ prefix (e.g., "wopal-space-ontology"),
    or None if .wopal is not a worktree or can't read its remote.
    """
    dot_git = workspace_root / ".wopal" / ".git"
    if not dot_git.exists() or not dot_git.is_file():
        return None

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=workspace_root / ".wopal",
            capture_output=True, text=True, check=True,
        )
        repo = _parse_github_repo_url(result.stdout.strip())
        if repo:
            return repo.split("/")[-1]
    except subprocess.CalledProcessError:
        pass

    return None


def resolve_project_type(project_name: str, workspace_root: Path | None = None) -> ProjectType:
    """Resolve project type from workspace structure.

    Checks if .wopal is a git worktree whose origin remote matches
    the project name. No hardcoded registry — fully derived from git.

    Args:
        project_name: Project name from Plan metadata
        workspace_root: Workspace root for dynamic detection

    Returns:
        ProjectType enum value.
    """
    if workspace_root:
        repo_name = _get_wopal_repo_name(workspace_root)
        if repo_name and repo_name == project_name:
            return ProjectType.ONTOLOGY_WORKTREE
    return ProjectType.STANDARD


def resolve_project_info(project_name: str, workspace_root: Path) -> tuple[ProjectType, str | None]:
    """Resolve project type and workspace-relative path.

    Derives the mapping from .wopal's git remote — if .wopal is a worktree
    and its origin remote repo name matches the project name, this is an
    ontology-worktree project at ".wopal". No configuration needed.

    Args:
        project_name: Project name
        workspace_root: Workspace root path

    Returns:
        Tuple of (ProjectType, workspace_relative_path or None)
    """
    repo_name = _get_wopal_repo_name(workspace_root)
    if repo_name and repo_name == project_name:
        return ProjectType.ONTOLOGY_WORKTREE, ".wopal"
    return ProjectType.STANDARD, None


def _parse_github_repo_url(url: str) -> str | None:
    """Parse GitHub remote URL to owner/repo format.

    Handles:
      - https://github.com/owner/repo.git
      - https://github.com/owner/repo
      - git@github.com:owner/repo.git

    Returns:
        "owner/repo" string, or None if URL can't be parsed.
    """
    match = re.search(r'github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$', url)
    if match:
        return match.group(1)
    return None


def _get_default_branch(project_path: Path) -> str:
    """Detect the remote default branch for a git repository.

    Uses git ls-remote --symref to query the ACTUAL remote HEAD,
    not the locally-cached refs/remotes/origin/HEAD (which can be
    stale for forks that inherited the upstream's HEAD).

    Args:
        project_path: Path to git repository

    Returns:
        Default branch name (e.g., "main"), falls back to "main".
    """
    # 1. Query remote HEAD (fast, always accurate)
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--symref", "origin", "HEAD"],
            cwd=project_path,
            capture_output=True, text=True, check=True,
        )
        # Parse: "ref: refs/heads/main\tHEAD\n<hash>\tHEAD"
        first_line = result.stdout.strip().split("\n")[0]
        if first_line.startswith("ref: refs/heads/"):
            return first_line.split("/")[-1].split("\t")[0]
    except subprocess.CalledProcessError:
        pass

    # 2. Fall back to local cache (no network)
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=project_path,
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip().split("/")[-1]
    except subprocess.CalledProcessError:
        pass

    # 3. Ultimate fallback
    return "main"


def resolve_project_repo(project_path: Path) -> tuple[str | None, str]:
    """Dynamically resolve GitHub repo and base branch from project path.

    Uses git commands:
      - repo: 'git remote get-url origin' → parsed to owner/repo
      - base_branch: from project's git state

    For ONTOLOGY_WORKTREE projects (.git is a file = worktree pointer),
    the base branch is the current branch (space/<name>).
    For standard projects, the base branch is detected from the remote
    via git ls-remote --symref (queries actual remote HEAD, not stale
    local cache that forks inherit from upstream).

    Args:
        project_path: Path to project's git root directory

    Returns:
        Tuple of (repo, base_branch).
        repo is None if git remote is unavailable.
    """
    if not project_path.exists():
        return None, "main"

    # Repo from git remote
    repo = None
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            capture_output=True, text=True, check=True,
        )
        repo = _parse_github_repo_url(result.stdout.strip())
    except subprocess.CalledProcessError:
        pass

    # Base branch
    dot_git = project_path / ".git"
    if dot_git.exists() and dot_git.is_file():
        # Ontology worktree: base = current branch (space/<name>)
        base_branch = get_current_branch(project_path) or "main"
    else:
        # Standard project: detect from remote HEAD
        base_branch = _get_default_branch(project_path)

    return repo, base_branch


def resolve_project_path(
    plan_path: str,
    project_name: str,
    workspace_root: Path,
) -> Path | None:
    """Resolve project's git root directory path.

    Resolution order:
      1. Read 'Project Path' from Plan metadata → find git root → return
      2. Fallback projects/<project_name> → return if it's a git repo
      3. Search workspace children for dir named <project_name>,
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
    declared = get_plan_field(plan_path, "Project Path")
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


def get_current_branch(repo_path: Path) -> str | None:
    """Get current branch name from git repository.

    Args:
        repo_path: Path to git repository (can be worktree root)

    Returns:
        Branch name (e.g., "space/main", "main"), or None if not on any branch
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        return branch if branch and branch != "HEAD" else None
    except subprocess.CalledProcessError:
        return None


def get_ontology_main_repo(workspace_root: Path) -> Path | None:
    """Resolve ontology main repository path from .wopal/.git file.

    The .wopal/.git file is a worktree pointer with format:
        gitdir: /path/to/main/repo/.git/worktrees/-wopal

    Args:
        workspace_root: Workspace root path

    Returns:
        Path to ontology main repository, or None if not resolvable
    """
    dot_git_path = workspace_root / ".wopal" / ".git"

    if not dot_git_path.exists() or not dot_git_path.is_file():
        return None

    try:
        content = dot_git_path.read_text().strip()
        # Format: "gitdir: /path/to/.git/worktrees/-wopal"
        if content.startswith("gitdir: "):
            gitdir_path = content[len("gitdir: "):].strip()
            # Extract main repo: remove /.git/worktrees/-wopal suffix
            # gitdir: /Users/sam/.wopal/ontologies/wopal-space-ontology/.git/worktrees/-wopal
            # main repo: /Users/sam/.wopal/ontologies/wopal-space-ontology
            if "/.git/worktrees/" in gitdir_path:
                main_repo = gitdir_path.split("/.git/worktrees/")[0]
                return Path(main_repo)
    except Exception:
        return None

    return None
