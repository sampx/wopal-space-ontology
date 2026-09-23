#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# evo.py - Command entry point for the ontology-evolution mechanism lane.
#
#   evo.sh new <title>                   create docs/evolutions/<name>.md (Stage: draft)
#   evo.sh status <name|path>            print stage, file path, and next command
#   evo.sh accept <name> [--no-worktree] accept for implementation (derive a worktree)
#   evo.sh advance <name> --to <state>   advance the state machine (illegal -> exit 1)
#   evo.sh commit <name> -m <message>    sparse-safe commit (--paths/--all in quick mode)
#   evo.sh fix -m <message> [...]        immediate defect repair (no proposal)
#   evo.sh integrate <name>              squash the isolated work into the space branch
#   evo.sh check <name>                  report proposal and sparse-state problems
#   evo.sh archive <name>                move an archived proposal to archived/
#
# Two rules the commands exist to enforce:
#
#   1. Never stage a work tree wholesale. On a corrupted sparse checkout,
#      `git add -A` records every out-of-range path as a deletion; the commit
#      path therefore widens the range first and stages named paths.
#   2. Refuse before writing. Every safety check runs before the first
#      mutation, so a rejected command leaves the repository untouched.
#
# Stage writes go through this script only: agents never hand-edit `Stage`.
# Delivery (space sync / ontology contribute) is intentionally absent — it is
# the user's terminal decision.

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from lib import proposal, repo, sparse, worktree

SKILL_NAME = "ontology-evolution"

USAGE = """usage: evo.sh <command> [args]

commands:
  new <title>                      create a proposal in docs/evolutions/ (Stage: draft)
  status <name|path>               show stage, file path, and suggested next command
  accept <name> [--no-worktree]    accept for implementation; derive an isolated worktree
  advance <name> --to <state>      advance the state machine
  commit <name> -m <message>       sparse-safe commit (--paths <p>... or --all in quick mode)
  fix -m <message> (--paths <p>... | --all)
                                   immediate defect repair: commit on the space branch
  integrate <name>                 squash the isolated work into the space branch
  check <name>                     report proposal and sparse-state problems
  archive <name>                   move an archived proposal to docs/evolutions/archived/

state machine: draft -> accepted -> implementing -> validating -> archived
"""

# The proposal skeleton lives in `templates/proposal.md` — an external file
# with per-section authoring comments, mirroring dev-flow's template layout.
# Loading it here (instead of embedding a string) is what keeps the scaffold
# and the authoring guidance one artifact: edit the file, and every new
# proposal inherits the change.
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "proposal.md"

# Placeholders the author must replace before a proposal counts as
# implemented. Derived from the template so the two can never drift apart.
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{1,80}>")

_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _prose(text: str) -> str:
    """The proposal text with code removed.

    A placeholder is an authoring gap in prose. Angle brackets inside a
    fenced block or an inline span are the CLI contract written down
    (`evo.sh advance <name> --to <state>`); scanning the raw text would
    fail every proposal that documents its own commands.
    """
    return _INLINE_CODE_RE.sub("", _FENCED_CODE_RE.sub("", text))


def _template_text() -> str:
    if not TEMPLATE_PATH.is_file():
        raise repo.RepoRootError(
            f"proposal template not found at {TEMPLATE_PATH}; the skill is "
            "incomplete without it"
        )
    return TEMPLATE_PATH.read_text()


def _placeholders() -> list[str]:
    seen: list[str] = []
    for token in PLACEHOLDER_RE.findall(_template_text()):
        if token not in seen:
            seen.append(token)
    return seen


# The sections a filled proposal must carry (structure contract, D-06/D-07).
# `## Implementation` requires at least one `### Task N:` with the six
# elements; `## Acceptance Criteria` requires both AV and UV subsections.
_REQUIRED_SECTIONS = (
    "## Goal",
    "## Technical Context",
    "## In Scope",
    "## Out of Scope",
    "## Affected Files",
    "## Acceptance Criteria",
    "### Agent Verification",
    "### User Validation",
    "## Implementation",
    "## Delegation Strategy",
)
_TASK_ELEMENTS = (
    "Verification Intent",
    "Behavior",
    "TDD",
    "Changes",
    "Verify",
    "Done",
)
_TASK_HEADER_RE = re.compile(r"^### Task (?P<number>\d+):.*$", re.MULTILINE)


def _structure_problems(text: str) -> list[str]:
    """The missing pieces of the proposal structure contract.

    Prose-only scan (code fences stripped) so a proposal that documents its
    own CLI contract cannot false-positive.
    """
    problems: list[str] = []
    prose = _prose(text)
    for section in _REQUIRED_SECTIONS:
        if section not in prose:
            problems.append(f"structure: missing section {section!r}")
    tasks = list(_TASK_HEADER_RE.finditer(prose))
    if not tasks:
        problems.append("structure: no `### Task N:` entries under Implementation")
    else:
        for index, task in enumerate(tasks):
            end = tasks[index + 1].start() if index + 1 < len(tasks) else len(prose)
            block = prose[task.start() : end]
            missing = [
                element
                for element in _TASK_ELEMENTS
                if not re.search(
                    rf"^\*\*{re.escape(element)}\*\*:",
                    block,
                    re.MULTILINE,
                )
            ]
            if missing:
                problems.append(
                    f"structure: Task {task.group('number')} lacks "
                    + " / ".join(missing)
                )
    return problems


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


# The command/stage guard table (D-08): one source of truth for every
# mutating command's stage precondition. Scattered checks drift; this table
# is covered by the stage-guard tests.
_GUARDS: dict[str, str] = {
    "commit": "implementing",
    "integrate": "implementing",
    "archive": "archived",
}


def _guard_stage(command: str, path: Path) -> int | None:
    """Refuse a mutating command outside its single permitted stage."""
    required = _GUARDS.get(command)
    if required is None:
        return None
    stage = proposal.get_stage(path)
    if stage == required:
        return None
    successors = proposal.next_states(stage or "")
    if successors:
        hint = f" Run `evo.sh advance {path.stem} --to {successors[0]}` first."
    else:
        hint = " No legal next state is available; create a new proposal for further work."
    return _fail(
        f"{path.name} is at stage {stage or 'unknown'!r}; `{command}` "
        f"requires {required!r}.{hint}"
    )


def _slugify(title: str) -> str:
    """Turn a free-form title into a path-safe proposal name."""
    slug = title.strip().lower()
    slug = re.sub(r"^[a-z]+\([^)]*\):\s*", "", slug)  # drop a conventional prefix
    slug = re.sub(r"[_\s]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def _git(repo_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args], capture_output=True, text=True
    )


def _zlines(result: subprocess.CompletedProcess) -> list[str]:
    return [token for token in result.stdout.split("\0") if token]


def _root() -> Path:
    return repo.resolve_repo_root(Path(__file__).resolve().parent)


