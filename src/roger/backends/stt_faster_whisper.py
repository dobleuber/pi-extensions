from __future__ import annotations

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import AudioSegment, Transcription


class FasterWhisperSttAdapter(OptionalDependencyMixin):
    dependency_module = "faster_whisper"

    def __init__(self, import_module: ImportModule = default_import_module):
        super().__init__(import_module=import_module)

    def transcribe(self, audio: AudioSegment) -> Transcription:
        self._load_module()
        raise NotImplementedError("faster-whisper transcription requires model loading integration.")
