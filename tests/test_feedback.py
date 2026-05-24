import unittest

from roger.feedback import CompositeFeedback, ConsoleFeedback


class FeedbackTests(unittest.TestCase):
    def test_console_feedback_records_status_lines(self):
        feedback = ConsoleFeedback()

        feedback.listening_for_wake(manual=True)
        feedback.wake_detected("hola roger", 0.91)
        feedback.capturing_instruction()
        feedback.transcription_ready("corre pwd")
        feedback.dispatching("current-project")

        output = feedback.output
        self.assertIn("Manual wake activado", output)
        self.assertIn("Wake detectado: hola roger", output)
        self.assertIn("Escuchando instrucción", output)
        self.assertIn("Transcripción: corre pwd", output)
        self.assertIn("Enviando a pi-agent: current-project", output)

    def test_composite_feedback_forwards_events_to_all_sinks(self):
        first = ConsoleFeedback()
        second = ConsoleFeedback()
        feedback = CompositeFeedback([first, second])

        feedback.wake_detected("hola roger", 0.9)

        self.assertIn("Wake detectado", first.output)
        self.assertIn("Wake detectado", second.output)


if __name__ == "__main__":
    unittest.main()
