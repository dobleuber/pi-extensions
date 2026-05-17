#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roger gtk-layer-shell overlay helper")
    parser.add_argument("--width", type=int, default=1100)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--top-margin", type=int, default=72)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import Gdk, GLib, Gtk, GtkLayerShell, Pango

    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    GtkLayerShell.init_for_window(window)
    GtkLayerShell.set_namespace(window, "roger")
    GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.NONE)
    GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, args.top_margin)
    window.set_default_size(args.width, args.height)
    window.set_size_request(args.width, args.height)
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
          background-color: rgba(17, 24, 39, 0.96);
          border: 3px solid rgba(147, 197, 253, 0.95);
          border-radius: 30px;
        }
        #roger-title { color: #93c5fd; }
        #roger-body { color: #f9fafb; }
        """
    )
    screen = Gdk.Screen.get_default()
    if screen is not None:
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    frame.set_name("roger-window")
    frame.set_size_request(args.width, args.height)
    frame.set_margin_top(28)
    frame.set_margin_bottom(28)
    frame.set_margin_start(34)
    frame.set_margin_end(34)
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
    body_label.set_max_width_chars(44)
    frame.pack_start(body_label, True, True, 0)

    hide_source = {"id": None}

    def hide():
        window.hide()
        hide_source["id"] = None
        return False

    def show_message(message: dict) -> None:
        if hide_source["id"] is not None:
            GLib.source_remove(hide_source["id"])
            hide_source["id"] = None
        title_label.set_text(message.get("title", "Roger"))
        body_label.set_text(message.get("body", ""))
        title_label.modify_font(Pango.FontDescription.from_string(message.get("title_font", "Sans Bold 36")))
        body_label.modify_font(Pango.FontDescription.from_string(message.get("body_font", "Sans 34")))
        window.show_all()
        window.present()
        timeout_ms = message.get("timeout_ms")
        if timeout_ms:
            hide_source["id"] = GLib.timeout_add(int(timeout_ms), hide)

    def on_stdin(_source, condition):
        if condition & (GLib.IO_HUP | GLib.IO_ERR):
            Gtk.main_quit()
            return False
        line = sys.stdin.readline()
        if not line:
            Gtk.main_quit()
            return False
        try:
            show_message(json.loads(line))
        except Exception as error:
            print(f"roger overlay helper ignored message: {error}", file=sys.stderr, flush=True)
        return True

    GLib.io_add_watch(sys.stdin, GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR, on_stdin)
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
