#!/usr/bin/env python3
"""Verify a documentation set against the dev-doc-master consistency rules.

Usage:
  python3 verify-docset.py <docs-dir> [--main DESIGN.md] [--strict] [--check-sync [--base <git-ref>] [--pure-refactor <reason>]]

Checks:
  1. Discover sub-documents (DESIGN-*.md / PRD-*.md) on disk and verify every sub-document header carries a parent link to the main document (main header Sub-DESIGNs enumeration is retired and unchecked).
  2. No absolute paths (file:/// or /Users/... or /Volumes/...) in any .md.
  3. Relative links resolve to existing files.
  4. End section (Reference Documents) contains no sub-DESIGNs and no header docs.
  5. No process-state vocabulary (已废弃/已放弃/不再执行/历史机制/deprecated/legacy/moved from).
  6. Every document has an Updated date.
  7. Header field names come from the fixed English vocabulary.
  8. Every document's Status is Draft / Proposed / Active.
  9. Every discovered sub-document is linked from the main document body outside Reference Documents (no orphan sub-DESIGNs).
 10. No unreplaced template placeholders or completely empty table skeleton rows.
 11. Non-empty ## sections (unless immediately followed by a ### subsection with content) and required boundaries on Project/Active Module DESIGNs.
 12. Optional (--check-sync): map changed code paths via Module Architecture's Source Carrier column and require owning DESIGN updates unless --pure-refactor is justified.

Exit code 0 on pass, 1 on any failure. Prints a report.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# High-signal process-state vocabulary. These mark historical/process narration in
# design docs. Lower-signal terms like 迁移 (data/config migration) and legacy
# (release taxonomy) are legitimate domain vocabulary and deliberately excluded.
PROCESS_STATE_TERMS = [
    "已废弃", "已放弃", "不再执行", "历史机制", "原方案已废弃", "原实现已废弃",
    "deprecated", "moved from", "no longer",
]

# Unreplaced template placeholders copied straight from templates/*.md.
TEMPLATE_PLACEHOLDERS = (
    "# <Project Name>",
    "# <Product Name>",
    "# DESIGN — <Topic or Module>",
    "Updated**: YYYY-MM-DD",
    "<parent-design-path or N/A>",
    "<parent-product-prd-path or N/A>",
    "<product-design-path or N/A>",
    "<product-prd-path or N/A>",
    "<ASCII architecture diagram>",
    "## <Topic or Module Overview>",
    "## <Domain Concept or Core Mechanism 1..N>",
    "## <Cross-Cutting Mechanism>",
    "<yyyy-mm-dd-slug>",
    "<decision>",
    "<settled conclusion and concise rationale>",
    "<reference-only material; never repeat Parent, Parent Architecture, or Parent Product>",
    "<prd-path>",
)

_EMPTY_TABLE_ROW_RE = re.compile(r"^\|\s*(?:\|\s*)+$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")
_H3_PLUS_RE = re.compile(r"^#{3,6}\s+(.+?)\s*$")
_TEST_PATH_RE = re.compile(
    r"(?:^|/)(?:test|tests|__tests__)/|\.(?:test|spec)\.[^/]+$|_test\.[^/]+$",
    re.IGNORECASE,
)


def fail(report, *lines):
    for line in lines:
        report.append(f"  FAIL: {line}")


# Design-set documents only: DESIGN*.md, PRD*.md, BRANDING.md, API-*.md, WORKBENCH.
# Excludes PLAN-TODOS.md (task lists), research/, and other auxiliary material.
_DESIGN_DOC_RE = re.compile(r"^(DESIGN|PRD|BRANDING|API-CONTRACT)[\w-]*\.md$")


def _doc_files(doc_dir):
    """Top-level design-set documents only.
    Excludes research/, references/, assets/, and task-list docs (PLAN-*.md)."""
    skip_dirs = {"research", "references", "assets", "images"}
    for p in sorted(Path(doc_dir).glob("*.md")):
        if any(part in skip_dirs for part in p.parts):
            continue
        if not _DESIGN_DOC_RE.match(p.name):
            continue
        yield p


def _iter_lines_with_fence_state(text):
    """Yield (line_number, line_text, in_fence) across a document."""
    fence_char = None
    for idx, line in enumerate(text.splitlines(), 1):
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(1)[0]
            if fence_char is None:
                fence_char = marker
                yield idx, line, True
                continue
            elif fence_char == marker:
                yield idx, line, True
                fence_char = None
                continue
        yield idx, line, (fence_char is not None)


def _split_non_ref_text(text):
    """Return text before ## Reference Documents / ## 参考文档 (ignoring fenced blocks)."""
    kept = []
    for _, line, in_fence in _iter_lines_with_fence_state(text):
        if not in_fence and line.strip() in ("## Reference Documents", "## 参考文档"):
            break
        kept.append(line)
    return "\n".join(kept)


