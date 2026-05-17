from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PreviewAction(StrEnum):
    ACCEPT = "accept"
    CANCEL = "cancel"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class PreviewDecision:
    text: str
    accepted: bool
    reason: str


class TranscriptionPreview:
    def __init__(self, accept_on_timeout: bool = True):
        self.accept_on_timeout = accept_on_timeout

    def review(self, text: str, action: PreviewAction = PreviewAction.TIMEOUT) -> PreviewDecision:
        if action == PreviewAction.ACCEPT:
            return PreviewDecision(text=text, accepted=True, reason="accepted")
        if action == PreviewAction.CANCEL:
            return PreviewDecision(text=text, accepted=False, reason="cancelled")
        return PreviewDecision(text=text, accepted=self.accept_on_timeout, reason="timeout")
