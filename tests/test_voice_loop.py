import unittest
from pathlib import Path

from roger.backends.interfaces import AudioSegment, Transcription, WakeDetection
from roger.routing.registry import SessionRegistry
from roger.voice_loop import VoiceLoop, VoiceLoopState


class FakeWake:
    def __init__(self, detection=None):
        self.detection = detection
        self.calls = 0

    def listen_once(self):
        self.calls += 1
        return self.detection


class FakeVad:
    def __init__(self):
        self.calls = 0

    def capture_until_silence(self):
        self.calls += 1
        return AudioSegment(pcm16=b"audio", sample_rate=16_000)


class FakeStt:
    def __init__(self, text="corre los tests"):
        self.text = text
        self.calls = 0

    def transcribe(self, audio):
        self.calls += 1
        return Transcription(text=self.text, confidence=0.9)


class FakePiRunner:
    def __init__(self):
        self.calls = []

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        return "Listo"


class FakeTts:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class VoiceLoopTests(unittest.TestCase):
    def test_no_wake_detection_keeps_listening_without_capture(self):
        wake = FakeWake(detection=None)
        vad = FakeVad()
        stt = FakeStt()
        pi = FakePiRunner()
        tts = FakeTts()
        loop = VoiceLoop(SessionRegistry.default(Path("/tmp/project")), wake, vad, stt, pi, tts)

        result = loop.run_once()

        self.assertEqual(result.state, VoiceLoopState.LISTENING)
        self.assertFalse(result.dispatched)
        self.assertEqual(vad.calls, 0)
        self.assertEqual(stt.calls, 0)
        self.assertEqual(pi.calls, [])

    def test_wake_capture_transcribe_preview_dispatch_tts_then_return_to_listening(self):
        wake = FakeWake(WakeDetection("hola roger", 0.99))
        vad = FakeVad()
        stt = FakeStt("corre los tests")
        pi = FakePiRunner()
        tts = FakeTts()
        loop = VoiceLoop(SessionRegistry.default(Path("/tmp/project")), wake, vad, stt, pi, tts)

        result = loop.run_once()

        self.assertEqual(result.state, VoiceLoopState.LISTENING)
        self.assertTrue(result.dispatched)
        self.assertEqual(vad.calls, 1)
        self.assertEqual(stt.calls, 1)
        self.assertEqual(pi.calls, [("current-project", "corre los tests")])
        self.assertEqual(tts.spoken, ["Listo"])

    def test_cancelled_preview_returns_to_listening_without_dispatch(self):
        loop = VoiceLoop(
            SessionRegistry.default(Path("/tmp/project")),
            FakeWake(WakeDetection("hola roger", 0.99)),
            FakeVad(),
            FakeStt("instala steam"),
            FakePiRunner(),
            FakeTts(),
            preview_action="cancel",
        )

        result = loop.run_once()

        self.assertEqual(result.state, VoiceLoopState.LISTENING)
        self.assertFalse(result.dispatched)
        self.assertEqual(result.status, "cancelled")


if __name__ == "__main__":
    unittest.main()
