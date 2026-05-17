from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from roger.backends.interfaces import SttBackend, TtsBackend, VadBackend, WakeWordBackend
from roger.manual_loop import ManualLoop, PiRunner
from roger.routing.registry import SessionRegistry


class VoiceLoopState(StrEnum):
    LISTENING = "listening"
    CAPTURING = "capturing"
    TRANSCRIBING = "transcribing"
    DISPATCHING = "dispatching"


@dataclass(frozen=True)
class VoiceLoopResult:
    state: VoiceLoopState
    status: str
    dispatched: bool
    message: str = ""


class VoiceLoop:
    """One-instruction voice loop: wake -> VAD -> STT -> preview/router/pi/TTS -> listening."""

    def __init__(
        self,
        registry: SessionRegistry,
        wake: WakeWordBackend,
        vad: VadBackend,
        stt: SttBackend,
        pi_runner: PiRunner,
        tts: TtsBackend,
        preview_action: str = "accept",
    ):
        self.wake = wake
        self.vad = vad
        self.stt = stt
        self.manual_loop = ManualLoop(registry, pi_runner=pi_runner, tts=tts)
        self.preview_action = preview_action

    def run_once(self) -> VoiceLoopResult:
        detection = self.wake.listen_once()
        if detection is None:
            return VoiceLoopResult(state=VoiceLoopState.LISTENING, status="listening", dispatched=False)

        audio = self.vad.capture_until_silence()
        transcription = self.stt.transcribe(audio)
        result = self.manual_loop.run_transcription(transcription.text, preview_action=self.preview_action)
        return VoiceLoopResult(
            state=VoiceLoopState.LISTENING,
            status=result.status,
            dispatched=result.dispatched,
            message=result.message,
        )
