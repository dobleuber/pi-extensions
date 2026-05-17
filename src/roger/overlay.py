from __future__ import annotations

from dataclasses import dataclass
from queue import Queue, Empty
from threading import Thread
from typing import Protocol


class Overlay(Protocol):
    def show(self, title: str, body: str, state: str = "active", timeout_ms: int | None = None) -> None: ...


@dataclass(frozen=True)
class OverlayMessage:
    title: str
    body: str
    state: str = "active"
    timeout_ms: int | None = None


class OverlayFeedback:
    """Feedback sink for a Siri/Google-like floating desktop overlay."""

    def __init__(self, overlay: Overlay | None = None):
        self.overlay = overlay or TkFloatingOverlay()

    def listening_for_wake(self, manual: bool = False) -> None:
        if manual:
            self.overlay.show("Roger activo", "Te escucho…", state="listening")

    def wake_detected(self, phrase: str, score: float) -> None:
        self.overlay.show("Roger activo", "Te escucho…", state="listening")

    def capturing_instruction(self) -> None:
        self.overlay.show("Escuchando", "Decime la tarea", state="listening")

    def transcribing(self) -> None:
        self.overlay.show("Transcribiendo", "Procesando tu voz…", state="processing")

    def transcription_ready(self, text: str) -> None:
        self.overlay.show("Transcripción", text, state="transcript")

    def dispatching(self, session_name: str) -> None:
        self.overlay.show("Ejecutando", f"Enviando a pi-agent: {session_name}", state="processing")

    def completed(self, status: str, message: str = "") -> None:
        body = message or status
        self.overlay.show("Resultado", body, state=status, timeout_ms=10_000)


class TkFloatingOverlay:
    """Small always-on-top overlay. Fails closed when no graphical session is available."""

    def __init__(self, width: int = 760, height: int = 220):
        self.width = width
        self.height = height
        self._queue: Queue[OverlayMessage] = Queue()
        self._started = False
        self._disabled = False

    def show(self, title: str, body: str, state: str = "active", timeout_ms: int | None = None) -> None:
        if self._disabled:
            return
        self._queue.put(OverlayMessage(title=title, body=body, state=state, timeout_ms=timeout_ms))
        self._ensure_started()

    def _ensure_started(self) -> None:
        if self._started or self._disabled:
            return
        self._started = True
        thread = Thread(target=self._run, name="roger-overlay", daemon=True)
        thread.start()

    def _run(self) -> None:
        try:
            import tkinter as tk
        except Exception:
            self._disabled = True
            return

        try:
            root = tk.Tk()
        except Exception:
            self._disabled = True
            return

        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.94)
        except Exception:
            pass

        screen_width = root.winfo_screenwidth()
        x = max(0, (screen_width - self.width) // 2)
        y = 72
        root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        root.configure(bg="#111827")

        title_var = tk.StringVar(value="Roger")
        body_var = tk.StringVar(value="")

        frame = tk.Frame(root, bg="#111827", padx=28, pady=24)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            textvariable=title_var,
            fg="#93c5fd",
            bg="#111827",
            font=("Sans", 22, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            frame,
            textvariable=body_var,
            fg="#f9fafb",
            bg="#111827",
            font=("Sans", 18),
            wraplength=self.width - 56,
            justify="left",
            anchor="w",
        ).pack(fill="both", expand=True, pady=(14, 0))

        hide_job = {"id": None}

        def hide() -> None:
            root.withdraw()

        def set_message(message: OverlayMessage) -> None:
            if hide_job["id"] is not None:
                root.after_cancel(hide_job["id"])
                hide_job["id"] = None
            title_var.set(message.title)
            body_var.set(message.body)
            root.deiconify()
            root.lift()
            if message.timeout_ms:
                hide_job["id"] = root.after(message.timeout_ms, hide)

        def poll() -> None:
            try:
                while True:
                    set_message(self._queue.get_nowait())
            except Empty:
                pass
            root.after(100, poll)

        poll()
        root.mainloop()
