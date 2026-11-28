#!/usr/bin/env python3
"""Regression tests for verify-proposals.py.

Each test builds a throwaway proposal tree under a temporary directory, so the
suite never touches a real repository. Assertions target the observable
contract: the exit code, the machines-readable issue codes, and the fact that a
broken tree reports the specific defect rather than a generic failure.

Run: python3 skills/dev-proposal/scripts/test_verify_proposals.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "verify-proposals.py"

LIFECYCLES = ("proposed", "implemented", "rejected", "archived")
CLASSES = ("feature", "bug-fix", "simplification", "architecture", "process", "testing")

HEADER = """# {title}

{status_line}

- **Class**: {cls}
- **Created**: 2026-11-20
"""

APPROVAL = """- **Approved**: 2026-11-22 — owner
- **Authorized scope**: {scope}
- **Delivery**: {delivery}
"""

PROPOSED_BODY = """
## Problem

The current notification path imports three modules directly, so a fourth
consumer forces edits in three unrelated places and risks a cycle.

## Design Basis

Preserve existing module ownership and notification delivery semantics.

## Proposal

Route notifications through an in-process bus.

## Acceptance criteria

1. No notification path imports another module's notifier.
"""

IMPLEMENTED_BODY = """
## Problem

The current notification path imports three modules directly, so a fourth
consumer forces edits in three unrelated places and risks a cycle.

## Design Basis

Preserve existing module ownership and notification delivery semantics.

## Decision

Notifications go through an in-process bus. Producers publish, consumers
subscribe.

## Consequences

Adding a consumer now touches one module. Event names are an implicit contract
pinned by a test.
"""

REJECTED_BODY = """
## Problem

Occasional validation failures were suspected to be transient.

## Design Basis

Keep deterministic schema validation.

## Proposal

Retry schema validation three times.

## Acceptance criteria

1. A transient failure succeeds on retry.
"""


def proposal(
    title: str,
    status_line: str,
    cls: str = "architecture",
    body: str = PROPOSED_BODY,
    extra_header: str = "",
) -> str:
    header = HEADER.format(title=title, status_line=status_line, cls=cls)
    if extra_header:
        header += extra_header + "\n"
    return header + body


class Tree:
    """One throwaway proposal root."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="verify-proposals-"))

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root), *extra],
        capture_output=True,
        text=True,
    )


def codes(result: subprocess.CompletedProcess) -> list[str]:
    """Issue codes from --json output."""
    payload = json.loads(result.stdout)
    return [issue["code"] for issue in payload["issues"]]


class BaseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = Tree()
        self.addCleanup(self.tree.cleanup)

    def assertPass(self, *extra: str) -> subprocess.CompletedProcess:
        result = run(self.tree.root, *extra)
        self.assertEqual(
            result.returncode,
            0,
            msg=f"expected PASS, got exit {result.returncode}\n{result.stdout}\n{result.stderr}",
        )
        return result

    def assertFailsWith(self, code: str, *extra: str) -> subprocess.CompletedProcess:
        result = run(self.tree.root, "--json", *extra)
        self.assertNotEqual(result.returncode, 0, msg=f"expected failure for {code}\n{result.stdout}")
        seen = codes(result)
        self.assertIn(code, seen, msg=f"expected {code} in {seen}\n{result.stdout}")
        return result

    def assertFailsOnlyWith(self, code: str) -> subprocess.CompletedProcess:
        result = run(self.tree.root, "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(codes(result), [code], msg=result.stdout)
        return result


class LegalTreeTests(BaseCase):
    def test_full_lifecycle_tree_passes(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-event-bus.md",
                        proposal("Adopt an event bus", "Status: proposed"))
        self.tree.write(
            "proposed/feature/2026-11-21-scheduled-export.md",
            proposal(
                "Scheduled export",
                "Status: approved",
                cls="feature",
                extra_header=APPROVAL.format(scope="two reporting tables only", delivery="plan").strip(),
            ),
        )
        self.tree.write("implemented/architecture/2026-10-02-single-loader.md",
                        proposal("Single loader", "Status: implemented", body=IMPLEMENTED_BODY))
        self.tree.write(
            "archived/process/2026-09-01-weekly-release.md",
            proposal("Weekly release", "Status: implemented\nArchived: 2026-11-20",
                     cls="process", body=IMPLEMENTED_BODY),
        )
        self.tree.write("rejected/bug-fix/2026-11-15-retry.md",
                        proposal("Retry validation",
                                 "Status: rejected — parse errors are deterministic",
                                 cls="bug-fix", body=REJECTED_BODY))
        result = self.assertPass("--json")
        report = json.loads(result.stdout)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["counts"]["files"], 5)

    def test_every_class_directory_is_accepted(self) -> None:
        for cls in CLASSES:
            self.tree.write(f"proposed/{cls}/2026-11-20-proposal-{cls}.md",
                            proposal(f"Proposal {cls}", "Status: proposed", cls=cls))
        self.assertPass()

    def test_empty_root_passes(self) -> None:
        self.assertPass()

    def test_preformat_file_is_rejected(self) -> None:
        # A pre-format file: no header block, no skeleton, no Status line.
        self.tree.write("proposed/2026-01-05-legacy-style.md",
                        "# Legacy style\n\nJust a paragraph written before the format existed.\n")
        self.tree.write("proposed/architecture/2026-11-20-event-bus.md",
                        proposal("Adopt an event bus", "Status: proposed"))
        self.assertFailsWith("LAYOUT_UNEXPECTED_PATH")

    def test_partial_supersession_cross_links_pass(self) -> None:
        self.tree.write("implemented/architecture/2026-10-02-single-loader.md",
                        proposal("Single loader", "Status: implemented", body=IMPLEMENTED_BODY))
        self.tree.write(
            "proposed/simplification/2026-11-22-narrow-loader.md",
            proposal(
                "Narrow the loader",
                "Status: proposed",
                cls="simplification",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n",
                    "## Proposal\n\nPartly supersedes "
                    "[single-loader](../../implemented/architecture/2026-10-02-single-loader.md).\n",
                ),
            ),
        )
        self.assertPass()


