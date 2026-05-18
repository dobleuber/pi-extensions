import unittest

from roger.backends.factory import create_stt_backend, create_tts_backend, create_vad_backend, create_wake_backend
from roger.backends.stt_faster_whisper import FasterWhisperSttAdapter
from roger.backends.tts_kokoro import KokoroTtsAdapter
from roger.backends.vad_silero import SileroVadAdapter
from roger.backends.wake_manual import ManualWakeWordAdapter
from roger.backends.wake_nanowakeword import NanoWakeWordAdapter
from roger.config import RogerConfig


class BackendFactoryTests(unittest.TestCase):
    def test_creates_selected_backends_from_default_config(self):
        config = RogerConfig.default()

        wake = create_wake_backend(config)
        self.assertIsInstance(wake, NanoWakeWordAdapter)
        self.assertEqual(wake.model_path, config.speech.wake.model_path)
        self.assertEqual(wake.target_phrase, "hola roger")
        self.assertEqual(wake.threshold, config.speech.wake.threshold)
        vad = create_vad_backend(config)
        self.assertIsInstance(vad, SileroVadAdapter)
        self.assertEqual(vad.max_capture_seconds, config.speech.vad.max_capture_seconds)
        self.assertEqual(vad.min_silence_duration_ms, config.speech.vad.silence_timeout_ms)
        stt = create_stt_backend(config)
        self.assertIsInstance(stt, FasterWhisperSttAdapter)
        self.assertEqual(stt.model_name, "large-v3-turbo")
        self.assertEqual(stt.language, "es")
        self.assertEqual(stt.device, "cuda")
        self.assertEqual(stt.compute_type, "float16")
        self.assertIsInstance(create_tts_backend(config), KokoroTtsAdapter)

    def test_manual_wake_backend_is_available_for_development(self):
        config = RogerConfig.default()
        wake = create_wake_backend(config, force_manual=True)

        self.assertIsInstance(wake, ManualWakeWordAdapter)


if __name__ == "__main__":
    unittest.main()
