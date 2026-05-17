from __future__ import annotations

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import AudioSegment


class SileroVadAdapter(OptionalDependencyMixin):
    dependency_module = "silero_vad"

    def __init__(self, import_module: ImportModule = default_import_module):
        super().__init__(import_module=import_module)

    def capture_until_silence(self) -> AudioSegment:
        self._load_module()
        raise NotImplementedError("Silero VAD capture requires microphone capture integration.")
