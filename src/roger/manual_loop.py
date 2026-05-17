from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from roger.routing.registry import SessionRegistry
from roger.routing.router import Router
from roger.summarization import summarize_for_speech
from roger.ui.preview import PreviewAction, TranscriptionPreview


class PiRunner(Protocol):
    def run_task(self, session_name: str, instruction: str) -> str: ...


class TtsSpeaker(Protocol):
    def speak(self, text: str) -> None: ...


@dataclass(frozen=True)
class ManualLoopResult:
    status: str
    dispatched: bool
    session_name: str | None
    message: str


class ManualLoop:
    def __init__(self, registry: SessionRegistry, pi_runner: PiRunner, tts: TtsSpeaker):
        self.router = Router(registry)
        self.preview = TranscriptionPreview()
        self.pi_runner = pi_runner
        self.tts = tts

    def run_transcription(self, transcription: str, preview_action: str = "accept") -> ManualLoopResult:
        action = PreviewAction(preview_action)
        decision = self.preview.review(transcription, action=action)
        if not decision.accepted:
            return ManualLoopResult(status="cancelled", dispatched=False, session_name=None, message="Preview cancelled")

        route = self.router.route(decision.text)
        if route.needs_clarification:
            return ManualLoopResult(status="needs_clarification", dispatched=False, session_name=None, message=route.question)

        try:
            response = self.pi_runner.run_task(route.session_name, decision.text)
        except Exception as error:  # pi-agent failures should surface without crashing the loop
            return ManualLoopResult(status="failed", dispatched=False, session_name=route.session_name, message=str(error))

        summary = summarize_for_speech(response)
        self.tts.speak(summary)
        return ManualLoopResult(status="complete", dispatched=True, session_name=route.session_name, message=summary)
