#!/usr/bin/env python3
# test_verify.py - Unit tests for verify command (merge status check)

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from support.git_fixtures import (
    init_repo as _shell_init_repo,
    install_failing_hook as _shell_install_failing_hook,
    shell_git as _shell_git,
)


# -- Fixtures -----------------------------------------------------------------

PLAN_VERIFYING_STANDARD = """\
- **Status**: verifying
- **Type**: feature
- **Target Project**: gesp
- **Project Type**: standard
- **Project Path**: projects/gesp
- **Issue**: #42
- **Worktree**:
  - enabled: true
  - branch: feature/test-1-slug
  - path: .worktrees/gesp-issue-1-slug
  - repo_root: /workspace/projects/gesp
  - base_branch: main
  - merge_target: main
  - verify_mode: direct
  - cleanup_policy: archive
"""

PLAN_VERIFYING_NO_WORKTREE = """\
- **Status**: verifying
- **Type**: feature
- **Target Project**: gesp
- **Project Type**: standard
- **Project Path**: projects/gesp
- **Issue**: #42
"""


def _write_plan(tmp_path, content: str, name: str = "42-feature-dev-flow-test.md") -> Path:
    """Write a Plan file with given content and return its path."""
    plan_dir = tmp_path / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / name
    plan_file.write_text(content)
    return plan_file


# -- Test: Final Commit recording -------------------------------------------------

class TestVerifyRecordsFinalCommit:
    """verify 应记录 Final Commit(合入后集成分支 HEAD)到 Plan metadata。"""

    def test_final_commit_records_integration_head(self, tmp_path):
        """Final Commit 应取集成分支 HEAD(standard: main)。"""
        from commands.verify import _record_final_commit
        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD)
        proj_dir = tmp_path / "projects" / "gesp"
        proj_dir.mkdir(parents=True)
        (proj_dir / ".git").mkdir()

        with patch("commands.verify.get_branch_head", return_value="deadbeef") as mock_head:
            with patch("commands.verify.set_plan_field", return_value=True) as mock_set:
                _record_final_commit(str(plan_path), tmp_path)

        mock_head.assert_called_once()
        mock_set.assert_called_once_with(
            str(plan_path), "Final Commit", "deadbeef"
        )

    def test_final_commit_uses_main_branch(self, tmp_path):
        """standard 项目 Final Commit 用 main 分支。"""
        from commands.verify import _record_final_commit
        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD)
        proj_dir = tmp_path / "projects" / "gesp"
        proj_dir.mkdir(parents=True)
        (proj_dir / ".git").mkdir()

        with patch("commands.verify.get_branch_head", return_value="abc123") as mock_head:
            with patch("commands.verify.set_plan_field", return_value=True):
                _record_final_commit(str(plan_path), tmp_path)

        cmd = mock_head.call_args[0][0]
        assert cmd == str(tmp_path / "projects" / "gesp")
        branch = mock_head.call_args[0][1]
        assert branch == "main"


# -- Test: _check_feature_branch_merged function -------------------------------

