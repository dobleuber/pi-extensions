from __future__ import annotations

from pathlib import Path
import time
from collections.abc import Callable
import numpy as np

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import WakeDetection


class NanoWakeWordAdapter(OptionalDependencyMixin):
    dependency_module = "nanowakeword"

    def __init__(
        self,
        model_path: str | Path,
        import_module: ImportModule = default_import_module,
        sounddevice_module=None,
        target_phrase: str = "hola roger",
        threshold: float = 0.85,
        samplerate: int = 16_000,
        blocksize: int = 1280,
        device: str | int | None = None,
        duration: float = 0.0,
        score_callback: Callable[[float], None] | None = None,
    ):
        super().__init__(import_module=import_module)
        self.model_path = Path(model_path)
        self.sounddevice_module = sounddevice_module
        self.target_phrase = target_phrase
        self.threshold = threshold
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.device = device
        self.duration = duration
        self.score_callback = score_callback
        self._interpreter = None

    def listen_once(self) -> WakeDetection | None:
        sounddevice = self._load_sounddevice()
        started = time.monotonic()
        with sounddevice.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="int16",
            blocksize=self.blocksize,
            device=self.device,
        ) as stream:
            while True:
                audio, _overflowed = stream.read(self.blocksize)
                samples = audio[:, 0] if getattr(audio, "ndim", 1) > 1 else audio
                detection = self.predict_samples(samples)
                if detection is not None:
                    return detection
                if self.duration > 0 and time.monotonic() - started >= self.duration:
                    return None

    def predict_chunk(self, pcm16: bytes, target_phrase: str = "hola roger") -> WakeDetection | None:
        chunk = np.frombuffer(pcm16, dtype=np.int16)
        return self.predict_samples(chunk, target_phrase=target_phrase)

    def predict_samples(self, samples, target_phrase: str | None = None) -> WakeDetection | None:
        interpreter = self._load_interpreter()
        phrase = self.target_phrase if target_phrase is None else target_phrase
        threshold = {interpreter.model_name: self.threshold} if hasattr(interpreter, "model_name") else {}
        result = interpreter.predict(samples, threshold=threshold)
        detected = bool(getattr(result, "detected", False))
        score = float(getattr(result, "score", 0.0))
        if self.score_callback is not None:
            self.score_callback(score)
        if not detected:
            return None
        return WakeDetection(phrase=phrase, score=score)

    def _load_interpreter(self):
        if self._interpreter is None:
            module = self._load_module()
            self._interpreter = module.NanoInterpreter.load_model(str(self.model_path))
        return self._interpreter

    def _load_sounddevice(self):
        if self.sounddevice_module is not None:
            return self.sounddevice_module
        return default_import_module("sounddevice")
