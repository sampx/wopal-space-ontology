#!/usr/bin/env python3
# test_plan_metadata_contract.py - Test the Product/Phase metadata contract
#
# Scenarios:
#   1. plan.py always renders the Product/Phase items; empty when unlinked
#   2. _resolve_product_phase: CLI overrides body; half-declared pair rejected
#   3. check_product_phase: missing items rejected; half-declared pair rejected
#   4. plan new parser registers --product/--phase; no-issue wiring passes them

import argparse
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.plan import (
    _cmd_plan_new,
    _resolve_product_phase,
    create_plan_from_template,
    register_plan_parser,
)
from plan import get_plan_field, set_plan_field
from validation import check_product_phase

SKILL_ROOT = Path(__file__).resolve().parents[3]


class TestTemplateRender(unittest.TestCase):
    """create_plan_from_template keeps the Product/Phase metadata items."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ws = Path(self.tmp)
        tmpl_dir = self.ws / ".wopal" / "skills" / "dev-flow" / "templates"
        tmpl_dir.mkdir(parents=True)
        shutil.copy(SKILL_ROOT / "templates" / "plan.md", tmpl_dir / "plan.md")
        self.plan_dir = self.ws / "plans"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _render(self, **overrides):
        kwargs = dict(
            plan_name="test-plan",
            plan_dir=self.plan_dir,
            issue_number=None,
            plan_type="enhance",
            project="wopal-cli",
            workspace_root=self.ws,
        )
        kwargs.update(overrides)
        return create_plan_from_template(**kwargs).read_text()

    def test_unlinked_plan_keeps_empty_product_phase(self):
        """No values -> items present with empty values; other empty
        optional items (Project Type) are still swept."""
        text = self._render()
        self.assertRegex(text, r'(?m)^- \*\*Product\*\*:\s*$')
        self.assertRegex(text, r'(?m)^- \*\*Phase\*\*:\s*$')
        self.assertNotIn("- **Project Type**:", text)

    def test_no_issue_mode_renders_na(self):
        """No-issue mode renders 'N/A' for Issue, not a bare '#'."""
        text = self._render()
        self.assertIn("- **Issue**: N/A", text)
        self.assertNotIn("- **Issue**: #\n", text)

    def test_linked_plan_renders_values(self):
        text = self._render(product="wopal-space", phase="P3")
        self.assertIn("- **Product**: wopal-space", text)
        self.assertIn("- **Phase**: P3", text)

    def test_issue_mode_renders_number(self):
        text = self._render(issue_number=196)
        self.assertIn("- **Issue**: #196", text)


class TestResolveProductPhase(unittest.TestCase):
    """_resolve_product_phase merges CLI flags over Issue body values."""

    def test_both_empty(self):
        self.assertEqual(
            _resolve_product_phase(None, None, None, None), (None, None)
        )

    def test_body_values_pass_through(self):
        self.assertEqual(
            _resolve_product_phase(None, None, "wopal-space", "P3"),
            ("wopal-space", "P3"),
        )

    def test_cli_overrides_body(self):
        self.assertEqual(
            _resolve_product_phase("other-product", "P9", "wopal-space", "P3"),
            ("other-product", "P9"),
        )

    def test_cli_fills_missing_half_from_body(self):
        self.assertEqual(
            _resolve_product_phase("wopal-space", None, None, "P3"),
            ("wopal-space", "P3"),
        )
        self.assertEqual(
            _resolve_product_phase(None, "P3", "wopal-space", None),
            ("wopal-space", "P3"),
        )

    def test_half_declared_pair_rejected(self):
        with self.assertRaises(ValueError):
            _resolve_product_phase(None, None, "wopal-space", None)
        with self.assertRaises(ValueError):
            _resolve_product_phase("wopal-space", None, None, None)


class TestCheckProductPhase(unittest.TestCase):
    """check_product_phase enforces presence and pair atomicity."""

    def test_both_present_empty_passes(self):
        content = "## Metadata\n\n- **Product**:\n- **Phase**:\n"
        self.assertEqual(check_product_phase(content), [])

    def test_both_present_filled_passes(self):
        content = "- **Product**: wopal-space\n- **Phase**: P3\n"
        self.assertEqual(check_product_phase(content), [])

    def test_missing_items_reported(self):
        issues = check_product_phase("- **Type**: feature\n")
        self.assertEqual(len(issues), 2)

    def test_half_declared_pair_reported(self):
        issues = check_product_phase("- **Product**: wopal-space\n- **Phase**:\n")
        self.assertEqual(len(issues), 1)
        self.assertIn("together", issues[0])
        issues = check_product_phase("- **Product**:\n- **Phase**: P3\n")
        self.assertEqual(len(issues), 1)


class TestPlanNewParserFlags(unittest.TestCase):
    """plan new registers --product/--phase."""

    def test_flags_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_plan_parser(sub)
        args = parser.parse_args([
            "plan", "new", "--title", "enhance(cli): add thing",
            "--project", "wopal-cli", "--type", "enhance",
            "--product", "wopal-space", "--phase", "P3",
        ])
        self.assertEqual(args.product, "wopal-space")
        self.assertEqual(args.phase, "P3")


class TestCmdPlanNewMetadataWiring(unittest.TestCase):
    """_cmd_plan_new resolves and forwards Product/Phase."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        wopal_git = Path(self.tmp) / ".wopal" / ".git"
        wopal_git.parent.mkdir(parents=True)
        wopal_git.write_text("gitdir: /some/path")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _make_args(self, **overrides):
        base = {
            "plan_command": "new",
            "issue": None,
            "title": "enhance(cli): add thing",
            "project": "wopal-cli",
            "type": "enhance",
            "scope": None,
            "slug": None,
            "product": None,
            "phase": None,
        }
        base.update(overrides)
        return Namespace(**base)

    def test_no_issue_mode_forwards_linked_pair(self):
        ws = Path(self.tmp)
        args = self._make_args(product="wopal-space", phase="P3")
        with patch('commands.plan.find_workspace_root', return_value=ws):
            with patch('commands.plan.detect_space_repo', return_value='test/repo'):
                with patch('commands.plan._resolve_plan_dir', return_value=Path(self.tmp) / "plans"):
                    with patch('commands.plan.create_plan_from_template') as mock_create:
                        mock_create.return_value = Path(self.tmp) / "plans" / "x.md"
                        result = _cmd_plan_new(args)
        self.assertEqual(result, 0)
        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs["product"], "wopal-space")
        self.assertEqual(kwargs["phase"], "P3")

    def test_no_issue_mode_rejects_half_pair(self):
        ws = Path(self.tmp)
        args = self._make_args(product="wopal-space")
        with patch('commands.plan.find_workspace_root', return_value=ws):
            with patch('commands.plan.detect_space_repo', return_value='test/repo'):
                with patch('commands.plan.log_error') as mock_log_error:
                    result = _cmd_plan_new(args)
        self.assertEqual(result, 1)
        calls = [str(c) for c in mock_log_error.call_args_list]
        self.assertTrue(any("together" in c for c in calls), calls)


class TestFieldParsingEmptyValues(unittest.TestCase):
    """get/set_plan_field must not leak across lines for empty values."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.plan_file = Path(self.tmp) / "plan.md"
        self.plan_file.write_text(
            "# t\n\n## Metadata\n\n"
            "- **Product**:\n- **Phase**:\n"
            "- **Status**: planning\n- **Type**: enhance\n"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_get_empty_field_returns_empty(self):
        self.assertEqual(get_plan_field(str(self.plan_file), "Product"), "")
        self.assertEqual(get_plan_field(str(self.plan_file), "Phase"), "")

    def test_set_empty_field_keeps_next_line(self):
        self.assertTrue(set_plan_field(str(self.plan_file), "Phase", "P3"))
        text = self.plan_file.read_text()
        self.assertIn("- **Phase**: P3", text)
        self.assertIn("- **Status**: planning", text)
        self.assertIn("- **Type**: enhance", text)

    def test_roundtrip_filled_value(self):
        self.assertTrue(set_plan_field(str(self.plan_file), "Product", "wopal-space"))
        self.assertEqual(get_plan_field(str(self.plan_file), "Product"), "wopal-space")


if __name__ == '__main__':
    unittest.main()
