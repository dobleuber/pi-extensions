from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from roger.routing.registry import SessionRegistry
from roger.routing.router import Router
from collections.abc import Callable

from roger.summarization import SpeechScript, prepare_speech_script
from roger.ui.preview import PreviewAction, TranscriptionPreview
from roger.feedback import Feedback
from roger.tts_speaker import speak_best_effort


class PiRunner(Protocol):
    def run_task(self, session_name: str, instruction: str) -> str: ...
    def cancel_active(self, session_name: str | None = None, command: str = "abort"): ...


class TtsSpeaker(Protocol):
    def speak(self, text: str) -> None: ...


@dataclass(frozen=True)
class ManualLoopResult:
    status: str
    dispatched: bool
    session_name: str | None
    message: str


class ManualLoop:
    def __init__(
        self,
        registry: SessionRegistry,
        pi_runner: PiRunner,
        tts: TtsSpeaker,
        feedback: Feedback | None = None,
        speech_preparer: Callable[[str], SpeechScript] = prepare_speech_script,
    ):
        self.router = Router(registry)
        self.preview = TranscriptionPreview()
        self.pi_runner = pi_runner
        self.tts = tts
        self.feedback = feedback
        self.speech_preparer = speech_preparer

    def run_transcription(self, transcription: str, preview_action: str = "accept") -> ManualLoopResult:
        action = PreviewAction(preview_action)
        decision = self.preview.review(transcription, action=action)
        if not decision.accepted:
            message = "Preview cancelled"
            speak_best_effort(self.tts, self.speech_preparer(message).speech_text)
            return ManualLoopResult(status="cancelled", dispatched=False, session_name=None, message=message)

        route = self.router.route(decision.text)
        if route.needs_clarification:
            speak_best_effort(self.tts, self.speech_preparer(route.question).speech_text)
            return ManualLoopResult(status="needs_clarification", dispatched=False, session_name=None, message=route.question)

        if self.feedback is not None:
            self.feedback.dispatching(route.session_name)

        try:
            response = self.pi_runner.run_task(route.session_name, decision.text)
        except Exception as error:  # pi-agent failures should surface without crashing the loop
            message = str(error)
            speak_best_effort(self.tts, self.speech_preparer(message).speech_text)
            return ManualLoopResult(status="failed", dispatched=False, session_name=route.session_name, message=message)

        script = self.speech_preparer(response)
        speak_best_effort(self.tts, script.speech_text)
        return ManualLoopResult(status="complete", dispatched=True, session_name=route.session_name, message=response)
