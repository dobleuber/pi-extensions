import unittest

from roger.backends.errors import BackendUnavailable
from roger.backends.wake_manual import ManualWakeWordAdapter
from roger.backends.wake_nanowakeword import NanoWakeWordAdapter
from roger.backends.vad_silero import SileroVadAdapter
from roger.backends.stt_faster_whisper import FasterWhisperSttAdapter
from roger.backends.tts_kokoro import KokoroTtsAdapter


class BackendAdapterTests(unittest.TestCase):
    def test_manual_wake_adapter_only_detects_after_trigger(self):
        adapter = ManualWakeWordAdapter(target_phrase="hola roger")

        self.assertIsNone(adapter.listen_once())

        adapter.trigger()
        detection = adapter.listen_once()

        self.assertIsNotNone(detection)
        self.assertEqual(detection.phrase, "hola roger")
        self.assertEqual(detection.score, 1.0)
        self.assertIsNone(adapter.listen_once())

    def test_nanowakeword_adapter_reports_missing_dependency(self):
        adapter = NanoWakeWordAdapter(model_path="model.onnx", import_module=lambda _: (_ for _ in ()).throw(ImportError("missing")))

        self.assertFalse(adapter.is_available())
        with self.assertRaises(BackendUnavailable):
            adapter.listen_once()

    def test_selected_backend_placeholders_fail_explicitly_when_dependencies_missing(self):
        adapters = [
            SileroVadAdapter(import_module=lambda _: (_ for _ in ()).throw(ImportError("missing"))),
            FasterWhisperSttAdapter(import_module=lambda _: (_ for _ in ()).throw(ImportError("missing"))),
            KokoroTtsAdapter(import_module=lambda _: (_ for _ in ()).throw(ImportError("missing"))),
        ]

        for adapter in adapters:
            with self.subTest(adapter=adapter.__class__.__name__):
                self.assertFalse(adapter.is_available())
                with self.assertRaises(BackendUnavailable):
                    adapter.health_check()


if __name__ == "__main__":
    unittest.main()
