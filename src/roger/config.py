from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any
import copy
import tomllib


@dataclass(frozen=True)
class WakeConfig:
    backend: str = "nanowakeword"
    target_phrase: str = "hola roger"
    model_path: Path = Path("models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx")
    architectures: list[str] = field(default_factory=lambda: ["gru", "lstm", "tcn"])
    threshold: float = 0.85


@dataclass(frozen=True)
class VadConfig:
    backend: str = "silero"
    silence_timeout_ms: int = 900
    max_capture_seconds: int = 30


@dataclass(frozen=True)
class SttConfig:
    backend: str = "faster-whisper"
    model: str = "large-v3-turbo"
    language: str = "es"
    device: str = "cuda"
    compute_type: str = "float16"


@dataclass(frozen=True)
class TtsConfig:
    backend: str = "kokoro"
    voice: str = "spanish-default"
    repo_id: str = "hexgrad/Kokoro-82M"
    config_path: Path | None = None
    model_path: Path | None = None
    voice_path: Path | None = None
    local_files_only: bool = True


@dataclass(frozen=True)
class SpeechConfig:
    wake: WakeConfig = field(default_factory=WakeConfig)
    vad: VadConfig = field(default_factory=VadConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str | None = None


@dataclass(frozen=True)
class ModelsConfig:
    online: ModelConfig = field(default_factory=lambda: ModelConfig(provider="pi-default"))
    offline: ModelConfig = field(default_factory=lambda: ModelConfig(provider="ollama"))


@dataclass(frozen=True)
class SessionConfig:
    cwd: Path
    description: str = ""


@dataclass(frozen=True)
class RogerConfig:
    speech: SpeechConfig = field(default_factory=SpeechConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    sessions: dict[str, SessionConfig] = field(default_factory=dict)

    @classmethod
    def default(cls, project_dir: Path | None = None) -> "RogerConfig":
        project = Path.cwd() if project_dir is None else project_dir
        return cls(
            sessions={
                "system": SessionConfig(cwd=Path.home(), description="Laptop/system tasks"),
                "current-project": SessionConfig(cwd=project, description="Active project tasks"),
            }
        )


def load_config(path: Path | None = None, project_dir: Path | None = None) -> RogerConfig:
    config = RogerConfig.default(project_dir=project_dir)
    if path is None or not path.exists():
        return config

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return _merge_config(config, data)


def _merge_config(config: RogerConfig, data: dict[str, Any]) -> RogerConfig:
    speech = config.speech
    speech_data = data.get("speech", {})
    if "wake" in speech_data:
        speech = replace(speech, wake=_merge_dataclass(speech.wake, speech_data["wake"]))
    if "vad" in speech_data:
        speech = replace(speech, vad=_merge_dataclass(speech.vad, speech_data["vad"]))
    if "stt" in speech_data:
        speech = replace(speech, stt=_merge_dataclass(speech.stt, speech_data["stt"]))
    if "tts" in speech_data:
        speech = replace(speech, tts=_merge_dataclass(speech.tts, speech_data["tts"]))

    models = config.models
    models_data = data.get("models", {})
    if "online" in models_data:
        models = replace(models, online=_merge_dataclass(models.online, models_data["online"]))
    if "offline" in models_data:
        models = replace(models, offline=_merge_dataclass(models.offline, models_data["offline"]))

    sessions = copy.copy(config.sessions)
    for name, values in data.get("sessions", {}).items():
        existing = sessions.get(name, SessionConfig(cwd=Path.cwd()))
        merged = _merge_dataclass(existing, values)
        sessions[name] = merged

    return RogerConfig(speech=speech, models=models, sessions=sessions)


def _merge_dataclass(instance: Any, values: dict[str, Any]) -> Any:
    converted: dict[str, Any] = {}
    for key, value in values.items():
        current = getattr(instance, key, None)
        if isinstance(current, Path):
            converted[key] = Path(value).expanduser()
        elif current is None and key.endswith("_path") and value is not None:
            converted[key] = Path(value).expanduser()
        else:
            converted[key] = value
    return replace(instance, **converted)
