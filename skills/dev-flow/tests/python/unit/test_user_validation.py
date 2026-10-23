#!/usr/bin/env python3
# test_user_validation.py - Language-neutral user-validation completion gate

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from validation import check_user_validation, ValidationError


def _write_tmp(content: str) -> str:
    file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    file.write(content)
    file.close()
    return file.name


class TestUserValidation(unittest.TestCase):

    def test_unchecked_checkbox_rejected(self):
        path = _write_tmp("""# plan

### User Validation

- [ ] 用户确认结果符合预期
""")
        try:
            with self.assertRaises(ValidationError):
                check_user_validation(path)
        finally:
            os.unlink(path)

    def test_checked_checkbox_passes_in_any_language(self):
        path = _write_tmp("""# plan

### User Validation

- [x] The user confirmed the result
""")
        try:
            check_user_validation(path)
        finally:
            os.unlink(path)

    def test_explicit_not_applicable_passes(self):
        # A Plan whose behaviour is fully covered by automated assertions has
        # nothing for the user to inspect; N/A is the way to say that.
        for text in ("N/A — 全部由自动化断言验证。", "**N/A**", "n/a"):
            path = _write_tmp(f"# plan\n\n### User Validation\n\n{text}\n")
            try:
                check_user_validation(path)
            finally:
                os.unlink(path)

    def test_freeform_prose_without_na_still_rejected(self):
        path = _write_tmp("""# plan

### User Validation

用户可能不会看这里。
""")
        try:
            with self.assertRaises(ValidationError):
                check_user_validation(path)
        finally:
            os.unlink(path)

    def test_section_without_checkbox_rejected(self):
        path = _write_tmp("""# plan

### User Validation

User said it looks good.
""")
        try:
            with self.assertRaises(ValidationError):
                check_user_validation(path)
        finally:
            os.unlink(path)

    def test_no_user_validation_section_passes(self):
        path = _write_tmp("# plan\n\n## Goal\n\nNo manual validation required.\n")
        try:
            check_user_validation(path)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
