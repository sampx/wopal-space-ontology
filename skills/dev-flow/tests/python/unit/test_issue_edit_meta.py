#!/usr/bin/env python3
# test_issue_edit_meta.py - Test cmd_issue_edit title/type/project updates
#
# Test Case: issue edit command (--title / --type / --project metadata updates)
#
# Scenarios:
#   1. --title updates the issue title
#   2. --type syncs the type label group
#   3. --project syncs the project label group
#   4. project falls back to existing label when --project omitted

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_edit


def _make_args(**overrides):
    """Build an args namespace with defaults for all edit fields."""
    defaults = {
        "issue_number": "42",
        "title": None,
        "type": None,
        "project": None,
        "body_file": None,
        "append": None,
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


class TestIssueEditMeta(unittest.TestCase):
    """Test cmd_issue_edit metadata updates (title/type/project)"""

    def _run_edit(self, args, issue_info=None):
        """Run cmd_issue_edit with standard mocks, return (result, gh_call_args)."""
        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.get_issue_info") as mock_get:
                mock_get.return_value = issue_info or {
                    "body": "## Goal\n\ntest",
                    "title": "feat(test): old title",
                    "labels": [
                        {"name": "type/feature"},
                        {"name": "project/test"},
                    ],
                }
                with patch("commands.issue.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stderr="")
                    with patch("commands.issue.sync_type_label_group"):
                        with patch("commands.issue.sync_project_label_group"):
                            result = cmd_issue_edit(args)
                            return result, mock_run.call_args[0][0]

    def test_title_update_passes_new_title_to_gh(self):
        """--title updates the issue title via gh issue edit"""
        args = _make_args(title="fix(test): new title")
        result, call_args = self._run_edit(args)

        self.assertEqual(result, 0)
        self.assertIn("--title", call_args)
        title_idx = call_args.index("--title")
        self.assertEqual(call_args[title_idx + 1], "fix(test): new title")

    def test_type_syncs_label_group(self):
        """--type syncs the type label group"""
        args = _make_args(type="fix")
        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.get_issue_info") as mock_get:
                mock_get.return_value = {
                    "body": "## Goal\n\ntest",
                    "title": "feat(test): old title",
                    "labels": [{"name": "type/feature"}, {"name": "project/test"}],
                }
                with patch("commands.issue.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stderr="")
                    with patch("commands.issue.sync_type_label_group") as mock_sync_type:
                        with patch("commands.issue.sync_project_label_group"):
                            result = cmd_issue_edit(args)

        self.assertEqual(result, 0)
        mock_sync_type.assert_called_once()
        # (issue_number, type_label, repo)
        type_args = mock_sync_type.call_args[0]
        self.assertEqual(type_args[0], "42")
        self.assertEqual(type_args[1], "type/bug")

    def test_project_syncs_label_group(self):
        """--project syncs the project label group"""
        args = _make_args(project="other-project")
        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.get_issue_info") as mock_get:
                mock_get.return_value = {
                    "body": "## Goal\n\ntest",
                    "title": "feat(test): old title",
                    "labels": [{"name": "type/feature"}, {"name": "project/test"}],
                }
                with patch("commands.issue.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stderr="")
                    with patch("commands.issue.sync_type_label_group"):
                        with patch("commands.issue.sync_project_label_group") as mock_sync_project:
                            result = cmd_issue_edit(args)

        self.assertEqual(result, 0)
        mock_sync_project.assert_called_once()
        project_args = mock_sync_project.call_args[0]
        self.assertEqual(project_args[0], "42")
        self.assertEqual(project_args[1], "project/other-project")

    def test_project_falls_back_to_existing_label(self):
        """project falls back to existing project/ label when --project omitted"""
        args = _make_args()  # no title/type/project changes, body untouched
        with patch("commands.issue.detect_space_repo", return_value="test/repo"):
            with patch("commands.issue.get_issue_info") as mock_get:
                mock_get.return_value = {
                    "body": "## Goal\n\ntest",
                    "title": "feat(test): old title",
                    "labels": [{"name": "type/feature"}, {"name": "project/existing"}],
                }
                with patch("commands.issue.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stderr="")
                    with patch("commands.issue.sync_type_label_group"):
                        with patch("commands.issue.sync_project_label_group") as mock_sync_project:
                            result = cmd_issue_edit(args)

        self.assertEqual(result, 0)
        mock_sync_project.assert_called_once()
        project_args = mock_sync_project.call_args[0]
        self.assertEqual(project_args[1], "project/existing")


if __name__ == "__main__":
    unittest.main()
