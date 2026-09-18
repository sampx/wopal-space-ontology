"""GitHub CLI (gh) operations wrapper for dev-flow.

Provides subprocess-based gh CLI operations for Issue management.
Split from infra/git.py — this module handles only gh CLI commands.
"""

import subprocess


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


# Dev-flow status label mapping for --status filter.
# Key: user-facing status alias. Value: GitHub label name.
STATUS_LABEL_MAP = {
    "planning": "status/planning",
    "executing": "status/in-progress",
    "in-progress": "status/in-progress",
    "verifying": "status/verifying",
    "done": "status/done",
}

# User-facing status aliases accepted by --status.
STATUS_ALIASES = sorted(STATUS_LABEL_MAP.keys())


def build_issue_search_query(projects: list[str], statuses: list[str]) -> str:
    """Build a GitHub issue search query from project and status filters.

    Multiple projects are OR-combined; multiple statuses are OR-combined;
    projects and statuses are AND-combined (when both present).

    Args:
        projects: Project names (without 'project/' prefix).
        statuses: User-facing status aliases (planning/executing/in-progress/verifying/done).

    Returns:
        Search query string, or "" when no filters are given.

    Raises:
        ValueError: When a status alias is not recognized (never silently dropped,
            which would widen the result scope).
    """
    parts = []
    if projects:
        project_terms = [f"label:project/{p}" for p in projects]
        projects_clause = " OR ".join(project_terms)
        parts.append(f"({projects_clause})" if len(project_terms) > 1 else project_terms[0])
    if statuses:
        status_terms = []
        for s in statuses:
            label = STATUS_LABEL_MAP.get(s.lower())
            if label is None:
                raise ValueError(
                    f"Invalid status: {s}. Allowed: {', '.join(STATUS_ALIASES)}"
                )
            status_terms.append(f"label:{label}")
        statuses_clause = " OR ".join(status_terms)
        parts.append(f"({statuses_clause})" if len(status_terms) > 1 else status_terms[0])
    return " ".join(parts)


def list_issues(repo: str, state: str = "open", projects: list[str] | None = None,
                statuses: list[str] | None = None, limit: int = 50) -> list[dict] | None:
    """List Issues via gh CLI with optional project/status filtering.

    Args:
        repo: Repository in owner/repo format.
        state: Issue state filter (open/closed).
        projects: Optional project names to filter by (AND with statuses, OR among themselves).
        statuses: Optional user-facing status aliases to filter by.
        limit: Max issues to list.

    Returns:
        List of issue dicts (number, title, labels, url), or None on failure
        (gh unavailable or non-zero exit).
    """
    args = ['gh', 'issue', 'list', '--repo', repo, '--state', state, '--limit', str(limit)]
    query = build_issue_search_query(projects or [], statuses or [])
    if query:
        args.extend(['--search', query])
    args.extend(['--json', 'number,title,labels,url'])

    try:
        result = subprocess.run(args, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None

    import json
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

