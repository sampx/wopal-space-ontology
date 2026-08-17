#!/usr/bin/env python3
# test_approve.py - Test approve command (--confirm-only mode)
#
# Test Cases:
#   - No --confirm: error with "Use: flow.sh submit <plan>"
#   - --confirm from planning/reviewing status: proceeds
#   - --confirm from executing/verifying/done status: blocked
#   - No target: error message
#   - Parser registration

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from lib.plan_commit import RESULT_OK


def _make_approve_mocks(status="planning"):
    """Common mock dict for approve --confirm tests.
    
    Returns dict of {attribute: MagicMock(return_value=value)}.
    """
    values = {
        "find_workspace_root": Path("/ws"),
        "find_plan": "/ws/.wopal-space/plans/space-ontology/42-fix-test.md",
        "parse_plan_status": status,
        "check_doc_plan": None,
        "get_plan_issue": 42,
        "get_plan_project": "space-ontology",
        "get_plan_field": "ontology-worktree",
        "resolve_project_path": Path("/ws/.wopal"),
        "detect_space_repo": "wopal-space-ontology",
        "is_repo_dirty": False,
        "write_worktree_context": True,
        "commit_and_push_plan": RESULT_OK,
        "update_plan_status": True,
        "sync_status_label": None,
        "sync_plan_to_issue_body": None,
        "ensure_issue_labels": None,
        "get_ontology_main_repo": Path("/ws/.wopal"),
        "get_current_branch": "space/wopal-workspace",
        "get_branch_head": "abc123def",
        "set_plan_field": True,
    }
    return {k: MagicMock(return_value=v) for k, v in values.items()}


class TestApproveNoConfirm(unittest.TestCase):
    """Test approve without --confirm errors with redirect to submit."""

    @patch("commands.approve.find_workspace_root", return_value=Path("/ws"))
    def test_approve_no_target_returns_error(self, mock_ws):
        from commands.approve import cmd_approve
        args = Namespace(target=None, confirm=False, no_worktree=False)
        result = cmd_approve(args)
        self.assertEqual(result, 1)

    @patch("commands.approve.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.approve.find_workspace_root", return_value=Path("/ws"))
    def test_approve_no_confirm_errors(self, mock_ws, mock_find):
        from commands.approve import cmd_approve
        args = Namespace(target="42", confirm=False, no_worktree=False)
        result = cmd_approve(args)
        self.assertEqual(result, 1)

    @patch("commands.approve.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.approve.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.approve.log_error")
    def test_approve_no_confirm_shows_submit_message(self, mock_log_error, mock_ws, mock_find):
        from commands.approve import cmd_approve
        args = Namespace(target="42", confirm=False, no_worktree=False)
        cmd_approve(args)
        calls = [str(c) for c in mock_log_error.call_args_list]
        self.assertTrue(
            any("flow.sh submit" in c for c in calls),
            f"Expected 'flow.sh submit' in error messages: {calls}"
        )


class TestApproveConfirmFromPlanning(unittest.TestCase):
    """Test approve --confirm from planning status proceeds."""

    def test_approve_confirm_from_planning_proceeds(self):
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="planning")
        with patch.multiple("commands.approve", **mocks):
            args = Namespace(target="42", confirm=True, no_worktree=True)
            result = cmd_approve(args)
            self.assertEqual(result, 0)


class TestApproveConfirmFromReviewing(unittest.TestCase):
    """Test approve --confirm from reviewing status proceeds."""

    def test_approve_confirm_from_reviewing_proceeds(self):
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="reviewing")
        with patch.multiple("commands.approve", **mocks):
            args = Namespace(target="42", confirm=True, no_worktree=True)
            result = cmd_approve(args)
            self.assertEqual(result, 0)


