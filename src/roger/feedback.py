from __future__ import annotations

from typing import Protocol


class Feedback(Protocol):
    def listening_for_wake(self, manual: bool = False) -> None: ...
    def wake_detected(self, phrase: str, score: float) -> None: ...
    def capturing_instruction(self) -> None: ...
    def transcribing(self) -> None: ...
    def transcription_ready(self, text: str) -> None: ...
    def dispatching(self, session_name: str) -> None: ...
    def completed(self, status: str, message: str = "") -> None: ...


class CompositeFeedback:
    def __init__(self, sinks: list[Feedback]):
        self.sinks = sinks

    def listening_for_wake(self, manual: bool = False) -> None:
        for sink in self.sinks:
            sink.listening_for_wake(manual=manual)

    def wake_detected(self, phrase: str, score: float) -> None:
        for sink in self.sinks:
            sink.wake_detected(phrase, score)

    def capturing_instruction(self) -> None:
        for sink in self.sinks:
            sink.capturing_instruction()

    def transcribing(self) -> None:
        for sink in self.sinks:
            sink.transcribing()

    def transcription_ready(self, text: str) -> None:
        for sink in self.sinks:
            sink.transcription_ready(text)

    def dispatching(self, session_name: str) -> None:
        for sink in self.sinks:
            sink.dispatching(session_name)

    def completed(self, status: str, message: str = "") -> None:
        for sink in self.sinks:
            sink.completed(status, message)


class ConsoleFeedback:
    def __init__(self, echo: bool = False, show_waiting: bool = True):
        self.echo = echo
        self.show_waiting = show_waiting
        self.lines: list[str] = []

    @property
    def output(self) -> str:
        return "\n".join(self.lines)

    def listening_for_wake(self, manual: bool = False) -> None:
        if not self.show_waiting:
            return
        if manual:
            self._write("Manual wake activado. Escuchando instrucción...")
        else:
            self._write("Esperando wake word: 'Hola Roger'...")

    def wake_detected(self, phrase: str, score: float) -> None:
        self._write(f"Wake detectado: {phrase} (score={score:.3f})")

    def capturing_instruction(self) -> None:
        self._write("Escuchando instrucción... hablá ahora; termino al detectar silencio.")

    def transcribing(self) -> None:
        self._write("Transcribiendo...")

    def transcription_ready(self, text: str) -> None:
        self._write(f"Transcripción: {text}")

    def dispatching(self, session_name: str) -> None:
        self._write(f"Enviando a pi-agent: {session_name}")

    def completed(self, status: str, message: str = "") -> None:
        self._write(f"Resultado: {status}")
        if message:
            self._write(f"Mensaje: {message}")

    def _write(self, line: str) -> None:
        self.lines.append(line)
        if self.echo:
            print(line, flush=True)
