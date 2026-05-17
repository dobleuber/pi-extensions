import unittest

from roger import cli


class FakeSpeaker:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class CliSayTests(unittest.TestCase):
    def test_say_command_speaks_text_for_audio_smoke_testing(self):
        speaker = FakeSpeaker()

        exit_code, output = cli.run(
            ["say", "Hola Roger"],
            dependencies=cli.RuntimeDependencies(
                create_tts_speaker=lambda config, no_tts=False: speaker,
            ),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(speaker.spoken, ["Hola Roger"])
        self.assertIn("spoken: yes", output)


if __name__ == "__main__":
    unittest.main()
