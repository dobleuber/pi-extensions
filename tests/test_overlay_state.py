import unittest

from roger.overlay import StatefulOverlayFeedback


class FakeOverlay:
    def __init__(self):
        self.calls = []

    def show(self, title, body, state="active", timeout_ms=None):
        self.calls.append({"title": title, "body": body, "state": state, "timeout_ms": timeout_ms})


class StatefulOverlayFeedbackTests(unittest.TestCase):
    def test_transcript_stays_visible_while_dispatching_and_in_result(self):
        overlay = FakeOverlay()
        feedback = StatefulOverlayFeedback(overlay)

        feedback.wake_detected("hola roger", 0.95)
        feedback.capturing_instruction()
        feedback.transcription_ready("corre pwd")
        feedback.dispatching("current-project")
        feedback.completed("complete", "El directorio actual es /tmp/project")

        dispatch_body = overlay.calls[-2]["body"]
        result_body = overlay.calls[-1]["body"]
        self.assertIn("corre pwd", dispatch_body)
        self.assertIn("corre pwd", result_body)
        self.assertIn("El directorio actual", result_body)

    def test_listening_state_is_not_replaced_by_duplicate_capture_message(self):
        overlay = FakeOverlay()
        feedback = StatefulOverlayFeedback(overlay)

        feedback.wake_detected("hola roger", 0.95)
        feedback.capturing_instruction()

        self.assertEqual(len(overlay.calls), 1)
        self.assertEqual(overlay.calls[0]["title"], "Roger activo")
        self.assertIn("Te escucho", overlay.calls[0]["body"])


if __name__ == "__main__":
    unittest.main()
