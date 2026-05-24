from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class WakeDetection:
    phrase: str
    score: float


@dataclass(frozen=True)
class AudioSegment:
    path: Path | None = None
    pcm16: bytes | None = None
    sample_rate: int = 16_000


@dataclass(frozen=True)
class Transcription:
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class SynthesizedSpeech:
    audio: bytes | None = None
    path: Path | None = None
    sample_rate: int | None = None


class WakeWordBackend(Protocol):
    def listen_once(self) -> WakeDetection | None: ...


class VadBackend(Protocol):
    def capture_until_silence(self) -> AudioSegment: ...


class SttBackend(Protocol):
    def transcribe(self, audio: AudioSegment) -> Transcription: ...


class TtsBackend(Protocol):
    def synthesize(self, text: str) -> SynthesizedSpeech: ...
