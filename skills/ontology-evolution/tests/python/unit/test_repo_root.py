#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_repo_root.py - Unit tests for ontology repo root resolution
#
# The scripts live nested inside the skill directory but operate on the
# ontology repository that contains them. Root resolution must therefore
# work without hard-coded absolute paths, and must work both in a git
# worktree and in a materialized space overlay where .git may be a file.

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path

ensure_scripts_path()

from lib import repo  # noqa: E402

ENV_KEY = "WOPAL_EVOLUTION_REPO_ROOT"


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(root), check=True)
    (root / "docs" / "evolutions").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "evolutions" / ".gitkeep").write_text("")
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=str(root), check=True)


class RepoRootCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        saved = os.environ.pop(ENV_KEY, None)
        if saved is not None:
            self.addCleanup(os.environ.__setitem__, ENV_KEY, saved)

    @property
    def nested_script_dir(self) -> Path:
        path = self.root / "skills" / "ontology-evolution" / "scripts"
        path.mkdir(parents=True, exist_ok=True)
        return path


class TestRepoRootResolution(RepoRootCase):
    def test_explicit_env_override_wins(self):
        (self.root / "docs" / "evolutions").mkdir(parents=True)
        os.environ[ENV_KEY] = str(self.root)
        other = self.root / "elsewhere"
        other.mkdir()
        self.assertEqual(repo.resolve_repo_root(other), self.root)

    def test_resolves_git_toplevel_from_nested_script_dir(self):
        _init_repo(self.root)
        resolved = repo.resolve_repo_root(self.nested_script_dir)
        self.assertEqual(Path(resolved).resolve(), self.root)

    def test_falls_back_to_evolutions_marker_without_git(self):
        (self.root / "docs" / "evolutions").mkdir(parents=True)
        resolved = repo.resolve_repo_root(self.nested_script_dir)
        self.assertEqual(Path(resolved).resolve(), self.root)

    def test_message_when_root_cannot_be_resolved(self):
        bare = self.root / "nowhere" / "deeper"
        bare.mkdir(parents=True)
        with self.assertRaises(repo.RepoRootError):
            repo.resolve_repo_root(bare)


if __name__ == "__main__":
    unittest.main()
