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
        return SileroVadAdapter(
            max_capture_seconds=config.speech.vad.max_capture_seconds,
            min_silence_duration_ms=config.speech.vad.silence_timeout_ms,
        )
    raise ValueError(f"Unsupported VAD backend: {config.speech.vad.backend}")


def create_stt_backend(config: RogerConfig):
    if config.speech.stt.backend == "faster-whisper":
        return FasterWhisperSttAdapter(
            model=config.speech.stt.model,
            language=config.speech.stt.language,
            device=config.speech.stt.device,
            compute_type=config.speech.stt.compute_type,
        )
    raise ValueError(f"Unsupported STT backend: {config.speech.stt.backend}")


def create_tts_backend(config: RogerConfig):
    if config.speech.tts.backend == "kokoro":
        voice = "ef_dora" if config.speech.tts.voice == "spanish-default" else config.speech.tts.voice
        return KokoroTtsAdapter(
            voice=voice,
            repo_id=config.speech.tts.repo_id,
            config_path=config.speech.tts.config_path,
            model_path=config.speech.tts.model_path,
            voice_path=config.speech.tts.voice_path,
            local_files_only=config.speech.tts.local_files_only,
        )
    raise ValueError(f"Unsupported TTS backend: {config.speech.tts.backend}")
