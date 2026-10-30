"""Read-only child Plan resolution for umbrella lifecycle gates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from plan import (
    find_plan_by_name,
    get_child_plan_entries,
    get_plan_issue,
    get_plan_project,
    get_plan_status,
    get_plan_worktree,
)
from lib.project import resolve_plan_location


@dataclass(frozen=True)
class ChildPlanState:
    name: str
    declared_project: str
    responsibility: str
    path: Path | None
    project: str
    issue: int | None
    status: str
    missing: bool


def _find_archived_child(name: str, workspace_root: Path) -> Path | None:
    plans_root = workspace_root / ".wopal-space" / "plans"
    if not plans_root.is_dir():
        return None
    suffix = f"-{name}.md"
    matches = sorted(
        candidate
        for candidate in plans_root.glob("*/done/*.md")
        if candidate.name == f"{name}.md" or candidate.name.endswith(suffix)
    )
    return matches[0] if len(matches) == 1 else None


def _find_declared_child(
    name: str, declared_project: str, workspace_root: Path
) -> tuple[Path | None, bool]:
    """Resolve a child using its declared project before global name lookup.

    Plan names are not globally unique across projects. The Child Plans table
    already carries Target Project specifically enough to disambiguate the
    normal case, so use that scope first.
    """
    if declared_project:
        project_dir = workspace_root / ".wopal-space" / "plans" / declared_project
        active = project_dir / f"{name}.md"
        if active.is_file():
            return active, False

        done_dir = project_dir / "done"
        if done_dir.is_dir():
            suffix = f"-{name}.md"
            archived = sorted(
                candidate
                for candidate in done_dir.glob("*.md")
                if candidate.name == f"{name}.md" or candidate.name.endswith(suffix)
            )
            if len(archived) == 1:
                return archived[0], True

        # The declaration is the disambiguator. If that project does not
        # contain the child, do not silently bind a same-named Plan from a
        # different project.
        return None, False

    try:
        path = Path(find_plan_by_name(name, workspace_root))
        return path, path.parent.name == "done"
    except (FileNotFoundError, ValueError):
        path = _find_archived_child(name, workspace_root)
        return path, path is not None


def _active_child_path(plan_path: Path, workspace_root: Path) -> Path:
    """Prefer a live worktree copy when one exists."""
    wt = get_plan_worktree(str(plan_path))
    if not wt or not wt.get("path"):
        return plan_path
    wt_root = Path(wt["path"])
    if not wt_root.is_absolute():
        wt_root = workspace_root / wt_root
    try:
        location = resolve_plan_location(plan_path, workspace_root)
    except Exception:
        return plan_path
    candidate = wt_root / location.repo_relative_path
    return candidate if candidate.is_file() else plan_path


def resolve_child_states(
    umbrella_plan: str | Path, workspace_root: str | Path
) -> list[ChildPlanState]:
    """Resolve umbrella child facts without mutating child Plans or Issues."""
    workspace = Path(workspace_root).resolve()
    states: list[ChildPlanState] = []
    for entry in get_child_plan_entries(str(umbrella_plan)):
        name = entry["name"]
        path, archived = _find_declared_child(
            name, entry["project"], workspace
        )

        if path is None:
            states.append(
                ChildPlanState(
                    name=name,
                    declared_project=entry["project"],
                    responsibility=entry["responsibility"],
                    path=None,
                    project=entry["project"],
                    issue=None,
                    status="missing",
                    missing=True,
                )
            )
            continue

        readable = path if archived else _active_child_path(path, workspace)
        states.append(
            ChildPlanState(
                name=name,
                declared_project=entry["project"],
                responsibility=entry["responsibility"],
                path=path,
                project=get_plan_project(str(readable)) or entry["project"],
                issue=get_plan_issue(str(readable)),
                status="archived" if archived else get_plan_status(str(readable)),
                missing=False,
            )
        )
    return states


_ALLOWED_BY_GATE = {
    "complete": {"verifying", "done", "archived"},
    "verify": {"done", "archived"},
    "archive": {"archived"},
}


def child_gate_failures(
    umbrella_plan: str | Path,
    workspace_root: str | Path,
    gate: str,
) -> list[str]:
    """Return child names/states that block an umbrella lifecycle gate."""
    try:
        allowed = _ALLOWED_BY_GATE[gate]
    except KeyError as exc:
        raise ValueError(f"Unsupported umbrella gate: {gate}") from exc

    return [
        f"{child.name} ({'missing' if child.missing else child.status})"
        for child in resolve_child_states(umbrella_plan, workspace_root)
        if child.missing or child.status not in allowed
    ]
