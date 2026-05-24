import unittest
from pathlib import Path

from roger.cli import build_parser, run


class RogerCliTests(unittest.TestCase):
    def test_parser_supports_health_and_spike_commands(self):
        parser = build_parser()

        health = parser.parse_args(["health"])
        wake = parser.parse_args(["spike", "wake"])
        vad = parser.parse_args(["spike", "vad"])
        stt = parser.parse_args(["spike", "stt"])
        tts = parser.parse_args(["spike", "tts"])

        self.assertEqual(health.command, "health")
        self.assertEqual(wake.spike, "wake")
        self.assertEqual(vad.spike, "vad")
        self.assertEqual(stt.spike, "stt")
        self.assertEqual(tts.spike, "tts")

    def test_health_command_reports_core_configuration(self):
        exit_code, output = run(["health", "--project-dir", "/tmp/project"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Roger health", output)
        self.assertIn("wake: nanowakeword", output)
        self.assertIn("target: hola roger", output)
        self.assertIn("wake threshold: 0.85", output)
        self.assertIn("stt model: large-v3-turbo", output)
        self.assertIn("stt device: cuda", output)
        self.assertIn("stt compute type: float16", output)
        self.assertIn("tts local files only: True", output)
        self.assertIn("tts device: cuda", output)
        self.assertIn("automatic fallback: True", output)
        self.assertIn("fallback enabled: True", output)
        self.assertIn("online probe URL: (not configured)", output)
        self.assertIn("provider probe timeout seconds: 2.0", output)
        self.assertIn("offline model provider: llama-cpp", output)
        self.assertIn("offline model: gemma4", output)
        self.assertIn("offline model base URL: http://127.0.0.1:11434/v1", output)
        self.assertIn("offline timeout seconds: 45.0", output)
        self.assertIn("sessions: current-project, system", output)
        self.assertIn("routing config: valid", output)

    def test_route_command_dry_runs_without_dispatching(self):
        exit_code, output = run(["route", "corre los tests", "--project-dir", "/tmp/project"])

        self.assertEqual(exit_code, 0)
        self.assertIn("session: current-project", output)
        self.assertIn("matched rule: keyword:tests", output)

    def test_spike_command_can_dry_run_each_spike(self):
        expected_candidates = {
            "wake": ["gru", "lstm", "tcn"],
            "vad": ["silero", "webrtc"],
            "stt": ["faster-whisper", "whisper.cpp"],
            "tts": ["kokoro", "piper"],
        }
        for spike in ["wake", "vad", "stt", "tts"]:
            with self.subTest(spike=spike):
                exit_code, output = run(["spike", spike, "--dry-run", "--project-dir", str(Path.cwd())])

                self.assertEqual(exit_code, 0)
                self.assertIn(f"{spike} spike", output)
                self.assertIn("dry-run", output)
                for candidate in expected_candidates[spike]:
                    self.assertIn(candidate, output)

    def test_wake_spike_can_write_nanowakeword_configs(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "configs"
            exit_code, output = run([
                "spike",
                "wake",
                "--write-configs",
                "--output-dir",
                str(output_dir),
            ])

            self.assertEqual(exit_code, 0)
            self.assertIn("wrote 3 NanoWakeWord configs", output)
            self.assertTrue((output_dir / "hola_roger_gru.json").exists())
            self.assertTrue((output_dir / "hola_roger_lstm.json").exists())
            self.assertTrue((output_dir / "hola_roger_tcn.json").exists())


if __name__ == "__main__":
    unittest.main()
