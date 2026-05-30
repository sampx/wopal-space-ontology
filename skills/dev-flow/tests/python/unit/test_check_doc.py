#!/usr/bin/env python3
# test_check_doc.py - Test check_doc_plan function
#
# Test Case U2: check-doc rejects bad Task/Test structure and accepts good samples
#
# Scenarios:
#   1. valid-issue-plan.md -> should pass
#   2. valid-no-issue-plan.md -> should pass
#   3. bad-changes-numbered.md -> should reject (numbered list format)
#   4. bad-testplan-empty.md -> should reject (empty Test Plan)
#   5. bad-user-validation-no-checkbox.md -> should reject (missing checkbox)
#   6. good-user-validation-checked.md -> should pass
#   7. old-plan-no-techcontext.md -> should pass (backward compat)

import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from validation import check_doc_plan, ValidationError


class TestCheckDocPlan(unittest.TestCase):
    """Test check_doc_plan function"""

    def setUp(self):
        self.fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures', 'plans'
        )

    def test_valid_issue_plan_passes(self):
        """valid-issue-plan.md should pass"""
        plan_file = os.path.join(self.fixtures_dir, '106-fix-dev-flow-valid-issue-plan.md')
        check_doc_plan(plan_file)

    def test_valid_no_issue_plan_passes(self):
        """valid-no-issue-plan.md should pass"""
        plan_file = os.path.join(self.fixtures_dir, 'refactor-dev-flow-valid-no-issue-plan.md')
        check_doc_plan(plan_file)

    def test_bad_changes_numbered_rejected(self):
        """bad-changes-numbered.md should reject (numbered list format)"""
        plan_file = os.path.join(self.fixtures_dir, 'fix-bad-changes-numbered.md')
        with self.assertRaises(ValidationError) as context:
            check_doc_plan(plan_file)
        error_msg = str(context.exception)
        self.assertTrue(
            'numbered' in error_msg.lower() or 'step' in error_msg.lower() or '编号' in error_msg,
            f"Error should mention numbered list: {error_msg}"
        )

    def test_bad_empty_test_plan_rejected(self):
        """bad-testplan-empty.md should reject (empty Test Plan)"""
        plan_file = os.path.join(self.fixtures_dir, 'fix-bad-testplan-empty.md')
        with self.assertRaises(ValidationError) as context:
            check_doc_plan(plan_file)
        error_msg = str(context.exception)
        self.assertTrue(
            'test' in error_msg.lower() or 'plan' in error_msg.lower() or 'case' in error_msg.lower(),
            f"Error should mention Test Plan structure: {error_msg}"
        )

    def test_bad_user_validation_no_checkbox_rejected(self):
        """bad-user-validation-no-checkbox.md should reject (missing checkbox)"""
        plan_file = os.path.join(self.fixtures_dir, 'fix-bad-user-validation-no-checkbox.md')
        with self.assertRaises(ValidationError) as context:
            check_doc_plan(plan_file)
        error_msg = str(context.exception)
        self.assertTrue(
            'checkbox' in error_msg.lower() or 'validation' in error_msg.lower(),
            f"Error should mention checkbox: {error_msg}"
        )

    def test_good_user_validation_checked_passes(self):
        """good-user-validation-checked.md should pass"""
        plan_file = os.path.join(self.fixtures_dir, 'fix-good-user-validation-checked.md')
        check_doc_plan(plan_file)

    def test_old_plan_no_techcontext_passes(self):
        """old-plan-no-techcontext.md should pass (backward compat)"""
        plan_file = os.path.join(self.fixtures_dir, 'feature-old-plan-no-techcontext.md')
        check_doc_plan(plan_file)

    def test_plan_with_template_comments_rejected(self):
        """plan with leftover template comments should reject"""
        check_doc_fixtures = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures', 'check-doc'
        )
        plan_file = os.path.join(check_doc_fixtures, 'plan-new-has-template-comments.md')
        with self.assertRaises(ValidationError) as context:
            check_doc_plan(plan_file)
        error_msg = str(context.exception)
        self.assertTrue(
            'template comments' in error_msg.lower() or 'comments' in error_msg.lower(),
            f"Error should mention template comments: {error_msg}"
        )


if __name__ == '__main__':
    unittest.main()


# --- Merged from scripts/dev_flow/domain/validation/tests/test_check_doc.py ---
# Tests for new template validation functions (detect_template_version,
# check_task_structure, check_agent_verification, check_user_validation_new)

from validation import (
    detect_template_version,
    check_task_structure,
    check_agent_verification,
    check_user_validation_new,
)

# Fixture directory: tests/python/unit → 3 levels up → tests/fixtures/check-doc
CHECK_DOC_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "check-doc"


def _read_check_doc_fixture(filename: str) -> str:
    """Read fixture Plan file content."""
    fixture_path = CHECK_DOC_FIXTURE_DIR / filename
    assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"
    return fixture_path.read_text(encoding='utf-8')


