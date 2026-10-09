#!/usr/bin/env python3
# test_two_beat_ac.py - Test the two-beat AC mechanism
#
# Two-beat AC design:
#   Beat 1 (submit): Agent Verification accepts criterion-style entries
#            (behavioral pass criteria without concrete commands).
#            Old rule: reject if no executable command — now too strict.
#            New rule: section must exist and each entry must be a
#            checkbox; commands are NOT required at submit time.
#   Beat 2 (complete): a CHECKED AC entry must contain an executable
#            command pattern — criterion-style ACs cannot pass complete
#            checked. Unchecked entries are allowed at submit.
#
# Related: check_doc_plan's "Agent Verification must appear before
# Implementation" ordering check stays unchanged.

import unittest
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from validation import (
    check_doc_plan,
    check_acceptance_criteria,
    ValidationError,
)


def _write_tmp(content: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', delete=False, encoding='utf-8'
    )
    f.write(content)
    f.close()
    return f.name


VALID_META = """# test-plan

## Metadata

- **Type**: test
- **Product**:
- **Phase**:
- **Project Path**: .
- **Status**: planning

"""

AC_BEAT1_CRITERIA = """## Acceptance Criteria

### Agent Verification

1. [ ] Runner 一致性测试全绿，后台无交互死等
2. [ ] 权限探针保留拒绝证据，直接与间接 commit/merge 被拒绝

## Implementation

### Task 1: Test Task

**Verification Intent**: AC#1

**Behavior**: Task produces correct output.

**Files**: `test.py`

**Pre-read**: N/A

**Design**:
Complete implementation design.

**TDD**: false

**Changes**:
1. Implement function A.

**Verify**: `rg -c 'pattern' test.py` ≥ 1

**Done**:
任务产出：test.py 实现完成
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）
"""

AC_BEAT2_CHECKED_COMMAND = """## Acceptance Criteria

### Agent Verification

1. [x] `python -m pytest tests/ -v` 全部 pass
"""

AC_BEAT2_CHECKED_CRITERIA = """## Acceptance Criteria

### Agent Verification

1. [x] Runner 一致性测试全绿，后台无交互死等
"""

AC_EMPTY_SECTION = """## Acceptance Criteria

### Agent Verification

## Implementation
"""


class TestBeatOneSubmit(unittest.TestCase):
    """Beat 1: submit-time validation accepts criterion-style ACs"""

    def test_criterion_style_ac_passes_submit(self):
        """Criterion-style ACs (no commands) must pass check_doc_plan"""
        path = _write_tmp(VALID_META + AC_BEAT1_CRITERIA)
        try:
            check_doc_plan(path)  # should not raise
        finally:
            os.unlink(path)

    def test_prose_only_av_section_rejected(self):
        """An AV section with prose but no checkbox entries is rejected —
        nothing verifiable was declared."""
        path = _write_tmp(VALID_META + """## Acceptance Criteria

### Agent Verification

Plain prose, no checkbox entries.

## Implementation
""")
        try:
            with self.assertRaises(ValidationError) as ctx:
                check_doc_plan(path)
            self.assertIn("Agent Verification", str(ctx.exception))
        finally:
            os.unlink(path)


class TestBeatTwoComplete(unittest.TestCase):
    """Beat 2: complete-time gate requires commands on checked ACs"""

    def test_checked_command_ac_passes_complete(self):
        """A checked AC with an executable command passes"""
        path = _write_tmp(VALID_META + AC_BEAT2_CHECKED_COMMAND)
        try:
            check_acceptance_criteria(path)  # should not raise
        finally:
            os.unlink(path)

    def test_checked_criterion_ac_rejected_at_complete(self):
        """A checked AC without a command must be rejected at complete"""
        path = _write_tmp(VALID_META + AC_BEAT2_CHECKED_CRITERIA)
        try:
            with self.assertRaises(ValidationError) as ctx:
                check_acceptance_criteria(path)
            msg = str(ctx.exception)
            self.assertTrue(
                "command" in msg.lower() or "命令" in msg,
                f"Error should mention missing command: {msg}"
            )
        finally:
            os.unlink(path)

    def test_unchecked_criterion_ac_rejected_at_complete(self):
        """Unchecked ACs are still rejected at complete (existing rule)"""
        path = _write_tmp(VALID_META + AC_BEAT1_CRITERIA.split("## Implementation")[0])
        try:
            with self.assertRaises(ValidationError) as ctx:
                check_acceptance_criteria(path)
            self.assertIn("not completed", str(ctx.exception))
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()