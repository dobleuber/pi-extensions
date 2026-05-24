from __future__ import annotations

from roger.backends.interfaces import WakeDetection


class ManualWakeWordAdapter:
    """Development wake adapter that activates only when explicitly triggered."""

    def __init__(self, target_phrase: str = "hola roger"):
        self.target_phrase = target_phrase
        self._triggered = False

    def trigger(self) -> None:
        self._triggered = True

    def listen_once(self) -> WakeDetection | None:
        if not self._triggered:
            return None
        self._triggered = False
        return WakeDetection(phrase=self.target_phrase, score=1.0)
