#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_cli_behavior.py - End-to-end behavior tests for evo.sh
#
# Contract (docs/DESIGN-evolution.md, Capability Evolution Workflow):
#   evo.sh new <title>                     -> docs/evolutions/<name>.md, Stage: draft
#   evo.sh status <name|path>              -> stage, file path, next command
#   evo.sh advance <name> --to <state>     -> validate transition; reject illegal
#   evo.sh archive <name>                  -> move to docs/evolutions/archived/
#
# Each case runs the real shell entry point against an isolated temp repo.

import os
import re
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[3]
EVO_SH = SKILL_ROOT / "scripts" / "evo.sh"

STAGES = ["draft", "accepted", "implementing", "validating", "archived"]


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["WOPAL_EVOLUTION_REPO_ROOT"] = str(root)
    return subprocess.run(
        ["bash", str(EVO_SH), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
    )


class EvoTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "docs" / "evolutions").mkdir(parents=True)
        self.addCleanup(self._tmp.cleanup)

    def proposal(self, name: str = "add-probe-capability") -> Path:
        return self.root / "docs" / "evolutions" / f"{name}.md"

    def stage_of(self, path: Path) -> str:
        match = re.search(r"^\- \*\*Stage\*\*:\s*(\S+)", path.read_text(), re.MULTILINE)
        return match.group(1) if match else ""


class TestNew(EvoTestCase):
    def test_new_creates_draft_proposal(self):
        result = _run(self.root, "new", "Add probe capability")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.proposal()
        self.assertTrue(path.is_file(), f"expected {path} to exist")
        self.assertEqual(self.stage_of(path), "draft")

    def test_new_records_creation_date(self):
        _run(self.root, "new", "Add probe capability")
        self.assertIn(f"**Created**: {date.today().isoformat()}", self.proposal().read_text())

    def test_new_slug_is_path_safe(self):
        result = _run(self.root, "new", "Fix: A/B (probe) plan")
        self.assertEqual(result.returncode, 0, result.stderr)
        produced = list((self.root / "docs" / "evolutions").glob("*.md"))
        self.assertEqual(len(produced), 1)
        self.assertNotIn("/", produced[0].name)

    def test_new_refuses_to_overwrite_existing(self):
        _run(self.root, "new", "Add probe capability")
        before = self.proposal().read_text()
        result = _run(self.root, "new", "Add probe capability")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.proposal().read_text())

    def test_new_without_title_fails(self):
        result = _run(self.root, "new")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.proposal().exists())


class TestAdvance(EvoTestCase):
    def _new(self, title: str = "Add probe capability") -> Path:
        self.assertEqual(_run(self.root, "new", title).returncode, 0)
        return self.proposal()

    def test_advance_to_legal_successor(self):
        self._new()
        result = _run(self.root, "advance", "add-probe-capability", "--to", "accepted")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.stage_of(self.proposal()), "accepted")

    def test_full_chain_walk(self):
        self._new()
        for state in STAGES[1:]:
            result = _run(self.root, "advance", "add-probe-capability", "--to", state)
            self.assertEqual(result.returncode, 0, f"{state}: {result.stderr}")
            self.assertEqual(self.stage_of(self.proposal()), state)

    def test_skip_ahead_rejected_and_file_untouched(self):
        path = self._new()
        before = path.read_text()
        result = _run(self.root, "advance", "add-probe-capability", "--to", "archived")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("accepted", result.stderr)
        self.assertEqual(before, path.read_text())

    def test_backward_move_rejected_and_file_untouched(self):
        self._new()
        for state in ["accepted", "implementing", "validating"]:
            _run(self.root, "advance", "add-probe-capability", "--to", state)
        before = self.proposal().read_text()
        result = _run(self.root, "advance", "add-probe-capability", "--to", "implementing")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archived", result.stderr)
        self.assertEqual(before, self.proposal().read_text())

    def test_repeated_advance_is_idempotent(self):
        self._new()
        first = _run(self.root, "advance", "add-probe-capability", "--to", "accepted")
        second = _run(self.root, "advance", "add-probe-capability", "--to", "accepted")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.proposal().read_text().count("**Stage**"), 1)
        self.assertEqual(self.stage_of(self.proposal()), "accepted")

    def test_unknown_target_state_rejected(self):
        self._new()
        result = _run(self.root, "advance", "add-probe-capability", "--to", "done")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.stage_of(self.proposal()), "draft")

    def test_missing_to_flag_fails(self):
        self._new()
        result = _run(self.root, "advance", "add-probe-capability")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.stage_of(self.proposal()), "draft")

    def test_unknown_proposal_fails(self):
        result = _run(self.root, "advance", "no-such-proposal", "--to", "accepted")
        self.assertNotEqual(result.returncode, 0)

    def test_proposal_without_stage_field_cannot_advance(self):
        stray = self.root / "docs" / "evolutions" / "hand-edited.md"
        stray.write_text("# hand-edited\n\n## Metadata\n\n- **Type**: chore\n")
        result = _run(self.root, "advance", "hand-edited", "--to", "accepted")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.stage_of(stray), "")

    def test_advance_accepts_explicit_path(self):
        self._new()
        result = _run(
            self.root,
            "advance",
            "docs/evolutions/add-probe-capability.md",
            "--to",
            "accepted",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.stage_of(self.proposal()), "accepted")


