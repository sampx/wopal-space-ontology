#!/usr/bin/env python3
# test_update_deprecated.py - Test cmd_issue_update deprecated warning
#
# Test Case: issue update prints DEPRECATED warning
#
# Scenarios:
#   1. cmd_issue_update prints DEPRECATED to stderr

import unittest
import sys
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from dev_flow.commands.issue import cmd_issue_update


class TestUpdateDeprecated(unittest.TestCase):
    """Test cmd_issue_update deprecated warning"""

    def test_update_prints_deprecated_warning(self):
        """cmd_issue_update prints DEPRECATED warning to stderr"""
        captured_stderr = io.StringIO()

        with patch('sys.stderr', captured_stderr):
            with patch('dev_flow.commands.issue.detect_space_repo', return_value='test/repo'):
                with patch('dev_flow.commands.issue.find_workspace_root', return_value='/test'):
                    with patch('dev_flow.commands.issue.get_issue_info') as mock_get:
                        mock_get.return_value = {
                            "body": "## Goal\n\ntest",
                            "title": "feat(test): test",
                            "labels": [{"name": "type/feature"}, {"name": "project/test"}],
                        }
                        with patch('dev_flow.commands.issue.subprocess.run') as mock_run:
                            mock_run.return_value = MagicMock(returncode=0, stderr="")
                            with patch('dev_flow.commands.issue.sync_type_label_group'):
                                with patch('dev_flow.commands.issue.sync_project_label_group'):

                                    args = MagicMock()
                                    args.issue_number = "42"
                                    args.title = None
                                    args.type = None
                                    args.project = None
                                    args.goal = None
                                    args.background = None
                                    args.confirmed_bugs = None
                                    args.content_model_defects = None
                                    args.cleanup_scope = None
                                    args.key_findings = None
                                    args.baseline = None
                                    args.target = None
                                    args.affected_components = None
                                    args.refactor_strategy = None
                                    args.target_documents = None
                                    args.audience = None
                                    args.test_scope = None
                                    args.test_strategy = None
                                    args.scope = None
                                    args.out_of_scope = None
                                    args.reference = None
                                    args.acceptance_criteria = None

                                    result = cmd_issue_update(args)

                                    stderr_output = captured_stderr.getvalue()
                                    self.assertIn("DEPRECATED", stderr_output)


if __name__ == '__main__':
    unittest.main()
