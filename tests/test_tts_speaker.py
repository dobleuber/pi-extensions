import unittest

from roger.backends.interfaces import SynthesizedSpeech
from roger.tts_speaker import NoopSpeaker, SynthesizingSpeaker


class FakeTtsBackend:
    def __init__(self):
        self.texts = []

    def synthesize(self, text):
        self.texts.append(text)
        return SynthesizedSpeech(audio=b"audio", sample_rate=24_000)


class TtsSpeakerTests(unittest.TestCase):
    def test_noop_speaker_records_text_without_synthesizing(self):
        speaker = NoopSpeaker()

        speaker.speak("Hola")

        self.assertEqual(speaker.spoken, ["Hola"])

    def test_synthesizing_speaker_calls_backend(self):
        backend = FakeTtsBackend()
        speaker = SynthesizingSpeaker(backend, audio_player=lambda speech: None)

        speaker.speak("Hola")

        self.assertEqual(backend.texts, ["Hola"])
        self.assertEqual(speaker.last_speech.audio, b"audio")

    def test_synthesizing_speaker_plays_generated_audio_when_player_is_available(self):
        backend = FakeTtsBackend()
        played = []

        def player(speech):
            played.append((speech.audio, speech.sample_rate))

        speaker = SynthesizingSpeaker(backend, audio_player=player)

        speaker.speak("Hola")

        self.assertEqual(played, [(b"audio", 24_000)])


if __name__ == "__main__":
    unittest.main()
