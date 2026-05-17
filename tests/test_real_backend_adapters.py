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
            model_name = "hola_roger_lstm"

            @classmethod
            def load_model(cls, model):
                self = cls()
                self.model = model
                return self

            def predict(self, chunk, threshold=None):
                self.chunk = chunk
                self.threshold = threshold
                return Result()

        module = types.SimpleNamespace(NanoInterpreter=Interpreter)
        adapter = NanoWakeWordAdapter("model.onnx", import_module=lambda _: module, threshold=0.85)

        detection = adapter.predict_chunk(b"\x00\x00" * 512)

        self.assertEqual(detection.phrase, "hola roger")
        self.assertEqual(detection.score, 0.97)
        self.assertEqual(adapter._interpreter.threshold, {"hola_roger_lstm": 0.85})

    def test_nanowakeword_reports_scores_even_below_detection_threshold(self):
        class Result:
            detected = False
            score = 0.42

        class Interpreter:
            model_name = "hola_roger_lstm"

            @classmethod
            def load_model(cls, model):
                return cls()

            def predict(self, chunk, threshold=None):
                return Result()

        scores = []
        module = types.SimpleNamespace(NanoInterpreter=Interpreter)
        adapter = NanoWakeWordAdapter(
            "model.onnx",
            import_module=lambda _: module,
            threshold=0.85,
            score_callback=scores.append,
        )

        detection = adapter.predict_chunk(b"\x00\x00" * 512)

        self.assertIsNone(detection)
        self.assertEqual(scores, [0.42])

    def test_nanowakeword_detects_by_score_threshold_like_standalone_listener(self):
        class Result:
            detected = False
            score = 0.91

        class Interpreter:
            model_name = "hola_roger_lstm"

            @classmethod
            def load_model(cls, model):
                return cls()

            def predict(self, chunk, threshold=None):
                return Result()

        module = types.SimpleNamespace(NanoInterpreter=Interpreter)
        adapter = NanoWakeWordAdapter("model.onnx", import_module=lambda _: module, threshold=0.85)

        detection = adapter.predict_chunk(b"\x00\x00" * 512)

        self.assertIsNotNone(detection)
        self.assertEqual(detection.score, 0.91)

    def test_nanowakeword_listen_once_reads_microphone_until_detection(self):
        import numpy as np

        class Result:
            def __init__(self, detected, score):
                self.detected = detected
                self.score = score

        class Interpreter:
            model_name = "hola_roger_lstm"

            def __init__(self):
                self.calls = 0

            @classmethod
            def load_model(cls, model):
                return cls()

            def predict(self, chunk, threshold=None):
                self.calls += 1
                return Result(self.calls == 2, 0.91 if self.calls == 2 else 0.1)

        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, blocksize):
                return np.zeros((blocksize, 1), dtype=np.int16), None

        sounddevice = types.SimpleNamespace(InputStream=lambda **kwargs: Stream())
        module = types.SimpleNamespace(NanoInterpreter=Interpreter)
        adapter = NanoWakeWordAdapter(
            "model.onnx",
            import_module=lambda _: module,
            sounddevice_module=sounddevice,
            threshold=0.85,
            duration=2.0,
        )

        detection = adapter.listen_once()

        self.assertEqual(detection.phrase, "hola roger")
        self.assertEqual(detection.score, 0.91)

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

    def test_silero_capture_until_silence_returns_pcm_after_end_event(self):
        import numpy as np

        class FakeVadIterator:
            def __init__(self, model, **kwargs):
                self.calls = 0

            def __call__(self, chunk):
                self.calls += 1
                if self.calls == 1:
                    return {"start": 0}
                if self.calls == 2:
                    return {"end": 512}
                return None

        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, blocksize):
                return np.ones((blocksize, 1), dtype=np.int16), None

        module = types.SimpleNamespace(
            load_silero_vad=lambda onnx=True: "model",
            VADIterator=FakeVadIterator,
        )
        sounddevice = types.SimpleNamespace(InputStream=lambda **kwargs: Stream())
        adapter = SileroVadAdapter(import_module=lambda _: module, sounddevice_module=sounddevice, max_capture_seconds=2)

        audio = adapter.capture_until_silence()

        self.assertEqual(audio.sample_rate, 16_000)
        self.assertGreater(len(audio.pcm16), 0)

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
            def __init__(self, lang_code, repo_id=None, device=None):
                self.lang_code = lang_code

            def __call__(self, text, voice=None, speed=1):
                yield Result()

        module = types.SimpleNamespace(KPipeline=KPipeline)
        adapter = KokoroTtsAdapter(import_module=lambda _: module, voice="ef_dora", local_files_only=False)

        speech = adapter.synthesize("Hola")

        self.assertEqual(speech.audio, b"audio")
        self.assertEqual(speech.sample_rate, 24_000)

    def test_kokoro_uses_local_model_config_and_voice_when_requested(self):
        import tempfile
        import warnings

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.json"
            model = root / "kokoro-v1_0.pth"
            voice = root / "voices" / "ef_dora.pt"
            voice.parent.mkdir()
            config.write_text("{}", encoding="utf-8")
            model.write_bytes(b"model")
            voice.write_bytes(b"voice")

            calls = {}

            class KModel:
                def __init__(self, repo_id=None, config=None, model=None):
                    warnings.warn("dropout option adds dropout after all but last recurrent layer", UserWarning)
                    calls["model"] = {"repo_id": repo_id, "config": config, "model": model}

                def eval(self):
                    return self

            class KPipeline:
                def __init__(self, lang_code, repo_id=None, model=True, device=None):
                    calls["pipeline"] = {"repo_id": repo_id, "model": model}

                def __call__(self, text, voice=None, speed=1):
                    calls["voice"] = voice
                    return []

            module = types.SimpleNamespace(KModel=KModel, KPipeline=KPipeline)
            adapter = KokoroTtsAdapter(
                import_module=lambda _: module,
                voice="ef_dora",
                config_path=config,
                model_path=model,
                voice_path=voice,
                local_files_only=True,
            )

            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                adapter.synthesize("Hola")

        self.assertEqual(calls["model"]["repo_id"], "hexgrad/Kokoro-82M")
        self.assertEqual(calls["model"]["config"], str(config))
        self.assertEqual(calls["model"]["model"], str(model))
        self.assertEqual(calls["voice"], str(voice))
        self.assertEqual(captured, [])


if __name__ == "__main__":
    unittest.main()
