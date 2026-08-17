#!/usr/bin/env python3
# test_issue_list.py - Test issue list command, its search query builder, and github wrapper
#
# Scenarios:
#   1. issue list prints open issues with repo URL
#   2. empty result prints "No open issues"
#   3. repo detection failure returns 1
#   4. gh failure (None) returns 1
#   5. invalid status / project validation returns 1
#   6. build_issue_search_query maps project/status to label query (pure input->output)
#   7. list_issues wrapper parses JSON fixture / returns None on failure

import unittest
import sys
import json
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_list
from lib.github import build_issue_search_query, list_issues

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "github"


def load_fixture(name):
    with open(FIXTURES / name, "r") as f:
        return json.load(f)


def make_args(project=None, status=None, limit=50):
    """Shared argparse.Namespace construction for cmd_issue_list tests."""
    return argparse.Namespace(project=project, status=status, limit=limit)


def patch_cmd_issue_list(list_issues_return):
    """Shared patch context for cmd_issue_list: workspace, repo, and list_issues."""
    from unittest.mock import patch as _patch
    return (
        _patch('commands.issue.find_workspace_root', return_value='/test/workspace'),
        _patch('commands.issue.detect_space_repo', return_value='sampx/wopal-space'),
        _patch('commands.issue.list_issues', return_value=list_issues_return),
    )


class TestIssueList(unittest.TestCase):
    """Test issue list command output and error handling"""

    def test_lists_open_issues_with_repo_url(self):
        """issue list: prints open issues and space repo URL"""
        p_ws, p_repo, p_list = patch_cmd_issue_list(load_fixture('issue-list-open.json'))
        with p_ws, p_repo, p_list:
            with patch('builtins.print') as mock_print:
                result = cmd_issue_list(make_args())
                self.assertEqual(result, 0)
                printed = [str(c) for c in mock_print.call_args_list]
                joined = " ".join(printed)
                self.assertIn('#209', joined)
                self.assertIn('wopal_task_output section content missing', joined)
                self.assertIn('https://github.com/sampx/wopal-space', joined)

    def test_empty_result_prints_no_open_issues(self):
        """issue list: prints message when no open issues"""
        p_ws, p_repo, p_list = patch_cmd_issue_list([])
        with p_ws, p_repo, p_list:
            with patch('builtins.print') as mock_print:
                result = cmd_issue_list(make_args())
                self.assertEqual(result, 0)
                printed = [str(c) for c in mock_print.call_args_list]
                joined = " ".join(printed)
                self.assertIn('No open issues', joined)

    def test_fails_cleanly_when_repo_detection_fails(self):
        """issue list: returns 1 with error when repo cannot be detected"""
        with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('commands.issue.detect_space_repo', side_effect=RuntimeError("no origin")):
                with patch('commands.issue.log_error') as mock_log_error:
                    result = cmd_issue_list(make_args())
                    self.assertEqual(result, 1)
                    error_calls = [str(c) for c in mock_log_error.call_args_list]
                    self.assertTrue(any('repo' in c.lower() for c in error_calls),
                                    f"Error should mention repo: {error_calls}")

    def test_fails_cleanly_when_gh_fails(self):
        """issue list: returns 1 when gh call fails (None from wrapper)"""
        p_ws, p_repo, p_list = patch_cmd_issue_list(None)
        with p_ws, p_repo, p_list:
            with patch('commands.issue.log_error') as mock_log_error:
                result = cmd_issue_list(make_args())
                self.assertEqual(result, 1)
                error_calls = [str(c) for c in mock_log_error.call_args_list]
                self.assertTrue(any('issue' in c.lower() for c in error_calls),
                                f"Error should mention issue: {error_calls}")

    def test_invalid_status_returns_error(self):
        """issue list: invalid status value returns 1 with error"""
        p_ws, p_repo, p_list = patch_cmd_issue_list([])
        with p_ws, p_repo, p_list:
            with patch('commands.issue.log_error') as mock_log_error:
                result = cmd_issue_list(make_args(status=['bogus']))
                self.assertEqual(result, 1)
                error_calls = [str(c) for c in mock_log_error.call_args_list]
                self.assertTrue(any('Invalid status' in c for c in error_calls),
                                f"Error should mention invalid status: {error_calls}")

    def test_invalid_project_returns_error(self):
        """issue list: invalid project name returns 1 with error"""
        p_ws, p_repo, p_list = patch_cmd_issue_list([])
        with p_ws, p_repo, p_list:
            with patch('commands.issue.log_error') as mock_log_error:
                result = cmd_issue_list(make_args(project=['Bad Project']))
                self.assertEqual(result, 1)
                error_calls = [str(c) for c in mock_log_error.call_args_list]
                self.assertTrue(any('Invalid project' in c for c in error_calls),
                                f"Error should mention invalid project: {error_calls}")


