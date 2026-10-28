---
name: codex-with-chatgpt
description: >
  Use when Codex needs sustained collaboration with ChatGPT on a workspace task,
  such as consultation, design, implementation help, debugging, or review across
  one or more exchanges around the same work goal.
---

# Codex with ChatGPT

C2C connects local Codex to a ChatGPT remote expert agent through
WopalSpace-Bot.

The key model is:

```text
SESSION = one work goal / one long-lived collaboration
  REQUEST 1 -> RESPONSE 1
  REQUEST 2 -> RESPONSE 2
  REQUEST 3 -> RESPONSE 3
```

A Session is not a Plan and not a review round. It may contain consultation,
design, implementation, debugging, and review requests for the same work goal.

## Hard rules

1. **C2C owns interaction, not workflow.** `dev-flow`, `ontology-evolution`, and
   other owning skills decide lifecycle, gates, retries, commits, and user
   approvals.
2. **ChatGPT is a remote expert agent, not a fixed planner/reviewer.** It may
   read, analyze, design, write documents, edit code, run commands/tests, debug,
   or review when the request authority and required skills allow it.
3. **Codex is the controller.** It owns the local work goal, decides what to
   delegate, supplies the relevant skills/context/authority, and continues the
   owning workflow after each response.
4. **C2C replaces Rook for all review duties.** In C2C mode, do not invoke Rook.
   ChatGPT loads the same review skill; Rook names inside that skill are only the
   default non-C2C binding.
5. **Review rules stay in review skills.** C2C never redefines review budget,
   PASS/REVISE/BLOCK, report format, or re-review rules.
6. **Session is first-class; request rounds are not workflow rounds.** One
   `SESSION_ID` contains many `REQUEST_ID` -> response exchanges. No C2C
   iteration counter exists.
7. **One Session normally binds one ChatGPT conversation.** A replacement chat
   after recovery keeps the same `SESSION_ID`.
8. **Pointers, not payloads.** Send paths, commits, revisions, skill paths, and
   concise goals. ChatGPT reads the real workspace itself.
9. **The background response is the machine completion signal.** Browser text
   is the human-visible explanation and recovery channel.
10. **C2C-owned artifacts live in the Session directory.** Workflow-owned
    canonical artifacts stay at their canonical paths and are only referenced
    by the Session.
11. **Pending means keep working.** After `prepare`, Codex must not send the
    final user reply until the matching response is received and consumed.
    `wait` timeout is not completion; recover the same request and keep waiting.
12. **WopalSpace-Bot is ChatGPT-only.** Codex never calls it. A failed Codex
    local tool must be fixed locally, or explicitly delegated to ChatGPT as a
    new C2C request.
13. **Codex owns implementation validation by default.** ChatGPT runs in a
    remote Docker environment that may not match the host workspace runtime,
    so Codex should normally implement, test, and verify locally. Delegate code
    implementation to ChatGPT only when it materially helps or Codex is stuck;
    Codex must still run the final tests/verification before accepting the work.
14. **Codex owns browser automation.** `session.py` manages Session/request
    checkpoints only. It never generates the browser payload, types into the
    ChatGPT composer, clicks Send, or decides browser navigation. Keep browser
    interaction in Codex and make the browser instructions precise enough that
    Codex can execute them directly.

## Rule precedence and authority

Each request is governed by three layers:

1. space `AGENTS.md` / startup rules;
2. owning workflow and task skills;
3. C2C transport, Session binding, and ChatGPT role binding.

C2C never weakens layers 1 or 2.

A request also carries `AUTHORITY`, describing what ChatGPT may do for that
request. Examples:

- `Analyze only; do not edit files.`
- `May revise the design document at <path>; do not change code.`
- `May implement the named task, edit code/tests, and run verification; do not commit.`
- `Review only; do not edit the reviewed change.`

Do not invent extra authority. When the owning skill restricts delegated work,
those restrictions still apply to ChatGPT.

## Review override

When C2C is active, ChatGPT completely replaces Rook:

- proposal/Plan review -> ChatGPT + `df-proposal-review`;
- implementation/code review -> ChatGPT + `df-implement-review`;
- no parallel Rook review for the same or any other C2C review duty;
- C2C adds no review rounds; every C2C review request consumes the owning
  review skill's budget. For example, `df-implement-review` still allows only
  the initial review plus one re-review.

## Connection

Connector: **WopalSpace-Bot**.

WopalSpace-Bot exists only inside the ChatGPT side of C2C. Codex uses its own
local tools plus the in-app browser and `session.py`; it never directly invokes
WopalSpace-Bot.

For each C2C request ChatGPT starts with `space_status`, then reads root
`AGENTS.md` and its startup chain. It loads the `REQUIRED_SKILLS` named by Codex
before doing the job and uses `AVAILABLE_SKILLS` when relevant.

