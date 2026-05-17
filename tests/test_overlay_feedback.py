import unittest

from roger.overlay import GtkLayerShellFloatingOverlay, OverlayFeedback


class FakeOverlay:
    def __init__(self):
        self.calls = []

    def show(self, title, body, state="active", timeout_ms=None):
        self.calls.append({
            "title": title,
            "body": body,
            "state": state,
            "timeout_ms": timeout_ms,
        })


class OverlayFeedbackTests(unittest.TestCase):
    def test_overlay_feedback_defaults_to_wayland_layer_shell_overlay(self):
        feedback = OverlayFeedback()

        self.assertIsInstance(feedback.overlay, GtkLayerShellFloatingOverlay)

    def test_layer_shell_overlay_has_large_default_size(self):
        overlay = GtkLayerShellFloatingOverlay()

        self.assertGreaterEqual(overlay.width, 900)
        self.assertGreaterEqual(overlay.height, 260)

    def test_layer_shell_overlay_uses_readable_font_sizes(self):
        overlay = GtkLayerShellFloatingOverlay()

        self.assertGreaterEqual(overlay.title_font_px, 34)
        self.assertGreaterEqual(overlay.body_font_px, 32)

    def test_layer_shell_overlay_uses_pango_font_descriptions(self):
        overlay = GtkLayerShellFloatingOverlay()

        self.assertEqual(overlay.title_font_description, "Sans Bold 36")
        self.assertEqual(overlay.body_font_description, "Sans 34")

    def test_overlay_feedback_shows_siri_like_phases(self):
        overlay = FakeOverlay()
        feedback = OverlayFeedback(overlay)

        feedback.wake_detected("hola roger", 0.92)
        feedback.capturing_instruction()
        feedback.transcription_ready("corre pwd")
        feedback.dispatching("current-project")
        feedback.completed("complete", "Listo")

        self.assertEqual(overlay.calls[0]["title"], "Roger activo")
        self.assertIn("Te escucho", overlay.calls[0]["body"])
        self.assertEqual(overlay.calls[1]["title"], "Transcripción")
        self.assertIn("corre pwd", overlay.calls[1]["body"])
        self.assertEqual(overlay.calls[2]["title"], "Ejecutando")
        self.assertIn("corre pwd", overlay.calls[2]["body"])
        self.assertIn("current-project", overlay.calls[2]["body"])
        self.assertEqual(overlay.calls[3]["title"], "Resultado")
        self.assertIn("corre pwd", overlay.calls[3]["body"])
        self.assertIn("Listo", overlay.calls[3]["body"])


if __name__ == "__main__":
    unittest.main()
