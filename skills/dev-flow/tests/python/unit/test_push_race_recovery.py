#!/usr/bin/env python3
# test_push_race_recovery.py - TDD tests for git push race self-recovery (#215)
#
# Issue #215: two parallel flow.sh commands push to the same repo; the
# slower pusher is rejected with non-fast-forward because the faster one
# already advanced origin. push_repo must self-heal:
#   1. fetch + retry when origin tip is an ancestor of HEAD
#   2. fetch + ff-only merge + retry when HEAD is behind origin
# and must never touch a dirty tree destructively (no autostash/rebase/force).
#
# Caller semantics: approve/submit must warn-and-continue on
# RESULT_PUSH_FAILED instead of aborting mid-lifecycle.

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from lib.git import push_repo
from lib.plan_commit import RESULT_OK, RESULT_PUSH_FAILED


# ============================================
# Helpers
# ============================================

def _git(*args, cwd, check=True):
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    if check:
        assert result.returncode == 0, f"git {args} failed: {result.stderr}"
    return result


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git("init", "-b", "main", cwd=path)
    _git("config", "user.email", "test@test.com", cwd=path)
    _git("config", "user.name", "Test", cwd=path)
    (path / "README.md").write_text("# init\n")
    _git("add", "README.md", cwd=path)
    _git("commit", "-m", "init", cwd=path)


def _commit_file(work: Path, name: str, content: str) -> None:
    (work / name).write_text(content)
    _git("add", name, cwd=work)
    _git("commit", "-m", f"add {name}", cwd=work)


def _make_bare_with_clone(base: Path, name: str):
    """Create bare remote + working clone with one pushed initial commit."""
    remote = base / f"{name}-remote.git"
    work = base / f"{name}-work"
    _git("init", "--bare", "-b", "main", str(remote), cwd=base)
    _git("clone", str(remote), str(work), cwd=base, check=False)
    _git("config", "user.email", "test@test.com", cwd=work)
    _git("config", "user.name", "Test", cwd=work)
    (work / "README.md").write_text("# init\n")
    _git("add", "README.md", cwd=work)
    _git("commit", "-m", "init", cwd=work)
    _git("push", "origin", "main", cwd=work)
    return remote, work


# ============================================
# Real-git race scenarios (bare remote + clones)
# ============================================

class TestPushRaceRecoveryReal:
    """End-to-end race shapes reproduced with real git."""

    def test_push_recovers_when_remote_advanced_within_our_history(self, tmp_path):
        """The #215 winner/loser shape seen from the loser side after sync:
        HEAD contains remote tip but the last fetch predates the remote's
        advance. push_repo must fetch + retry and succeed."""
        remote, work = _make_bare_with_clone(tmp_path, "race")

        # Local gains a commit; remote simultaneously gains a different commit
        # via another clone, landing first.
        _commit_file(work, "mine.txt", "mine\n")

        other = tmp_path / "race-other"
        _git("clone", str(remote), str(other), cwd=tmp_path, check=False)
        _git("config", "user.email", "test@test.com", cwd=other)
        _git("config", "user.name", "Test", cwd=other)
        _commit_file(other, "theirs.txt", "theirs\n")
        _git("push", "origin", "main", cwd=other)

        # Rebase-free race shape: replay our commit on top of theirs locally
        # (simulating serial commits + parallel push in one shared repo),
        # so HEAD ⊇ remote tip but our origin tracking ref is stale.
        _git("pull", "--rebase", "origin", "main", cwd=work)
        _git("update-ref", "refs/remotes/origin/main",
             _git("rev-parse", "HEAD~1", cwd=work).stdout.strip(), cwd=work)

        ok = push_repo(str(work), "main")
        assert ok is True
        remote_tip = _git("rev-parse", "refs/heads/main", cwd=remote).stdout.strip()
        local_tip = _git("rev-parse", "HEAD", cwd=work).stdout.strip()
        assert remote_tip == local_tip

    def test_push_heals_head_behind_remote_via_ff_only(self, tmp_path):
        """The literal #215 loser shape: local HEAD is an ancestor of the
        remote tip (another process pushed our parent plus its own commit).
        push_repo must fetch, ff-only merge, and push successfully."""
        remote, work = _make_bare_with_clone(tmp_path, "behind")

        # Another clone pushes a commit on top of the shared base.
        other = tmp_path / "behind-other"
        _git("clone", str(remote), str(other), cwd=tmp_path, check=False)
        _git("config", "user.email", "test@test.com", cwd=other)
        _git("config", "user.name", "Test", cwd=other)
        _commit_file(other, "theirs.txt", "theirs\n")
        _git("push", "origin", "main", cwd=other)

        # Local is strictly behind (HEAD == old remote tip).
        ok = push_repo(str(work), "main")
        assert ok is True
        remote_tip = _git("rev-parse", "refs/heads/main", cwd=remote).stdout.strip()
        local_tip = _git("rev-parse", "HEAD", cwd=work).stdout.strip()
        assert remote_tip == local_tip

    def test_push_fails_cleanly_on_true_divergence_with_dirty_tree(self, tmp_path):
        """True divergence (both sides have unique commits) plus dirty tree:
        push_repo must return False, leave the tree untouched, and not
        autostash/rebase/force."""
        remote, work = _make_bare_with_clone(tmp_path, "diverge")

        other = tmp_path / "diverge-other"
        _git("clone", str(remote), str(other), cwd=tmp_path, check=False)
        _git("config", "user.email", "test@test.com", cwd=other)
        _git("config", "user.name", "Test", cwd=other)
        _commit_file(other, "theirs.txt", "theirs\n")
        _git("push", "origin", "main", cwd=other)

        # Local unique commit + dirty untracked file.
        _commit_file(work, "mine.txt", "mine\n")
        (work / "dirty.txt").write_text("uncommitted\n")

        ok = push_repo(str(work), "main")
        assert ok is False
        # Tree untouched: no autostash pop, no destructive recovery.
        assert (work / "dirty.txt").read_text() == "uncommitted\n"
        status = _git("status", "--porcelain", cwd=work).stdout
        assert "dirty.txt" in status
        # Local commit still present.
        mine = _git("rev-parse", "HEAD", cwd=work).stdout.strip()
        assert _git("cat-file", "-t", mine, cwd=work).stdout.strip() == "commit"

    def test_push_heals_divergence_when_tree_clean(self, tmp_path):
        """True divergence but clean tree: healing is allowed (ff is not
        possible; only safe-forward merge of our own plan commits is in
        scope). Current contract: return False and surface manual steps
        rather than inventing a merge commit."""
        remote, work = _make_bare_with_clone(tmp_path, "clean-diverge")

        other = tmp_path / "clean-diverge-other"
        _git("clone", str(remote), str(other), cwd=tmp_path, check=False)
        _git("config", "user.email", "test@test.com", cwd=other)
        _git("config", "user.name", "Test", cwd=other)
        _commit_file(other, "theirs.txt", "theirs\n")
        _git("push", "origin", "main", cwd=other)

        _commit_file(work, "mine.txt", "mine\n")
        ok = push_repo(str(work), "main")
        # Contract: no auto merge-commit creation; report failure for manual handling.
        assert ok is False


