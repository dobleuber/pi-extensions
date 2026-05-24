from __future__ import annotations

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import AudioSegment, Transcription


class FasterWhisperSttAdapter(OptionalDependencyMixin):
    dependency_module = "faster_whisper"

    def __init__(
        self,
        import_module: ImportModule = default_import_module,
        model: str = "base",
        language: str = "es",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        super().__init__(import_module=import_module)
        self.model_name = model
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def transcribe(self, audio: AudioSegment) -> Transcription:
        model = self._load_model()
        if audio.path is not None:
            source = str(audio.path)
        elif audio.pcm16 is not None:
            import numpy as np

            source = np.frombuffer(audio.pcm16, dtype=np.int16).astype("float32") / 32768.0
        else:
            raise ValueError("AudioSegment must contain either path or pcm16 data")
        segments, _info = model.transcribe(
            source,
            language=self.language,
            task="transcribe",
            beam_size=1,
            condition_on_previous_text=False,
            temperature=0.0,
        )
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        return Transcription(text=text)

    def _load_model(self):
        if self._model is None:
            module = self._load_module()
            self._model = module.WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
        return self._model
