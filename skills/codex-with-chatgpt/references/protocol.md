# C2C Session / Request Protocol

C2C connects local Codex to a ChatGPT remote expert agent. A Session represents
one stable work goal and contains many request/response exchanges.

WopalSpace-Bot is ChatGPT-only. Codex uses its own local tools; a failed local
tool call is fixed locally or delegated explicitly as a C2C request.

## Session identity

```text
SESSION_ID: c2c_<stable-goal>
SESSION_GOAL: <one work goal>
```

Normally one Session reuses one ChatGPT conversation. A replacement conversation
keeps the same `SESSION_ID`.

## Request

```text
[C2C]
SESSION_ID: <stable session id>
REQUEST_ID: <unique request id inside this session>

ROLE:
You are the remote expert agent for this Session. Codex is the controller.

SESSION_GOAL:
<stable work goal>

GOAL:
<one concrete expert job>

CONTEXT:
- <path / checkout / commit / evidence pointer>

AVAILABLE_SKILLS:
- .codex/skills/<skill>/SKILL.md — <why relevant>

REQUIRED_SKILLS:
- .codex/skills/<skill>/SKILL.md — <must govern this request>

AUTHORITY:
<what ChatGPT may read/edit/run/decide for this request>

CONSTRAINTS:
<settled boundaries or none>

EXPECTED_RESULT:
<analysis / recommendation / implementation / artifact / review result>

SESSION_DIR:
.wopal-space/c2c/sessions/<SESSION_ID>/

INSTRUCTION:
open_space first. Read root AGENTS.md and its startup chain. Read REQUIRED_SKILLS
before doing the job; use AVAILABLE_SKILLS when relevant. Inspect the real
workspace through WopalSpace-Bot instead of trusting summaries. Follow
AUTHORITY and the owning skills when deciding what may be edited or executed.
Put C2C-owned intermediate artifacts under SESSION_DIR; keep formal workflow
artifacts at their canonical owning-skill paths.

LAST_ACTION:
Record this request's response with:
python3 .codex/skills/codex-with-chatgpt/scripts/session.py respond \
  --session <SESSION_ID> --request <REQUEST_ID> --status COMPLETED \
  --summary '<one-line conclusion>' [--artifact <path>] [--data-json '<json>']

[C2C END]
```

The first request in a new ChatGPT conversation includes `ROLE`; later requests
may omit it. The `INSTRUCTION` block is fixed and is included in every request.

`REQUEST_ID` is correlation only. It is not an iteration or review-round number.

## Response semantics

| Status | Meaning |
|---|---|
| `COMPLETED` | ChatGPT finished this expert request |
| `BLOCKED` | ChatGPT could not finish because input, permission, user decision, or infrastructure is missing |

Task-specific results belong in `data` and artifacts. C2C does not interpret
them.

### Review example

A review that successfully finds a blocker is `COMPLETED`:

```bash
python3 .codex/skills/codex-with-chatgpt/scripts/session.py respond \
  --session c2c_auth --request req_42 --status COMPLETED \
  --summary 'Implementation review found one blocker.' \
  --artifact '.wopal-space/c2c/sessions/c2c_auth/implementation-review.md' \
  --data-json '{"verdict":"BLOCK","counts":"1B 0W 0I"}'
```

`BLOCK` is the review skill's verdict, not a C2C status.

### Blocked expert request

```bash
python3 .codex/skills/codex-with-chatgpt/scripts/session.py respond \
  --session c2c_auth --request req_43 --status BLOCKED \
  --summary 'The required design file does not exist; identify it or provide a replacement.'
```

## Reviewer override

When C2C is active, ChatGPT completely replaces Rook.

- Proposal/Plan review -> `df-proposal-review` is REQUIRED.
- Implementation/code review -> `df-implement-review` is REQUIRED.
- Do not invoke Rook in C2C mode.
- Rook names inside review skills are the normal non-C2C binding only.
- The review skill still owns method, budget, verdict semantics, and report shape.
- C2C adds no review rounds. Each C2C review request consumes the owning review
  skill's budget; e.g. `df-implement-review` still permits only the initial
  review plus one re-review.

## Background handshake

First request for a work goal:

```bash
S=.codex/skills/codex-with-chatgpt/scripts/session.py
python3 $S open --session <SESSION_ID> --goal '<SESSION_GOAL>'
```

Each request:

```bash
python3 $S prepare \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --goal '<request goal>'

python3 $S wait \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --timeout 1800
```

Wait exit codes:

