import unittest
from pathlib import Path

from roger.backends.interfaces import AudioSegment, Transcription, WakeDetection
from roger.pi_rpc.runner import CancellationResult
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
        self.cancel_calls = []

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        return "Listo"

    def cancel_active(self, session_name=None, command="abort"):
        self.cancel_calls.append((session_name, command))
        return CancellationResult("cancel_requested", True, "Cancelación solicitada", session_name=session_name, command=command)


class FakeTts:
    def __init__(self, fail=False):
        self.spoken = []
        self.fail = fail

    def speak(self, text):
        self.spoken.append(text)
        if self.fail:
            raise RuntimeError("tts failed")


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

    def test_goodbye_keeps_result_when_tts_fails(self):
        loop = VoiceLoop(
            SessionRegistry.default(Path("/tmp/project")),
            FakeWake(WakeDetection("hola roger", 0.99)),
            FakeVad(),
            FakeStt("gracias Roger"),
            FakePiRunner(),
            FakeTts(fail=True),
        )

        result = loop.run_once()

        self.assertEqual(result.status, "goodbye")
        self.assertFalse(result.dispatched)
        self.assertEqual(result.message, "Hasta luego.")

    def test_stop_phrase_attempts_cancellation_instead_of_routing(self):
        pi = FakePiRunner()
        loop = VoiceLoop(
            SessionRegistry.default(Path("/tmp/project")),
            FakeWake(WakeDetection("hola roger", 0.99)),
            FakeVad(),
            FakeStt("para Roger"),
            pi,
            FakeTts(),
        )

        result = loop.run_once()

        self.assertEqual(result.status, "cancel_requested")
        self.assertFalse(result.dispatched)
        self.assertEqual(pi.calls, [])
        self.assertEqual(pi.cancel_calls, [(None, "abort")])


if __name__ == "__main__":
    unittest.main()
