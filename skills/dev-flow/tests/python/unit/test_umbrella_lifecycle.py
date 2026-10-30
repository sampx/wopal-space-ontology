#!/usr/bin/env python3
"""Lifecycle gates for coordination-only umbrella Plans."""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path

ensure_scripts_path()

from lib.umbrella import child_gate_failures, resolve_child_states
from commands.approve import cmd_approve
from commands.complete import cmd_complete
from commands.verify import cmd_verify
from commands.archive import cmd_archive
from commands.integrate import cmd_integrate
from commands.verify_switch import run_verify_switch


def _plan_text(*, kind="normal", status="executing", project="api", issue="N/A"):
    kind_line = "- **Plan Kind**: umbrella\n" if kind == "umbrella" else ""
    project_lines = "" if kind == "umbrella" else (
        f"- **Target Project**: {project}\n"
        f"- **Project Path**: projects/{project}\n"
    )
    return (
        "# plan\n\n## Metadata\n\n"
        f"{kind_line}"
        f"- **Issue**: {issue}\n"
        "- **Type**: enhance\n"
        f"{project_lines}"
        "- **Product**:\n- **Phase**:\n"
        "- **Created**: 2026-10-30\n"
        f"- **Status**: {status}\n"
    )


def _write_umbrella(workspace: Path, status: str, rows: list[tuple[str, str, str]]) -> Path:
    directory = workspace / ".wopal-space" / "plans" / "_umbrella"
    directory.mkdir(parents=True, exist_ok=True)
    plan = directory / "enhance-release-train.md"
    table = "\n".join(f"| {name} | {project} | {role} |" for name, project, role in rows)
    plan.write_text(
        _plan_text(kind="umbrella", status=status)
        + "\n## Acceptance Criteria\n\n"
        + "### Agent Verification\n\n1. [x] children satisfy the gate\n\n"
        + "### User Validation\n\nN/A — automated coordination only\n\n"
        + "## Child Plans\n\n"
        + "| Plan | Target Project | Responsibility |\n"
        + "|------|----------------|----------------|\n"
        + table + "\n"
    )
    return plan


def _write_child(workspace: Path, name: str, project: str, status: str, issue: str = "N/A") -> Path:
    directory = workspace / ".wopal-space" / "plans" / project
    directory.mkdir(parents=True, exist_ok=True)
    child = directory / f"{name}.md"
    child.write_text(_plan_text(status=status, project=project, issue=issue))
    return child


def _archive_child(workspace: Path, child: Path) -> Path:
    done = child.parent / "done"
    done.mkdir()
    archived = done / f"20261030-{child.name}"
    child.rename(archived)
    return archived


def test_child_state_resolution_supports_same_project_cross_project_archived_and_missing(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "executing", [
        ("api-one", "api", "first API change"),
        ("api-two", "api", "second API change"),
        ("web-one", "web", "web change"),
        ("missing-one", "worker", "missing change"),
    ])
    _write_child(ws, "api-one", "api", "verifying", "#11")
    api_two = _write_child(ws, "api-two", "api", "done", "#12")
    _archive_child(ws, api_two)
    _write_child(ws, "web-one", "web", "done", "#13")

    states = resolve_child_states(str(umbrella), ws)
    by_name = {state.name: state for state in states}
    assert by_name["api-one"].status == "verifying"
    assert by_name["api-one"].project == "api"
    assert by_name["api-one"].issue == 11
    assert by_name["api-two"].status == "archived"
    assert by_name["web-one"].project == "web"
    assert by_name["missing-one"].missing is True


def test_child_state_resolution_uses_declared_project_to_disambiguate_same_plan_name(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "executing", [
        ("feature-sync", "api", "api sync"),
        ("feature-sync", "web", "web sync"),
    ])
    _write_child(ws, "feature-sync", "api", "verifying", "#11")
    _write_child(ws, "feature-sync", "web", "done", "#12")

    states = resolve_child_states(str(umbrella), ws)

    assert [(state.project, state.issue, state.status) for state in states] == [
        ("api", 11, "verifying"),
        ("web", 12, "done"),
    ]


def test_missing_declared_project_child_does_not_bind_same_name_from_other_project(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "executing", [
        ("feature-sync", "api", "api sync"),
    ])
    _write_child(ws, "feature-sync", "web", "done", "#12")

    states = resolve_child_states(str(umbrella), ws)

    assert len(states) == 1
    assert states[0].missing is True
    assert states[0].declared_project == "api"


