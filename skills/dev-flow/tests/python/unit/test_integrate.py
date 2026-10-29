#!/usr/bin/env python3
"""Behavior tests for formal Delivery integration."""

from __future__ import annotations

import sys
import os
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
from support.git_fixtures import init_repo, install_failing_hook, shell_git

ensure_scripts_path()


def _commit_file(repo: Path, name: str, text: str, subject: str) -> str:
    (repo / name).write_text(text)
    shell_git("add", name, cwd=repo)
    shell_git("commit", "-m", subject, cwd=repo)
    return shell_git("rev-parse", "HEAD", cwd=repo).stdout.strip()


@pytest.mark.parametrize("main_advanced", [False, True])
def test_squash_delivery_adds_one_formal_commit_and_keeps_work_history(tmp_path, main_advanced):
    """Default integration is one exact-subject commit even when main advanced."""
    from commands.integrate import integrate_local_delivery

    repo = tmp_path / "repo"
    init_repo(repo)
    base = shell_git("rev-parse", "HEAD", cwd=repo).stdout.strip()

    shell_git("checkout", "-b", "work-delivery", cwd=repo)
    work_commits = [
        _commit_file(repo, "one.txt", "one\n", "work one"),
        _commit_file(repo, "two.txt", "two\n", "review fix"),
        _commit_file(repo, "three.txt", "three\n", "validation fix"),
    ]
    work_tip = work_commits[-1]

    shell_git("checkout", "main", cwd=repo)
    if main_advanced:
        _commit_file(repo, "parallel.txt", "parallel\n", "parallel main work")
    main_before = shell_git("rev-parse", "HEAD", cwd=repo).stdout.strip()

    subject = "feat(delivery): preserve exact formal subject"
    integrated = integrate_local_delivery(
        repo,
        integration_branch="main",
        work_branch="work-delivery",
        delivery_base=base,
        strategy="squash",
        commit_subject=subject,
    )

    assert integrated == shell_git("rev-parse", "main", cwd=repo).stdout.strip()
    assert shell_git("log", "-1", "--format=%s", "main", cwd=repo).stdout.strip() == subject
    assert int(shell_git("rev-list", "--count", f"{main_before}..main", cwd=repo).stdout) == 1
    assert shell_git("rev-parse", "work-delivery", cwd=repo).stdout.strip() == work_tip
    for commit in work_commits:
        assert shell_git(
            "merge-base", "--is-ancestor", commit, "main", cwd=repo, check=False
        ).returncode != 0


def test_preserve_history_is_explicit_and_keeps_work_commits(tmp_path):
    """preserve-history keeps development commits and uses the exact merge subject."""
    from commands.integrate import integrate_local_delivery

    repo = tmp_path / "repo"
    init_repo(repo)
    base = shell_git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    shell_git("checkout", "-b", "work-delivery", cwd=repo)
    work_commit = _commit_file(repo, "work.txt", "work\n", "work detail")
    shell_git("checkout", "main", cwd=repo)

    subject = "refactor(delivery): retain development history"
    integrated = integrate_local_delivery(
        repo,
        integration_branch="main",
        work_branch="work-delivery",
        delivery_base=base,
        strategy="preserve-history",
        commit_subject=subject,
    )

    assert integrated == shell_git("rev-parse", "main", cwd=repo).stdout.strip()
    assert shell_git("log", "-1", "--format=%s", "main", cwd=repo).stdout.strip() == subject
    assert shell_git(
        "merge-base", "--is-ancestor", work_commit, "main", cwd=repo, check=False
    ).returncode == 0


def test_formal_subject_is_required_and_never_generated(tmp_path):
    """Formal integration refuses an empty subject instead of synthesizing one."""
    from commands.integrate import integrate_local_delivery

    repo = tmp_path / "repo"
    init_repo(repo)
    base = shell_git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    shell_git("checkout", "-b", "work-delivery", cwd=repo)
    _commit_file(repo, "work.txt", "work\n", "work detail")
    shell_git("checkout", "main", cwd=repo)

    with pytest.raises(ValueError, match="Commit Subject"):
        integrate_local_delivery(
            repo,
            integration_branch="main",
            work_branch="work-delivery",
            delivery_base=base,
            strategy="squash",
            commit_subject="",
        )


