#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# proposal.py - Evolution proposal state machine and `Stage` field access.
#
# State machine contract (docs/DESIGN-evolution.md, Evolution Workflow States):
#
#   draft -> accepted -> implementing -> validating -> archived
#
# The vocabulary deliberately shares no words with the code-development
# workflow (`planning / reviewing / approved / executing / verifying /
# done`) so the two flows cannot be confused inside one space.

import re
from pathlib import Path

STATES: tuple[str, ...] = (
    "draft",
    "accepted",
    "implementing",
    "validating",
    "archived",
)

_STAGE_RE = re.compile(r"^\- \*\*Stage\*\*:[ \t]*(.+?)[ \t]*$", re.MULTILINE)


def _field_re(field: str) -> re.Pattern:
    return re.compile(rf"^\- \*\*{re.escape(field)}\*\*:[ \t]*(.*?)[ \t]*$", re.MULTILINE)


def _unquote(value: str) -> str:
    """Strip one surrounding markdown code span from a metadata value.

    Hand-authored proposals read naturally with `` `value` `` (the semantic
    lane writes prose, not machine output), but consumers need the literal:
    a branch name or worktree path handed to git must not carry backticks.
    """
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] == "`":
        return text[1:-1].strip()
    return text


def get_field(path: str | Path, field: str) -> str | None:
    """Read an arbitrary `- **Field**:` metadata value, or None when absent."""
    file_path = Path(path)
    if not file_path.is_file():
        return None
    match = _field_re(field).search(file_path.read_text())
    return _unquote(match.group(1)) if match else None


def set_field(path: str | Path, field: str, value: str) -> bool:
    """Write a metadata field in place. Returns True when the file changed.

    Replacing in place keeps repeated writes from growing duplicate lines,
    which is what makes `accept` idempotent when re-run.
    """
    file_path = Path(path)
    text = file_path.read_text()
    pattern = _field_re(field)
    if pattern.search(text) is None:
        raise ProposalError(
            f"{file_path.name} has no `- **{field}**:` field; "
            "recreate the proposal with `evo.sh new`"
        )
    if get_field(file_path, field) == value:
        return False
    updated, count = pattern.subn(lambda m: f"- **{field}**: {value}", text, count=1)
    if count != 1:
        raise ProposalError(f"failed to update {field} in {file_path}")
    file_path.write_text(updated)
    return True


class ProposalError(Exception):
    """Raised for malformed proposals or illegal operations."""


def is_state(value: str) -> bool:
    return value in STATES


def next_states(state: str) -> list[str]:
    """Return the legal successors of ``state`` (empty when terminal)."""
    if state not in STATES:
        return []
    index = STATES.index(state)
    return list(STATES[index + 1 : index + 2])


def validate_transition(current: str, target: str) -> tuple[bool, str | None]:
    """Validate a state change. Returns ``(ok, error_message)``.

    Re-advancing to the current state is legal and idempotent: callers use
    it to re-run a command without side effects. Anything else that is not
    the single legal successor is rejected.
    """
    if not is_state(target):
        return False, (
            f"unknown state {target!r}; "
            f"legal states: {', '.join(STATES)}"
        )

    if not is_state(current):
        return False, (
            f"proposal has unknown stage {current!r}; "
            f"legal states: {', '.join(STATES)}"
        )

    if target == current:
        return True, None

    successors = next_states(current)
    if target in successors:
        return True, None

    legal = ", ".join(successors) if successors else "none (terminal state)"
    return False, (
        f"illegal transition {current} -> {target}; "
        f"legal next state: {legal}"
    )


def get_stage(path: str | Path) -> str | None:
    """Read the proposal's ``Stage`` field, or ``None`` when absent."""
    file_path = Path(path)
    if not file_path.is_file():
        return None
    match = _STAGE_RE.search(file_path.read_text())
    return _unquote(match.group(1)) if match else None


def set_stage(path: str | Path, stage: str) -> bool:
    """Write ``stage`` into the proposal's ``Stage`` field.

    Returns ``True`` when the file changed, ``False`` when it already held
    the requested stage. The field is replaced in place, so repeated calls
    never grow duplicate lines.
    """
    if not is_state(stage):
        raise ProposalError(f"unknown stage {stage!r}")

    file_path = Path(path)
    text = file_path.read_text()

    if _STAGE_RE.search(text) is None:
        raise ProposalError(
            f"{file_path.name} has no `- **Stage**:` field; "
            "recreate the proposal with `evo.sh new`"
        )

    if get_stage(file_path) == stage:
        return False

    updated, count = _STAGE_RE.subn(f"- **Stage**: {stage}", text, count=1)
    if count != 1:
        raise ProposalError(f"failed to update Stage in {file_path}")

    file_path.write_text(updated)
    return True
