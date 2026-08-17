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
#   8. repeatable --project/--status args parse to lists with default limit

import unittest
import sys
import json
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_list, register_issue_parser
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
    return (
        patch('commands.issue.find_workspace_root', return_value='/test/workspace'),
        patch('commands.issue.detect_space_repo', return_value='sampx/wopal-space'),
        patch('commands.issue.list_issues', return_value=list_issues_return),
    )


def make_process_result(returncode, stdout=""):
    """Shared subprocess.run result construction for list_issues tests."""
    mock_result = MagicMock()
    mock_result.returncode = returncode
    mock_result.stdout = stdout
    return mock_result


def assert_error_contains(test_case, mock_log_error, expected):
    """Shared assertion: one log_error call contains the expected substring."""
    error_calls = [str(c) for c in mock_log_error.call_args_list]
    test_case.assertTrue(
        any(expected in c for c in error_calls),
        f"Error should contain '{expected}': {error_calls}",
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
        p_ws, p_repo, p_list = patch_cmd_issue_list(load_fixture('issue-list-empty.json'))
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
                    assert_error_contains(self, mock_log_error, 'Failed to detect space repo')

    def test_fails_cleanly_when_gh_fails(self):
        """issue list: returns 1 when gh call fails (None from wrapper)"""
        p_ws, p_repo, p_list = patch_cmd_issue_list(None)
        with p_ws, p_repo, p_list:
            with patch('commands.issue.log_error') as mock_log_error:
                result = cmd_issue_list(make_args())
                self.assertEqual(result, 1)
                assert_error_contains(self, mock_log_error, 'Failed to list issues')

    def test_invalid_status_returns_error(self):
        """issue list: invalid status value returns 1 with error"""
        p_ws, p_repo, p_list = patch_cmd_issue_list(load_fixture('issue-list-empty.json'))
        with p_ws, p_repo, p_list:
            with patch('commands.issue.log_error') as mock_log_error:
                result = cmd_issue_list(make_args(status=['bogus']))
                self.assertEqual(result, 1)
                assert_error_contains(self, mock_log_error, 'Invalid status')

    def test_invalid_project_returns_error(self):
        """issue list: invalid project name returns 1 with error"""
        p_ws, p_repo, p_list = patch_cmd_issue_list(load_fixture('issue-list-empty.json'))
        with p_ws, p_repo, p_list:
            with patch('commands.issue.log_error') as mock_log_error:
                result = cmd_issue_list(make_args(project=['Bad Project']))
                self.assertEqual(result, 1)
                assert_error_contains(self, mock_log_error, 'Invalid project')


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

    def test_status_alias_mapping(self):
        """build_issue_search_query: status aliases map to their labels (table)"""
        cases = [
            ("planning", "label:status/planning"),
            ("executing", "label:status/in-progress"),
            ("in-progress", "label:status/in-progress"),
            ("verifying", "label:status/verifying"),
            ("done", "label:status/done"),
        ]
        for status, expected in cases:
            with self.subTest(status=status):
                self.assertEqual(build_issue_search_query([], [status]), expected)

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
            mock_run.return_value = make_process_result(0, fixture_text)

            issues = list_issues(repo="sampx/wopal-space")

            self.assertIsNotNone(issues)
            self.assertEqual(len(issues), 3)
            self.assertEqual(issues[0]["number"], 209)
            self.assertEqual(issues[0]["title"], "fix(wopal-plugin): wopal_task_output section content missing")

    def test_returns_none_on_nonzero_exit(self):
        """list_issues: returns None when gh exits non-zero"""
        with patch('lib.github.subprocess.run') as mock_run:
            mock_run.return_value = make_process_result(1)

            issues = list_issues(repo="sampx/wopal-space")
            self.assertIsNone(issues)

    def test_returns_none_on_gh_missing(self):
        """list_issues: returns None when gh binary not found"""
        with patch('lib.github.subprocess.run', side_effect=FileNotFoundError):
            issues = list_issues(repo="sampx/wopal-space")
            self.assertIsNone(issues)


class TestIssueListParser(unittest.TestCase):
    """Test issue list argparse registration behavior"""

    def _build_issue_parser(self):
        import argparse as _argparse
        parser = _argparse.ArgumentParser(prog="flow.py")
        subparsers = parser.add_subparsers(dest="command")
        register_issue_parser(subparsers)
        return parser

    def test_repeatable_project_status_and_default_limit(self):
        """issue list: --project/--status repeatable, default limit=50"""
        parser = self._build_issue_parser()
        args = parser.parse_args([
            "issue", "list",
            "--project", "firecrawl",
            "--project", "wopal-cli",
            "--status", "planning",
            "--status", "verifying",
        ])
        self.assertEqual(args.issue_cmd, "list")
        self.assertEqual(args.project, ["firecrawl", "wopal-cli"])
        self.assertEqual(args.status, ["planning", "verifying"])
        self.assertEqual(args.limit, 50)

    def test_limit_override(self):
        """issue list: --limit overrides default"""
        parser = self._build_issue_parser()
        args = parser.parse_args(["issue", "list", "--limit", "100"])
        self.assertEqual(args.limit, 100)
        self.assertIsNone(args.project)
        self.assertIsNone(args.status)


if __name__ == '__main__':
    unittest.main()