def _space_root(root: Path) -> Path:
    """The space root that holds `.wopal`.

    Works from `.wopal`, from the skill directory nested inside either the
    space worktree or an isolated one, and from an isolated worktree under
    `<space>/.worktrees/`. The space is the nearest ancestor-or-self holding
    a `.wopal` directory.
    """
    for candidate in [root, *root.parents]:
        if (candidate / ".wopal").is_dir():
            return candidate
    return root


def _recorded(space: Path, value: str) -> Path:
    """Resolve a recorded worktree path, which is stored space-relative."""
    path = Path(value)
    return path if path.is_absolute() else space / path


def _portable(space: Path, path: Path) -> str:
    """Prefer a space-relative worktree path so the record stays readable."""
    try:
        return str(path.resolve().relative_to(space.resolve()))
    except ValueError:
        return str(path)


def _commit_paths(work_dir: Path, paths: list[str], message: str) -> bool:
    """Stage exactly `paths` and commit. False when there was nothing to do.

    Staging is always by name: `git add -A` on a checkout whose range has
    drifted records every out-of-range path as a deletion.
    """
    if not paths:
        return False
    _git(work_dir, "add", "--", *sorted(set(paths)))
    staged = _git(work_dir, "diff", "--cached", "--name-only")
    if not staged.stdout.strip():
        return False
    result = _git(work_dir, "commit", "-m", message)
    if result.returncode != 0:
        raise proposal.ProposalError(
            f"failed to commit in {work_dir}: {result.stderr.strip()}"
        )
    return True



def _resolve_proposal(ref: str) -> Path | None:
    """Locate a proposal from a bare name or a path.

    The canonical copy lives on the space branch inside `.wopal`, and that
    copy is preferred even when the script runs from an isolated worktree.
    The worktree holds a checked-out copy too, but it is a snapshot: the
    stage moves on the space branch, and reading the snapshot would report a
    stage the proposal no longer has.

    Archived files carry a `YYYYMMDD-` prefix, so a bare name resolves
    against the dated form: `status <name>` keeps working after archive.
    """
    candidate = Path(ref)
    if candidate.suffix == ".md" and candidate.is_file():
        return candidate.resolve()

    space = _space_root(_root())
    bases = [
        repo.evolutions_root(worktree.space_worktree_path(space)),
        repo.archived_root(worktree.space_worktree_path(space)),
        repo.evolutions_root(_root()),
        repo.archived_root(_root()),
    ]
    dated = re.compile(r"^\d{8}-")
    for base in bases:
        for path in (base / f"{ref}.md", base / f"{ref}"):
            if path.is_file():
                return path.resolve()
    for base in bases:
        if base.is_dir() and base.parent.name == "evolutions" and base.name == "archived":
            for path in sorted(base.glob(f"*{ref}.md")):
                if dated.match(path.name):
                    return path.resolve()
    return None


def _resolve_work_dir(path: Path, mode: str) -> tuple[Path | None, str | None]:
    """Where the changes live, plus the invariants that must hold there.

    In quick mode the workspace is the space worktree itself, which must be
    sitting on the branch that carries the space: committing there while it
    is on `main` would land ontology work straight into the base every other
    space depends on.
    """
    space = _space_root(_root())

    if mode == "quick":
        wopal = worktree.space_worktree_path(space)
        if not wopal.is_dir():
            return None, (
                "quick mode needs a space assembly worktree to commit into; "
                "none was found"
            )
        current = worktree.current_branch(wopal)
        if not current.startswith("space/"):
            return None, (
                f"quick mode commits on the space branch, but the space "
                f"worktree is on {current!r}; refusing to commit there"
            )
        return wopal, None

    recorded = proposal.get_field(path, "Worktree") or ""
    if not recorded or recorded == "(none)":
        return None, "no worktree recorded; re-run `evo.sh accept <name>`"
    work_dir = _recorded(space, recorded)
    if not worktree.worktree_exists(work_dir):
        if proposal.get_stage(path) in ("accepted", "implementing"):
            return None, (
                f"recorded worktree {recorded} is missing; "
                "re-run `evo.sh accept` to re-attach it"
            )
        return None, (
            f"recorded worktree {recorded} is missing; its content is already "
            "integrated — finish the lifecycle (advance to archived, then "
            "`evo.sh archive`) or restore the worktree"
        )

    expected = proposal.get_field(path, "Branch") or ""
    actual = worktree.current_branch(work_dir)
    if expected and expected != "(none)" and actual != expected:
        return None, (
            f"recorded branch {expected!r} does not match the worktree's "
            f"{actual!r}; refusing to commit from an unexpected branch"
        )
    return work_dir, None


# ── commands ────────────────────────────────────────────────────────────


