#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_proposal_state.py - Unit tests for the evolution state machine
#
# Contract under test (docs/DESIGN-evolution.md, Evolution Workflow States):
#   draft -> accepted -> implementing -> validating -> archived
#
#   - the ordered state set is exactly these five
#   - every state has at most one legal successor (a linear chain)
#   - stage read/write goes through the proposal's `Stage` field
#   - writing the current stage is idempotent: no field is duplicated

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path

ensure_scripts_path()

from lib import proposal  # noqa: E402


PROPOSAL_BODY = """# probe-proposal

## Metadata

- **Type**: refactor
- **Created**: 2026-09-21
- **Stage**: {stage}

## Goal

Body text.
"""


def _write_proposal(root: Path, stage: str, name: str = "probe-proposal") -> Path:
    path = root / "docs" / "evolutions" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PROPOSAL_BODY.format(stage=stage))
    return path


class TestStateSet(unittest.TestCase):
    def test_states_are_exactly_the_five_contract_states_in_order(self):
        self.assertEqual(
            list(proposal.STATES),
            ["draft", "accepted", "implementing", "validating", "archived"],
        )

    def test_terminal_state_has_no_successor(self):
        self.assertEqual(proposal.next_states("archived"), [])

    def test_each_state_has_at_most_one_successor(self):
        for index, state in enumerate(proposal.STATES[:-1]):
            self.assertEqual(
                proposal.next_states(state),
                [proposal.STATES[index + 1]],
                f"state {state!r} must have exactly one successor",
            )


class TestTransitionValidation(unittest.TestCase):
    def test_legal_chain_transitions_are_accepted(self):
        for index, state in enumerate(proposal.STATES[:-1]):
            ok, error = proposal.validate_transition(state, proposal.STATES[index + 1])
            self.assertTrue(ok, f"{state} -> next should be legal, got: {error}")
            self.assertIsNone(error)

    def test_skip_ahead_is_rejected(self):
        ok, error = proposal.validate_transition("draft", "archived")
        self.assertFalse(ok)
        self.assertIn("accepted", error)

    def test_backward_move_is_rejected(self):
        ok, error = proposal.validate_transition("validating", "implementing")
        self.assertFalse(ok)
        self.assertIn("archived", error)

    def test_same_state_is_idempotent_not_an_error(self):
        ok, error = proposal.validate_transition("accepted", "accepted")
        self.assertTrue(ok)
        self.assertIsNone(error)

    def test_unknown_target_is_rejected(self):
        ok, error = proposal.validate_transition("draft", "done")
        self.assertFalse(ok)
        self.assertIn("accepted", error)


class TestStageReadWrite(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_get_stage_reads_the_stage_field(self):
        path = _write_proposal(self.root, "implementing")
        self.assertEqual(proposal.get_stage(path), "implementing")

    def test_set_stage_advances_the_field(self):
        path = _write_proposal(self.root, "draft")
        self.assertTrue(proposal.set_stage(path, "accepted"))
        self.assertEqual(proposal.get_stage(path), "accepted")

    def test_set_stage_is_idempotent(self):
        path = _write_proposal(self.root, "accepted")
        proposal.set_stage(path, "accepted")
        proposal.set_stage(path, "accepted")
        text = path.read_text()
        self.assertEqual(text.count("**Stage**"), 1)
        self.assertEqual(proposal.get_stage(path), "accepted")

    def test_set_stage_preserves_surrounding_content(self):
        path = _write_proposal(self.root, "draft")
        before = path.read_text()
        proposal.set_stage(path, "accepted")
        after = path.read_text()
        self.assertNotIn("**Stage**: draft", after)
        self.assertEqual(before.count("## Goal"), after.count("## Goal"))
        self.assertIn("Body text.", after)


QUOTED_PROPOSAL = """# probe-proposal

## Metadata

- **Type**: refactor
- **Created**: 2026-09-21
- **Stage**: `implementing`
- **Mode**: isolated
- **Worktree**: `.worktrees/probe`
- **Branch**: `probe-branch`

## Goal

Body text.
"""


class TestQuotedFieldValues(unittest.TestCase):
    """Hand-authored proposals read naturally with `` `value` `` metadata.

    The mechanism lane consumes `Branch` and `Worktree` as literal git
    values, so one surrounding code span has to be stripped before use —
    otherwise `git merge` is handed a branch name wrapped in backticks.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _write(self) -> Path:
        path = self.root / "docs" / "evolutions" / "probe-proposal.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(QUOTED_PROPOSAL)
        return path

    def test_get_field_strips_backtick_quoting(self):
        path = self._write()
        self.assertEqual(proposal.get_field(path, "Branch"), "probe-branch")
        self.assertEqual(proposal.get_field(path, "Worktree"), ".worktrees/probe")

    def test_get_field_leaves_plain_values_untouched(self):
        path = self._write()
        self.assertEqual(proposal.get_field(path, "Mode"), "isolated")

    def test_get_stage_strips_backtick_quoting(self):
        path = self._write()
        self.assertEqual(proposal.get_stage(path), "implementing")


if __name__ == "__main__":
    unittest.main()