class TestCheckFeatureBranchMerged:
    """Test _check_feature_branch_merged helper function.

    After refactoring, _check_feature_branch_merged delegates to
    lib.git.check_branch_merged. Mocks target lib.git where the actual
    subprocess and log_error calls happen.
    """

    def test_standard_branch_merged_returns_zero(self, tmp_path):
        """Standard project: feature branch is in merged list, returns 0."""
        from commands.verify import _check_feature_branch_merged

        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD)
        # Create project dir with .git so repo_root resolves
        proj_dir = tmp_path / "projects" / "gesp"
        proj_dir.mkdir(parents=True)
        (proj_dir / ".git").mkdir()

        merged_output = "  main\n* feature/test-1-slug\n"

        with patch("lib.git.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=merged_output,
            )
            result = _check_feature_branch_merged(tmp_path, str(plan_path))

        assert result == 0

    def test_standard_branch_not_merged_returns_one(self, tmp_path):
        """Standard project: feature branch NOT in merged list, returns 1."""
        from commands.verify import _check_feature_branch_merged

        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD)
        proj_dir = tmp_path / "projects" / "gesp"
        proj_dir.mkdir(parents=True)
        (proj_dir / ".git").mkdir()

        # Subprocess calls: local merged, tree x2, remote merged, git log --grep
        def fake_run(cmd, *args, **kwargs):
            if cmd[0] == "git" and cmd[1] == "branch" and "--merged" in cmd and "-r" not in cmd:
                return MagicMock(returncode=0, stdout="  main\n")
            if "rev-parse" in cmd and any("^{tree}" in c for c in cmd):
                return MagicMock(returncode=0, stdout="tree-diff-main\n")
            if cmd[1] == "branch" and "-r" in cmd:
                return MagicMock(returncode=0, stdout="")
            return MagicMock(returncode=0, stdout="")

        # Override: feature tree differs from integration tree
        def fake_run2(cmd, *args, **kwargs):
            if "rev-parse" in cmd and any("^{tree}" in c for c in cmd):
                if any("feature/test-1-slug" in c for c in cmd):
                    return MagicMock(returncode=0, stdout="tree-diff-feature\n")
                return MagicMock(returncode=0, stdout="tree-diff-main\n")
            return fake_run(cmd, *args, **kwargs)

        with patch("lib.git.subprocess.run", side_effect=fake_run2) as mock_run:
            with patch("lib.git.log_error") as mock_log:
                result = _check_feature_branch_merged(tmp_path, str(plan_path))

        assert result == 1
        mock_log.assert_any_call(
            "Feature branch 'feature/test-1-slug' not yet merged to main. "
            "Please merge first."
        )

    def test_no_worktree_metadata_returns_zero(self, tmp_path):
        """Plan without worktree metadata: skip check, returns 0."""
        from commands.verify import _check_feature_branch_merged

        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_NO_WORKTREE)

        result = _check_feature_branch_merged(tmp_path, str(plan_path))
        assert result == 0

    def test_no_branch_in_worktree_returns_zero(self, tmp_path):
        """Worktree metadata without branch: skip check, returns 0."""
        from commands.verify import _check_feature_branch_merged

        plan_content = PLAN_VERIFYING_NO_WORKTREE + "\n- **Worktree**:  | .worktrees/some-path\n"
        plan_path = _write_plan(tmp_path, plan_content)

        with patch("plan.get_plan_worktree", return_value={"branch": "", "path": ""}):
            result = _check_feature_branch_merged(tmp_path, str(plan_path))

        assert result == 0

    def test_git_command_failure_returns_one(self, tmp_path):
        """git branch --merged fails: returns 1."""
        from commands.verify import _check_feature_branch_merged

        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD)
        proj_dir = tmp_path / "projects" / "gesp"
        proj_dir.mkdir(parents=True)
        (proj_dir / ".git").mkdir()

        with patch("lib.git.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128,
                stderr="fatal: bad revision 'unknown'",
            )
            with patch("lib.git.log_error") as mock_log:
                result = _check_feature_branch_merged(tmp_path, str(plan_path))

        assert result == 1
        mock_log.assert_any_call(
            "Failed to check merge status for branch 'feature/test-1-slug'"
        )

    def test_uses_correct_integration_branch(self, tmp_path):
        """Verify git branch --merged is called with correct integration branch."""
        from commands.verify import _check_feature_branch_merged

        # Standard → main (branch in merged list → fallback not triggered)
        plan_path_std = _write_plan(
            tmp_path, PLAN_VERIFYING_STANDARD, name="42-std.md"
        )
        proj_dir = tmp_path / "projects" / "gesp"
        proj_dir.mkdir(parents=True)
        (proj_dir / ".git").mkdir()

        def fake_run_std(cmd, *args, **kwargs):
            if cmd[0] == "git" and cmd[1] == "branch" and "--merged" in cmd and "-r" not in cmd:
                return MagicMock(returncode=0, stdout="  main\n* feature/test-1-slug\n")
            return MagicMock(returncode=0, stdout="")

        with patch("lib.git.subprocess.run", side_effect=fake_run_std) as mock_run:
            _check_feature_branch_merged(tmp_path, str(plan_path_std))

        merged_calls = [
            c.args[0] for c in mock_run.call_args_list
            if "--merged" in c.args[0]
        ]
        assert merged_calls, "expected git branch --merged call"
        cmd = merged_calls[0]
        assert "--merged" in cmd
        assert "main" in cmd

    def test_verify_keep_worktree_skips_merge_check_and_records_feature_head(self, tmp_path):
        """verify --keep-worktree 应跳过合并检测并将 Final Commit 记录为 feature 分支 HEAD。"""
        import argparse
        from commands.verify import cmd_verify

        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD, name="42-keep.md")
        # Ensure worktree directory exists
        wt_dir = tmp_path / ".worktrees" / "gesp-issue-1-slug"
        wt_dir.mkdir(parents=True)

        with patch("commands.verify.find_workspace_root", return_value=tmp_path):
            with patch("commands.verify.find_plan", return_value=str(plan_path)):
                with patch("commands.verify.check_user_validation"):
                    with patch("commands.verify.get_branch_head", return_value="feature_tip_sha_123"):
                        with patch("commands.verify.commit_paths", return_value=True):
                            args = argparse.Namespace(
                                target="42",
                                confirm=True,
                                keep_worktree=True,
                            )
                            result = cmd_verify(args)

        assert result == 0
        from plan import get_plan_field
        assert get_plan_field(str(plan_path), "Final Commit") == "feature_tip_sha_123"

    def test_verify_keep_worktree_aborts_when_head_unresolvable(self, tmp_path):
        """verify --keep-worktree 在无法获取 feature HEAD 时报错中止，不推进到 done。"""
        import argparse
        from commands.verify import cmd_verify

        plan_path = _write_plan(tmp_path, PLAN_VERIFYING_STANDARD, name="42-err.md")
        # Ensure worktree directory exists on disk so it passes is_dir() check and tests get_branch_head failure
        wt_dir = tmp_path / ".worktrees" / "gesp-issue-1-slug"
        wt_dir.mkdir(parents=True)

        with patch("commands.verify.find_workspace_root", return_value=tmp_path):
            with patch("commands.verify.find_plan", return_value=str(plan_path)):
                with patch("commands.verify.check_user_validation"):
                    with patch("commands.verify.get_branch_head", return_value=""):
                        args = argparse.Namespace(
                            target="42",
                            confirm=True,
                            keep_worktree=True,
                        )
                        result = cmd_verify(args)

        assert result == 1
        from plan import get_plan_status
        assert get_plan_status(str(plan_path)) == "verifying"


