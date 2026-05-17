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
        self.assertEqual(overlay.calls[1]["title"], "Escuchando")
        self.assertEqual(overlay.calls[2]["title"], "Transcripción")
        self.assertIn("corre pwd", overlay.calls[2]["body"])
        self.assertEqual(overlay.calls[3]["title"], "Ejecutando")
        self.assertIn("current-project", overlay.calls[3]["body"])
        self.assertEqual(overlay.calls[4]["title"], "Resultado")
        self.assertIn("Listo", overlay.calls[4]["body"])


if __name__ == "__main__":
    unittest.main()
