"""Real-Git regressions for archive worktree cleanup safety."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
from support.git_fixtures import init_repo, shell_git

ensure_scripts_path()

from commands.archive import _cleanup_worktree
from lib.worktree import clean_worktree


@pytest.mark.parametrize("change", ["staged", "unstaged", "untracked"])
def test_archive_cleanup_never_discards_local_file_work(tmp_path, change):
    project = tmp_path / "project"
    init_repo(project)
    wt = tmp_path / ".worktrees" / "project-feature"
    wt.parent.mkdir()
    shell_git("worktree", "add", "-b", "feature", str(wt), cwd=project)

    if change == "untracked":
        file = wt / "new-file.txt"
    else:
        file = wt / "README.md"
    file.write_text("unsaved work\n")
    if change == "staged":
        shell_git("add", "README.md", cwd=wt)

    result = clean_worktree(project, "feature", wt.parent)

    assert result["removed"] is False
    assert result["branch_status"] == "skipped"
    assert file.read_text() == "unsaved work\n"
    assert shell_git("branch", "--list", "feature", cwd=project).stdout.strip()


@pytest.mark.parametrize("published_in_main", [True, False])
def test_archive_cleanup_checks_pinned_submodule_recoverability(
    tmp_path, published_in_main,
):
    source = tmp_path / "upstream"
    init_repo(source)
    shell_git("checkout", "-b", "wopal", cwd=source)
    (source / "fork.txt").write_text("committed fork\n")
    shell_git("add", "fork.txt", cwd=source)
    shell_git("commit", "-m", "fork", cwd=source)
    pinned = shell_git("rev-parse", "HEAD", cwd=source).stdout.strip()
    shell_git("checkout", "main", cwd=source)

    project = tmp_path / "project"
    init_repo(project)
    child_path = "third_party/CLIProxyAPI"
    main_child = project / child_path
    main_child.parent.mkdir(parents=True)
    shell_git("clone", str(source), str(main_child), cwd=tmp_path)
    shell_git("checkout", "--detach", pinned, cwd=main_child)
    (project / ".gitmodules").write_text(
        f'[submodule "third_party/CLIProxyAPI"]\n'
        f'\tpath = {child_path}\n'
        f'\turl = {source}\n'
    )
    shell_git("add", ".gitmodules", child_path, cwd=project)
    shell_git("commit", "-m", "pin fork", cwd=project)

    wt = tmp_path / ".worktrees" / "project-feature"
    wt.parent.mkdir()
    shell_git("worktree", "add", "-b", "feature", str(wt), cwd=project)
    child = wt / child_path
    child.parent.mkdir(parents=True, exist_ok=True)
    shell_git("clone", "--depth", "1", "--single-branch", "-b", "wopal",
              f"file://{source}", str(child), cwd=tmp_path)
    shell_git("checkout", "--detach", "HEAD", cwd=child)
    shell_git("update-ref", "-d", "refs/remotes/origin/wopal", cwd=child)
    assert shell_git("branch", "-r", "--contains", pinned, cwd=child).stdout.strip() == ""
    assert shell_git("branch", "-r", "--contains", pinned, cwd=main_child).stdout.strip()
    if not published_in_main:
        shell_git("update-ref", "-d", "refs/remotes/origin/wopal", cwd=main_child)
    assert shell_git("status", "--porcelain", cwd=wt).stdout.strip() == ""

    result = clean_worktree(project, "feature", wt.parent)

    assert result["removed"] is published_in_main, result["errors"]
    assert wt.exists() is not published_in_main
    assert main_child.exists()  # The primary checkout is never removed.


def test_incomplete_cleanup_reports_retained_branch_not_wrong_checkout(tmp_path, capsys):
    with patch("commands.archive.clean_worktree", return_value={
        "removed": False, "branch_deleted": False,
        "branch_status": "skipped", "errors": ["unsaved data"],
    }):
        success = _cleanup_worktree(
            str(tmp_path / "project"), "feature", str(tmp_path / "wt"), tmp_path,
        )
    output = capsys.readouterr().out
    assert success is False
    assert "retained" in output.lower()
    assert "currently checked out in" not in output
