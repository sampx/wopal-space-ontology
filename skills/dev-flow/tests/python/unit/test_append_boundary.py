#!/usr/bin/env python3
# test_append_boundary.py - Boundary behavior tests for issue write --append
#
# Test Cases:
#   1. Empty file append returns error (exit 1)
#   2. Consecutive append produces \n\n separation

import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from dev_flow.commands.issue import cmd_issue_write


class TestAppendBoundary(unittest.TestCase):
    """Boundary behavior tests for issue write --append"""

    def test_append_empty_file_returns_error(self):
        """Appending from empty file returns exit code 1"""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        f.write("")
        f.close()
        try:
            args = MagicMock()
            args.issue = "42"
            args.body_file = f.name
            args.append = True
            result = cmd_issue_write(args)
            self.assertEqual(result, 1)
        finally:
            os.unlink(f.name)

    def test_append_consecutive_produces_double_newline(self):
        """Two consecutive appends produce \\n\\n separation between bodies"""
        from dev_flow.commands.issue import cmd_issue_write

        body_state = {"body": "Initial content"}

        file_a = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        file_a.write("Part A")
        file_a.close()

        file_b = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        file_b.write("Part B")
        file_b.close()

        try:
            with patch("dev_flow.commands.issue.get_issue_info", return_value=body_state), \
                 patch("dev_flow.commands.issue.detect_space_repo", return_value="org/repo"), \
                 patch("dev_flow.commands.issue.find_workspace_root", return_value="/tmp/ws"), \
                 patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                args_a = MagicMock()
                args_a.issue = "42"
                args_a.body_file = file_a.name
                args_a.append = True
                cmd_issue_write(args_a)

                first_body = mock_run.call_args[0][0][-1]
                body_state["body"] = first_body

                args_b = MagicMock()
                args_b.issue = "42"
                args_b.body_file = file_b.name
                args_b.append = True
                cmd_issue_write(args_b)

                second_body = mock_run.call_args[0][0][-1]
                self.assertIn("Part A", second_body)
                self.assertIn("Part B", second_body)
                idx_a = second_body.index("Part A")
                idx_b = second_body.index("Part B")
                between = second_body[idx_a + len("Part A"):idx_b]
                self.assertIn("\n\n", between)
        finally:
            os.unlink(file_a.name)
            os.unlink(file_b.name)


if __name__ == '__main__':
    unittest.main()