# ============================================
# cmd_verify durability gate (Task 4, AC#6)
# ============================================
#
# Real construction: a temp workspace repo holding a verifying Plan and a
# project repo supplying Final Commit. The Plan rewrite, the git commit and
# the retry run for real; network side effects (PR lookups / Issue sync /
# gh close) are mocked so the failure path can assert they are unreached.

VERIFY_PLAN_REL = ".wopal-space/plans/ontology/204-fix-verifying-plan.md"

VERIFY_PLAN_TEMPLATE = """\
# 204-fix-verifying-plan

## Metadata

- **Issue**: #204
- **Type**: fix
- **Target Project**: gesp
- **Project Type**: standard
- **Project Path**: projects/gesp
- **Status**: verifying

## Goal

Verifying plan used by the verify durability-gate tests.

## Acceptance Criteria

### User Validation

#### Scenario 1: gate behavior
- Goal: confirm verify runs
- Launch Command: `flow.sh verify 204 --confirm`
- Pass Criteria: Plan reaches done

- [x] 用户已完成上述功能验证并确认结果符合预期
"""


def _make_verify_workspace(tmp_path):
    ws = tmp_path / "ws"
    _shell_init_repo(ws)
    _shell_init_repo(ws / "projects" / "gesp")
    plan = ws / VERIFY_PLAN_REL
    plan.parent.mkdir(parents=True)
    plan.write_text(VERIFY_PLAN_TEMPLATE)
    _shell_git("add", VERIFY_PLAN_REL, cwd=ws)
    _shell_git("commit", "-m", "add plan", cwd=ws)
    return ws, plan


