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
        self.assertEqual(config.speech.wake.threshold, 0.85)
        self.assertEqual(config.speech.wake.architectures, ["gru", "lstm", "tcn"])
        self.assertEqual(
            config.speech.wake.model_path,
            Path("models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx"),
        )
        self.assertEqual(config.speech.vad.backend, "silero")
        self.assertEqual(config.speech.vad.no_speech_timeout_seconds, 4.0)
        self.assertEqual(config.speech.stt.backend, "faster-whisper")
        self.assertEqual(config.speech.stt.model, "large-v3-turbo")
        self.assertEqual(config.speech.stt.device, "cuda")
        self.assertEqual(config.speech.stt.compute_type, "float16")
        self.assertEqual(config.speech.tts.backend, "kokoro")
        self.assertEqual(config.speech.tts.repo_id, "hexgrad/Kokoro-82M")
        self.assertEqual(config.speech.tts.device, "cuda")
        self.assertTrue(config.speech.tts.local_files_only)
        self.assertEqual(config.models.online.provider, "pi-default")
        self.assertEqual(config.models.offline.provider, "llama-cpp")
        self.assertEqual(config.models.offline.model, "gemma4")
        self.assertEqual(config.models.offline.base_url, "http://127.0.0.1:11434/v1")
        self.assertEqual(config.models.offline.timeout_seconds, 45.0)
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
                    local_files_only = false

                    [speech.stt]
                    model = "medium"
                    device = "cpu"
                    compute_type = "int8"

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
        self.assertFalse(config.speech.tts.local_files_only)
        self.assertEqual(config.speech.stt.model, "medium")
        self.assertEqual(config.speech.stt.device, "cpu")
        self.assertEqual(config.speech.stt.compute_type, "int8")
        self.assertEqual(config.speech.wake.threshold, 0.82)
        self.assertEqual(config.speech.wake.target_phrase, "hola roger")
        self.assertEqual(config.sessions["system"].cwd, Path("/tmp"))
        self.assertEqual(config.sessions["current-project"].cwd, Path("/workspace/app"))


if __name__ == "__main__":
    unittest.main()
