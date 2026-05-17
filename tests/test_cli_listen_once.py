import unittest

from roger import cli


class FakeWake:
    def __init__(self, *args, **kwargs):
        pass


class FakeVad:
    def __init__(self, *args, **kwargs):
        pass


class FakeStt:
    def __init__(self, *args, **kwargs):
        pass


class FakeRunner:
    def __init__(self, *args, **kwargs):
        pass


class FakeSpeaker:
    def __init__(self, *args, **kwargs):
        self.spoken = []


class CliListenOnceTests(unittest.TestCase):
    def test_listen_once_command_wires_voice_loop_and_reports_result(self):
        class FakeVoiceLoop:
            def __init__(self, registry, wake, vad, stt, pi_runner, tts, preview_action="accept", feedback=None):
                self.preview_action = preview_action

            def run_once(self):
                return type("Result", (), {
                    "status": "complete",
                    "dispatched": True,
                    "message": "Hecho",
                })()

        exit_code, output = cli.run(
            ["listen-once", "--project-dir", "/tmp/project", "--no-tts", "--quiet"],
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
        self.assertIn("dispatched: yes", output)
        self.assertIn("Hecho", output)

    def test_listen_once_supports_manual_wake_and_cancel_preview(self):
        captured = {}

        class FakeVoiceLoop:
            def __init__(self, registry, wake, vad, stt, pi_runner, tts, preview_action="accept", feedback=None):
                captured["preview_action"] = preview_action
                captured["wake"] = wake

            def run_once(self):
                return type("Result", (), {
                    "status": "cancelled",
                    "dispatched": False,
                    "message": "Preview cancelled",
                })()

        def fake_wake(config, force_manual=False):
            captured["force_manual"] = force_manual
            return FakeWake()

        exit_code, output = cli.run(
            ["listen-once", "--manual-wake", "--preview-action", "cancel", "--no-tts", "--quiet"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=fake_wake,
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(captured["force_manual"])
        self.assertEqual(captured["preview_action"], "cancel")
        self.assertIn("dispatched: no", output)


if __name__ == "__main__":
    unittest.main()