def test_child_gates_match_complete_verify_and_archive_contract(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "executing", [
        ("a", "api", "a"),
        ("b", "web", "b"),
    ])
    a = _write_child(ws, "a", "api", "verifying")
    b = _write_child(ws, "b", "web", "done")

    assert child_gate_failures(str(umbrella), ws, "complete") == []
    assert child_gate_failures(str(umbrella), ws, "verify") == ["a (verifying)"]
    _archive_child(ws, b)
    assert child_gate_failures(str(umbrella), ws, "archive") == ["a (verifying)"]
    a.write_text(a.read_text().replace("verifying", "done"))
    assert child_gate_failures(str(umbrella), ws, "verify") == []
    _archive_child(ws, a)
    assert child_gate_failures(str(umbrella), ws, "archive") == []


def test_approve_umbrella_skips_delivery_and_worktree(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "reviewing", [])
    args = argparse.Namespace(
        target="enhance-release-train", confirm=True,
        no_worktree=False, existing_worktree=None,
    )

    with patch("commands.approve.find_workspace_root", return_value=ws), \
         patch("commands.approve.find_plan", return_value=str(umbrella)), \
         patch("commands.approve.check_doc_plan"), \
         patch("commands.approve.detect_space_repo", return_value="example/repo"), \
         patch("commands.approve.commit_and_push_plan", return_value="ok"), \
         patch("commands.approve._prepare_delivery_fields") as delivery, \
         patch("commands.approve._create_worktree") as create_worktree:
        assert cmd_approve(args) == 0

    delivery.assert_not_called()
    create_worktree.assert_not_called()
    assert "- **Status**: executing" in umbrella.read_text()


def test_complete_umbrella_blocks_until_every_child_is_at_least_verifying(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "executing", [("child", "api", "api")])
    child = _write_child(ws, "child", "api", "executing")
    before = child.read_text()
    active = SimpleNamespace(
        active_plan_path=umbrella,
        commit_repo_root=ws,
        repo_relative_plan_path=str(umbrella.relative_to(ws)),
        branch_context="integration",
    )

    with patch("commands.complete.find_workspace_root", return_value=ws), \
         patch("commands.complete.find_plan", return_value=str(umbrella)), \
         patch("commands.complete.resolve_active_plan", return_value=active), \
         patch("commands.complete._commit_plan_status_or_rollback", return_value=True), \
         patch("commands.complete.is_repo_dirty") as dirty:
        assert cmd_complete(argparse.Namespace(target="enhance-release-train", pr=False)) == 1

    dirty.assert_not_called()
    assert child.read_text() == before
    assert "- **Status**: executing" in umbrella.read_text()


def test_complete_umbrella_advances_when_children_ready_without_touching_children(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "executing", [("child", "api", "api")])
    child = _write_child(ws, "child", "api", "verifying")
    before = child.read_text()
    active = SimpleNamespace(
        active_plan_path=umbrella,
        commit_repo_root=ws,
        repo_relative_plan_path=str(umbrella.relative_to(ws)),
        branch_context="integration",
    )

    with patch("commands.complete.find_workspace_root", return_value=ws), \
         patch("commands.complete.find_plan", return_value=str(umbrella)), \
         patch("commands.complete.resolve_active_plan", return_value=active), \
         patch("commands.complete._commit_plan_status_or_rollback", return_value=True), \
         patch("commands.complete.resolve_space_repo", return_value=None), \
         patch("commands.complete.is_repo_dirty") as dirty:
        assert cmd_complete(argparse.Namespace(target="enhance-release-train", pr=False)) == 0

    dirty.assert_not_called()
    assert child.read_text() == before
    assert "- **Status**: verifying" in umbrella.read_text()


