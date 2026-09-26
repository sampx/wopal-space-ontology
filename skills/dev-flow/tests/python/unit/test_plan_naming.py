#!/usr/bin/env python3
# test_plan_naming.py - Test validate_plan_name function with mandatory scope
#
# Test Case U5: Plan file naming with mandatory scope validation
#
# Scenarios:
#   1. Issue format with scope -> passes (e.g., 110-feature-dev-flow-slug)
#   2. No-issue format with scope -> passes (e.g., feature-dev-flow-slug)
#   3. Old format without scope -> fails (e.g., 110-feature-slug)
#   4. No-issue old format -> fails (e.g., feature-slug)
#   5. Invalid type -> fails
#
# Note: Tests the new mandatory scope naming requirement from #110
# Extended: slug length guard (<= 20 chars) and no-issue --slug override

import unittest
import sys
import os
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from plan import validate_plan_name, make_plan_name, ValidationError
from commands.plan import _cmd_plan_new


class TestValidatePlanName(unittest.TestCase):
    """Test validate_plan_name with mandatory scope"""

    def test_issue_format_with_scope_passes(self):
        """validate_plan_name: Issue format with scope passes"""
        issue_plan = "110-feature-dev-flow-improve-plan-naming"
        validate_plan_name(issue_plan)

    def test_issue_format_with_cli_scope(self):
        """validate_plan_name: Issue format with cli scope"""
        cli_plan = "42-feature-cli-add-skills-remove"
        validate_plan_name(cli_plan)

    def test_no_issue_format_with_scope_passes(self):
        """validate_plan_name: No-issue format with scope passes"""
        no_issue_plan = "fix-dev-flow-handle-expired-tokens"
        validate_plan_name(no_issue_plan)

    def test_no_issue_with_hyphenated_scope(self):
        """validate_plan_name: No-issue with hyphenated scope"""
        hyphen_scope_plan = "refactor-wopal-plugin-optimize-modules"
        validate_plan_name(hyphen_scope_plan)

    def test_old_issue_format_with_multi_segment_slug_matches(self):
        """validate_plan_name: Old Issue format with multi-segment slug still matches (regex limitation)
        
        Note: The regex cannot distinguish old format (no scope) from new format
        when the old slug happens to have 2+ segments. E.g., "110-feature-improve-plan-naming"
        matches as: issue=110, type=feature, scope=improve, slug=plan-naming.
        Scope enforcement happens at plan creation time (via extract_scope from Issue title),
        not at regex validation time. The regex only checks structural format.
        """
        old_issue_plan = "110-feature-improve-plan-naming"
        # This passes because regex sees: issue=110, type=feature, scope=improve, slug=plan-naming
        # Scope enforcement is at creation time, not validation time
        validate_plan_name(old_issue_plan)

    def test_single_segment_after_type_fails(self):
        """validate_plan_name: Single segment after type fails (no scope no slug)"""
        single_segment = "feature-someslug"
        with self.assertRaises(ValidationError) as context:
            validate_plan_name(single_segment)
        error_msg = str(context.exception)
        self.assertTrue(
            "scope" in error_msg.lower() or "invalid" in error_msg.lower(),
            f"Error should fail with only one segment after type: {error_msg}"
        )

    def test_old_no_issue_format_with_multi_segment_slug_matches(self):
        """validate_plan_name: Old no-issue format with multi-segment slug matches
        
        Matches as: type=fix, scope=handle, slug=expired-tokens
        """
        old_no_issue_plan = "fix-handle-expired-tokens"
        # Matches as: type=fix, scope=handle, slug=expired-tokens
        validate_plan_name(old_no_issue_plan)

    def test_invalid_type_fails(self):
        """validate_plan_name: Invalid type fails"""
        invalid_type_plan = "42-invalid-dev-flow-some-slug"
        with self.assertRaises(ValidationError) as context:
            validate_plan_name(invalid_type_plan)
        error_msg = str(context.exception)
        self.assertTrue(
            "type" in error_msg.lower() or "invalid" in error_msg.lower(),
            f"Error should mention invalid type: {error_msg}"
        )

    def test_valid_fix_type_with_scope(self):
        """validate_plan_name: Valid fix type with scope"""
        fix_plan = "15-fix-plugin-handle-error"
        validate_plan_name(fix_plan)

    def test_valid_refactor_type_with_scope(self):
        """validate_plan_name: Valid refactor type with scope"""
        refactor_plan = "refactor-cli-optimize-commands"
        validate_plan_name(refactor_plan)

    def test_valid_docs_type_with_scope(self):
        """validate_plan_name: Valid docs type with scope"""
        docs_plan = "docs-dev-flow-update-readme"
        validate_plan_name(docs_plan)

    def test_valid_chore_type_with_scope(self):
        """validate_plan_name: Valid chore type with scope"""
        chore_plan = "chore-cli-reorganize-scripts"
        validate_plan_name(chore_plan)

    def test_valid_test_type_with_scope(self):
        """validate_plan_name: Valid test type with scope"""
        test_plan = "test-cli-add-unit-tests"
        validate_plan_name(test_plan)

    def test_valid_enhance_type_with_scope(self):
        """validate_plan_name: Valid enhance type with scope"""
        enhance_plan = "21-enhance-plugin-improve-performance"
        validate_plan_name(enhance_plan)