class LayoutTests(BaseCase):
    def test_singular_proposal_directory_is_rejected(self) -> None:
        self.tree.write("proposal/feature/2026-11-20-x.md",
                        proposal("Singular dir", "Status: proposed"))
        self.assertFailsWith("LAYOUT_SINGULAR_DIR")

    def test_centralized_index_is_rejected(self) -> None:
        self.tree.write("INDEX.md", "# Index\n")
        self.assertFailsWith("LAYOUT_INDEX_FILE")

    def test_unknown_class_directory_is_rejected(self) -> None:
        self.tree.write("proposed/refactor/2026-11-20-x.md",
                        proposal("Unknown class", "Status: proposed", cls="refactor"))
        self.assertFailsWith("LAYOUT_UNKNOWN_CLASS")

    def test_filename_must_carry_stdio_date_prefix(self) -> None:
        self.tree.write("proposed/architecture/no-date-event-bus.md",
                        proposal("No date", "Status: proposed"))
        self.assertFailsWith("LAYOUT_BAD_FILENAME")

    def test_archived_must_not_nest_implemented(self) -> None:
        self.tree.write("archived/implemented/architecture/2026-10-02-x.md",
                        proposal("Nested", "Status: implemented", body=IMPLEMENTED_BODY))
        self.assertFailsWith("LAYOUT_ARCHIVED_NESTED")

    def test_unknown_lifecycle_directory_is_rejected(self) -> None:
        self.tree.write("done/architecture/2026-11-20-x.md",
                        proposal("Unknown lifecycle", "Status: proposed"))
        self.assertFailsWith("LAYOUT_UNKNOWN_LIFECYCLE")


class StatusPathTests(BaseCase):
    def test_implemented_directory_with_proposed_status_is_rejected(self) -> None:
        self.tree.write("implemented/architecture/2026-10-02-x.md",
                        proposal("Rewound", "Status: proposed", body=IMPLEMENTED_BODY))
        self.assertFailsOnlyWith("STATUS_PATH_MISMATCH")

    def test_proposed_directory_with_implemented_status_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Jumped", "Status: implemented"))
        self.assertFailsWith("STATUS_PATH_MISMATCH")

    def test_rejected_status_requires_a_reason(self) -> None:
        self.tree.write("rejected/bug-fix/2026-11-15-x.md",
                        proposal("No reason", "Status: rejected", cls="bug-fix", body=REJECTED_BODY))
        self.assertFailsWith("STATUS_REJECTED_NO_REASON")

    def test_rejected_file_outside_rejected_dir_is_rejected(self) -> None:
        self.tree.write("proposed/bug-fix/2026-11-15-x.md",
                        proposal("Misplaced", "Status: rejected — nope",
                                 cls="bug-fix", body=REJECTED_BODY))
        self.assertFailsWith("STATUS_PATH_MISMATCH")

    def test_missing_status_line_is_rejected_for_formatted_file(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        "# No status\n\n- **Class**: architecture\n\n## Problem\nx\n")
        self.assertFailsWith("STATUS_MISSING")

    def test_unknown_status_value_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Odd status", "Status: implementing"))
        self.assertFailsWith("STATUS_UNKNOWN_VALUE")