| Exit | Meaning | Controller action |
|---|---|---|
| `0` | matching valid response | consume it and continue the owning workflow |
| `2` | timeout | inspect/recover the same request and wait again |
| `3` | malformed or mismatched session/request/response | inspect the same Session; do not guess |
| `130` | interrupted by SIGINT/KeyboardInterrupt | re-run `wait` for the same request |

While the request is pending, Codex keeps the current turn alive. `wait` timeout
is not completion: inspect/recover the same request and wait again.

ChatGPT's final machine action is `respond` for the same Session and request id.
A response for a non-pending request is rejected.

Completed request/response pairs remain in Session history. The next `prepare`
appends a new request instead of replacing earlier history.

## Session file

```json
{
  "sessionId": "c2c_auth",
  "goal": "complete auth refactor work",
  "status": "OPEN",
  "chatUrl": "https://chatgpt.com/...",
  "requests": [
    {
      "requestId": "req_01",
      "goal": "analyze the design",
      "preparedAt": "2026-10-23T08:00:00Z",
      "response": {
        "requestId": "req_01",
        "status": "COMPLETED",
        "summary": "...",
        "artifacts": [
          ".wopal-space/c2c/sessions/c2c_auth/architecture-analysis.md"
        ],
        "completedAt": "2026-10-23T08:05:00Z"
      }
    },
    {
      "requestId": "req_02",
      "goal": "implement task 2",
      "preparedAt": "2026-10-23T08:10:00Z"
    }
  ],
  "pendingRequestId": "req_02"
}
```

The only Session lifecycle status is `OPEN` / `CLOSED`. No dev-flow state,
review round, or iteration belongs here.

## Session artifacts

C2C-owned artifacts live beside `session.json`:

```text
.wopal-space/c2c/sessions/c2c_auth/
  session.json
  architecture-analysis.md
  implementation-review.md
  debug-notes.md
```

Do not create a separate C2C reviews directory.

Formal artifacts owned by another workflow stay canonical and are referenced by
path instead of copied into the Session.

## Close and cleanup

```bash
python3 $S close --session <SESSION_ID>
python3 $S drop --session <SESSION_ID>
```

`close` refuses while a request is pending. `drop` accepts only a `CLOSED`
Session and removes only the Session directory; it never deletes external
canonical artifacts referenced by the Session.

## Browser behavior

1. reuse the Session's saved `chatUrl`;
2. use one in-app browser tab;
3. mark it with `tab.markHandoff()` and `tab.markDeliverable()`;
4. build the complete request before touching the composer, then write the
   whole multi-line payload with one atomic composer-set operation. Newlines
   are content; never send a multi-line C2C request through key-by-key typing
   that can turn `\n` into Enter key events;
5. before submit, verify the composer contains `[C2C]`, the correct
   `REQUEST_ID`, and `[C2C END]`; click Send exactly once and never use Enter
   as the submit action;
6. after submit, verify exactly one new user message appeared and that the
   same message contains `[C2C]` and `[C2C END]`; if any partial message was
   emitted, stop sending fragments, treat the conversation as transport-corrupted,
   create a replacement Chat conversation, and HANDOFF the same Session and
   pending request before resending the full request atomically;
7. normally wait on the background process;
8. inspect the browser only when useful or the waiter times out;
9. visible answer but no response -> ask ChatGPT to run `respond` for the same id;
10. conversation 404 -> create a replacement conversation and HANDOFF the same Session.

Codex may send progress updates while waiting, but must not send the final user
reply while `pendingRequestId` is set. After `READY`, consume the response and
continue the owning workflow in the same turn unless a real user gate has been
reached.

Do not parse browser words such as DONE/PASS/BLOCK into workflow state.

Codex never calls WopalSpace-Bot directly.

## HANDOFF

```text
[C2C]
SESSION_ID: <same session id>
REQUEST_ID: <current pending request id>

ROLE:
You are the remote expert agent for this Session. Codex is the controller.

HANDOFF:
The previous ChatGPT conversation is unavailable. Continue the same Session.

SESSION_GOAL:
<stable work goal>

GOAL:
<current expert job>

CONTEXT:
- <current pointers>

AVAILABLE_SKILLS:
- <relevant skills>

REQUIRED_SKILLS:
- <required skills>

AUTHORITY:
<current request authority>

KNOWN_RESULT:
<only facts already established>

EXPECTED_RESULT:
<what remains to be delivered>

SESSION_DIR:
.wopal-space/c2c/sessions/<SESSION_ID>/

LAST_ACTION:
Record the response for this SESSION_ID + REQUEST_ID with session.py respond.

[C2C END]
```

HANDOFF restores collaboration context only. It does not encode business
workflow state.