def _run_verify(ws, target="204"):
    """Run cmd_verify with workspace/repo detection and network mocked."""
    from argparse import Namespace

    from commands.verify import cmd_verify

    close_run = MagicMock(return_value=MagicMock(returncode=0))
    sync_label = MagicMock()
    sync_body = MagicMock()
    with patch.multiple(
        "commands.verify",
        find_workspace_root=MagicMock(return_value=ws),
        resolve_space_repo=MagicMock(return_value="test/space"),
        sync_status_label=sync_label,
        sync_plan_to_issue_body=sync_body,
        _get_pr_url_from_issue=MagicMock(return_value=""),
        _search_merged_pr_for_issue=MagicMock(return_value=False),
        subprocess=MagicMock(run=close_run),
    ):
        result = cmd_verify(Namespace(target=target, confirm=True))
    return result, sync_label, sync_body, close_run


class TestVerifyDurabilityGate:
    """A failed Plan commit must not reach Issue sync/close and must leave
    the Plan retryable (AC#6)."""

    def test_commit_failure_blocks_sync_and_close_and_restores_plan(
        self, tmp_path, capsys
    ):
        ws, plan = _make_verify_workspace(tmp_path)
        original = plan.read_text()
        _shell_install_failing_hook(ws, "injected verify-commit failure")

        result, sync_label, sync_body, close_run = _run_verify(ws)

        assert result == 1
        assert plan.read_text() == original
        assert "- **Status**: verifying" in plan.read_text()
        assert "Final Commit" not in plan.read_text()
        # No staged Plan residue: a retry sees the same clean state.
        assert _shell_git(
            "status", "--porcelain", "--", VERIFY_PLAN_REL, cwd=ws
        ).stdout == ""
        sync_label.assert_not_called()
        sync_body.assert_not_called()
        close_run.assert_not_called()
        out, err = capsys.readouterr()
        assert "injected verify-commit failure" in (out + err)

    def test_retry_after_commit_failure_succeeds(self, tmp_path):
        ws, plan = _make_verify_workspace(tmp_path)
        hook = _shell_install_failing_hook(ws, "injected verify-commit failure")

        first, _, _, _ = _run_verify(ws)
        assert first == 1

        hook.unlink()
        second, sync_label, sync_body, close_run = _run_verify(ws)

        assert second == 0
        committed = _shell_git("show", f"HEAD:{VERIFY_PLAN_REL}", cwd=ws).stdout
        assert "- **Status**: done" in committed
        assert "Final Commit" in committed
        assert _shell_git(
            "log", "-1", "--format=%s", cwd=ws
        ).stdout.strip() == "docs(plan): verify plan #204"
        assert _shell_git(
            "status", "--porcelain", "--", VERIFY_PLAN_REL, cwd=ws
        ).stdout == ""
        sync_label.assert_called_once_with(204, "done", "test/space")
        sync_body.assert_called_once()
        close_run.assert_called_once()
        assert "close" in close_run.call_args[0][0]

    def test_success_path_commits_done_and_syncs(self, tmp_path):
        ws, plan = _make_verify_workspace(tmp_path)

        result, sync_label, sync_body, close_run = _run_verify(ws)

        assert result == 0
        committed = _shell_git("show", f"HEAD:{VERIFY_PLAN_REL}", cwd=ws).stdout
        assert "- **Status**: done" in committed
        sync_label.assert_called_once()
        sync_body.assert_called_once()
        close_run.assert_called_once()
