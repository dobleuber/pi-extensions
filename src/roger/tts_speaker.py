from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import shutil
import subprocess
import tempfile
import wave
import numpy as np

from roger.backends.interfaces import TtsBackend, SynthesizedSpeech


@dataclass(frozen=True)
class SpeakResult:
    text: str
    success: bool
    skipped: bool = False
    error: str = ""


class NoopSpeaker:
    def __init__(self):
        self.spoken: list[str] = []

    def speak(self, text: str) -> SpeakResult:
        self.spoken.append(text)
        return SpeakResult(text=text, success=True, skipped=True)


@dataclass
class SafeSpeaker:
    speaker: object
    warning_callback: Callable[[str], None] | None = None
    repeat_warning_interval: int = 5
    failures: int = 0
    last_error: str = ""

    def speak(self, text: str) -> SpeakResult:
        try:
            result = self.speaker.speak(text)
        except Exception as error:
            self.failures += 1
            self.last_error = str(error)
            self._maybe_warn(str(error))
            return SpeakResult(text=text, success=False, error=str(error))
        if isinstance(result, SpeakResult):
            return result
        return SpeakResult(text=text, success=True)

    def _maybe_warn(self, error: str) -> None:
        if self.warning_callback is None:
            return
        if self.failures != 1 and (self.failures - 1) % self.repeat_warning_interval != 0:
            return
        self.warning_callback(f"Speech output degraded: {error}")


@dataclass
class SynthesizingSpeaker:
    backend: TtsBackend
    audio_player: Callable[[SynthesizedSpeech], None] | None = None
    last_speech: SynthesizedSpeech | None = None

    def speak(self, text: str) -> SpeakResult:
        self.last_speech = self.backend.synthesize(text)
        player = self.audio_player or SystemAudioPlayer().play
        player(self.last_speech)
        return SpeakResult(text=text, success=True)


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


def speak_best_effort(speaker: object, text: str) -> SpeakResult:
    try:
        result = speaker.speak(text)
    except Exception as error:
        return SpeakResult(text=text, success=False, error=str(error))
    if isinstance(result, SpeakResult):
        return result
    return SpeakResult(text=text, success=True)


def play_with_sounddevice(speech: SynthesizedSpeech) -> None:
    if not speech.audio or not speech.sample_rate:
        return
    SystemAudioPlayer(command_exists=lambda command: False).play(speech)
