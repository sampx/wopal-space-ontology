#!/usr/bin/env python3
"""Project-label behavior for issue create/edit."""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path

ensure_scripts_path()

from commands.issue import cmd_issue_create, register_issue_parser


def _create_args(projects):
    return argparse.Namespace(
        title="feat(flow): flexible issue projects",
        project=projects,
        type="feat",
        body=None,
        body_file=None,
    )


def _successful_gh_result():
    result = MagicMock()
    result.returncode = 0
    result.stdout = "https://github.com/example/repo/issues/42\n"
    result.stderr = ""
    return result


def test_issue_create_without_project_emits_no_project_label():
    with patch("commands.issue.find_workspace_root", return_value="/workspace"):
        with patch("commands.issue.detect_space_repo", return_value="example/repo"):
            with patch("commands.issue.ensure_flow_labels_exist"):
                with patch("commands.issue.ensure_label_exists") as ensure_label:
                    with patch("commands.issue.subprocess.run", return_value=_successful_gh_result()) as run:
                        assert cmd_issue_create(_create_args([])) == 0

    args = run.call_args[0][0]
    labels = [args[index + 1] for index, value in enumerate(args[:-1]) if value == "--label"]
    assert labels == ["status/planning", "type/feature"]
    ensured = [call.args[0] for call in ensure_label.call_args_list]
    assert all(not label.startswith("project/") for label in ensured)


def test_issue_create_accepts_multiple_projects_without_dropping_any():
    with patch("commands.issue.find_workspace_root", return_value="/workspace"):
        with patch("commands.issue.detect_space_repo", return_value="example/repo"):
            with patch("commands.issue.ensure_flow_labels_exist"):
                with patch("commands.issue.ensure_label_exists"):
                    with patch("commands.issue.subprocess.run", return_value=_successful_gh_result()) as run:
                        assert cmd_issue_create(_create_args(["alpha", "beta"])) == 0

    args = run.call_args[0][0]
    labels = [args[index + 1] for index, value in enumerate(args[:-1]) if value == "--label"]
    assert "project/alpha" in labels
    assert "project/beta" in labels


def test_issue_create_project_option_is_repeatable():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register_issue_parser(subparsers)

    args = parser.parse_args([
        "issue", "create",
        "--title", "feat(flow): flexible issue projects",
        "--project", "alpha",
        "--project", "beta",
    ])

    assert args.project == ["alpha", "beta"]


def test_issue_edit_project_options_are_repeatable_and_distinct():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register_issue_parser(subparsers)

    args = parser.parse_args([
        "issue", "edit", "42",
        "--add-project", "alpha",
        "--add-project", "beta",
        "--remove-project", "legacy",
    ])

    assert args.add_project == ["alpha", "beta"]
    assert args.remove_project == ["legacy"]