class SkeletonTests(BaseCase):
    def test_design_basis_skeleton_accepts_optional_decisions_and_no_risks(self) -> None:
        bodies = {
            "proposed": ("Status: proposed", "## Proposal\n\nUse a bus.\n\n## Acceptance criteria\n\n1. Producers publish through the bus."),
            "implemented": ("Status: implemented", "## Decision\n\nProducers publish through the bus.\n\n## Consequences\n\nVerified delivery."),
            "rejected": ("Status: rejected — infeasible", "## Proposal\n\nUse a bus."),
        }
        for lifecycle, (status, tail) in bodies.items():
            with self.subTest(lifecycle=lifecycle):
                body = "\n## Problem\n\nReduce coupling.\n\n## Design Basis\n\nPreserve module ownership.\n\n" + tail + "\n"
                self.tree.write(f"{lifecycle}/architecture/2026-11-20-x.md",
                                proposal("Bus", status, body=body))
                self.assertPass()

    def test_new_skeleton_missing_required_heading_is_rejected(self) -> None:
        body = "\n## Problem\n\nReduce coupling.\n\n## Design Basis\n\nPreserve ownership.\n\n## Proposal\n\nUse a bus.\n\n## Acceptance criteria\n\n1. Publish."
        for heading in ("Design Basis", "Proposal", "Acceptance criteria"):
            with self.subTest(heading=heading):
                self.tree.write("proposed/architecture/2026-11-20-x.md",
                                proposal("Incomplete", "Status: proposed",
                                         body=body.replace(f"## {heading}", "## Other")))
                self.assertFailsWith("SKELETON_MISSING_SECTION")

    def test_former_skeleton_is_rejected(self) -> None:
        body = "\n## Problem\n\nCoupling.\n\n## Proposal\n\nUse a bus.\n\n## Alternatives considered\n\nDirect calls.\n\n## Acceptance criteria\n\n1. Publish.\n\n## Risks\n\nNone.\n"
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Missing design basis", "Status: proposed", body=body))
        self.assertFailsWith("SKELETON_MISSING_SECTION")

    def test_proposed_missing_acceptance_criteria_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("No AC", "Status: proposed",
                     body=PROPOSED_BODY.replace("## Acceptance criteria", "## Done when")),
        )
        self.assertFailsWith("SKELETON_MISSING_SECTION")

    def test_implemented_missing_decision_is_rejected(self) -> None:
        self.tree.write("implemented/architecture/2026-10-02-x.md",
                        proposal("No decision", "Status: implemented", body=PROPOSED_BODY))
        self.assertFailsWith("SKELETON_MISSING_SECTION")

    def test_implemented_with_planning_headings_is_rejected(self) -> None:
        self.tree.write(
            "implemented/architecture/2026-10-02-x.md",
            proposal(
                "Stale headings",
                "Status: implemented",
                body=IMPLEMENTED_BODY + "\n## Acceptance criteria\n\n1. x\n",
            ),
        )
        self.assertFailsWith("SKELETON_FORBIDDEN_SECTION")

    def test_each_planning_heading_is_forbidden_in_implemented(self) -> None:
        for heading in ("## Proposal", "## Plan", "## Migration plan", "## Acceptance criteria"):
            with self.subTest(heading=heading):
                self.tree.write(
                    "implemented/architecture/2026-10-02-x.md",
                    proposal("Stale", "Status: implemented",
                             body=IMPLEMENTED_BODY + f"\n{heading}\n\n1. x\n"),
                )
                self.assertFailsWith("SKELETON_FORBIDDEN_SECTION")

    def test_reordered_fixed_sections_are_rejected(self) -> None:
        body = ("\n## Problem\n\nCoupling.\n\n## Decision\n\nUse a bus.\n\n"
                "## Design Basis\n\nPreserve ownership.\n\n## Consequences\n\nDelivered.\n")
        self.tree.write("implemented/architecture/2026-10-02-x.md",
                        proposal("Shuffled", "Status: implemented", body=body))
        self.assertFailsWith("SKELETON_SECTION_ORDER")

    def test_bespoke_sections_keep_fixed_order(self) -> None:
        body = ("\n## Problem\n\nCoupling.\n\n## Design Basis\n\nPreserve ownership.\n\n"
                "## Decision\n\nUse a bus.\n\n## Routing\n\nBespoke detail.\n\n"
                "## Design Decisions\n\nBus beats direct calls here.\n\n## Consequences\n\nDelivered.\n")
        self.tree.write("implemented/architecture/2026-10-02-x.md",
                        proposal("Ordered", "Status: implemented", body=body))
        self.assertPass()

    def test_archived_skips_skeleton_rules(self) -> None:
        # An archived body keeps whatever it had; only metadata is checked.
        self.tree.write(
            "archived/architecture/2026-09-01-x.md",
            proposal("Archived legacy body", "Status: implemented\nArchived: 2026-11-20",
                     body="\n## Whatever\n\nFrozen content.\n"),
        )
        self.assertPass()