class TestBuildIssueSearchQuery(unittest.TestCase):
    """Test search query builder input -> output mapping"""

    def test_no_filters_returns_empty(self):
        """build_issue_search_query: no filters -> empty string"""
        self.assertEqual(build_issue_search_query([], []), "")

    def test_single_project(self):
        """build_issue_search_query: single project -> single label term"""
        self.assertEqual(build_issue_search_query(["firecrawl"], []), "label:project/firecrawl")

    def test_multiple_projects_or_combined(self):
        """build_issue_search_query: multiple projects -> OR clause"""
        q = build_issue_search_query(["firecrawl", "wopal-cli"], [])
        self.assertEqual(q, "(label:project/firecrawl OR label:project/wopal-cli)")

    def test_single_status_maps_to_label(self):
        """build_issue_search_query: single status -> mapped status label"""
        self.assertEqual(build_issue_search_query([], ["planning"]), "label:status/planning")

    def test_executing_and_in_progress_alias(self):
        """build_issue_search_query: 'executing' and 'in-progress' both map to status/in-progress"""
        q1 = build_issue_search_query([], ["executing"])
        q2 = build_issue_search_query([], ["in-progress"])
        self.assertEqual(q1, "label:status/in-progress")
        self.assertEqual(q2, "label:status/in-progress")

    def test_invalid_status_raises(self):
        """build_issue_search_query: unknown status raises ValueError"""
        with self.assertRaises(ValueError):
            build_issue_search_query([], ["bogus"])

    def test_projects_and_statuses_and_combined(self):
        """build_issue_search_query: project + status -> AND of OR clauses"""
        q = build_issue_search_query(["firecrawl"], ["planning"])
        self.assertEqual(q, "label:project/firecrawl label:status/planning")

    def test_multiple_projects_and_statuses(self):
        """build_issue_search_query: multi project + multi status -> OR x OR with AND"""
        q = build_issue_search_query(["firecrawl", "ellamaka"], ["planning", "verifying"])
        self.assertEqual(
            q,
            "(label:project/firecrawl OR label:project/ellamaka) "
            "(label:status/planning OR label:status/verifying)"
        )


class TestListIssues(unittest.TestCase):
    """Test lib.github.list_issues wrapper"""

    def test_parses_json_fixture(self):
        """list_issues: parses gh JSON output into list of dicts"""
        fixture_text = Path(FIXTURES / "issue-list-open.json").read_text()
        with patch('lib.github.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = fixture_text
            mock_run.return_value = mock_result

            issues = list_issues(repo="sampx/wopal-space")

            self.assertIsNotNone(issues)
            self.assertEqual(len(issues), 3)
            self.assertEqual(issues[0]["number"], 209)
            self.assertEqual(issues[0]["title"], "fix(wopal-plugin): wopal_task_output section content missing")

    def test_returns_none_on_nonzero_exit(self):
        """list_issues: returns None when gh exits non-zero"""
        with patch('lib.github.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "error"
            mock_run.return_value = mock_result

            issues = list_issues(repo="sampx/wopal-space")
            self.assertIsNone(issues)

    def test_returns_none_on_gh_missing(self):
        """list_issues: returns None when gh binary not found"""
        with patch('lib.github.subprocess.run', side_effect=FileNotFoundError):
            issues = list_issues(repo="sampx/wopal-space")
            self.assertIsNone(issues)

    def test_returns_none_on_invalid_json(self):
        """list_issues: returns None when gh output is not valid JSON"""
        with patch('lib.github.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "not-json"
            mock_run.return_value = mock_result

            issues = list_issues(repo="sampx/wopal-space")
            self.assertIsNone(issues)


if __name__ == '__main__':
    unittest.main()
