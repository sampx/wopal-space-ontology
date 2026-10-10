#!/usr/bin/env python3
# test_submit.py - Test submit command
#
# Test Cases:
#   - Happy path: planning → reviewing with commit/push
#   - Wrong status guard: non-planning status rejected
#   - Validation failure: check_doc blocks submit
#   - No target: error message
#   - Output message: "Next: flow.sh approve <plan> --confirm"

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from support.git_fixtures import (
    init_repo as _shell_init_repo,
    install_failing_hook as _shell_install_failing_hook,
    shell_git as _shell_git,
)

from commands.submit import cmd_submit, register_submit_parser
from lib.plan_commit import RESULT_OK


class TestSubmitHappyPath(unittest.TestCase):
    """Test submit happy path: planning → reviewing."""

    @patch("commands.submit.commit_and_push_plan", return_value=RESULT_OK)
    @patch("commands.submit.update_plan_status", return_value=True)
    @patch("commands.submit.check_doc_plan")
    @patch("commands.submit.get_plan_issue", return_value=42)
    @patch("commands.submit.get_plan_status", return_value="planning")
    @patch("commands.submit.parse_plan_status", return_value="planning")
    @patch("commands.submit.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    def test_submit_transitions_planning_to_reviewing(
        self, mock_ws, mock_find, mock_parse, mock_get_status,
        mock_get_issue, mock_check_doc, mock_update, mock_commit
    ):
        args = Namespace(target="42")
        result = cmd_submit(args)
        self.assertEqual(result, 0)
        mock_update.assert_called_once_with("/ws/.wopal-space/plans/space-ontology/42-fix-test.md", "reviewing")

    @patch("commands.submit.commit_and_push_plan", return_value=RESULT_OK)
    @patch("commands.submit.update_plan_status", return_value=True)
    @patch("commands.submit.check_doc_plan")
    @patch("commands.submit.get_plan_issue", return_value=42)
    @patch("commands.submit.get_plan_status", return_value="planning")
    @patch("commands.submit.parse_plan_status", return_value="planning")
    @patch("commands.submit.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    def test_submit_outputs_next_approve_confirm(
        self, mock_ws, mock_find, mock_parse, mock_get_status,
        mock_get_issue, mock_check_doc, mock_update, mock_commit
    ):
        import io
        import sys as _sys
        old_stdout = _sys.stdout
        _sys.stdout = io.StringIO()
        try:
            args = Namespace(target="42")
            result = cmd_submit(args)
            output = _sys.stdout.getvalue()
            self.assertIn("Next: flow.sh approve 42 --confirm", output)
            self.assertIn("Status: reviewing", output)
        finally:
            _sys.stdout = old_stdout


class TestSubmitWrongStatus(unittest.TestCase):
    """Test submit rejects non-planning status."""

    @patch("commands.submit.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.submit.parse_plan_status", return_value="executing")
    def test_submit_rejects_executing(self, mock_parse, mock_ws, mock_find):
        args = Namespace(target="42")
        result = cmd_submit(args)
        self.assertEqual(result, 1)

    @patch("commands.submit.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.submit.parse_plan_status", return_value="reviewing")
    def test_submit_rejects_reviewing(self, mock_parse, mock_ws, mock_find):
        args = Namespace(target="42")
        result = cmd_submit(args)
        self.assertEqual(result, 1)

    @patch("commands.submit.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.submit.parse_plan_status", return_value="done")
    def test_submit_rejects_done(self, mock_parse, mock_ws, mock_find):
        args = Namespace(target="42")
        result = cmd_submit(args)
        self.assertEqual(result, 1)


class TestSubmitValidationFailure(unittest.TestCase):
    """Test submit blocked by check_doc validation failure."""

    @patch("commands.submit.check_doc_plan", side_effect=Exception("Validation failed"))
    @patch("commands.submit.get_plan_issue", return_value=42)
    @patch("commands.submit.get_plan_status", return_value="planning")
    @patch("commands.submit.parse_plan_status", return_value="planning")
    @patch("commands.submit.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    def test_submit_blocks_on_validation_error(
        self, mock_ws, mock_find, mock_parse, mock_get_status,
        mock_get_issue, mock_check_doc
    ):
        # Patch ValidationError at the module level
        from validation import ValidationError
        mock_check_doc.side_effect = ValidationError("missing field")
        args = Namespace(target="42")
        result = cmd_submit(args)
        self.assertEqual(result, 1)


