import unittest

from roger.summarization import GemmaSpeechNaturalizer, prepare_speech_script, summarize_for_speech
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

    def test_gemma_naturalizer_uses_local_completion_response(self):
        calls = []

        def complete(payload, timeout):
            calls.append((payload, timeout))
            return {"choices": [{"message": {"content": "Son las diez y treinta de la mañana."}}]}

        naturalizer = GemmaSpeechNaturalizer(
            base_url="http://127.0.0.1:11434/v1",
            model="gemma4",
            timeout_seconds=1.5,
            complete=complete,
        )

        script = naturalizer.naturalize("Son las **10:30 am**")

        self.assertEqual(script.display_text, "Son las **10:30 am**")
        self.assertEqual(script.speech_text, "Son las diez y treinta de la mañana.")
        self.assertEqual(script.source, "gemma")
        self.assertEqual(calls[0][0]["model"], "gemma4")
        system_prompt = calls[0][0]["messages"][0]["content"]
        self.assertIn("solo para TTS", system_prompt)
        self.assertIn("responder en español", system_prompt)
        self.assertIn("excepto anglicismos", system_prompt)
        self.assertIn("Son las **10:30 am**", calls[0][0]["messages"][1]["content"])
        self.assertEqual(calls[0][1], 1.5)

    def test_gemma_naturalizer_falls_back_when_completion_fails(self):
        def complete(payload, timeout):
            raise TimeoutError("too slow")

        naturalizer = GemmaSpeechNaturalizer(complete=complete, timeout_seconds=0.1)

        script = naturalizer.naturalize("Abrí el README en GitHub")

        self.assertEqual(script.source, "fallback")
        self.assertIn("too slow", script.degradation_reason)
        self.assertIn("ridmi", script.speech_text)
        self.assertIn("guit jab", script.speech_text)

    def test_gemma_naturalizer_rejects_invalid_output_and_falls_back(self):
        naturalizer = GemmaSpeechNaturalizer(
            complete=lambda payload, timeout: {"choices": [{"message": {"content": ""}}]},
        )

        script = naturalizer.naturalize("Usa Docker")

        self.assertEqual(script.source, "fallback")
        self.assertIn("invalid", script.degradation_reason)
        self.assertIn("dóker", script.speech_text)

    def test_gemma_naturalizer_rejects_chat_template_echo_and_falls_back(self):
        naturalizer = GemmaSpeechNaturalizer(
            complete=lambda payload, timeout: {
                "choices": [{"message": {"content": "Son las **10:30 am**<|im_end|>\n<|im_start|>assistant"}}]
            },
        )

        script = naturalizer.naturalize("Son las **10:30 am**")

        self.assertEqual(script.source, "fallback")
        self.assertIn("invalid", script.degradation_reason)
        self.assertEqual(script.speech_text, "Son las diez y treinta de la mañana")

    def test_gemma_naturalizer_rejects_unchanged_english_without_sending_it_to_tts(self):
        text = "Respond again: it's eight, thirty-nine and nine zero five."
        naturalizer = GemmaSpeechNaturalizer(
            complete=lambda payload, timeout: {"choices": [{"message": {"content": text}}]},
        )

        script = naturalizer.naturalize(text)

        self.assertEqual(script.source, "fallback")
        self.assertIn("invalid", script.degradation_reason)
        self.assertEqual(script.display_text, text)
        self.assertNotEqual(script.speech_text, text)
        self.assertEqual(script.speech_text, "No pude preparar una respuesta hablada en español.")

    def test_gemma_naturalizer_rejects_partial_english_with_curly_apostrophe(self):
        naturalizer = GemmaSpeechNaturalizer(
            complete=lambda payload, timeout: {"choices": [{"message": {"content": "It’s 2026-05-24."}}]},
        )

        script = naturalizer.naturalize("It’s 2026-05-24 20:55:39 -05.")

        self.assertEqual(script.source, "fallback")
        self.assertIn("invalid", script.degradation_reason)
        self.assertEqual(script.speech_text, "No pude preparar una respuesta hablada en español.")


if __name__ == "__main__":
    unittest.main()
