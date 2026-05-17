import unittest

from roger import cli


class FakeRunner:
    def __init__(self):
        self.calls = []

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        return "Respuesta real de pi"


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


if __name__ == "__main__":
    unittest.main()