class TestApproveBlockedStatus(unittest.TestCase):
    """Test approve --confirm blocked by wrong status."""

    @patch("commands.approve.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.approve.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.approve.parse_plan_status", return_value="executing")
    def test_approve_confirm_rejects_executing(self, mock_parse, mock_ws, mock_find):
        from commands.approve import cmd_approve
        args = Namespace(target="42", confirm=True, no_worktree=False)
        result = cmd_approve(args)
        self.assertEqual(result, 1)

    @patch("commands.approve.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.approve.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.approve.parse_plan_status", return_value="done")
    def test_approve_confirm_rejects_done(self, mock_parse, mock_ws, mock_find):
        from commands.approve import cmd_approve
        args = Namespace(target="42", confirm=True, no_worktree=False)
        result = cmd_approve(args)
        self.assertEqual(result, 1)

    @patch("commands.approve.find_plan", return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md")
    @patch("commands.approve.find_workspace_root", return_value=Path("/ws"))
    @patch("commands.approve.parse_plan_status", return_value="verifying")
    def test_approve_confirm_rejects_verifying(self, mock_parse, mock_ws, mock_find):
        from commands.approve import cmd_approve
        args = Namespace(target="42", confirm=True, no_worktree=False)
        result = cmd_approve(args)
        self.assertEqual(result, 1)


class TestApproveRecordsBaseCommit(unittest.TestCase):
    """approve --confirm 应记录 Base Commit(集成分支 HEAD)到 Plan metadata。"""

    def test_approve_writes_base_commit(self):
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="reviewing")
        with patch.multiple("commands.approve", **mocks):
            args = Namespace(target="42", confirm=True, no_worktree=True)
            result = cmd_approve(args)
            mocks["set_plan_field"].assert_any_call(
                "/ws/.wopal-space/plans/space-ontology/42-fix-test.md",
                "Base Commit",
                "abc123def",
            )
        self.assertEqual(result, 0)

    def test_base_commit_uses_integration_branch_head(self):
        """Base Commit 应取集成分支 HEAD(standard: main;ontology: 当前空间分支)。"""
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="reviewing")
        # 切到 standard 项目场景,验证用 main 分支
        mocks["get_plan_field"] = MagicMock(return_value="standard")
        with patch.multiple("commands.approve", **mocks):
            args = Namespace(target="42", confirm=True, no_worktree=True)
            result = cmd_approve(args)
            mocks["get_branch_head"].assert_any_call(
                str(mocks["resolve_project_path"].return_value),
                "main",
            )
        self.assertEqual(result, 0)


class TestApproveBranchDerivation(unittest.TestCase):
    """Test branch derivation from Plan name: <project>-<plan-name>."""

    def test_branch_derives_from_plan_name(self):
        """Branch = <project>-<plan-name> for issue plans."""
        from commands.approve import _derive_branch
        self.assertEqual(
            _derive_branch("ellamaka", "42-feature-cli-add-skills-remove-command"),
            "ellamaka-42-feature-cli-add-skills-remove-command",
        )

    def test_branch_derives_for_no_issue_plan(self):
        """Branch = <project>-<plan-name> for no-issue plans."""
        from commands.approve import _derive_branch
        self.assertEqual(
            _derive_branch("wopal-site", "refactor-cli-optimize-commands"),
            "wopal-site-refactor-cli-optimize-commands",
        )

    def test_branch_derives_for_hyphenated_scope(self):
        """Branch handles hyphenated scope (no split ambiguity)."""
        from commands.approve import _derive_branch
        self.assertEqual(
            _derive_branch("wopal-space-ontology", "42-feature-dev-flow-decouple-naming"),
            "wopal-space-ontology-42-feature-dev-flow-decouple-naming",
        )

    def test_branch_derives_for_ontology_worktree(self):
        """Branch = <project>-<plan-name> for ontology-worktree projects."""
        from commands.approve import _derive_branch
        self.assertEqual(
            _derive_branch("wopal-space-ontology", "42-refactor-dev-flow-unify-naming"),
            "wopal-space-ontology-42-refactor-dev-flow-unify-naming",
        )


