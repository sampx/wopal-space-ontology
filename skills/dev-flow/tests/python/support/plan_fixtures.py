#!/usr/bin/env python3
# plan_fixtures.py - Write Plan files whose names satisfy the naming contract
#
# check_doc_plan validates the file name as part of the Plan's identity, so
# fixtures must be named like real Plans instead of using a random tmp prefix.

import tempfile
import shutil
from pathlib import Path


def write_plan_file(content: str, name: str = "test-example") -> str:
    """Write content to a disposable directory as <name>.md and return its path.

    Args:
        content: Plan markdown content
        name: Plan name stem; must satisfy the Plan naming contract

    Returns:
        Path to the created file
    """
    directory = tempfile.mkdtemp()
    path = Path(directory) / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)


def remove_plan_file(path: str) -> None:
    """Remove the fixture directory that holds the file."""
    shutil.rmtree(Path(path).parent, ignore_errors=True)
