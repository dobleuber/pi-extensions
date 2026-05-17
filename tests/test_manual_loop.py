import unittest
from pathlib import Path

from roger.manual_loop import ManualLoop, ManualLoopResult
from roger.routing.registry import SessionRegistry


class FakePiRunner:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        if self.fail:
            raise RuntimeError("pi unavailable")
        return "Tarea completada con muchos detalles"


class FakeTts:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


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


if __name__ == "__main__":
    unittest.main()