class TestRegisterApproveParser(unittest.TestCase):
    """Test approve parser registration."""

    def test_approve_parser_has_confirm(self):
        import argparse
        from commands.approve import register_approve_parser
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_approve_parser(subparsers)
        args = parser.parse_args(["approve", "42", "--confirm"])
        self.assertEqual(args.command, "approve")
        self.assertEqual(args.target, "42")
        self.assertTrue(args.confirm)

    def test_approve_parser_no_confirm_by_default(self):
        import argparse
        from commands.approve import register_approve_parser
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_approve_parser(subparsers)
        args = parser.parse_args(["approve", "42"])
        self.assertEqual(args.command, "approve")
        self.assertFalse(args.confirm)

    def test_approve_parser_has_existing_worktree(self):
        import argparse
        from commands.approve import register_approve_parser
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_approve_parser(subparsers)
        args = parser.parse_args(["approve", "42", "--confirm", "--existing-worktree", ".worktrees/my-wt"])
        self.assertEqual(args.command, "approve")
        self.assertEqual(args.target, "42")
        self.assertTrue(args.confirm)
        self.assertEqual(args.existing_worktree, ".worktrees/my-wt")


class TestApproveExistingWorktree(unittest.TestCase):
    """Test approve with --existing-worktree option (evolution mode)."""

    def test_existing_worktree_binds_branch_and_records_worktree_head_as_base_commit(self):
        """--existing-worktree 应绑定已有 worktree 分支，并将 Base Commit 记录为该分支 HEAD。"""
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="reviewing")
        mocks["get_plan_field"] = MagicMock(return_value="standard")
        mocks["get_branch_head"] = MagicMock(return_value="wt_head_sha_999")
        mocks["get_current_branch"] = MagicMock(return_value="feature/existing-branch")
        mocks["_has_unmerged_files"] = MagicMock(return_value=False)

        with patch.multiple("commands.approve", **mocks):
            with patch("commands.approve.Path.exists", return_value=True), \
                 patch("commands.approve.Path.is_dir", return_value=True), \
                 patch("commands.approve.Path.resolve", side_effect=lambda p: p):
                args = Namespace(
                    target="42",
                    confirm=True,
                    no_worktree=False,
                    existing_worktree=".worktrees/ellamaka-feature-existing",
                )
                result = cmd_approve(args)

        self.assertEqual(result, 0)
        mocks["write_worktree_context"].assert_called_once_with(
            "/ws/.wopal-space/plans/space-ontology/42-fix-test.md",
            "feature/existing-branch",
            ".worktrees/ellamaka-feature-existing",
        )
        mocks["set_plan_field"].assert_any_call(
            "/ws/.wopal-space/plans/space-ontology/42-fix-test.md",
            "Base Commit",
            "wt_head_sha_999",
        )

    def test_existing_worktree_rejects_non_directory_file(self):
        """--existing-worktree 传入文件时报错退出。"""
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="reviewing")
        with patch.multiple("commands.approve", **mocks):
            with patch("commands.approve.Path.exists", return_value=True), \
                 patch("commands.approve.Path.is_dir", return_value=False):
                args = Namespace(
                    target="42",
                    confirm=True,
                    no_worktree=False,
                    existing_worktree=".worktrees/some-file.txt",
                )
                result = cmd_approve(args)
        self.assertEqual(result, 1)

    def test_existing_worktree_rejects_integration_branch(self):
        """--existing-worktree 绑定的 worktree 在 main 分支时报错拒绝。"""
        from commands.approve import cmd_approve
        mocks = _make_approve_mocks(status="reviewing")
        mocks["get_current_branch"] = MagicMock(return_value="main")
        with patch.multiple("commands.approve", **mocks):
            with patch("commands.approve.Path.exists", return_value=True), \
                 patch("commands.approve.Path.is_dir", return_value=True):
                args = Namespace(
                    target="42",
                    confirm=True,
                    no_worktree=False,
                    existing_worktree=".worktrees/primary-main",
                )
                result = cmd_approve(args)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
