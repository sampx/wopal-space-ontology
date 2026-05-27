#!/usr/bin/env python3
# test_plan_product_phase.py - Test _extract_product_phase_from_body
#
# Test Case: Plan Product/Phase extraction from Issue body
#
# Scenarios:
#   1. Both Product and Phase present
#   2. Neither field present
#   3. Empty body
#   4. Phase only

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from dev_flow.commands.plan import _extract_product_phase_from_body


class TestExtractProductPhase(unittest.TestCase):
    """Test _extract_product_phase_from_body pure function"""

    def test_extract_product_and_phase(self):
        """body with Product and Phase -> returns both"""
        issue_info = {
            "body": "- **Product**: foo\n- **Phase**: P1\n"
        }
        product, phase = _extract_product_phase_from_body(issue_info)
        self.assertEqual(product, "foo")
        self.assertEqual(phase, "P1")

    def test_extract_missing_fields(self):
        """body without Product or Phase -> returns (None, None)"""
        issue_info = {
            "body": "## Goal\n\nSome goal text\n"
        }
        product, phase = _extract_product_phase_from_body(issue_info)
        self.assertIsNone(product)
        self.assertIsNone(phase)

    def test_extract_empty_body(self):
        """empty body string -> returns (None, None)"""
        issue_info = {"body": ""}
        product, phase = _extract_product_phase_from_body(issue_info)
        self.assertIsNone(product)
        self.assertIsNone(phase)

    def test_extract_phase_only(self):
        """body with only Phase -> returns (None, phase)"""
        issue_info = {
            "body": "- **Phase**: P2\n"
        }
        product, phase = _extract_product_phase_from_body(issue_info)
        self.assertIsNone(product)
        self.assertEqual(phase, "P2")


if __name__ == '__main__':
    unittest.main()