def discover_subdesigns(doc_dir, main_name, report):
    """Verify the main document exists and discover sub-documents on disk.

    Main DESIGNs (product and project alike) no longer list `Sub-DESIGNs` in
    their headers; sub-documents identify themselves by filename and `Parent`.
    """
    prefix = "PRD-" if main_name.startswith("PRD") else "DESIGN-"
    sub_files = sorted(
        p.name for p in Path(doc_dir).glob(f"{prefix}*.md")
        if p.parent == Path(doc_dir)
    )
    main_path = Path(doc_dir) / main_name
    if not main_path.exists():
        fail(report, f"main document {main_name} not found")
        return sub_files

    report.append(f"  OK: Discovered {len(sub_files)} sub-documents for {main_name}")
    return sub_files


def check_sub_parent_links(doc_dir, main_name, sub_files, report):
    """Each sub-document must carry a Parent (上级) link to the main document."""
    for name in sub_files:
        p = Path(doc_dir) / name
        text = p.read_text(encoding="utf-8")
        header = text.split("##")[0]
        parent_ref = f"./{main_name}"
        # allow 上级 / 上级架构 pointing at the main doc
        ok = (
            parent_ref in header
            or (f"`{main_name}`" in header and "上级" in header)
        )
        if not ok:
            fail(report, f"{name}: missing 上级 parent link to ./{main_name}")


def check_absolute_paths(doc_dir, report):
    for p in _doc_files(doc_dir):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "file:///" in line or re.search(r"/Users/|/Volumes/", line):
                fail(report, f"{p.name}:{i}: absolute path: {line.strip()[:80]}")


def check_relative_links(doc_dir, report):
    """Verify the document links that carry lineage resolve on disk.

    Documents reference each other two ways: as a Markdown link
    (`[text](./x.md)`) and as a backticked path (`` `./x.md` ``). Both are checked,
    because the header lineage fields (`Parent`, `Parent Architecture`,
    `Sub-DESIGNs`, `Product PRD`) use the backticked form and carry the most
    load-bearing references in the set. Checking only the Markdown form leaves
    exactly those links unverified.

    Scope is deliberately narrow. A document body also mentions paths that are
    not links at all: a repository-root path (`projects/x/docs/y.md`), a
    runtime path inside a space (`.wopal/skills/...`), or a path inside another
    repository (`packages/app/AGENTS.md`). Those resolve against a different
    root than the document does, so a document-relative resolution reports them
    as broken when they are correct. Only two forms are treated as links:

    - Markdown link targets, which are always document-relative by convention.
    - Backticked paths that begin with `./` or `../`, the explicit relative
      form used throughout the header fields.

    A backticked path with no leading `./` or `../` names something resolved
    against some other root, and is left alone.
    """
    md_link_re = re.compile(r"\]\(([^)#]+?)(?:#[^)]*)?\)")
    rel_tick_re = re.compile(r"`((?:\.{1,2}/)[^`\s]*?\.md)`")
    errors = []
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            targets = list(md_link_re.findall(line))
            targets += rel_tick_re.findall(line)
            for target in targets:
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#")[0]
                if not target or "://" in target or "*" in target:
                    continue
                resolved = (p.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"{p.name}:{i}: broken link {target}")
    for e in errors:
        fail(report, e)


# A link may be written as a backticked path (`./DESIGN.md`) or as a bare
# path reference inside prose. Both forms establish a header obligation, so
# both must be caught when checking for header/end duplication.
_LINK_RE = re.compile(r"`([^`\s]+\.md)`|(?<![`\w/.-])((?:\.{1,2}/|[\w.-]+/)*[\w.-]+\.md)")


def _split_end_section(text):
    """Return the end-section body, or None when the document has no end section."""
    for marker in ("## 参考文档", "## Reference Documents"):
        if marker in text:
            return text.split(marker)[-1]
    return None