class ApprovalTests(BaseCase):
    def test_approved_without_approval_record_is_rejected(self) -> None:
        self.tree.write("proposed/feature/2026-11-21-x.md",
                        proposal("No approval", "Status: approved", cls="feature"))
        self.assertFailsWith("APPROVAL_MISSING")

    def test_approved_without_authorized_scope_is_rejected(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("No scope", "Status: approved", cls="feature",
                     extra_header="- **Approved**: 2026-11-22 — owner\n- **Delivery**: direct"),
        )
        self.assertFailsWith("APPROVAL_MISSING")

    def test_approved_without_delivery_is_rejected(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("No delivery", "Status: approved", cls="feature",
                     extra_header="- **Approved**: 2026-11-22 — owner\n"
                                  "- **Authorized scope**: two tables"),
        )
        self.assertFailsWith("APPROVAL_MISSING")

    def test_invalid_delivery_value_is_rejected(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("Bad delivery", "Status: approved", cls="feature",
                     extra_header=APPROVAL.format(scope="two tables", delivery="quick").strip()),
        )
        self.assertFailsWith("APPROVAL_BAD_DELIVERY")

    def test_both_delivery_values_are_accepted(self) -> None:
        for delivery in ("direct", "plan"):
            with self.subTest(delivery=delivery):
                name = f"proposed/feature/2026-11-2{1 if delivery == 'direct' else 2}-{delivery}.md"
                self.tree.write(
                    name,
                    proposal(f"Delivery {delivery}", "Status: approved", cls="feature",
                             extra_header=APPROVAL.format(scope="two tables", delivery=delivery).strip()),
                )
        self.assertPass()

    def test_approval_fields_are_required_only_when_approved(self) -> None:
        self.tree.write("proposed/feature/2026-11-21-x.md",
                        proposal("Still proposed", "Status: proposed", cls="feature"))
        self.assertPass()


class ArchiveTests(BaseCase):
    def test_archived_without_archive_date_is_rejected(self) -> None:
        self.tree.write("archived/architecture/2026-09-01-x.md",
                        proposal("No date", "Status: implemented", body=IMPLEMENTED_BODY))
        self.assertFailsWith("ARCHIVE_MISSING_DATE")

    def test_archived_with_malformed_date_is_rejected(self) -> None:
        self.tree.write("archived/architecture/2026-09-01-x.md",
                        proposal("Bad date", "Status: implemented\nArchived: 20-11-20",
                                 body=IMPLEMENTED_BODY))
        self.assertFailsWith("ARCHIVE_MISSING_DATE")

    def test_archived_with_non_implemented_status_is_rejected(self) -> None:
        self.tree.write("archived/architecture/2026-09-01-x.md",
                        proposal("Proposed archive", "Status: proposed\nArchived: 2026-11-20"))
        self.assertFailsWith("STATUS_PATH_MISMATCH")

    def test_archived_outbound_links_are_not_checked(self) -> None:
        self.tree.write(
            "archived/architecture/2026-09-01-x.md",
            proposal(
                "Frozen with dead link",
                "Status: implemented\nArchived: 2026-11-20",
                body=IMPLEMENTED_BODY.replace(
                    "## Decision\n",
                    "## Decision\n\nSee [gone](../feature/2020-01-01-deleted.md).\n",
                ),
            ),
        )
        self.assertPass()

    def test_archived_is_exempt_from_absolute_path_rule(self) -> None:
        self.tree.write(
            "archived/architecture/2026-09-01-x.md",
            proposal(
                "Frozen with absolute path",
                "Status: implemented\nArchived: 2026-11-20",
                body=IMPLEMENTED_BODY.replace(
                    "## Decision\n", "## Decision\n\nSnapshot at `file:///tmp/old.md`.\n",
                ),
            ),
        )
        self.assertPass()


