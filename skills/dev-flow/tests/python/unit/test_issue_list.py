#!/usr/bin/env python3
# test_issue_list.py - Test issue list command for dev-flow
#
# Test Case: issue list command
#
# Scenarios:
#   1. lists open issues from space repo with repo URL
#   2. fails cleanly when repo detection fails

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_list

# Real sample recorded from `gh issue list --repo sampx/wopal-space --state open`
# (2026-08-17, owner=sampx, repo=wopal-space)
GH_ISSUE_LIST_SAMPLE = """\
209|fix(wopal-plugin): wopal_task_output section content missing|status/planning,type/bug,project/wopal-plugin|https://github.com/sampx/wopal-space/issues/209
203|feat(fc-local): generalize skill and publish multi-arch images|status/planning,type/feature,project/firecrawl|https://github.com/sampx/wopal-space/issues/203
"""


class TestIssueList(unittest.TestCase):
    """Test issue list command"""

    def test_lists_open_issues_with_repo_url(self):
        """issue list: prints open issues and space repo URL"""
        with patch('commands.issue.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = GH_ISSUE_LIST_SAMPLE
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
                with patch('commands.issue.detect_space_repo', return_value='sampx/wopal-space'):
                    with patch('builtins.print') as mock_print:
                        result = cmd_issue_list(MagicMock())

                        self.assertEqual(result, 0)

                        # gh command must target the detected space repo
                        call_args = mock_run.call_args[0][0]
                        self.assertIn('--repo', call_args)
                        self.assertEqual(call_args[call_args.index('--repo') + 1], 'sampx/wopal-space')
                        self.assertIn('--state', call_args)
                        self.assertEqual(call_args[call_args.index('--state') + 1], 'open')

                        # Output must include issue lines and repo URL
                        printed = [str(c) for c in mock_print.call_args_list]
                        joined = " ".join(printed)
                        self.assertIn('#209', joined)
                        self.assertIn('wopal_task_output section content missing', joined)
                        self.assertIn('https://github.com/sampx/wopal-space', joined)

    def test_fails_cleanly_when_repo_detection_fails(self):
        """issue list: returns 1 with error when repo cannot be detected"""
        with patch('commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('commands.issue.detect_space_repo', side_effect=RuntimeError("no origin")):
                with patch('commands.issue.log_error') as mock_log_error:
                    result = cmd_issue_list(MagicMock())

                    self.assertEqual(result, 1)
                    error_calls = [str(c) for c in mock_log_error.call_args_list]
                    self.assertTrue(any('repo' in c.lower() for c in error_calls),
                                    f"Error should mention repo: {error_calls}")


if __name__ == '__main__':
    unittest.main()
