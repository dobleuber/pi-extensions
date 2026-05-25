import json
import tempfile
import unittest
from pathlib import Path

from roger.summarization import SpeechScript
from roger.ui.logs import TaskLog, TaskLogStore


class TaskLogTests(unittest.TestCase):
    def test_task_log_records_start_metadata_and_status(self):
        log = TaskLog(
            session_name="system",
            model_mode="offline-fallback",
            clock=lambda: "2026-05-24T12:00:00Z",
        )

        log.start("instala steam")

        self.assertEqual(log.status, "running")
        self.assertEqual(log.instruction, "instala steam")
        self.assertEqual(log.started_at, "2026-05-24T12:00:00Z")
        self.assertEqual(log.events[0].kind, "start")
        self.assertEqual(log.events[0].data["model_mode"], "offline-fallback")

    def test_task_log_records_prompt_rejection_as_failed_event(self):
        log = TaskLog(session_name="system")
        log.start("instala steam")

        log.reject("provider unavailable")

        self.assertEqual(log.status, "failed")
        self.assertEqual(log.events[-1].kind, "error")
        self.assertIn("provider unavailable", log.status_context)

    def test_task_log_records_assistant_delta_and_error_reason(self):
        log = TaskLog(session_name="current-project")

        log.record_event({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "Hola"}})
        log.record_event({"type": "message_update", "assistantMessageEvent": {"type": "message_done", "reason": "abort"}})

        self.assertEqual(log.text, "Hola")
        self.assertIn("abort", log.status_context)
        self.assertEqual([event.kind for event in log.events], ["assistant", "assistant_status"])

    def test_task_log_correlates_tool_start_update_and_end(self):
        log = TaskLog(session_name="current-project")

        log.record_event({
            "type": "tool_execution_start",
            "toolName": "bash",
            "toolCallId": "tool-1",
            "args": {"command": "pytest -q", "secret": "hidden"},
        })
        log.record_event({
            "type": "tool_execution_update",
            "toolName": "bash",
            "toolCallId": "tool-1",
            "partialResult": "running...",
        })
        log.record_event({
            "type": "tool_execution_end",
            "toolName": "bash",
            "toolCallId": "tool-1",
            "result": "1 passed",
            "isError": False,
        })

        tool = log.tools["tool-1"]
        self.assertEqual(tool.name, "bash")
        self.assertIn("pytest -q", tool.args_summary)
        self.assertEqual(tool.partial_output, "running...")
        self.assertEqual(tool.final_output, "1 passed")
        self.assertFalse(tool.is_error)

    def test_visible_rendering_is_truncated_when_log_is_long(self):
        log = TaskLog(session_name="system", visible_limit=80)
        log.start("haz algo")
        log.record_event({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "x" * 200}})

        rendered = log.render_visible()

        self.assertLessEqual(len(rendered), 80)
        self.assertIn("truncated", rendered)

    def test_task_log_records_speech_metadata_without_showing_phonetic_text(self):
        log = TaskLog(session_name="current-project")
        script = SpeechScript(
            display_text="Revisa el README en GitHub",
            speech_text="Revisa el ridmi en guit jab",
            source="fallback",
            style="neutral",
            degradation_reason="naturalizer unavailable",
        )

        log.record_speech(script)
        rendered = log.render_visible()

        self.assertEqual(log.events[-1].kind, "speech")
        self.assertEqual(log.events[-1].data["display_text"], "Revisa el README en GitHub")
        self.assertEqual(log.events[-1].data["speech_text"], "Revisa el ridmi en guit jab")
        self.assertNotIn("ridmi", rendered)
        self.assertNotIn("guit jab", rendered)

    def test_task_log_store_persists_jsonl_and_prunes_old_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "old.jsonl"
            old.write_text("{}\n", encoding="utf-8")
            newer = root / "newer.jsonl"
            newer.write_text("{}\n", encoding="utf-8")
            store = TaskLogStore(root=root, max_logs=2)
            log = TaskLog(session_name="system", clock=lambda: "2026-05-24T12:00:00Z")
            log.start("instala steam")
            log.complete()

            path = store.save(log)

            self.assertTrue(path.exists())
            payloads = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(payloads[0]["kind"], "start")
            self.assertEqual(payloads[-1]["kind"], "complete")
            self.assertEqual(len(list(root.glob("*.jsonl"))), 2)


if __name__ == "__main__":
    unittest.main()
