#!/usr/bin/env python3
"""Glossary integration tests for the real docset gate."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-docset.py")
MAIN = """# Project

> **Status**: Active
> **Updated**: 2026-01-01

## Overview

The service manages subscriptions.
"""
GLOSSARY = """# Domain Glossary

> **Status**: Active
> **Updated**: 2026-01-01
> **Scope**: Subscriptions

## Terms

| Term | Definition |
|---|---|
| Subscription | An agreement between a customer and a service. |
"""


class GlossaryGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = Path(self.temp.name)
        self.main = self.docs / "DESIGN.md"
        self.glossary = self.docs / "GLOSSARY.md"
        self.main.write_text(MAIN, encoding="utf-8")

    def run_gate(self):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.docs)],
            capture_output=True, text=True, check=False,
        )

    def assert_gate(self, expected, message=None):
        result = self.run_gate()
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if message:
            self.assertIn(message, result.stdout)

    def register(self):
        self.main.write_text(
            MAIN.replace("## Overview", "> **Companion Documents**: `./GLOSSARY.md`\n\n## Overview"),
            encoding="utf-8",
        )

    def test_glossary_is_optional(self):
        self.assert_gate(0)

    def test_valid_registered_glossary(self):
        self.register()
        self.glossary.write_text(GLOSSARY, encoding="utf-8")
        self.assert_gate(0)

    def test_missing_registered_glossary_fails(self):
        self.register()
        self.assert_gate(1, "broken link ./GLOSSARY.md")

    def test_missing_bare_glossary_reference_fails(self):
        self.main.write_text(MAIN.replace("## Overview", "> **Companion Documents**: `GLOSSARY.md`\n\n## Overview"), encoding="utf-8")
        self.assert_gate(1, "broken link GLOSSARY.md")

    def test_glossary_label_is_not_registration(self):
        self.main.write_text(MAIN.replace("## Overview", "> **Companion Documents**: [GLOSSARY.md](./DESIGN.md)\n\n## Overview"), encoding="utf-8")
        self.glossary.write_text(GLOSSARY, encoding="utf-8")
        self.assert_gate(1, "missing Companion Documents registration")

    def test_markdown_glossary_target_is_registration(self):
        self.main.write_text(MAIN.replace("## Overview", "> **Companion Documents**: [Terms](GLOSSARY.md)\n\n## Overview"), encoding="utf-8")
        self.glossary.write_text(GLOSSARY, encoding="utf-8")
        self.assert_gate(0)

    def test_unregistered_glossary_fails(self):
        self.glossary.write_text(GLOSSARY, encoding="utf-8")
        self.assert_gate(1, "GLOSSARY.md: missing Companion Documents registration")

    def test_glossary_is_scanned_for_broken_links(self):
        self.register()
        self.glossary.write_text(GLOSSARY + "\n[Contract](./missing.md)\n", encoding="utf-8")
        self.assert_gate(1, "broken link ./missing.md")

    def test_glossary_cannot_link_transient_proposal(self):
        self.register()
        target = self.docs / "proposals/proposed/feature/2026-01-01-subscription.md"
        target.parent.mkdir(parents=True)
        target.write_text("# Proposal\n", encoding="utf-8")
        self.glossary.write_text(GLOSSARY + f"\n[Proposal](./{target.relative_to(self.docs)})\n", encoding="utf-8")
        self.assert_gate(1, "transient proposal link")

    def test_glossary_rejects_unfilled_template(self):
        self.register()
        self.glossary.write_text(GLOSSARY.replace("Subscription |", "<canonical term> |"), encoding="utf-8")
        self.assert_gate(1, "unreplaced template placeholder")


if __name__ == "__main__":
    unittest.main()
