import unittest

from roger.dialogue import DialogueControl, DialogueDecision


class DialogueControlTests(unittest.TestCase):
    def test_detects_thanks_roger_as_goodbye(self):
        control = DialogueControl()

        for text in ["gracias roger", "gracias, Roger", "muchas gracias roger", "ok gracias roger"]:
            with self.subTest(text=text):
                decision = control.decide(text)
                self.assertEqual(decision, DialogueDecision.GOODBYE)

    def test_non_goodbye_continues(self):
        control = DialogueControl()

        self.assertEqual(control.decide("dame la hora en colombia"), DialogueDecision.CONTINUE)


if __name__ == "__main__":
    unittest.main()
