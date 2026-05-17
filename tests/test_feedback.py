import unittest

from roger.feedback import ConsoleFeedback


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


if __name__ == "__main__":
    unittest.main()
