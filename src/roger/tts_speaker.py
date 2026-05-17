from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import numpy as np

from roger.backends.interfaces import TtsBackend, SynthesizedSpeech


class NoopSpeaker:
    def __init__(self):
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


@dataclass
class SynthesizingSpeaker:
    backend: TtsBackend
    audio_player: Callable[[SynthesizedSpeech], None] | None = None
    last_speech: SynthesizedSpeech | None = None

    def speak(self, text: str) -> None:
        self.last_speech = self.backend.synthesize(text)
        player = self.audio_player or play_with_sounddevice
        player(self.last_speech)


def play_with_sounddevice(speech: SynthesizedSpeech) -> None:
    if not speech.audio or not speech.sample_rate:
        return
    import sounddevice as sd

    audio = np.frombuffer(speech.audio, dtype=np.float32)
    sd.play(audio, samplerate=speech.sample_rate)
    sd.wait()
