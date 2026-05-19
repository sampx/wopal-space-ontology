"""Shared commit helpers for dev-flow complete and archive commands.

Contains commit message building logic and commit-only operations.
Push is handled separately by the archive command.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from dev_flow.core.logging import log_info, log_success, log_error, log_warn, log_step
from dev_flow.infra.git import has_uncommitted_changes, get_current_branch, push_branch


# Plan type to git commit type mapping
_PLAN_TYPE_TO_COMMIT = {
    'feature': 'feat',
    'enhance': 'enhance',
    'fix': 'fix',
    'refactor': 'refactor',
    'docs': 'docs',
    'test': 'test',
    'chore': 'chore',
    'perf': 'perf',
}

_MAX_COMMIT_FIRST_LINE = 72


def _get_issue_title(issue_number: int, repo: str) -> str | None:
    """Get Issue title via gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'issue', 'view', str(issue_number), '--repo', repo,
             '--json', 'title', '--jq', '.title'],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _parse_plan_name_for_commit(plan_name: str) -> tuple[str, str]:
    """Parse plan name to (type, rest) for commit message.

    Plan name format (after stripping issue prefix and date prefix):
        <type>-<scope>-<slug>

    Returns (type, rest) where rest covers scope + slug as one string.
    """
    name = Path(plan_name).stem
    name = re.sub(r'^\d{8}-', '', name)
    name = re.sub(r'^[0-9]+-', '', name)

    match = re.match(r'^([a-z]+)-(.+)$', name)
    if match:
        return match.group(1), match.group(2)
    return 'chore', name


def _slug_to_description(slug: str) -> str:
    """Convert hyphen-separated slug to space-separated description."""
    return slug.replace('-', ' ')


def build_commit_message(
    plan_name: str,
    plan_type: str,
    issue_number: int | None,
    repo: str | None,
) -> str:
    """Build descriptive commit message from Issue title or Plan name.

    - Issue-driven: ``<Issue title> (#N)``  (≤72 chars, truncates if needed)
    - No Issue: ``<type>: <description>``  (≤72 chars)
    """
    if issue_number and repo:
        title = _get_issue_title(issue_number, repo)
        if title:
            suffix = f" (#{issue_number})"
            total_len = len(title) + len(suffix)
            if total_len <= _MAX_COMMIT_FIRST_LINE:
                return f"{title}{suffix}"
            m = re.match(r'^([a-z]+\([^)]+\):\s*)(.*)$', title)
            if m:
                prefix, desc = m.group(1), m.group(2)
                max_desc = _MAX_COMMIT_FIRST_LINE - len(prefix) - len(suffix)
                return f"{prefix}{desc[:max_desc]}{suffix}"

    parsed_type, slug = _parse_plan_name_for_commit(plan_name)
    effective_type = _PLAN_TYPE_TO_COMMIT.get(parsed_type, plan_type) or 'chore'
    description = _slug_to_description(slug)
    msg = f"{effective_type}: {description}"
    if len(msg) > _MAX_COMMIT_FIRST_LINE:
        prefix_len = len(f"{effective_type}: ")
        description = description[:_MAX_COMMIT_FIRST_LINE - prefix_len]
        msg = f"{effective_type}: {description}"
    return msg


def commit_project_changes(
    project_path: str,
    plan_type: str,
    issue_number: int | None,
    plan_name: str | None = None,
    repo: str | None = None,
) -> bool:
    """Commit (but NOT push) project repo changes.

    Returns:
        True if commit succeeded (or nothing to commit).
    """
    if plan_name:
        commit_msg = build_commit_message(plan_name, plan_type, issue_number, repo)
    else:
        commit_type = _PLAN_TYPE_TO_COMMIT.get(plan_type, 'chore')
        if issue_number:
            commit_msg = f"{commit_type}: implement plan changes (#{issue_number})"
        else:
            commit_msg = f"{commit_type}: implement plan changes"

    subprocess.run(
        ["git", "add", "-A"],
        cwd=project_path,
        capture_output=True,
    )

    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=project_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        if "nothing to commit" in result.stdout:
            log_info("No changes to commit in project repo")
            return True
        log_error(f"Project commit failed: {result.stderr.strip()}")
        return False

    log_success(f"Project committed: {commit_msg}")
    return True


def commit_ontology_worktree(
    workspace_root: Path,
    plan_type: str,
    issue_number: int | None,
    plan_name: str | None = None,
    repo: str | None = None,
) -> bool:
    """Commit (but NOT push) ontology worktree changes.

    Ontology worktree (.wopal/) commits directly to space/<space-name> branch.
    Push is handled by archive.
    """
    ontology_path = workspace_root / ".wopal"

    if not ontology_path.exists():
        log_error("Ontology worktree path not found: .wopal/")
        return False

    if not has_uncommitted_changes(str(ontology_path)):
        log_info("No uncommitted changes in ontology worktree")
        return True

    branch = get_current_branch(ontology_path)
    if not branch:
        log_error("Cannot resolve ontology worktree branch")
        return False

    if plan_name:
        commit_msg = build_commit_message(plan_name, plan_type, issue_number, repo)
    else:
        commit_type = _PLAN_TYPE_TO_COMMIT.get(plan_type, 'chore')
        if issue_number:
            commit_msg = f"{commit_type}: implement plan changes (#{issue_number})"
        else:
            commit_msg = f"{commit_type}: implement plan changes"

    log_step(f"Committing ontology changes to {branch}...")

    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(ontology_path),
        capture_output=True,
    )

    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=str(ontology_path),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        if "nothing to commit" in result.stdout:
            log_info("No changes to commit in ontology worktree")
            return True
        log_error(f"Ontology commit failed: {result.stderr.strip()}")
        return False

    log_success(f"Ontology committed: {commit_msg}")
    return True


def push_project_changes(project_path: str) -> bool:
    """Push project repo changes to origin/main.

    Returns:
        True if push succeeded.
    """
    if not push_branch(project_path, 'main'):
        log_error("Project push failed")
        return False
    log_success("Project pushed to origin/main")
    return True


def push_ontology_worktree(workspace_root: Path) -> bool:
    """Push ontology worktree changes to origin.

    Returns:
        True if push succeeded.
    """
    ontology_path = workspace_root / ".wopal"
    branch = get_current_branch(ontology_path)
    if not branch:
        log_error("Cannot resolve ontology worktree branch")
        return False

    if not push_branch(str(ontology_path), branch):
        log_error("Ontology push failed")
        return False
    log_success(f"Ontology pushed to origin/{branch}")
    return True
