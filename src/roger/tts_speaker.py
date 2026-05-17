from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import shutil
import subprocess
import tempfile
import wave
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
        player = self.audio_player or SystemAudioPlayer().play
        player(self.last_speech)


class SystemAudioPlayer:
    def __init__(
        self,
        command_exists: Callable[[str], bool] | None = None,
        run_command: Callable[[list[str]], object] | None = None,
        sounddevice_module=None,
    ):
        self.command_exists = command_exists or (lambda command: shutil.which(command) is not None)
        self.run_command = run_command or (lambda command: subprocess.run(command, check=False))
        self.sounddevice_module = sounddevice_module

    def play(self, speech: SynthesizedSpeech) -> None:
        if not speech.audio or not speech.sample_rate:
            return
        audio = np.frombuffer(speech.audio, dtype=np.float32)
        if audio.size == 0:
            return
        if self.command_exists("pw-play"):
            self._play_with_pw_play(audio, speech.sample_rate)
            return
        self._play_with_sounddevice(audio, speech.sample_rate)

    def _play_with_pw_play(self, audio: np.ndarray, sample_rate: int) -> None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as file:
            pcm16 = np.clip(audio, -1.0, 1.0)
            pcm16 = (pcm16 * 32767).astype(np.int16)
            with wave.open(file.name, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(pcm16.tobytes())
            self.run_command(["pw-play", file.name])

    def _play_with_sounddevice(self, audio: np.ndarray, sample_rate: int) -> None:
        sd = self.sounddevice_module
        if sd is None:
            import sounddevice as sd
        sd.play(audio, samplerate=sample_rate)
        sd.wait()


def play_with_sounddevice(speech: SynthesizedSpeech) -> None:
    if not speech.audio or not speech.sample_rate:
        return
    SystemAudioPlayer(command_exists=lambda command: False).play(speech)