def check_end_section(doc_dir, main_name, sub_files, report):
    """A document's end section carries reference-only material.

    Two rules are enforced across every document in the set:

    1. A sub-DESIGN declared in the main header must not reappear in the end
       section — the header is the structure declaration, the end section is
       reference material, and a file belongs to exactly one of them.
    2. No document may list in its end section anything its own header already
       names. A header link is an obligation; repeating it as reference makes
       the obligation ambiguous to a reader.

    The second rule is what keeps authors from using the end section as a
    dumping ground: if a document matters enough to bind the reader, it belongs
    in the header; if it does not, it does not need to be named twice.
    """
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        end = _split_end_section(text)
        if end is None:
            continue

        header = text.split("##")[0]
        header_links = {m.group(1) for m in _LINK_RE.finditer(header)}
        end_links = {m.group(1) for m in _LINK_RE.finditer(end)}

        if p.name == main_name:
            # Match the sub-design as a standalone link target, not as a
            # substring of a longer path. `./DESIGN-foo.md` is the sub-design;
            # `../other-repo/docs/DESIGN-foo.md` is a different document that
            # happens to share a filename.
            end_targets = {m.group(1) for m in _LINK_RE.finditer(end)}
            end_targets |= {m.group(2) for m in _LINK_RE.finditer(end) if m.group(2)}
            for name in sub_files:
                local = {f"./{name}", name}
                if end_targets & local:
                    fail(report, f"{p.name}: sub-DESIGN {name} appears in the end section")

        for link in sorted(header_links & end_links):
            fail(report, f"{p.name}: '{link}' listed in both header and end section")


def check_sub_body_reachability(doc_dir, main_name, sub_files, report):
    """Every sub-document on disk must be linked from the main document outside Reference Documents."""
    main_path = Path(doc_dir) / main_name
    if not main_path.exists() or not sub_files:
        return

    non_ref = _split_non_ref_text(main_path.read_text(encoding="utf-8"))
    md_link_re = re.compile(r"\]\(([^)#\s]+?)(?:#[^)]*)?\)")
    referenced = set()
    for _, line, in_fence in _iter_lines_with_fence_state(non_ref):
        if in_fence:
            continue
        for target in md_link_re.findall(line):
            referenced.add(target.strip())
        for m in _LINK_RE.finditer(line):
            target = m.group(1) or m.group(2)
            if target:
                referenced.add(target.strip())

    for sub_name in sub_files:
        local = {sub_name, f"./{sub_name}"}
        if not (referenced & local):
            fail(report, f"{main_name}: orphan sub-document {sub_name} is not linked from main document body")


def check_template_placeholders(doc_dir, report):
    """Reject unreplaced template placeholders and completely empty table skeleton rows."""
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        for i, line, in_fence in _iter_lines_with_fence_state(text):
            for placeholder in TEMPLATE_PLACEHOLDERS:
                if placeholder in line:
                    fail(report, f"{p.name}:{i}: unreplaced template placeholder '{placeholder}'")
            if not in_fence and _EMPTY_TABLE_ROW_RE.match(line):
                fail(report, f"{p.name}:{i}: empty template table row")


def check_required_sections(doc_dir, main_name, report):
    """Verify non-empty ## sections and mandatory boundaries on Project/Active Module DESIGNs."""
    main_path = Path(doc_dir) / main_name
    main_is_product = False
    if main_path.exists():
        main_header = main_path.read_text(encoding="utf-8").split("##")[0]
        main_is_product = bool(re.search(r"^> \*\*Product Intent\*\*:", main_header, re.M))

    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        header = text.split("##")[0]
        sections = []
        current = None
        for i, line, in_fence in _iter_lines_with_fence_state(text):
            if not in_fence:
                m = _H2_RE.match(line)
                if m:
                    current = {"line": i, "heading": m.group(1).strip(), "body": []}
                    sections.append(current)
                    continue
            if current is not None:
                current["body"].append((line, in_fence))

        h2_names = set()
        for sec in sections:
            h2_names.add(sec["heading"])
            meaningful = []
            for body_line, in_fence in sec["body"]:
                stripped = body_line.strip()
                if not stripped or stripped == "---":
                    continue
                meaningful.append((stripped, in_fence))
            has_non_heading_content = any(
                in_fence or not _H3_PLUS_RE.match(line) for line, in_fence in meaningful
            )
            if not has_non_heading_content:
                fail(report, f"{p.name}:{sec['line']}: empty section '## {sec['heading']}' has no content")

        has_parent_arch = bool(re.search(r"^> \*\*Parent Architecture\*\*:", header, re.M))
        has_parent = bool(re.search(r"^> \*\*Parent\*\*:", header, re.M))
        status_m = _STATUS_RE.search(header)
        status_val = status_m.group(1).strip() if status_m else ""

        if p.name == main_name and has_parent_arch and not has_parent:
            if "Module Architecture" not in h2_names:
                fail(report, f"{p.name}: missing required '## Module Architecture' section")
            if not ({"Business Rules and Failure Boundaries", "Business Rules & Failure Boundaries"} & h2_names):
                fail(report, f"{p.name}: missing required '## Business Rules and Failure Boundaries' section")
        elif p.name != main_name and p.name.startswith("DESIGN-") and not main_is_product:
            if has_parent and has_parent_arch and status_val == "Active":
                if not ({"Business Rules and Failure Boundaries", "Business Rules & Failure Boundaries"} & h2_names):
                    fail(report, f"{p.name}: missing required '## Business Rules and Failure Boundaries' section")


