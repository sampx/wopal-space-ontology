import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "session.py"


class SessionProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)
        (self.ws / ".wopal-space").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_session(self, *args, expect=0):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "-w", str(self.ws), *args],
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            proc.returncode,
            expect,
            msg=f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        return proc

    def session_dir(self, session="c2c_demo"):
        return self.ws / ".wopal-space" / "c2c" / "sessions" / session

    def session_json(self, session="c2c_demo"):
        path = self.session_dir(session) / "session.json"
        return json.loads(path.read_text())

    def open_session(self, session="c2c_demo", goal="finish demo task"):
        return self.run_session(
            "open", "--session", session, "--goal", goal,
            "--chat-url", "https://chatgpt.com/c/demo",
        )

    def test_open_creates_one_directory_per_session(self):
        self.open_session()
        data = self.session_json()
        self.assertEqual(data["sessionId"], "c2c_demo")
        self.assertEqual(data["goal"], "finish demo task")
        self.assertEqual(data["status"], "OPEN")
        self.assertEqual(data["chatUrl"], "https://chatgpt.com/c/demo")
        self.assertEqual(data["requests"], [])
        self.assertIsNone(data["pendingRequestId"])
        self.assertTrue(self.session_dir().is_dir())

    def test_open_is_idempotent_for_same_goal_and_rejects_goal_reuse(self):
        self.open_session()
        self.open_session()
        self.assertEqual(self.session_json()["goal"], "finish demo task")
        proc = self.run_session(
            "open", "--session", "c2c_demo", "--goal", "different work goal",
            expect=3,
        )
        self.assertIn("different work goal", proc.stderr)

    def test_prepare_appends_request_without_workflow_state(self):
        self.open_session()
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_a",
            "--goal", "review the implementation",
        )
        data = self.session_json()
        self.assertEqual(data["pendingRequestId"], "req_a")
        self.assertEqual(len(data["requests"]), 1)
        self.assertEqual(data["requests"][0]["requestId"], "req_a")
        self.assertEqual(data["requests"][0]["goal"], "review the implementation")
        for key in ("iteration", "state", "waitingFor", "reply"):
            self.assertNotIn(key, data)

    def test_respond_records_result_in_request_history_and_clears_pending(self):
        self.open_session()
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_a",
            "--goal", "review the implementation",
        )
        artifact = ".wopal-space/c2c/sessions/c2c_demo/implementation-review.md"
        self.run_session(
            "respond", "--session", "c2c_demo", "--request", "req_a",
            "--status", "COMPLETED", "--summary", "review complete",
            "--artifact", artifact,
            "--data-json", '{"verdict":"BLOCK","counts":"1B 0W"}',
        )
        data = self.session_json()
        self.assertIsNone(data["pendingRequestId"])
        response = data["requests"][0]["response"]
        self.assertEqual(response["status"], "COMPLETED")
        self.assertEqual(response["data"]["verdict"], "BLOCK")
        self.assertEqual(response["artifacts"], [artifact])

    def test_multiple_requests_stay_in_one_session_history(self):
        self.open_session()
        for request_id, goal in (("req_1", "design advice"), ("req_2", "implement helper")):
            self.run_session(
                "prepare", "--session", "c2c_demo", "--request", request_id,
                "--goal", goal,
            )
            self.run_session(
                "respond", "--session", "c2c_demo", "--request", request_id,
                "--status", "COMPLETED", "--summary", f"done {request_id}",
            )
        data = self.session_json()
        self.assertEqual([r["requestId"] for r in data["requests"]], ["req_1", "req_2"])
        self.assertEqual([r["goal"] for r in data["requests"]], ["design advice", "implement helper"])
        self.assertTrue(all("response" in r for r in data["requests"]))

    def test_only_one_request_can_be_pending_in_a_session(self):
        self.open_session()
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_a", "--goal", "first",
        )
        proc = self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_b", "--goal", "second",
            expect=3,
        )
        self.assertIn("req_a", proc.stderr)
        self.assertEqual(len(self.session_json()["requests"]), 1)

    def test_stale_response_is_rejected(self):
        self.open_session()
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_new", "--goal", "current",
        )
        proc = self.run_session(
            "respond", "--session", "c2c_demo", "--request", "req_old",
            "--status", "COMPLETED", "--summary", "stale",
            expect=3,
        )
        self.assertIn("req_new", proc.stderr)
        self.assertNotIn("response", self.session_json()["requests"][0])

    def test_blocked_means_this_request_could_not_complete(self):
        self.open_session()
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_a",
            "--goal", "inspect missing design",
        )
        self.run_session(
            "respond", "--session", "c2c_demo", "--request", "req_a",
            "--status", "BLOCKED", "--summary", "required design is missing",
        )
        response = self.session_json()["requests"][0]["response"]
        self.assertEqual(response["status"], "BLOCKED")
        self.assertNotIn("verdict", response)

    def test_wait_can_read_completed_request_after_later_rounds(self):
        self.open_session()
        for request_id in ("req_1", "req_2"):
            self.run_session(
                "prepare", "--session", "c2c_demo", "--request", request_id,
                "--goal", request_id,
            )
            self.run_session(
                "respond", "--session", "c2c_demo", "--request", request_id,
                "--status", "COMPLETED", "--summary", f"done {request_id}",
            )
        proc = self.run_session(
            "wait", "--session", "c2c_demo", "--request", "req_1",
            "--timeout", "1", "--json",
        )
        response = json.loads(proc.stdout)
        self.assertEqual(response["requestId"], "req_1")
        self.assertEqual(response["summary"], "done req_1")

    def test_close_is_session_lifecycle_only_and_refuses_pending_request(self):
        self.open_session()
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_a", "--goal", "work",
        )
        self.run_session("close", "--session", "c2c_demo", expect=3)
        self.run_session(
            "respond", "--session", "c2c_demo", "--request", "req_a",
            "--status", "COMPLETED", "--summary", "done",
        )
        self.run_session("close", "--session", "c2c_demo")
        data = self.session_json()
        self.assertEqual(data["status"], "CLOSED")
        self.assertIn("closedAt", data)
        self.run_session(
            "prepare", "--session", "c2c_demo", "--request", "req_b", "--goal", "more",
            expect=3,
        )

    def test_drop_removes_only_the_session_directory(self):
        self.open_session()
        note = self.session_dir() / "analysis.md"
        note.write_text("temporary expert artifact", encoding="utf-8")
        external = self.ws / ".wopal-space" / "plans" / "keep.md"
        external.parent.mkdir(parents=True)
        external.write_text("canonical", encoding="utf-8")
        self.run_session("drop", "--session", "c2c_demo", expect=3)
        self.run_session("close", "--session", "c2c_demo")
        self.run_session("drop", "--session", "c2c_demo")
        self.assertFalse(self.session_dir().exists())
        self.assertTrue(external.exists())

    def test_set_has_no_mode_switch(self):
        proc = self.run_session(
            "set", "--mode", "project", expect=2,
        )
        self.assertIn("unrecognized arguments", proc.stderr)

    def test_legacy_cli_is_removed(self):
        proc = self.run_session(
            "reply", "--task", "c2c_old", "--iteration", "1",
            "--state", "DONE", "--verdict", "PASS", "--summary", "old",
            expect=2,
        )
        self.assertIn("invalid choice", proc.stderr)

        proc = self.run_session(
            "prepare", "--task", "c2c_old", "--request", "req_old",
            "--goal", "old", expect=2,
        )
        self.assertIn("--session", proc.stderr)



if __name__ == "__main__":
    unittest.main()