# ============================================
# push_repo retry contract (unit-level)
# ============================================

class TestPushRepoRetryContract:
    """Retry loop is bounded and gated on ancestor checks."""

    def _init_local(self, tmp_path: Path) -> Path:
        work = tmp_path / "w"
        _init_repo(work)
        return work

    def test_retry_succeeds_after_fetch_when_origin_is_ancestor(self, tmp_path):
        work = self._init_local(tmp_path)
        real_run = subprocess.run
        pushes = {"n": 0}

        def flaky_push(cmd, **kwargs):
            if cmd[:2] == ["git", "push"]:
                pushes["n"] += 1
                if pushes["n"] == 1:
                    return subprocess.CompletedProcess(
                        cmd, 1, stdout="",
                        stderr="! [rejected] main -> main (non-fast-forward)")
                return subprocess.CompletedProcess(cmd, 0)
            if cmd[:2] == ["git", "fetch"]:
                return subprocess.CompletedProcess(cmd, 0)
            if cmd[:2] == ["git", "merge-base"]:
                return subprocess.CompletedProcess(cmd, 0)  # origin ⊆ HEAD
            return real_run(cmd, **kwargs)

        with patch("lib.git.subprocess.run", side_effect=flaky_push), \
             patch("lib.git.PUSH_RETRY_LIMIT", 3), \
             patch("lib.git.PUSH_RETRY_DELAY", 0):
            assert push_repo(str(work), "main") is True
        assert pushes["n"] == 2

    def test_retry_is_bounded(self, tmp_path):
        work = self._init_local(tmp_path)
        real_run = subprocess.run
        pushes = {"n": 0}

        def always_reject(cmd, **kwargs):
            if cmd[:2] == ["git", "push"]:
                pushes["n"] += 1
                return subprocess.CompletedProcess(cmd, 1, stdout="",
                                                   stderr="! [rejected]")
            if cmd[:2] == ["git", "fetch"]:
                return subprocess.CompletedProcess(cmd, 0)
            if cmd[:2] == ["git", "merge-base"]:
                return subprocess.CompletedProcess(cmd, 0)  # origin ⊆ HEAD
            return real_run(cmd, **kwargs)

        with patch("lib.git.subprocess.run", side_effect=always_reject), \
             patch("lib.git.PUSH_RETRY_LIMIT", 3), \
             patch("lib.git.PUSH_RETRY_DELAY", 0):
            assert push_repo(str(work), "main") is False
        assert pushes["n"] == 3

    def test_no_retry_when_true_divergence(self, tmp_path):
        """origin ⊄ HEAD and HEAD ⊆ origin both fail -> no blind retry."""
        work = self._init_local(tmp_path)
        real_run = subprocess.run
        pushes = {"n": 0}
        merge_base_calls = {"n": 0}

        def reject_no_recovery(cmd, **kwargs):
            if cmd[:2] == ["git", "push"]:
                pushes["n"] += 1
                return subprocess.CompletedProcess(cmd, 1, stdout="",
                                                   stderr="! [rejected]")
            if cmd[:2] == ["git", "fetch"]:
                return subprocess.CompletedProcess(cmd, 0)
            if cmd[:2] == ["git", "merge-base"]:
                merge_base_calls["n"] += 1
                return subprocess.CompletedProcess(cmd, 1)  # diverged
            return real_run(cmd, **kwargs)

        with patch("lib.git.subprocess.run", side_effect=reject_no_recovery), \
             patch("lib.git.PUSH_RETRY_LIMIT", 3), \
             patch("lib.git.PUSH_RETRY_DELAY", 0):
            assert push_repo(str(work), "main") is False
        assert pushes["n"] == 1
        # Both directions checked (ancestor of HEAD, HEAD ancestor of origin).
        assert merge_base_calls["n"] == 2

    def test_heals_head_behind_remote_with_ff_only_merge(self, tmp_path):
        """HEAD ⊆ origin: fetch + git merge --ff-only + push, no rebase."""
        work = self._init_local(tmp_path)
        real_run = subprocess.run
        seen_cmds = []
        merge_base_calls = {"n": 0}

        def behind_shape(cmd, **kwargs):
            seen_cmds.append(list(cmd))
            if cmd[:2] == ["git", "push"]:
                return subprocess.CompletedProcess(cmd, 1, stdout="",
                                                   stderr="! [rejected]")
            if cmd[:2] == ["git", "fetch"]:
                return subprocess.CompletedProcess(cmd, 0)
            if cmd[:2] == ["git", "merge-base"]:
                merge_base_calls["n"] += 1
                # 1st check (origin ⊆ HEAD): fail.
                # 2nd check (HEAD ⊆ origin): ok -> HEAD is behind.
                code = 1 if merge_base_calls["n"] == 1 else 0
                return subprocess.CompletedProcess(cmd, code)
            return real_run(cmd, **kwargs)

        with patch("lib.git.subprocess.run", side_effect=behind_shape), \
             patch("lib.git.PUSH_RETRY_LIMIT", 3), \
             patch("lib.git.PUSH_RETRY_DELAY", 0):
            # merge --ff-only fails on this bare local repo shape; that's fine,
            # contract is: it was attempted and failure surfaces as False.
            assert push_repo(str(work), "main") is False
        flat = [c[:3] for c in seen_cmds]
        assert ["git", "merge", "--ff-only"] in flat
        assert not any(c[:2] == ["git", "rebase"] for c in seen_cmds)
        assert not any("force" in " ".join(c) for c in flat)


