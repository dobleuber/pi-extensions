from __future__ import annotations

from pathlib import Path
import numpy as np

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import WakeDetection


class NanoWakeWordAdapter(OptionalDependencyMixin):
    dependency_module = "nanowakeword"

    def __init__(self, model_path: str | Path, import_module: ImportModule = default_import_module):
        super().__init__(import_module=import_module)
        self.model_path = Path(model_path)
        self._interpreter = None

    def listen_once(self) -> WakeDetection | None:
        self._load_module()
        raise NotImplementedError("Streaming NanoWakeWord inference will be wired after model training artifacts exist.")

    def predict_chunk(self, pcm16: bytes, target_phrase: str = "hola roger") -> WakeDetection | None:
        interpreter = self._load_interpreter()
        chunk = np.frombuffer(pcm16, dtype=np.int16)
        result = interpreter.predict(chunk)
        detected = bool(getattr(result, "detected", False))
        score = float(getattr(result, "score", 0.0))
        if not detected:
            return None
        return WakeDetection(phrase=target_phrase, score=score)

    def _load_interpreter(self):
        if self._interpreter is None:
            module = self._load_module()
            self._interpreter = module.NanoInterpreter.load_model(str(self.model_path))
        return self._interpreter
