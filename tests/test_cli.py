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
        self.assertIn("sessions: current-project, system", output)

    def test_spike_command_can_dry_run_each_spike(self):
        for spike in ["wake", "vad", "stt", "tts"]:
            with self.subTest(spike=spike):
                exit_code, output = run(["spike", spike, "--dry-run", "--project-dir", str(Path.cwd())])

                self.assertEqual(exit_code, 0)
                self.assertIn(f"{spike} spike", output)
                self.assertIn("dry-run", output)


if __name__ == "__main__":
    unittest.main()