def test_pr_delivery_uses_exact_approved_subject(tmp_path, monkeypatch):
    """PR delivery produces the same exact formal subject as local delivery."""
    from commands.integrate import integrate_pr_delivery

    repo = tmp_path / "repo"
    init_repo(repo)
    bare = tmp_path / "origin.git"
    shell_git("init", "--bare", "-b", "main", str(bare), cwd=tmp_path)
    shell_git("remote", "add", "origin", str(bare), cwd=repo)
    shell_git("push", "-u", "origin", "main", cwd=repo)

    shell_git("checkout", "-b", "work-delivery", cwd=repo)
    work_commit = _commit_file(repo, "work.txt", "work\n", "work detail")
    shell_git("push", "-u", "origin", "work-delivery", cwd=repo)
    shell_git("checkout", "main", cwd=repo)

    server = tmp_path / "server"
    shell_git("clone", str(bare), str(server), cwd=tmp_path)
    shell_git("config", "user.email", "test@test.com", cwd=server)
    shell_git("config", "user.name", "Test", cwd=server)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        "subject=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = '--subject' ]; then shift; subject=$1; fi\n"
        "  shift\n"
        "done\n"
        "cd \"$FAKE_SERVER\" || exit 1\n"
        "git fetch origin || exit 1\n"
        "git checkout main >/dev/null 2>&1 || exit 1\n"
        "git reset --hard origin/main >/dev/null || exit 1\n"
        "git merge --squash origin/$FAKE_WORK_BRANCH >/dev/null || exit 1\n"
        "git commit -m \"$subject\" >/dev/null || exit 1\n"
        "git push origin main >/dev/null || exit 1\n"
    )
    fake_gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_SERVER", str(server))
    monkeypatch.setenv("FAKE_WORK_BRANCH", "work-delivery")

    subject = "feat(delivery): exact approved pr subject"
    integrated = integrate_pr_delivery(
        repo,
        pr_url="https://github.com/example/repo/pull/1",
        integration_branch="main",
        strategy="squash",
        commit_subject=subject,
    )

    assert integrated == shell_git("rev-parse", "main", cwd=repo).stdout.strip()
    assert shell_git("log", "-1", "--format=%s", "main", cwd=repo).stdout.strip() == subject
    assert shell_git(
        "merge-base", "--is-ancestor", work_commit, "main", cwd=repo, check=False
    ).returncode != 0


def _write_delivery_plan(
    path: Path,
    *,
    name: str,
    base: str,
    subject: str = "feat(delivery): exact approved subject",
    delivery: str | None = None,
    status: str = "verifying",
) -> Path:
    plan = path / f"{name}.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        f"# {name}\n\n"
        "## Metadata\n\n"
        "- **Issue**: N/A\n"
        "- **Type**: feature\n"
        "- **Target Project**: demo\n"
        "- **Project Path**: projects/demo\n"
        f"- **Status**: {status}\n"
        f"- **Delivery**: {delivery or name}\n"
        f"- **Commit Subject**: {subject}\n"
        "- **Integration Strategy**: squash\n"
        "- **Integration Branch**: main\n"
        "- **Work Branch**: work-delivery\n"
        f"- **Delivery Base Commit**: {base}\n"
        "- **Verification Commit**: (none)\n"
        "- **Integration Commit**: (none)\n"
        "- **Worktree**:\n"
        "  - branch: work-delivery\n"
        "  - path: .worktrees/demo-delivery\n\n"
        "## Goal\n\nTest delivery.\n"
    )
    return plan


def _make_command_workspace(tmp_path: Path):
    ws = tmp_path / "ws"
    init_repo(ws)
    project = ws / "projects" / "demo"
    init_repo(project)
    base = shell_git("rev-parse", "HEAD", cwd=project).stdout.strip()
    shell_git("checkout", "-b", "work-delivery", cwd=project)
    _commit_file(project, "one.txt", "one\n", "work one")
    _commit_file(project, "two.txt", "two\n", "work two")
    work_tip = shell_git("rev-parse", "HEAD", cwd=project).stdout.strip()
    shell_git("checkout", "main", cwd=project)
    return ws, project, base, work_tip


