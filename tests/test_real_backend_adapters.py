import types
import unittest
from pathlib import Path

from roger.backends.interfaces import AudioSegment
from roger.backends.stt_faster_whisper import FasterWhisperSttAdapter
from roger.backends.tts_kokoro import KokoroTtsAdapter
from roger.backends.vad_silero import SileroVadAdapter
from roger.backends.wake_nanowakeword import NanoWakeWordAdapter


class RealAdapterBehaviorTests(unittest.TestCase):
    def test_nanowakeword_predict_chunk_uses_interpreter_score(self):
        class Result:
            detected = True
            score = 0.97

        class Interpreter:
            @classmethod
            def load_model(cls, model):
                self = cls()
                self.model = model
                return self

            def predict(self, chunk):
                self.chunk = chunk
                return Result()

        module = types.SimpleNamespace(NanoInterpreter=Interpreter)
        adapter = NanoWakeWordAdapter("model.onnx", import_module=lambda _: module)

        detection = adapter.predict_chunk(b"\x00\x00" * 512)

        self.assertEqual(detection.phrase, "hola roger")
        self.assertEqual(detection.score, 0.97)

    def test_silero_detect_speech_from_path_uses_timestamps(self):
        module = types.SimpleNamespace(
            load_silero_vad=lambda onnx=True: "model",
            read_audio=lambda path, sampling_rate=16000: f"audio:{path}:{sampling_rate}",
            get_speech_timestamps=lambda audio, model, sampling_rate=16000, **kwargs: [
                {"start": 0, "end": 1600}
            ],
        )
        adapter = SileroVadAdapter(import_module=lambda _: module)

        timestamps = adapter.detect_speech(AudioSegment(path=Path("cmd.wav")))

        self.assertEqual(timestamps, [{"start": 0, "end": 1600}])

    def test_faster_whisper_transcribes_audio_path(self):
        class Segment:
            def __init__(self, text):
                self.text = text

        class WhisperModel:
            def __init__(self, model, device="auto", compute_type="default"):
                self.model = model

            def transcribe(self, audio, **kwargs):
                return [Segment(" hola"), Segment(" roger ")], types.SimpleNamespace(language="es")

        module = types.SimpleNamespace(WhisperModel=WhisperModel)
        adapter = FasterWhisperSttAdapter(import_module=lambda _: module, model="base", language="es")

        transcription = adapter.transcribe(AudioSegment(path=Path("cmd.wav")))

        self.assertEqual(transcription.text, "hola roger")

    def test_kokoro_synthesizes_float_audio_bytes(self):
        class FakeArray:
            def astype(self, dtype):
                return self

            def tobytes(self):
                return b"audio"

        class FakeTensor:
            def detach(self):
                return self

            def cpu(self):
                return self

            def numpy(self):
                return FakeArray()

        class Result:
            output = types.SimpleNamespace(audio=FakeTensor())

        class KPipeline:
            def __init__(self, lang_code, device=None):
                self.lang_code = lang_code

            def __call__(self, text, voice=None, speed=1):
                yield Result()

        module = types.SimpleNamespace(KPipeline=KPipeline)
        adapter = KokoroTtsAdapter(import_module=lambda _: module, voice="ef_dora")

        speech = adapter.synthesize("Hola")

        self.assertEqual(speech.audio, b"audio")
        self.assertEqual(speech.sample_rate, 24_000)


if __name__ == "__main__":
    unittest.main()
