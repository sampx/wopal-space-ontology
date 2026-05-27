#!/usr/bin/env python3
# body.py - Plan body extraction for Issue sync
#
# Provides:
#   - build_issue_body_from_plan: Build normalized Issue body from Plan content
#
# Unified implementation - eliminates duplication between commands/sync.py and domain/issue/sync.py

import os
import re
from pathlib import Path

from dev_flow.domain.plan.metadata import get_plan_field
from dev_flow.domain.issue.link import build_repo_blob_url


def _extract_plan_section(plan_file: str, section: str, limit: int = 0) -> str:
    """
    Extract a markdown section body from a plan file.
    
    Handles fenced code blocks (```) — only matches ## headings outside code blocks.
    """
    content = []
    in_code = False
    found = False
    count = 0
    
    with open(plan_file, 'r') as f:
        for line in f:
            if line.strip().startswith('```'):
                in_code = not in_code
                continue
            
            if not in_code and line.strip() == f"## {section}":
                found = True
                continue
            
            if found and not in_code and line.startswith("##") and not line.startswith(f"## {section}"):
                break
            
            if found and not in_code:
                content.append(line)
                count += 1
                if limit > 0 and count >= limit:
                    break
    
    return ''.join(content).strip()


def _extract_subsection(plan_file: str, subsection: str) -> str:
    """
    Extract a named subsection from a section.
    
    Stops at next ### or ## heading.
    """
    content = []
    in_subsection = False
    
    with open(plan_file, 'r') as f:
        for line in f:
            if line.strip() == f"### {subsection}":
                in_subsection = True
                continue
            
            if in_subsection and (line.startswith("###") or (line.startswith("##") and not line.startswith("###"))):
                break
            
            if in_subsection:
                content.append(line)
    
    return ''.join(content).strip()


def _plan_has_audit_subsections(plan_file: str) -> bool:
    """Check if Plan has Technical Context audit subsections (old format for audit tasks)."""
    subsections = ["Confirmed Bugs", "Content Model Defects", "Cleanup Scope", "Key Findings"]
    
    with open(plan_file, 'r') as f:
        content = f.read()
    
    for subsection in subsections:
        if f"### {subsection}" in content:
            return True
    
    return False


def _plan_has_new_template_subsections(plan_file: str) -> bool:
    """Check if Plan has new template Technical Context 4 subsections."""
    subsections = ["Architecture Context", "Research Findings", "Key Decisions", "Key Interfaces"]
    
    with open(plan_file, 'r') as f:
        content = f.read()
    
    for subsection in subsections:
        if f"### {subsection}" in content:
            return True
    
    return False


def _extract_acceptance_criteria(plan_file: str) -> str:
    """Extract Acceptance Criteria section (including Agent/User sub-sections).
    
    Converts numbered checkboxes (1. [ ]) to GitHub-compatible format (- [ ]).
    """
    content = []
    in_section = False
    
    with open(plan_file, 'r') as f:
        for line in f:
            if line.strip() == "## Acceptance Criteria":
                in_section = True
                continue
            
            if in_section and line.startswith("## ") and not line.startswith("## Acceptance Criteria"):
                break
            
            if in_section:
                content.append(line)
    
    raw_content = ''.join(content).strip()
    
    # Convert numbered checkboxes to GitHub-compatible format:
    # 1. [ ] → - [ ]  (unchecked)
    # 2. [x] → - [x]  (checked)
    converted = re.sub(r'^(\s*)(\d+)\.\s+\[\s*\]', r'\1- [ ]', raw_content, flags=re.MULTILINE)
    converted = re.sub(r'^(\s*)(\d+)\.\s+\[x\]', r'\1- [x]', converted, flags=re.MULTILINE)
    
    return converted


def _extract_technical_context_top(plan_file: str) -> str:
    """Extract Technical Context top-level content (before first ### subsection)."""
    content = []
    in_section = False
    
    with open(plan_file, 'r') as f:
        for line in f:
            if line.strip() == "## Technical Context":
                in_section = True
                continue
            
            if in_section and line.startswith("## ") and not line.startswith("## Technical Context"):
                break
            
            if in_section and line.startswith("###"):
                break
            
            if in_section:
                content.append(line)
    
    return '\n'.join(line for line in content if line.strip())


def _render_issue_section(heading: str, content: str, placeholder: str = "") -> str:
    """Render a markdown section with heading."""
    if not content:
        content = placeholder
    
    return f"## {heading}\n\n{content}\n"


def _render_related_resources_table(reference: str, plan_link: str) -> str:
    """Render Related Resources table."""
    rows = []
    
    if reference:
        rows.append(f"| Research | {reference} |")
    
    rows.append(f"| Plan | {plan_link} |")
    
    return "## Related Resources\n\n" + "\n".join(rows) + "\n"


def build_plan_link_for_issue(plan_file: str, plan_name: str, repo: str, workspace_root: str = None) -> str:
    """Build Plan link row for Issue's Related Resources table.
    
    Args:
        plan_file: Path to Plan file
        plan_name: Plan name (stem of filename)
        repo: Repository in owner/repo format
        workspace_root: Optional workspace root (for Project-based Plan path resolution)
    
    Returns:
        Markdown table row: | Plan | [{plan_name}]({github_url}) |
        Or: | Plan | _待关联_ | if Plan is in planning/draft status
    """
    plan_status = get_plan_field(plan_file, "Status")
    if plan_status in ('planning', 'draft'):
        return "| Plan | _待关联_ |"
    
    project = get_plan_field(plan_file, "Target Project")
    if workspace_root:
        plan_path = Path(plan_file).resolve().relative_to(Path(workspace_root).resolve()).as_posix()
    elif project:
        plan_path = f"docs/projects/{project}/plans/{plan_name}.md"
    else:
        plan_path = f"docs/projects/plans/{plan_name}.md"
    github_url = build_repo_blob_url(repo, plan_path)
    return f"| Plan | [{plan_name}]({github_url}) |"


def build_issue_body_from_plan(plan_file: str, plan_name: str, repo: str, workspace_root: str = None) -> str:
    """Deprecated: Use build_plan_link_for_issue instead.
    
    Returns only the Plan link row (same as build_plan_link_for_issue).
    """
    return build_plan_link_for_issue(plan_file, plan_name, repo, workspace_root)