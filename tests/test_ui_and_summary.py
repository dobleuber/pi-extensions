import unittest

from roger.summarization import summarize_for_speech
from roger.ui.logs import TaskLog
from roger.ui.preview import PreviewAction, TranscriptionPreview


class UiAndSummaryTests(unittest.TestCase):
    def test_preview_accepts_or_cancels_transcription(self):
        preview = TranscriptionPreview()

        accepted = preview.review("instala steam", action=PreviewAction.ACCEPT)
        cancelled = preview.review("borra todo", action=PreviewAction.CANCEL)

        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.text, "instala steam")
        self.assertFalse(cancelled.accepted)
        self.assertEqual(cancelled.text, "borra todo")

    def test_preview_timeout_accepts_when_configured(self):
        preview = TranscriptionPreview(accept_on_timeout=True)

        decision = preview.review("corre los tests", action=PreviewAction.TIMEOUT)

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "timeout")

    def test_task_log_collects_pi_events_and_status(self):
        log = TaskLog(session_name="current-project")
        log.start("corre los tests")
        log.record_event({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "delta": "Listo"}})
        log.record_event({"type": "tool_execution_end", "toolName": "bash", "isError": False})
        log.complete()

        self.assertEqual(log.status, "complete")
        self.assertEqual(log.text, "Listo")
        self.assertIn("bash", "\n".join(log.entries))

    def test_speech_summary_keeps_long_logs_concise(self):
        long_text = "Resultado detallado. " * 100

        summary = summarize_for_speech(long_text, max_chars=80)

        self.assertLessEqual(len(summary), 81)
        self.assertTrue(summary.endswith("…"))


if __name__ == "__main__":
    unittest.main()
