#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# bootstrap.py - Test harness for scripts path injection
#
# Provides ensure_scripts_path() so tests can import the skill's scripts
# package (lib/, commands/) in both direct execution and pytest discovery.

import sys
from pathlib import Path

# bootstrap.py is at: <skill-root>/tests/python/support/bootstrap.py
# scripts/ is at: <skill-root>/scripts (parents[3] from here)
_THIS_FILE = Path(__file__).resolve()
_SCRIPTS_DIR = str(_THIS_FILE.parents[3] / "scripts")


def ensure_scripts_path() -> str:
    """Inject the skill scripts directory into sys.path (idempotent)."""
    if _SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SCRIPTS_DIR)
    return _SCRIPTS_DIR
