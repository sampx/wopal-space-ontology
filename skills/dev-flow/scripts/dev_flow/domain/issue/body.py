#!/usr/bin/env python3
# body.py - Issue body domain operations
#
# Provides:
#   - build_structured_issue_body: Build structured Issue body from fields
#
# Ported from lib/issue.sh build_structured_issue_body()


def _render_section(heading: str, content: str, fallback: str = None) -> str:
    """
    Render a single issue section with consistent formatting.
    
    Args:
        heading: Section heading (without ## prefix)
        content: Section content
        fallback: Optional fallback if content is empty
        
    Returns:
        Formatted markdown section (with newline) or empty string
    """
    if content:
        return f"## {heading}\n\n{content}\n"
    elif fallback:
        return f"## {heading}\n\n{fallback}\n"
    return ""


def _format_list(raw_items: str, prefix: str = "- ") -> str:
    """
    Format comma-separated items as markdown list.
    
    Args:
        raw_items: Comma-separated items string
        prefix: List item prefix (default "- ")
        
    Returns:
        Formatted markdown list or empty string
    """
    if not raw_items:
        return ""
    
    items = [item.strip() for item in raw_items.split(',') if item.strip()]
    if not items:
        return ""
    
    return "\n".join(f"{prefix}{item}" for item in items)


def _render_related_resources_table(reference: str = None) -> str:
    """
    Build Related Resources table.
    
    Args:
        reference: Optional research document reference
        
    Returns:
        Formatted Related Resources section
    """
    lines = [
        "## Related Resources",
        "",
        "| Resource | Link |",
        "|----------|------|"
    ]
    
    if reference:
        lines.append(f"| Research | {reference} |")
    
    lines.append("| Plan | _待关联_ |")
    
    return "\n".join(lines) + "\n"


def build_structured_issue_body(**kwargs) -> str:
    """
    Build structured Issue body with unified five-section layout.

    Section order:
        Goal → Context → Scope (In/Out) → Acceptance Criteria → Related Resources

    Args:
        type: Issue type (unused for rendering, kept for API compat)
        goal: One-line goal description
        context: Background context (research, decisions, references)
        scope: In-scope items, comma-separated
        out_of_scope: Out-of-scope items, comma-separated
        reference: Research document path

    Returns:
        Formatted Issue body markdown
    """
    goal = kwargs.get('goal', '')
    context = kwargs.get('context', '')
    scope = kwargs.get('scope', '')
    out_of_scope = kwargs.get('out_of_scope', '')
    reference = kwargs.get('reference', '')

    sections = []

    # Goal (always present with fallback)
    sections.append(_render_section("Goal", goal, "<一句话描述目标>"))

    # Context (optional)
    if context:
        sections.append(_render_section("Context", context))

    # Scope: In / Out
    scope_parts = []
    if scope:
        scope_parts.append("### In\n")
        scope_parts.append(_format_list(scope))
    if out_of_scope:
        if scope_parts:
            scope_parts.append("\n")
        scope_parts.append("### Out\n")
        scope_parts.append(_format_list(out_of_scope))
    if scope_parts:
        sections.append("## Scope\n\n" + "".join(scope_parts) + "\n")

    # Acceptance Criteria (always present with fallback)
    sections.append(_render_section("Acceptance Criteria", "", "待 plan 阶段细化"))

    # Related Resources (always present)
    sections.append(_render_related_resources_table(reference))

    body = "\n".join(sections)

    return body