class LinkTests(BaseCase):
    def test_broken_relative_outbound_link_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal(
                "Broken link",
                "Status: proposed",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n",
                    "## Proposal\n\nSee [missing](../implemented/feature/2020-01-01-gone.md).\n",
                ),
            ),
        )
        self.assertFailsWith("LINK_BROKEN_OUTBOUND")

    def test_absolute_path_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal(
                "Absolute",
                "Status: proposed",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n", "## Proposal\n\nSee `file:///Users/someone/doc.md`.\n",
                ),
            ),
        )
        self.assertFailsWith("LINK_ABSOLUTE_PATH")

    def test_broken_inbound_link_is_rejected(self) -> None:
        # A caller links to a file that does not exist inside the same tree.
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal(
                "Cites a tree file",
                "Status: proposed",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n",
                    "## Proposal\n\nExtends [old](./2026-01-01-absent.md).\n",
                ),
            ),
        )
        self.assertFailsWith("LINK_BROKEN_OUTBOUND")

    def test_valid_links_across_directories_pass(self) -> None:
        self.tree.write("implemented/architecture/2026-10-02-old.md",
                        proposal("Old", "Status: implemented", body=IMPLEMENTED_BODY))
        self.tree.write(
            "proposed/simplification/2026-11-22-new.md",
            proposal(
                "New",
                "Status: proposed",
                cls="simplification",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n",
                    "## Proposal\n\nSee [old](../../implemented/architecture/2026-10-02-old.md) "
                    "and [local](./2026-11-22-new.md).\n",
                ),
            ),
        )
        self.assertPass()

    def test_external_and_anchor_links_are_ignored(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal(
                "External",
                "Status: proposed",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n",
                    "## Proposal\n\nSee [spec](https://example.com/x) and [anchor](#risks).\n",
                ),
            ),
        )
        self.assertPass()