def _make_real_worktree_workspace(tmp_path: Path):
    """Workspace whose feature branch is checked out in a registered worktree."""
    ws = tmp_path / "ws"
    init_repo(ws)
    project = ws / "projects" / "demo"
    init_repo(project)
    base = shell_git("rev-parse", "HEAD", cwd=project).stdout.strip()
    worktree = ws / ".worktrees" / "demo-delivery"
    worktree.parent.mkdir(parents=True)
    shell_git(
        "worktree", "add", "-b", "work-delivery", str(worktree),
        cwd=project,
    )
    _commit_file(worktree, "one.txt", "one\n", "work one")
    work_tip = _commit_file(worktree, "two.txt", "two\n", "work two")
    return ws, project, worktree, base, work_tip


def _install_fake_pr_merger(tmp_path: Path, project: Path, monkeypatch) -> Path:
    """Install a local origin plus fake gh that squash-merges the work branch."""
    bare = tmp_path / "origin.git"
    shell_git("init", "--bare", "-b", "main", str(bare), cwd=tmp_path)
    shell_git("remote", "add", "origin", str(bare), cwd=project)
    shell_git("push", "-u", "origin", "main", cwd=project)
    shell_git("push", "-u", "origin", "work-delivery", cwd=project)

    server = tmp_path / "server"
    shell_git("clone", str(bare), str(server), cwd=tmp_path)
    shell_git("config", "user.email", "test@test.com", cwd=server)
    shell_git("config", "user.name", "Test", cwd=server)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        "subject=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = '--subject' ]; then shift; subject=$1; fi\n"
        "  shift\n"
        "done\n"
        "cd \"$FAKE_SERVER\" || exit 1\n"
        "git fetch origin || exit 1\n"
        "git checkout main >/dev/null 2>&1 || exit 1\n"
        "git reset --hard origin/main >/dev/null || exit 1\n"
        "git merge --squash origin/work-delivery >/dev/null || exit 1\n"
        "git commit -m \"$subject\" >/dev/null || exit 1\n"
        "git push origin main >/dev/null || exit 1\n"
    )
    fake_gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_SERVER", str(server))
    return bare


