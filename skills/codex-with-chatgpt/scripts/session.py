#!/usr/bin/env python3
"""C2C session + request/response checkpoint manager.

A C2C session is one long-lived collaboration around one work goal. It binds one
ChatGPT conversation and contains many sequential request/response exchanges.
C2C owns this interaction history only; business workflow state remains in the
owning workspace skills.

Layout:
  .wopal-space/c2c/sessions/<sessionId>/session.json
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

C2C_REL = ".wopal-space/c2c"
SPACE_FILE = "space.json"
SESSIONS_DIR = "sessions"
SESSION_FILE = "session.json"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
RESPONSE_STATUSES = {"COMPLETED", "BLOCKED"}
SESSION_STATUSES = {"OPEN", "CLOSED"}

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def emit(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def find_workspace_root(start=None):
    p = Path(start or Path.cwd()).resolve()
    for d in [p, *p.parents]:
        if (d / ".wopal-space").is_dir():
            return d
    raise SystemExit("Not in a WopalSpace (no .wopal-space/ found)")


def c2c_dir(ws):
    return ws / C2C_REL


def space_path(ws):
    return c2c_dir(ws) / SPACE_FILE


def sessions_dir(ws):
    return c2c_dir(ws) / SESSIONS_DIR


def validate_id(value, regex, label):
    if not value or not regex.fullmatch(value):
        die(f"Invalid {label} {value!r}.")
    return value


def session_dir(ws, session_id):
    validate_id(session_id, ID_RE, "session id")
    return sessions_dir(ws) / session_id


def session_path(ws, session_id):
    return session_dir(ws, session_id) / SESSION_FILE


@contextmanager
def storage_lock(ws):
    d = sessions_dir(ws)
    d.mkdir(parents=True, exist_ok=True)
    if fcntl is None:  # pragma: no cover
        yield
        return
    fd = os.open(str(d), os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updatedAt"] = now()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def workspace_rel(ws, path):
    try:
        return str(path.relative_to(ws))
    except ValueError:  # pragma: no cover
        return str(path)


def parse_data_json(raw):
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"Invalid --data-json: {exc.msg}.")
    if not isinstance(value, dict):
        die("--data-json must decode to a JSON object.")
    return value


def build_response(args):
    if args.status not in RESPONSE_STATUSES:
        die(f"Invalid response status {args.status!r}; use COMPLETED or BLOCKED.")
    if not args.summary or not args.summary.strip():
        die("--summary is required and must not be empty.")
    response = {
        "requestId": args.request,
        "status": args.status,
        "summary": args.summary.strip(),
        "completedAt": now(),
    }
    if args.artifact:
        response["artifacts"] = args.artifact
    payload = parse_data_json(args.data_json)
    if payload is not None:
        response["data"] = payload
    return response


def validate_response(response, request_id):
    if not isinstance(response, dict):
        return False, "response is not an object"
    if response.get("requestId") != request_id:
        return False, f"response is for {response.get('requestId')!r}, waiting for {request_id!r}"
    if response.get("status") not in RESPONSE_STATUSES:
        return False, f"invalid status {response.get('status')!r}"
    summary = response.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return False, "summary missing or empty"
    artifacts = response.get("artifacts")
    if artifacts is not None and (
        not isinstance(artifacts, list)
        or not all(isinstance(x, str) and x for x in artifacts)
    ):
        return False, "artifacts must be a list of non-empty paths"
    payload = response.get("data")
    if payload is not None and not isinstance(payload, dict):
        return False, "data must be an object"
    return True, ""


def find_request(data, request_id):
    for request in data.get("requests", []):
        if request.get("requestId") == request_id:
            return request
    return None


# ---------------------------------------------------------------------------
# New session model


def cmd_open(args):
    ws = find_workspace_root(args.workspace)
    validate_id(args.session, ID_RE, "session id")
    goal = (args.goal or "").strip()
    if not goal:
        die("--goal is required and must not be empty.")
    sp = session_path(ws, args.session)

    with storage_lock(ws):
        data = read_json(sp)
        if data:
            if data.get("goal") != goal:
                die(
                    f"Session {args.session!r} already exists for goal {data.get('goal')!r}; "
                    "use a new SESSION_ID for a different work goal."
                )
            if data.get("status") != "OPEN":
                die(f"Session {args.session!r} is {data.get('status')}; create a new session instead.")
            if args.chat_url is not None:
                data["chatUrl"] = args.chat_url or None
                write_json(sp, data)
        else:
            data = {
                "sessionId": args.session,
                "goal": goal,
                "status": "OPEN",
                "chatUrl": args.chat_url or None,
                "requests": [],
                "pendingRequestId": None,
                "createdAt": now(),
            }
            write_json(sp, data)

    emit({
        "session": data,
        "sessionDir": workspace_rel(ws, session_dir(ws, args.session)),
    })


def load_new_session(ws, session_id):
    sp = session_path(ws, session_id)
    data = read_json(sp)
    if not data:
        die(f"No C2C session {session_id!r}; run open first.")
    if data.get("sessionId") != session_id:
        die(f"Malformed session file {sp}: sessionId mismatch.")
    return sp, data


def cmd_prepare(args):
    ws = find_workspace_root(args.workspace)
    validate_id(args.request, REQUEST_ID_RE, "request id")
    goal = (args.goal or "").strip()
    if not goal:
        die("--goal is required for each request and must not be empty.")

    with storage_lock(ws):
        sp, data = load_new_session(ws, args.session)
        if data.get("status") != "OPEN":
            die(f"Session {args.session!r} is closed; create a new session for more work.")
        pending = data.get("pendingRequestId")
        if pending:
            die(f"Session {args.session!r} already has pending request {pending!r}.")
        if find_request(data, args.request):
            die(f"Request id {args.request!r} already exists in session {args.session!r}.")
        request = {
            "requestId": args.request,
            "goal": goal,
            "preparedAt": now(),
        }
        data.setdefault("requests", []).append(request)
        data["pendingRequestId"] = args.request
        write_json(sp, data)

    emit({
        "sessionId": args.session,
        "request": request,
        "sessionDir": workspace_rel(ws, session_dir(ws, args.session)),
    })


def cmd_respond(args):
    ws = find_workspace_root(args.workspace)
    validate_id(args.request, REQUEST_ID_RE, "request id")
    response = build_response(args)

    with storage_lock(ws):
        sp, data = load_new_session(ws, args.session)
        pending = data.get("pendingRequestId")
        if pending != args.request:
            die(
                f"Refusing response for request {args.request!r}: current pending request is {pending!r}."
            )
        request = find_request(data, args.request)
        if not request:
            die(f"Request {args.request!r} is missing from session history.")
        if "response" in request:
            die(f"Request {args.request!r} already has a response.")
        request["response"] = response
        data["pendingRequestId"] = None
        write_json(sp, data)

    emit({"sessionId": args.session, "response": response})


def cmd_wait(args):
    ws = find_workspace_root(args.workspace)
    validate_id(args.request, REQUEST_ID_RE, "request id")
    sp = session_path(ws, args.session)
    deadline = time.monotonic() + args.timeout
    reason = "no response yet"

    while time.monotonic() < deadline:
        try:
            data = read_json(sp)
        except (OSError, json.JSONDecodeError) as exc:
            reason = f"unreadable ({exc.__class__.__name__})"
        else:
            if not data:
                print(f"BADSESSION {sp}: session does not exist", file=sys.stderr)
                return 3
            request = find_request(data, args.request)
            if not request:
                print(f"BADREQUEST {sp}: request {args.request!r} does not exist", file=sys.stderr)
                return 3
            response = request.get("response")
            if response is not None:
                ok, why = validate_response(response, args.request)
                if not ok:
                    print(f"BADRESPONSE {sp}: {why}", file=sys.stderr)
                    return 3
                if args.json:
                    emit(response)
                else:
                    print(f"READY {sp} request={args.request} status={response['status']}")
                    print(json.dumps(response, indent=2, ensure_ascii=False))
                return 0
            pending = data.get("pendingRequestId")
            if pending != args.request:
                print(
                    f"BADREQUEST {sp}: request {args.request!r} has no response and is not pending",
                    file=sys.stderr,
                )
                return 3
            reason = "no response yet"
        time.sleep(args.interval)

    print(f"TIMEOUT {sp} after {args.timeout}s: {reason}")
    return 2


def cmd_close(args):
    ws = find_workspace_root(args.workspace)
    with storage_lock(ws):
        sp, data = load_new_session(ws, args.session)
        pending = data.get("pendingRequestId")
        if pending:
            die(f"Cannot close session {args.session!r}: request {pending!r} is still pending.")
        if data.get("status") == "CLOSED":
            emit({"session": data, "sessionDir": workspace_rel(ws, session_dir(ws, args.session))})
            return
        data["status"] = "CLOSED"
        data["closedAt"] = now()
        write_json(sp, data)
    emit({"session": data, "sessionDir": workspace_rel(ws, session_dir(ws, args.session))})


def cmd_drop(args):
    ws = find_workspace_root(args.workspace)
    sd = session_dir(ws, args.session)
    sp = sd / SESSION_FILE
    with storage_lock(ws):
        data = read_json(sp)
        if not data:
            die(f"No C2C session {args.session!r}.")
        pending = data.get("pendingRequestId")
        if pending:
            die(f"Cannot drop session {args.session!r}: request {pending!r} is still pending.")
        if data.get("status") != "CLOSED":
            die(f"Cannot drop session {args.session!r}: close it first.")
        shutil.rmtree(sd)
    emit({"dropped": args.session, "path": workspace_rel(ws, sd)})


# ---------------------------------------------------------------------------
# Workspace binding + inspection


def cmd_ls(args):
    ws = find_workspace_root(args.workspace)
    rows = []
    d = sessions_dir(ws)
    if d.is_dir():
        for p in sorted(d.iterdir(), key=lambda x: x.name):
            if p.is_dir():
                data = read_json(p / SESSION_FILE)
                if not data:
                    continue
                rows.append({
                    "sessionId": data.get("sessionId", p.name),
                    "goal": data.get("goal"),
                    "status": data.get("status"),
                    "pendingRequestId": data.get("pendingRequestId"),
                    "requestCount": len(data.get("requests", [])),
                    "chatUrl": data.get("chatUrl"),
                    "updatedAt": data.get("updatedAt"),
                })
    emit({"space": read_json(space_path(ws)), "sessions": rows})


def cmd_get(args):
    ws = find_workspace_root(args.workspace)
    if args.session:
        sp, data = load_new_session(ws, args.session)
        emit({
            "session": data,
            "sessionDir": workspace_rel(ws, sp.parent),
            "space": read_json(space_path(ws)),
        })
        return
    cmd_ls(args)


def cmd_set(args):
    ws = find_workspace_root(args.workspace)
    space_updates = {}
    if args.space_id:
        space_updates["spaceId"] = args.space_id
    if args.connector_name:
        space_updates["connectorName"] = args.connector_name
    if args.project_url is not None:
        space_updates["projectUrl"] = args.project_url or None

    with storage_lock(ws):
        space = read_json(space_path(ws))
        if space_updates:
            space.update(space_updates)
            write_json(space_path(ws), space)

        session_data = None
        if args.session is not None:
            if args.chat_url is None:
                die("--session with set requires --chat-url.")
            sp, session_data = load_new_session(ws, args.session)
            session_data["chatUrl"] = args.chat_url or None
            write_json(sp, session_data)

    if not space_updates and args.session is None:
        raise SystemExit("Nothing to set.")
    emit({"space": space, "session": session_data})


# ---------------------------------------------------------------------------
# CLI


def add_workspace_arg(parser):
    parser.add_argument(
        "-w", "--workspace", help="workspace root (default: auto-detect)",
    )


def build_parser():
    p = argparse.ArgumentParser(description="C2C session request/response manager")
    add_workspace_arg(p)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("open", help="open one long-lived expert collaboration session")
    sp.add_argument("--session", required=True)
    sp.add_argument("--goal", required=True)
    sp.add_argument("--chat-url")
    sp.set_defaults(func=cmd_open)

    sp = sub.add_parser("get", help="show one session, or list all sessions")
    sp.add_argument("--session")
    sp.set_defaults(func=cmd_get)

    sp = sub.add_parser("ls", help="list C2C sessions")
    sp.set_defaults(func=cmd_ls)

    sp = sub.add_parser("set", help="set workspace binding or session chat URL")
    sp.add_argument("--space-id")
    sp.add_argument("--connector-name")
    sp.add_argument("--project-url")
    sp.add_argument("--session")
    sp.add_argument("--chat-url")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("prepare", help="append one pending request to an open session")
    sp.add_argument("--session", required=True)
    sp.add_argument("--request", required=True)
    sp.add_argument("--goal", required=True)
    sp.set_defaults(func=cmd_prepare)

    sp = sub.add_parser("respond", help="record ChatGPT's response to one request")
    sp.add_argument("--session", required=True)
    sp.add_argument("--request", required=True)
    sp.add_argument("--status", required=True, choices=sorted(RESPONSE_STATUSES))
    sp.add_argument("--summary", required=True)
    sp.add_argument("--artifact", action="append", default=[])
    sp.add_argument("--data-json")
    sp.set_defaults(func=cmd_respond)

    sp = sub.add_parser("wait", help="wait for one request response")
    sp.add_argument("--session", required=True)
    sp.add_argument("--request", required=True)
    sp.add_argument("--timeout", type=float, default=1800)
    sp.add_argument("--interval", type=float, default=1)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_wait)

    sp = sub.add_parser("close", help="close a session after all requests are complete")
    sp.add_argument("--session", required=True)
    sp.set_defaults(func=cmd_close)

    sp = sub.add_parser("drop", help="delete a closed session directory")
    sp.add_argument("--session", required=True)
    sp.set_defaults(func=cmd_drop)

    return p


def main():
    args = build_parser().parse_args()
    result = args.func(args)
    if isinstance(result, int):
        raise SystemExit(result)


if __name__ == "__main__":
    main()
