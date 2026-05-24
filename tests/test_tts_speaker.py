import unittest

from roger.backends.interfaces import SynthesizedSpeech
import numpy as np

from roger.tts_speaker import NoopSpeaker, SafeSpeaker, SynthesizingSpeaker, SystemAudioPlayer


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

    def test_safe_speaker_reports_synthesis_failure_without_raising(self):
        class FailingSpeaker:
            def speak(self, text):
                raise RuntimeError("kokoro unavailable")

        speaker = SafeSpeaker(FailingSpeaker())

        result = speaker.speak("Hola")

        self.assertFalse(result.success)
        self.assertIn("kokoro unavailable", result.error)
        self.assertEqual(speaker.failures, 1)

    def test_safe_speaker_reports_playback_failure_without_raising(self):
        backend = FakeTtsBackend()
        speaker = SafeSpeaker(
            SynthesizingSpeaker(
                backend,
                audio_player=lambda speech: (_ for _ in ()).throw(RuntimeError("pipewire unavailable")),
            )
        )

        result = speaker.speak("Hola")

        self.assertFalse(result.success)
        self.assertIn("pipewire unavailable", result.error)
        self.assertEqual(backend.texts, ["Hola"])

    def test_safe_speaker_reports_success(self):
        backend = FakeTtsBackend()
        speaker = SafeSpeaker(SynthesizingSpeaker(backend, audio_player=lambda speech: None))

        result = speaker.speak("Hola")

        self.assertTrue(result.success)
        self.assertEqual(result.text, "Hola")

    def test_safe_speaker_rate_limits_failure_warnings(self):
        class FailingSpeaker:
            def speak(self, text):
                raise RuntimeError("kokoro unavailable")

        warnings = []
        speaker = SafeSpeaker(FailingSpeaker(), warning_callback=warnings.append, repeat_warning_interval=3)

        for _ in range(5):
            speaker.speak("Hola")

        self.assertEqual(len(warnings), 2)
        self.assertIn("Speech output degraded", warnings[0])
        self.assertIn("kokoro unavailable", warnings[0])

    def test_system_audio_player_prefers_pipewire_pw_play_when_available(self):
        calls = []
        speech = SynthesizedSpeech(
            audio=np.array([0.0, 0.5, -0.5], dtype=np.float32).tobytes(),
            sample_rate=24_000,
        )
        player = SystemAudioPlayer(
            command_exists=lambda command: command == "pw-play",
            run_command=lambda command: calls.append(command),
        )

        player.play(speech)

        self.assertEqual(calls[0][0], "pw-play")
        self.assertTrue(calls[0][1].endswith(".wav"))

    def test_system_audio_player_falls_back_to_sounddevice(self):
        played = []
        waited = []
        speech = SynthesizedSpeech(
            audio=np.array([0.0, 0.5], dtype=np.float32).tobytes(),
            sample_rate=24_000,
        )
        player = SystemAudioPlayer(
            command_exists=lambda command: False,
            sounddevice_module=type("SD", (), {
                "play": staticmethod(lambda audio, samplerate: played.append((len(audio), samplerate))),
                "wait": staticmethod(lambda: waited.append(True)),
            }),
        )

        player.play(speech)

        self.assertEqual(played, [(2, 24_000)])
        self.assertEqual(waited, [True])


if __name__ == "__main__":
    unittest.main()
