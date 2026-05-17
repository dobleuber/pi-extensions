from __future__ import annotations

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import SynthesizedSpeech


class KokoroTtsAdapter(OptionalDependencyMixin):
    dependency_module = "kokoro"

    def __init__(self, import_module: ImportModule = default_import_module):
        super().__init__(import_module=import_module)

    def synthesize(self, text: str) -> SynthesizedSpeech:
        self._load_module()
        raise NotImplementedError("Kokoro synthesis requires voice/model integration.")
