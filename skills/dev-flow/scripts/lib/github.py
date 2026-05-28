"""GitHub CLI (gh) operations wrapper for dev-flow.

Provides subprocess-based gh CLI operations for Issue management.
Split from infra/git.py — this module handles only gh CLI commands.
"""

import subprocess


def _check_gh_available() -> bool:
    """Check if gh CLI is available."""
    try:
        result = subprocess.run(
            ['gh', '--version'],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_issue(repo: str, title: str, body: str = "", labels: list[str] | None = None) -> str:
    """Create a GitHub Issue.

    Args:
        repo: Repository in owner/repo format
        title: Issue title
        body: Issue body (optional)
        labels: List of label names (optional)

    Returns:
        Issue URL string, or empty string if creation failed
    """
    args = ['gh', 'issue', 'create', '--repo', repo, '--title', title]
    if body:
        args.extend(['--body', body])
    if labels:
        for label in labels:
            args.extend(['--label', label])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    return ""


def update_issue(repo: str, issue_number: int | str, title: str | None = None,
                 body: str | None = None, labels: list[str] | None = None) -> bool:
    """Update a GitHub Issue.

    Args:
        repo: Repository in owner/repo format
        issue_number: Issue number
        title: New title (optional)
        body: New body (optional)
        labels: New labels (optional, replaces all labels)

    Returns:
        True if update succeeded
    """
    args = ['gh', 'issue', 'edit', str(issue_number), '--repo', repo]
    if title is not None:
        args.extend(['--title', title])
    if body is not None:
        args.extend(['--body', body])
    if labels is not None:
        for label in labels:
            args.extend(['--add-label', label])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_issue(repo: str, issue_number: int | str) -> dict | None:
    """Get Issue details via gh CLI.

    Args:
        repo: Repository in owner/repo format
        issue_number: Issue number

    Returns:
        Dict with issue fields (title, body, labels, state, etc.), or None
    """
    try:
        result = subprocess.run(
            ['gh', 'issue', 'view', str(issue_number), '--repo', repo,
             '--json', 'title,body,labels,state,number'],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except (FileNotFoundError, Exception):
        pass

    return None


def add_labels(repo: str, issue_number: int | str, labels: list[str]) -> bool:
    """Add labels to a GitHub Issue.

    Args:
        repo: Repository in owner/repo format
        issue_number: Issue number
        labels: List of label names to add

    Returns:
        True if labels were added successfully
    """
    if not labels:
        return True

    args = ['gh', 'issue', 'edit', str(issue_number), '--repo', repo]
    for label in labels:
        args.extend(['--add-label', label])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_issue_labels(issue_number: int | str, repo: str) -> list[str]:
    """Get current labels for an issue.

    Args:
        issue_number: Issue number
        repo: Repository in owner/repo format

    Returns:
        List of label names
    """
    try:
        result = subprocess.run(
            ['gh', 'issue', 'view', str(issue_number), '--repo', repo,
             '--json', 'labels', '--jq', '.labels[].name'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
