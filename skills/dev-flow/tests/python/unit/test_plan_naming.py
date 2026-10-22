#!/usr/bin/env python3
# test_plan_naming.py - Plan naming contract: <issue>-<type>-<slug> / <type>-<slug>
#
# A Plan name is <issue?>-<type>-<slug> and nothing else: type and slug are
# always explicit, never derived from a title. The name must be ASCII kebab-case
# within the slug length cap because it derives the feature branch and worktree.

import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from plan import validate_plan_name, make_plan_name, ValidationError
from commands.plan import _cmd_plan_new


class TestValidatePlanName:
    """validate_plan_name: structure is <issue?>-<type>-<slug>, ASCII only."""

    @pytest.mark.parametrize(
        "name",
        [
            "fix-pr-102",
            "196-feature-cli-plan-scheduler",
            "docs-readme",
            "refactor-cli-sdk-integration",
        ],
    )
    def test_valid_names_pass(self, name):
        validate_plan_name(name)

    @pytest.mark.parametrize(
        "name",
        [
            # CJK slug — the defect this contract exists to stop
            "fix-dsh-pr-102-评审修复",
            "fix-评审",
            # no type segment
            "110-improve-plan-naming",
            # unknown type
            "42-invalid-some-slug",
            # underscores and uppercase are not kebab-case
            "fix-some_slug",
            "fix-Some-Slug",
        ],
    )
    def test_invalid_names_rejected(self, name):
        with pytest.raises(ValidationError):
            validate_plan_name(name)

    def test_error_names_the_accepted_shape_and_ascii_rule(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_plan_name("fix-dsh-pr-102-评审修复")
        message = str(exc_info.value)
        assert "<type>-<slug>" in message, message
        assert "--slug" in message, message

    def test_scope_like_segment_is_now_part_of_the_slug(self):
        """`fix-dsh-pr-102` is legal — `dsh-pr-102` is just the slug.

        The contract no longer has a scope slot, so a name that used to read as
        `<type>-<scope>-<slug>` simply reads as `<type>-<slug>` now. What this
        guards is that the rule is about characters and structure, not about
        banning a word that looks like a scope.
        """
        validate_plan_name("fix-dsh-pr-102")


class TestSlugLength:
    """The 20-char cap is a creation-time rule, not a lifecycle gate."""

    def test_slug_at_20_chars_is_accepted(self):
        make_plan_name(110, "feature", "token-expiry-refresh")

    @pytest.mark.parametrize("slug", ["deliver-plugin-config", "deliver-plugin-config-table-to-plugins"])
    def test_over_20_chars_raises_with_length_limit_and_fix(self, slug):
        with pytest.raises(ValidationError) as exc_info:
            make_plan_name(110, "feature", slug)
        message = str(exc_info.value)
        assert str(len(slug)) in message, message
        assert "20" in message, message
        assert "--slug" in message, message

    def test_existing_plan_name_skips_the_length_cap(self):
        """An in-flight Plan keeps its name; the branch is already derived."""
        validate_plan_name("refactor-runtime-dsh-foundation", enforce_slug_length=False)


class TestMakePlanName:
    """make_plan_name: builds the name and validates it in the same step."""

    @pytest.mark.parametrize(
        "issue_number,plan_type,slug,expected",
        [
            (110, "feature", "token-expiry", "110-feature-token-expiry"),
            (None, "fix", "token-expiry", "fix-token-expiry"),
            (15, "feat", "add-skills-remove", "15-feature-add-skills-remove"),
            (21, "enhance", "improve-performance", "21-enhance-improve-performance"),
        ],
    )
    def test_builds_expected_name(self, issue_number, plan_type, slug, expected):
        assert make_plan_name(issue_number, plan_type, slug) == expected

    def test_non_ascii_slug_rejected(self):
        with pytest.raises(ValidationError):
            make_plan_name(None, "fix", "评审修复")


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


def _no_issue_args(title, slug, plan_type="feature"):
    return Namespace(
        plan_command="new",
        issue=None,
        title=title,
        project="wopal-cli",
        type=plan_type,
        slug=slug,
    )


class TestNoIssueModeThroughCli:
    """_cmd_plan_new (no-issue): the Plan name comes from --type and --slug only."""

    @pytest.mark.parametrize(
        "title,slug,plan_type,expected_name",
        [
            # a long, structured title does not leak into the name
            ("feat(engine): deliver plugin config table to every plugin", "config-tables",
             "feature", "feature-config-tables"),
            # a Chinese title is irrelevant — the slug decides the name
            ("修复 PR 102 的评审问题", "pr-102", "fix", "fix-pr-102"),
        ],
    )
    def test_name_comes_from_type_and_slug_only(self, tmp_path, title, slug, plan_type, expected_name):
        _write_plan_template(tmp_path)
        assert _run_no_issue_new(_no_issue_args(title, slug, plan_type), tmp_path) == 0
        assert (tmp_path / ".wopal-space" / "plans" / "wopal-cli" / f"{expected_name}.md").is_file()

    def test_missing_slug_rejected_before_write(self, tmp_path):
        """There is no fallback: without --slug nothing is created."""
        _write_plan_template(tmp_path)
        with patch("commands.plan.log_error") as mock_log_error:
            result = _run_no_issue_new(_no_issue_args("feat(engine): add cache layer", None), tmp_path)

        assert result == 1
        plans_root = tmp_path / ".wopal-space" / "plans"
        assert list(plans_root.rglob("*.md")) if plans_root.exists() else [] == []
        message = " ".join(str(call.args[0]) for call in mock_log_error.call_args_list)
        assert "--slug" in message, message

    def test_slug_over_20_chars_rejected_before_write(self, tmp_path):
        _write_plan_template(tmp_path)
        args = _no_issue_args("feat(engine): add cache layer", "deliver-plugin-config-table-to-plugins")
        with patch("commands.plan.log_error") as mock_log_error:
            result = _run_no_issue_new(args, tmp_path)

        assert result == 1
        plans_root = tmp_path / ".wopal-space" / "plans"
        assert list(plans_root.rglob("*.md")) if plans_root.exists() else [] == []
        message = " ".join(str(call.args[0]) for call in mock_log_error.call_args_list)
        assert "20" in message, message
        assert "--slug" in message, message


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, "-v"]))
