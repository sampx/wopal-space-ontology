#!/usr/bin/env python3
# plan_state.py - Transactional Plan file snapshot / index recovery
#
# Shared by lifecycle commands that rewrite Plan state fields and then commit
# them (approve, complete): capture the pre-write content, and when the Plan
# commit fails restore the content plus drop any staged Plan residue, so the
# command stays retryable and no half-committed Plan state remains.

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from lib.logging import log_warn
from lib.git import GitMutationFailure
from lib.project import resolve_plan_location


@dataclass
class PlanFieldSnapshot:
    """Pre-transaction Plan content snapshot.

    Captured before a command writes any Plan state field. Restore rewrites
    the captured content, so every field the command changed returns to its
    original value and every other byte of the document stays untouched.
    """

    content: str

    @classmethod
    def capture(cls, plan_path: str) -> "PlanFieldSnapshot | None":
        """Read the Plan's pre-transaction content; None when unreadable."""
        try:
            return cls(content=Path(plan_path).read_text())
        except OSError:
            return None

    def restore(self, plan_path: str) -> bool:
        """Write the pre-transaction content back; False on failure."""
        try:
            Path(plan_path).write_text(self.content)
            return True
        except OSError:
            return False


@dataclass
class IndexResetResult:
    """Outcome of dropping the staged Plan entry after a failed commit.

    ok: True when the index carries no Plan residue.
    message: on failure, the full mutation diagnostics plus the manual
        command; empty on success.
    """

    ok: bool
    message: str = ""


@dataclass
class PlanRecovery:
    """Layered outcome of restoring a Plan after a failed commit.

    file_restored: the Plan file content was written back.
    index_reset_ok: the staged Plan entry was dropped (or no reset was
        requested — nothing is known to be dirty).
    index_failure: failure detail when index_reset_ok is False.
    """

    file_restored: bool
    index_reset_ok: bool
    index_failure: str = ""


def reset_plan_index(plan_path: str, workspace_root: Path) -> IndexResetResult:
    """Drop the staged Plan entry left behind by a failed Plan commit.

    A failed commit can leave the Plan staged (`git add` succeeded, `git
    commit` did not). Reset only this one path in the Plan's owning repo —
    never the whole index. Failures keep the full mutation diagnostics
    (command / cwd / exit / stderr) and name the manual command, so callers
    can report the residual state truthfully instead of claiming retryable.

    Best-effort: never raises.
    """
    try:
        location = resolve_plan_location(Path(plan_path), workspace_root)
        rel = location.repo_relative_path
        cmd = ["git", "reset", "--", rel]
        result = subprocess.run(
            cmd,
            cwd=str(location.repo_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failure = GitMutationFailure.from_completed(
                cmd, str(location.repo_root), result,
            )
            message = (
                f"{failure}\n"
                f"manual: git -C {location.repo_root} reset -- {rel}"
            )
            log_warn(
                "Failed to reset staged Plan entry; index residue may "
                "remain:\n" + message
            )
            return IndexResetResult(ok=False, message=message)
        return IndexResetResult(ok=True)
    except Exception as e:
        message = f"Failed to reset staged Plan entry: {e}"
        log_warn(message)
        return IndexResetResult(ok=False, message=message)


def recover_plan_after_failed_commit(
    plan_path: str,
    snapshot: "PlanFieldSnapshot | None",
    workspace_root: Path,
    reset_index: bool = True,
) -> PlanRecovery:
    """Restore a Plan after a failed commit and report each layer.

    Layer 1 restores the file content from the snapshot; layer 2 drops the
    staged Plan entry. Both outcomes are returned separately so callers never
    conflate "file restored" with "safe to retry".
    """
    file_restored = snapshot is not None and snapshot.restore(plan_path)
    if not file_restored:
        return PlanRecovery(file_restored=False, index_reset_ok=False)
    if not reset_index:
        return PlanRecovery(file_restored=True, index_reset_ok=True)
    result = reset_plan_index(plan_path, workspace_root)
    return PlanRecovery(
        file_restored=True,
        index_reset_ok=result.ok,
        index_failure="" if result.ok else result.message,
    )