class TestMakePlanName(unittest.TestCase):
    """Test make_plan_name function"""

    def test_make_plan_name_with_issue(self):
        """make_plan_name: creates plan name with issue number"""
        plan_name = make_plan_name(
            issue_number=110,
            plan_type="feature",
            scope="dev-flow",
            slug="improve-plan-naming"
        )
        self.assertEqual(plan_name, "110-feature-dev-flow-improve-plan-naming")

    def test_make_plan_name_without_issue(self):
        """make_plan_name: creates plan name without issue number"""
        plan_name = make_plan_name(
            issue_number=None,
            plan_type="fix",
            scope="dev-flow",
            slug="handle-token-expiry"
        )
        self.assertEqual(plan_name, "fix-dev-flow-handle-token-expiry")

    def test_make_plan_name_with_hyphenated_scope(self):
        """make_plan_name: handles hyphenated scope"""
        plan_name = make_plan_name(
            issue_number=42,
            plan_type="feature",
            scope="wopal-plugin",
            slug="add-new-feature"
        )
        self.assertEqual(plan_name, "42-feature-wopal-plugin-add-new-feature")

    def test_make_plan_name_normalizes_type(self):
        """make_plan_name: normalizes plan type"""
        plan_name = make_plan_name(
            issue_number=15,
            plan_type="feat",  # Should normalize to feature
            scope="cli",
            slug="add-skills-remove"
        )
        self.assertEqual(plan_name, "15-feature-cli-add-skills-remove")

    def test_make_plan_name_enhance_type(self):
        """make_plan_name: handles enhance type"""
        plan_name = make_plan_name(
            issue_number=21,
            plan_type="enhance",
            scope="plugin",
            slug="improve-performance"
        )
        self.assertEqual(plan_name, "21-enhance-plugin-improve-performance")


class TestMakePlanNameSlugLength:
    """make_plan_name: slug segment is capped at 20 chars (plan-guide slug rules)

    Input -> expected outcome:
      len(slug) <= 20 -> name is built with the slug kept verbatim
      len(slug) > 20  -> ValidationError naming the actual length, the 20-char
                         limit, and the input to shorten
                         (--slug in Issue mode, the title in no-issue mode)
    """

    @pytest.mark.parametrize(
        "issue_number,expected_name",
        [
            # Exactly 20 chars is within the limit — both modes
            (110, "110-feature-engine-token-expiry-refresh"),
            (None, "feature-engine-token-expiry-refresh"),
        ],
    )
    def test_slug_at_20_char_limit_is_accepted(self, issue_number, expected_name):
        """20-char slug -> accepted verbatim in both modes"""
        assert make_plan_name(issue_number, "feature", "engine", "token-expiry-refresh") == expected_name

    @pytest.mark.parametrize(
        "issue_number,slug,slug_from_title,hint",
        [
            # 21 chars: first length over the limit — Issue mode (explicit --slug)
            (110, "deliver-plugin-config", False, "--slug"),
            # 21 chars: no-issue mode with an explicit --slug
            (None, "deliver-plugin-config", False, "--slug"),
            # 21 chars: no-issue mode, slug derived from the title
            (None, "deliver-plugin-config", True, "title"),
            # 38 chars: the verbose slug that exposed the missing guard
            (110, "deliver-plugin-config-table-to-plugins", False, "--slug"),
        ],
    )
    def test_slug_over_20_chars_raises_actionable_error(self, issue_number, slug, slug_from_title, hint):
        """over-20 slug -> ValidationError with length, limit and fix hint"""
        with pytest.raises(ValidationError) as exc_info:
            make_plan_name(issue_number, "feature", "engine", slug, slug_from_title=slug_from_title)
        message = str(exc_info.value)
        assert str(len(slug)) in message, f"must name actual length {len(slug)}: {message}"
        assert "20" in message, f"must name the 20-char limit: {message}"
        assert hint in message.lower(), f"must point at the fix ({hint}): {message}"


