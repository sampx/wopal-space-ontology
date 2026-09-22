---
name: ontology-evolution
description: Ontology capability evolution — semantic lane (Maka) plus mechanism lane (state machine, sparse isolation, delivery terminal)
---

# Agent Development Rules

## 1. Canonical References

- Parent Rules: `.wopal/AGENTS.md`
- Skill entry: `SKILL.md`
- Command contract: `references/commands.md`
- Design source of truth: `docs/DESIGN-evolution.md`

## 2. Architecture and Directories

| Directory | Responsibility |
|---|---|
| `scripts/evo.sh` | CLI entry point; resolves its own directory and execs the Python program |
| `scripts/evo.py` | argparse dispatch for every command; owns the proposal template and the staging logic |
| `scripts/lib/repo.py` | Locates the ontology repository root (env override, git toplevel, `docs/evolutions` marker) |
| `scripts/lib/proposal.py` | State machine (`STATES`, `next_states`, `validate_transition`) and metadata field read/write |
| `scripts/lib/sparse.py` | Sparse-checkout reads (`is_enabled`, `read_patterns`, bit inspection) and the `preflight` / `widen` pair |
| `scripts/lib/worktree.py` | Derivation of the isolated worktree, isolation assertions, and squash integration inside `.wopal` |
| `references/` | Command reference and background |
| `tests/python/unit/` | Behavior tests driven through the real `evo.sh` entry point |

The skill operates on the ontology repository that contains it. It never
hard-codes an absolute path: the root is discovered from the script's own
location, which is what lets the same script run from a sparse assembly
worktree and from an isolated implementation worktree.

Sparse state is read and written **only** through `lib/sparse.py`. A direct
`git add -A`, `git checkout`, or `git sparse-checkout` call scattered elsewhere
is how the range and the index drift apart unnoticed.

## 3. Development Commands

| Scenario | Command |
|---|---|
| Run tests | `python3 -m pytest tests/ -q` |
| Show a proposal's stage | `bash scripts/evo.sh status <name>` |
| CLI help | `bash scripts/evo.sh --help` |

Working directory: `skills/ontology-evolution/` (or `.wopal/skills/ontology-evolution/` in a live space).

Runtime dependencies: bash 3.x+, Python 3.10+.

## 4. Implementation Rules

### State Machine

`draft -> accepted -> implementing -> validating -> archived`

The vocabulary deliberately shares no words with `dev-flow`'s
(`planning / reviewing / approved / executing / verifying / done`). Changing a
state name is a contract change: it must be updated here, in
`docs/DESIGN-evolution.md`, and in `references/commands.md` together.

`Stage` is written only by `scripts/lib/proposal.py`. A new command must
declare its precondition stage and its resulting stage, and must refuse —
non-zero exit, file untouched — when the precondition does not hold.

### No Automatic Delivery

`space sync` and `ontology contribute` are the user's terminal decision
(`docs/DESIGN-evolution.md`, Delivery Terminal). No code path in this skill
may invoke a delivery CLI, add a remote, or push. The test suite enforces this
by shimming the delivery CLIs on `PATH` and asserting they are never called.

### Script Conventions

- `evo.sh` must exec the Python program so the exit code propagates unchanged.
- Errors go to stderr, the exit code is non-zero, and a rejected operation
  leaves the proposal file byte-for-byte unmodified.
- Repository root resolution goes through `lib/repo.py`; never re-derive it
  inline.
- Commands that mutate a repository must run every safety check **before** the
  first write, so refusal is side-effect free.

### Sparse Safety Invariants

These are the properties `lib/sparse.py` exists to protect. Any change to it
must keep them true, and each has a test in
`tests/python/unit/test_sparse_safety.py`:

1. **`core.sparseCheckout` is checked by value, not by presence.**
   `git sparse-checkout disable` writes `false`; it does not unset the key.
2. **skip-worktree bits are read from `ls-files --debug` flags, not from the
   `-t` tag letter.** Measured: `ls-files -t` prints `H` for an in-range entry
   whose flags are `0x4000`. CE_SKIP_WORKTREE is `0x4000`; out-of-range entries
   also carry `0x40000000` (`40004000`), so the test is a mask.
3. **Two incoherent states are refused, and they are not equally dangerous.**
   An out-of-range entry *without* the bit makes `git status` report a
   deletion, but `git add -A` still stages nothing while the range is on; it
   becomes a real staged deletion only once the range is switched off
   (`git sparse-checkout disable`). An in-range path *with* a stray bit is the
   mirror image and is remedied by `git sparse-checkout reapply`. Do not
   describe either as instant pool destruction — measured behaviour is the
   three-state table in `references/commands.md`, and the messages the user
   sees have to match it.
4. **Widening is additive and happens before staging.** `git add --sparse` does
   not widen the range, and the next range recompute sweeps the entry off disk.
5. **A directory pattern carries exactly one trailing slash.** `"/skills/x//"`
   is accepted by git and matches nothing, so the following `git add` fails
   with "path exists outside your sparse-checkout definition".
6. **`merge --squash` is the only integration path.** `git push .` to a branch
   checked out elsewhere is refused; `git update-ref` leaves the space worktree
   inconsistent.
7. **Integration widens the space range to match the feature branch before
   merging.** Otherwise a brand-new capability directory lands as an off-disk
   skip-worktree entry: committed, listed, and invisible to the runtime.

## 5. Testing

- Test framework: pytest (tests written with `unittest.TestCase`)
- Test directory: `tests/python/unit/`
- Test support: `tests/python/support/bootstrap.py` injects `scripts/` into `sys.path`
- **TDD requirement**: a new behavior gets a failing test first, then the
  implementation that turns it green

### Test Rules

**R1 Behavior assertions only.** A test asserts an input to output mapping:
exit code, file content, printed result. Asserting internal call sequences,
which branch ran, or searching source text for strings is forbidden — the
implementation must be rewritable without breaking the test.

**R2 Isolation.** Tests that touch the filesystem use
`tempfile.TemporaryDirectory()`. CLI tests set `WOPAL_EVOLUTION_REPO_ROOT` to
point the script at an isolated repository. Tests must never write inside the
skill directory or the live ontology.

**R3 One case per behavior.** Same-shaped cases are `parametrize`d or looped,
not copy-pasted.

**R4 Red-green law.** A new test must first fail against the missing behavior.
A test that cannot fail is decoration.

**R5 No implementation coincidence.** Do not assert incidental details (for
example internal function names); assert the contract in `SKILL.md`.

## 6. User-Supplied Rules

(None)
