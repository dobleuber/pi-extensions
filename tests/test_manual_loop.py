import unittest
from pathlib import Path

from roger.manual_loop import ManualLoop, ManualLoopResult
from roger.routing.registry import SessionRegistry


class FakePiRunner:
    def __init__(self, fail=False, response="Tarea completada con muchos detalles"):
        self.calls = []
        self.fail = fail
        self.response = response

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        if self.fail:
            raise RuntimeError("pi unavailable")
        return self.response


class FakeTts:
    def __init__(self, fail=False):
        self.spoken = []
        self.fail = fail

    def speak(self, text):
        self.spoken.append(text)
        if self.fail:
            raise RuntimeError("tts failed")


class ManualLoopTests(unittest.TestCase):
    def test_manual_loop_routes_preview_dispatches_and_speaks_current_project_task(self):
        pi = FakePiRunner()
        tts = FakeTts()
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=pi, tts=tts)

        result = loop.run_transcription("corre los tests")

        self.assertTrue(result.dispatched)
        self.assertEqual(result.session_name, "current-project")
        self.assertEqual(pi.calls, [("current-project", "corre los tests")])
        self.assertEqual(tts.spoken, ["Tarea completada con muchos detalles"])

    def test_manual_loop_dispatches_system_task(self):
        pi = FakePiRunner()
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=pi, tts=FakeTts())

        result = loop.run_transcription("actualiza el sistema")

        self.assertTrue(result.dispatched)
        self.assertEqual(result.session_name, "system")
        self.assertEqual(pi.calls, [("system", "actualiza el sistema")])

    def test_manual_loop_does_not_dispatch_cancelled_preview(self):
        pi = FakePiRunner()
        tts = FakeTts()
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=pi, tts=tts)

        result = loop.run_transcription("instala steam", preview_action="cancel")

        self.assertFalse(result.dispatched)
        self.assertEqual(pi.calls, [])
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(tts.spoken, ["Preview cancelled"])

    def test_manual_loop_speaks_clarification_questions(self):
        tts = FakeTts()
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=FakePiRunner(), tts=tts)

        result = loop.run_transcription("haz eso")

        self.assertEqual(result.status, "needs_clarification")
        self.assertEqual(tts.spoken, [result.message])

    def test_manual_loop_reports_pi_failure(self):
        tts = FakeTts()
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=FakePiRunner(fail=True), tts=tts)

        result = loop.run_transcription("instala steam")

        self.assertFalse(result.dispatched)
        self.assertEqual(result.session_name, "system")
        self.assertEqual(result.status, "failed")
        self.assertIn("pi unavailable", result.message)
        self.assertEqual(tts.spoken, ["pi unavailable"])

    def test_completed_task_keeps_complete_status_when_tts_fails(self):
        tts = FakeTts(fail=True)
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=FakePiRunner(), tts=tts)

        result = loop.run_transcription("corre los tests")

        self.assertEqual(result.status, "complete")
        self.assertTrue(result.dispatched)
        self.assertEqual(result.message, "Tarea completada con muchos detalles")

    def test_manual_loop_speaks_naturalized_text_but_returns_canonical_message(self):
        tts = FakeTts()
        pi = FakePiRunner(response="Son las **10:30 am**. Revisa el README en GitHub.")
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=pi, tts=tts)

        result = loop.run_transcription("corre los tests")

        self.assertEqual(result.message, "Son las **10:30 am**. Revisa el README en GitHub.")
        self.assertEqual(tts.spoken, ["Son las diez y treinta de la mañana Revisa el [README](/ɹˈiːdmi/) en [GitHub](/ɡˈɪthʌb/)."])

    def test_manual_loop_records_speech_text_for_daemon_debugging(self):
        from roger.ui.logs import TaskLog

        tts = FakeTts()
        pi = FakePiRunner(response="The response is in English")
        pi.last_task_log = TaskLog(session_name="current-project")
        loop = ManualLoop(
            SessionRegistry.default(project_dir=Path("/tmp/project")),
            pi_runner=pi,
            tts=tts,
            speech_preparer=lambda text: __import__("roger.summarization", fromlist=["SpeechScript"]).SpeechScript(
                display_text=text,
                speech_text="La respuesta está en español.",
                source="gemma",
            ),
        )

        loop.run_transcription("corre los tests")

        speech_events = [event for event in pi.last_task_log.events if event.kind == "speech"]
        self.assertEqual(len(speech_events), 1)
        self.assertEqual(speech_events[0].data["display_text"], "The response is in English")
        self.assertEqual(speech_events[0].data["speech_text"], "La respuesta está en español.")

    def test_clarification_keeps_visible_message_when_tts_fails(self):
        tts = FakeTts(fail=True)
        pi = FakePiRunner()
        loop = ManualLoop(SessionRegistry.default(project_dir=Path("/tmp/project")), pi_runner=pi, tts=tts)

        result = loop.run_transcription("haz eso")

        self.assertEqual(result.status, "needs_clarification")
        self.assertFalse(result.dispatched)
        self.assertEqual(pi.calls, [])
        self.assertIn("system o current-project", result.message)


if __name__ == "__main__":
    unittest.main()