class TestSubmitNoTarget(unittest.TestCase):
    """Test submit with no target."""

    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    def test_submit_no_target_returns_error(self, mock_ws):
        args = Namespace(target=None)
        result = cmd_submit(args)
        self.assertEqual(result, 1)


class TestSubmitPlanNotFound(unittest.TestCase):
    """Test submit with plan not found."""

    @patch("commands.submit.find_plan", side_effect=FileNotFoundError("not found"))
    @patch("commands.submit.find_workspace_root", return_value=Path("/ws"))
    def test_submit_plan_not_found(self, mock_ws, mock_find):
        args = Namespace(target="999")
        result = cmd_submit(args)
        self.assertEqual(result, 1)


class TestRegisterSubmitParser(unittest.TestCase):
    """Test submit parser registration."""

    def test_submit_parser_registered(self):
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_submit_parser(subparsers)
        # Parse submit command
        args = parser.parse_args(["submit", "42"])
        self.assertEqual(args.command, "submit")
        self.assertEqual(args.target, "42")


if __name__ == "__main__":
    unittest.main()


# ============================================
# submit commit-failure retryability (Task 4, AC#6)
# ============================================
#
# Real construction: a temp workspace repo (+ bare origin) holding a Plan in
# planning state. check_doc validation is mocked (not the concern here); the
# status write, git commit/push and the retry run for real.


SUBMIT_PLAN_REL = ".wopal-space/plans/ontology/106-fix-dev-flow-valid-issue-plan.md"
FIXTURE_106 = (
    Path(__file__).resolve().parents[2]
    / "fixtures" / "plans" / "106-fix-dev-flow-valid-issue-plan.md"
)


def _make_submit_workspace(tmp_path):
    ws = tmp_path / "ws"
    _shell_init_repo(ws)
    origin = tmp_path / "ws-origin.git"
    _shell_git("init", "--bare", "-b", "main", str(origin), cwd=tmp_path)
    _shell_git("remote", "add", "origin", str(origin), cwd=ws)

    plan = ws / SUBMIT_PLAN_REL
    plan.parent.mkdir(parents=True)
    plan.write_text(FIXTURE_106.read_text())
    _shell_git("add", SUBMIT_PLAN_REL, cwd=ws)
    _shell_git("commit", "-m", "add plan", cwd=ws)
    _shell_git("push", "-u", "origin", "main", cwd=ws)
    _shell_git("remote", "set-head", "origin", "main", cwd=ws)
    return ws, plan


def _run_submit(ws, target="106"):
    from commands.submit import cmd_submit

    with patch.multiple(
        "commands.submit",
        find_workspace_root=MagicMock(return_value=ws),
        check_doc_plan=MagicMock(),
    ):
        return cmd_submit(Namespace(target=target))


class TestSubmitCommitFailureRetryable:
    """A failed submit commit must leave the Plan retryable (planning), not
    half-written in reviewing."""

    def test_commit_failure_restores_plan_to_planning(self, tmp_path):
        ws, plan = _make_submit_workspace(tmp_path)
        original = plan.read_text()
        _shell_install_failing_hook(ws, "injected submit-commit failure")

        result = _run_submit(ws)

        assert result == 1
        assert plan.read_text() == original
        assert "- **Status**: planning" in plan.read_text()
        # No staged Plan residue.
        assert _shell_git(
            "status", "--porcelain", "--", SUBMIT_PLAN_REL, cwd=ws
        ).stdout == ""

    def test_retry_after_commit_failure_succeeds(self, tmp_path):
        ws, plan = _make_submit_workspace(tmp_path)
        hook = _shell_install_failing_hook(ws, "injected submit-commit failure")

        first = _run_submit(ws)
        assert first == 1

        hook.unlink()
        second = _run_submit(ws)

        assert second == 0
        committed = _shell_git("show", f"HEAD:{SUBMIT_PLAN_REL}", cwd=ws).stdout
        assert "- **Status**: reviewing" in committed
        assert _shell_git(
            "log", "-1", "--format=%s", cwd=ws
        ).stdout.strip() == "docs(plan): submit plan #106"
        assert _shell_git(
            "status", "--porcelain", "--", SUBMIT_PLAN_REL, cwd=ws
        ).stdout == ""
