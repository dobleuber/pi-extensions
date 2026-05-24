from __future__ import annotations

from pathlib import Path
import warnings
from contextlib import contextmanager

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
        repo_id: str = "hexgrad/Kokoro-82M",
        config_path: str | Path | None = None,
        model_path: str | Path | None = None,
        voice_path: str | Path | None = None,
        local_files_only: bool = True,
    ):
        super().__init__(import_module=import_module)
        self.voice = voice
        self.lang_code = lang_code
        self.device = device
        self.repo_id = repo_id
        self.config_path = Path(config_path).expanduser() if config_path is not None else None
        self.model_path = Path(model_path).expanduser() if model_path is not None else None
        self.voice_path = Path(voice_path).expanduser() if voice_path is not None else None
        self.local_files_only = local_files_only
        self._pipeline = None
        self._voice_for_call: str | None = None

    def synthesize(self, text: str) -> SynthesizedSpeech:
        pipeline = self._load_pipeline()
        audio_chunks: list[bytes] = []
        voice = self._voice_for_call or self.voice
        for result in pipeline(text, voice=voice, speed=1):
            audio = _extract_audio(result)
            if audio is None:
                continue
            array = audio.detach().cpu().numpy().astype("float32")
            audio_chunks.append(array.tobytes())
        return SynthesizedSpeech(audio=b"".join(audio_chunks), sample_rate=24_000)

    def _load_pipeline(self):
        if self._pipeline is None:
            module = self._load_module()
            if self.local_files_only:
                config_path, model_path, voice_path = self._resolve_local_assets()
                with _suppress_known_kokoro_warnings():
                    model = module.KModel(repo_id=self.repo_id, config=str(config_path), model=str(model_path))
                if self.device is not None and hasattr(model, "to"):
                    model = model.to(self.device)
                if hasattr(model, "eval"):
                    model = model.eval()
                self._voice_for_call = str(voice_path)
                with _suppress_known_kokoro_warnings():
                    self._pipeline = module.KPipeline(
                        lang_code=self.lang_code,
                        repo_id=self.repo_id,
                        model=model,
                        device=self.device,
                    )
            else:
                self._voice_for_call = self.voice
                with _suppress_known_kokoro_warnings():
                    self._pipeline = module.KPipeline(
                        lang_code=self.lang_code,
                        repo_id=self.repo_id,
                        device=self.device,
                    )
        return self._pipeline

    def _resolve_local_assets(self) -> tuple[Path, Path, Path]:
        config_path = self.config_path or _hf_cache_file(self.repo_id, "config.json")
        model_path = self.model_path or _hf_cache_file(self.repo_id, "kokoro-v1_0.pth")
        voice_path = self.voice_path or _hf_cache_file(self.repo_id, f"voices/{self.voice}.pt")
        missing = [path for path in (config_path, model_path, voice_path) if not path.exists()]
        if missing:
            missing_list = ", ".join(str(path) for path in missing)
            raise FileNotFoundError(
                "Kokoro local assets not found. Run a one-time model download or set "
                "speech.tts.config_path/model_path/voice_path. Missing: " + missing_list
            )
        return config_path, model_path, voice_path


def _extract_audio(result):
    if isinstance(result, tuple | list):
        return result[-1]
    output = getattr(result, "output", None)
    audio = getattr(output, "audio", None)
    if audio is not None:
        return audio
    return getattr(result, "audio", None)


def _hf_cache_file(repo_id: str, filename: str) -> Path:
    repo_dir = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo_id.replace('/', '--')}"
    ref = repo_dir / "refs" / "main"
    if ref.exists():
        revision = ref.read_text(encoding="utf-8").strip()
        return repo_dir / "snapshots" / revision / filename
    return repo_dir / "snapshots" / "main" / filename


@contextmanager
def _suppress_known_kokoro_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*dropout option adds dropout.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*weight_norm.*deprecated.*", category=FutureWarning)
        yield
