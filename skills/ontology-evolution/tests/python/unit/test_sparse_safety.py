#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_sparse_safety.py - Behavior tests for accept / commit / integrate / check.
#
# The contract these tests pin down (docs/DESIGN-evolution.md, Isolation
# Discipline; references/commands.md):
#
#   accept    -> derive an isolated sparse worktree, record its metadata
#   commit    -> widen the sparse range, then commit; refuse unsafe states
#   integrate -> squash the isolated work into the space branch inside .wopal
#   check     -> report proposal and sparse-state problems
#
# The fixture mirrors the real layout: a host repository on `main` that holds
# the assembly source, a `.wopal` sparse worktree on `space/demo` that carries
# the proposal, and a derived worktree under `.worktrees/`. Nothing touches
# the live space.

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[3]
EVO_SH = SKILL_ROOT / "scripts" / "evo.sh"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True
    )


def _run_evo(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["WOPAL_EVOLUTION_REPO_ROOT"] = str(root)
    return subprocess.run(
        ["bash", str(EVO_SH), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
    )


def _fill_placeholders(path: Path) -> None:
    """Replace every `<...>` the template ships with, so `check` passes.

    Read from the script's own template rather than a hand-kept list: a
    second copy of the placeholder set would drift the moment the template
    changes, and the drift would look like a `check` bug.
    """
    import importlib.util
    import sys as _sys

    scripts = str(SKILL_ROOT / "scripts")
    if scripts not in _sys.path:
        _sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "evo_under_test", SKILL_ROOT / "scripts" / "evo.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    text = path.read_text()
    for token in module._placeholders():
        text = text.replace(token, "filled in")
    path.write_text(text)


def worktree_problems(space: Path, target: Path) -> list[str]:
    """Run the isolation assertions against a derived worktree."""
    import sys

    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
    from lib import worktree  # noqa: PLC0415

    return worktree.assert_isolated(space, target)


class SparseSpaceFixture(unittest.TestCase):
    """A host repo + `.wopal` space worktree + a draft proposal."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.space = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)

        self._init_host()
        self._init_wopal()
        self.proposal = self._make_proposal("probe-evolution")

    # ── fixture construction ────────────────────────────────────────────

    def _init_host(self):
        host = self.space
        _git(host, "init", "-q", ".")
        _git(host, "config", "user.email", "probe@local")
        _git(host, "config", "user.name", "probe")
        _git(host, "symbolic-ref", "HEAD", "refs/heads/main")

        (host / "skills" / "alpha").mkdir(parents=True)
        (host / "skills" / "alpha" / "SKILL.md").write_text("alpha\n")
        (host / "skills" / "beta").mkdir(parents=True)
        (host / "skills" / "beta" / "SKILL.md").write_text("beta\n")
        (host / "agents").mkdir()
        (host / "agents" / "maka.md").write_text("maka\n")
        (host / "docs" / "evolutions").mkdir(parents=True)
        (host / "docs" / "DESIGN.md").write_text("design\n")

        _git(host, "add", "-A")
        _git(host, "commit", "-qm", "init")
        _git(host, "branch", "space/demo")

    def _init_wopal(self):
        """Create `.wopal` as a sparse worktree on `space/demo`."""
        result = subprocess.run(
            ["git", "-C", str(self.space), "worktree", "add", "-q",
             str(self.space / ".wopal"), "space/demo"],
            capture_output=True, text=True,
        )
        self.wopal = self.space / ".wopal"
        if result.returncode != 0:  # pragma: no cover - fixture guard
            self.fail(f"fixture failed to create .wopal: {result.stderr}")
        _git(self.wopal, "sparse-checkout", "set", "--no-cone",
             "/skills/alpha/", "/agents/maka.md", "/docs/")

    def _make_proposal(self, name: str) -> Path:
        result = _run_evo(self.wopal, "new", name)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.wopal / "docs" / "evolutions" / f"{name}.md"
        self.assertTrue(path.is_file(), "proposal was not written into .wopal")
        # A real proposal is filled in before it is accepted; the fixture
        # does the same so the accept-time contract gate sees a real shape.
        _fill_placeholders(path)
        # The proposal rides on the space branch, as it does in a live space.
        _git(self.wopal, "add", "--", "docs/evolutions")
        _git(self.wopal, "commit", "-qm", f"docs(evolutions): draft {name}")
        return path

    # ── helpers ─────────────────────────────────────────────────────────

    def stage_of(self, path: Path) -> str:
        match = re.search(r"^\- \*\*Stage\*\*:\s*(\S+)", path.read_text(), re.MULTILINE)
        return match.group(1) if match else ""

    def field_of(self, path: Path, field: str) -> str:
        match = re.search(
            rf"^\- \*\*{re.escape(field)}\*\*:\s*(.*)$", path.read_text(), re.MULTILINE
        )
        return match.group(1).strip() if match else ""

    def patterns_of(self, repo: Path | None = None) -> list[str]:
        result = _git(repo or self.wopal, "sparse-checkout", "list")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def flags_of(self, repo: Path, path: str) -> str:
        """The raw `ls-files --debug` flags value for one path."""
        result = _git(repo, "ls-files", "--debug", "--", path)
        match = re.search(r"flags:\s*(\S+)", result.stdout)
        return match.group(1) if match else ""

    def derived(self) -> Path:
        return self.space / ".worktrees" / "ontology-probe-evolution"


class TestAccept(SparseSpaceFixture):
    def test_accept_derives_worktree_and_records_metadata(self):
        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        target = self.derived()
        self.assertTrue((target / ".git").exists(), "worktree not derived")
        self.assertEqual(self.stage_of(self.proposal), "accepted")
        self.assertEqual(self.field_of(self.proposal, "Mode"), "isolated")
        self.assertEqual(
            self.field_of(self.proposal, "Worktree"),
            ".worktrees/ontology-probe-evolution",
        )
        self.assertEqual(
            (self.wopal / self.field_of(self.proposal, "Branch")).exists(), False
        )
        self.assertEqual(
            self.field_of(self.proposal, "Branch"), "ontology-probe-evolution"
        )
        base = self.field_of(self.proposal, "Base Commit")
        self.assertTrue(base and not base.startswith("("), base)
        # The recorded base is an ancestor of the worktree head, and the
        # worktree already carries the accept metadata.
        self.assertEqual(
            _git(target, "merge-base", "--is-ancestor", base, "HEAD").returncode, 0
        )
        self.assertEqual(self.stage_of(target / "docs" / "evolutions" / "probe-evolution.md"), "accepted")

    def test_derived_worktree_inherits_patterns_and_keeps_host_on_main(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        target = self.derived()

        self.assertEqual(self.patterns_of(target), self.patterns_of())
        self.assertEqual(
            _git(self.space, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), "main"
        )
        self.assertEqual(
            _git(self.wopal, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "space/demo",
        )

    def test_derived_worktree_keeps_out_of_range_files_off_disk(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        target = self.derived()
        # `skills/beta` is tracked but outside the range: no on-disk copy.
        self.assertFalse((target / "skills" / "beta").exists())
        skipped = _git(target, "ls-files", "-t").stdout
        self.assertIn("S skills/beta/SKILL.md", skipped)

    def test_isolation_allows_a_widened_range_but_not_a_narrowed_one(self):
        # An evolution that adds a capability widens the derived range as it
        # goes, so "the worktree sees more than the space" is the normal
        # mid-flight state. "The worktree sees less" is the failure: it means
        # part of the space it was derived from is no longer visible.
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        target = self.derived()

        _git(target, "sparse-checkout", "add", "/skills/newcap/")
        self.assertEqual(worktree_problems(self.space, target), [])

        _git(target, "sparse-checkout", "set", "--no-cone", "/skills/alpha/")
        self.assertTrue(
            any("missing" in item for item in worktree_problems(self.space, target))
        )

    def test_accept_is_idempotent(self):
        first = _run_evo(self.wopal, "accept", "probe-evolution")
        second = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.stage_of(self.proposal), "accepted")

    def test_accept_no_worktree_records_quick_mode(self):
        result = _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.field_of(self.proposal, "Mode"), "quick")
        self.assertFalse((self.derived() / ".git").exists(), "worktree was created")

    def test_accept_rejects_wrong_stage(self):
        # 'validating' and beyond are past the isolation boundary: an accept
        # there could re-derive work that is already integrated.
        for state in ("accepted", "implementing", "validating"):
            _run_evo(self.wopal, "advance", "probe-evolution", "--to", state)
        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("validating", result.stderr)


class TestPreflight(SparseSpaceFixture):
    """The sparse state itself: what counts as coherent, and what does not."""

    def _accept_isolated(self) -> Path:
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        return self.derived()

    def _sparse(self):
        import sys

        sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        from lib import sparse  # noqa: PLC0415 - path is set up just above

        return sparse

    def test_clean_derived_worktree_has_no_problems(self):
        self.assertEqual(self._sparse().preflight(self._accept_isolated()), [])

    def test_disable_leaves_config_false_and_rematerializes(self):
        target = self._accept_isolated()
        _git(target, "sparse-checkout", "disable")
        value = _git(target, "config", "--get", "core.sparseCheckout")
        # `disable` writes `false`; it does not remove the key. A presence-only
        # check would therefore read a destroyed checkout as an enabled one.
        self.assertEqual(value.returncode, 0)
        self.assertEqual(value.stdout.strip(), "false")
        self.assertTrue(self._sparse().preflight(target))

    def test_stripping_a_skip_bit_off_an_out_of_range_entry_is_flagged(self):
        # This is the reachable form of the 2026-09-20 signature: the entry is
        # outside the range, so it has no on-disk copy, and without the bit
        # git reads that as a deletion.
        sparse = self._sparse()
        target = self._accept_isolated()
        self.assertEqual(self.flags_of(target, "skills/beta/SKILL.md"), "40004000")

        _git(target, "update-index", "--no-skip-worktree", "--", "skills/beta/SKILL.md")
        self.assertEqual(self.flags_of(target, "skills/beta/SKILL.md"), "0")
        self.assertEqual(
            sparse.stranded_paths(target), ["skills/beta/SKILL.md"]
        )
        self.assertTrue(sparse.preflight(target))
        status = _git(target, "status", "--porcelain").stdout
        self.assertIn(" D skills/beta/SKILL.md", status)

    def test_in_range_paths_can_carry_a_stray_skip_bit(self):
        # skip-worktree is derived state of the range, so inside the range it
        # is always wrong. Measured: setting it moves the flags from 0 to
        # 0x4000, and a range recompute clears it again.
        sparse = self._sparse()
        target = self._accept_isolated()
        _git(target, "update-index", "--skip-worktree", "--", "skills/alpha/SKILL.md")
        self.assertEqual(self.flags_of(target, "skills/alpha/SKILL.md"), "4000")

        self.assertEqual(sparse.drifted_paths(target), ["skills/alpha/SKILL.md"])
        self.assertTrue(sparse.preflight(target))

        _git(target, "sparse-checkout", "reapply")
        self.assertEqual(self.flags_of(target, "skills/alpha/SKILL.md"), "0")
        self.assertEqual(sparse.drifted_paths(target), [])
        self.assertEqual(sparse.preflight(target), [])

    def test_a_cleared_bit_needs_the_range_off_to_become_destructive(self):
        # The documented three-state table, pinned as behavior so the
        # severity claims in references/commands.md cannot rot:
        #
        #   range | bit   | status   | `git add -A`
        #   on    | clear | ` D`     | stages nothing (git still protects)
        #   off   | clear | ` D`     | stages the deletion
        #
        # This is why a cleared bit is a warning rather than the disaster,
        # and why refusing a switched-off range is the sharper check.
        target = self._accept_isolated()
        _git(target, "update-index", "--no-skip-worktree", "--", "skills/beta/SKILL.md")

        self.assertIn(" D skills/beta/SKILL.md", _git(target, "status", "--porcelain").stdout)
        _git(target, "add", "-A")
        self.assertEqual(_git(target, "diff", "--cached", "--name-only").stdout.strip(), "")
        _git(target, "reset", "-q")

        _git(target, "sparse-checkout", "disable")
        _git(target, "update-index", "--no-skip-worktree", "--", "skills/beta/SKILL.md")
        (target / "skills" / "beta" / "SKILL.md").unlink(missing_ok=True)
        self.assertIn(" D skills/beta/SKILL.md", _git(target, "status", "--porcelain").stdout)
        _git(target, "add", "-A")
        self.assertIn(
            "skills/beta/SKILL.md",
            _git(target, "diff", "--cached", "--name-only").stdout,
            "with the range off, the phantom deletion is staged for real",
        )


class TestCommitSafety(SparseSpaceFixture):
    def _accept_isolated(self) -> Path:
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        return self.derived()

    def test_commit_requires_accept_first(self):
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("accept", result.stderr)

    def test_commit_refuses_when_sparse_is_disabled(self):
        target = self._accept_isolated()
        _git(target, "sparse-checkout", "disable")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse checkout is not enabled", result.stderr)

    def test_commit_refuses_a_stranded_out_of_range_entry(self):
        target = self._accept_isolated()
        _git(target, "update-index", "--no-skip-worktree", "--", "skills/beta/SKILL.md")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills/beta/SKILL.md", result.stderr)

    def test_commit_is_refused_before_writing_anything(self):
        target = self._accept_isolated()
        _git(target, "update-index", "--no-skip-worktree", "--", "skills/beta/SKILL.md")
        before = _git(target, "rev-parse", "HEAD").stdout.strip()
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(_git(target, "rev-parse", "HEAD").stdout.strip(), before)

    def test_commit_widens_range_so_new_file_survives_reapply(self):
        target = self._accept_isolated()
        new_dir = target / "skills" / "newskill"
        new_dir.mkdir(parents=True)
        (new_dir / "SKILL.md").write_text("new\n")

        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "add newskill")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertIn("/skills/newskill/", self.patterns_of(target))
        self.assertNotIn("/skills/newskill//", self.patterns_of(target))

        # The decisive property: after a range recompute the file is still on
        # disk. With `--sparse` instead of widening it would be swept away.
        _git(target, "sparse-checkout", "reapply")
        self.assertTrue(
            (new_dir / "SKILL.md").exists(),
            "new file was swept off disk by a range recompute",
        )

    def test_commit_stages_named_paths_only(self):
        target = self._accept_isolated()
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        # A stray file in the host space must not ride along.
        stray = self.space / "stray.txt"
        stray.write_text("stray\n")

        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit alpha")
        self.assertEqual(result.returncode, 0, result.stderr)

        committed = _git(target, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("skills/alpha/SKILL.md", committed)
        self.assertNotIn("stray.txt", committed)
        self.assertTrue(stray.exists())

    def test_commit_reports_nothing_to_commit(self):
        self._accept_isolated()
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "x")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nothing to commit", result.stdout)

    def test_quick_mode_requires_explicit_paths(self):
        _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (self.wopal / "agents" / "maka.md").write_text("maka edited\n")

        refused = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--paths", refused.stderr)

        allowed = _run_evo(
            self.wopal, "commit", "probe-evolution", "-m", "edit",
            "--paths", "agents/maka.md",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        committed = _git(self.wopal, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("agents/maka.md", committed)

    def test_quick_commit_all_stages_every_changed_path(self):
        # A multi-file fix should not need one --paths entry per file: --all
        # stages every changed path (transient build output still dropped).
        _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (self.wopal / "agents" / "maka.md").write_text("maka edited\n")
        (self.wopal / "skills" / "alpha" / "SKILL.md").write_text("alpha edited\n")

        result = _run_evo(
            self.wopal, "commit", "probe-evolution", "-m", "fix", "--all"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        committed = _git(self.wopal, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("agents/maka.md", committed)
        self.assertIn("skills/alpha/SKILL.md", committed)

    def test_quick_commit_requires_paths_or_all(self):
        _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (self.wopal / "agents" / "maka.md").write_text("maka edited\n")

        refused = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "fix")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--all", refused.stderr)

    def test_quick_mode_commit_includes_the_proposal_record(self):
        _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        # An implementation that changes the proposal itself must be able to
        # commit that change without naming the file explicitly.
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        result = _run_evo(
            self.wopal, "commit", "probe-evolution", "-m", "implement",
            "--paths", "agents/maka.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        committed = _git(self.wopal, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("docs/evolutions/probe-evolution.md", committed)


class TestIntegrate(SparseSpaceFixture):
    def test_integrate_refuses_in_quick_mode(self):
        _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("quick", result.stderr)

    def test_integrate_squashes_work_into_space_branch(self):
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")

        (target / "skills" / "alpha" / "SKILL.md").write_text("alpha EDITED\n")
        new_dir = target / "skills" / "newskill"
        new_dir.mkdir(parents=True)
        (new_dir / "SKILL.md").write_text("new\n")
        committed = _run_evo(
            self.wopal, "commit", "probe-evolution", "-m", "feature work"
        )
        self.assertEqual(committed.returncode, 0, committed.stderr)

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        # The space branch now carries the feature tree. The only permitted
        # difference is the proposal's own `Final Commit` annotation, which
        # cannot be written before the squash exists.
        diff = _git(
            self.wopal, "diff", "--name-only", "ontology-probe-evolution", "HEAD"
        ).stdout.split()
        self.assertEqual(
            diff,
            ["docs/evolutions/probe-evolution.md"],
            f"space branch diverged from the feature tree: {diff}",
        )

        # The space worktree must stay coherent: no stray D/M entries.
        status = _git(self.wopal, "status", "--porcelain").stdout.strip()
        self.assertEqual(status, "", f"space worktree left dirty: {status}")
        final = self.field_of(self.proposal, "Final Commit")
        self.assertTrue(final and not final.startswith("("), final)

        # The integrated commit really is the one that carries the content.
        self.assertIn(
            "skills/newskill/SKILL.md",
            _git(self.wopal, "log", "--name-only", "--format=", "-3").stdout,
        )

        # Range and bits survive integration untouched.
        self.assertIn("/skills/newskill/", self.patterns_of())
        self.assertFalse((self.wopal / "skills" / "beta").exists())

        self.assertEqual(
            _git(self.space, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), "main"
        )

    def test_integrate_materializes_a_brand_new_capability_directory(self):
        # The whole point of an evolution that adds a capability: after
        # integration the new directory must be ON DISK in the space
        # worktree. A squash that only stages it leaves it off-disk and
        # invisible to the runtime.
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")

        new_dir = target / "skills" / "newskill"
        new_dir.mkdir(parents=True)
        (new_dir / "SKILL.md").write_text("brand new\n")
        _run_evo(self.wopal, "commit", "probe-evolution", "-m", "add newskill")

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertIn("/skills/newskill/", self.patterns_of())
        self.assertTrue(
            (self.wopal / "skills" / "newskill" / "SKILL.md").is_file(),
            "new capability directory is not materialized in the space worktree",
        )
        self.assertEqual(
            (self.wopal / "skills" / "newskill" / "SKILL.md").read_text(),
            "brand new\n",
        )
        self.assertEqual(
            self.flags_of(self.wopal, "skills/newskill/SKILL.md"), "0"
        )
        self.assertEqual(
            _git(self.wopal, "status", "--porcelain").stdout.strip(), ""
        )

    def test_stage_transitions_do_not_leave_the_space_worktree_dirty(self):
        # A stage change made while the worktree is derived must be recorded
        # on the space branch AND mirrored into the worktree. Either copy
        # left dirty blocks the next `integrate`.
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")

        for state in ("implementing", "validating", "archived"):
            result = _run_evo(
                self.wopal, "advance", "probe-evolution", "--to", state
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                _git(self.wopal, "status", "--porcelain").stdout.strip(),
                "",
                f"space worktree dirty after -> {state}",
            )
            self.assertEqual(
                _git(target, "status", "--porcelain").stdout.strip(),
                "",
                f"derived worktree dirty after -> {state}",
            )
            self.assertEqual(self.stage_of(self.proposal), state)
            self.assertEqual(
                self.stage_of(target / "docs" / "evolutions" / "probe-evolution.md"),
                state,
            )

    def test_archive_records_its_own_move(self):
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "validating")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "archived")

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        # The move is a deletion plus an addition, and both must be recorded
        # or the space worktree is left dirty.
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")
        # The archived name carries the YYYYMMDD- prefix (D-03), and the
        # default archive cleans up the isolation artifacts (D-02).
        dated = list(
            (self.wopal / "docs" / "evolutions" / "archived").glob(
                "[0-9]" * 8 + "-probe-evolution.md"
            )
        )
        self.assertEqual(len(dated), 1, "archived copy lacks the dated name")
        self.assertFalse((self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists())
        self.assertFalse((target / ".git").exists(), "worktree not cleaned up")

    def test_check_notices_missing_content_not_the_record_commits(self):
        # The space branch legitimately carries stage records the derived
        # worktree does not, so a commit count would fire forever. What the
        # notice has to report is missing *content*.
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")

        record_only = _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        self.assertEqual(record_only.returncode, 0, record_only.stderr)
        clean = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotIn("not integrated", clean.stdout + clean.stderr)

        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit alpha")
        pending = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertIn("skills/alpha/SKILL.md", pending.stdout + pending.stderr)

        _run_evo(self.wopal, "integrate", "probe-evolution")
        settled = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotIn("not integrated", settled.stdout + settled.stderr)

    def test_archive_from_inside_the_worktree_moves_the_canonical_copy(self):
        # Archiving must move the space-branch copy whatever the cwd: a move
        # of the isolated copy would leave the archived file absent from the
        # live space.
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        for state in ("implementing", "validating", "archived"):
            _run_evo(self.wopal, "advance", "probe-evolution", "--to", state)

        result = _run_evo(target, "archive", "probe-evolution", "--keep-worktree")
        self.assertEqual(result.returncode, 0, result.stderr)

        dated = list(
            (self.wopal / "docs" / "evolutions" / "archived").glob(
                "[0-9]" * 8 + "-probe-evolution.md"
            )
        )
        self.assertEqual(len(dated), 1, "canonical copy was not archived (dated name)")
        self.assertFalse(
            (self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists()
        )
        # The mirror keeps the isolated copy in the same shape, committed.
        self.assertEqual(
            len(
                list(
                    (target / "docs" / "evolutions" / "archived").glob(
                        "[0-9]" * 8 + "-probe-evolution.md"
                    )
                )
            ),
            1,
        )
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")
        self.assertEqual(_git(target, "status", "--porcelain").stdout.strip(), "")

    def test_new_from_inside_a_worktree_lands_on_the_space_branch(self):
        # A proposal created from a derived worktree must be visible in the
        # live space, otherwise `accept` and every later command that
        # resolves by space branch cannot see it.
        unrelated = self.space / ".worktrees" / "ontology-unrelated"
        _git(self.space, "worktree", "add", "-q", str(unrelated), "-b",
             "ontology-unrelated", "space/demo")

        result = _run_evo(unrelated, "new", "worktree origin")
        self.assertEqual(result.returncode, 0, result.stderr)

        produced = list(
            (self.wopal / "docs" / "evolutions").glob("worktree-origin.md")
        )
        self.assertEqual(len(produced), 1, "proposal not on the space branch")
        self.assertFalse(
            (unrelated / "docs" / "evolutions" / "worktree-origin.md").exists()
        )

    def test_commit_never_stages_build_output_even_without_gitignore(self):
        # The space constitution forbids committing build output. A repo that
        # forgot to ignore it must not have it swept in by the safe-commit
        # path either, so the drop is explicit and not left to .gitignore.
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        cache = target / "skills" / "ontology-evolution" / "scripts" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "evo.cpython-314.pyc").write_bytes(b"\x00")

        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit alpha")
        self.assertEqual(result.returncode, 0, result.stderr)

        committed = _git(target, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("skills/alpha/SKILL.md", committed)
        self.assertNotIn("__pycache__", committed)

    def test_integrate_is_a_noop_when_nothing_is_outstanding(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        first = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("no-op", second.stdout)


class TestWorktreeCorrectness(SparseSpaceFixture):
    """The 2026-09-23 probe findings, pinned as behavior (proposal D-13/14/15).

    Each test here was first reproduced as a silent corruption or a dead-end
    residue in a temp-repo probe; the assertions encode the corrected
    behavior, not the current one.
    """

    def _accepted(self) -> Path:
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        return self.derived()

    def _widen_and_commit_new_capability(self, target: Path) -> None:
        _git(target, "sparse-checkout", "add", "/skills/gamma/")
        gamma = target / "skills" / "gamma"
        gamma.mkdir(parents=True)
        (gamma / "SKILL.md").write_text("gamma capability\n")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "add gamma")
        self.assertEqual(result.returncode, 0, result.stderr)

    # ── D-13: integrate must refuse a missing or foreign worktree ────────

    def test_integrate_refuses_a_missing_worktree(self):
        # Probe B: a lost worktree directory used to make integrate widen
        # nothing, commit the capability as an off-disk skip-worktree entry,
        # and report success. It must refuse instead, before any mutation.
        target = self._accepted()
        self._widen_and_commit_new_capability(target)

        shutil.rmtree(target)
        _git(self.wopal, "worktree", "prune")
        head_before = _git(self.wopal, "rev-parse", "HEAD").stdout.strip()

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("worktree", result.stderr.lower())
        # Recovery guidance must not lead toward destroying the branch.
        self.assertNotIn("remove the stale branch", result.stderr)
        # Refusal precedes mutation: nothing moved, nothing committed.
        self.assertEqual(
            _git(self.wopal, "rev-parse", "HEAD").stdout.strip(), head_before
        )
        self.assertFalse((self.wopal / "skills" / "gamma").exists())

    def test_integrate_refuses_a_worktree_on_a_foreign_branch(self):
        # Probe D: the recorded worktree sitting on some other branch used to
        # pass integrate with only a dirtiness check. The recorded branch and
        # the worktree's checked-out branch must agree.
        target = self._accepted()
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit")
        self.assertEqual(result.returncode, 0, result.stderr)

        result = _git(target, "checkout", "-qb", "stray-branch")
        self.assertEqual(result.returncode, 0, result.stderr)
        head_before = _git(self.wopal, "rev-parse", "HEAD").stdout.strip()

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("branch", result.stderr.lower())
        self.assertEqual(
            _git(self.wopal, "rev-parse", "HEAD").stdout.strip(), head_before
        )

    def test_integrate_reruns_the_isolation_assertion(self):
        # Defense in depth: an accept-time assertion is not enough; the range
        # can be narrowed or disabled afterwards, and integrate is the last
        # gate before the pool is written.
        target = self._accepted()
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit")
        self.assertEqual(result.returncode, 0, result.stderr)

        _git(target, "sparse-checkout", "disable")
        head_before = _git(self.wopal, "rev-parse", "HEAD").stdout.strip()

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse", result.stderr.lower())
        self.assertEqual(
            _git(self.wopal, "rev-parse", "HEAD").stdout.strip(), head_before
        )

    # ── D-14: the poison-killer — no committed-but-invisible path ────────

    def test_integrate_refuses_when_a_merged_path_stays_out_of_range(self):
        # The invariant: every path the squash stages must end up visible to
        # the runtime. A path staged but left out of the (widened) range is
        # the silent-poison shape from the 2026-09-20 incident: committed,
        # listed, and never materialized. The assertion runs after staging
        # and before commit, so refusal leaves the space worktree clean.
        #
        # Setup: the implementer bypassed `evo.sh commit` and staged a new
        # capability with `git add --sparse`, so the feature branch carries
        # it while the worktree range (the widening source) does not declare
        # it. Widening proposes nothing; the corpus assertion must catch it.
        target = self._accepted()
        gamma = target / "skills" / "gamma"
        gamma.mkdir(parents=True)
        (gamma / "SKILL.md").write_text("gamma capability\n")
        _git(target, "add", "--sparse", "--", "skills/gamma/SKILL.md")
        self.assertEqual(_git(target, "commit", "-qm", "raw git commit").returncode, 0)
        self.assertNotIn("/skills/gamma/", self.patterns_of(target))

        head_before = _git(self.wopal, "rev-parse", "HEAD").stdout.strip()
        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills/gamma/SKILL.md", result.stderr)
        # Refusal restored the space worktree: no staged poison, no residue.
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")
        self.assertEqual(
            _git(self.wopal, "rev-parse", "HEAD").stdout.strip(), head_before
        )
        self.assertFalse((self.wopal / "skills" / "gamma").exists())

    def test_integrate_happy_path_materializes_new_capability(self):
        # The belt-and-braces companion: with a healthy worktree the same
        # flow must keep working end to end.
        target = self._accepted()
        self._widen_and_commit_new_capability(target)

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            (self.wopal / "skills" / "gamma" / "SKILL.md").is_file(),
            "gamma not materialized in the space worktree",
        )
        self.assertEqual(self.flags_of(self.wopal, "skills/gamma/SKILL.md"), "0")

    # ── D-15: accept is transactional; failure cleans up its own residue ─

    def test_accept_refuses_a_corrupted_source_before_deriving(self):
        # Probe G: a disabled-sparse .wopal used to derive a full-checkout
        # worktree first and only fail at the isolation assertion, leaving a
        # branch, a worktree directory, and committed metadata behind. The
        # source health check must refuse before anything is created.
        _git(self.wopal, "sparse-checkout", "disable")

        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse", result.stderr.lower())
        # Zero residue: no worktree, no branch, no metadata commit.
        self.assertFalse((self.derived() / ".git").exists())
        self.assertFalse(
            _git(self.wopal, "branch", "--list", "ontology-probe-evolution").stdout.strip()
        )
        self.assertEqual(self.stage_of(self.proposal), "draft")
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")

    def test_accept_failure_after_derive_cleans_up_its_own_residue(self):
        # Half-derive shape: the branch exists (its worktree was lost) and
        # the derive path is occupied, so re-attaching fails. The refusal
        # must leave the branch untouched — its commits are possibly
        # unmerged work — and never write the accept metadata.
        target = self.derived()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
        (target / "blocker.txt").write_text("blocked\n")
        _git(self.wopal, "branch", "ontology-probe-evolution")

        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        # The metadata was never written: stage and tree are untouched.
        self.assertEqual(self.stage_of(self.proposal), "draft")
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")
        # The branch and its potential commits survive the refusal.
        self.assertTrue(
            _git(self.wopal, "branch", "--list", "ontology-probe-evolution").stdout.strip()
        )

    # ── E4-E8: failed integrate restores cleanly; untracked survives ─────

    def test_failed_integrate_restores_the_space_worktree(self):
        # Probe E: a conflicted squash is refused and the reset must leave
        # no unmerged entries and a clean status, with untracked files the
        # user left in .wopal surviving the refusal.
        target = self._accepted()
        prop_wt = target / "docs" / "evolutions" / "probe-evolution.md"
        prop_wt.write_text(prop_wt.read_text() + "\nworktree-side edit\n")
        _git(target, "add", "--", "docs/evolutions/probe-evolution.md")
        _git(target, "commit", "-qm", "wt edit")
        prop_sp = self.wopal / "docs" / "evolutions" / "probe-evolution.md"
        prop_sp.write_text(prop_sp.read_text() + "\nspace-side edit\n")
        _git(self.wopal, "add", "--", "docs/evolutions/probe-evolution.md")
        _git(self.wopal, "commit", "-qm", "space edit")

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")
        self.assertEqual(_git(self.wopal, "ls-files", "--unmerged").stdout.strip(), "")

    def test_integrate_refuses_but_untracked_files_survive(self):
        # Probe E7/E8: an in-range untracked file blocks integrate at the
        # dirty check, and the refusal must not delete it.
        target = self._accepted()
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit")
        self.assertEqual(result.returncode, 0, result.stderr)

        scratch = self.wopal / "agents" / "scratch.md"
        scratch.write_text("in-range untracked\n")

        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(scratch.exists(), "untracked scratch was deleted by a refusal")

    # ── R1-R3: recovery guidance must not push toward branch deletion ────

    def test_reaccept_with_missing_worktree_recovers_instead_of_destroying(self):
        # Probe R: a re-run of accept with the branch present and the
        # worktree gone used to fail with "remove the stale branch" — advice
        # that destroys possibly-unmerged work. The recovery must re-attach a
        # worktree to the existing branch instead.
        target = self._accepted()
        (target / "skills" / "alpha" / "SKILL.md").write_text("stranded work\n")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "stranded")
        self.assertEqual(result.returncode, 0, result.stderr)

        shutil.rmtree(target)
        _git(self.wopal, "worktree", "prune")

        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        # The stranded work survived: the re-attached worktree carries it.
        self.assertTrue((self.derived() / ".git").exists())
        self.assertEqual(
            (self.derived() / "skills" / "alpha" / "SKILL.md").read_text(),
            "stranded work\n",
        )


class TestTransactionalArchive(SparseSpaceFixture):
    """Archive hygiene (proposal D-02/D-03): dated name, cleanup, guards."""

    def _archiveable(self, keep_worktree: bool = False):
        """Drive a proposal through to the archived stage with real work."""
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (target / "skills" / "alpha" / "SKILL.md").write_text("archived work\n")
        result = _run_evo(self.wopal, "commit", "probe-evolution", "-m", "work")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        for state in ("implementing", "validating", "archived"):
            result = _run_evo(self.wopal, "advance", "probe-evolution", "--to", state)
            self.assertEqual(result.returncode, 0, result.stderr)
        return target

    def test_archive_names_the_file_with_a_date_prefix(self):
        target = self._archiveable()

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        dated = list(
            (self.wopal / "docs" / "evolutions" / "archived").glob(
                "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-probe-evolution.md"
            )
        )
        self.assertEqual(len(dated), 1, "archived file lacks the YYYYMMDD- prefix")
        self.assertFalse(
            (self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists()
        )

    def test_archive_resolves_a_bare_name_to_the_dated_file(self):
        self._archiveable()
        _run_evo(self.wopal, "archive", "probe-evolution")

        result = _run_evo(self.wopal, "status", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("archived", result.stdout)

    def test_archive_refuses_a_duplicate_dated_name(self):
        # A file archived earlier the same day already occupies the dated
        # name; a second archive of the same stem must refuse to overwrite.
        self._archiveable()
        _run_evo(self.wopal, "archive", "probe-evolution", "--keep-worktree")

        # Restore an active copy of the same proposal (stage already
        # 'archived'), then archive again: the dated target exists.
        archived = next(
            (self.wopal / "docs" / "evolutions" / "archived").glob(
                "*-probe-evolution.md"
            )
        )
        restored = self.wopal / "docs" / "evolutions" / "probe-evolution.md"
        restored.write_text(archived.read_text())
        _git(self.wopal, "add", "--", str(restored.relative_to(self.wopal)))
        _git(self.wopal, "commit", "-qm", "restore for re-archive")

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)

    def test_archive_cleans_up_the_isolated_worktree_and_branch(self):
        target = self._archiveable()

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertFalse((target / ".git").exists(), "worktree not removed")
        self.assertFalse(
            _git(self.wopal, "branch", "--list", "ontology-probe-evolution").stdout.strip(),
            "feature branch not removed",
        )
        self.assertEqual(_git(self.wopal, "status", "--porcelain").stdout.strip(), "")

    def test_archive_keep_worktree_preserves_the_isolation_artifacts(self):
        target = self._archiveable()

        result = _run_evo(
            self.wopal, "archive", "probe-evolution", "--keep-worktree"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((target / ".git").exists())
        self.assertTrue(
            _git(self.wopal, "branch", "--list", "ontology-probe-evolution").stdout.strip()
        )

    def test_archive_refuses_unintegrated_content(self):
        # The guard that makes cleanup safe: a branch that still carries
        # unintegrated content must never be deleted, and the archive move
        # must not happen either (refusal precedes mutation).
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (target / "skills" / "alpha" / "SKILL.md").write_text("stranded\n")
        _run_evo(self.wopal, "commit", "probe-evolution", "-m", "stranded")
        for state in ("implementing", "validating", "archived"):
            _run_evo(self.wopal, "advance", "probe-evolution", "--to", state)

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("integrated", result.stderr.lower())
        # Refusal precedes mutation: nothing moved, nothing deleted.
        self.assertTrue((target / ".git").exists())
        self.assertTrue(
            _git(self.wopal, "branch", "--list", "ontology-probe-evolution").stdout.strip()
        )
        self.assertTrue(
            (self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists()
        )
        self.assertFalse(
            list(
                (self.wopal / "docs" / "evolutions" / "archived").glob(
                    "*probe-evolution*"
                )
            )
        )

    def test_archive_skips_cleanup_in_quick_mode(self):
        _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        for state in ("implementing", "validating", "archived"):
            _run_evo(self.wopal, "advance", "probe-evolution", "--to", state)

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            (self.wopal / "docs" / "evolutions" / "archived").glob(
                "[0-9]" * 8 + "-probe-evolution.md"
            )
        )

    def test_archive_moves_the_mirror_to_the_dated_name(self):
        target = self._archiveable()

        result = _run_evo(
            self.wopal, "archive", "probe-evolution", "--keep-worktree"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        dated = list(
            (target / "docs" / "evolutions" / "archived").glob(
                "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-probe-evolution.md"
            )
        )
        self.assertEqual(len(dated), 1, "mirror not moved to the dated name")
        self.assertFalse(
            (target / "docs" / "evolutions" / "probe-evolution.md").exists(),
            "stale active copy left in the worktree",
        )
        self.assertEqual(_git(target, "status", "--porcelain").stdout.strip(), "")

    def test_archive_refuses_a_corrupted_space_worktree(self):
        self._archiveable()
        _git(self.wopal, "sparse-checkout", "disable")

        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse", result.stderr.lower())
        self.assertTrue(
            (self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists(),
            "the move happened despite the refusal",
        )


class TestProposalContract(SparseSpaceFixture):
    """The self-validating proposal contract (D-05/D-06/D-07): the external
    template, the accept-time structure gate, and the corpus lint."""

    def test_new_uses_the_external_template_file(self):
        template = SKILL_ROOT / "templates" / "proposal.md"
        self.assertTrue(template.is_file(), "templates/proposal.md missing")

        result = _run_evo(self.wopal, "new", "template-probe")
        self.assertEqual(result.returncode, 0, result.stderr)
        produced = self.wopal / "docs" / "evolutions" / "template-probe.md"
        text = produced.read_text()
        # The in-use format sections, not the old six thin ones.
        for section in (
            "## Technical Context",
            "### Key Decisions",
            "## In Scope",
            "## Out of Scope",
            "## Affected Files",
            "## Acceptance Criteria",
            "### Agent Verification",
            "### User Validation",
            "## Implementation",
            "## Delegation Strategy",
        ):
            self.assertIn(section, text, f"template lacks {section}")

    def test_new_template_matches_the_live_proposal_shape(self):
        result = _run_evo(self.wopal, "new", "shape-probe")
        self.assertEqual(result.returncode, 0, result.stderr)
        produced = self.wopal / "docs" / "evolutions" / "shape-probe.md"
        text = produced.read_text()
        # The metadata block carries every field the state machine reads.
        for field in (
            "**Stage**",
            "**Mode**",
            "**Worktree**",
            "**Branch**",
            "**Base Commit**",
            "**Final Commit**",
        ):
            self.assertIn(field, text)

    def test_accept_refuses_a_proposal_missing_task_structure(self):
        # A proposal whose Implementation section has no Task structure
        # cannot be accept-gated into implementation: fill everything else,
        # leave the tasks shapeless, and accept must refuse.
        result = _run_evo(self.wopal, "new", "shapeless")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.wopal / "docs" / "evolutions" / "shapeless.md"
        _fill_placeholders(path)
        text = path.read_text()
        # Strip the Implementation body to a shapeless blob.
        text = text.split("## Implementation")[0] + (
            "## Implementation\n\nJust do it.\n\n## Delegation Strategy\n\nN/A\n"
        )
        path.write_text(text)
        _git(self.wopal, "add", "--", "docs/evolutions")
        _git(self.wopal, "commit", "-qm", "shapeless proposal")

        result = _run_evo(self.wopal, "accept", "shapeless")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Task", result.stderr)

    def test_accept_refuses_a_proposal_missing_ac_sections(self):
        result = _run_evo(self.wopal, "new", "no-ac")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.wopal / "docs" / "evolutions" / "no-ac.md"
        _fill_placeholders(path)
        text = path.read_text()
        head, _, tail = text.partition("## Acceptance Criteria")
        tail = tail.partition("## Implementation")[2]
        path.write_text(head + "## Implementation" + tail)
        _git(self.wopal, "add", "--", "docs/evolutions")
        _git(self.wopal, "commit", "-qm", "ac-less proposal")

        result = _run_evo(self.wopal, "accept", "no-ac")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Acceptance Criteria", result.stderr)

    def test_accept_passes_a_well_formed_proposal(self):
        # The fixture's own proposal is filled and Task-shaped; accept
        # must pass it (and this stays green as the contract evolves).
        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_lints_an_undated_file_in_archived(self):
        result = _run_evo(self.wopal, "new", "corpus-lint")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.wopal / "docs" / "evolutions" / "corpus-lint.md"
        _fill_placeholders(path)
        archived_dir = self.wopal / "docs" / "evolutions" / "archived"
        archived_dir.mkdir(parents=True, exist_ok=True)
        (archived_dir / "corpus-lint.md").write_text(path.read_text())
        _git(self.wopal, "add", "--", "docs/evolutions")
        _git(self.wopal, "commit", "-qm", "undated archived file")

        result = _run_evo(self.wopal, "check", "corpus-lint")
        # A lint note, not a hard failure: the file is still addressable.
        self.assertEqual(result.returncode, 0)
        self.assertIn("corpus-lint.md", result.stdout)
        self.assertIn("YYYYMMDD-", result.stdout)

    def test_check_requires_all_six_elements_for_each_task(self):
        # A global element count is not a contract: Task 1 can be complete
        # while Task 2 silently lacks Done. Every Task block must carry all
        # six required elements independently.
        result = _run_evo(self.wopal, "new", "per-task-contract")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.wopal / "docs" / "evolutions" / "per-task-contract.md"
        _fill_placeholders(path)
        result = _run_evo(self.wopal, "accept", "per-task-contract")
        self.assertEqual(result.returncode, 0, result.stderr)

        incomplete_task = """
### Task 2: missing done

**Verification Intent**: AC#1

**Behavior**:
- second behavior

**Pre-read**: N/A

**Design**: second design

**TDD**: true

**Changes**:
1. RED: second test

**Verify**: `true`

"""
        path.write_text(
            path.read_text().replace(
                "\n---\n\n## Delegation Strategy",
                f"\n{incomplete_task}---\n\n## Delegation Strategy",
            )
        )
        _git(self.wopal, "commit", "-qam", "drop task two done")

        result = _run_evo(self.wopal, "check", "per-task-contract")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Task 2", result.stderr)
        self.assertIn("Done", result.stderr)


class TestStageGuards(SparseSpaceFixture):
    """D-08: stage guards fail before mode, sparse, or git operations."""

    def _quick_at(self, stage: str) -> None:
        result = _run_evo(self.wopal, "accept", "probe-evolution", "--no-worktree")
        self.assertEqual(result.returncode, 0, result.stderr)
        chain = {
            "accepted": (),
            "implementing": ("implementing",),
            "validating": ("implementing", "validating"),
            "archived": ("implementing", "validating", "archived"),
        }
        for target in chain[stage]:
            result = _run_evo(self.wopal, "advance", "probe-evolution", "--to", target)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_commit_and_integrate_refuse_before_implementing(self):
        self._quick_at("accepted")
        (self.wopal / "agents" / "maka.md").write_text("edited\n")

        for argv in (
            ("commit", "probe-evolution", "-m", "edit", "--paths", "agents/maka.md"),
            ("integrate", "probe-evolution"),
        ):
            with self.subTest(command=argv[0]):
                result = _run_evo(self.wopal, *argv)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("requires 'implementing'", result.stderr)
                self.assertIn(
                    "evo.sh advance probe-evolution --to implementing",
                    result.stderr,
                )

    def test_terminal_stage_refuses_without_a_guard_crash(self):
        self._quick_at("archived")
        (self.wopal / "agents" / "maka.md").write_text("edited\n")

        for argv in (
            ("commit", "probe-evolution", "-m", "edit", "--paths", "agents/maka.md"),
            ("integrate", "probe-evolution"),
        ):
            with self.subTest(command=argv[0]):
                result = _run_evo(self.wopal, *argv)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("requires 'implementing'", result.stderr)
                self.assertNotIn("Traceback", result.stderr)


class TestP2Hardening(SparseSpaceFixture):
    """D-10/P2: naming bounds, status informativeness, assembly hygiene."""

    def test_slug_truncates_beyond_55_characters(self):
        # Long branch names collide with hook limits and hurt readability;
        # past 55 characters the slug truncates with a 4-hex suffix.
        long_name = "a" * 70
        slug = None
        import sys as _sys
        _sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        from lib import worktree as _wt

        slug = _wt.slugify(long_name)
        self.assertLessEqual(len(slug), 55 + 1 + 4)
        self.assertTrue(slug.endswith(tuple("0123456789abcdef")))

    def test_status_reports_isolation_metadata(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        result = _run_evo(self.wopal, "status", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ("Mode", "Worktree", "Branch", "Base Commit"):
            self.assertIn(expected, result.stdout)


class TestCheck(SparseSpaceFixture):
    def test_check_reports_ok_for_a_draft_with_placeholders(self):
        # A fresh draft is supposed to be full of placeholders; failing it
        # would punish the workflow for working as designed.
        result = _run_evo(self.wopal, "new", "raw-draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = _run_evo(self.wopal, "check", "raw-draft")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("note", result.stdout)
        self.assertIn("placeholder", result.stdout)

    def test_check_is_silent_about_placeholders_a_draft_already_filled(self):
        _fill_placeholders(self.proposal)
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("placeholder", result.stdout)

    def test_check_ignores_angle_brackets_inside_code(self):
        # A proposal that records the CLI contract writes `<name>` / `<state>`
        # inside a fenced block or an inline span. That is documentation, not
        # an unreplaced template placeholder — failing it would reject every
        # proposal that documents its own commands.
        _fill_placeholders(self.proposal)
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        self.proposal.write_text(
            self.proposal.read_text()
            + "\n## Commands\n\n```\nevo.sh advance <name> --to <state>\n```\n"
            + "\nInline `evo.sh check <name>` too.\n"
        )
        _git(self.wopal, "commit", "-qam", "document commands")

        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("placeholder", result.stderr)

    def test_check_still_flags_a_real_placeholder_in_prose(self):
        _fill_placeholders(self.proposal)
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        self.proposal.write_text(
            self.proposal.read_text() + "\nA real <unfilled> placeholder.\n"
        )
        _git(self.wopal, "commit", "-qam", "leave a placeholder")

        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("<unfilled>", result.stderr)

    def test_check_reports_ok_for_an_accepted_isolated_proposal(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        _fill_placeholders(self.proposal)
        _git(self.wopal, "commit", "-qam", "fill in proposal")

        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_detects_missing_metadata(self):
        text = self.proposal.read_text().replace("- **Type**: enhance\n", "")
        self.proposal.write_text(text)
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Type", result.stderr)

    def test_check_detects_unreplaced_placeholder_after_accept(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        self.proposal.write_text(
            self.proposal.read_text() + "\nA late <unfilled> placeholder.\n"
        )
        _git(self.wopal, "commit", "-qam", "late placeholder")
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("placeholder", result.stderr)

    def test_check_detects_disabled_sparse_checkout(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        _git(self.derived(), "sparse-checkout", "disable")
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse", result.stderr)

    def test_check_notes_unintegrated_commits(self):
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit alpha")
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertIn("not integrated", result.stdout + result.stderr)

    def test_check_passes_for_a_cleanly_archived_proposal(self):
        # The terminal state: `archive` moved the file and cleaned up the
        # isolation artifacts. A missing worktree there is the expected end
        # state, not a problem (2026-09-23 fix).
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "validating")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "archived")
        result = _run_evo(self.wopal, "archive", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((target / ".git").exists(), "fixture: cleanup did not run")

        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("missing", result.stderr)
        self.assertNotIn("re-run", result.stderr)

    def test_check_notes_an_incomplete_archive_cleanup(self):
        # Worktree gone but branch still present: cleanup did not finish.
        # The content is already integrated, so this is a notice, not a
        # failure — and the advice must not point at `accept` (impossible
        # for an archived proposal).
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "validating")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "archived")
        result = _run_evo(self.wopal, "archive", "probe-evolution", "--keep-worktree")
        self.assertEqual(result.returncode, 0, result.stderr)
        _git(self.wopal, "worktree", "remove", "--force", str(target))
        _git(self.wopal, "worktree", "prune")

        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("branch", result.stdout)

    def test_check_still_fails_a_missing_worktree_before_archive(self):
        # The archived terminal state is the only place a missing worktree
        # is expected; mid-flight it stays a hard problem.
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        shutil.rmtree(target)
        _git(self.wopal, "worktree", "prune")

        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr)


class TestFix(SparseSpaceFixture):
    """The immediate defect-repair path: a commit, and nothing else."""

    def test_fix_commits_named_paths_without_a_proposal(self):
        (self.wopal / "agents" / "maka.md").write_text("repaired\n")

        result = _run_evo(
            self.wopal, "fix", "-m", "fix: repair maka", "--paths", "agents/maka.md"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        committed = _git(self.wopal, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("agents/maka.md", committed)
        self.assertNotIn("docs/evolutions", committed)
        # No proposal artifact appears, and none is touched.
        proposals = [
            item.name
            for item in (self.wopal / "docs" / "evolutions").glob("*.md")
        ]
        self.assertEqual(proposals, ["probe-evolution.md"])
        self.assertEqual(self.stage_of(self.proposal), "draft")

    def test_fix_all_stages_changed_paths_and_drops_transient(self):
        (self.wopal / "agents" / "maka.md").write_text("a\n")
        (self.wopal / "skills" / "alpha" / "SKILL.md").write_text("b\n")
        cache = self.wopal / "skills" / "ontology-evolution" / "scripts" / "__pycache__"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "x.pyc").write_bytes(b"\x00")

        result = _run_evo(self.wopal, "fix", "-m", "fix: two files", "--all")
        self.assertEqual(result.returncode, 0, result.stderr)

        committed = _git(self.wopal, "show", "--name-only", "--format=", "HEAD").stdout
        self.assertIn("agents/maka.md", committed)
        self.assertIn("skills/alpha/SKILL.md", committed)
        self.assertNotIn("__pycache__", committed)

    def test_fix_refuses_without_message_or_paths(self):
        missing_paths = _run_evo(self.wopal, "fix", "-m", "fix: x")
        self.assertNotEqual(missing_paths.returncode, 0)
        self.assertIn("--all", missing_paths.stderr)

        missing_message = _run_evo(self.wopal, "fix", "--paths", "agents/maka.md")
        self.assertNotEqual(missing_message.returncode, 0)
        self.assertIn("message", missing_message.stderr)

    def test_fix_refuses_an_unknown_path(self):
        result = _run_evo(
            self.wopal, "fix", "-m", "fix: x", "--paths", "no/such/file.md"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no/such/file.md", result.stderr)

    def test_fix_widens_the_range_for_a_new_capability_file(self):
        new_dir = self.wopal / "skills" / "newcap"
        new_dir.mkdir(parents=True)
        (new_dir / "SKILL.md").write_text("new\n")

        result = _run_evo(
            self.wopal,
            "fix", "-m", "fix: new cap",
            "--paths", "skills/newcap/SKILL.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("/skills/newcap/", self.patterns_of())
        # The decisive property: the file survives a range recompute.
        _git(self.wopal, "sparse-checkout", "reapply")
        self.assertTrue((new_dir / "SKILL.md").exists())

    def test_fix_refuses_on_an_incoherent_sparse_state(self):
        _git(self.wopal, "sparse-checkout", "disable")
        (self.wopal / "agents" / "maka.md").write_text("repaired\n")

        result = _run_evo(
            self.wopal, "fix", "-m", "fix: x", "--paths", "agents/maka.md"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse", result.stderr.lower())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
