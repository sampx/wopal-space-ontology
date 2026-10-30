#!/usr/bin/env python3
"""Umbrella Plan creation and status behavior."""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path

ensure_scripts_path()

from commands.plan import _cmd_plan_new, _cmd_plan_status, register_plan_parser
from plan import get_child_plan_entries, is_umbrella_plan
from validation import check_doc_plan, ValidationError


def _args(**overrides):
    values = {
        "plan_command": "new",
        "issue": None,
        "title": None,
        "project": None,
        "type": "enhance",
        "slug": "release-train",
        "product": None,
        "phase": None,
        "umbrella": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def _write_umbrella_template(workspace: Path) -> None:
    template = workspace / ".wopal" / "skills" / "dev-flow" / "templates" / "umbrella-plan.md"
    template.parent.mkdir(parents=True)
    template.write_text(
        "# {plan_name}\n\n"
        "<!-- author guidance -->\n\n"
        "## Metadata\n\n"
        "- **Plan Kind**: umbrella\n"
        "- **Issue**: {issue}\n"
        "- **Type**: {type}\n"
        "- **Product**: {product}\n"
        "- **Phase**: {phase}\n"
        "- **Created**: {date}\n"
        "- **Status**: planning\n\n"
        "## Goal\n\n<Describe the umbrella goal.>\n\n"
        "## Child Plans\n\n"
        "| Plan | Target Project | Responsibility |\n"
        "|------|----------------|----------------|\n"
    )


def test_plan_new_parser_supports_umbrella_without_project():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register_plan_parser(subparsers)

    args = parser.parse_args([
        "plan", "new", "--umbrella", "--type", "enhance", "--slug", "release-train"
    ])

    assert args.umbrella is True
    assert args.project is None


def test_plan_new_umbrella_creates_reserved_plan_without_project_metadata(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_umbrella_template(workspace)

    with patch("commands.plan.find_workspace_root", return_value=workspace):
        with patch("commands.plan.detect_space_repo", return_value="example/repo"):
            result = _cmd_plan_new(_args())

    assert result == 0
    plan = workspace / ".wopal-space" / "plans" / "_umbrella" / "enhance-release-train.md"
    assert plan.exists()
    text = plan.read_text()
    assert "- **Plan Kind**: umbrella" in text
    assert "- **Issue**: N/A" in text
    assert "- **Target Project**:" not in text
    assert "- **Project Path**:" not in text
    assert "## Child Plans" in text
    assert "<!--" not in text
    assert is_umbrella_plan(str(plan))


def test_plan_new_umbrella_with_issue_does_not_require_one_project_label(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_umbrella_template(workspace)
    issue_info = {
        "title": "coordinate multiple repositories",
        "body": "",
        "number": 42,
        "state": "OPEN",
        "labels": [
            {"name": "project/alpha"},
            {"name": "project/beta"},
        ],
    }

    with patch("commands.plan.find_workspace_root", return_value=workspace):
        with patch("commands.plan.detect_space_repo", return_value="example/repo"):
            with patch("commands.plan.find_plan_by_issue", side_effect=FileNotFoundError):
                with patch("commands.plan._get_issue_info", return_value=issue_info):
                    with patch("commands.plan.ensure_label_exists"):
                        with patch("commands.plan.sync_status_label_group"):
                            result = _cmd_plan_new(_args(issue="42"))

    assert result == 0
    plan = workspace / ".wopal-space" / "plans" / "_umbrella" / "42-enhance-release-train.md"
    assert "- **Issue**: #42" in plan.read_text()


def test_child_plan_parser_reads_name_project_and_responsibility(tmp_path):
    plan = tmp_path / "umbrella.md"
    plan.write_text(
        "# umbrella\n\n## Child Plans\n\n"
        "| Plan | Target Project | Responsibility |\n"
        "|------|----------------|----------------|\n"
        "| `feature-api` | api | expose endpoint |\n"
        "| feature-web | web | consume endpoint |\n"
    )

    assert get_child_plan_entries(str(plan)) == [
        {"name": "feature-api", "project": "api", "responsibility": "expose endpoint"},
        {"name": "feature-web", "project": "web", "responsibility": "consume endpoint"},
    ]


def test_plan_status_umbrella_reports_live_child_state_and_missing_child(tmp_path, capsys):
    workspace = tmp_path / "workspace"
    umbrella_dir = workspace / ".wopal-space" / "plans" / "_umbrella"
    api_dir = workspace / ".wopal-space" / "plans" / "api"
    umbrella_dir.mkdir(parents=True)
    api_dir.mkdir(parents=True)

    umbrella = umbrella_dir / "enhance-release-train.md"
    umbrella.write_text(
        "# enhance-release-train\n\n"
        "## Metadata\n\n"
        "- **Plan Kind**: umbrella\n"
        "- **Issue**: N/A\n"
        "- **Type**: enhance\n"
        "- **Product**:\n"
        "- **Phase**:\n"
        "- **Created**: 2026-10-30\n"
        "- **Status**: planning\n\n"
        "## Child Plans\n\n"
        "| Plan | Target Project | Responsibility |\n"
        "|------|----------------|----------------|\n"
        "| feature-api | api | expose endpoint |\n"
        "| feature-missing | web | consume endpoint |\n"
    )
    child = api_dir / "feature-api.md"
    child.write_text(
        "# feature-api\n\n## Metadata\n\n"
        "- **Issue**: #11\n"
        "- **Type**: feature\n"
        "- **Target Project**: api\n"
        "- **Created**: 2026-10-30\n"
        "- **Status**: executing\n"
    )

    with patch("commands.plan.find_workspace_root", return_value=workspace):
        with patch("commands.plan.find_plan", return_value=str(umbrella)):
            assert _cmd_plan_status("enhance-release-train") == 0

    output = capsys.readouterr().out
    assert "feature-api" in output
    assert "api" in output
    assert "#11" in output
    assert "executing" in output
    assert "feature-missing" in output
    assert "web" in output
    assert "MISSING" in output


def test_umbrella_check_rejects_reusing_umbrella_issue_for_multiple_children(tmp_path):
    workspace = tmp_path / "workspace"
    umbrella_dir = workspace / ".wopal-space" / "plans" / "_umbrella"
    api_dir = workspace / ".wopal-space" / "plans" / "api"
    web_dir = workspace / ".wopal-space" / "plans" / "web"
    umbrella_dir.mkdir(parents=True)
    api_dir.mkdir(parents=True)
    web_dir.mkdir(parents=True)

    umbrella = umbrella_dir / "42-enhance-release-train.md"
    umbrella.write_text(
        "# 42-enhance-release-train\n\n## Metadata\n\n"
        "- **Plan Kind**: umbrella\n"
        "- **Issue**: #42\n"
        "- **Type**: enhance\n"
        "- **Product**:\n- **Phase**:\n"
        "- **Created**: 2026-10-30\n"
        "- **Status**: planning\n\n"
        "## Child Plans\n\n"
        "| Plan | Target Project | Responsibility |\n"
        "|------|----------------|----------------|\n"
        "| feature-api | api | api |\n"
        "| feature-web | web | web |\n"
    )
    for path, name, project in [
        (api_dir / "feature-api.md", "feature-api", "api"),
        (web_dir / "feature-web.md", "feature-web", "web"),
    ]:
        path.write_text(
            f"# {name}\n\n## Metadata\n\n"
            "- **Issue**: #42\n"
            "- **Type**: feature\n"
            f"- **Target Project**: {project}\n"
            f"- **Project Path**: projects/{project}\n"
            "- **Product**:\n- **Phase**:\n"
            "- **Created**: 2026-10-30\n"
            "- **Status**: planning\n"
        )

    with pytest.raises(ValidationError, match="umbrella Issue"):
        check_doc_plan(str(umbrella))
