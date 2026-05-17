from __future__ import annotations

from roger.backends.stt_faster_whisper import FasterWhisperSttAdapter
from roger.backends.tts_kokoro import KokoroTtsAdapter
from roger.backends.vad_silero import SileroVadAdapter
from roger.backends.wake_manual import ManualWakeWordAdapter
from roger.backends.wake_nanowakeword import NanoWakeWordAdapter
from roger.config import RogerConfig


def create_wake_backend(config: RogerConfig, force_manual: bool = False):
    if force_manual:
        return ManualWakeWordAdapter(target_phrase=config.speech.wake.target_phrase)
    if config.speech.wake.backend == "nanowakeword":
        return NanoWakeWordAdapter(
            model_path=config.speech.wake.model_path,
            target_phrase=config.speech.wake.target_phrase,
            threshold=config.speech.wake.threshold,
        )
    if config.speech.wake.backend == "manual":
        return ManualWakeWordAdapter(target_phrase=config.speech.wake.target_phrase)
    raise ValueError(f"Unsupported wake backend: {config.speech.wake.backend}")


def create_vad_backend(config: RogerConfig):
    if config.speech.vad.backend == "silero":
        return SileroVadAdapter()
    raise ValueError(f"Unsupported VAD backend: {config.speech.vad.backend}")


def create_stt_backend(config: RogerConfig):
    if config.speech.stt.backend == "faster-whisper":
        return FasterWhisperSttAdapter()
    raise ValueError(f"Unsupported STT backend: {config.speech.stt.backend}")


def create_tts_backend(config: RogerConfig):
    if config.speech.tts.backend == "kokoro":
        return KokoroTtsAdapter()
    raise ValueError(f"Unsupported TTS backend: {config.speech.tts.backend}")
