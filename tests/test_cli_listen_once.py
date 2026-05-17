import io
import tempfile
import wave
import unittest
from contextlib import redirect_stdout
from pathlib import Path

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
    def test_wake_score_callback_respects_minimum_score(self):
        callback = cli._build_wake_score_callback(quiet=False, min_score=0.0)
        output = io.StringIO()

        with redirect_stdout(output):
            callback(0.01)

        self.assertIn("wake score=0.010", output.getvalue())

    def test_wake_score_callback_ignores_scores_below_minimum(self):
        callback = cli._build_wake_score_callback(quiet=False, min_score=0.2)
        output = io.StringIO()

        with redirect_stdout(output):
            callback(0.01)

        self.assertEqual(output.getvalue(), "")

    def test_listen_once_handles_keyboard_interrupt_without_traceback(self):
        class InterruptingVoiceLoop:
            def __init__(self, *args, **kwargs):
                pass

            def run_once(self):
                raise KeyboardInterrupt

        exit_code, output = cli.run(
            ["listen-once", "--no-tts", "--quiet"],
            dependencies=cli.RuntimeDependencies(
                create_wake_backend=lambda config, force_manual=False: FakeWake(),
                create_vad_backend=lambda config: FakeVad(),
                create_stt_backend=lambda config: FakeStt(),
                create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                voice_loop_class=InterruptingVoiceLoop,
            ),
        )

        self.assertEqual(exit_code, 130)
        self.assertIn("interrumpido", output.lower())

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

    def test_listen_once_does_not_print_unsolicited_waiting_feedback(self):
        class FakeVoiceLoop:
            def __init__(self, *args, **kwargs):
                pass

            def run_once(self):
                return type("Result", (), {
                    "status": "listening",
                    "dispatched": False,
                    "message": "",
                })()

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            cli.run(
                ["listen-once", "--no-tts"],
                dependencies=cli.RuntimeDependencies(
                    create_wake_backend=lambda config, force_manual=False: FakeWake(),
                    create_vad_backend=lambda config: FakeVad(),
                    create_stt_backend=lambda config: FakeStt(),
                    create_pi_runner=lambda config, registry, offline=False: FakeRunner(),
                    create_tts_speaker=lambda config, no_tts=False: FakeSpeaker(),
                    voice_loop_class=FakeVoiceLoop,
                ),
            )

        self.assertEqual(stdout.getvalue(), "")

    def test_wake_file_scores_recorded_audio_with_same_adapter(self):
        class FileWake:
            def __init__(self):
                self.threshold = 0.85
                self.calls = 0
                self.score_callback = None

            def predict_samples(self, samples):
                self.calls += 1
                score = 0.91 if self.calls == 2 else 0.1
                if self.score_callback is not None:
                    self.score_callback(score)
                if score >= self.threshold:
                    from roger.backends.interfaces import WakeDetection

                    return WakeDetection("hola roger", score)
                return None

        with tempfile.TemporaryDirectory() as tmp:
            wav_path = Path(tmp) / "hola.wav"
            with wave.open(str(wav_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16_000)
                wav.writeframes(b"\x00\x00" * 2560)

            exit_code, output = cli.run(
                ["wake-file", str(wav_path)],
                dependencies=cli.RuntimeDependencies(
                    create_wake_backend=lambda config, force_manual=False: FileWake(),
                ),
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("detected: yes", output)
        self.assertIn("max score: 0.910", output)

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

    def test_listen_once_can_override_wake_threshold_and_enable_debug_scores(self):
        captured = {}

        class DebuggableWake:
            def __init__(self):
                self.threshold = 0.95
                self.score_callback = None

        wake = DebuggableWake()

        class FakeVoiceLoop:
            def __init__(self, registry, wake, vad, stt, pi_runner, tts, preview_action="accept", feedback=None):
                captured["wake"] = wake

            def run_once(self):
                return type("Result", (), {
                    "status": "listening",
                    "dispatched": False,
                    "message": "",
                })()

        exit_code, output = cli.run(
            ["listen-once", "--wake-threshold", "0.75", "--wake-debug", "--no-tts", "--quiet"],
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
        self.assertEqual(captured["wake"].threshold, 0.75)
        self.assertIsNotNone(captured["wake"].score_callback)


if __name__ == "__main__":
    unittest.main()
