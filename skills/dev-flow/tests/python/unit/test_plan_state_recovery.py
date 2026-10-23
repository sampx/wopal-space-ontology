#!/usr/bin/env python3
# test_plan_state_recovery.py - Layered Plan recovery results (W-01)
#
# A failed Plan commit recovery has two independent layers: restore the Plan
# file, then reset the staged index entry. The second can fail on its own
# (e.g. a held index lock), and callers must report that residue instead of
# claiming the Plan is ready to retry.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from support.git_fixtures import init_repo, shell_git

from lib.plan_state import (
    PlanFieldSnapshot,
    reset_plan_index,
    recover_plan_after_failed_commit,
)

PLAN_REL = ".wopal-space/plans/p/42-test.md"


def _make_plan_repo(tmp_path):
    ws = tmp_path / "ws"
    init_repo(ws)
    plan = ws / PLAN_REL
    plan.parent.mkdir(parents=True)
    plan.write_text("# plan\n\n## Metadata\n\n- **Status**: executing\n")
    shell_git("add", PLAN_REL, cwd=ws)
    shell_git("commit", "-m", "add plan", cwd=ws)
    return ws, plan


def test_reset_failure_reports_diagnostics(tmp_path):
    """A failed `git reset` returns ok=False with the full diagnostics and
    the manual escape hatch."""
    ws, plan = _make_plan_repo(tmp_path)
    plan.write_text(plan.read_text() + "\n- **PR**: x\n")
    shell_git("add", PLAN_REL, cwd=ws)

    # Real injection: a held index lock makes `git reset` fail.
    lock = ws / ".git" / "index.lock"
    lock.write_text("")
    try:
        result = reset_plan_index(str(plan), ws)
    finally:
        lock.unlink()

    assert result.ok is False
    assert "git reset" in result.message
    assert "index.lock" in result.message
    assert f"git -C {ws}" in result.message


def test_reset_success_reports_ok(tmp_path):
    ws, plan = _make_plan_repo(tmp_path)
    plan.write_text(plan.read_text() + "\n- **PR**: x\n")
    shell_git("add", PLAN_REL, cwd=ws)

    result = reset_plan_index(str(plan), ws)

    assert result.ok is True
    assert shell_git("diff", "--cached", "--name-only", cwd=ws).stdout == ""


def test_recover_reports_file_and_index_layers_separately(tmp_path):
    """File restore succeeds while index reset fails: the layered result
    must show exactly that."""
    ws, plan = _make_plan_repo(tmp_path)
    snapshot = PlanFieldSnapshot.capture(str(plan))
    plan.write_text("# half-written\n")
    shell_git("add", PLAN_REL, cwd=ws)

    lock = ws / ".git" / "index.lock"
    lock.write_text("")
    try:
        recovery = recover_plan_after_failed_commit(str(plan), snapshot, ws)
    finally:
        lock.unlink()

    assert recovery.file_restored is True
    assert recovery.index_reset_ok is False
    assert recovery.index_failure
    assert plan.read_text() == snapshot.content
