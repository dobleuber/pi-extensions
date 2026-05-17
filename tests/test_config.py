import tempfile
import textwrap
import unittest
from pathlib import Path

from roger.config import RogerConfig, load_config


class RogerConfigTests(unittest.TestCase):
    def test_default_config_has_required_backends_and_sessions(self):
        config = RogerConfig.default(project_dir=Path("/tmp/project"))

        self.assertEqual(config.speech.wake.backend, "nanowakeword")
        self.assertEqual(config.speech.wake.target_phrase, "hola roger")
        self.assertEqual(config.speech.wake.architectures, ["gru", "lstm", "tcn"])
        self.assertEqual(config.speech.vad.backend, "silero")
        self.assertEqual(config.speech.stt.backend, "faster-whisper")
        self.assertEqual(config.speech.tts.backend, "kokoro")
        self.assertEqual(config.models.online.provider, "pi-default")
        self.assertEqual(config.models.offline.provider, "ollama")
        self.assertIn("system", config.sessions)
        self.assertIn("current-project", config.sessions)
        self.assertEqual(config.sessions["current-project"].cwd, Path("/tmp/project"))

    def test_load_config_merges_user_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "roger.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [speech.tts]
                    backend = "piper"

                    [speech.wake]
                    threshold = 0.82

                    [sessions.system]
                    cwd = "/tmp"
                    """
                ),
                encoding="utf-8",
            )

            config = load_config(config_path, project_dir=Path("/workspace/app"))

        self.assertEqual(config.speech.tts.backend, "piper")
        self.assertEqual(config.speech.wake.threshold, 0.82)
        self.assertEqual(config.speech.wake.target_phrase, "hola roger")
        self.assertEqual(config.sessions["system"].cwd, Path("/tmp"))
        self.assertEqual(config.sessions["current-project"].cwd, Path("/workspace/app"))


if __name__ == "__main__":
    unittest.main()
