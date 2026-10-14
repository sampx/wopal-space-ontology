#!/usr/bin/env python3
# test_two_beat_ac.py - Acceptance completion gate

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from validation import check_doc_plan, check_acceptance_criteria, ValidationError


META = """# test-plan

## Metadata

- **Product**:
- **Phase**:
- **Status**: planning

"""


def _write_tmp(content: str) -> str:
    file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    file.write(content)
    file.close()
    return file.name


class TestSubmitDoesNotJudgeAcceptanceSemantics(unittest.TestCase):

    def test_prose_or_criterion_style_does_not_block_submit_check(self):
        path = _write_tmp(META + """## Acceptance Criteria

### Agent Verification

Plain prose is a review-quality issue, not a lifecycle-parser issue.
""")
        try:
            check_doc_plan(path)
        finally:
            os.unlink(path)


class TestCompleteRequiresCheckedAcceptance(unittest.TestCase):

    def test_checked_criterion_passes_without_command_parsing(self):
        path = _write_tmp(META + """## Acceptance Criteria

### Agent Verification

1. [x] Observable behavior has been verified by the controller
""")
        try:
            check_acceptance_criteria(path)
        finally:
            os.unlink(path)

    def test_unchecked_entry_rejected(self):
        path = _write_tmp(META + """## Acceptance Criteria

### Agent Verification

1. [ ] Still pending
""")
        try:
            with self.assertRaises(ValidationError):
                check_acceptance_criteria(path)
        finally:
            os.unlink(path)

    def test_present_section_without_checkbox_rejected(self):
        path = _write_tmp(META + """## Acceptance Criteria

### Agent Verification

No checkbox.
""")
        try:
            with self.assertRaises(ValidationError):
                check_acceptance_criteria(path)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