class InboundScopeTests(BaseCase):
    """A document outside the proposal tree may cite a proposal path.

    The tree scan cannot see that citation, so callers pass the owning docs
    directory with --link-scope; the referring file is then checked too.
    """

    def setUp(self) -> None:
        super().setUp()
        self.docs = Path(tempfile.mkdtemp(prefix="verify-scope-"))
        self.addCleanup(shutil.rmtree, self.docs, True)
        shutil.rmtree(self.tree.root, ignore_errors=True)
        self.tree.root = self.docs

    def test_inbound_link_to_an_existing_proposal_passes(self) -> None:
        self.tree.write(
            "proposals/implemented/architecture/2026-11-20-x.md",
            proposal("X", "Status: implemented", body=IMPLEMENTED_BODY),
        )
        self.tree.write(
            "DESIGN.md",
            "# Project\n\n> **Status**: Active\n\n## Key Decisions\n\n"
            "- [x](./proposals/implemented/architecture/2026-11-20-x.md)\n",
        )
        self.assertPass("--link-scope", str(self.docs))

    def test_inbound_link_to_a_deleted_proposal_is_rejected(self) -> None:
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("X", "Status: proposed"))
        self.tree.write(
            "DESIGN.md",
            "# Project\n\n> **Status**: Active\n\n## Key Decisions\n\n"
            "- [gone](./proposals/implemented/feature/2026-01-01-deleted.md)\n",
        )
        result = run(self.docs, "--json", "--link-scope", str(self.docs))
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn("LINK_BROKEN_OUTBOUND", codes(result), msg=result.stdout)

    def test_absent_link_scope_is_ignored(self) -> None:
        # The tree alone stays green; the caller opts into the wider scan.
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("X", "Status: proposed"))
        self.tree.write(
            "DESIGN.md",
            "# Project\n\n- [gone](./proposals/implemented/feature/2026-01-01-deleted.md)\n",
        )
        self.assertPass()

    def test_scope_scan_also_requires_the_root_to_exist(self) -> None:
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("X", "Status: proposed"))
        result = run(self.docs, "--json", "--link-scope", str(self.docs / "nope"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LINK_SCOPE_MISSING", codes(result), msg=result.stdout)

    def test_scope_scan_skips_research_and_references_subdirs(self) -> None:
        self.tree.write(
            "proposals/implemented/architecture/2026-11-20-x.md",
            proposal("X", "Status: implemented", body=IMPLEMENTED_BODY),
        )
        self.tree.write("DESIGN.md", "# Project\n\n- [x](./proposals/implemented/architecture/2026-11-20-x.md)\n")
        self.tree.write(
            "research/upstream-snapshot.md",
            "# Upstream\n\nExample path `/home/coder/.local/share/x` and `file:///path/to/plugin.ts`.\n",
        )
        self.tree.write(
            "references/notes.md",
            "# Notes\n\nSee `/Users/example/demo.md`.\n",
        )
        self.assertPass("--link-scope", str(self.docs))

    def test_scope_scan_still_checks_design_docs_when_research_is_skipped(self) -> None:
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("X", "Status: proposed"))
        self.tree.write("DESIGN.md", "# Project\n\n- [gone](./proposals/implemented/feature/2026-01-01-deleted.md)\n")
        self.tree.write("research/upstream-snapshot.md", "# Upstream\n\n`file:///path/to/plugin.ts`\n")
        result = run(self.docs, "--json", "--link-scope", str(self.docs))
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertEqual(codes(result), ["LINK_BROKEN_OUTBOUND"], msg=result.stdout)


class HeaderContractTests(BaseCase):
    """A formatted file states one status and the fields that identify it."""

    def test_duplicate_status_line_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Two states", "Status: proposed\n\nStatus: implemented"),
        )
        self.assertFailsWith("STATUS_DUPLICATE")

    def test_missing_class_field_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            "# No class\n\nStatus: proposed\n\n- **Created**: 2026-11-20\n" + PROPOSED_BODY,
        )
        self.assertFailsWith("CLASS_MISSING")

    def test_missing_created_field_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            "# No created\n\nStatus: proposed\n\n- **Class**: architecture\n" + PROPOSED_BODY,
        )
        self.assertFailsWith("CREATED_MISSING")

    def test_malformed_created_date_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            "# Odd date\n\nStatus: proposed\n\n- **Class**: architecture\n"
            "- **Created**: 2026-99-99\n" + PROPOSED_BODY,
        )
        self.assertFailsWith("CREATED_BAD_DATE")

    def test_created_date_is_checked_in_every_lifecycle(self) -> None:
        self.tree.write(
            "implemented/architecture/2026-10-02-x.md",
            "# Odd date\n\nStatus: implemented\n\n- **Class**: architecture\n"
            "- **Created**: not-a-date\n" + IMPLEMENTED_BODY,
        )
        self.assertFailsWith("CREATED_BAD_DATE")

    def test_complete_header_passes(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Complete", "Status: proposed"))
        self.assertPass()


class ApprovalFormatTests(BaseCase):
    def test_undated_approval_record_is_rejected(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("Undated", "Status: approved", cls="feature",
                     extra_header="- **Approved**: tomorrow\n"
                                  "- **Authorized scope**: two tables\n"
                                  "- **Delivery**: plan"),
        )
        self.assertFailsWith("APPROVAL_BAD_DATE")

    def test_approval_without_an_approver_is_rejected(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("Anonymous", "Status: approved", cls="feature",
                     extra_header="- **Approved**: 2026-11-22 —\n"
                                  "- **Authorized scope**: two tables\n"
                                  "- **Delivery**: plan"),
        )
        self.assertFailsWith("APPROVAL_BAD_DATE")

    def test_impossible_approval_date_is_rejected(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("Impossible", "Status: approved", cls="feature",
                     extra_header="- **Approved**: 2026-02-31 — owner\n"
                                  "- **Authorized scope**: two tables\n"
                                  "- **Delivery**: plan"),
        )
        self.assertFailsWith("APPROVAL_BAD_DATE")

    def test_dated_and_signed_approval_passes(self) -> None:
        self.tree.write(
            "proposed/feature/2026-11-21-x.md",
            proposal("Signed", "Status: approved", cls="feature",
                     extra_header=APPROVAL.format(scope="two tables", delivery="direct").strip()),
        )
        self.assertPass()


class ArchiveAdjacencyTests(BaseCase):
    def test_archive_date_on_the_next_line_passes(self) -> None:
        self.tree.write(
            "archived/process/2026-09-01-x.md",
            proposal("Adjacent", "Status: implemented\nArchived: 2026-11-20",
                     cls="process", body=IMPLEMENTED_BODY),
        )
        self.assertPass()

    def test_archive_date_detached_by_a_blank_line_is_rejected(self) -> None:
        self.tree.write(
            "archived/process/2026-09-01-x.md",
            proposal("Detached", "Status: implemented\n\nArchived: 2026-11-20",
                     cls="process", body=IMPLEMENTED_BODY),
        )
        self.assertFailsWith("ARCHIVE_DATE_MISPLACED")

    def test_archive_date_below_the_identity_fields_is_rejected(self) -> None:
        self.tree.write(
            "archived/process/2026-09-01-x.md",
            "# Late\n\nStatus: implemented\n\n- **Class**: process\n"
            "- **Created**: 2026-09-01\nArchived: 2026-11-20\n" + IMPLEMENTED_BODY,
        )
        self.assertFailsWith("ARCHIVE_DATE_MISPLACED")

    def test_archive_date_in_the_body_is_not_accepted(self) -> None:
        self.tree.write(
            "archived/process/2026-09-01-x.md",
            proposal("Body date", "Status: implemented", cls="process",
                     body=IMPLEMENTED_BODY + "\nArchived: 2026-11-20\n"),
        )
        self.assertFailsWith("ARCHIVE_MISSING_DATE")


class FilenameDateTests(BaseCase):
    def test_impossible_filename_date_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/2026-99-99-alpha-beta.md",
                        proposal("Bad date", "Status: proposed"))
        self.assertFailsWith("LAYOUT_BAD_FILENAME")

    def test_single_word_slug_is_accepted(self) -> None:
        # Slug length is a writing preference, not a structural invariant.
        self.tree.write("proposed/architecture/2026-11-20-alpha.md",
                        proposal("Short slug", "Status: proposed"))
        self.assertPass()

    def test_long_slug_is_accepted(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-one-two-three-four-five.md",
                        proposal("Long slug", "Status: proposed"))
        self.assertPass()


