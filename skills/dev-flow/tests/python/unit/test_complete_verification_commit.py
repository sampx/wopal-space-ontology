#!/usr/bin/env python3
# test_complete_verification_commit.py
#
# complete 必须在 plan 所在仓库写入 Verification Commit 字段（供 verify L1
# 祖先检测）。当 feature 分支不在空间仓库（verify-switch 移除 worktree 后，
# 分支只存在于项目仓库）时，rev-parse 必须回退到代码仓库，失败则显式告警
# 而不是静默跳过。
#
# 同时覆盖 complete 的 Plan commit durability gate（Task 3）：commit 失败
# 时不得执行 Issue sync、不得返回 0，且 Plan 必须回到可重试状态。

import unittest
import json
import sys
import os
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from support.git_fixtures import (
    init_repo as _shell_init_repo,
    install_failing_hook as _shell_install_failing_hook,
    shell_git as _shell_git,
)

from commands.complete import _record_verification_commit


def _write_plan(tmp_path: str, branch: str = "feature/test-1-slug") -> str:
    content = f"""\
# test-plan

## Metadata
- **Status**: executing
- **Target Project**: gesp
- **Project Type**: standard
- **Project Path**: projects/gesp
- **Issue**: #42
- **Worktree**:
  - branch: {branch}
  - path: .worktrees/gesp-issue-1-slug

## Goal

Test.
"""
    plan_path = os.path.join(tmp_path, "42-feature-test.md")
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(content)
    return plan_path


class ActiveInfo:
    def __init__(self, repo_root: str):
        self.commit_repo_root = Path(repo_root)
        self.repo_relative_plan_path = "x.md"


