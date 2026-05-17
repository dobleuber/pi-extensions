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
        self.overlay = overlay or GtkLayerShellFloatingOverlay()

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


class GtkLayerShellFloatingOverlay:
    """Wayland-native always-on-top overlay for Hyprland/Omarchy.

    Uses gtk-layer-shell when available so the Roger UI behaves like a desktop
    shell surface instead of a normal application window. This is a better fit
    for Omarchy/Hyprland than Tk/XWayland-style topmost windows.
    """

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
        thread = Thread(target=self._run, name="roger-layer-shell-overlay", daemon=True)
        thread.start()

    def _run(self) -> None:
        try:
            import gi

            gi.require_version("Gtk", "3.0")
            gi.require_version("GtkLayerShell", "0.1")
            from gi.repository import Gdk, GLib, Gtk, GtkLayerShell
        except Exception:
            self._fallback_to_tk()
            return

        try:
            window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            GtkLayerShell.init_for_window(window)
            GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
            GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.NONE)
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 72)
            window.set_default_size(self.width, self.height)
            window.set_decorated(False)
            window.set_app_paintable(True)
            window.set_resizable(False)
            window.set_keep_above(True)
            window.set_skip_taskbar_hint(True)
            window.set_skip_pager_hint(True)

            css = Gtk.CssProvider()
            css.load_from_data(
                b"""
                #roger-window {
                  background-color: rgba(17, 24, 39, 0.94);
                  border: 2px solid rgba(147, 197, 253, 0.90);
                  border-radius: 28px;
                }
                #roger-title {
                  color: #93c5fd;
                  font-size: 22px;
                  font-weight: 700;
                }
                #roger-body {
                  color: #f9fafb;
                  font-size: 18px;
                }
                """
            )
            screen = Gdk.Screen.get_default()
            if screen is not None:
                Gtk.StyleContext.add_provider_for_screen(
                    screen,
                    css,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )

            frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            frame.set_name("roger-window")
            frame.set_margin_top(24)
            frame.set_margin_bottom(24)
            frame.set_margin_start(28)
            frame.set_margin_end(28)
            window.add(frame)

            title_label = Gtk.Label(label="Roger")
            title_label.set_name("roger-title")
            title_label.set_xalign(0)
            frame.pack_start(title_label, False, False, 0)

            body_label = Gtk.Label(label="")
            body_label.set_name("roger-body")
            body_label.set_xalign(0)
            body_label.set_yalign(0)
            body_label.set_line_wrap(True)
            body_label.set_max_width_chars(72)
            frame.pack_start(body_label, True, True, 0)

            hide_source = {"id": None}

            def hide():
                window.hide()
                hide_source["id"] = None
                return False

            def set_message(message: OverlayMessage) -> None:
                if hide_source["id"] is not None:
                    GLib.source_remove(hide_source["id"])
                    hide_source["id"] = None
                title_label.set_text(message.title)
                body_label.set_text(message.body)
                window.show_all()
                window.present()
                if message.timeout_ms:
                    hide_source["id"] = GLib.timeout_add(message.timeout_ms, hide)

            def poll():
                try:
                    while True:
                        set_message(self._queue.get_nowait())
                except Empty:
                    pass
                return True

            GLib.timeout_add(100, poll)
            Gtk.main()
        except Exception:
            self._fallback_to_tk()

    def _fallback_to_tk(self) -> None:
        fallback = TkFloatingOverlay(width=self.width, height=self.height)
        try:
            while True:
                fallback.show(**self._queue.get_nowait().__dict__)
        except Empty:
            pass
        self.show = fallback.show  # type: ignore[method-assign]
