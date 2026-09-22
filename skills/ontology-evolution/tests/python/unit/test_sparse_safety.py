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
        _run_evo(self.wopal, "accept", "probe-evolution")
        _run_evo(self.wopal, "advance", "probe-evolution", "--to", "implementing")
        result = _run_evo(self.wopal, "accept", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)


class TestPreflight(SparseSpaceFixture):
    """The sparse state itself: what counts as coherent, and what does not."""

    def _accept_isolated(self) -> Path:
        _run_evo(self.wopal, "accept", "probe-evolution")
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
        result = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("quick", result.stderr)

    def test_integrate_squashes_work_into_space_branch(self):
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")

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
        self.assertEqual(_git(target, "status", "--porcelain").stdout.strip(), "")
        self.assertTrue(
            (self.wopal / "docs" / "evolutions" / "archived" / "probe-evolution.md").is_file()
        )
        self.assertFalse((self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists())
        self.assertTrue(
            (target / "docs" / "evolutions" / "archived" / "probe-evolution.md").is_file()
        )

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
        for state in ("implementing", "validating", "archived"):
            _run_evo(self.wopal, "advance", "probe-evolution", "--to", state)

        result = _run_evo(target, "archive", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertTrue(
            (self.wopal / "docs" / "evolutions" / "archived" / "probe-evolution.md").is_file(),
            "canonical copy was not archived on the space branch",
        )
        self.assertFalse(
            (self.wopal / "docs" / "evolutions" / "probe-evolution.md").exists()
        )
        # The mirror keeps the isolated copy in the same shape, committed.
        self.assertTrue(
            (target / "docs" / "evolutions" / "archived" / "probe-evolution.md").is_file()
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
        first = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = _run_evo(self.wopal, "integrate", "probe-evolution")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("no-op", second.stdout)


class TestCheck(SparseSpaceFixture):
    def test_check_reports_ok_for_a_draft_with_placeholders(self):
        # A fresh draft is supposed to be full of placeholders; failing it
        # would punish the workflow for working as designed.
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("note", result.stdout)
        self.assertIn("placeholder", result.stdout)

    def test_check_is_silent_about_placeholders_a_draft_already_filled(self):
        _fill_placeholders(self.proposal)
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("placeholder", result.stdout)

    def test_check_reports_ok_for_an_accepted_isolated_proposal(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
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
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("placeholder", result.stderr)

    def test_check_detects_disabled_sparse_checkout(self):
        _run_evo(self.wopal, "accept", "probe-evolution")
        _git(self.derived(), "sparse-checkout", "disable")
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sparse", result.stderr)

    def test_check_notes_unintegrated_commits(self):
        target = self.derived()
        _run_evo(self.wopal, "accept", "probe-evolution")
        (target / "skills" / "alpha" / "SKILL.md").write_text("edited\n")
        _run_evo(self.wopal, "commit", "probe-evolution", "-m", "edit alpha")
        result = _run_evo(self.wopal, "check", "probe-evolution")
        self.assertIn("not integrated", result.stdout + result.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
