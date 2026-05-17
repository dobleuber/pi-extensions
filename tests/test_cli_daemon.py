import unittest

from roger import cli
from roger.feedback_system import SystemFeedback


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


class FakeOverlayFeedback:
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
                create_overlay_feedback=lambda config: FakeOverlayFeedback(),
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
                create_overlay_feedback=lambda config: FakeOverlayFeedback(),
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(wake.triggered, 3)

    def test_daemon_includes_overlay_feedback_by_default(self):
        captured = {}
        overlay = FakeOverlayFeedback()

        class FakeVoiceLoop:
            def __init__(self, registry, wake, vad, stt, pi_runner, tts, preview_action="accept", feedback=None):
                captured["feedback"] = feedback

            def run_once(self):
                return type("Result", (), {"dispatched": False})()

        cli.run(
            ["daemon", "--max-cycles", "1", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=lambda config, force_manual=False: FakeWake(),
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                create_overlay_feedback=lambda config: overlay,
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertIn(overlay, captured["feedback"].sinks)

    def test_daemon_does_not_send_desktop_notifications_by_default(self):
        captured = {}

        class FakeVoiceLoop:
            def __init__(self, registry, wake, vad, stt, pi_runner, tts, preview_action="accept", feedback=None):
                captured["feedback"] = feedback

            def run_once(self):
                return type("Result", (), {"dispatched": False})()

        cli.run(
            ["daemon", "--max-cycles", "1", "--no-tts"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=lambda config, force_manual=False: FakeWake(),
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                create_overlay_feedback=lambda config: FakeOverlayFeedback(),
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertFalse(any(isinstance(sink, SystemFeedback) for sink in captured["feedback"].sinks))

    def test_daemon_can_opt_into_desktop_notifications(self):
        captured = {}

        class FakeVoiceLoop:
            def __init__(self, registry, wake, vad, stt, pi_runner, tts, preview_action="accept", feedback=None):
                captured["feedback"] = feedback

            def run_once(self):
                return type("Result", (), {"dispatched": False})()

        cli.run(
            ["daemon", "--max-cycles", "1", "--no-tts", "--desktop-notifications"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=lambda config, force_manual=False: FakeWake(),
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                create_overlay_feedback=lambda config: FakeOverlayFeedback(),
                voice_loop_class=FakeVoiceLoop,
            ),
        )

        self.assertTrue(any(isinstance(sink, SystemFeedback) for sink in captured["feedback"].sinks))


if __name__ == "__main__":
    unittest.main()
