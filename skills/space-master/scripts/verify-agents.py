#!/usr/bin/env python3
"""Verify an AGENTS.md tree against the mechanically checkable parts of the
space-master agent-rules maintenance standard.

Usage:
  python3 verify-agents.py <project-AGENTS.md> [--base <git-ref>] [--strict]

Checks:
  1. frontmatter carries name, description and maintenance.
  2. No unreplaced template placeholders and no `N/A` placeholders.
  3. No chapter numbering in headings (`## 1. ...`).
  4. Line count stays inside the tier limit (project root 300, docs/ 80, module 100).
  5. Every backticked path-like reference exists in the repository.
  6. A localized sibling `AGENTS.<locale>.md` carries the same headings.
  7. ... the same section skeleton, section by section.
  8. ... the same rule count in every section.
  9. ... the same inline-code identifier set.
 10. `User-Supplied Rules` is untouched (--base only).
 11. Nested AGENTS.md files below this one do not duplicate a parent rule verbatim.

What this script deliberately does not judge: whether a rule should exist at
all, whether it restates implementation, whether it conflicts with a DESIGN, or
whether it reads clearly. Those need semantic review and stay with the reviewer.

Exit code 0 on pass, 1 on any failure. Prints a report.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

TIER_LIMITS = {"project": 300, "docs": 80, "module": 100}

TEMPLATE_PLACEHOLDERS = (
    "<Project Name>",
    "<One-line stable description of the current project responsibility>",
    "<When this file should change",
    "<Brief current architecture description",
    "<module ownership and coding-style rule",
    "<canonical error type, stable fields and side-effect uncertainty rule>",
    "<State explicitly that this project inherits the space's canonical testing/TDD rule",
    "<unit test directory and command",
    "<reusable fixtures, contract helpers and isolation/cleanup rules",
    "<which host APIs, external systems, or real runtime boundaries require manual verification",
    "<Project-specific review checkpoints>",
    "<repository-specific checks that complement",
    "<user-supplied rules",
    "<path-when-relevant>",
    "<command>",
    "<failure condition>",
    "<doc-check command",
    "<broken links, orphan sub-DESIGNs",
)

CHAPTER_NUMBER = re.compile(r"^#{1,6}\s+\d+(?:\.\d+)*\.?\s")
INLINE_CODE = re.compile(r"`([^`\n]+)`")

# A backticked token counts as a path reference only when it is unambiguous:
# a repo-rooted path (contains a separator) or a real file extension. Bare file
# names, route-like fragments (auto/free), npm-style scopes (./...) and
# illustrative values are not existence-checked; mistaking them for paths
# produced mostly false positives.
PATH_CANDIDATE = re.compile(
    r"^(?:internal|cmd|docs|labs|projects|scripts|templates|references)/[\w./-]+$"
    r"|^[\w.-]+\.(?:go|py|ts|tsx|js|jsx|json|md|sh|ya?ml|toml|mod|sum)$"
)
# Repo-rooted trees that must exist for a path reference to be meaningful.
ROOTED_PREFIXES = ("internal/", "cmd/", "docs/", "labs/", "projects/", "scripts/", "templates/", "references/")


def fail(report, message):
    report.append(message)


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    block = text[4:end]
    fields = {}
    for line in block.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields, text[end + 5 :]


def split_sections(body):
    """Return an ordered list of (heading, rule_lines) for level-1/2 sections."""
    sections = []
    current = ("(preamble)", [])
    for line in body.splitlines():
        if re.match(r"^#{1,2}\s", line):
            sections.append(current)
            current = (line.strip(), [])
            continue
        current[1].append(line)
    sections.append(current)
    return [(heading, lines) for heading, lines in sections if heading != "(preamble)"]


def rule_count(lines):
    return sum(1 for line in lines if line.startswith("- "))


def headings_of(body):
    return [line.strip() for line in body.splitlines() if re.match(r"^#{1,6}\s", line)]


def tier_for(path):
    name, parent = path.name, path.parent.name
    if name != "AGENTS.md":
        return "module"
    if parent == "docs":
        return "docs"
    return "project"


def find_localized(main_path):
    stem = main_path.name[: -len(".md")]
    return sorted(p for p in main_path.parent.glob(f"{stem}.*.md") if p != main_path)


def check_single(report, path, text, fields, body, tier):
    for field in ("name", "description", "maintenance"):
        if not fields or not fields.get(field):
            fail(report, f"{path.name}: frontmatter is missing `{field}`")

    for marker in TEMPLATE_PLACEHOLDERS:
        if marker in text:
            fail(report, f"{path.name}: unreplaced template placeholder {marker!r}")
    # Only a placeholder value counts. Mentioning `N/A` while explaining a rule
    # is prose; a field filled with nothing but `N/A` is an unfilled slot.
    NA_PLACEHOLDER = re.compile(
        r"^\s*(?:[-*]\s*)?(?:[\w`][\w ./<>-]*:\s*)?(?:`N/A`|N/A)\s*$"
    )
    for line in body.splitlines():
        if NA_PLACEHOLDER.match(line):
            fail(report, f"{path.name}: contains an `N/A` placeholder: {line.strip()!r}")
    for heading in headings_of(body):
        if CHAPTER_NUMBER.match(heading):
            fail(report, f"{path.name}: chapter numbering in heading {heading!r}")

    limit = TIER_LIMITS[tier]
    total = len(text.splitlines())
    if total > limit:
        fail(report, f"{path.name}: {total} lines exceeds the {tier} limit of {limit}")


def check_paths(report, path, body, repo_root):
    if repo_root is None:
        return
    seen = set()
    for token in INLINE_CODE.findall(body):
        for piece in token.split():
            piece = piece.strip("()[],;:")
            if not piece or piece in seen or not PATH_CANDIDATE.match(piece):
                continue
            seen.add(piece)
            if "<" in piece or ">" in piece or "*" in piece:
                continue
            # Only repo-rooted trees are resolvable from the repository root.
            # Everything else is a relative or illustrative mention.
            scoped = piece.startswith(ROOTED_PREFIXES) or (
                path.parent / piece
            ).exists() or (repo_root / piece).exists()
            if not scoped:
                continue
            target = repo_root / piece.rstrip("/")
            if not target.exists():
                fail(report, f"{path.name}: reference to missing path `{piece}`")


def check_localized(report, main_path, main_body, localized):
    main_headings = headings_of(main_body)
    main_sections = dict(split_sections(main_body))
    for lpath in localized:
        raw = lpath.read_text(encoding="utf-8")
        _, lbody = parse_frontmatter(raw)
        local_headings = headings_of(lbody)
        if local_headings != main_headings:
            only_main = [h for h in main_headings if h not in local_headings]
            only_local = [h for h in local_headings if h not in main_headings]
            detail = []
            if only_main:
                detail.append(f"missing {only_main}")
            if only_local:
                detail.append(f"extra {only_local}")
            fail(
                report,
                f"{lpath.name}: headings differ from {main_path.name}"
                + (f" ({'; '.join(detail)})" if detail else ""),
            )
        for heading, lines in split_sections(lbody):
            if heading not in main_sections:
                continue
            expected = rule_count(main_sections[heading])
            actual = rule_count(lines)
            if expected != actual:
                fail(
                    report,
                    f"{lpath.name}: section {heading!r} has {actual} rules, {main_path.name} has {expected}",
                )
        main_code = set(INLINE_CODE.findall(main_body))
        local_code = set(INLINE_CODE.findall(lbody))
        missing = sorted(main_code - local_code)
        extra = sorted(local_code - main_code)
        if missing:
            fail(report, f"{lpath.name}: missing inline identifiers {missing}")
        if extra:
            fail(report, f"{lpath.name}: unexpected inline identifiers {extra}")


def git_show(repo_root, ref, rel_path):
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{ref}:{rel_path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def user_rules_block(body):
    match = re.search(r"^## User-Supplied Rules\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return match.group(1).strip() if match else None


def check_user_rules(report, path, body, base, repo_root):
    if not base or repo_root is None:
        return
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    previous = git_show(repo_root, base, rel)
    if previous is None:
        return
    _, prev_body = parse_frontmatter(previous)
    before = user_rules_block(prev_body)
    after = user_rules_block(body)
    if before is not None and after is not None and before != after:
        fail(report, f"{path.name}: `User-Supplied Rules` changed against {base}")


def check_duplication(report, main_path, main_body):
    """Flag a nested AGENTS.md that repeats a parent rule verbatim.

    A localized sibling is not a nested tier: its rules are translations of the
    same file, so comparing them would report every rule as duplication.
    """
    parent_rules = {
        line.strip()
        for _, lines in split_sections(main_body)
        for line in lines
        if len(line.strip()) > 40
    }
    for child in sorted(main_path.parent.rglob("*.md")):
        if not re.fullmatch(r"AGENTS(\.[\w-]{2,8})?\.md", child.name):
            continue
        if child.parent == main_path.parent:
            continue
        try:
            _, child_body = parse_frontmatter(child.read_text(encoding="utf-8"))
        except OSError:
            continue
        for heading, lines in split_sections(child_body):
            for line in lines:
                stripped = line.strip()
                if stripped in parent_rules:
                    fail(
                        report,
                        f"{child.name}: rule in {heading!r} duplicates the parent verbatim: {stripped[:60]}...",
                    )


def locate_repo_root(path):
    try:
        out = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Verify AGENTS.md against space-master standards.")
    parser.add_argument("path", help="path to the formal English AGENTS.md")
    parser.add_argument("--base", default=None, help="git ref to diff User-Supplied Rules against")
    parser.add_argument("--no-duplication", action="store_true", help="skip the nested-duplication scan")
    args = parser.parse_args()

    main_path = Path(args.path).resolve()
    if not main_path.is_file():
        print(f"verify-agents: not a file: {main_path}", file=sys.stderr)
        sys.exit(2)

    text = main_path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text)
    repo_root = locate_repo_root(main_path)
    tier = tier_for(main_path)
    report = []

    check_single(report, main_path, text, fields, body, tier)
    check_paths(report, main_path, body, repo_root)
    check_localized(report, main_path, body, find_localized(main_path))
    check_user_rules(report, main_path, body, args.base, repo_root)
    if not args.no_duplication:
        check_duplication(report, main_path, body)

    print(f"AGENTS verification: {main_path}")
    print("=" * 50)
    if report:
        for item in report:
            print(f"  FAIL: {item}")
        print("=" * 50)
        print(f"RESULT: FAIL ({len(report)} issue(s))")
        sys.exit(1)
    print(f"  OK: tier={tier}, {len(text.splitlines())} lines")
    print("=" * 50)
    print("RESULT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
