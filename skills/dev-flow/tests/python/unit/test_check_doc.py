#!/usr/bin/env python3
# test_check_doc.py - Mechanical submit/approve validation

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from validation import check_doc_plan, ValidationError


BASE = """# test-plan

## Metadata

- **Type**: test
- **Target Project**:
- **Product**:
- **Phase**:
- **Project Path**:
- **Status**: planning

## Goal

Any human-readable plan content is allowed here.
"""


def _write_tmp(content: str) -> str:
    file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    file.write(content)
    file.close()
    return file.name


class TestCheckDocPlan(unittest.TestCase):

    def test_valid_minimal_metadata_passes(self):
        path = _write_tmp(BASE)
        try:
            check_doc_plan(path)
        finally:
            os.unlink(path)

    def test_plan_semantics_do_not_block_mechanical_check(self):
        content = BASE + """
## Implementation

### Task 1: Example

Free-form task content without Design Source, Behavior, TDD, or special formatting.
"""
        path = _write_tmp(content)
        try:
            check_doc_plan(path)
        finally:
            os.unlink(path)

    def test_missing_status_rejected(self):
        path = _write_tmp(BASE.replace("- **Status**: planning\n", ""))
        try:
            with self.assertRaises(ValidationError) as ctx:
                check_doc_plan(path)
            self.assertIn("Status", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_unsupported_status_rejected(self):
        path = _write_tmp(BASE.replace("planning", "unknown-state"))
        try:
            with self.assertRaises(ValidationError) as ctx:
                check_doc_plan(path)
            self.assertIn("Status", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_target_project_requires_project_path(self):
        content = BASE.replace("- **Target Project**:\n", "- **Target Project**: example\n")
        path = _write_tmp(content)
        try:
            with self.assertRaises(ValidationError) as ctx:
                check_doc_plan(path)
            self.assertIn("Project Path", str(ctx.exception))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