def check_process_state(doc_dir, report):
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        for term in PROCESS_STATE_TERMS:
            if term in text:
                fail(report, f"{p.name}: process-state term '{term}'")


def check_updated_dates(doc_dir, report):
    date_re = re.compile(r"20\d\d-\d\d-\d\d")
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        if not date_re.search(text):
            fail(report, f"{p.name}: no Updated date found")


# Field names allowed in a document header. English only: a localized field
# name would force every consumer (script and reader alike) to carry both
# vocabularies, which is exactly the ambiguity this rule removes.
ALLOWED_HEADER_FIELDS = {
    "Status", "Updated", "Parent", "Parent Architecture", "Parent Product",
    "Product Intent", "Sibling DESIGNs", "Sub-DESIGNs", "Sub-PRs", "Sub-PRDs",
    "Companion Documents", "Design Source", "Companion", "Scope",
    "Product PRD", "Product DESIGN", "Phase ID", "Product",
}
# Status values a design document may carry. Draft (`Draft` / `Proposed`)
# indicates a work in progress; `Active` indicates a live, verified contract.
# Design docs never carry a `Completed` state.
ALLOWED_STATUS_VALUES = {"Draft", "Proposed", "Active"}
_STATUS_RE = re.compile(r"^> \*\*Status\*\*:\s*([A-Za-z ]+?)\s*$", re.M)
# Fields whose value must be a document link, checked for resolvability.
LINK_FIELDS = {"Parent Architecture", "Parent Product", "Product Intent",
               "Product PRD", "Product DESIGN", "Design Source"}
_FIELD_RE = re.compile(r"^> \*\*([^*]+)\*\*:", re.M)


def check_header_fields(doc_dir, report):
    """Header field names come from one fixed English vocabulary.

    A document that invents a field name, or writes one in a localized form,
    makes its header unreadable to tooling and inconsistent with its siblings.
    The header is metadata; its field names are part of the contract, not part
    of the prose.
    """
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        header = text.split("##")[0]
        for m in _FIELD_RE.finditer(header):
            field = m.group(1).strip()
            if field not in ALLOWED_HEADER_FIELDS:
                fail(report, f"{p.name}: unknown header field '{field}'")


def check_status_values(doc_dir, report):
    """A design document's Status is one of the lifecycle values.

    The lifecycle has exactly two classes: draft (`Draft` / `Proposed`) and
    formal (`Active`). A value outside the set — including a retired one such
    as `Target Shape`, or `Completed`, which is a Plan state rather than a
    design state — leaves the document unclassifiable, so no consumer can tell
    whether its target shape is settled.
    """
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        header = text.split("##")[0]
        m = _STATUS_RE.search(header)
        if not m:
            fail(report, f"{p.name}: header missing 'Status' field")
            continue
        value = m.group(1).strip()
        if value not in ALLOWED_STATUS_VALUES:
            fail(report, f"{p.name}: unknown Status value '{value}' "
                         f"(use {' / '.join(sorted(ALLOWED_STATUS_VALUES))})")


def _git_nul_paths(git_root, args):
    """Run git command with NUL-delimited path output; return normalized POSIX paths or None on failure."""
    res = subprocess.run(
        ["git", "-C", str(git_root), "-c", "core.fsmonitor=false", *args],
        capture_output=True,
    )
    if res.returncode != 0:
        return None
    paths = []
    for raw in res.stdout.split(b"\x00"):
        if raw:
            paths.append(raw.decode("utf-8", errors="replace").replace("\\", "/"))
    return paths


