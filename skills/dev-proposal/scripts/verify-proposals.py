#!/usr/bin/env python3
"""Verify a Business Proposal tree against the dev-proposal contract.

Usage:
  python3 verify-proposals.py <proposals-root> [--json]
                              [--link-scope <docs-dir>]...

The root may be the `proposals/` directory itself or any directory that holds
one (for example a project's `docs/`); `<dir>/proposals` is used when present.

Single-snapshot, static, deterministic checks only:

  1. Layout: `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md` under the closed
     lifecycles `proposed | implemented | rejected | archived` and the closed
     classes `feature | bug-fix | simplification | architecture | process |
     testing`. Rejects a singular `proposal/` directory, unknown class
     directories, a centralized `INDEX.md`, and an `archived/implemented/`
     nesting.
  2. Status agreement: `proposed`/`approved` only in `proposed/`;
     `implemented` only in `implemented/` or an `archived/` record that carries
     `Archived: YYYY-MM-DD`; `rejected — <reason>` only in `rejected/`.
  3. Skeleton: the future-tense sections in `proposed/`, the present-tense
     sections in `implemented/` with planning-era headings forbidden, and the
     proposal-time sections in `rejected/`. Active records use the Design
     Basis skeleton. Archived bodies are frozen and not checked.
  4. Authorization: `Status: approved` carries `Approved`, `Authorized scope`
     and `Delivery: direct | plan`, with a real calendar date and a named
     approver. This checks shape only; it can never prove that a human approved
     anything.
  5. Links: relative outbound links resolve inside a non-frozen tree, with no
     local absolute paths. A path segment inside an HTTP(S) URL is a remote
     reference, not a local coordinate, so it is exempt. Archived records are
     excluded from both, because a frozen
     snapshot may legitimately point at paths that no longer exist. A broken
     inbound link from within the same tree is the same defect seen from the
     referring file, so it surfaces as that file's outbound error.
     Pass `--link-scope <docs-dir>` for each directory whose Markdown cites
     proposal paths (a project `docs/` directory, for example). Every `.md`
     under that scope is checked as a referring file too, so a link left
     dangling by a move or deletion is caught at its caller. A scope that does
     not exist is an error, not a silent skip.

Deliberately absent: a history database, a frozen-content hash manifest, Git
history rollback comparison, and cross-repository scans. Cross-commit rewinds
and archived-body tampering are guarded by the agent rules and normal review.

A parent directory is a valid entry point, so `<dir>/proposals` is used when
present. A competing singular `<dir>/proposal` is reported rather than ignored:
two roots in one project defeat the claim that the path is the index.

All Markdown in the proposal tree must follow the current layout and metadata.

Exit code 0 when clean, 1 on any issue, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

LIFECYCLES = ("proposed", "implemented", "rejected", "archived")
CLASSES = ("feature", "bug-fix", "simplification", "architecture", "process", "testing")

IMPLEMENTED_FORBIDDEN = ("Proposal", "Plan", "Migration plan", "Acceptance criteria")

REQUIRED_BY_LIFECYCLE = {
    "proposed": ("Problem", "Design Basis", "Proposal", "Acceptance criteria"),
    "implemented": ("Problem", "Design Basis", "Decision", "Consequences"),
    "rejected": ("Problem", "Design Basis", "Proposal"),
    "archived": (),
}
FORBIDDEN_BY_LIFECYCLE = {
    "proposed": (),
    "implemented": IMPLEMENTED_FORBIDDEN,
    "rejected": (),
    "archived": (),
}

ALLOWED_STATUS_BY_LIFECYCLE = {
    "proposed": ("proposed", "approved"),
    "implemented": ("implemented",),
    "rejected": ("rejected",),
    "archived": ("implemented",),
}

FIX_HINTS = {
    "LAYOUT_SINGULAR_DIR": "merge the singular 'proposal/' directory into 'proposals/<lifecycle>/<class>/'",
    "LAYOUT_INDEX_FILE": "delete the centralized index; the directory paths are the index",
    "LAYOUT_UNKNOWN_CLASS": "move the file under one of: " + ", ".join(CLASSES),
    "LAYOUT_UNKNOWN_LIFECYCLE": "move the file under one of: " + ", ".join(LIFECYCLES),
    "LAYOUT_ARCHIVED_NESTED": "archived records sit at 'archived/<class>/', with no 'implemented' level",
    "LAYOUT_BAD_FILENAME": "rename to '<yyyy-mm-dd-slug>.md' using the first-proposed date",
    "LAYOUT_SINGULAR_SIBLING": "merge or delete the singular 'proposal/' directory next to 'proposals/'",
    "LAYOUT_UNEXPECTED_PATH": "place the file at '{lifecycle}/{class}/yyyy-mm-dd-<slug>.md'",
    "STATUS_MISSING": "add a 'Status: <value>' line before the first '## ' heading",
    "STATUS_UNKNOWN_VALUE": "use 'proposed', 'approved', 'implemented', or 'rejected — <reason>'",
    "STATUS_DUPLICATE": "keep exactly one 'Status:' line before the first '## ' heading",
    "CREATED_MISSING": "add '- **Created**: <YYYY-MM-DD>' to the header block",
    "CREATED_BAD_DATE": "set 'Created' to a real calendar date as YYYY-MM-DD",
    "CLASS_MISSING": "add '- **Class**: <class>' matching the class directory",
    "STATUS_REJECTED_NO_REASON": "write 'Status: rejected — <one-line reason>'",
    "STATUS_PATH_MISMATCH": "align the Status value with the lifecycle directory that holds the file",
    "SKELETON_MISSING_SECTION": "add the required section for this lifecycle",
    "SKELETON_FORBIDDEN_SECTION": "remove the planning-era heading and fold it into '## Consequences'",
    "APPROVAL_MISSING": "add 'Approved', 'Authorized scope' and 'Delivery' before treating it as authorized",
    "APPROVAL_BAD_DELIVERY": "set 'Delivery' to 'direct' or 'plan'",
    "APPROVAL_BAD_DATE": "write '- **Approved**: YYYY-MM-DD \u2014 <approver>' with a real calendar date",
    "CLASS_FIELD_MISMATCH": "make the '**Class**' field match the class directory",
    "CLASS_UNKNOWN_VALUE": "set '**Class**' to one of: " + ", ".join(CLASSES),
    "ARCHIVE_MISSING_DATE": "insert 'Archived: YYYY-MM-DD' immediately below 'Status: implemented'",
    "ARCHIVE_DATE_MISPLACED": "move 'Archived: YYYY-MM-DD' to the line directly below 'Status: implemented'",
    "LINK_BROKEN_OUTBOUND": "fix or remove the relative link; repair inbound references when a file moved",
    "LINK_ABSOLUTE_PATH": "use a relative link instead of an absolute path",
    "LINK_SCOPE_MISSING": "pass an existing directory to --link-scope, or omit the flag",
}

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")
_STATUS_RE = re.compile(r"^Status:\s*(.*?)\s*$")
_CLASS_RE = re.compile(r"^- \*\*Class\*\*:\s*(.*?)\s*$")
_CREATED_RE = re.compile(r"^- \*\*Created\*\*:\s*(.*?)\s*$")
_DELIVERY_RE = re.compile(r"^- \*\*Delivery\*\*:\s*(.*?)\s*$")
_APPROVED_RE = re.compile(r"^- \*\*Approved\*\*:\s*(\S.*)$")
_APPROVED_FORMAT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*(?:\u2014|\u2013|---|--)\s*(\S.*?)\s*$")
_SCOPE_RE = re.compile(r"^- \*\*Authorized scope\*\*:\s*(\S.*)$")
_ARCHIVED_RE = re.compile(r"^Archived:\s*(\d{4}-\d{2}-\d{2})\s*$")
_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_MD_LINK_RE = re.compile(r"\]\(([^)#\s]+?)(?:#[^)]*)?\)")
_TICK_LINK_RE = re.compile(r"`((?:\.{1,2}/)[^`\s]*?\.md)`")
_ABSOLUTE_RE = re.compile(r"file:///|(?<![A-Za-z0-9_.$}~-])(?:/Users/|/Volumes/|/home/|/root/)")
_LINK_SCOPE_SKIP_DIRS = frozenset({"research", "references", "assets", "images"})
_URL_RE = re.compile(r"\b(?:https?://|mailto:)\S+")
_REJECT_REASON_RE = re.compile(r"^rejected\s*(?:—|-{1,2})\s*(\S.*)$")


class Report:
    def __init__(self) -> None:
        self.issues: list[dict] = []
        self.files = 0
        self.scanned: set[Path] = set()

    def add(self, code: str, path: Path, message: str, line: int | None = None) -> None:
        self.issues.append(
            {
                "code": code,
                "path": str(path),
                "line": line,
                "message": message,
                "fix": FIX_HINTS.get(code, ""),
            }
        )

    def as_dict(self) -> dict:
        return {
            "verdict": "FAIL" if self.issues else "PASS",
            "counts": {
                "files": self.files,
                "errors": len(self.issues),
            },
            "issues": self.issues,
        }


def _header_boundary(text: str) -> int:
    """Index of the first `## ` heading line, or the text length."""
    offset = 0
    for line in text.splitlines(keepends=True):
        if _H2_RE.match(line.rstrip("\n")):
            return offset
        offset += len(line)
    return len(text)


def _fence_aware_lines(text: str):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = _FENCE_RE.match(line)
        if marker:
            char = marker.group(1)[0]
            if fence is None:
                fence = char
                yield number, line, True
                continue
            if fence == char:
                fence = None
                yield number, line, True
                continue
        yield number, line, fence is not None


def _h2_sections(text: str) -> list[str]:
    names = []
    for _, line, in_fence in _fence_aware_lines(text):
        if in_fence:
            continue
        match = _H2_RE.match(line)
        if match:
            names.append(match.group(1).strip())
    return names


def _line_of(text: str, pattern: re.Pattern) -> tuple[int | None, str | None]:
    for number, line, in_fence in _fence_aware_lines(text):
        if in_fence:
            continue
        match = pattern.match(line)
        if match:
            return number, match.group(1) if match.groups() else ""
    return None, None


def _all_lines_of(text: str, pattern: re.Pattern) -> list[tuple[int, str]]:
    """Every match, so a duplicated field cannot hide behind the first one."""
    hits = []
    for number, line, in_fence in _fence_aware_lines(text):
        if in_fence:
            continue
        match = pattern.match(line)
        if match:
            hits.append((number, match.group(1) if match.groups() else ""))
    return hits


def _is_real_date(value: str) -> bool:
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        return False
    return True


def _has_local_absolute_path(line: str) -> bool:
    """True when the line cites a local absolute path outside any URL.

    A URL path segment is not a local coordinate: `https://example.com/home/x`
    cites a remote document. Matching position-by-position rather than deleting
    URL text keeps a real `/home/...` citation that sits beside a remote link
    from being swallowed along with it.
    """
    spans = [match.span() for match in _URL_RE.finditer(line)]
    for match in _ABSOLUTE_RE.finditer(line):
        if not any(start <= match.start() < end for start, end in spans):
            return True
    return False


def _check_links(path: Path, text: str, report: Report) -> None:
    for number, line, in_fence in _fence_aware_lines(text):
        if in_fence:
            continue
        if _has_local_absolute_path(line):
            report.add("LINK_ABSOLUTE_PATH", path, f"absolute path in: {line.strip()[:80]}", number)
            continue
        targets = list(_MD_LINK_RE.findall(line)) + list(_TICK_LINK_RE.findall(line))
        for target in targets:
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("/"):
                report.add("LINK_ABSOLUTE_PATH", path, f"absolute link target: {target}", number)
                continue
            if "://" in target or "*" in target:
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                report.add("LINK_BROKEN_OUTBOUND", path, f"broken relative link: {target}", number)


def _check_link_scope(scope: Path, report: Report, seen: set[Path]) -> None:
    """Check every Markdown file in a referring directory for broken links.

    The proposal tree only sees its own files. A design document one level up
    can cite a proposal that was later moved or deleted; without this scan the
    dangling link survives until a human notices. Files already covered by the
    tree scan are skipped so one defect is not reported twice, and historical
    research/reference subdirectories are skipped unless targeted directly.
    """
    for path in sorted(scope.rglob("*.md")):
        rel_parts = path.relative_to(scope).parts[:-1]
        if any(part in _LINK_SCOPE_SKIP_DIRS for part in rel_parts):
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        _check_links(path, path.read_text(encoding="utf-8"), report)


def _check_skeleton(path: Path, text: str, lifecycle: str, report: Report) -> None:
    if lifecycle == "archived":
        return
    present = _h2_sections(text)
    required = REQUIRED_BY_LIFECYCLE[lifecycle]
    for name in required:
        if name not in present:
            report.add("SKELETON_MISSING_SECTION", path, f"missing required section '## {name}'")
    for name in FORBIDDEN_BY_LIFECYCLE[lifecycle]:
        if name in present:
            report.add("SKELETON_FORBIDDEN_SECTION", path, f"forbidden planning-era section '## {name}'")


def _check_authorization(path: Path, header: str, status: str, report: Report) -> None:
    if status != "approved":
        return
    checks = (
        ("Approved", _APPROVED_RE, "missing '- **Approved**: <date> — <approver>'"),
        ("Authorized scope", _SCOPE_RE, "missing '- **Authorized scope**: <approved scope>'; a scope with no boundary approves nothing"),
        ("Delivery", _DELIVERY_RE, "missing '- **Delivery**: direct | plan'"),
    )
    for _, pattern, message in checks:
        found = False
        for number, line, in_fence in _fence_aware_lines(header):
            if in_fence:
                continue
            if pattern.match(line):
                found = True
                break
        if not found:
            report.add("APPROVAL_MISSING", path, message)
    delivery_line, delivery = _line_of(header, _DELIVERY_RE)
    if delivery is not None and delivery not in ("direct", "plan"):
        report.add(
            "APPROVAL_BAD_DELIVERY",
            path,
            f"'Delivery' must be 'direct' or 'plan', found '{delivery}'",
            delivery_line,
        )

    approved_line, approved = _line_of(header, _APPROVED_RE)
    if approved is not None:
        # Shape only. A well-formed record still proves nothing about consent;
        # that lives in the conversation, never in this file.
        match = _APPROVED_FORMAT_RE.match(approved)
        if match is None or not _is_real_date(match.group(1)):
            report.add(
                "APPROVAL_BAD_DATE",
                path,
                "'Approved' needs a real 'YYYY-MM-DD — <approver>' value, "
                f"found '{approved}'",
                approved_line,
            )


def _archived_date_is_adjacent(text: str, status_line: int | None) -> bool:
    """`Archived: YYYY-MM-DD` must sit on the line right below `Status: implemented`.

    Archiving writes exactly one line and nothing else, so the pair is the
    frozen metadata stamp. A date somewhere else in the header is a different
    claim, not a cosmetic difference.
    """
    if status_line is None:
        return False
    lines = text.splitlines()
    index = status_line  # 0-based position of the following line
    if index >= len(lines):
        return False
    match = _ARCHIVED_RE.match(lines[index])
    return bool(match) and _is_real_date(match.group(1))


def inspect_file(path: Path, lifecycle: str, class_dir: str, report: Report) -> None:
    report.scanned.add(path.resolve())
    text = path.read_text(encoding="utf-8")
    header = text[: _header_boundary(text)]

    status_hits = _all_lines_of(header, _STATUS_RE)
    status_line, status = status_hits[0] if status_hits else (None, None)
    class_line, class_value = _line_of(header, _CLASS_RE)
    created_line, created_value = _line_of(header, _CREATED_RE)

    report.files += 1

    if status_line is None:
        report.add("STATUS_MISSING", path, "no 'Status:' line in the header block")
        status = ""
    elif len(status_hits) > 1:
        report.add(
            "STATUS_DUPLICATE",
            path,
            f"{len(status_hits)} 'Status:' lines in the header; a record has exactly one state",
            status_hits[1][0],
        )
    elif status not in ("proposed", "approved", "implemented") and not status.startswith("rejected"):
        report.add(
            "STATUS_UNKNOWN_VALUE",
            path,
            f"unknown Status value '{status}'",
            status_line,
        )
        status = ""

    if status.startswith("rejected"):
        if not _REJECT_REASON_RE.match(status):
            report.add(
                "STATUS_REJECTED_NO_REASON",
                path,
                "a rejected proposal needs 'Status: rejected — <one-line reason>'",
                status_line,
            )

    normalized = "rejected" if status.startswith("rejected") else status
    allowed = ALLOWED_STATUS_BY_LIFECYCLE[lifecycle]
    if normalized and normalized not in allowed:
        report.add(
            "STATUS_PATH_MISMATCH",
            path,
            f"Status '{normalized}' is not allowed under '{lifecycle}/' "
            f"(allowed: {', '.join(allowed)})",
            status_line,
        )

    if class_value is None:
        report.add(
            "CLASS_MISSING",
            path,
            "no '- **Class**: <class>' field; without it the class check has nothing to compare",
        )
    elif class_value not in CLASSES:
        report.add("CLASS_UNKNOWN_VALUE", path, f"unknown Class value '{class_value}'", class_line)
    elif class_dir and class_value != class_dir:
        report.add(
            "CLASS_FIELD_MISMATCH",
            path,
            f"Class '{class_value}' does not match directory '{class_dir}'",
            class_line,
        )

    if created_value is None:
        report.add("CREATED_MISSING", path, "no '- **Created**: <YYYY-MM-DD>' field")
    elif not _is_real_date(created_value):
        report.add(
            "CREATED_BAD_DATE",
            path,
            f"'Created' must be a real date as YYYY-MM-DD, found '{created_value}'",
            created_line,
        )

    if lifecycle == "archived":
        if not _archived_date_is_adjacent(text, status_line):
            report.add(
                "ARCHIVE_MISSING_DATE"
                if _line_of(header, _ARCHIVED_RE)[0] is None
                else "ARCHIVE_DATE_MISPLACED",
                path,
                "archived record needs 'Archived: YYYY-MM-DD' on the line "
                "directly below 'Status: implemented'",
            )
        return

    _check_skeleton(path, text, lifecycle, report)
    _check_authorization(path, header, normalized, report)
    _check_links(path, text, report)


def inspect_lifecycle_dir(root: Path, lifecycle: str, report: Report) -> None:
    base = root / lifecycle
    for path in sorted(base.rglob("*.md")):
        parts = path.relative_to(base).parts

        if lifecycle == "archived" and parts and parts[0] == "implemented":
            report.add(
                "LAYOUT_ARCHIVED_NESTED",
                path,
                f"archived records carry no 'implemented' level: {path.relative_to(root)}",
            )
            continue

        if len(parts) != 2:
            report.add(
                "LAYOUT_UNEXPECTED_PATH",
                path,
                f"expected '{lifecycle}/<class>/<yyyy-mm-dd-slug>.md', found "
                f"'{path.relative_to(root)}'",
            )
            continue

        class_dir, filename = parts
        if class_dir not in CLASSES:
            report.add(
                "LAYOUT_UNKNOWN_CLASS",
                path,
                f"unknown class directory '{class_dir}'",
            )
            continue

        filename_match = _FILENAME_RE.match(filename)
        if filename_match is None:
            report.add(
                "LAYOUT_BAD_FILENAME",
                path,
                f"filename '{filename}' must be '<yyyy-mm-dd-slug>.md'",
            )
        elif not _is_real_date(filename_match.group(1)):
            report.add(
                "LAYOUT_BAD_FILENAME",
                path,
                f"filename date '{filename_match.group(1)}' is not a real calendar date",
            )

        inspect_file(path, lifecycle, class_dir, report)


def inspect_tree(root: Path, report: Report) -> None:
    for entry in sorted(root.iterdir()):
        if entry.name == "INDEX.md":
            report.add(
                "LAYOUT_INDEX_FILE",
                entry,
                "a centralized INDEX.md duplicates the directory layout",
            )
            continue
        if not entry.is_dir():
            if entry.suffix == ".md":
                report.add("LAYOUT_UNEXPECTED_PATH", entry,
                           "Markdown proposal must be inside a lifecycle and class directory")
            continue

        if entry.name == "proposal":
            for path in sorted(entry.rglob("*.md")):
                report.add(
                    "LAYOUT_SINGULAR_DIR",
                    path,
                    f"singular 'proposal/' directory must be 'proposals/': {path.relative_to(root)}",
                )
            continue

        if entry.name not in LIFECYCLES:
            for path in sorted(entry.rglob("*.md")):
                report.add(
                    "LAYOUT_UNKNOWN_LIFECYCLE",
                    path,
                    f"unknown lifecycle directory '{entry.name}'",
                )
            continue

        inspect_lifecycle_dir(root, entry.name, report)


def _resolve_root(raw: str) -> tuple[Path | None, Path | None]:
    """Resolve the tree root, reporting a competing singular sibling.

    A parent directory is a documented entry point: pass `docs/` and the tree at
    `docs/proposals/` is used. That convenience must not hide a second, competing
    root at `docs/proposal/`, which would leave two indexes in one project.
    """
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        return None, None
    if root.name != "proposals" and (root / "proposals").is_dir():
        sibling = root / "proposal"
        return root / "proposals", (sibling if sibling.is_dir() else None)
    return root, None


def _print_human(report: Report, root: Path) -> None:
    data = report.as_dict()
    print(f"Proposal tree verification: {root}")
    print("=" * 60)
    print(f"  Files checked: {data['counts']['files']}")
    for issue in report.issues:
        location = issue["path"] if issue["line"] is None else f"{issue['path']}:{issue['line']}"
        print(f"  FAIL: [{issue['code']}] {location}: {issue['message']}")
        if issue["fix"]:
            print(f"        fix: {issue['fix']}")
    if not report.issues:
        print("  OK: layout, status, skeleton, authorization, archive metadata and links all agree")
    print("=" * 60)
    print("RESULT:", data["verdict"])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="verify-proposals.py",
        description="Verify a Business Proposal tree (single-snapshot static checks).",
    )
    parser.add_argument("root", help="proposals root, or a directory containing one")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    parser.add_argument(
        "--link-scope",
        action="append",
        default=[],
        metavar="DIR",
        help="extra directory whose Markdown may cite proposal paths (repeatable)",
    )
    args = parser.parse_args(argv)

    root, singular_sibling = _resolve_root(args.root)
    if root is None:
        message = f"root not found or not a directory: {args.root}"
        if args.as_json:
            print(json.dumps({"verdict": "FAIL", "counts": {"files": 0, "errors": 1},
                              "issues": [{"code": "ROOT_MISSING", "path": args.root, "line": None,
                                          "message": message, "fix": "pass the proposals directory"}]}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        return 2

    report = Report()
    if singular_sibling is not None:
        for path in sorted(singular_sibling.rglob("*.md")):
            report.add(
                "LAYOUT_SINGULAR_SIBLING",
                path,
                f"singular 'proposal/' sits next to 'proposals/': "
                f"{path.relative_to(singular_sibling.parent)}",
            )
    inspect_tree(root, report)

    for raw_scope in args.link_scope:
        scope = Path(raw_scope).expanduser().resolve()
        if not scope.is_dir():
            report.add(
                "LINK_SCOPE_MISSING",
                scope,
                f"--link-scope directory not found: {raw_scope}",
            )
            continue
        _check_link_scope(scope, report, report.scanned)

    if args.as_json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        _print_human(report, root)
    return 1 if report.issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
