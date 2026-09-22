#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# evo.py - Command entry point for the ontology-evolution mechanism lane.
#
#   evo.sh new <title>                   create docs/evolutions/<name>.md (Stage: draft)
#   evo.sh status <name|path>            print stage, file path, and next command
#   evo.sh accept <name> [--no-worktree] accept for implementation (derive a worktree)
#   evo.sh advance <name> --to <state>   advance the state machine (illegal -> exit 1)
#   evo.sh commit <name> -m <message>    sparse-safe commit of the working changes
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
  commit <name> -m <message>       sparse-safe commit of the working changes
  integrate <name>                 squash the isolated work into the space branch
  check <name>                     report proposal and sparse-state problems
  archive <name>                   move an archived proposal to docs/evolutions/archived/

state machine: draft -> accepted -> implementing -> validating -> archived
"""

PROPOSAL_TEMPLATE = """# {name}

## Metadata

- **Type**: {type}
- **Project Path**: .wopal
- **Created**: {created}
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Goal

<这项本体能力进化要达到什么目标。>

## Scope Assessment

- **Complexity**: <Low | Medium | High>
- **Confidence**: <Low | Medium | High>

## Design

<设计契约：不可改动的部分与必须成立的行为。>

## Changes

<改动清单>

## Verification

<如何在运行时确认改动生效；加载链路变更以重启 ellamaka 后的结果为准。>

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。
"""

# Placeholders the author must replace before a proposal counts as
# implemented. Derived from the template so the two can never drift apart.
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{1,80}>")


def _placeholders() -> list[str]:
    seen: list[str] = []
    for token in PLACEHOLDER_RE.findall(PROPOSAL_TEMPLATE):
        if token not in seen:
            seen.append(token)
    return seen


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


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
    for base in bases:
        for path in (base / f"{ref}.md", base / f"{ref}"):
            if path.is_file():
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
        return None, f"recorded worktree {recorded} is missing; re-run `evo.sh accept`"

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
        PROPOSAL_TEMPLATE.format(
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
    if stage not in ("draft", "accepted"):
        return _fail(
            f"{path.name} is at stage {stage!r}; accept expects 'draft' or 'accepted'"
        )

    space = _space_root(_root())
    slug = path.stem
    wopal = worktree.space_worktree_path(space)

    if args.no_worktree:
        mode, wt_path, branch, base_commit = "quick", "", "", ""
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

        base_commit = _git(wopal, "rev-parse", base_branch).stdout.strip()
        isolated = worktree.slugify(slug)
        target = worktree.derive_path(space, isolated)
        branch = worktree.branch_name(isolated)
        mode, wt_path = "isolated", target

    # `Base Commit` is the commit the isolated work starts from, so it must be
    # read before the metadata commit below moves the space branch forward.
    # Recording the post-metadata head would point a reviewer at a commit
    # that contains none of the work.

    # Metadata is recorded, then the worktree is derived, so the derived copy
    # starts from a tree that already carries it. Writing it afterwards would
    # leave both copies dirty and make the squash merge conflict on the
    # proposal file itself.
    proposal.set_field(path, "Mode", mode)
    proposal.set_field(path, "Worktree", _portable(space, wt_path) if wt_path else "(none)")
    proposal.set_field(path, "Branch", branch or "(none)")
    proposal.set_field(path, "Base Commit", base_commit or "(none)")
    if stage == "draft":
        proposal.set_stage(path, "accepted")

    if not _commit_proposal(path, f"docs(evolutions): accept {slug}"):
        return _fail(
            f"could not record accept metadata in {path}; the proposal has "
            "uncommitted changes that do not belong to this command — commit "
            "or resolve them first"
        )

    if mode == "isolated":
        # The metadata commit advanced the space branch, so the derived
        # worktree is created from that new head and the proposal file it
        # inherits already carries the metadata.
        base_commit = _git(wopal, "rev-parse", base_branch).stdout.strip()
        landed = (
            worktree.current_branch(wt_path) if worktree.worktree_exists(wt_path) else ""
        )
        if landed and landed != branch:
            # Adopting an existing worktree is only safe when it is the one
            # this proposal derived.
            return _fail(
                f"{wt_path} exists but is on {landed!r}, not {branch!r}; "
                "resolve the stale worktree before accepting"
            )
        if not worktree.worktree_exists(wt_path):
            try:
                worktree.derive(space, worktree.slugify(slug), base_commit)
            except worktree.WorktreeError as exc:
                return _fail(str(exc))
        else:
            _fast_forward(wt_path, base_commit)

        problems = worktree.assert_isolated(space, wt_path)
        if problems:
            return _fail(
                "derived worktree failed the isolation checks: " + "; ".join(problems)
            )

    print(f"{path}")
    print(f"Mode    : {mode}")
    if mode == "isolated":
        print(f"Worktree: {proposal.get_field(path, 'Worktree')}")
        print(f"Branch  : {branch}")
    print(f"Stage   : {proposal.get_stage(path)}")
    return 0


def _fast_forward(worktree_path: Path, base_branch: str) -> None:
    """Bring a derived worktree onto the space branch head when it trails.

    A re-run of `accept` (or a space branch that moved since the worktree was
    derived) would otherwise leave the worktree on a stale base and its next
    squash would try to re-apply commits the space branch already has.
    """
    ahead = _git(
        worktree_path, "rev-list", "--count", f"HEAD..{base_branch}"
    ).stdout.strip()
    if ahead and ahead != "0":
        _git(worktree_path, "merge", "--ff-only", base_branch)


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

    candidates = [
        repo.evolutions_root(wopal) / path.name,
        repo.archived_root(wopal) / path.name,
    ]
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
        # The canonical copy moved into archived/; mirror the move.
        if copy.is_file():
            archived_copy.parent.mkdir(parents=True, exist_ok=True)
            archived_copy.write_text(canonical.read_text())
            copy.unlink()
            _commit_paths(
                work_dir,
                ["docs/evolutions/archived", f"docs/evolutions/{name}"],
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

    mode = proposal.get_field(path, "Mode") or ""
    if mode not in ("isolated", "quick"):
        return _fail(
            f"{path.name} has no recorded Mode; run `evo.sh accept <name>` first"
        )

    if mode == "quick" and not args.paths:
        return _fail(
            "quick mode commits into the live space worktree, so it stages only "
            "the paths you name: pass `--paths <path>...` (the proposal file is "
            "always included)"
        )

    work_dir, error = _resolve_work_dir(path, mode)
    if error or work_dir is None:
        return _fail(error or "cannot resolve the working directory")

    problems = sparse.preflight(work_dir)
    if problems:
        return _fail("refusing to commit: " + "; ".join(problems))

    if mode == "quick":
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


def cmd_integrate(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh integrate <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

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

    if work_dir is not None and worktree.worktree_exists(work_dir):
        dirty = _git(work_dir, "status", "--porcelain").stdout.strip()
        if dirty:
            return _fail(
                f"{work_dir} has uncommitted changes; run `evo.sh commit` first"
            )

    message = args.message or f"evolve({path.stem}): squash validated work"
    try:
        squashed = worktree.integrate(space, branch, message)
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

    if draft:
        remaining = PLACEHOLDER_RE.findall(path.read_text())
        if remaining:
            notices.append(
                f"stage is 'draft': {len(remaining)} placeholder(s) are "
                "expected until the proposal is accepted"
            )
    else:
        if mode not in ("isolated", "quick"):
            problems.append(
                f"metadata: Mode is {mode or 'unset'!r}; "
                "expected 'isolated' or 'quick'"
            )
        for placeholder in PLACEHOLDER_RE.findall(path.read_text()):
            problems.append(f"content: unreplaced placeholder {placeholder}")

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
        work_dir, error = _resolve_work_dir(path, mode)
        if error or work_dir is None:
            problems.append(f"sparse: {error or 'cannot resolve the working directory'}")
        else:
            problems.extend(f"sparse: {item}" for item in sparse.preflight(work_dir))
            if mode == "isolated":
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


def cmd_archive(args: argparse.Namespace) -> int:
    if not args.name:
        return _fail("a proposal name is required: evo.sh archive <name>")

    path = _resolve_proposal(args.name)
    if path is None:
        return _fail(f"no proposal named {args.name!r} under docs/evolutions/")

    stage = proposal.get_stage(path)
    if stage is None:
        return _fail(f"{path} has no `- **Stage**:` field")
    if stage != "archived":
        return _fail(
            f"{path.name} is at stage {stage!r}; "
            "advance it to 'archived' before archiving"
        )
    if path.parent.name == "archived":
        return _fail(f"{path.name} is already archived")

    # The canonical copy lives on the space branch, so the move happens
    # there; `_sync_record` then mirrors it into the derived worktree. Moving
    # the copy the command happened to resolve would leave the archived file
    # inside the isolated worktree and absent from the live space.
    target_dir = repo.archived_root(_space_worktree(_root()))
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    if target.exists():
        return _fail(f"{target} already exists")

    if target.resolve() != path.resolve():
        shutil.move(str(path), str(target))
    _sync_record(target, f"docs(evolutions): archive {target.stem}")
    print(target.resolve())
    return 0


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
        help="explicit paths to stage (required in quick mode)",
    )
    p_commit.set_defaults(func=cmd_commit)

    p_integrate = sub.add_parser("integrate", help="squash isolated work into the space branch")
    p_integrate.add_argument("name", nargs="?", default="")
    p_integrate.add_argument("-m", "--message", default="", help="squash commit message")
    p_integrate.set_defaults(func=cmd_integrate)

    p_check = sub.add_parser("check", help="report proposal and sparse-state problems")
    p_check.add_argument("name", nargs="?", default="")
    p_check.set_defaults(func=cmd_check)

    p_archive = sub.add_parser("archive", help="move an archived proposal")
    p_archive.add_argument("name", nargs="?", default="")
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
