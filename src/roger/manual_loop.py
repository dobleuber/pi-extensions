from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from roger.routing.registry import SessionRegistry
from roger.routing.router import Router
from roger.summarization import summarize_for_speech
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
    def __init__(self, registry: SessionRegistry, pi_runner: PiRunner, tts: TtsSpeaker, feedback: Feedback | None = None):
        self.router = Router(registry)
        self.preview = TranscriptionPreview()
        self.pi_runner = pi_runner
        self.tts = tts
        self.feedback = feedback

    def run_transcription(self, transcription: str, preview_action: str = "accept") -> ManualLoopResult:
        action = PreviewAction(preview_action)
        decision = self.preview.review(transcription, action=action)
        if not decision.accepted:
            speak_best_effort(self.tts, "Preview cancelled")
            return ManualLoopResult(status="cancelled", dispatched=False, session_name=None, message="Preview cancelled")

        route = self.router.route(decision.text)
        if route.needs_clarification:
            speak_best_effort(self.tts, route.question)
            return ManualLoopResult(status="needs_clarification", dispatched=False, session_name=None, message=route.question)

        if self.feedback is not None:
            self.feedback.dispatching(route.session_name)

        try:
            response = self.pi_runner.run_task(route.session_name, decision.text)
        except Exception as error:  # pi-agent failures should surface without crashing the loop
            speak_best_effort(self.tts, str(error))
            return ManualLoopResult(status="failed", dispatched=False, session_name=route.session_name, message=str(error))

        summary = summarize_for_speech(response)
        speak_best_effort(self.tts, summary)
        return ManualLoopResult(status="complete", dispatched=True, session_name=route.session_name, message=summary)
