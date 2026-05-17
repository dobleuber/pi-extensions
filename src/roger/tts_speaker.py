from __future__ import annotations

from dataclasses import dataclass

from roger.backends.interfaces import TtsBackend, SynthesizedSpeech


class NoopSpeaker:
    def __init__(self):
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


@dataclass
class SynthesizingSpeaker:
    backend: TtsBackend
    last_speech: SynthesizedSpeech | None = None

    def speak(self, text: str) -> None:
        self.last_speech = self.backend.synthesize(text)
