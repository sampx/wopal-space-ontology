#!/usr/bin/env python3
# test_issue_view.py - Test issue view command (#216 follow-up to #215 session)
#
# Test Cases:
#   1. Happy path: prints number/title/state/labels/body from get_issue_info
#   2. Raw JSON output with --json
#   3. Repo detection failure returns 1
#   4. gh failure (RuntimeError) returns 1
#   5. Dispatch: cmd_issue routes "view" to cmd_issue_view
#   6. Parser registration: positional issue number + --json flag

import argparse
import unittest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from contextlib import ExitStack

from commands.issue import cmd_issue_view, cmd_issue, register_issue_parser


SAMPLE_ISSUE = {
    "number": 215,
    "title": "fix(dev-flow): race on git push in parallel flow.sh runs",
    "state": "OPEN",
    "labels": [{"name": "type/bug"}, {"name": "project/dev-flow"}],
    "body": "## Goal\n\nFix the push race.\n\n## Acceptance Criteria\n\n- [ ] done\n",
}


def make_args(issue=None, json_flag=False):
    return argparse.Namespace(issue=issue, json_flag=json_flag)


def patch_happy(get_info_return=SAMPLE_ISSUE):
    return (
        patch("commands.issue.find_workspace_root", return_value="/test/workspace"),
        patch("commands.issue.detect_space_repo", return_value="sampx/wopal-space"),
        patch("commands.issue.get_issue_info", return_value=get_info_return),
    )


class TestIssueViewHappyPath(unittest.TestCase):
    """issue view prints issue content without listing."""

    def _run_view(self, args):
        import io, contextlib
        buf = io.StringIO()
        with ExitStack() as stack:
            for p in patch_happy():
                stack.enter_context(p)
            with contextlib.redirect_stdout(buf):
                result = cmd_issue_view(args)
        return result, buf.getvalue()

    def test_prints_number_title_state_labels_body(self):
        result, out = self._run_view(make_args(issue="215"))
        self.assertEqual(result, 0)
        self.assertIn("#215", out)
        self.assertIn("race on git push", out)
        self.assertIn("OPEN", out)
        self.assertIn("type/bug", out)
        self.assertIn("project/dev-flow", out)
        self.assertIn("## Goal", out)
        self.assertIn("- [ ] done", out)

    def test_json_output_is_valid_json_with_all_fields(self):
        import json as jsonlib
        result, out = self._run_view(make_args(issue="215", json_flag=True))
        self.assertEqual(result, 0)
        parsed = jsonlib.loads(out)
        self.assertEqual(parsed["number"], 215)
        self.assertEqual(parsed["body"], SAMPLE_ISSUE["body"])

    def test_repo_detection_failure_returns_1(self):
        with patch("commands.issue.find_workspace_root", return_value="/ws"), \
             patch("commands.issue.detect_space_repo",
                   side_effect=RuntimeError("not a space")), \
             patch("commands.issue.log_error") as mock_err:
            result = cmd_issue_view(make_args(issue="215"))
        self.assertEqual(result, 1)
        self.assertTrue(mock_err.called)

    def test_gh_failure_returns_1(self):
        with patch("commands.issue.find_workspace_root", return_value="/ws"), \
             patch("commands.issue.detect_space_repo",
                   return_value="sampx/wopal-space"), \
             patch("commands.issue.get_issue_info",
                   side_effect=RuntimeError("gh failed")), \
             patch("commands.issue.log_error") as mock_err:
            result = cmd_issue_view(make_args(issue="215"))
        self.assertEqual(result, 1)
        self.assertTrue(mock_err.called)


class TestIssueViewDispatchAndParser(unittest.TestCase):
    """cmd_issue routes view; parser accepts issue + --json."""

    def test_dispatch_routes_view(self):
        with patch("commands.issue.cmd_issue_view",
                   return_value=0) as mock_view:
            args = argparse.Namespace(issue_cmd="view", issue="215",
                                      json_flag=False)
            result = cmd_issue(args)
        self.assertEqual(result, 0)
        mock_view.assert_called_once_with(args)

    def test_parser_accepts_issue_number_and_json_flag(self):
        root = argparse.ArgumentParser()
        real_sub = root.add_subparsers(dest="issue_cmd")
        with patch("commands.issue.log_error"), \
             patch("commands.issue.cmd_issue", return_value=0):
            register_issue_parser(real_sub)
        ns = root.parse_args(["issue", "view", "215", "--json"])
        self.assertEqual(ns.issue, "215")
        self.assertTrue(ns.json_flag)

    def test_parser_view_requires_issue_number(self):
        root = argparse.ArgumentParser()
        real_sub = root.add_subparsers(dest="issue_cmd")
        with patch("commands.issue.log_error"), \
             patch("commands.issue.cmd_issue", return_value=0):
            register_issue_parser(real_sub)
        with self.assertRaises(SystemExit):
            root.parse_args(["issue", "view"])