If the connector is unavailable, stop and report the connection problem. Do not
fabricate workspace evidence or a response.

## Session model

A Session represents one stable work goal. Use a new Session when the work goal
changes materially.

```text
SESSION_ID: c2c_dsh_upgrade
GOAL: complete DSH upgrade guardrails work
CHAT: one ChatGPT conversation

requests:
  req_01 -> architecture consultation
  req_02 -> revise DESIGN
  req_03 -> implement one task
  req_04 -> implementation review
```

The Session lifecycle is deliberately tiny:

```text
OPEN -> CLOSED
```

`OPEN/CLOSED` only means whether the collaboration may receive another request.
It is not dev-flow or product workflow state.

## Session storage

```text
.wopal-space/c2c/
  space.json
  sessions/
    <SESSION_ID>/
      session.json
      <C2C-owned artifacts...>
```

Examples of C2C-owned artifacts:

```text
architecture-analysis.md
plan-review.md
implementation-review.md
debug-notes.md
evidence.patch
```

Do not create a separate C2C `reviews/` directory. Reviews belong to the Session
that produced them.

Formal workflow artifacts stay where their owning skill requires them:

- dev-flow Plan -> canonical Plan path;
- product/project DESIGN -> canonical design path;
- ontology proposal -> canonical proposal path;
- project source/tests -> project checkout.

The Session only records pointers to those external artifacts. Dropping a
Session deletes only its own directory, never external canonical artifacts.

## Before opening or using a Session

Codex already sees the local workspace. Before delegating:

1. Load the owning workflow skill.
2. Identify skills relevant to the current work goal and current request.
3. Open one Session for that stable goal.
4. Reuse that Session for subsequent requests about the same goal.
5. Put relevant skill paths in each request:
   - `AVAILABLE_SKILLS`: useful skills ChatGPT may need;
   - `REQUIRED_SKILLS`: skills whose method must govern this request.
6. State `AUTHORITY` explicitly.
7. Point to the real Plan/DESIGN/checkout/commit/evidence instead of pasting it.

Do not dump the full skill directory.

## Request protocol

Use the exact request template in `references/protocol.md`; it is the canonical
C2C envelope. The first request in a new ChatGPT conversation includes `ROLE`;
every request includes the fixed `INSTRUCTION` block. Dynamic fields such as
goal, context, skills, authority, and expected result are filled per request.

## Browser channel

The browser is the visible interaction channel.

### Conversation binding

- One `SESSION_ID` normally reuses one ChatGPT conversation.
- Prefer the Session's saved `chatUrl`; do not open a second conversation just
  because a response is slow.
- Use Codex's in-app browser (`iab`), not the user's desktop browser unless the
  user explicitly asks.
- New C2C conversations use Chat mode, not Work mode.
- Claim the tab with `tab.markHandoff()` + `tab.markDeliverable()` and mark it
  again before handing the turn back to the user.

### Sending and monitoring

1. Open/recover the Session conversation.
2. Build the complete request first, then write it to the composer in one
   atomic content-setting operation. Embedded newlines are message data; do
   not use a key-by-key typing primitive that can translate `\n` into Enter
   key events. Prefer one fill/paste-style DOM write or an equivalent atomic
   composer-set operation.
3. Before submitting, verify the composer contains `[C2C]`, the correct
   `REQUEST_ID`, and the terminal `[C2C END]` marker. Submit by clicking Send
   exactly once; do not use Enter as the submit action.
4. After submitting, verify exactly one new user message appeared and that it
   contains both `[C2C]` and `[C2C END]`. If any fragment was emitted, do not
   send the remaining fragments. Treat that conversation as transport-corrupted,
   create a replacement Chat conversation, HANDOFF the same Session/pending
   request, and resend the complete request atomically.
5. Start/continue the background waiter.
6. Inspect the browser only when useful:
   - still generating -> keep waiting;
   - visible answer but no background response -> ask ChatGPT to run `respond`;
   - tool/error UI -> retry the failed step, not the whole request;
   - Retry-only page -> Retry once;
   - conversation 404 -> create a replacement chat and HANDOFF the same Session.

After a Codex restart with a pending request, do not blindly resend. Reopen the
saved conversation first and inspect the visible user messages. If one message
already contains the same `REQUEST_ID` plus both `[C2C]` and `[C2C END]`, the
request was already sent: resume `wait` only. Resend only when that complete
message is absent; if only a fragment exists, use the transport-corrupted
recovery above.

Never infer workflow state from browser words such as DONE/PASS/BLOCK.

While a request is pending, user-facing messages are progress updates only.
After `READY`, consume the response and continue the owning workflow in the
same turn unless a real user gate has been reached.

## Background channel

Script:

```bash
S=.codex/skills/codex-with-chatgpt/scripts/session.py
```

