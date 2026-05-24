import unittest

from roger.feedback_system import DesktopNotifier, SystemFeedback


class SystemFeedbackTests(unittest.TestCase):
    def test_desktop_notifier_sends_notify_send_when_enabled(self):
        calls = []
        notifier = DesktopNotifier(run_command=lambda command: calls.append(command))

        notifier.notify("Roger", "Wake detectado")

        self.assertEqual(calls, [["notify-send", "Roger", "Wake detectado"]])

    def test_desktop_notifier_ignores_missing_notify_send(self):
        def missing(command):
            raise FileNotFoundError("notify-send")

        notifier = DesktopNotifier(run_command=missing)

        notifier.notify("Roger", "Wake detectado")

    def test_system_feedback_emits_desktop_notifications_for_key_phases(self):
        messages = []
        feedback = SystemFeedback(notifier=DesktopNotifier(run_command=lambda command: messages.append(command)))

        feedback.wake_detected("hola roger", 0.91)
        feedback.transcription_ready("corre los tests")
        feedback.dispatching("current-project")
        feedback.completed("complete", "Listo")

        bodies = [command[2] for command in messages]
        self.assertIn("Wake detectado: hola roger", bodies)
        self.assertIn("Transcripción: corre los tests", bodies)
        self.assertIn("Enviando a pi-agent: current-project", bodies)
        self.assertIn("Resultado: complete", bodies)


if __name__ == "__main__":
    unittest.main()
