from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from roger.feedback import Feedback


RunCommand = Callable[[list[str]], object]


@dataclass
class DesktopNotifier:
    run_command: RunCommand | None = None
    enabled: bool = True

    def notify(self, title: str, body: str) -> None:
        if not self.enabled:
            return
        runner = self.run_command or _default_run_command
        try:
            runner(["notify-send", title, body])
        except FileNotFoundError:
            return


class SystemFeedback:
    def __init__(self, notifier: DesktopNotifier | None = None):
        self.notifier = notifier or DesktopNotifier()

    def listening_for_wake(self, manual: bool = False) -> None:
        if manual:
            self.notifier.notify("Roger", "Manual wake activado")

    def wake_detected(self, phrase: str, score: float) -> None:
        self.notifier.notify("Roger", f"Wake detectado: {phrase}")

    def capturing_instruction(self) -> None:
        self.notifier.notify("Roger", "Escuchando instrucción")

    def transcribing(self) -> None:
        self.notifier.notify("Roger", "Transcribiendo")

    def transcription_ready(self, text: str) -> None:
        self.notifier.notify("Roger", f"Transcripción: {text}")

    def dispatching(self, session_name: str) -> None:
        self.notifier.notify("Roger", f"Enviando a pi-agent: {session_name}")

    def completed(self, status: str, message: str = "") -> None:
        self.notifier.notify("Roger", f"Resultado: {status}")


def _default_run_command(command: list[str]) -> object:
    return subprocess.run(command, check=False)
