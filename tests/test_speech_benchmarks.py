import unittest

from roger.benchmarks.speech import (
    build_stt_plan,
    build_tts_plan,
    build_vad_plan,
    default_stt_backend,
    default_tts_backend,
    default_vad_backend,
)


class SpeechBenchmarkPlanTests(unittest.TestCase):
    def test_vad_plan_compares_silero_and_webrtc_with_endpoint_metrics(self):
        plan = build_vad_plan()

        self.assertEqual([candidate["backend"] for candidate in plan["candidates"]], ["silero", "webrtc"])
        self.assertIn("clipped_start_rate", plan["metrics"])
        self.assertIn("end_latency_p95_ms", plan["metrics"])
        self.assertEqual(default_vad_backend(), "silero")

    def test_stt_plan_compares_faster_whisper_and_whisper_cpp_for_spanish(self):
        plan = build_stt_plan()

        self.assertEqual([candidate["backend"] for candidate in plan["candidates"]], ["faster-whisper", "whisper.cpp"])
        self.assertEqual(plan["language"], "es")
        self.assertIn("intent_accuracy", plan["metrics"])
        self.assertIn("real_time_factor", plan["metrics"])
        self.assertEqual(default_stt_backend(), "faster-whisper")

    def test_tts_plan_compares_kokoro_and_piper_for_spanish(self):
        plan = build_tts_plan()

        self.assertEqual([candidate["backend"] for candidate in plan["candidates"]], ["kokoro", "piper"])
        self.assertEqual(plan["language"], "es")
        self.assertIn("voice_quality_score", plan["metrics"])
        self.assertIn("license_verified", plan["metrics"])
        self.assertEqual(default_tts_backend(), "kokoro")


if __name__ == "__main__":
    unittest.main()