class TestRecordVerificationCommit(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="dev-flow-vc-")
        self.space_repo = os.path.join(self.tmp, "space")
        self.code_repo = os.path.join(self.tmp, "code")
        os.makedirs(self.space_repo)
        os.makedirs(self.code_repo)
        self.plan_path = _write_plan(self.tmp)
        self.active = ActiveInfo(self.space_repo)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fake_run(self, cmd, cwd=None, **kwargs):
        if cmd[0] == "git" and cmd[1] == "rev-parse":
            if Path(cwd) == Path(self.space_repo):
                return MagicMock(
                    returncode=128, stdout="", stderr="fatal: unknown revision"
                )
            return MagicMock(returncode=0, stdout="abc123def456\n")
        return MagicMock(returncode=0, stdout="")

    def test_falls_back_to_code_repo_when_space_repo_lacks_branch(self):
        with patch(
            "commands.complete.subprocess.run", side_effect=self._fake_run
        ):
            with patch(
                "commands.complete.resolve_project_path",
                return_value=Path(self.code_repo),
            ):
                result = _record_verification_commit(
                    self.plan_path, Path(self.tmp), self.active
                )

        self.assertEqual(result, "abc123def456")
        with open(self.plan_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("- **Verification Commit**: abc123def456", content)

    def test_warns_when_branch_unresolvable_everywhere(self):
        def fake_run(cmd, cwd=None, **kwargs):
            if cmd[0] == "git" and cmd[1] == "rev-parse":
                return MagicMock(returncode=128, stdout="", stderr="fatal")
            return MagicMock(returncode=0, stdout="")

        with patch(
            "commands.complete.subprocess.run", side_effect=fake_run
        ):
            with patch("commands.complete.log_warn") as mock_warn:
                result = _record_verification_commit(
                    self.plan_path, Path(self.tmp), self.active
                )

        self.assertEqual(result, "")
        mock_warn.assert_called_once()
        with open(self.plan_path, encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("Verification Commit", content)

    def test_no_worktree_metadata_skips(self):
        import tempfile
        no_wt = os.path.join(tempfile.mkdtemp(prefix="dev-flow-vc-nw-"))
        plan_path = os.path.join(no_wt, "p.md")
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write("# p\n\n## Metadata\n- **Status**: executing\n")

        with patch("commands.complete.get_plan_worktree", return_value=None):
            result = _record_verification_commit(
                plan_path, Path(no_wt), self.active
            )

        self.assertEqual(result, "")


# ============================================
# cmd_complete durability gate (Task 3, AC#3)
# ============================================
#
# Construction: a temp workspace repo (+ bare origin) holding a Plan derived
# from tests/fixtures/plans/106-fix-dev-flow-valid-issue-plan.md — Status set
# to executing, and both checked Agent Verification entries extended with an
# executable command (two-beat AC, beat 2; the commands mirror the fixture's
# own Test Plan scripts). Workspace/repo detection and Issue sync are mocked;
# the Plan file, git commits and the real validation gates run for real.

FIXTURE_106 = (
    Path(__file__).resolve().parents[2]
    / "fixtures" / "plans" / "106-fix-dev-flow-valid-issue-plan.md"
)
PR_SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "fixtures" / "github" / "pr-merged-recorded.json"
)
COMPLETE_PLAN_REL = (
    ".wopal-space/plans/ontology/106-fix-dev-flow-valid-issue-plan.md"
)


def _recorded_pr_url() -> str:
    """PR URL from a recorded `gh pr list` sample (R2)."""
    return json.loads(PR_SAMPLE.read_text())[0]["url"]


def _make_complete_workspace(tmp_path, no_issue: bool = False):
    ws = tmp_path / "ws"
    _shell_init_repo(ws)
    origin = tmp_path / "ws-origin.git"
    _shell_git("init", "--bare", "-b", "main", str(origin), cwd=tmp_path)
    _shell_git("remote", "add", "origin", str(origin), cwd=ws)
    project = ws / "projects" / "ontology"
    _shell_init_repo(project)
    # The Worktree feature branch exists in the project repo, so
    # _record_verification_commit resolves it and writes the field.
    _shell_git("branch", "feature/complete-vc", cwd=project)

    plan_text = (
        FIXTURE_106.read_text()
        .replace("- **Status**: planning", "- **Status**: executing")
        .replace(
            "- **Status**: executing",
            "- **Status**: executing\n- **Worktree**:\n"
            "  - branch: feature/complete-vc\n"
            "  - path: .worktrees/complete-vc",
        )
        .replace(
            "- [x] approve.sh 的 push 检测基于文件级 commit 可达性",
            "- [x] approve.sh 的 push 检测基于文件级 commit 可达性 — "
            "`python -m pytest tests/unit/test-approve-push.sh`",
        )
        .replace(
            "- [x] 无 Issue 模式 complete --pr 走真实 helper",
            "- [x] 无 Issue 模式 complete --pr 走真实 helper — "
            "`python -m pytest tests/unit/test-complete-pr.sh`",
        )
    )
    if no_issue:
        plan_text = plan_text.replace("- **Issue**: #106\n", "")
        assert "- **Issue**" not in plan_text
    assert "executing" in plan_text
    assert plan_text.count("`python -m pytest") == 2
    # The Worktree branch must be resolvable so _record_verification_commit
    # writes the Verification Commit field before the Plan commit — only then
    # does the failure path prove that write gets rolled back (W-03 gap).
    assert "- **Worktree**:" in plan_text

    plan = ws / COMPLETE_PLAN_REL
    plan.parent.mkdir(parents=True)
    plan.write_text(plan_text)
    _shell_git("add", COMPLETE_PLAN_REL, cwd=ws)
    _shell_git("commit", "-m", "add plan", cwd=ws)
    _shell_git("push", "-u", "origin", "main", cwd=ws)
    _shell_git("remote", "set-head", "origin", "main", cwd=ws)
    return ws, plan


def _run_complete(ws, target="106", pr=False):
    """Run cmd_complete with workspace/repo detection and Issue sync mocked."""
    from commands.complete import cmd_complete

    sync_label = MagicMock()
    sync_body = MagicMock()
    log_error = MagicMock()
    with patch.multiple(
        "commands.complete",
        find_workspace_root=MagicMock(return_value=ws),
        resolve_space_repo=MagicMock(return_value="test/space"),
        sync_status_label=sync_label,
        sync_plan_to_issue_body=sync_body,
        log_error=log_error,
    ):
        result = cmd_complete(Namespace(target=target, pr=pr))
    return result, sync_label, sync_body, log_error


class TestCompleteDurabilityGate:
    """Plan commit failure blocks Issue sync, exits non-zero, and leaves the
    Plan in a retryable state (AC#3)."""

    def test_commit_failure_blocks_sync_and_restores_plan(self, tmp_path):
        ws, plan = _make_complete_workspace(tmp_path)
        original = plan.read_text()
        _shell_install_failing_hook(ws, "injected complete-commit failure")

        result, sync_label, sync_body, log_error = _run_complete(ws)

        assert result == 1
        assert plan.read_text() == original
        assert "- **Status**: executing" in plan.read_text()
        # The Verification Commit field was written before the failed commit
        # and must be gone after the restore.
        assert "Verification Commit" not in plan.read_text()
        # No staged Plan residue: a retry sees the same clean state.
        assert _shell_git(
            "status", "--porcelain", "--", COMPLETE_PLAN_REL, cwd=ws
        ).stdout == ""
        sync_label.assert_not_called()
        sync_body.assert_not_called()
        text = "\n".join(str(c.args[0]) for c in log_error.call_args_list)
        assert "injected complete-commit failure" in text

    def test_retry_after_commit_failure_succeeds(self, tmp_path):
        ws, plan = _make_complete_workspace(tmp_path)
        hook = _shell_install_failing_hook(ws, "injected complete-commit failure")

        first, _, _, _ = _run_complete(ws)
        assert first == 1

        hook.unlink()
        second, sync_label, sync_body, _ = _run_complete(ws)

        assert second == 0
        committed = _shell_git("show", f"HEAD:{COMPLETE_PLAN_REL}", cwd=ws).stdout
        assert "- **Status**: verifying" in committed
        # The Verification Commit write also survives the successful retry.
        assert "Verification Commit" in committed
        assert _shell_git("log", "-1", "--format=%s", cwd=ws).stdout.strip() == (
            "docs(plan): complete plan #106"
        )
        assert _shell_git(
            "status", "--porcelain", "--", COMPLETE_PLAN_REL, cwd=ws
        ).stdout == ""
        sync_label.assert_called_once_with(106, "verifying", "test/space")
        sync_body.assert_called_once()

    def test_success_path_commits_verifying_and_syncs(self, tmp_path):
        ws, plan = _make_complete_workspace(tmp_path)

        result, sync_label, sync_body, _ = _run_complete(ws)

        assert result == 0
        committed = _shell_git("show", f"HEAD:{COMPLETE_PLAN_REL}", cwd=ws).stdout
        assert "- **Status**: verifying" in committed
        assert "executing" in _shell_git(
            "show", f"HEAD~1:{COMPLETE_PLAN_REL}", cwd=ws
        ).stdout
        sync_label.assert_called_once()
        sync_body.assert_called_once()

    def test_does_not_sweep_foreign_staged_files(self, tmp_path):
        """The Plan-only commit never carries unrelated staged files from the
        Plan's repo, and leaves their index state intact (B-05)."""
        ws, plan = _make_complete_workspace(tmp_path)
        (ws / "foreign.txt").write_text("foreign\n")
        _shell_git("add", "foreign.txt", cwd=ws)

        result, _, _, _ = _run_complete(ws)

        assert result == 0
        changed = _shell_git(
            "show", "HEAD", "--name-only", "--format=", cwd=ws
        ).stdout
        assert "foreign.txt" not in changed
        assert COMPLETE_PLAN_REL in changed
        # The foreign file is still staged and uncommitted.
        assert "A  foreign.txt" in _shell_git(
            "status", "--porcelain", cwd=ws
        ).stdout

    def test_reset_failure_not_reported_as_retry_ready(self, tmp_path, capsys):
        """When the index reset itself fails, the command must report the
        residual staged state instead of claiming '可直接重试' (W-01)."""
        ws, plan = _make_complete_workspace(tmp_path)
        original = plan.read_text()

        # Real injection: a held index lock makes both `git add` and the
        # recovery `git reset` fail.
        lock = ws / ".git" / "index.lock"
        lock.write_text("")
        try:
            result, _, _, log_error = _run_complete(ws)
        finally:
            lock.unlink()

        assert result == 1
        # The Plan file itself was restored.
        assert plan.read_text() == original
        # W-03: log_error is mocked by _run_complete, so its calls do not
        # appear in capsys. Include the mock's call content in the assertion
        # so a regression that re-introduces '可直接重试' is actually caught.
        log_error_text = "\n".join(
            str(c.args[0]) if c.args else str(c)
            for c in log_error.call_args_list
        )
        combined = "".join(capsys.readouterr()) + log_error_text
        assert "可直接重试" not in combined
        assert "git -C" in combined and "reset" in combined
        assert "index" in combined.lower()


if __name__ == "__main__":
    unittest.main()


class TestCompletePrCommitFailureGuidance:
    """PR path: the PR is created before the Plan commit; when that commit
    fails, the created PR identity must survive the rollback so the retry
    adopts the existing PR and verify still gates on it (B-06)."""

    PLAN_NAME = "106-fix-dev-flow-valid-issue-plan"

    def _run_complete_pr(self, ws, create_pr, target="106"):
        from commands.complete import cmd_complete

        with patch.multiple(
            "commands.complete",
            find_workspace_root=MagicMock(return_value=ws),
            resolve_space_repo=MagicMock(return_value="test/space"),
            sync_status_label=MagicMock(),
            sync_plan_to_issue_body=MagicMock(),
            _create_pr=create_pr,
            _create_pr_for_plan=create_pr,
        ):
            return cmd_complete(Namespace(target=target, pr=True))

    def _run_verify(self, ws, target="106"):
        """Run cmd_verify with the PR-merge query mocked to 'not merged'."""
        from commands.verify import cmd_verify

        is_pr_merged = MagicMock(return_value=False)
        with patch.multiple(
            "commands.verify",
            find_workspace_root=MagicMock(return_value=ws),
            resolve_space_repo=MagicMock(return_value="test/space"),
            _is_pr_merged=is_pr_merged,
            _get_pr_url_from_issue=MagicMock(return_value=""),
            _search_merged_pr_for_issue=MagicMock(return_value=False),
        ):
            result = cmd_verify(Namespace(target=target, confirm=True))
        return result, is_pr_merged

    def test_commit_failure_retains_pr_and_retry_still_gates_verify(
        self, tmp_path, capsys
    ):
        ws, plan = _make_complete_workspace(tmp_path)
        hook = _shell_install_failing_hook(ws, "injected complete-commit failure")

        pr_url = _recorded_pr_url()
        create_pr = MagicMock(return_value=pr_url)

        first = self._run_complete_pr(ws, create_pr)
        assert first == 1
        text = plan.read_text()
        # Retryable executing state, with the created PR identity retained.
        assert "- **Status**: executing" in text
        assert f"- **PR**: {pr_url}" in text
        # No staged Plan residue (the file keeps an unstaged PR edit).
        assert _shell_git(
            "diff", "--cached", "--name-only", "--", COMPLETE_PLAN_REL, cwd=ws
        ).stdout == ""
        # The guidance names the PR and the plain re-run that adopts it.
        combined = "".join(capsys.readouterr())
        assert pr_url in combined
        assert "--pr" in combined
        assert "flow.sh complete 106" in combined

        # Retry exactly per guidance: plain re-run, no --pr.
        hook.unlink()
        second = _run_complete(ws)[0]
        assert second == 0
        assert create_pr.call_count == 1, "retry must adopt the existing PR"
        committed = _shell_git("show", f"HEAD:{COMPLETE_PLAN_REL}", cwd=ws).stdout
        assert "- **Status**: verifying" in committed
        assert f"- **PR**: {pr_url}" in committed

        # verify still gates on the recovered PR identity.
        result, is_pr_merged = self._run_verify(ws)
        assert result == 1
        is_pr_merged.assert_called_once_with(pr_url)

    def test_no_issue_pr_retained_and_verify_gates_on_it(self, tmp_path):
        ws, plan = _make_complete_workspace(tmp_path, no_issue=True)
        hook = _shell_install_failing_hook(ws, "injected complete-commit failure")

        pr_url = _recorded_pr_url()
        create_pr = MagicMock(return_value=pr_url)
        target = self.PLAN_NAME

        first = self._run_complete_pr(ws, create_pr, target=target)
        assert first == 1
        assert f"- **PR**: {pr_url}" in plan.read_text()

        hook.unlink()
        second = _run_complete(ws, target=target)[0]
        assert second == 0
        committed = _shell_git("show", f"HEAD:{COMPLETE_PLAN_REL}", cwd=ws).stdout
        assert f"- **PR**: {pr_url}" in committed

        # Without the retained PR a no-Issue plan has no PR identity to check;
        # with it retained, verify blocks on the unmerged PR.
        result, is_pr_merged = self._run_verify(ws, target=target)
        assert result == 1
        is_pr_merged.assert_called_once_with(pr_url)
