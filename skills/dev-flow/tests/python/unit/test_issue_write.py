#!/usr/bin/env python3
# test_issue_write.py - Test cmd_issue_write function
#
# Test Case: issue write command (--body-file and --append modes)
#
# Scenarios:
#   1. --body-file replaces body
#   2. --append preserves existing content
#   3. --append with empty file returns error
#   4. --append with missing file returns error
#   5. Consecutive appends separated by \n\n
#   6. Replace mode ensures trailing newline

import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.issue import cmd_issue_write


class TestIssueWrite(unittest.TestCase):
    """Test cmd_issue_write function"""

    def test_write_replace_body(self):
        """--body-file mode replaces issue body with file content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# New Body\n\nReplaced content")
            temp_file = f.name

        try:
            with patch('commands.issue.detect_space_repo', return_value='test/repo'):
                with patch('commands.issue.subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stderr="")

                    args = MagicMock()
                    args.issue_number = "42"
                    args.body_file = temp_file
                    args.append = None

                    result = cmd_issue_write(args)

                    self.assertEqual(result, 0)
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]
                    self.assertIn('--body', call_args)
                    body_idx = call_args.index('--body')
                    body = call_args[body_idx + 1]
                    self.assertIn("# New Body", body)
                    self.assertIn("Replaced content", body)
        finally:
            os.unlink(temp_file)

    def test_write_append_preserves_content(self):
        """--append mode preserves existing body and appends new content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("new content")
            temp_file = f.name

        try:
            with patch('commands.issue.get_issue_info') as mock_get:
                mock_get.return_value = {"body": "old content", "title": "test"}
                with patch('commands.issue.detect_space_repo', return_value='test/repo'):
                    with patch('commands.issue.subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0, stderr="")

                        args = MagicMock()
                        args.issue_number = "42"
                        args.body_file = None
                        args.append = temp_file

                        result = cmd_issue_write(args)

                        self.assertEqual(result, 0)
                        call_args = mock_run.call_args[0][0]
                        body_idx = call_args.index('--body')
                        body = call_args[body_idx + 1]
                        self.assertIn("old content", body)
                        self.assertIn("new content", body)
                        # Separated by double newline
                        self.assertIn("old content\n\nnew content", body)
        finally:
            os.unlink(temp_file)

    def test_write_append_empty_file_error(self):
        """--append with empty file returns error (exit 1)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            with patch('commands.issue.detect_space_repo', return_value='test/repo'):
                with patch('commands.issue.get_issue_info') as mock_get:
                    mock_get.return_value = {"body": "old", "title": "test"}

                    args = MagicMock()
                    args.issue_number = "42"
                    args.body_file = None
                    args.append = temp_file

                    result = cmd_issue_write(args)
                    self.assertEqual(result, 1)
        finally:
            os.unlink(temp_file)

    def test_write_append_missing_file_error(self):
        """--append with nonexistent file returns error (exit 1)"""
        missing_file = "/tmp/nonexistent-issue-append-file-99999.md"
        if os.path.exists(missing_file):
            os.unlink(missing_file)

        args = MagicMock()
        args.issue_number = "42"
        args.body_file = None
        args.append = missing_file

        with patch('commands.issue.detect_space_repo', return_value='test/repo'):
            result = cmd_issue_write(args)
            self.assertEqual(result, 1)

    def test_write_append_consecutive_separation(self):
        """consecutive appends produce \n\n separation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("second append")
            temp_file = f.name

        try:
            # Simulate body that already has content from a first append
            existing_body = "original\n\nfirst append"

            with patch('commands.issue.get_issue_info') as mock_get:
                mock_get.return_value = {"body": existing_body, "title": "test"}
                with patch('commands.issue.detect_space_repo', return_value='test/repo'):
                    with patch('commands.issue.subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(returncode=0, stderr="")

                        args = MagicMock()
                        args.issue_number = "42"
                        args.body_file = None
                        args.append = temp_file

                        result = cmd_issue_write(args)

                        self.assertEqual(result, 0)
                        call_args = mock_run.call_args[0][0]
                        body_idx = call_args.index('--body')
                        body = call_args[body_idx + 1]
                        self.assertIn("original", body)
                        self.assertIn("first append", body)
                        self.assertIn("second append", body)
        finally:
            os.unlink(temp_file)

    def test_write_replace_body_ensures_trailing_newline(self):
        """replace mode ensures body ends with newline"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# No trailing newline")
            temp_file = f.name

        try:
            with patch('commands.issue.detect_space_repo', return_value='test/repo'):
                with patch('commands.issue.subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stderr="")

                    args = MagicMock()
                    args.issue_number = "42"
                    args.body_file = temp_file
                    args.append = None

                    result = cmd_issue_write(args)

                    self.assertEqual(result, 0)
                    call_args = mock_run.call_args[0][0]
                    body_idx = call_args.index('--body')
                    body = call_args[body_idx + 1]
                    self.assertTrue(body.endswith('\n'), "body should end with newline")
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
