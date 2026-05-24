from __future__ import annotations

from enum import StrEnum
import re
import unicodedata


class DialogueDecision(StrEnum):
    CONTINUE = "continue"
    GOODBYE = "goodbye"
    STOP = "stop"


class DialogueControl:
    def decide(self, text: str) -> DialogueDecision:
        normalized = _normalize(text)
        if re.search(r"\bgracias\b.*\broger\b", normalized):
            return DialogueDecision.GOODBYE
        if re.search(r"\b(para|cancela|detente|stop)\b.*\broger\b", normalized):
            return DialogueDecision.STOP
        return DialogueDecision.CONTINUE


def _normalize(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9ñ ]+", " ", without_accents)
