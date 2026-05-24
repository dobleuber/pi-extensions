import unittest
from pathlib import Path

from roger.backends.interfaces import AudioSegment, Transcription, WakeDetection
from roger.feedback import ConsoleFeedback
from roger.routing.registry import SessionRegistry
from roger.voice_loop import VoiceLoop


class FakeWake:
    def listen_once(self):
        return WakeDetection("hola roger", 0.95)


class FakeVad:
    def capture_until_silence(self):
        return AudioSegment(pcm16=b"audio", sample_rate=16_000)


class FakeStt:
    def transcribe(self, audio):
        return Transcription("corre los tests", confidence=0.9)


class FakePiRunner:
    def run_task(self, session_name, instruction):
        return "Hecho"


class FakeTts:
    def speak(self, text):
        pass


class VoiceLoopFeedbackTests(unittest.TestCase):
    def test_voice_loop_reports_wake_capture_transcription_and_dispatch(self):
        feedback = ConsoleFeedback()
        loop = VoiceLoop(
            SessionRegistry.default(Path("/tmp/project")),
            FakeWake(),
            FakeVad(),
            FakeStt(),
            FakePiRunner(),
            FakeTts(),
            feedback=feedback,
        )

        loop.run_once()

        output = feedback.output
        self.assertIn("Esperando wake word", output)
        self.assertIn("Wake detectado: hola roger", output)
        self.assertIn("Escuchando instrucción", output)
        self.assertIn("Transcripción: corre los tests", output)
        self.assertIn("Enviando a pi-agent: current-project", output)


if __name__ == "__main__":
    unittest.main()