class PosixPathTests(BaseCase):
    def test_home_directory_path_in_inline_code_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Linux path", "Status: proposed",
                     body=PROPOSED_BODY.replace("## Proposal\n",
                                                "## Proposal\n\nSee `/home/sam/secret.md`.\n")),
        )
        self.assertFailsWith("LINK_ABSOLUTE_PATH")

    def test_root_owned_path_is_rejected(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Root path", "Status: proposed",
                     body=PROPOSED_BODY.replace("## Proposal\n",
                                                "## Proposal\n\nConfig lives at `/root/conf.md`.\n")),
        )
        self.assertFailsWith("LINK_ABSOLUTE_PATH")

    def test_https_link_containing_home_is_not_an_absolute_path(self) -> None:
        # A URL path segment is not a local absolute path.
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("External doc", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nSee [help](https://example.com/home/help.md).\n")),
        )
        self.assertPass()

    def test_https_link_containing_root_is_not_an_absolute_path(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("External doc", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nSee [docs](https://example.com/root/docs.md).\n")),
        )
        self.assertPass()

    def test_https_link_containing_users_is_not_an_absolute_path(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("External doc", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nSee https://example.com/Users/foo.md\n")),
        )
        self.assertPass()

    def test_local_absolute_path_beside_an_https_link_is_still_caught(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Mixed", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nSee [help](https://example.com/home/help.md) "
                         "and `/home/sam/secret.md`.\n")),
        )
        self.assertFailsWith("LINK_ABSOLUTE_PATH")

    def test_local_path_immediately_after_a_url_is_still_caught(self) -> None:
        # The URL exemption must not swallow a citation that follows the link.
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Adjacent", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nSee https://example.com/home/a.md then "
                         "`/home/sam/secret.md`.\n")),
        )
        self.assertFailsWith("LINK_ABSOLUTE_PATH")

    def test_link_target_with_a_home_segment_is_ignored(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Remote", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nRead [x](http://example.com/root/x.md) first.\n")),
        )
        self.assertPass()

    def test_route_like_paths_are_not_mistaken_for_absolute_ones(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal("Relative", "Status: proposed",
                     body=PROPOSED_BODY.replace(
                         "## Proposal\n",
                         "## Proposal\n\nRoutes live under `/api/v1/orders` and "
                         "settings under `/etc/wopal/`; both are runtime coordinates.\n",
                     )),
        )
        self.assertPass()

    def test_embedded_home_and_root_segments_are_not_flagged_as_absolute(self) -> None:
        self.tree.write(
            "proposed/architecture/2026-11-20-x.md",
            proposal(
                "Embedded path segments",
                "Status: proposed",
                body=PROPOSED_BODY.replace(
                    "## Proposal\n",
                    "## Proposal\n\nStore config under `$WOPAL_HOME/dsh/home/profiles/web/cordis.patch.yml`, "
                    "pass `name/root/ontology`, and bundle `$bunfs/root/worker.js`.\n",
                ),
            ),
        )
        self.assertPass()

    def test_standalone_home_and_root_paths_in_parens_or_backticks_are_rejected(self) -> None:
        for snippet in ("See `/home/sam/file.md`.", "See (/root/x.md)."):
            with self.subTest(snippet=snippet):
                self.tree.write(
                    "proposed/architecture/2026-11-20-x.md",
                    proposal(
                        "Standalone POSIX path",
                        "Status: proposed",
                        body=PROPOSED_BODY.replace("## Proposal\n", f"## Proposal\n\n{snippet}\n"),
                    ),
                )
                self.assertFailsWith("LINK_ABSOLUTE_PATH")