def cmd_new(args: argparse.Namespace) -> int:
    if not args.title or not args.title.strip():
        return _fail('a proposal title is required: evo.sh new "<title>"')

    name = _slugify(args.title)
    if not name:
        return _fail(f"title {args.title!r} produces an empty proposal name")

    # A new proposal always lands on the space branch, even when the command
    # is run from inside a derived worktree: that is the copy the space reads,
    # and the copy `accept` and every later command resolve against. Writing
    # it into a derived worktree would leave it invisible in the live space
    # and unreachable by name. Outside a space (no `.wopal`) the ontology
    # repository the script found is the only place to put it.
    space = _space_root(_root())
    wopal = worktree.space_worktree_path(space)
    target_dir = repo.evolutions_root(wopal if wopal.is_dir() else _root())
    target_dir.mkdir(parents=True, exist_ok=True)

    path = target_dir / f"{name}.md"
    if path.exists():
        return _fail(f"{path} already exists; pick another title or edit it directly")

    path.write_text(
        _template_text().format(
            name=name, type=args.type, created=date.today().isoformat()
        )
    )
    print(path.resolve())
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh status <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    stage = proposal.get_stage(path)
    if stage is None:
        return _fail(f"{path} has no `- **Stage**:` field")

    print(f"Proposal : {path}")
    print(f"Stage    : {stage}")

    mode = proposal.get_field(path, "Mode") or ""
    if mode in ("isolated", "quick"):
        print(f"Mode     : {mode}")
        for field in ("Worktree", "Branch", "Base Commit", "Final Commit"):
            value = proposal.get_field(path, field) or ""
            if value and not value.startswith("("):
                print(f"{field:<9}: {value}")

    successors = proposal.next_states(stage)
    if successors:
        print(f"Next     : evo.sh advance {path.stem} --to {successors[0]}")
    else:
        print("Next     : none (terminal)")
        print(f"Archive  : evo.sh archive {path.stem}")
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh advance <name> --to <state>")
    if not args.to:
        return _fail("--to <state> is required: evo.sh advance <name> --to <state>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    current = proposal.get_stage(path)
    if current is None:
        return _fail(f"{path} has no `- **Stage**:` field")

    ok, error = proposal.validate_transition(current, args.to)
    if not ok:
        print(f"ERROR: {error}", file=sys.stderr)
        print(f"state machine: {' -> '.join(proposal.STATES)}", file=sys.stderr)
        return 1

    proposal.set_stage(path, args.to)
    _sync_record(path, f"docs(evolutions): {path.stem} -> {args.to}")
    print(f"{path}")
    print(f"Stage: {current} -> {args.to}")
    return 0


def cmd_accept(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh accept <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    stage = proposal.get_stage(path)
    if stage is None:
        return _fail(f"{path} has no `- **Stage**:` field")
    if stage not in ("draft", "accepted", "implementing"):
        return _fail(
            f"{path.name} is at stage {stage!r}; accept expects 'draft', "
            "'accepted', or 'implementing' (the last one covers re-attaching "
            "a worktree lost mid-implementation)"
        )

    # The accept gate: a proposal is read and judged here. Unreplaced
    # placeholders and a missing structure contract mean it was never
    # actually written, so acceptance refuses (mirrors dev-flow's submit).
    text = path.read_text()
    blocking = list(PLACEHOLDER_RE.findall(_prose(text)))
    if blocking:
        return _fail(
            f"{path.name} still has {len(blocking)} unreplaced "
            f"placeholder(s) ({blocking[0]}...); fill the proposal in "
            "before accepting"
        )
    structural = _structure_problems(text)
    if structural:
        return _fail(
            f"{path.name} does not meet the proposal structure contract: "
            + "; ".join(structural)
        )

    space = _space_root(_root())
    slug = path.stem
    wopal = worktree.space_worktree_path(space)

    recorded_base = ""
    if args.no_worktree:
        mode, wt_path, branch = "quick", None, ""
    else:
        if not wopal.is_dir():
            return _fail(
                f"no space assembly worktree at {wopal}; "
                "use --no-worktree to implement directly on the space branch"
            )

        base_branch = worktree.current_branch(wopal)
        if not base_branch.startswith("space/"):
            return _fail(
                f"the space worktree is on {base_branch!r}, not a 'space/*' "
                "branch; isolate from the branch that carries this space"
            )

        # The source must be healthy before anything is derived from it.
        # A disabled or corrupted space range otherwise spawns a full-checkout
        # worktree that only fails at the isolation assertion — by which time
        # the residue has to be cleaned up from exists (measured 2026-09-23).
        problems = sparse.preflight(wopal)
        if problems:
            return _fail(
                "refusing to accept: the space worktree is not coherent: "
                + "; ".join(problems)
            )

        isolated = worktree.slugify(slug)
        wt_path = worktree.derive_path(space, isolated)
        branch = worktree.branch_name(isolated)
        mode = "isolated"

        # Transactional derive (2026-09-23): the proposal metadata is written
        # and committed only after the worktree exists and passes the
        # isolation checks. A failure before that point cleans up the
        # artifacts it created, so a refused accept leaves the repository
        # exactly as it was.
        branch_preexists = worktree.reference_exists(wopal, f"refs/heads/{branch}")
        created = "none"
        if worktree.worktree_exists(wt_path):
            landed = worktree.current_branch(wt_path)
            if landed != branch:
                return _fail(
                    f"{wt_path} exists but is on {landed!r}, not {branch!r}; "
                    "resolve the stale worktree before accepting"
                )
            error = _fast_forward(wt_path, base_branch, wopal)
            if error:
                return _fail(error)
        elif branch_preexists:
            # The branch outlived its worktree (directory lost, cleanup never
            # ran). The commits on it are work: re-attach a worktree to the
            # branch instead of advising its deletion.
            result = _git(wopal, "worktree", "add", str(wt_path), branch)
            if result.returncode != 0:
                return _fail(
                    f"failed to re-attach a worktree to {branch!r} at "
                    f"{wt_path}: {result.stderr.strip()}"
                )
            created = "reattach"
            _adopt_space_patterns(wt_path, wopal)
            _widen_worktree_over_branch(wt_path, wopal, base_branch, branch)
            error = _fast_forward(wt_path, base_branch, wopal)
            if error:
                _cleanup_failed_derive(wopal, wt_path, branch, remove_branch=False)
                return _fail(error)
        else:
            base_commit = _git(wopal, "rev-parse", base_branch).stdout.strip()
            try:
                worktree.derive(space, isolated, base_commit)
            except worktree.WorktreeError as exc:
                _cleanup_failed_derive(wopal, wt_path, branch, remove_branch=True)
                return _fail(str(exc))
            created = "derive"

        problems = worktree.assert_isolated(space, wt_path)
        if problems:
            if created != "none":
                _cleanup_failed_derive(
                    wopal, wt_path, branch, remove_branch=(created == "derive")
                )
            return _fail(
                "derived worktree failed the isolation checks: " + "; ".join(problems)
            )

        # `Base Commit` is the worktree's actual fork point: the start commit
        # of a fresh derive, or the merge base for an adopted or re-attached
        # worktree. One source of truth for the record and the derivation.
        if created == "derive":
            recorded_base = base_commit
        else:
            recorded_base = _git(
                wopal, "merge-base", base_branch, branch
            ).stdout.strip()

    # Everything above is side-effect free with respect to the proposal; the
    # metadata is recorded only now that the worktree is verified.
    original = path.read_text()
    proposal.set_field(path, "Mode", mode)
    proposal.set_field(
        path, "Worktree", _portable(space, wt_path) if wt_path else "(none)"
    )
    proposal.set_field(path, "Branch", branch or "(none)")
    proposal.set_field(path, "Base Commit", recorded_base or "(none)")
    if stage == "draft":
        proposal.set_stage(path, "accepted")

    if not _commit_proposal(path, f"docs(evolutions): accept {slug}"):
        path.write_text(original)
        return _fail(
            f"could not record accept metadata in {path}; the proposal has "
            "uncommitted changes that do not belong to this command — commit "
            "or resolve them first"
        )

    if mode == "isolated":
        # The worktree predates the metadata commit, so its checked-out copy
        # of the proposal is stale. Mirror the record in and commit it on the
        # feature branch, or the next `integrate` refuses a dirty worktree.
        _mirror_into_worktree(space, path.name, path)

    print(f"{path}")
    print(f"Mode    : {mode}")
    if mode == "isolated":
        print(f"Worktree: {proposal.get_field(path, 'Worktree')}")
        print(f"Branch  : {branch}")
    print(f"Stage   : {proposal.get_stage(path)}")
    return 0


def _fast_forward(worktree_path: Path, base_branch: str, wopal: Path) -> str | None:
    """Bring an adopted worktree onto the space branch head when it trails.

    A worktree that carries its own commits is left alone: adoption keeps
    the work, and the squash at integration time reconciles the rest. A
    strictly-behind worktree is fast-forwarded, and its range is widened
    back over any pattern the space adopted in the meantime — the merge
    brings commits, not the worktree-local pattern list, and the isolation
    assertion would (correctly) refuse a worktree that no longer sees the
    whole space it was derived from.

    Returns an error message, or None on success.
    """
    ahead = _git(
        worktree_path, "rev-list", "--count", f"HEAD..{base_branch}"
    ).stdout.strip()
    if not ahead or ahead == "0":
        return None
    behind = _git(
        worktree_path, "rev-list", "--count", f"{base_branch}..HEAD"
    ).stdout.strip()
    if behind and behind != "0":
        return None
    result = _git(worktree_path, "merge", "--ff-only", base_branch)
    if result.returncode != 0:
        return (
            f"failed to fast-forward {worktree_path} onto {base_branch}: "
            f"{result.stderr.strip()}"
        )
    _adopt_space_patterns(worktree_path, wopal)
    return None


def _adopt_space_patterns(worktree_path: Path, wopal: Path) -> None:
    """Widen a worktree over every pattern the space range carries."""
    space_patterns = sparse.read_patterns(wopal)
    if not space_patterns:
        return
    own = sparse.read_patterns(worktree_path)
    missing = [item for item in space_patterns if item not in own]
    if missing:
        _git(worktree_path, "sparse-checkout", "add", *missing)


def _widen_worktree_over_branch(
    worktree_path: Path, wopal: Path, base_branch: str, branch: str
) -> None:
    """Give a re-attached worktree back the visibility its range died with.

    The lost worktree's pattern list lived in its git dir and is gone with
    the directory; the branch it checked out still carries what that range
    had to cover. Widening over the branch's own changed paths reconstructs
    exactly that, so the implementer sees the work again and the integrate
    corpus assertion does not fire on it later.
    """
    result = _git(wopal, "diff", "--name-only", "-z", f"{base_branch}...{branch}")
    paths = [item for item in result.stdout.split("\0") if item]
    if paths:
        sparse.widen(worktree_path, paths)


def _cleanup_failed_derive(
    wopal: Path, target: Path, branch: str, *, remove_branch: bool
) -> None:
    """Best-effort removal of the artifacts a failed accept just created.

    Only ever called for artifacts this run created: a branch that was
    verified absent a moment ago, or a worktree re-attached to a branch
    that predates this run (the branch is never touched in that case — its
    commits are possibly-unmerged work).
    """
    if worktree.worktree_exists(target):
        _git(wopal, "worktree", "remove", "--force", str(target))
    _git(wopal, "worktree", "prune")
    if remove_branch:
        _git(wopal, "branch", "-D", branch)


def _commit_proposal(path: Path, message: str) -> bool:
    """Commit the proposal file wherever it currently lives.

    False means the file could not be recorded (for example it is untracked,
    or unrelated changes are staged) — the caller treats that as a refusal,
    because a proposal whose metadata is not on the branch cannot be
    integrated cleanly later.
    """
    work_dir = _enclosing_repo(path)
    if work_dir is None:
        return True
    relative = str(path.resolve().relative_to(work_dir.resolve()))
    if not _has_pending(work_dir, [relative]):
        return True
    return _commit_paths(work_dir, [relative], message)


def _has_pending(work_dir: Path, paths: list[str]) -> bool:
    """Whether any of `paths` has an uncommitted change."""
    result = _git(work_dir, "status", "--porcelain", "-z", "--", *paths)
    return bool(result.stdout.strip())


def _sync_record(path: Path, message: str) -> bool:
    """Reconcile the proposal across the space branch and the isolated worktree.

    The proposal is tracked on the space branch, but the commands run from
    wherever the user happens to be — often the isolated worktree. Two things
    have to stay true:

    1. **The space branch carries the record.** Otherwise the mutation sits
       uncommitted in `.wopal` and blocks the next `integrate`, which refuses
       a dirty workspace by design.
    2. **Both copies agree.** Otherwise the worktree's checked-out file reads
       as a modification and blocks `integrate` the same way.

    Both of the proposal's possible locations are staged, so archiving (which
    moves the file) records its deletion as well as its new path.

    Outside a space (no `.wopal`) there is nothing to reconcile against: the
    proposal's own directory is the only copy. That is the shape the CLI
    tests use.
    """
    space = _space_root(_root())
    wopal = worktree.space_worktree_path(space)

    if not wopal.is_dir():
        work_dir = _enclosing_repo(path)
        if work_dir is None:
            return True
        relative = str(path.resolve().relative_to(work_dir.resolve()))
        if not _has_pending(work_dir, [relative]):
            return True
        return _commit_paths(work_dir, [relative], message)

    candidates = [repo.evolutions_root(wopal) / path.name, path]
    if path.parent.name == "archived":
        candidates.insert(1, path.parent / path.name)
        # A dated archive (`YYYYMMDD-<name>.md`) removed the undated active
        # copy; the record commit must stage that deletion too, or the space
        # worktree is left dirty with a phantom `D` entry.
        dated = re.compile(r"^\d{8}-(?P<stem>.+\.md)$")
        match = dated.match(path.name)
        if match:
            # The stem group already carries the `.md` suffix; appending
            # another produced `x.md.md` and silently missed the deletion.
            candidates.append(repo.evolutions_root(wopal) / match.group("stem"))
    else:
        candidates.append(repo.archived_root(wopal) / path.name)
    canonical = next((item for item in candidates if item.is_file()), candidates[0])

    # Adopt the caller's content into the canonical location.
    if canonical.resolve() != path.resolve() and path.is_file():
        canonical.write_text(path.read_text())

    work_dir = _enclosing_repo(canonical)
    if work_dir is None:
        return True

    relatives = [
        str(item.resolve().relative_to(work_dir.resolve()))
        for item in candidates
        if work_dir.resolve() in item.resolve().parents
    ]
    pending = [item for item in relatives if _has_pending(work_dir, [item])]
    if pending:
        if not _commit_paths(work_dir, pending, message):
            return False

    _mirror_into_worktree(space, path.name, canonical)
    return True


def _mirror_into_worktree(space: Path, name: str, canonical: Path) -> None:
    """Keep the isolated worktree's proposal copy identical to the canonical one.

    The copy is committed too: an uncommitted mirror is indistinguishable
    from unfinished work, and `integrate` refuses a dirty worktree.

    `name` is the file's CURRENT name, which for an archived proposal is the
    dated form (`YYYYMMDD-<name>.md`). The worktree's stale active copy
    (undated) is removed alongside, so a dated archive leaves no double
    copy behind.
    """
    recorded = proposal.get_field(canonical, "Worktree") or ""
    if not recorded or recorded == "(none)":
        return
    work_dir = _recorded(space, recorded)
    if not worktree.worktree_exists(work_dir):
        return

    copy = work_dir / "docs" / "evolutions" / name
    archived_copy = work_dir / "docs" / "evolutions" / "archived" / name

    if canonical.parent.name == "archived":
        # The canonical copy moved into archived/ (possibly with a date
        # prefix). Mirror the move and remove the stale active copy — the
        # undated original this proposal used before archiving.
        stale_names = {name}
        dated = re.compile(r"^\d{8}-(?P<stem>.+\.md)$")
        match = dated.match(name)
        if match:
            stale_names.add(match.group("stem"))
        moved = False
        if not archived_copy.is_file() or archived_copy.read_text() != canonical.read_text():
            archived_copy.parent.mkdir(parents=True, exist_ok=True)
            archived_copy.write_text(canonical.read_text())
            moved = True
        for stale in stale_names:
            active = work_dir / "docs" / "evolutions" / stale
            if active.is_file():
                active.unlink()
                moved = True
        if moved:
            # Stage exactly what changed under the proposal's docs tree.
            # porcelain -z entries are `XY <path>` (two status letters, one
            # space); untracked directories collapse to `dir/`, so unroll
            # them with ls-files instead of trusting the collapsed entry.
            targets = _zlines(
                _git(work_dir, "status", "--porcelain", "-z", "--", "docs/evolutions")
            )
            paths: set[str] = set()
            for entry in targets:
                path = entry[3:] if len(entry) > 3 else ""
                if not path:
                    continue
                if path.endswith("/"):
                    unrolled = _zlines(
                        _git(
                            work_dir,
                            "ls-files",
                            "--others",
                            "--exclude-standard",
                            "-z",
                            "--",
                            path,
                        )
                    )
                    paths.update(unrolled or [path])
                else:
                    paths.add(path)
            ordered = sorted(paths)
            if ordered:
                _commit_paths(
                    work_dir,
                    ordered,
                    f"docs(evolutions): archive {Path(name).stem}",
                )
        return

    if not copy.is_file() or copy.resolve() == canonical.resolve():
        return
    if copy.read_text() == canonical.read_text():
        return
    copy.write_text(canonical.read_text())
    _commit_paths(
        work_dir,
        [str(copy.resolve().relative_to(work_dir.resolve()))],
        f"docs(evolutions): sync {Path(name).stem}",
    )


def _pending_content(wopal: Path, branch: str) -> list[str]:
    """Paths whose content differs between the space branch and `branch`.

    Excludes the proposal file itself: the space branch advances it with the
    accept and stage records, so it always differs and reporting it would
    make the notice permanent noise rather than a real signal.
    """
    result = _git(wopal, "diff", "--name-only", "-z", f"HEAD..{branch}")
    paths = [item for item in result.stdout.split("\0") if item]
    return [item for item in paths if not item.startswith("docs/evolutions/")]


def _enclosing_repo(path: Path) -> Path | None:
    """The git worktree that tracks `path`."""
    result = _git(path.parent, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())

def _staging_candidates(work_dir: Path) -> list[str]:
    """Paths that belong in the next commit: new, modified, or already staged.

    Collected by name rather than by `git add -A`, so a corrupted checkout
    cannot turn "stage everything" into "record the pool as deleted".

    Build output is dropped explicitly as well as via the ignore rules: a
    repository that forgot to ignore `__pycache__/` would otherwise have it
    swept into the commit by the very command that is supposed to be safe.
    """
    paths = set(sparse.untracked_paths(work_dir))
    for args in (
        ("diff", "--name-only", "-z"),
        ("diff", "--cached", "--name-only", "-z"),
    ):
        paths.update(_zlines(_git(work_dir, *args)))
    return [
        path for path in sorted(paths) if path and not sparse.is_transient(path)
    ]


def cmd_commit(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh commit <name> -m <message>")
    if not args.message:
        return _fail("a commit message is required: evo.sh commit <name> -m <message>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    refused = _guard_stage("commit", path)
    if refused is not None:
        return refused

    mode = proposal.get_field(path, "Mode") or ""
    if mode not in ("isolated", "quick"):
        return _fail(
            f"{path.name} has no recorded Mode; run `evo.sh accept <name>` first"
        )

    if mode == "quick" and not args.paths and not args.all_paths:
        return _fail(
            "quick mode commits into the live space worktree, so it stages only "
            "the paths you name: pass `--paths <path>...` or `--all` "
            "(the proposal file is always included)"
        )

    work_dir, error = _resolve_work_dir(path, mode)
    if error or work_dir is None:
        return _fail(error or "cannot resolve the working directory")

    problems = sparse.preflight(work_dir)
    if problems:
        return _fail("refusing to commit: " + "; ".join(problems))

    if mode == "quick":
        if args.all_paths:
            # Multi-file fixes should not need one --paths entry per file.
            # Still by name and still transient-free: `_staging_candidates`
            # is the same collector isolated mode uses.
            targets = _staging_candidates(work_dir)
        else:
            targets = _quick_targets(path, work_dir, args.paths)
        try:
            inside = path.resolve().relative_to(work_dir.resolve())
        except ValueError:
            inside = None
        if inside is not None and str(inside) not in targets:
            targets.append(str(inside))
    else:
        targets = _staging_candidates(work_dir)

    if not targets:
        print("nothing to commit")
        return 0

    # New paths must enter the range BEFORE staging: `--sparse` would force
    # the index entry, and the next range recompute would sweep the file off
    # disk. A path whose parent is outside the range needs widening too,
    # otherwise the very same `git add` fails.
    try:
        added = sparse.widen(work_dir, targets)
    except sparse.SparseError as exc:
        return _fail(str(exc))

    if added:
        # Widening rewrites the index and refreshes the bits; re-check so a
        # range that just changed cannot hide an incoherent state.
        problems = sparse.preflight(work_dir)
        if problems:
            return _fail("refusing to commit: " + "; ".join(problems))

    staged = _git(work_dir, "add", "--", *sorted(set(targets)))
    if staged.returncode != 0:
        return _fail(f"failed to stage changes: {staged.stderr.strip()}")

    committed = _git(work_dir, "commit", "-m", args.message)
    if committed.returncode != 0:
        if "nothing to commit" in (committed.stdout + committed.stderr):
            print("nothing to commit")
            return 0
        return _fail(f"commit failed: {committed.stderr.strip()}")

    head = _git(work_dir, "rev-parse", "HEAD").stdout.strip()
    print(f"commit  : {head[:12]} ({len(set(targets))} path(s))")
    for item in sorted(set(targets)):
        print(f"          {item}")
    if added:
        print(f"widened : {', '.join(added)}")
    if mode == "isolated":
        print(f"next    : evo.sh integrate {path.stem}")
    return 0


def _quick_targets(path: Path, work_dir: Path, requested: list[str]) -> list[str]:
    """Validate an explicit quick-mode path list.

    Each entry must be an existing path inside the worktree that git already
    tracks or that is untracked — the point of the explicit list is that a
    stray file never rides along into the space branch.
    """
    targets: list[str] = []
    for raw in requested:
        candidate = raw.strip()
        if not candidate or sparse.is_transient(candidate):
            continue
        if not (work_dir / candidate).exists():
            continue
        targets.append(candidate)
    return targets


def cmd_fix(args: argparse.Namespace) -> int:
    """Commit a defect fix directly on the space branch — no proposal.

    A defect is existing, already-agreed behavior that is wrong; restoring
    intent needs no design review, no isolated worktree, and no validation
    gate. The commit is the record. Everything safety-relevant still holds:
    the sparse preflight runs first, the range widens before staging, and
    staging is by name.
    """
    if not args.message:
        return _fail(
            "a commit message is required: evo.sh fix -m <message> "
            "(--paths <path>... | --all)"
        )
    if not args.paths and not args.all_paths:
        return _fail(
            "name the paths to commit (`--paths <path>...`) or stage every "
            "change (`--all`)"
        )

    space = _space_root(_root())
    wopal = worktree.space_worktree_path(space)
    if not wopal.is_dir():
        return _fail(
            "no space assembly worktree found; `fix` commits on the space branch"
        )
    current = worktree.current_branch(wopal)
    if not current.startswith("space/"):
        return _fail(
            f"the space worktree is on {current!r}, not a 'space/*' branch; "
            "refusing to commit a fix there"
        )

    problems = sparse.preflight(wopal)
    if problems:
        return _fail("refusing to commit: " + "; ".join(problems))

    if args.all_paths:
        targets = _staging_candidates(wopal)
    else:
        targets, invalid = _fix_targets(wopal, args.paths)
        if invalid:
            return _fail(
                "these paths are neither on disk nor tracked, so there is "
                "nothing to commit for them: " + ", ".join(invalid)
            )
    if not targets:
        print("nothing to commit")
        return 0

    try:
        added = sparse.widen(wopal, targets)
    except sparse.SparseError as exc:
        return _fail(str(exc))

    if added:
        problems = sparse.preflight(wopal)
        if problems:
            return _fail("refusing to commit: " + "; ".join(problems))

    staged = _git(wopal, "add", "--", *sorted(set(targets)))
    if staged.returncode != 0:
        return _fail(f"failed to stage changes: {staged.stderr.strip()}")

    committed = _git(wopal, "commit", "-m", args.message)
    if committed.returncode != 0:
        if "nothing to commit" in (committed.stdout + committed.stderr):
            print("nothing to commit")
            return 0
        return _fail(f"commit failed: {committed.stderr.strip()}")

    head = _git(wopal, "rev-parse", "HEAD").stdout.strip()
    print(f"commit  : {head[:12]} ({len(set(targets))} path(s))")
    for item in sorted(set(targets)):
        print(f"          {item}")
    if added:
        print(f"widened : {', '.join(added)}")
    print("record  : none (the commit is the record)")
    return 0


def _fix_targets(work_dir: Path, requested: list[str]) -> tuple[list[str], list[str]]:
    """Validate explicit fix paths: each must be on disk or tracked.

    A deleted tracked path is valid (a rename records its deletion); an
    unknown path is refused loudly rather than silently dropped.
    """
    targets: list[str] = []
    invalid: list[str] = []
    for raw in requested:
        candidate = raw.strip()
        if not candidate or sparse.is_transient(candidate):
            continue
        on_disk = (work_dir / candidate).exists()
        tracked = bool(_git(work_dir, "ls-files", "--", candidate).stdout.strip())
        if on_disk or tracked:
            targets.append(candidate)
        else:
            invalid.append(candidate)
    return targets, invalid


def cmd_integrate(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh integrate <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    refused = _guard_stage("integrate", path)
    if refused is not None:
        return refused

    mode = proposal.get_field(path, "Mode") or ""
    if mode != "isolated":
        return _fail(
            f"{path.name} mode is {mode or 'unset'!r}; integration only applies to "
            "isolated mode (quick mode commits directly on the space branch)"
        )

    space = _space_root(_root())
    branch = proposal.get_field(path, "Branch") or ""
    if not branch or branch == "(none)":
        return _fail(f"{path.name} has no recorded Branch; re-run `evo.sh accept`")

    recorded = proposal.get_field(path, "Worktree") or ""
    work_dir = (
        _recorded(space, recorded) if recorded and recorded != "(none)" else None
    )
    if work_dir is None:
        return _fail(
            f"{path.name} has no recorded Worktree; re-run `evo.sh accept` "
            "before integrating"
        )

    if work_dir is not None and worktree.worktree_exists(work_dir):
        dirty = _git(work_dir, "status", "--porcelain").stdout.strip()
        if dirty:
            return _fail(
                f"{work_dir} has uncommitted changes; run `evo.sh commit` first"
            )

    message = args.message or f"evolve({path.stem}): squash validated work"
    try:
        squashed = worktree.integrate(space, branch, message, work_dir)
    except worktree.WorktreeError as exc:
        return _fail(str(exc))

    wopal = worktree.space_worktree_path(space)
    if squashed is None:
        print(f"{path}")
        print("integrate: the space branch already contains every change (no-op)")
        return 0

    # `Final Commit` is the squash that carries the content into the space
    # branch. It cannot be written before the squash exists, so it lands as a
    # follow-up doc commit on the space branch — the branch the delivery
    # decision reads from. The squashed tree itself is byte-identical to the
    # feature tree; this commit only annotates it.
    _record_final_commit(path, wopal, squashed)

    print(f"{path}")
    print(f"integrated into {worktree.current_branch(wopal)} at {squashed[:12]}")
    print(f"stage   : {proposal.get_stage(path)}")
    return 0


def _record_final_commit(path: Path, wopal: Path, squashed: str) -> None:
    """Write `Final Commit` into the space-branch copy of the proposal."""
    canonical = wopal / "docs" / "evolutions" / path.name
    if not canonical.is_file():
        return
    proposal.set_field(canonical, "Final Commit", squashed)
    relative = str(canonical.resolve().relative_to(wopal.resolve()))
    _commit_paths(
        wopal,
        [relative],
        f"docs(evolutions): record integrated commit {squashed[:12]}",
    )


def cmd_check(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh check <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    problems: list[str] = []
    notices: list[str] = []

    stage = proposal.get_stage(path)
    if stage is None:
        problems.append("metadata: missing `- **Stage**:` field")
    elif not proposal.is_state(stage):
        problems.append(f"metadata: unknown stage {stage!r}")

    for field in ("Type", "Project Path", "Created"):
        if not proposal.get_field(path, field):
            problems.append(f"metadata: missing field {field}")

    created = proposal.get_field(path, "Created") or ""
    if created and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", created):
        problems.append(f"metadata: Created {created!r} is not an ISO date")

    # A draft is expected to be full of placeholders — failing it would punish
    # the workflow for working as designed. From `accepted` onward an
    # unreplaced placeholder means the proposal was never actually written.
    draft = stage == "draft"
    mode = proposal.get_field(path, "Mode") or ""

    text = path.read_text()
    if draft:
        remaining = PLACEHOLDER_RE.findall(_prose(text))
        if remaining:
            notices.append(
                f"stage is 'draft': {len(remaining)} placeholder(s) are "
                "expected until the proposal is accepted"
            )
        # The structure contract is advisory in draft: warn, do not fail —
        # a scaffold is allowed to be mid-authoring.
        for item in _structure_problems(text):
            notices.append(item)
    else:
        if mode not in ("isolated", "quick"):
            problems.append(
                f"metadata: Mode is {mode or 'unset'!r}; "
                "expected 'isolated' or 'quick'"
            )
        for placeholder in PLACEHOLDER_RE.findall(_prose(text)):
            problems.append(f"content: unreplaced placeholder {placeholder}")
        # From accepted onward the contract is hard: an ill-structured
        # proposal has been gated into implementation.
        problems.extend(_structure_problems(text))

    # Corpus lint (D-04): the archive corpus is dated; bare names are
    # outliers worth surfacing wherever check runs. Notes, not failures —
    # history is not rewritten by a lint.
    archived_root = repo.archived_root(
        worktree.space_worktree_path(_space_root(_root()))
    )
    if archived_root.is_dir():
        undated = [
            item.name
            for item in sorted(archived_root.iterdir())
            if item.suffix == ".md" and not re.match(r"^\d{8}-", item.name)
        ]
        for name in undated[:10]:
            notices.append(
                f"corpus: archived file {name!r} lacks the YYYYMMDD- prefix"
            )

    space = _space_root(_root())
    wopal = worktree.space_worktree_path(space)

    if wopal.is_dir():
        current = worktree.current_branch(wopal)
        if not current.startswith("space/"):
            problems.append(
                f"structure: the space worktree is on {current!r}, "
                "expected a 'space/*' branch"
            )

    if mode in ("isolated", "quick"):
        recorded = proposal.get_field(path, "Worktree") or ""
        recorded_dir = (
            _recorded(space, recorded)
            if recorded and recorded != "(none)"
            else None
        )
        # The archived terminal state is the one place a missing worktree is
        # expected: `archive` removes the isolation artifacts by design. A
        # surviving branch there means the cleanup did not finish — a notice,
        # not a failure (the content is integrated; 2026-09-23 fix).
        archived_clean = (
            stage == "archived"
            and mode == "isolated"
            and (recorded_dir is None or not worktree.worktree_exists(recorded_dir))
        )
        if archived_clean:
            branch = proposal.get_field(path, "Branch") or ""
            if (
                branch
                and branch != "(none)"
                and worktree.reference_exists(wopal, f"refs/heads/{branch}")
            ):
                notices.append(
                    f"branch {branch!r} still exists although the proposal is "
                    "archived; isolation cleanup did not finish — remove it "
                    "once you have confirmed its content is integrated"
                )
        else:
            work_dir, error = _resolve_work_dir(path, mode)
            if error or work_dir is None:
                problems.append(
                    f"sparse: {error or 'cannot resolve the working directory'}"
                )
            else:
                problems.extend(f"sparse: {item}" for item in sparse.preflight(work_dir))
            if work_dir is not None and not error and mode == "isolated":
                problems.extend(
                    f"isolation: {item}"
                    for item in worktree.assert_isolated(space, work_dir)
                )
                branch = proposal.get_field(path, "Branch") or ""
                if branch and worktree.reference_exists(wopal, f"refs/heads/{branch}"):
                    # Commits ahead of the space branch are not by themselves
                    # a problem: the space branch legitimately carries the
                    # accept and stage records the worktree does not. What
                    # matters is whether any *content* is missing, so compare
                    # the trees instead of counting commits.
                    pending_content = _pending_content(wopal, branch)
                    if pending_content:
                        sample = ", ".join(pending_content[:5])
                        notices.append(
                            f"{len(pending_content)} path(s) on {branch} are not "
                            f"integrated into the space branch yet ({sample})"
                        )
                elif branch:
                    notices.append(
                        f"branch {branch!r} does not exist yet (nothing committed)"
                    )

    if problems:
        print(f"{path}: {len(problems)} problem(s)", file=sys.stderr)
        for item in problems:
            print(f"  - {item}", file=sys.stderr)
        for item in notices:
            print(f"  note: {item}", file=sys.stderr)
        return 1

    print(f"{path}: OK (stage={stage}, mode={mode or 'unset'})")
    for item in notices:
        print(f"  note: {item}")
    return 0


def _archive_name(name: str) -> str:
    """The dated name every archived proposal carries (a pure function).

    The corpus convention is `YYYYMMDD-<name>.md` — sortable, self-describing,
    and what 74 of 75 historical files already look like. Keeping it a pure
    function (date + name in, filename out) makes it testable and gives
    `_resolve_proposal` a deterministic thing to invert.
    """
    return f"{date.today().strftime('%Y%m%d')}-{name}"


def cmd_archive(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh archive <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    stage = proposal.get_stage(path)
    if stage is None:
        return _fail(f"{path} has no `- **Stage**:` field")
    refused = _guard_stage("archive", path)
    if refused is not None:
        return refused
    if path.parent.name == "archived":
        return _fail(f"{path.name} is already archived")

    # The canonical copy lives on the space branch, so the move happens
    # there; `_sync_record` then mirrors it into the derived worktree. Moving
    # the copy the command happened to resolve would leave the archived file
    # inside the isolated worktree and absent from the live space.
    space = _space_root(_root())
    wopal = _space_worktree(_root())

    # ── preflight: every check runs before the first mutation ────────────
    # A corrupted space range must not be the stage a cleanup runs on, and
    # an uncommitted anything blocks the record commit the move depends on.
    if wopal.is_dir() and wopal == worktree.space_worktree_path(space):
        problems = sparse.preflight(wopal)
        if problems:
            return _fail(
                "refusing to archive: the space worktree is not coherent: "
                + "; ".join(problems)
            )
        dirty = _git(wopal, "status", "--porcelain").stdout.strip()
        if dirty:
            return _fail(
                "refusing to archive: the space worktree has uncommitted "
                f"changes: {dirty[:200]}"
            )

    mode = proposal.get_field(path, "Mode") or ""
    branch = proposal.get_field(path, "Branch") or ""
    recorded = proposal.get_field(path, "Worktree") or ""
    work_dir = _recorded(space, recorded) if recorded and recorded != "(none)" else None

    # Cleanup preflight: the isolation artifacts are only removed when the
    # feature content is fully integrated — deleting a branch that still
    # carries work destroys it (probe R). The guard mirrors dev-flow's
    # check_branch_merged: refuse before touching anything.
    will_clean = (
        mode == "isolated"
        and not args.keep_worktree
        and work_dir is not None
        and (work_dir.exists() or not _branch_is_gone(wopal, branch))
    )
    if will_clean and branch and branch != "(none)":
        pending = _pending_content(wopal, branch)
        if pending:
            sample = ", ".join(pending[:5])
            return _fail(
                f"refusing to archive: {len(pending)} path(s) on {branch!r} are "
                f"not integrated into the space branch ({sample}); run "
                "`evo.sh integrate <name>` first"
            )

    target_dir = repo.archived_root(wopal)
    target_name = _archive_name(path.name)
    target = target_dir / target_name
    if target.exists():
        return _fail(
            f"{target} already exists; refusing to overwrite"
        )

    # ── mutations: preflight passed, run in order, stop on first failure ─
    if target_dir != path.parent:
        target_dir.mkdir(parents=True, exist_ok=True)
        if target.resolve() != path.resolve():
            shutil.move(str(path), str(target))
    if not _sync_record(target, f"docs(evolutions): archive {target.stem}"):
        return _fail(
            "archive move could not be recorded on the space branch; the "
            "repository is unchanged — resolve the reported commit failure "
            "and re-run `evo.sh archive`"
        )

    # Cleanup last: it is the only step that can be safely skipped or
    # retried, and it must never run before the move is recorded.
    if will_clean:
        _cleanup_isolation(space, work_dir, wopal, branch, keep=False)

    print(target.resolve())
    if will_clean:
        print("cleaned : worktree and branch removed (--keep-worktree to keep)")
    elif mode == "isolated" and args.keep_worktree:
        print("kept    : worktree and branch preserved (--keep-worktree)")
    return 0


def _branch_is_gone(wopal: Path, branch: str) -> bool:
    return not worktree.reference_exists(wopal, f"refs/heads/{branch}")


def _cleanup_isolation(
    space: Path, work_dir: Path | None, wopal: Path, branch: str, *, keep: bool
) -> None:
    """Remove the isolation artifacts the metadata declares (post-integrate).

    Targets are taken from the proposal's metadata only — never discovered by
    name similarity. Cleanup failure is loud: partial removal leaves the
    repository usable but the residue visible, so it prints to stderr rather
    than failing the (already archived) command.
    """
    if work_dir is not None and worktree.worktree_exists(work_dir):
        result = _git(wopal, "worktree", "remove", "--force", str(work_dir))
        if result.returncode != 0:
            print(
                f"WARNING: failed to remove worktree {work_dir}: "
                f"{result.stderr.strip()}",
                file=sys.stderr,
            )
            return
    _git(wopal, "worktree", "prune")
    if branch and branch != "(none)" and not _branch_is_gone(wopal, branch):
        # `-D`, not `-d`: the integrated squash is not an ancestor of the
        # feature branch (squash rewrites history by design), so `-d` refuses
        # every legitimate cleanup. Safety comes from the caller's
        # `_pending_content` guard — content proven integrated — never from
        # the ancestry check.
        result = _git(wopal, "branch", "-D", branch)
        if result.returncode != 0:
            print(
                f"WARNING: branch {branch!r} was not fully integrated or "
                f"could not be deleted: {result.stderr.strip()}",
                file=sys.stderr,
            )


def _space_worktree(root: Path) -> Path:
    """The `.wopal` worktree when there is one, else the given root.

    Every command that touches the canonical proposal goes through this: the
    proposal belongs to the space branch, so that is where it must be read
    and written, whether the command was run from the live space or from an
    isolated worktree.
    """
    space = _space_root(root)
    wopal = worktree.space_worktree_path(space)
    return wopal if wopal.is_dir() else root


# ── wiring ──────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=True, description=SKILL_NAME)
    sub = parser.add_subparsers(dest="command")

    p_new = sub.add_parser("new", help="create a proposal")
    p_new.add_argument("title", nargs="?", default="")
    p_new.add_argument("--type", default="enhance", help="proposal type (default: enhance)")
    p_new.set_defaults(func=cmd_new)

    p_status = sub.add_parser("status", help="show proposal status")
    p_status.add_argument("name", nargs="?", default="")
    p_status.set_defaults(func=cmd_status)

    p_accept = sub.add_parser("accept", help="accept a proposal for implementation")
    p_accept.add_argument("name", nargs="?", default="")
    p_accept.add_argument(
        "--no-worktree",
        dest="no_worktree",
        action="store_true",
        help="skip worktree derivation and implement directly on the space branch",
    )
    p_accept.set_defaults(func=cmd_accept)

    p_advance = sub.add_parser("advance", help="advance the state machine")
    p_advance.add_argument("name", nargs="?", default="")
    p_advance.add_argument("--to", default="", help="target state")
    p_advance.set_defaults(func=cmd_advance)

    p_commit = sub.add_parser("commit", help="sparse-safe commit of working changes")
    p_commit.add_argument("name", nargs="?", default="")
    p_commit.add_argument("-m", "--message", default="", help="commit message")
    p_commit.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="explicit paths to stage (quick mode)",
    )
    p_commit.add_argument(
        "--all",
        dest="all_paths",
        action="store_true",
        help="stage every changed path (quick mode multi-file fixes)",
    )
    p_commit.set_defaults(func=cmd_commit)

    p_fix = sub.add_parser(
        "fix", help="immediate defect repair: commit on the space branch (no proposal)"
    )
    p_fix.add_argument("-m", "--message", default="", help="commit message")
    p_fix.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="explicit paths to commit",
    )
    p_fix.add_argument(
        "--all",
        dest="all_paths",
        action="store_true",
        help="stage every changed path",
    )
    p_fix.set_defaults(func=cmd_fix)

    p_integrate = sub.add_parser("integrate", help="squash isolated work into the space branch")
    p_integrate.add_argument("name", nargs="?", default="")
    p_integrate.add_argument("-m", "--message", default="", help="squash commit message")
    p_integrate.set_defaults(func=cmd_integrate)

    p_check = sub.add_parser("check", help="report proposal and sparse-state problems")
    p_check.add_argument("name", nargs="?", default="")
    p_check.set_defaults(func=cmd_check)

    p_archive = sub.add_parser("archive", help="move an archived proposal")
    p_archive.add_argument("name", nargs="?", default="")
    p_archive.add_argument(
        "--keep-worktree",
        dest="keep_worktree",
        action="store_true",
        help="keep the isolated worktree and branch instead of cleaning up",
    )
    p_archive.set_defaults(func=cmd_archive)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2

    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "func", None):
        print(USAGE, file=sys.stderr)
        return 2

    try:
        return args.func(args)
    except proposal.ProposalError as exc:
        return _fail(str(exc))
    except repo.RepoRootError as exc:
        return _fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