### 1. Workspace binding

```bash
python3 $S set --space-id <space-id> \
  --connector-name WopalSpace-Bot --project-url '<project-url>'
```

### 2. Open one Session for the work goal

```bash
python3 $S open \
  --session <SESSION_ID> \
  --goal '<stable work goal>' \
  [--chat-url '<chat-url>']
```

`open` creates:

```text
.wopal-space/c2c/sessions/<SESSION_ID>/session.json
```

Re-running `open` with the same goal is idempotent. Reusing the same Session id
for a different goal is rejected.

Update the bound conversation later with:

```bash
python3 $S set --session <SESSION_ID> --chat-url '<chat-url>'
```

### 3. Prepare one request

```bash
python3 $S prepare \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --goal '<this request goal>'
```

A Session accepts only one pending request at a time, but completed requests stay
in its history and are never overwritten by the next request.

### 4. Wait for the response

```bash
python3 $S wait \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --timeout 1800
```

Keep the waiter owned by the harness. Do not detach with `nohup`, `&`, or
`setsid`.

Timeout only means the response has not arrived yet. Inspect/recover the same
request and continue waiting; do not end the turn.

### 5. ChatGPT records its response

ChatGPT's last machine action is:

```bash
python3 $S respond \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --status COMPLETED \
  --summary '<one-line conclusion>' \
  [--artifact '<path>'] \
  [--data-json '<task-specific JSON object>']
```

For a review, prefer a Session-owned report:

```bash
python3 $S respond \
  --session c2c_auth \
  --request req_04 \
  --status COMPLETED \
  --summary 'Implementation review found one blocker.' \
  --artifact '.wopal-space/c2c/sessions/c2c_auth/implementation-review.md' \
  --data-json '{"verdict":"BLOCK","counts":"1B 0W 0I"}'
```

A successful review that finds a Blocker is still `COMPLETED`. `BLOCK` is the
review skill's verdict.

If the expert job itself cannot be completed:

```bash
python3 $S respond \
  --session <SESSION_ID> --request <REQUEST_ID> \
  --status BLOCKED --summary '<what is missing and what is needed>'
```

### 6. Continue with another request

After a response, Codex may prepare another `REQUEST_ID` in the same Session.
This is the normal multi-turn collaboration model.

### 7. Close and clean up

When the whole Session work goal is finished and no request is pending:

```bash
python3 $S close --session <SESSION_ID>
```

When the owning workflow no longer needs the Session history or its temporary
artifacts:

```bash
python3 $S drop --session <SESSION_ID>
```

`drop` deletes only `.wopal-space/c2c/sessions/<SESSION_ID>/`.
It also refuses an `OPEN` Session; close the Session first.

Exit codes and recovery actions are defined in `references/protocol.md`.

## What ChatGPT may do

C2C does not classify requests into a fixed workflow. The same Session can ask
ChatGPT to:

- analyze a problem or architecture;
- advise Codex during implementation;
- create or revise DESIGN/Plan when the owning skill permits it;
- implement a delegated task when Codex needs help, subject to Codex-side final
  testing and verification;
- diagnose failures or debug code;
- review a Plan/proposal;
- review an implementation, commit, diff, or arbitrary code;
- produce other workspace artifacts allowed by the request.

The request's `REQUIRED_SKILLS`, `AUTHORITY`, space rules, and owning workflow
determine the allowed actions.

## Evidence and diffs

ChatGPT reads evidence through WopalSpace-Bot.

- Workspace-visible repo/worktree -> `exec_command` with `git -C <path>`.
- Git metadata outside the worker boundary -> Codex writes sanitized evidence in
  the Session directory when it is Session-specific, or another owning-skill
  path when appropriate.
- External CI/GitHub evidence -> same pointer-based pattern.
- Never paste large diffs/logs into the C2C control message.

## Recovery

Useful commands:

```bash
python3 $S ls
python3 $S get --session <SESSION_ID>
```

After a Codex restart:

1. recover `session.json` and `chatUrl`;
2. see whether `pendingRequestId` is set;
3. re-run `wait` for that request if needed;
4. let the owning workflow recover its own business state from its own files.

A ChatGPT conversation replacement does not create a new Session. Keep the same
`SESSION_ID`, update `chatUrl`, and HANDOFF the Session goal/current request.

## Media

- OpenAI/user file reference available -> `save_artifact` to a permitted path.
- Browser download without a file reference -> `scripts/media_import.py`.
- Images -> `read_image` for expert inspection.
- Session-owned media/evidence may live in the Session directory.
- Workflow/product-owned media stays at its canonical path.

## References

- `docs/DESIGN.md` — architecture and boundaries
- `references/protocol.md` — Session/request/response and HANDOFF templates
- `references/project-instructions.md` — minimal ChatGPT Project binding text
