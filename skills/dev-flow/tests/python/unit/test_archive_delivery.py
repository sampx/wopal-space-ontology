#!/usr/bin/env python3
"""Real-git regression for shared Delivery archive cleanup ownership."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
from support.git_fixtures import init_repo, shell_git

ensure_scripts_path()


def _write_plan(path: Path, name: str, delivery: str, wt_rel: str) -> Path:
    plan = path / f"{name}.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        f"# {name}\n\n## Metadata\n\n"
        "- **Issue**: N/A\n"
        "- **Type**: feature\n"
        "- **Target Project**: demo\n"
        "- **Project Path**: projects/demo\n"
        "- **Product**:\n"
        "- **Phase**:\n"
        "- **Status**: done\n"
        f"- **Delivery**: {delivery}\n"
        "- **Integration Commit**: formal123\n"
        "- **Worktree**:\n"
        "  - branch: work-delivery\n"
        f"  - path: {wt_rel}\n\n"
        "## Goal\n\nArchive delivery.\n"
    )
    return plan


def test_shared_delivery_cleans_worktree_only_when_owner_archives_last(tmp_path):
    from commands.archive import cmd_archive

    ws = tmp_path / "ws"
    init_repo(ws)
    origin = tmp_path / "space-origin.git"
    shell_git("init", "--bare", "-b", "main", str(origin), cwd=tmp_path)
    shell_git("remote", "add", "origin", str(origin), cwd=ws)

    project = ws / "projects" / "demo"
    init_repo(project)
    wt_rel = ".worktrees/demo-delivery"
    wt = ws / wt_rel
    wt.parent.mkdir(parents=True, exist_ok=True)
    shell_git("worktree", "add", "-b", "work-delivery", str(wt), cwd=project)
    (wt / "work.txt").write_text("delivery\n")
    shell_git("add", "work.txt", cwd=wt)
    shell_git("commit", "-m", "work detail", cwd=wt)
    shell_git("merge", "--squash", "work-delivery", cwd=project)
    shell_git("commit", "-m", "feat(delivery): formal", cwd=project)

    plans = ws / ".wopal-space" / "plans" / "demo"
    owner_name = "feature-owner"
    owner = _write_plan(plans, owner_name, owner_name, wt_rel)
    member = _write_plan(plans, "feature-member", owner_name, wt_rel)
    shell_git("add", str(owner.relative_to(ws)), str(member.relative_to(ws)), cwd=ws)
    shell_git("commit", "-m", "add shared delivery plans", cwd=ws)
    shell_git("push", "-u", "origin", "main", cwd=ws)

    with patch("commands.archive.find_workspace_root", return_value=ws), patch(
        "commands.archive.find_plan", return_value=str(member)
    ), patch("commands.archive.resolve_space_repo", return_value=None):
        member_result = cmd_archive(
            Namespace(target="feature-member", force=False, keep_worktree=True)
        )

    assert member_result == 0
    assert wt.exists()
    assert shell_git(
        "rev-parse", "--verify", "refs/heads/work-delivery", cwd=project, check=False
    ).returncode == 0

    with patch("commands.archive.find_workspace_root", return_value=ws), patch(
        "commands.archive.find_plan", return_value=str(owner)
    ), patch("commands.archive.resolve_space_repo", return_value=None):
        owner_result = cmd_archive(
            Namespace(target=owner_name, force=False, keep_worktree=False)
        )

    assert owner_result == 0
    assert not wt.exists()
    assert shell_git(
        "rev-parse", "--verify", "refs/heads/work-delivery", cwd=project, check=False
    ).returncode != 0