def _write_plan_template(workspace_root: Path) -> None:
    """Minimal plan template so create_plan_from_template can run for real."""
    template = workspace_root / ".wopal" / "skills" / "dev-flow" / "templates" / "plan.md"
    template.parent.mkdir(parents=True)
    template.write_text("# {plan_name}\n")


def _run_no_issue_new(args, workspace_root: Path) -> int:
    """Run _cmd_plan_new in no-issue mode against a disposable workspace.

    Workspace detection is patched; plan creation runs for real so the
    resulting file name is the artifact under test.
    """
    with patch("commands.plan.find_workspace_root", return_value=workspace_root):
        with patch("commands.plan.detect_space_repo", return_value="test/repo"):
            return _cmd_plan_new(args)


class TestNoIssueModeSlug:
    """_cmd_plan_new (no-issue mode): --slug wins over the title-derived slug

    Input -> expected artifact:
      --slug given    -> plan file name uses that slug, verbatim
      --slug omitted  -> plan file name derives from the title (regression guard)
      --slug too long -> exit 1, error names length/limit/--slug, no file written
    """

    @staticmethod
    def _args(title, slug, plan_type="feature"):
        return Namespace(
            plan_command="new",
            issue=None,
            title=title,
            project="wopal-cli",
            type=plan_type,
            scope=None,
            slug=slug,
        )

    @pytest.mark.parametrize(
        "title,slug,plan_type,expected_name",
        [
            # explicit --slug wins over a long title-derived slug
            (
                "feat(engine): deliver plugin config table to plugins",
                "config-tables", "feature", "feature-engine-config-tables",
            ),
            # explicit --slug is kept verbatim — no type-prefix stripping
            (
                "fix(cli): handle tokens",
                "fix-token-flow", "fix", "fix-cli-fix-token-flow",
            ),
            # no --slug: falls back to the title-derived slug (regression guard)
            (
                "feat(engine): add cache layer",
                None, "feature", "feature-engine-add-cache-layer",
            ),
        ],
    )
    def test_plan_file_name_follows_slug_source(self, tmp_path, title, slug, plan_type, expected_name):
        """slug input -> plan file created under that name"""
        _write_plan_template(tmp_path)
        result = _run_no_issue_new(self._args(title, slug, plan_type), tmp_path)
        assert result == 0
        assert (tmp_path / ".wopal-space" / "plans" / "wopal-cli" / f"{expected_name}.md").is_file()

    def test_explicit_slug_over_20_chars_rejected_before_write(self, tmp_path):
        """38-char explicit --slug -> exit 1, actionable error, no plan file"""
        _write_plan_template(tmp_path)
        args = self._args(
            "feat(engine): add cache layer",
            "deliver-plugin-config-table-to-plugins",
        )
        with patch("commands.plan.log_error") as mock_log_error:
            result = _run_no_issue_new(args, tmp_path)

        assert result == 1
        plans_root = tmp_path / ".wopal-space" / "plans"
        created = list(plans_root.rglob("*.md")) if plans_root.exists() else []
        assert created == []
        message = " ".join(str(call.args[0]) for call in mock_log_error.call_args_list)
        assert "38" in message, f"must name actual length: {message}"
        assert "20" in message, f"must name the 20-char limit: {message}"
        assert "--slug" in message, f"must point at --slug: {message}"


if __name__ == '__main__':
    unittest.main()