def test_verify_umbrella_requires_done_children_and_skips_delivery_git(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "verifying", [("child", "api", "api")])
    child = _write_child(ws, "child", "api", "verifying")
    active = SimpleNamespace(
        active_plan_path=umbrella,
        commit_repo_root=ws,
        repo_relative_plan_path=str(umbrella.relative_to(ws)),
        branch_context="integration",
    )
    args = argparse.Namespace(target="enhance-release-train", confirm=True, keep_worktree=False)

    with patch("commands.verify.find_workspace_root", return_value=ws), \
         patch("commands.verify.find_plan", return_value=str(umbrella)), \
         patch("commands.verify.resolve_active_plan", return_value=active), \
         patch("commands.verify.resolve_space_repo", return_value=None), \
         patch("commands.verify._commit_plan_status_or_rollback", return_value=True), \
         patch("commands.verify._check_recorded_integration") as integration_check, \
         patch("commands.verify._check_feature_branch_merged") as merge_check:
        assert cmd_verify(args) == 1

    integration_check.assert_not_called()
    merge_check.assert_not_called()
    assert "- **Status**: verifying" in umbrella.read_text()

    child.write_text(child.read_text().replace("verifying", "done"))
    with patch("commands.verify.find_workspace_root", return_value=ws), \
         patch("commands.verify.find_plan", return_value=str(umbrella)), \
         patch("commands.verify.resolve_active_plan", return_value=active), \
         patch("commands.verify.resolve_space_repo", return_value=None), \
         patch("commands.verify._commit_plan_status_or_rollback", return_value=True), \
         patch("commands.verify._check_recorded_integration") as integration_check, \
         patch("commands.verify._check_feature_branch_merged") as merge_check:
        assert cmd_verify(args) == 0

    integration_check.assert_not_called()
    merge_check.assert_not_called()
    assert "- **Status**: done" in umbrella.read_text()


def test_archive_umbrella_blocks_until_all_children_are_archived(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "done", [("child", "api", "api")])
    _write_child(ws, "child", "api", "done")
    args = argparse.Namespace(target="enhance-release-train", force=False, keep_worktree=False)

    with patch("commands.archive.find_workspace_root", return_value=ws), \
         patch("commands.archive.find_plan", return_value=str(umbrella)), \
         patch("commands.archive.archive_plan_file") as archive_file:
        assert cmd_archive(args) == 1

    archive_file.assert_not_called()


def test_archive_umbrella_succeeds_after_all_children_are_archived_without_code_cleanup(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "done", [("child", "api", "api")])
    child = _write_child(ws, "child", "api", "done")
    _archive_child(ws, child)
    archived_umbrella = (
        ws / ".wopal-space" / "plans" / "_umbrella" / "done" /
        "20261030-enhance-release-train.md"
    )
    args = argparse.Namespace(target="enhance-release-train", force=False, keep_worktree=False)
    location = SimpleNamespace(repo_root=ws, branch="main")

    with patch("commands.archive.find_workspace_root", return_value=ws), \
         patch("commands.archive.find_plan", return_value=str(umbrella)), \
         patch("commands.archive.resolve_space_repo", return_value=None), \
         patch("commands.archive.archive_plan_file", return_value=str(archived_umbrella)) as archive_file, \
         patch("commands.archive.resolve_plan_location", return_value=location), \
         patch("commands.archive._stage_archived_plan", return_value=None), \
         patch("commands.archive._update_phase_doc_plan_status", return_value=None), \
         patch("commands.archive.commit_archived_plan", return_value=True), \
         patch("commands.archive._detect_worktree") as detect_worktree, \
         patch("commands.archive._cleanup_worktree") as cleanup_worktree:
        assert cmd_archive(args) == 0

    archive_file.assert_called_once()
    detect_worktree.assert_not_called()
    cleanup_worktree.assert_not_called()


def test_integrate_and_verify_switch_reject_umbrella_before_git(tmp_path):
    ws = tmp_path / "ws"
    umbrella = _write_umbrella(ws, "verifying", [])

    with patch("commands.integrate.find_workspace_root", return_value=ws), \
         patch("commands.integrate.find_plan", return_value=str(umbrella)), \
         patch("commands.integrate.get_branch_head") as git_head:
        assert cmd_integrate(argparse.Namespace(target="enhance-release-train", confirm=True)) == 1
    git_head.assert_not_called()

    with patch("commands.verify_switch.find_workspace_root", return_value=ws), \
         patch("commands.verify_switch.find_plan", return_value=str(umbrella)), \
         patch("commands.verify_switch._git_fetch") as git_fetch:
        assert run_verify_switch("enhance-release-train") is False
    git_fetch.assert_not_called()
