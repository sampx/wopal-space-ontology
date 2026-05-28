#!/usr/bin/env python3
# test_roadmap_slices_parse.py - Test parse_roadmap_slices and Slice dataclass
#
# Test Case: ROADMAP.md Slices table parsing
#
# Scenarios:
#   1. Basic table parsing (2 slices)
#   2. = prefix project resolution
#   3. Depends parsing
#   4. Demo text extraction
#   5. Empty Slices section

import unittest
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support.bootstrap import ensure_scripts_path
ensure_scripts_path()

from commands.decompose import parse_roadmap_slices, Slice, create_slice_issue
from unittest.mock import patch, MagicMock


ROADMAP_FIXTURE = """# Roadmap

## Slices

| Slice | Title | Project | Risk | Depends | Demo |
|-------|-------|---------|------|---------|------|
| S01 | CLI 多空间管理 | =space-flow | high | none | `wopal space list` 显示多空间 |
| S02 | 空间切换热加载 | space-flow | medium | S01 | 切换空间后 3s 内配置生效 |

### S01: CLI 多空间管理
实现 CLI 命令支持多空间管理。

After this: `wopal space list` 显示多空间

### S02: 空间切换热加载
实现空间切换时的热加载机制。

After this: 切换空间后 3s 内配置生效
"""

ROADMAP_EMPTY_SLICES = """# Roadmap

## Slices

No slices defined yet.
"""


class TestRoadmapSlicesParse(unittest.TestCase):
    """Test parse_roadmap_slices and Slice dataclass"""

    def _write_fixture(self, content: str) -> str:
        """Write content to temp file and return path."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        f.write(content)
        f.close()
        return f.name

    def test_parse_basic_table(self):
        """parse ROADMAP.md table into 2 Slice objects"""
        path = self._write_fixture(ROADMAP_FIXTURE)
        try:
            slices = parse_roadmap_slices(path)
            self.assertEqual(len(slices), 2)
            self.assertEqual(slices[0].id, 'S01')
            self.assertEqual(slices[1].id, 'S02')
        finally:
            os.unlink(path)

    def test_parse_project_equals_prefix(self):
        """=space-flow resolves to space-flow (strip = prefix)"""
        path = self._write_fixture(ROADMAP_FIXTURE)
        try:
            slices = parse_roadmap_slices(path)
            self.assertEqual(slices[0].project, 'space-flow')
        finally:
            os.unlink(path)

    def test_parse_depends(self):
        """S01 depends=[], S02 depends=['S01']"""
        path = self._write_fixture(ROADMAP_FIXTURE)
        try:
            slices = parse_roadmap_slices(path)
            self.assertEqual(slices[0].depends, [])
            self.assertEqual(slices[1].depends, ['S01'])
        finally:
            os.unlink(path)

    def test_parse_demo_text(self):
        """S01 demo contains 'wopal space list'"""
        path = self._write_fixture(ROADMAP_FIXTURE)
        try:
            slices = parse_roadmap_slices(path)
            self.assertIn("wopal space list", slices[0].demo)
        finally:
            os.unlink(path)

    def test_parse_empty_slices_section(self):
        """## Slices with no table returns empty list"""
        path = self._write_fixture(ROADMAP_EMPTY_SLICES)
        try:
            slices = parse_roadmap_slices(path)
            self.assertEqual(slices, [])
        finally:
            os.unlink(path)


    def _get_body_from_gh_call(self, mock_run):
        """Extract --body value from gh issue create call args."""
        call_args = mock_run.call_args[0][0]
        body_idx = call_args.index("--body") + 1
        return call_args[body_idx]

    def test_create_slice_issue_depends_with_titles(self):
        """create_slice_issue renders depends with titles from slice_titles mapping"""
        s = Slice(id="S02", title="空间切换热加载", project="space-flow", risk="medium", depends=["S01"], demo="")
        titles = {"S01": "CLI 多空间管理"}
        with patch("commands.decompose.find_workspace_root", return_value="/tmp/ws"), \
             patch("issue.build_repo_blob_url", return_value="https://example.com/ROADMAP.md"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/org/repo/issues/42\n")
            result = create_slice_issue(s, "org/repo", "/tmp/ws/ROADMAP.md", "wopal", slice_titles=titles)
            self.assertEqual(result, "42")
            body = self._get_body_from_gh_call(mock_run)
            self.assertIn("- S01: CLI 多空间管理", body)
            self.assertNotIn("_(see ROADMAP)_", body)

    def test_create_slice_issue_depends_without_titles(self):
        """create_slice_issue falls back to _(see ROADMAP)_ when slice_titles missing"""
        s = Slice(id="S02", title="空间切换热加载", project="space-flow", risk="medium", depends=["S01"], demo="")
        with patch("commands.decompose.find_workspace_root", return_value="/tmp/ws"), \
             patch("issue.build_repo_blob_url", return_value="https://example.com/ROADMAP.md"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/org/repo/issues/42\n")
            result = create_slice_issue(s, "org/repo", "/tmp/ws/ROADMAP.md", "wopal", slice_titles=None)
            self.assertEqual(result, "42")
            body = self._get_body_from_gh_call(mock_run)
            self.assertIn("- S01: _(see ROADMAP)_", body)


if __name__ == '__main__':
    unittest.main()
