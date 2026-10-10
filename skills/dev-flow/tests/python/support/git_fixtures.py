#!/usr/bin/env python3
# git_fixtures.py - Shared real-git-repo construction for lifecycle tests
#
# Several lifecycle tests build throwaway git repositories on disk and inject
# failures through a real pre-commit hook. This module is the single copy of
# that construction (R4), so each test file only describes its own scenario.

import shlex
import subprocess
from pathlib import Path


def shell_git(*args, cwd, check=True):
    """Run git in cwd; assert success unless check=False.

    Returns:
        CompletedProcess with text stdout/stderr.
    """
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    if check:
        assert result.returncode == 0, f"git {args} failed: {result.stderr}"
    return result


def init_repo(path: Path) -> None:
    """Create a git repo at path with one initial commit on main."""
    path.mkdir(parents=True, exist_ok=True)
    shell_git("init", "-b", "main", cwd=path)
    shell_git("config", "user.email", "test@test.com", cwd=path)
    shell_git("config", "user.name", "Test", cwd=path)
    (path / "README.md").write_text("# init\n")
    shell_git("add", "README.md", cwd=path)
    shell_git("commit", "-m", "init", cwd=path)


def install_failing_hook(repo: Path, message: str) -> Path:
    """Install a pre-commit hook that fails loudly with `message` on stderr."""
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(f"#!/bin/sh\necho {shlex.quote(message)} >&2\nexit 1\n")
    hook.chmod(0o755)
    return hook
