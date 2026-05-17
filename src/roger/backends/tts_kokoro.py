from __future__ import annotations

from roger.backends._optional import ImportModule, OptionalDependencyMixin, default_import_module
from roger.backends.interfaces import SynthesizedSpeech


class KokoroTtsAdapter(OptionalDependencyMixin):
    dependency_module = "kokoro"

    def __init__(
        self,
        import_module: ImportModule = default_import_module,
        voice: str = "ef_dora",
        lang_code: str = "e",
        device: str | None = None,
    ):
        super().__init__(import_module=import_module)
        self.voice = voice
        self.lang_code = lang_code
        self.device = device
        self._pipeline = None

    def synthesize(self, text: str) -> SynthesizedSpeech:
        pipeline = self._load_pipeline()
        audio_chunks: list[bytes] = []
        for result in pipeline(text, voice=self.voice, speed=1):
            output = getattr(result, "output", None)
            audio = getattr(output, "audio", None)
            if audio is None:
                continue
            array = audio.detach().cpu().numpy().astype("float32")
            audio_chunks.append(array.tobytes())
        return SynthesizedSpeech(audio=b"".join(audio_chunks), sample_rate=24_000)

    def _load_pipeline(self):
        if self._pipeline is None:
            module = self._load_module()
            self._pipeline = module.KPipeline(lang_code=self.lang_code, device=self.device)
        return self._pipeline
