#!/usr/bin/env python3
# test_issue_body_file.py - Test --body-file parameter for issue create
#
# Test Case: Issue body file parameter
#
# Scenarios:
#   1. body-file reads file content successfully
#   2. body-file not found raises error
#   3. body-file provides content, --body ignored when body_file is set

import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from dev_flow.commands.issue import cmd_issue_create


class TestIssueBodyFile(unittest.TestCase):
    """Test --body-file parameter for issue create"""

    def test_body_file_reads_content_successfully(self):
        """body-file: reads file content and passes to gh issue create"""
        # Create a temp file with multi-paragraph content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Issue\n\n")
            f.write("## Background\n\nThis is a multi-paragraph body.\n\n")
            f.write("## Goal\n\n- Item 1\n- Item 2\n")
            temp_file = f.name
        
        try:
            # Mock gh CLI call
            with patch('dev_flow.commands.issue.subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "https://github.com/test/repo/issues/42\n"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                # Mock workspace detection
                with patch('dev_flow.commands.issue.find_workspace_root', return_value='/test/workspace'):
                    with patch('dev_flow.commands.issue.detect_space_repo', return_value='test/repo'):
                        with patch('dev_flow.commands.issue.resolve_project_info', return_value=('standard', None)):
                            # Create args with body-file
                            args = MagicMock()
                            args.title = "feat(cli): test body-file"
                            args.project = "test-project"
                            args.type = "feat"
                            args.body_file = temp_file
                            args.body = None
                            
                            result = cmd_issue_create(args)
                            
                            # Should succeed
                            self.assertEqual(result, 0)
                            
                            # Verify gh call received file content
                            mock_run.assert_called()
                            call_args = mock_run.call_args[0][0]
                            self.assertIn('--body', call_args)
                            # Find body content in args
                            body_idx = call_args.index('--body')
                            body_content = call_args[body_idx + 1]
                            self.assertIn("# Test Issue", body_content)
                            self.assertIn("multi-paragraph", body_content)
        finally:
            os.unlink(temp_file)

    def test_body_file_not_found_raises_error(self):
        """body-file: nonexistent file raises error"""
        nonexistent_file = "/tmp/nonexistent-issue-body-12345.md"
        
        # Ensure file does not exist
        if os.path.exists(nonexistent_file):
            os.unlink(nonexistent_file)
        
        # Create args with nonexistent body-file
        args = MagicMock()
        args.title = "feat(cli): test body-file"
        args.project = "test-project"
        args.type = "feat"
        args.body_file = nonexistent_file
        args.body = None
        
        # Mock workspace detection
        with patch('dev_flow.commands.issue.find_workspace_root', return_value='/test/workspace'):
            with patch('dev_flow.commands.issue.log_error') as mock_log_error:
                result = cmd_issue_create(args)
                
                # Should fail
                self.assertEqual(result, 1)
                
                # Verify error message mentions body-file
                error_calls = [str(call) for call in mock_log_error.call_args_list]
                found_error = any('body-file' in call.lower() or 'not found' in call.lower() for call in error_calls)
                self.assertTrue(found_error, f"Error should mention body-file or not found: {error_calls}")

    def test_body_file_takes_priority_over_body_param(self):
        """body-file: when both body-file and --body provided, body-file takes priority"""
        # Create a temp file with specific content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Body from file - this should be used\n")
            temp_file = f.name
        
        try:
            # Mock gh CLI call
            with patch('dev_flow.commands.issue.subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "https://github.com/test/repo/issues/42\n"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                # Mock workspace detection
                with patch('dev_flow.commands.issue.find_workspace_root', return_value='/test/workspace'):
                    with patch('dev_flow.commands.issue.detect_space_repo', return_value='test/repo'):
                        with patch('dev_flow.commands.issue.resolve_project_info', return_value=('standard', None)):
                            # Create args with BOTH body-file and --body
                            args = MagicMock()
                            args.title = "feat(cli): test body-file priority"
                            args.project = "test-project"
                            args.type = "feat"
                            args.body_file = temp_file  # Body file provided
                            args.body = "Body from --body param"  # Also provided
                            
                            result = cmd_issue_create(args)
                            
                            # Should succeed
                            self.assertEqual(result, 0)
                            
                            # Verify gh call received file content (NOT --body param)
                            call_args = mock_run.call_args[0][0]
                            body_idx = call_args.index('--body')
                            body_content = call_args[body_idx + 1]
                            self.assertIn("Body from file", body_content)
                            self.assertNotIn("Body from --body param", body_content)
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
