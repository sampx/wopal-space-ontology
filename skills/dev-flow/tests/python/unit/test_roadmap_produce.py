#!/usr/bin/env python3
# test_roadmap_produce.py - Test roadmap Produce phase (phase doc writing)
#
# Scenarios:
#   1. Phase documents written to phases/ directory
#   2. Phase document content matches schema (Metadata/Goal/Involved Projects/Exit Criteria)
#   3. PRD reference writeback (Phase heading gets `> Phase doc:` line)

import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.roadmap import (
    ConfirmedPhase,
    _produce,
    _writeback_prd_reference,
)


PRD_WITH_PHASES = """# Product PRD

## Phase 1: Foundation

Build the core infrastructure.

## Phase 2: Features

Implement features.

"""


class TestRoadmapProduce(unittest.TestCase):
    """Test roadmap Produce phase: phase document writing and PRD writeback."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.prd_path = os.path.join(self.tmpdir, "PRD.md")
        with open(self.prd_path, "w") as f:
            f.write(PRD_WITH_PHASES)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_phase_docs_written_to_phases_dir(self):
        """Phase documents are written to phases/ directory next to PRD."""
        phases = [
            ConfirmedPhase(
                id="P1", title="Foundation",
                goal="Build the core",
                involved_projects=["ontology"],
                exit_criteria=["Tests pass"],
            ),
            ConfirmedPhase(
                id="P2", title="Features",
                goal="Implement features",
                involved_projects=["space-flow"],
                exit_criteria=["Demo works"],
            ),
        ]

        written = _produce(phases, "myproduct", self.prd_path, Path(self.tmpdir))

        self.assertEqual(len(written), 2)
        phases_dir = os.path.join(self.tmpdir, "phases")
        self.assertTrue(os.path.isdir(phases_dir))

        files = os.listdir(phases_dir)
        self.assertEqual(len(files), 2)
        # Filenames should contain product and phase id
        for fn in files:
            self.assertTrue(fn.startswith("myproduct-p"))
            self.assertTrue(fn.endswith(".md"))

    def test_phase_doc_content_matches_schema(self):
        """Phase document content has Metadata, Goal, Involved Projects, Exit Criteria."""
        phases = [
            ConfirmedPhase(
                id="P1", title="Foundation",
                goal="Build the core",
                involved_projects=["ontology"],
                exit_criteria=["Tests pass", "No regressions"],
            ),
        ]

        written = _produce(phases, "myproduct", self.prd_path, Path(self.tmpdir))
        self.assertEqual(len(written), 1)

        content = written[0].read_text(encoding="utf-8")

        # Check Metadata section
        self.assertIn("**Phase ID**: P1", content)
        self.assertIn("**Product**: myproduct", content)
        self.assertIn("**Status**: planning", content)

        # Check Goal section
        self.assertIn("## Goal", content)
        self.assertIn("Build the core", content)

        # Check Involved Projects
        self.assertIn("## Involved Projects", content)
        self.assertIn("project: ontology", content)

        # Check Exit Criteria
        self.assertIn("## Exit Criteria", content)
        self.assertIn("Tests pass", content)
        self.assertIn("No regressions", content)

    def test_prd_reference_writeback(self):
        """PRD gets `> Phase doc:` reference line after Phase heading."""
        # Write a PRD with a clear Phase heading
        prd_content = "# Product PRD\n\n## Phase 1: Foundation\n\nBuild the core.\n\n## Phase 2: Features\n\nMore stuff.\n"
        prd_path = os.path.join(self.tmpdir, "test-PRD.md")
        with open(prd_path, "w") as f:
            f.write(prd_content)

        _writeback_prd_reference(prd_path, "P1", "myproduct-p1-foundation.md")

        with open(prd_path, "r") as f:
            updated = f.read()

        self.assertIn("> Phase doc: [phases/myproduct-p1-foundation.md](phases/myproduct-p1-foundation.md)", updated)
        # The reference should appear right after Phase 1 heading
        phase1_idx = updated.index("## Phase 1: Foundation")
        ref_idx = updated.index("> Phase doc:", phase1_idx)
        # Reference should be within 3 lines of the heading
        between = updated[phase1_idx:ref_idx]
        self.assertLess(between.count("\n"), 4)

    def test_prd_writeback_idempotent(self):
        """Running writeback twice does not duplicate the reference line."""
        prd_content = "# Product PRD\n\n## Phase 1: Foundation\n\nBuild the core.\n"
        prd_path = os.path.join(self.tmpdir, "idem-PRD.md")
        with open(prd_path, "w") as f:
            f.write(prd_content)

        _writeback_prd_reference(prd_path, "P1", "prod-p1-foundation.md")
        _writeback_prd_reference(prd_path, "P1", "prod-p1-foundation.md")

        with open(prd_path, "r") as f:
            updated = f.read()

        count = updated.count("> Phase doc: [phases/prod-p1-foundation.md]")
        self.assertEqual(count, 1, "Reference line should appear exactly once")


if __name__ == '__main__':
    unittest.main()