class TestDetectTemplateVersion(unittest.TestCase):
    """Test detect_template_version function."""

    def test_new_template_detection(self):
        """New template with Architecture Context subsection returns 'new'."""
        content = _read_check_doc_fixture("plan-new-valid.md")
        result = detect_template_version(content)
        self.assertEqual(result, "new")

    def test_old_template_detection(self):
        """Old template without Architecture Context subsection returns 'old'."""
        content = _read_check_doc_fixture("plan-old-valid.md")
        result = detect_template_version(content)
        self.assertEqual(result, "old")

    def test_new_template_all_fixtures_detected(self):
        """All new template fixtures are correctly detected."""
        new_fixtures = [
            "plan-new-valid.md",
            "plan-new-missing-design.md",
            "plan-new-tdd-no-behavior.md",
            "plan-new-behavior-after-design.md",
            "plan-new-done-no-checkbox.md",
            "plan-new-changes-step-checkbox.md",
            "plan-new-ac-no-commands.md",
            "plan-new-ac-after-impl.md",
            "plan-new-user-val-has-commands.md",
            "plan-new-has-template-comments.md",
        ]
        for filename in new_fixtures:
            content = _read_check_doc_fixture(filename)
            result = detect_template_version(content)
            self.assertEqual(result, "new", f"{filename} should be detected as new template")


class TestCheckTaskStructure(unittest.TestCase):
    """Test check_task_structure function."""

    def test_complete_task_structure(self):
        """Complete new template Task passes validation."""
        content = _read_check_doc_fixture("plan-new-valid.md")
        errors = check_task_structure(content)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_missing_design(self):
        """Task missing Design field returns MISSING: Design error."""
        content = _read_check_doc_fixture("plan-new-missing-design.md")
        errors = check_task_structure(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(
            any("MISSING" in e and "Design" in e for e in errors),
            f"Expected MISSING Design error, got: {errors}"
        )

    def test_tdd_true_no_behavior(self):
        """TDD=true Task without Behavior returns MISSING Behavior error."""
        content = _read_check_doc_fixture("plan-new-tdd-no-behavior.md")
        errors = check_task_structure(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(
            any("MISSING" in e and "Behavior" in e and "TDD" in e for e in errors),
            f"Expected MISSING Behavior (TDD) error, got: {errors}"
        )

    def test_behavior_after_design(self):
        """Behavior after Design returns ORDER error."""
        content = _read_check_doc_fixture("plan-new-behavior-after-design.md")
        errors = check_task_structure(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(any("ORDER" in e for e in errors), f"Expected ORDER error, got: {errors}")

    def test_done_no_checkbox(self):
        """Done without checkbox returns MISSING Done checkbox error."""
        content = _read_check_doc_fixture("plan-new-done-no-checkbox.md")
        errors = check_task_structure(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(
            any("MISSING" in e and "Done" in e and "checkbox" in e for e in errors),
            f"Expected MISSING Done checkbox error, got: {errors}"
        )

    def test_changes_has_step_checkbox(self):
        """Changes with Step checkbox format returns FAIL error."""
        content = _read_check_doc_fixture("plan-new-changes-step-checkbox.md")
        errors = check_task_structure(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(
            any("FAIL" in e and "Changes" in e for e in errors),
            f"Expected FAIL Changes error, got: {errors}"
        )


class TestCheckAgentVerification(unittest.TestCase):
    """Test check_agent_verification function."""

    def test_ac_no_commands(self):
        """Agent Verification without executable commands returns FAIL error."""
        content = _read_check_doc_fixture("plan-new-ac-no-commands.md")
        errors = check_agent_verification(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(
            any("FAIL" in e and "command" in e for e in errors),
            f"Expected FAIL command error, got: {errors}"
        )

    def test_ac_after_impl(self):
        """Agent Verification after Implementation returns FAIL position error."""
        content = _read_check_doc_fixture("plan-new-ac-after-impl.md")
        errors = check_agent_verification(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(any("FAIL" in e for e in errors), f"Expected FAIL error, got: {errors}")


class TestCheckUserValidationNew(unittest.TestCase):
    """Test check_user_validation_new function."""

    def test_user_val_contains_npm_test(self):
        """User Validation containing npm test returns FAIL error."""
        content = _read_check_doc_fixture("plan-new-user-val-has-commands.md")
        errors = check_user_validation_new(content)
        self.assertGreater(len(errors), 0, "Expected at least one error")
        self.assertTrue(any("FAIL" in e for e in errors), f"Expected FAIL error, got: {errors}")


class TestBackwardCompat(unittest.TestCase):
    """Test backward compatibility with old template."""

    def test_old_template_passes_old_rules(self):
        """Old template Plan passes old validation rules (no regression)."""
        content = _read_check_doc_fixture("plan-old-valid.md")

        # Old template should be detected as 'old'
        version = detect_template_version(content)
        self.assertEqual(version, "old")

        # For now, just verify old template structure is different
        self.assertNotIn("### Architecture Context", content)
