from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from roger.backends.interfaces import SttBackend, TtsBackend, VadBackend, WakeWordBackend
from roger.dialogue import DialogueControl, DialogueDecision
from roger.feedback import Feedback
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
        feedback: Feedback | None = None,
        dialogue_control: DialogueControl | None = None,
    ):
        self.wake = wake
        self.vad = vad
        self.stt = stt
        self.feedback = feedback
        self.tts = tts
        self.dialogue_control = dialogue_control or DialogueControl()
        self.manual_loop = ManualLoop(registry, pi_runner=pi_runner, tts=tts, feedback=feedback)
        self.preview_action = preview_action

    def run_once(self) -> VoiceLoopResult:
        if self.feedback is not None:
            self.feedback.listening_for_wake()
        detection = self.wake.listen_once()
        if detection is None:
            return VoiceLoopResult(state=VoiceLoopState.LISTENING, status="listening", dispatched=False)

        if self.feedback is not None:
            self.feedback.wake_detected(detection.phrase, detection.score)
            self.feedback.capturing_instruction()
        audio = self.vad.capture_until_silence()
        if audio.pcm16 == b"":
            if self.feedback is not None:
                self.feedback.completed("no_input", "")
            return VoiceLoopResult(
                state=VoiceLoopState.LISTENING,
                status="no_input",
                dispatched=False,
                message="",
            )
        if self.feedback is not None:
            self.feedback.transcribing()
        transcription = self.stt.transcribe(audio)
        if self.feedback is not None:
            self.feedback.transcription_ready(transcription.text)
        if not transcription.text.strip():
            if self.feedback is not None:
                self.feedback.completed("no_input", "")
            return VoiceLoopResult(
                state=VoiceLoopState.LISTENING,
                status="no_input",
                dispatched=False,
                message="",
            )
        if self.dialogue_control.decide(transcription.text) == DialogueDecision.GOODBYE:
            message = "Hasta luego."
            self.tts.speak(message)
            if self.feedback is not None:
                self.feedback.completed("goodbye", message)
            return VoiceLoopResult(
                state=VoiceLoopState.LISTENING,
                status="goodbye",
                dispatched=False,
                message=message,
            )
        result = self.manual_loop.run_transcription(transcription.text, preview_action=self.preview_action)
        if self.feedback is not None:
            self.feedback.completed(result.status, result.message)
        return VoiceLoopResult(
            state=VoiceLoopState.LISTENING,
            status=result.status,
            dispatched=result.dispatched,
            message=result.message,
        )