class UncoveredCodeTests(BaseCase):
    """Every issue code the verifier can emit has a test that pins it."""

    def test_unexpected_directory_depth_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/nested/deep/2026-11-20-x.md",
                        proposal("Deep", "Status: proposed"))
        self.assertFailsWith("LAYOUT_UNEXPECTED_PATH")

    def test_class_field_that_disagrees_with_the_directory_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Mismatch", "Status: proposed", cls="feature"))
        self.assertFailsWith("CLASS_FIELD_MISMATCH")

    def test_unknown_class_field_value_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Unknown", "Status: proposed", cls="refactor"))
        self.assertFailsWith("CLASS_UNKNOWN_VALUE")

    def test_root_level_markdown_is_rejected(self) -> None:
        self.tree.write("2026-01-05-flat-style.md", "# Flat\n\nSits outside any lifecycle.\n")
        self.assertFailsWith("LAYOUT_UNEXPECTED_PATH")

    def test_headerless_file_at_valid_path_is_rejected(self) -> None:
        self.tree.write("proposed/architecture/2026-01-05-x.md", "# No header\n")
        self.assertFailsWith("STATUS_MISSING")

    def test_headerless_file_in_unknown_class_is_rejected(self) -> None:
        self.tree.write("proposed/unknown/2026-01-05-x.md", "# No header\n")
        self.assertFailsWith("LAYOUT_UNKNOWN_CLASS")

    def test_headerless_file_in_unknown_lifecycle_is_rejected(self) -> None:
        self.tree.write("unknown/architecture/2026-01-05-x.md", "# No header\n")
        self.assertFailsWith("LAYOUT_UNKNOWN_LIFECYCLE")


class ParentRootTests(BaseCase):
    """A parent directory is a documented entry point; both roots are visible."""

    def test_singular_sibling_next_to_proposals_is_rejected(self) -> None:
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("Main root", "Status: proposed"))
        self.tree.write("proposal/feature/2026-11-20-old.md",
                        proposal("Old root", "Status: proposed", cls="feature"))
        self.assertFailsWith("LAYOUT_SINGULAR_SIBLING")

    def test_parent_entry_with_a_single_root_passes(self) -> None:
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("Main root", "Status: proposed"))
        self.assertPass()

    def test_direct_proposals_root_is_unaffected_by_a_parent_sibling(self) -> None:
        self.tree.write("proposals/proposed/architecture/2026-11-20-x.md",
                        proposal("Main root", "Status: proposed"))
        self.tree.write("proposal/feature/2026-11-20-old.md",
                        proposal("Old root", "Status: proposed", cls="feature"))
        result = run(self.tree.root / "proposals", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout)


class ReportingTests(BaseCase):
    def test_json_report_names_counts_and_fix_hint(self) -> None:
        self.tree.write("proposed/refactor/2026-11-20-x.md",
                        proposal("Unknown class", "Status: proposed", cls="refactor"))
        result = run(self.tree.root, "--json")
        report = json.loads(result.stdout)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertGreaterEqual(report["counts"]["errors"], 1)
        issue = next(i for i in report["issues"] if i["code"] == "LAYOUT_UNKNOWN_CLASS")
        self.assertIn("path", issue)
        self.assertIn("fix", issue)
        self.assertTrue(issue["fix"])

    def test_human_report_is_readable(self) -> None:
        self.tree.write("INDEX.md", "# Index\n")
        result = run(self.tree.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL", result.stdout)
        self.assertIn("INDEX", result.stdout.upper())

    def test_missing_root_is_an_error_not_a_crash(self) -> None:
        missing = self.tree.root / "does-not-exist"
        result = subprocess.run([sys.executable, str(SCRIPT), str(missing)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_link_scope_is_reported(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Ok", "Status: proposed"))
        self.assertFailsWith("LINK_SCOPE_MISSING", "--link-scope", str(self.tree.root / "absent"))

    def test_missing_root_is_reported_as_a_code(self) -> None:
        missing = self.tree.root / "does-not-exist"
        result = subprocess.run([sys.executable, str(SCRIPT), str(missing), "--json"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(codes(result), ["ROOT_MISSING"])

    def test_exit_code_distinguishes_pass_from_fail(self) -> None:
        self.tree.write("proposed/architecture/2026-11-20-x.md",
                        proposal("Ok", "Status: proposed"))
        self.assertEqual(run(self.tree.root).returncode, 0)
        self.tree.write("INDEX.md", "# Index\n")
        self.assertEqual(run(self.tree.root).returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
