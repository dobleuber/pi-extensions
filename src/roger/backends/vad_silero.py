from __future__ import annotations

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import AudioSegment


class SileroVadAdapter(OptionalDependencyMixin):
    dependency_module = "silero_vad"

    def __init__(self, import_module: ImportModule = default_import_module):
        super().__init__(import_module=import_module)
        self._model = None

    def capture_until_silence(self) -> AudioSegment:
        self._load_module()
        raise NotImplementedError("Silero VAD capture requires microphone capture integration.")

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
