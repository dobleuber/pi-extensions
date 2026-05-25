import unittest

from roger.summarization import parse_speech_response, prepare_speech_script, summarize_for_speech
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

    def test_prepare_speech_script_preserves_display_text_and_rewrites_tts_text(self):
        display = "Son las **10:30 am**. Abrí el README y crea un pull request en GitHub."

        script = prepare_speech_script(display)

        self.assertEqual(script.display_text, display)
        self.assertNotIn("**", script.speech_text)
        self.assertIn("diez y treinta de la mañana", script.speech_text)
        self.assertIn("ridmi", script.speech_text)
        self.assertIn("pul ricuest", script.speech_text)
        self.assertIn("guit jab", script.speech_text)
        self.assertEqual(script.source, "fallback")

    def test_prepare_speech_script_accepts_configurable_anglicisms(self):
        script = prepare_speech_script("Ejecuta FooBar", anglicisms={"FooBar": "fu bar"})

        self.assertEqual(script.display_text, "Ejecuta FooBar")
        self.assertEqual(script.speech_text, "Ejecuta fu bar")

    def test_parse_structured_speech_response_keeps_display_and_speech_separate(self):
        payload = '{"display_text":"It is 8:39.","speech_text":"Son las ocho treinta y nueve.","speech_language":"es","speech_source":"pi-router"}'

        script = parse_speech_response(payload)

        self.assertEqual(script.display_text, "It is 8:39.")
        self.assertEqual(script.speech_text, "Son las ocho treinta y nueve.")
        self.assertEqual(script.source, "pi-router")
        self.assertEqual(script.metadata["speech_language"], "es")

    def test_parse_plain_text_response_uses_minimal_fallback(self):
        script = parse_speech_response("Son las **10:30 am**")

        self.assertEqual(script.display_text, "Son las **10:30 am**")
        self.assertEqual(script.speech_text, "Son las diez y treinta de la mañana")
        self.assertEqual(script.source, "fallback")


if __name__ == "__main__":
    unittest.main()
