#!/usr/bin/env python3
# test_roadmap_analyze.py - Test roadmap Analyze phase (PRD parsing)
#
# Scenarios:
#   1. Extract phase headings from mock PRD
#   2. Extract phase goal/description
#   3. Product name inference (--product flag vs PRD filename stem)
#   4. Empty file / no phase heading boundary

import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.roadmap import parse_prd_phases, _infer_product


PRD_FIXTURE = """# Product PRD

## Overview

This is the overview.

## Implementation Phases

### Phase 1: Foundation

Build the core infrastructure with solid abstractions.

### Phase 2: Feature Development

Implement main user-facing features.

- project: ontology, scope: core
- project: space-flow, scope: integration

### Phase 3: Polish

Final polish and optimization.

## Exit Criteria

- [ ] All tests pass
"""


PRD_H2_FIXTURE = """# Product PRD

## Phase 1: Alpha

The alpha release goal.

## Phase 2: Beta

The beta release goal.
"""


PRD_NO_PHASES = """# Empty PRD

## Overview

Just an overview with no phases.
"""


class TestRoadmapAnalyze(unittest.TestCase):
    """Test roadmap Analyze phase: PRD parsing and product inference."""

    def _write_fixture(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        f.write(content)
        f.close()
        return f.name

    def test_extract_phase_headings_from_prd(self):
        """parse_prd_phases extracts ## Phase N and ### Phase N headings."""
        path = self._write_fixture(PRD_FIXTURE)
        try:
            phases = parse_prd_phases(path)
            self.assertEqual(len(phases), 3)
            self.assertEqual(phases[0].id, "P1")
            self.assertEqual(phases[0].title, "Foundation")
            self.assertEqual(phases[1].id, "P2")
            self.assertEqual(phases[2].title, "Polish")
        finally:
            os.unlink(path)

    def test_extract_phase_goal_and_description(self):
        """parse_prd_phases extracts goal (first paragraph) from each phase."""
        path = self._write_fixture(PRD_FIXTURE)
        try:
            phases = parse_prd_phases(path)
            self.assertIn("core infrastructure", phases[0].goal)
            self.assertIn("main user-facing features", phases[1].goal)
        finally:
            os.unlink(path)

    def test_product_inference_flag_priority(self):
        """--product flag takes priority over PRD filename stem."""
        args = MagicMock()
        args.product = "my-product"

        result = _infer_product("/some/path/PRD.md", args)
        self.assertEqual(result, "my-product")

    def test_product_inference_from_filename(self):
        """Product inferred from PRD filename when --product not set."""
        args = MagicMock(spec=[])
        # MagicMock(spec=[]) means no attributes -> getattr returns MagicMock truthy
        # Need explicit setup
        args = MagicMock()
        del args.product

        result = _infer_product("/some/path/space-flow-PRD.md", args)
        self.assertEqual(result, "space-flow")

    def test_product_inference_plain_prd(self):
        """PRD.md filename -> 'unknown' fallback (empty after stripping)."""
        args = MagicMock(spec=[])
        result = _infer_product("/some/path/PRD.md", args)
        # After stripping "PRD" -> empty -> falls to stem.lower() = "prd"
        self.assertEqual(result, "prd")

    def test_empty_prd_returns_no_phases(self):
        """PRD with no phase headings returns empty list."""
        path = self._write_fixture(PRD_NO_PHASES)
        try:
            phases = parse_prd_phases(path)
            self.assertEqual(phases, [])
        finally:
            os.unlink(path)

    def test_h2_phase_headings(self):
        """## Phase N: headings also recognized (not just ###)."""
        path = self._write_fixture(PRD_H2_FIXTURE)
        try:
            phases = parse_prd_phases(path)
            self.assertEqual(len(phases), 2)
            self.assertEqual(phases[0].id, "P1")
            self.assertEqual(phases[1].id, "P2")
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
