import unittest

from roger import cli
from roger.summarization import SpeechScript


class FakeRunner:
    def __init__(self, response="Respuesta real de pi"):
        self.calls = []
        self.last_task_log = None
        self.response = response
        self.request_speech_metadata = None

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        return self.response


class FakeSpeaker:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class FakeOverlayFeedback:
    def __init__(self):
        self.calls = []

    def transcription_ready(self, text):
        self.calls.append(("transcription", text))

    def dispatching(self, session_name):
        self.calls.append(("dispatching", session_name))

    def completed(self, status, message=""):
        self.calls.append(("completed", status, message))


class CliTaskTests(unittest.TestCase):
    def test_task_command_dispatches_typed_instruction_to_selected_session(self):
        runner = FakeRunner()
        speaker = FakeSpeaker()

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: speaker,
                create_overlay_feedback=lambda config: FakeOverlayFeedback(),
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(runner.calls, [("current-project", "corre pwd")])
        self.assertIn("session: current-project", output)
        self.assertIn("Respuesta real de pi", output)

    def test_task_command_uses_router_when_session_is_not_forced(self):
        runner = FakeRunner()

        exit_code, output = cli.run(
            ["task", "corre los tests", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                create_overlay_feedback=lambda config: FakeOverlayFeedback(),
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(runner.calls, [("current-project", "corre los tests")])

    def test_task_command_shows_transcript_and_result_in_overlay_by_default(self):
        runner = FakeRunner()
        overlay = FakeOverlayFeedback()

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                create_overlay_feedback=lambda config: overlay,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(overlay.calls[0], ("transcription", "corre pwd"))
        self.assertEqual(overlay.calls[1], ("dispatching", "current-project"))
        self.assertEqual(overlay.calls[2], ("completed", "complete", "Respuesta real de pi"))

    def test_task_command_includes_task_log_reference_when_available(self):
        from roger.ui.logs import TaskLog

        runner = FakeRunner()
        log = TaskLog(session_name="current-project")
        log.start("corre pwd")
        log.complete()
        log.path = ".roger/logs/task.jsonl"
        runner.last_task_log = log

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-tts", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("log: .roger/logs/task.jsonl", output)

    def test_task_command_speaks_response_when_tts_is_enabled(self):
        runner = FakeRunner()
        speaker = FakeSpeaker()

        cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: speaker,
            ),
        )

        self.assertEqual(speaker.spoken, ["Respuesta real de pi"])

    def test_task_command_speaks_naturalized_response_but_prints_canonical_output(self):
        runner = FakeRunner(response="Son las **10:30 am**. Revisa el README en GitHub.")
        speaker = FakeSpeaker()

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: speaker,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Son las **10:30 am**. Revisa el README en GitHub.", output)
        self.assertEqual(speaker.spoken, ["Son las diez y treinta de la mañana Revisa el ridmi en guit jab."])

    def test_task_command_sets_speech_metadata_flag_only_when_tts_enabled(self):
        runner = FakeRunner()

        cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
            ),
        )

        self.assertTrue(runner.request_speech_metadata)

        no_tts_runner = FakeRunner()
        cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-tts", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: no_tts_runner,
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
            ),
        )

        self.assertFalse(no_tts_runner.request_speech_metadata)

    def test_task_command_speaks_structured_pi_router_speech_text(self):
        runner = FakeRunner(response='{"display_text":"The task is complete.","speech_text":"La tarea está completa.","speech_language":"es","speech_source":"pi-router"}')
        speaker = FakeSpeaker()

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: speaker,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("The task is complete.", output)
        self.assertNotIn("La tarea está completa.", output)
        self.assertEqual(speaker.spoken, ["La tarea está completa."])

    def test_task_command_no_tts_mode_skips_synthesis_but_keeps_text_result(self):
        class UnexpectedSpeaker(FakeSpeaker):
            def speak(self, text):
                raise AssertionError("TTS should be skipped")

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-overlay", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: UnexpectedSpeaker(),
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Respuesta real de pi", output)

    def test_task_command_reports_runner_failure_without_crashing(self):
        class FailingRunner:
            def run_task(self, session_name, instruction):
                raise RuntimeError("llama.cpp server unavailable")

        speaker = FakeSpeaker()
        overlay = FakeOverlayFeedback()

        exit_code, output = cli.run(
            ["task", "--session", "system", "responde exactamente: ok", "--offline"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: FailingRunner(),
                create_tts_speaker=lambda config, no_tts=False: speaker,
                create_overlay_feedback=lambda config: overlay,
            ),
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("status: failed", output)
        self.assertIn("llama.cpp server unavailable", output)
        self.assertEqual(overlay.calls[-1], ("completed", "failed", "llama.cpp server unavailable"))
        self.assertEqual(speaker.spoken, ["llama.cpp server unavailable"])

    def test_say_command_uses_naturalized_speech_text(self):
        speaker = FakeSpeaker()

        exit_code, output = cli.run(
            ["say", "Abrí el README en GitHub"],
            dependencies=cli.RuntimeDependencies(
                create_tts_speaker=lambda config, no_tts=False: speaker,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("spoken: yes", output)
        self.assertEqual(speaker.spoken, ["Abrí el ridmi en guit jab"])

    def test_task_command_keeps_complete_status_when_tts_fails(self):
        class FailingSpeaker:
            def speak(self, text):
                raise RuntimeError("audio device unavailable")

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-overlay"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FailingSpeaker(),
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("status: complete", output)
        self.assertIn("Respuesta real de pi", output)


if __name__ == "__main__":
    unittest.main()
