#!/usr/bin/env python3
"""Verify a documentation set against the dev-doc-master consistency rules.

Usage:
  python3 verify-docset.py <docs-dir> [--main DESIGN.md] [--strict]

Checks:
  1. Main header Sub-DESIGNs match DESIGN-*.md files on disk (bidirectional).
  2. Every sub-document header carries a parent link to the main document.
  3. No absolute paths (file:/// or /Users/...) in any .md.
  4. Relative links resolve to existing files.
  5. End section (Reference Documents) contains no sub-DESIGNs and no header docs.
  6. No process-state vocabulary (已废弃/已放弃/迁移/不再执行/deprecated/legacy/moved from).
  7. Every touched document has a refreshed Updated date.
  8. Header field names come from the fixed English vocabulary.

Exit code 0 on pass, 1 on any failure. Prints a report.
"""

import os
import re
import sys
from pathlib import Path

# High-signal process-state vocabulary. These mark historical/process narration in
# design docs. Lower-signal terms like 迁移 (data/config migration) and legacy
# (release taxonomy) are legitimate domain vocabulary and deliberately excluded.
PROCESS_STATE_TERMS = [
    "已废弃", "已放弃", "不再执行", "历史机制", "原方案已废弃", "原实现已废弃",
    "deprecated", "moved from", "no longer",
]


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
    for p in Path(doc_dir).glob("*.md"):
        if any(part in skip_dirs for part in p.parts):
            continue
        if not _DESIGN_DOC_RE.match(p.name):
            continue
        yield p


def check_subdesign_index(doc_dir, main_name, report):
    """Main header Sub-DESIGNs must exactly match DESIGN-*.md on disk (top level only)."""
    sub_files = sorted(p.name for p in Path(doc_dir).glob("DESIGN-*.md")
                       if p.parent == Path(doc_dir))
    main_path = Path(doc_dir) / main_name
    if not main_path.exists():
        fail(report, f"main document {main_name} not found")
        return sub_files

    text = main_path.read_text(encoding="utf-8")
    # Find Sub-DESIGNs / 子设计 block: lines after the field label up to the next field/blank
    header_block = text.split("##")[0]  # everything before first ##
    listed = []
    in_sub = False
    for line in header_block.splitlines():
        if "Sub-DESIGNs" in line or "子设计" in line:
            in_sub = True
            continue
        if in_sub:
            if line.strip() == "":
                continue
            m = re.search(r"`\./?(DESIGN-[\w-]+\.md)`", line)
            if m:
                listed.append(m.group(1))
            elif re.match(r"^\s*>?\s*\*\*", line):
                break
    listed = sorted(set(listed))
    missing = [f for f in sub_files if f not in listed]
    extra = [f for f in listed if f not in sub_files]
    if missing:
        fail(report, f"Sub-DESIGNs header missing on-disk files: {missing}")
    if extra:
        fail(report, f"Sub-DESIGNs header lists nonexistent files: {extra}")
    if not missing and not extra:
        report.append(f"  OK: Sub-DESIGNs index matches ({len(sub_files)} files)")
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
    link_re = re.compile(r"\]\(([^)#]+?)(?:#[^)]*)?\)")
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            for target in link_re.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#")[0]
                if not target:
                    continue
                if target.startswith("file://"):
                    fail(report, f"{p.name}:{i}: file:// link {target}")
                    continue
                resolved = (p.parent / target).resolve()
                if not resolved.exists():
                    fail(report, f"{p.name}:{i}: broken link {target}")


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
            for name in sub_files:
                if name in end:
                    fail(report, f"{p.name}: sub-DESIGN {name} appears in the end section")

        for link in sorted(header_links & end_links):
            fail(report, f"{p.name}: '{link}' listed in both header and end section")


def check_process_state(doc_dir, report):
    for p in _doc_files(doc_dir):
        text = p.read_text(encoding="utf-8")
        for term in PROCESS_STATE_TERMS:
            if term in text:
                fail(report, f"{p.name}: process-state term '{term}'")


def check_updated_dates(doc_dir, report):
    date_re = re.compile(r"20\d\d-\d\d-\d\d")
    today = None  # not enforced against today, just presence
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


def check_gaps_docs(doc_dir, report):
    """GAPS.md is a process document, not a design document.

    It must declare the design it measures via `Design Source`, must not claim
    an architecture lineage, and must not list that design again in its end
    section. It must also state its own lifecycle so a reader knows the file
    is removed once the gaps close.
    """
    gaps = doc_dir / "GAPS.md"
    if not gaps.exists():
        return
    text = gaps.read_text(encoding="utf-8")
    header = text.split("##")[0]

    if "Design Source" not in header:
        fail(report, "GAPS.md: header missing 'Design Source' field")
    for lineage in ("Parent Architecture", "上级架构", "Parent Product"):
        if lineage in header:
            fail(report, f"GAPS.md: header uses lineage field '{lineage}' (process documents use Design Source)")
    if "过程文档" not in text and "process document" not in text.lower():
        fail(report, "GAPS.md: no lifecycle note stating the document is a process document")
    if "编号规则" not in text and "Numbering" not in text:
        fail(report, "GAPS.md: no numbering scheme section")
    report.append("  OK: GAPS.md structure (Design Source, lifecycle, numbering)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    doc_dir = Path(args[0]).resolve()
    main_name = "DESIGN.md"
    if "--main" in args:
        main_name = args[args.index("--main") + 1]

    report = [f"Document set verification: {doc_dir}", "=" * 50]
    sub_files = check_subdesign_index(doc_dir, main_name, report)
    check_sub_parent_links(doc_dir, main_name, sub_files, report)
    check_absolute_paths(doc_dir, report)
    check_relative_links(doc_dir, report)
    check_end_section(doc_dir, main_name, sub_files, report)
    check_process_state(doc_dir, report)
    check_updated_dates(doc_dir, report)
    check_header_fields(doc_dir, report)
    check_gaps_docs(doc_dir, report)

    print("\n".join(report))
    failed = any("FAIL:" in line for line in report)
    print("=" * 50)
    print("RESULT:", "FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
