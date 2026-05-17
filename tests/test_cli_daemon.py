import unittest

from roger import cli


class FakeWake:
    def __init__(self):
        self.triggered = 0

    def trigger(self):
        self.triggered += 1


class FakeVad:
    pass


class FakeStt:
    pass


class FakeRunner:
    pass


class FakeSpeaker:
    pass


class CliDaemonTests(unittest.TestCase):
    def test_daemon_command_wires_voice_loop_and_reports_cycles(self):
        created = {}

        class FakeVoiceLoop:
            def __init__(self, *args, **kwargs):
                created["loop"] = self

            def run_once(self):
                return type("Result", (), {"dispatched": True})()

        exit_code, output = cli.run(
            ["daemon", "--max-cycles", "2", "--no-tts", "--quiet"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=lambda config, force_manual=False: FakeWake(),
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("status: complete", output)
        self.assertIn("cycles: 2", output)
        self.assertIn("dispatched: 2", output)

    def test_daemon_manual_wake_triggers_each_cycle(self):
        wake = FakeWake()

        class FakeVoiceLoop:
            def __init__(self, *args, **kwargs):
                pass

            def run_once(self):
                return type("Result", (), {"dispatched": False})()

        exit_code, output = cli.run(
            ["daemon", "--manual-wake", "--max-cycles", "3", "--no-tts", "--quiet"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=lambda config, force_manual=False: wake,
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(wake.triggered, 3)


if __name__ == "__main__":
    unittest.main()
