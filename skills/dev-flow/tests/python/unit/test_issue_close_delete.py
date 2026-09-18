#!/usr/bin/env python3
# test_issue_close_delete.py - Test cmd_issue_close and cmd_issue_delete
#
# Test Case: issue close / delete commands
#
# Scenarios:
#   1. close calls gh issue close with --repo
#   2. delete calls gh issue delete with --repo and --yes
#   3. missing issue number returns error

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_close, cmd_issue_delete


class TestIssueClose(unittest.TestCase):
    """Test cmd_issue_close function"""

    def test_close_calls_gh_issue_close(self):
        """close calls gh issue close with --repo"""
        args = MagicMock(issue_number="42")

        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                result = cmd_issue_close(args)

                self.assertEqual(result, 0)
                call_args = mock_run.call_args[0][0]
                self.assertEqual(call_args[0], "gh")
                self.assertIn("issue", call_args)
                self.assertIn("close", call_args)
                self.assertIn("--repo", call_args)
                self.assertIn("test/repo", call_args)
                self.assertIn("42", call_args)

    def test_close_missing_issue_number_errors(self):
        """missing issue number returns error (exit 1)"""
        args = MagicMock(issue_number=None)

        result = cmd_issue_close(args)
        self.assertEqual(result, 1)

    def test_close_failure_returns_error(self):
        """gh failure returns error (exit 1)"""
        args = MagicMock(issue_number="42")

        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="boom")

                result = cmd_issue_close(args)
                self.assertEqual(result, 1)


class TestIssueDelete(unittest.TestCase):
    """Test cmd_issue_delete function"""

    def test_delete_calls_gh_issue_delete_with_yes(self):
        """delete calls gh issue delete with --repo and --yes"""
        args = MagicMock(issue_number="42")

        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                result = cmd_issue_delete(args)

                self.assertEqual(result, 0)
                call_args = mock_run.call_args[0][0]
                self.assertEqual(call_args[0], "gh")
                self.assertIn("issue", call_args)
                self.assertIn("delete", call_args)
                self.assertIn("--yes", call_args)
                self.assertIn("--repo", call_args)
                self.assertIn("test/repo", call_args)
                self.assertIn("42", call_args)

    def test_delete_missing_issue_number_errors(self):
        """missing issue number returns error (exit 1)"""
        args = MagicMock(issue_number=None)

        result = cmd_issue_delete(args)
        self.assertEqual(result, 1)

    def test_delete_failure_returns_error(self):
        """gh failure returns error (exit 1)"""
        args = MagicMock(issue_number="42")

        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="boom")

                result = cmd_issue_delete(args)
                self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
