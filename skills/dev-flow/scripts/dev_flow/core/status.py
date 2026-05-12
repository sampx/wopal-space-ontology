#!/usr/bin/env python3
# status.py - Plan status update for dev-flow
#
# Provides:
#   - update_plan_status: Update Plan Metadata Status line

import re
from pathlib import Path


def update_plan_status(plan_path: str | Path, new_status: str) -> bool:
    """Update Plan file's first Status line in Metadata section.
    
    Finds and replaces the first occurrence of `- **Status**: <value>`
    in the plan file.
    
    Args:
        plan_path: Path to Plan markdown file
        new_status: New status value (e.g., "executing", "done")
        
    Returns:
        True if updated successfully, False if file not found,
        no Status line found, or status unchanged
    """
    path = Path(plan_path)
    
    if not path.exists():
        return False
    
    content = path.read_text()
    
    new_content = re.sub(
        r'^\- \*\*Status\*\*:\s*\w+',
        f'- **Status**: {new_status}',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    
    if new_content == content:
        return False
    
    path.write_text(new_content)
    return True