def _collect_git_modified_paths(doc_dir, base_ref):
    """Locate enclosing Git repo and collect changed repository-relative paths."""
    top = subprocess.run(
        ["git", "-C", str(doc_dir), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if top.returncode != 0:
        return None, None

    git_root = Path(top.stdout.strip()).resolve()
    changed = set()

    staged = _git_nul_paths(git_root, ["diff", "--cached", "--no-renames", "--name-only", "-z", "--"]) or []
    unstaged = _git_nul_paths(git_root, ["diff", "--no-renames", "--name-only", "-z", "--"]) or []
    untracked = _git_nul_paths(git_root, ["ls-files", "--others", "--exclude-standard", "-z", "--"]) or []

    if base_ref:
        committed = _git_nul_paths(git_root, ["diff", "--no-renames", "--name-only", "-z", f"{base_ref}...HEAD", "--"])
        if committed is None:
            committed = _git_nul_paths(git_root, ["diff", "--no-renames", "--name-only", "-z", f"{base_ref}..HEAD", "--"]) or []
        changed.update(committed)
        changed.update(staged)
        changed.update(unstaged)
        changed.update(untracked)
    else:
        changed.update(staged)
        changed.update(unstaged)
        changed.update(untracked)
        if not changed:
            prev = _git_nul_paths(git_root, ["diff", "--no-renames", "--name-only", "-z", "HEAD~1..HEAD", "--"])
            if prev is None:
                prev = _git_nul_paths(git_root, ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"]) or []
            changed.update(prev)

    return git_root, sorted(changed)


def _parse_module_carriers(main_path, main_name):
    """Extract (carrier_prefixes, owning_doc) mappings from ## Module Architecture table."""
    if not main_path.exists():
        return []

    text = main_path.read_text(encoding="utf-8")
    in_section = False
    section_lines = []
    for _, line, in_fence in _iter_lines_with_fence_state(text):
        if not in_fence:
            h2 = _H2_RE.match(line)
            if h2:
                if in_section:
                    break
                if h2.group(1).strip() == "Module Architecture":
                    in_section = True
                continue
        if in_section and not in_fence:
            section_lines.append(line)

    md_link_re = re.compile(r"\]\(([^)#\s]+?)(?:#[^)]*)?\)")
    rows = []
    headers = None
    carrier_idx = None
    sub_idx = None

    for raw in section_lines:
        line = raw.strip()
        if not line.startswith("|"):
            if headers is not None and not line:
                continue
            elif headers is not None:
                break
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c.replace(" ", "")) or not c for c in cells):
            continue

        if headers is None:
            headers = [c.lower() for c in cells]
            for idx, name in enumerate(headers):
                if "source carrier" in name or "carrier" in name:
                    carrier_idx = idx
                elif "sub-design" in name:
                    sub_idx = idx
            continue

        if carrier_idx is None or carrier_idx >= len(cells):
            continue

        carrier_cell = cells[carrier_idx]
        if not carrier_cell or carrier_cell in ("-", "N/A", "`N/A`", "`<path>`", "<path>"):
            continue

        carriers = re.findall(r"`([^`]+)`", carrier_cell)
        if not carriers:
            carriers = [part.strip() for part in re.split(r"[,;]", carrier_cell) if part.strip()]
        carriers = [
            c.lstrip("./").rstrip("/")
            for c in carriers
            if c and c not in ("-", "N/A", "<path>")
        ]
        if not carriers:
            continue

        owning_doc = main_name
        if sub_idx is not None and sub_idx < len(cells):
            sub_cell = cells[sub_idx]
            m = md_link_re.search(sub_cell)
            if m:
                candidate = Path(m.group(1)).name
                if candidate.endswith(".md"):
                    owning_doc = candidate
            else:
                m2 = _LINK_RE.search(sub_cell)
                if m2:
                    candidate = Path(m2.group(1) or m2.group(2)).name
                    if candidate.endswith(".md"):
                        owning_doc = candidate

        rows.append((carriers, owning_doc))

    return rows


def check_doc_sync(doc_dir, main_name, base_ref, pure_refactor, report):
    """Map changed non-test code files to owning DESIGNs via Module Architecture Source Carriers."""
    git_root, modified_git_paths = _collect_git_modified_paths(doc_dir, base_ref)
    if git_root is None:
        fail(report, "doc-sync: --check-sync requires a Git repository")
        return

    project_root = Path(doc_dir).resolve().parent
    try:
        project_rel = project_root.relative_to(git_root).as_posix()
    except ValueError:
        project_rel = "."

    try:
        doc_dir_rel = Path(doc_dir).resolve().relative_to(git_root).as_posix()
    except ValueError:
        doc_dir_rel = "docs"

    modified_set = set(modified_git_paths)
    project_code_files = []
    for git_path in modified_git_paths:
        if project_rel == ".":
            proj_path = git_path
        elif git_path.startswith(project_rel + "/"):
            proj_path = git_path[len(project_rel) + 1:]
        else:
            continue

        if doc_dir_rel != "." and (git_path == doc_dir_rel or git_path.startswith(doc_dir_rel + "/")):
            continue
        if proj_path.startswith("docs/") or proj_path.endswith(".md"):
            continue
        if _TEST_PATH_RE.search(proj_path):
            continue
        project_code_files.append((git_path, proj_path))

    if not project_code_files:
        report.append("  OK: doc-sync skipped (no non-test code changes detected in scope)")
        return

    module_rows = _parse_module_carriers(Path(doc_dir) / main_name, main_name)
    triggered = []
    seen_docs = set()

    for git_path, proj_path in project_code_files:
        candidates = []
        for carriers, owning_doc in module_rows:
            for carrier in carriers:
                matches_git = git_path == carrier or git_path.startswith(carrier + "/")
                matches_proj = proj_path == carrier or proj_path.startswith(carrier + "/")
                if matches_git or matches_proj:
                    candidates.append((len(carrier), carrier, owning_doc, proj_path))
        if candidates:
            best_len = max(c[0] for c in candidates)
            for clen, carrier, owning_doc, sample_file in candidates:
                if clen == best_len and owning_doc not in seen_docs:
                    seen_docs.add(owning_doc)
                    triggered.append((carrier, owning_doc, sample_file))

    if not triggered:
        triggered.append((".", main_name, project_code_files[0][1]))

    for carrier, owning_doc, sample_file in triggered:
        expected_doc_rel = owning_doc if doc_dir_rel == "." else f"{doc_dir_rel}/{owning_doc}"
        if expected_doc_rel in modified_set:
            report.append(f"  OK: code changes in '{carrier}' synced with {owning_doc}")
        elif pure_refactor and pure_refactor.strip():
            report.append(
                f"  WARN: code under '{carrier}' changed without updating {owning_doc} "
                f"(pure-refactor declared: {pure_refactor.strip()}) — independent review must verify zero observable contract change"
            )
        else:
            fail(
                report,
                f"doc-sync: code under '{carrier}' ({sample_file}) changed but owning '{owning_doc}' "
                "was not updated (sync the doc or pass --pure-refactor '<reason>')",
            )


def _parse_args(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("doc_dir")
    parser.add_argument("--main", default="DESIGN.md")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--check-sync", action="store_true")
    parser.add_argument("--base", default=None)
    parser.add_argument("--pure-refactor", default=None)
    return parser.parse_args(argv)


def main():
    args_list = sys.argv[1:]
    if not args_list or args_list[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args_list else 2)

    try:
        opts = _parse_args(args_list)
    except SystemExit:
        print(__doc__)
        sys.exit(2)

    doc_dir = Path(opts.doc_dir).resolve()
    main_name = opts.main

    report = [f"Document set verification: {doc_dir}", "=" * 50]
    sub_files = discover_subdesigns(doc_dir, main_name, report)
    check_sub_parent_links(doc_dir, main_name, sub_files, report)
    check_sub_body_reachability(doc_dir, main_name, sub_files, report)
    check_absolute_paths(doc_dir, report)
    check_relative_links(doc_dir, report)
    check_end_section(doc_dir, main_name, sub_files, report)
    check_template_placeholders(doc_dir, report)
    check_required_sections(doc_dir, main_name, report)
    check_process_state(doc_dir, report)
    check_updated_dates(doc_dir, report)
    check_header_fields(doc_dir, report)
    check_status_values(doc_dir, report)
    if opts.check_sync:
        check_doc_sync(doc_dir, main_name, opts.base, opts.pure_refactor, report)

    print("\n".join(report))
    failed = any("FAIL:" in line for line in report)
    print("=" * 50)
    print("RESULT:", "FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