def test_integrate_command_records_verified_and_formal_commits(tmp_path):
    """Command integrates once and records both commit identities in the Plan."""
    from commands.integrate import cmd_integrate

    ws, project, base, work_tip = _make_command_workspace(tmp_path)
    plan = _write_delivery_plan(
        ws / ".wopal-space" / "plans" / "demo",
        name="feature-delivery",
        base=base,
    )
    shell_git("add", str(plan.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add plan", cwd=ws)

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        result = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    assert result == 0
    integration_commit = shell_git("rev-parse", "main", cwd=project).stdout.strip()
    text = plan.read_text()
    assert f"- **Verification Commit**: {work_tip}" in text
    assert f"- **Integration Commit**: {integration_commit}" in text
    assert shell_git("log", "-1", "--format=%s", cwd=project).stdout.strip() == (
        "feat(delivery): exact approved subject"
    )


def test_integrate_rejects_dirty_registered_worktree_before_formal_mutation(tmp_path):
    """Uncommitted worktree changes cannot be omitted from a formal Delivery."""
    from commands.integrate import cmd_integrate

    ws, project, worktree, base, _ = _make_real_worktree_workspace(tmp_path)
    plan = _write_delivery_plan(
        ws / ".wopal-space" / "plans" / "demo",
        name="feature-delivery",
        base=base,
    )
    shell_git("add", str(plan.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add plan", cwd=ws)
    main_before = shell_git("rev-parse", "main", cwd=project).stdout.strip()

    (worktree / "dirty-fix.txt").write_text("not committed\n")

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        result = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    assert result == 1
    assert shell_git("rev-parse", "main", cwd=project).stdout.strip() == main_before
    text = plan.read_text()
    assert "- **Verification Commit**: (none)" in text
    assert "- **Integration Commit**: (none)" in text


def test_integrate_rejects_shared_delivery_subject_mismatch_before_git_mutation(tmp_path):
    """Every member of one Delivery must carry the owner's exact subject."""
    from commands.integrate import cmd_integrate

    ws, project, base, _ = _make_command_workspace(tmp_path)
    plans = ws / ".wopal-space" / "plans" / "demo"
    owner = _write_delivery_plan(plans, name="feature-owner", base=base)
    member = _write_delivery_plan(
        plans,
        name="feature-member",
        base=base,
        delivery="feature-owner",
        subject="feat(delivery): different subject",
    )
    shell_git("add", str(owner.relative_to(ws)), str(member.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add shared plans", cwd=ws)
    main_before = shell_git("rev-parse", "main", cwd=project).stdout.strip()

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(member)
    ):
        result = cmd_integrate(Namespace(target="feature-member", confirm=True))

    assert result == 1
    assert shell_git("rev-parse", "main", cwd=project).stdout.strip() == main_before


def test_shared_delivery_integrates_once_and_shares_owner_commit(tmp_path):
    """Any member may trigger one integration; owner stores the formal commit."""
    from commands.integrate import cmd_integrate

    ws, project, base, work_tip = _make_command_workspace(tmp_path)
    plans = ws / ".wopal-space" / "plans" / "demo"
    owner = _write_delivery_plan(plans, name="feature-owner", base=base)
    member = _write_delivery_plan(
        plans,
        name="feature-member",
        base=base,
        delivery="feature-owner",
    )
    shell_git("add", str(owner.relative_to(ws)), str(member.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add shared plans", cwd=ws)
    main_before = shell_git("rev-parse", "main", cwd=project).stdout.strip()

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(member)
    ):
        result = cmd_integrate(Namespace(target="feature-member", confirm=True))

    assert result == 0
    integration_commit = shell_git("rev-parse", "main", cwd=project).stdout.strip()
    assert integration_commit != main_before
    assert int(shell_git("rev-list", "--count", f"{main_before}..main", cwd=project).stdout) == 1
    assert f"- **Verification Commit**: {work_tip}" in owner.read_text()
    assert f"- **Verification Commit**: {work_tip}" in member.read_text()
    assert f"- **Integration Commit**: {integration_commit}" in owner.read_text()
    assert "- **Integration Commit**: (none)" in member.read_text()


def test_shared_delivery_uses_member_pr_as_the_single_formal_path(
    tmp_path, monkeypatch
):
    """A PR recorded by any Delivery member governs integration for the group."""
    from commands.integrate import cmd_integrate

    ws, project, base, _ = _make_command_workspace(tmp_path)
    bare = _install_fake_pr_merger(tmp_path, project, monkeypatch)
    plans = ws / ".wopal-space" / "plans" / "demo"
    owner = _write_delivery_plan(plans, name="feature-owner", base=base)
    member = _write_delivery_plan(
        plans,
        name="feature-member",
        base=base,
        delivery="feature-owner",
    )
    pr_url = "https://github.com/example/repo/pull/7"
    from plan import set_plan_field
    assert set_plan_field(str(member), "PR", pr_url)
    shell_git("add", str(owner.relative_to(ws)), str(member.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add shared plans", cwd=ws)
    remote_before = shell_git("rev-parse", "main", cwd=bare).stdout.strip()

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(member)
    ):
        result = cmd_integrate(Namespace(target="feature-member", confirm=True))

    assert result == 0
    local_main = shell_git("rev-parse", "main", cwd=project).stdout.strip()
    remote_main = shell_git("rev-parse", "main", cwd=bare).stdout.strip()
    assert remote_main != remote_before
    assert remote_main == local_main
    assert f"- **PR**: {pr_url}" in owner.read_text()
    assert f"- **PR**: {pr_url}" in member.read_text()


def test_shared_delivery_rejects_conflicting_pr_identities(tmp_path, capsys):
    """One Delivery cannot carry two competing PR identities."""
    from commands.integrate import cmd_integrate
    from plan import set_plan_field

    ws, project, base, _ = _make_command_workspace(tmp_path)
    plans = ws / ".wopal-space" / "plans" / "demo"
    owner = _write_delivery_plan(plans, name="feature-owner", base=base)
    member = _write_delivery_plan(
        plans,
        name="feature-member",
        base=base,
        delivery="feature-owner",
    )
    assert set_plan_field(str(owner), "PR", "https://github.com/example/repo/pull/7")
    assert set_plan_field(str(member), "PR", "https://github.com/example/repo/pull/8")
    shell_git("add", str(owner.relative_to(ws)), str(member.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add conflicting pr plans", cwd=ws)
    main_before = shell_git("rev-parse", "main", cwd=project).stdout.strip()

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(member)
    ):
        result = cmd_integrate(Namespace(target="feature-member", confirm=True))

    assert result == 1
    assert shell_git("rev-parse", "main", cwd=project).stdout.strip() == main_before
    out, err = capsys.readouterr()
    assert "different PR URLs" in (out + err)


def test_retry_after_plan_record_commit_failure_does_not_integrate_twice(tmp_path):
    """A failed Plan-record commit retries the record, not the formal squash."""
    from commands.integrate import cmd_integrate

    ws, project, base, _ = _make_command_workspace(tmp_path)
    plan = _write_delivery_plan(
        ws / ".wopal-space" / "plans" / "demo",
        name="feature-delivery",
        base=base,
    )
    shell_git("add", str(plan.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add plan", cwd=ws)
    main_before = shell_git("rev-parse", "main", cwd=project).stdout.strip()
    hook = install_failing_hook(ws, "injected delivery-record failure")

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        first = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    assert first == 1
    main_after_first = shell_git("rev-parse", "main", cwd=project).stdout.strip()
    assert main_after_first != main_before
    assert int(shell_git("rev-list", "--count", f"{main_before}..main", cwd=project).stdout) == 1
    assert f"- **Integration Commit**: {main_after_first}" in plan.read_text()

    hook.unlink()
    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        second = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    assert second == 0
    assert shell_git("rev-parse", "main", cwd=project).stdout.strip() == main_after_first
    assert int(shell_git("rev-list", "--count", f"{main_before}..main", cwd=project).stdout) == 1
    committed = shell_git(
        "show", f"HEAD:{plan.relative_to(ws)}", cwd=ws
    ).stdout
    assert f"- **Integration Commit**: {main_after_first}" in committed


def test_plan_record_status_failure_is_not_reported_as_durable_success(tmp_path):
    """A failed Plan status query aborts durability and retries without re-integrating."""
    from commands.integrate import cmd_integrate

    ws, project, base, _ = _make_command_workspace(tmp_path)
    plan = _write_delivery_plan(
        ws / ".wopal-space" / "plans" / "demo",
        name="feature-delivery",
        base=base,
    )
    shell_git("add", str(plan.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add plan", cwd=ws)
    main_before = shell_git("rev-parse", "main", cwd=project).stdout.strip()

    # Corrupt the Plan repo index after the baseline commit. Project Git stays
    # healthy, so formal integration succeeds before Plan-record durability is
    # queried, reproducing the review finding with real Git failure output.
    index = ws / ".git" / "index"
    index_bytes = index.read_bytes()
    index.write_bytes(b"not-a-git-index\n")

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        first = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    main_after_first = shell_git("rev-parse", "main", cwd=project).stdout.strip()
    assert first == 1
    assert main_after_first != main_before
    assert int(shell_git("rev-list", "--count", f"{main_before}..main", cwd=project).stdout) == 1
    assert f"- **Integration Commit**: {main_after_first}" in plan.read_text()
    committed_before_retry = shell_git(
        "show", f"HEAD:{plan.relative_to(ws)}", cwd=ws
    ).stdout
    assert f"- **Integration Commit**: {main_after_first}" not in committed_before_retry

    # Restore the index and retry. The already-recorded metadata must be
    # committed without generating a second formal Delivery commit.
    index.write_bytes(index_bytes)
    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        second = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    assert second == 0
    assert shell_git("rev-parse", "main", cwd=project).stdout.strip() == main_after_first
    assert int(shell_git("rev-list", "--count", f"{main_before}..main", cwd=project).stdout) == 1
    committed_after_retry = shell_git(
        "show", f"HEAD:{plan.relative_to(ws)}", cwd=ws
    ).stdout
    assert f"- **Integration Commit**: {main_after_first}" in committed_after_retry


def test_retry_rejects_work_branch_drift_after_formal_integration(tmp_path):
    """A completed Delivery cannot silently absorb later work-branch commits."""
    from commands.integrate import cmd_integrate

    ws, project, worktree, base, _ = _make_real_worktree_workspace(tmp_path)
    plan = _write_delivery_plan(
        ws / ".wopal-space" / "plans" / "demo",
        name="feature-delivery",
        base=base,
    )
    shell_git("add", str(plan.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add plan", cwd=ws)

    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        first = cmd_integrate(Namespace(target="feature-delivery", confirm=True))
    assert first == 0
    formal_commit = shell_git("rev-parse", "main", cwd=project).stdout.strip()

    _commit_file(worktree, "late.txt", "late\n", "late work")
    with patch("commands.integrate.find_workspace_root", return_value=ws), patch(
        "commands.integrate.find_plan", return_value=str(plan)
    ):
        second = cmd_integrate(Namespace(target="feature-delivery", confirm=True))

    assert second == 1
    assert shell_git("rev-parse", "main", cwd=project).stdout.strip() == formal_commit
