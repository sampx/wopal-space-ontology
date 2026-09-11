#!/usr/bin/env python3
# test_project_resolver.py - TDD tests for lib.project resolver module

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from lib.project import (
    ProjectType,
    PlanLocation,
    resolve_plan_dir,
    find_plan,
    resolve_plan_location,
    build_plan_blob_url,
    _get_default_branch,
)


@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "workspace"
    (ws / ".wopal-space" / "plans" / "gesp").mkdir(parents=True)
    (ws / ".wopal-space" / "plans" / "space-ontology").mkdir(parents=True)
    (ws / ".git").mkdir()
    return ws


def _slug_by_path(path):
    p = str(path)
    if "wopal-space" in p:
        return "sampx/wopal-space"
    return None


# -- resolve_plan_dir -----------------------------------------------------------

class TestResolvePlanDir:
    def test_standard(self, workspace):
        result = resolve_plan_dir("gesp", workspace)
        assert result == workspace / ".wopal-space" / "plans" / "gesp"

    def test_ontology(self, workspace):
        result = resolve_plan_dir("space-ontology", workspace)
        assert result == workspace / ".wopal-space" / "plans" / "space-ontology"


# -- find_plan ------------------------------------------------------------------

class TestFindPlan:
    @patch("lib.project._get_default_branch", return_value="main")
    @patch("lib.project._get_repo_slug", side_effect=_slug_by_path)
    def test_by_name(self, mock_slug, mock_branch, workspace):
        plan_file = workspace / ".wopal-space" / "plans" / "gesp" / "feature-dev-flow-resolver.md"
        plan_file.write_text("# Plan")
        result = find_plan("feature-dev-flow-resolver", workspace)
        assert isinstance(result, PlanLocation)
        assert result.path == plan_file.resolve()
        assert result.is_archived is False

    @patch("lib.project._get_default_branch", return_value="main")
    @patch("lib.project._get_repo_slug", side_effect=_slug_by_path)
    def test_by_issue_number(self, mock_slug, mock_branch, workspace):
        plan_file = workspace / ".wopal-space" / "plans" / "gesp" / "42-feature-dev-flow-resolver.md"
        plan_file.write_text("# Plan 42")
        result = find_plan("42", workspace)
        assert isinstance(result, PlanLocation)
        assert result.path == plan_file.resolve()

    def test_not_found_raises(self, workspace):
        with pytest.raises(FileNotFoundError, match="No plan found"):
            find_plan("nonexistent-plan", workspace)


# -- resolve_plan_location ------------------------------------------------------

class TestResolvePlanLocation:
    @patch("lib.project._get_default_branch", return_value="main")
    @patch("lib.project._get_repo_slug", return_value="sampx/wopal-space")
    def test_active_plan(self, mock_slug, mock_branch, workspace):
        plan_file = workspace / ".wopal-space" / "plans" / "gesp" / "feature-resolver.md"
        plan_file.write_text("# Plan")
        result = resolve_plan_location(plan_file, workspace)
        assert result.path == plan_file.resolve()
        assert result.repo_root == workspace.resolve()
        assert result.repo_relative_path == ".wopal-space/plans/gesp/feature-resolver.md"
        assert result.github_repo == "sampx/wopal-space"
        assert result.branch == "main"
        assert result.is_archived is False

    @patch("lib.project._get_default_branch", return_value="main")
    @patch("lib.project._get_repo_slug", return_value="sampx/wopal-space")
    def test_archived_plan(self, mock_slug, mock_branch, workspace):
        done_dir = workspace / ".wopal-space" / "plans" / "gesp" / "done"
        done_dir.mkdir(parents=True)
        plan_file = done_dir / "feature-old.md"
        plan_file.write_text("# Archived")
        result = resolve_plan_location(plan_file, workspace)
        assert result.is_archived is True


# -- build_plan_blob_url --------------------------------------------------------

class TestBuildPlanBlobUrl:
    def test_with_repo(self):
        loc = PlanLocation(
            path=Path("/repo/.wopal-space/plans/gesp/test.md"),
            repo_root=Path("/repo"),
            repo_relative_path=".wopal-space/plans/gesp/test.md",
            github_repo="sampx/wopal-space",
            branch="main",
            is_archived=False,
        )
        assert build_plan_blob_url(loc) == "https://github.com/sampx/wopal-space/blob/main/.wopal-space/plans/gesp/test.md"

    def test_no_repo(self):
        loc = PlanLocation(
            path=Path("/repo/.wopal-space/plans/gesp/test.md"),
            repo_root=Path("/repo"),
            repo_relative_path=".wopal-space/plans/gesp/test.md",
            github_repo=None,
            branch="main",
            is_archived=False,
        )
        assert build_plan_blob_url(loc) == ""


# -- _get_default_branch ------------------------------------------------------

class _FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _FakeRun:
    """Mimic subprocess.run honoring check=True: raise CalledProcessError
    when returncode != 0 and check is truthy."""

    def __init__(self, scripted):
        # scripted: list of (returncode, stdout) consumed in order; last entry repeats
        self._scripted = scripted
        self.calls = []

    def __call__(self, cmd, *args, **kwargs):
        self.calls.append(cmd)
        rc, out = self._scripted[min(len(self.calls) - 1, len(self._scripted) - 1)]
        if rc != 0 and kwargs.get("check"):
            raise subprocess.CalledProcessError(rc, cmd, output=out, stderr="fatal")
        return _FakeResult(rc, out)


class TestGetDefaultBranch:
    """_get_default_branch must resolve the default branch from LOCAL git
    refs only. It must NEVER invoke `git ls-remote` (a network round-trip that
    hangs in sandboxed environments and caused flow.sh verify/archive timeouts).
    """

    def test_uses_local_symbolic_ref_when_available(self, tmp_path, monkeypatch):
        """Prefer local origin/HEAD symbolic-ref over any fallback."""
        fake = _FakeRun([(0, "refs/remotes/origin/main\n")])
        monkeypatch.setattr("lib.project.subprocess.run", fake)
        assert _get_default_branch(tmp_path) == "main"
        # Only a single local git call, never the network ls-remote
        assert fake.calls == [["git", "symbolic-ref", "refs/remotes/origin/HEAD"]]

    def test_falls_back_to_rev_parse_abbrev_ref(self, tmp_path, monkeypatch):
        """When symbolic-ref fails, fall back to rev-parse --abbrev-ref."""
        fake = _FakeRun([(1, ""), (0, "origin/main\n")])
        monkeypatch.setattr("lib.project.subprocess.run", fake)
        assert _get_default_branch(tmp_path) == "main"
        assert not any("ls-remote" in c for c in fake.calls)

    def test_never_calls_ls_remote_when_refs_exist(self, tmp_path, monkeypatch):
        """Regression guard: resolving default branch must be purely local —
        even when every local lookup fails it degrades to 'main' without
        ever issuing a network call."""
        fake = _FakeRun([(1, ""), (1, ""), (1, "")])
        monkeypatch.setattr("lib.project.subprocess.run", fake)
        assert _get_default_branch(tmp_path) == "main"
        assert not any("ls-remote" in c for c in fake.calls)