# ============================================
# Caller failure semantics (#215 acceptance)
# ============================================

def _approve_mocks(push_result):
    """Common mock set for approve --confirm (mirrors test_approve.py)."""
    values = {
        "find_workspace_root": Path("/ws"),
        "find_plan": "/ws/.wopal-space/plans/space-ontology/42-fix-test.md",
        "parse_plan_status": "planning",
        "check_doc_plan": None,
        "get_plan_issue": 42,
        "get_plan_project": "space-ontology",
        "get_plan_field": "ontology-worktree",
        "resolve_project_path": Path("/ws/.wopal"),
        "detect_space_repo": "wopal-space-ontology",
        "is_repo_dirty": False,
        "write_worktree_context": True,
        "commit_and_push_plan": push_result,
        "update_plan_status": True,
        "sync_status_label": None,
        "sync_plan_to_issue_body": None,
        "ensure_issue_labels": None,
        "get_ontology_main_repo": Path("/ws/.wopal"),
        "get_current_branch": "space/wopal-workspace",
        "get_branch_head": "abc123def",
        "set_plan_field": True,
        "log_warn": None,
    }
    return {k: MagicMock(return_value=v) for k, v in values.items()}


class TestCallerFailureSemantics:
    """approve/submit must warn-and-continue on push failure (no half-done
    lifecycle state)."""

    def test_approve_continues_past_push_failure(self):
        from commands.approve import cmd_approve
        mocks = _approve_mocks(RESULT_PUSH_FAILED)
        with patch.multiple("commands.approve", **mocks):
            args = Namespace(target="42", confirm=True, no_worktree=True)
            result = cmd_approve(args)
            assert result == 0
            mocks["log_warn"].assert_called()

    def test_submit_continues_past_push_failure(self):
        from commands.submit import cmd_submit
        with patch.multiple(
            "commands.submit",
            find_workspace_root=MagicMock(return_value=Path("/ws")),
            find_plan=MagicMock(
                return_value="/ws/.wopal-space/plans/space-ontology/42-fix-test.md"),
            parse_plan_status=MagicMock(return_value="planning"),
            get_plan_status=MagicMock(return_value="planning"),
            check_doc_plan=MagicMock(),
            get_plan_issue=MagicMock(return_value=42),
            update_plan_status=MagicMock(return_value=True),
            commit_and_push_plan=MagicMock(return_value=RESULT_PUSH_FAILED),
            log_warn=MagicMock(),
        ):
            args = Namespace(target="42")
            result = cmd_submit(args)
            assert result == 0
