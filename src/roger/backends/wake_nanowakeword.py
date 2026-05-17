from __future__ import annotations

from pathlib import Path

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import WakeDetection


class NanoWakeWordAdapter(OptionalDependencyMixin):
    dependency_module = "nanowakeword"

    def __init__(self, model_path: str | Path, import_module: ImportModule = default_import_module):
        super().__init__(import_module=import_module)
        self.model_path = Path(model_path)

    def listen_once(self) -> WakeDetection | None:
        self._load_module()
        raise NotImplementedError("Streaming NanoWakeWord inference will be wired after model training artifacts exist.")
