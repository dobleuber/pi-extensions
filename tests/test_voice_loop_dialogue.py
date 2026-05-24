import unittest
from pathlib import Path

from roger.backends.interfaces import AudioSegment, Transcription, WakeDetection
from roger.dialogue import DialogueControl
from roger.routing.registry import SessionRegistry
from roger.voice_loop import VoiceLoop


class Wake:
    def listen_once(self):
        return WakeDetection("hola roger", 1.0)


class Vad:
    def capture_until_silence(self):
        return AudioSegment(pcm16=b"audio")


class Stt:
    def transcribe(self, audio):
        return Transcription("gracias Roger")


class Pi:
    def __init__(self):
        self.calls = []

    def run_task(self, session_name, instruction):
        self.calls.append((session_name, instruction))
        return "no deberia ejecutar"


class Tts:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class Feedback:
    def __init__(self):
        self.completed_calls = []
        self.transcriptions = []

    def listening_for_wake(self, manual=False): pass
    def wake_detected(self, phrase, score): pass
    def capturing_instruction(self): pass
    def transcribing(self): pass
    def transcription_ready(self, text): self.transcriptions.append(text)
    def dispatching(self, session_name): pass
    def completed(self, status, message=""): self.completed_calls.append((status, message))


class VoiceLoopDialogueTests(unittest.TestCase):
    def test_gracias_roger_speaks_goodbye_and_does_not_dispatch(self):
        pi = Pi()
        tts = Tts()
        feedback = Feedback()
        loop = VoiceLoop(
            SessionRegistry.default(Path("/tmp/project")),
            Wake(),
            Vad(),
            Stt(),
            pi,
            tts,
            feedback=feedback,
            dialogue_control=DialogueControl(),
        )

        result = loop.run_once()

        self.assertEqual(result.status, "goodbye")
        self.assertFalse(result.dispatched)
        self.assertEqual(pi.calls, [])
        self.assertEqual(tts.spoken, ["Hasta luego."])
        self.assertEqual(feedback.transcriptions, ["gracias Roger"])
        self.assertEqual(feedback.completed_calls, [("goodbye", "Hasta luego.")])


if __name__ == "__main__":
    unittest.main()
