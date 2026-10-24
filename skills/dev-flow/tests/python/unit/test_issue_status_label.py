#!/usr/bin/env python3
# test_issue_status_label.py - Issue status label sync must never fail silently

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

import issue


def _completed(returncode=0, stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = ""
    result.stderr = stderr
    return result


class TestSyncStatusLabel(unittest.TestCase):

    def test_missing_label_is_created_then_retried(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            if args[:2] == ["gh", "--version"]:
                return _completed(0)
            if args[:3] == ["gh", "issue", "edit"]:
                # First edit fails because the label does not exist yet.
                failing = sum(1 for c in calls if c[:3] == ["gh", "issue", "edit"]) == 1
                return _completed(1 if failing else 0)
            if args[:3] == ["gh", "label", "create"]:
                return _completed(0)
            raise AssertionError(f"unexpected call: {args}")

        with patch("issue.subprocess.run", side_effect=fake_run), \
             patch("issue.get_issue_labels", return_value=["status/planning"]), \
             patch("issue.log_warn") as warn:
            issue.sync_status_label(7, "executing", "owner/repo")

        self.assertEqual(warn.call_count, 0)
        self.assertTrue(any(c[:3] == ["gh", "label", "create"] for c in calls))
        edits = [c for c in calls if c[:3] == ["gh", "issue", "edit"]]
        self.assertEqual(len(edits), 2)
        self.assertIn("status/in-progress", edits[-1])
        self.assertIn("status/planning", edits[-1])

    def test_persistent_failure_warns_loudly(self):
        def fake_run(args, **kwargs):
            if args[:2] == ["gh", "--version"]:
                return _completed(0)
            return _completed(1, "label not found")

        with patch("issue.subprocess.run", side_effect=fake_run), \
             patch("issue.get_issue_labels", return_value=["status/planning"]), \
             patch("issue.log_warn") as warn:
            issue.sync_status_label(7, "executing", "owner/repo")

        self.assertEqual(warn.call_count, 1)
        self.assertIn("status/in-progress", warn.call_args[0][0])

    def test_noop_when_label_already_set(self):
        with patch("issue.subprocess.run", return_value=_completed(0)) as run, \
             patch("issue.get_issue_labels", return_value=["status/in-progress"]):
            issue.sync_status_label(7, "executing", "owner/repo")
        edits = [c for c in run.call_args_list if c[0][0][:3] == ["gh", "issue", "edit"]]
        self.assertEqual(edits, [])


if __name__ == "__main__":
    unittest.main()
