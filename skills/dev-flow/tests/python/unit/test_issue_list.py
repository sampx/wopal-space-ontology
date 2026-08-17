#!/usr/bin/env python3
# test_issue_list.py - Test issue list command and its search query builder
#
# Test Case: issue list command with project/status filtering
#
# Scenarios:
#   1. lists open issues from space repo with repo URL
#   2. empty result prints "No open issues"
#   3. fails cleanly when repo detection fails
#   4. fails cleanly when gh returns failure
#   5. build_issue_search_query maps project/status to label query

import unittest
import sys
import json
import argparse
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_list
from lib.github import build_issue_search_query

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "github"


def load_fixture(name):
    with open(FIXTURES / name, "r") as f:
        return json.load(f)


class TestIssueList(unittest.TestCase):
    """Test issue list command output and error handling"""

    def test_lists_open_issues_with_repo_url(self):
        """issue list: prints open issues and space repo URL"""
        with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('commands.issue.detect_space_repo', return_value='sampx/wopal-space'):
                with patch('commands.issue.list_issues',
                           return_value=load_fixture('issue-list-open.json')):
                    with patch('builtins.print') as mock_print:
                        args = argparse.Namespace(project=None, status=None, limit=50)
                        result = cmd_issue_list(args)

                        self.assertEqual(result, 0)
                        printed = [str(c) for c in mock_print.call_args_list]
                        joined = " ".join(printed)
                        self.assertIn('#209', joined)
                        self.assertIn('wopal_task_output section content missing', joined)
                        self.assertIn('https://github.com/sampx/wopal-space', joined)

    def test_empty_result_prints_no_open_issues(self):
        """issue list: prints message when no open issues"""
        with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('commands.issue.detect_space_repo', return_value='sampx/wopal-space'):
                with patch('commands.issue.list_issues', return_value=[]):
                    with patch('builtins.print') as mock_print:
                        args = argparse.Namespace(project=None, status=None, limit=50)
                        result = cmd_issue_list(args)

                        self.assertEqual(result, 0)
                        printed = [str(c) for c in mock_print.call_args_list]
                        joined = " ".join(printed)
                        self.assertIn('No open issues', joined)

    def test_fails_cleanly_when_repo_detection_fails(self):
        """issue list: returns 1 with error when repo cannot be detected"""
        with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('commands.issue.detect_space_repo', side_effect=RuntimeError("no origin")):
                with patch('commands.issue.log_error') as mock_log_error:
                    args = argparse.Namespace(project=None, status=None, limit=50)
                    result = cmd_issue_list(args)

                    self.assertEqual(result, 1)
                    error_calls = [str(c) for c in mock_log_error.call_args_list]
                    self.assertTrue(any('repo' in c.lower() for c in error_calls),
                                    f"Error should mention repo: {error_calls}")

    def test_fails_cleanly_when_gh_fails(self):
        """issue list: returns 1 when gh call fails (None from wrapper)"""
        with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('commands.issue.detect_space_repo', return_value='sampx/wopal-space'):
                with patch('commands.issue.list_issues', return_value=None):
                    with patch('commands.issue.log_error') as mock_log_error:
                        args = argparse.Namespace(project=None, status=None, limit=50)
                        result = cmd_issue_list(args)

                        self.assertEqual(result, 1)
                        error_calls = [str(c) for c in mock_log_error.call_args_list]
                        self.assertTrue(any('issue' in c.lower() for c in error_calls),
                                        f"Error should mention issue: {error_calls}")


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

    def test_executing_alias_maps_to_in_progress(self):
        """build_issue_search_query: 'executing' and 'in-progress' map to status/in-progress"""
        q = build_issue_search_query([], ["executing"])
        self.assertEqual(q, "label:status/in-progress")

    def test_projects_and_statuses_and_combined(self):
        """build_issue_search_query: project + status -> AND of OR clauses"""
        q = build_issue_search_query(["firecrawl"], ["planning"])
        self.assertEqual(q, "label:project/firecrawl label:status/planning")


if __name__ == '__main__':
    unittest.main()
