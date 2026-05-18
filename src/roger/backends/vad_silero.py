from __future__ import annotations
import time
import numpy as np

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import AudioSegment


class SileroVadAdapter(OptionalDependencyMixin):
    dependency_module = "silero_vad"

    def __init__(
        self,
        import_module: ImportModule = default_import_module,
        sounddevice_module=None,
        sample_rate: int = 16_000,
        blocksize: int = 512,
        device: str | int | None = None,
        max_capture_seconds: float = 30.0,
        no_speech_timeout_seconds: float = 4.0,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 700,
        speech_pad_ms: int = 200,
        monotonic=time.monotonic,
    ):
        super().__init__(import_module=import_module)
        self._model = None
        self.sounddevice_module = sounddevice_module
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.device = device
        self.max_capture_seconds = max_capture_seconds
        self.no_speech_timeout_seconds = no_speech_timeout_seconds
        self.threshold = threshold
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms
        self.monotonic = monotonic

    def capture_until_silence(self) -> AudioSegment:
        module = self._load_module()
        sounddevice = self._load_sounddevice()
        model = self._load_model(module)
        vad_iterator = module.VADIterator(
            model,
            threshold=self.threshold,
            sampling_rate=self.sample_rate,
            min_silence_duration_ms=self.min_silence_duration_ms,
            speech_pad_ms=self.speech_pad_ms,
        )
        chunks: list[np.ndarray] = []
        seen_speech = False
        started = self.monotonic()
        with sounddevice.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.blocksize,
            device=self.device,
        ) as stream:
            while True:
                audio, _overflowed = stream.read(self.blocksize)
                samples = audio[:, 0] if getattr(audio, "ndim", 1) > 1 else audio
                chunks.append(np.asarray(samples, dtype=np.int16).copy())
                event = vad_iterator(self._to_float_tensor(samples))
                elapsed = self.monotonic() - started
                if event and "start" in event:
                    seen_speech = True
                if seen_speech and event and "end" in event:
                    break
                if not seen_speech and elapsed >= self.no_speech_timeout_seconds:
                    return AudioSegment(pcm16=b"", sample_rate=self.sample_rate)
                if elapsed >= self.max_capture_seconds:
                    break
        pcm16 = np.concatenate(chunks).astype(np.int16).tobytes() if chunks else b""
        return AudioSegment(pcm16=pcm16, sample_rate=self.sample_rate)

    def detect_speech(self, audio: AudioSegment) -> list[dict]:
        module = self._load_module()
        model = self._load_model(module)
        if audio.path is not None:
            waveform = module.read_audio(str(audio.path), sampling_rate=audio.sample_rate)
        elif audio.pcm16 is not None:
            import numpy as np
            import torch

            samples = np.frombuffer(audio.pcm16, dtype=np.int16).astype("float32") / 32768.0
            waveform = torch.from_numpy(samples)
        else:
            raise ValueError("AudioSegment must contain either path or pcm16 data")
        return module.get_speech_timestamps(
            waveform,
            model,
            sampling_rate=audio.sample_rate,
            threshold=0.5,
            min_speech_duration_ms=200,
            min_silence_duration_ms=700,
            speech_pad_ms=200,
        )

    def _load_model(self, module):
        if self._model is None:
            self._model = module.load_silero_vad(onnx=True)
        return self._model

    def _load_sounddevice(self):
        if self.sounddevice_module is not None:
            return self.sounddevice_module
        return default_import_module("sounddevice")

    @staticmethod
    def _to_float_tensor(samples):
        import torch

        array = np.asarray(samples, dtype=np.int16).astype("float32") / 32768.0
        return torch.from_numpy(array)
