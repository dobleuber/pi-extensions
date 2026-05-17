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


class CliTaskTests(unittest.TestCase):
    def test_task_command_dispatches_typed_instruction_to_selected_session(self):
        runner = FakeRunner()
        speaker = FakeSpeaker()

        exit_code, output = cli.run(
            ["task", "--session", "current-project", "corre pwd", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_pi_runner=lambda config, registry, offline=False: runner,
                create_tts_speaker=lambda config, no_tts=False: speaker,
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
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(runner.calls, [("current-project", "corre los tests")])


if __name__ == "__main__":
    unittest.main()