class TestStatus(EvoTestCase):
    def test_status_reports_stage_path_and_next_step(self):
        self.assertEqual(_run(self.root, "new", "Add probe capability").returncode, 0)
        result = _run(self.root, "status", "add-probe-capability")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("draft", result.stdout)
        self.assertIn(str(self.proposal()), result.stdout)
        self.assertIn("advance", result.stdout)
        self.assertIn("accepted", result.stdout)

    def test_status_of_archived_proposal_reports_terminal(self):
        self.assertEqual(_run(self.root, "new", "Add probe capability").returncode, 0)
        for state in STAGES[1:]:
            _run(self.root, "advance", "add-probe-capability", "--to", state)
        result = _run(self.root, "status", "add-probe-capability")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("archived", result.stdout)

    def test_status_unknown_proposal_fails(self):
        result = _run(self.root, "status", "no-such-proposal")
        self.assertNotEqual(result.returncode, 0)


class TestArchive(EvoTestCase):
    def _advance_to_archived(self):
        self.assertEqual(_run(self.root, "new", "Add probe capability").returncode, 0)
        for state in STAGES[1:]:
            _run(self.root, "advance", "add-probe-capability", "--to", state)

    def test_archive_moves_proposal_to_archived_dir(self):
        self._advance_to_archived()
        result = _run(self.root, "archive", "add-probe-capability")
        self.assertEqual(result.returncode, 0, result.stderr)
        archived = self.root / "docs" / "evolutions" / "archived" / "add-probe-capability.md"
        self.assertTrue(archived.is_file())
        self.assertFalse(self.proposal().exists())

    def test_archive_refuses_proposal_not_yet_archived(self):
        self.assertEqual(_run(self.root, "new", "Add probe capability").returncode, 0)
        result = _run(self.root, "archive", "add-probe-capability")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.proposal().is_file())


class TestUsage(EvoTestCase):
    def test_no_arguments_shows_usage(self):
        result = _run(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr.lower() + result.stdout.lower())

    def test_unknown_command_fails(self):
        result = _run(self.root, "frobnicate")
        self.assertNotEqual(result.returncode, 0)


class TestNoAutomaticDelivery(EvoTestCase):
    """The skill must contain no code path that ships changes upstream.

    Delivery (`space sync` / `ontology contribute`) is the user's terminal
    decision (docs/DESIGN-evolution.md, Delivery Terminal). To observe the
    absence of automation directly, every delivery CLI is shimmed on PATH
    with a recorder; running the full command surface must never touch it.
    """

    DELIVERY_CLIS = ("wopal-dev", "wopal", "git-push")

    def test_no_command_invokes_a_delivery_cli(self):
        shim_dir = self.root / "shim-bin"
        shim_dir.mkdir()
        recorder = self.root / "delivery-invocations.log"
        for cli in self.DELIVERY_CLIS:
            shim = shim_dir / cli
            shim.write_text(f'#!/bin/bash\necho "{cli} $*" >> "{recorder}"\nexit 0\n')
            shim.chmod(0o755)

        env = dict(os.environ)
        env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
        env["WOPAL_EVOLUTION_REPO_ROOT"] = str(self.root)

        def run(*args: str) -> None:
            subprocess.run(
                ["bash", str(EVO_SH), *args],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                env=env,
            )

        run("new", "Add probe capability")
        run("status", "add-probe-capability")
        for state in ["accepted", "implementing", "validating", "archived"]:
            run("advance", "add-probe-capability", "--to", state)
        run("archive", "add-probe-capability")

        self.assertFalse(
            recorder.exists(),
            f"a delivery CLI was invoked: {recorder.read_text() if recorder.exists() else ''}",
        )


if __name__ == "__main__":
    unittest.main()
