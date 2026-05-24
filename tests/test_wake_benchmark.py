import unittest

from roger.benchmarks.wake_benchmark import WakeBenchmarkResult, select_wake_architecture


class WakeBenchmarkTests(unittest.TestCase):
    def test_selects_architecture_with_reliable_detection_then_low_latency(self):
        results = [
            WakeBenchmarkResult("gru", false_positives_per_hour=0.2, false_negative_rate=0.03, p95_latency_ms=180, idle_cpu_percent=2.0, rss_mb=90),
            WakeBenchmarkResult("lstm", false_positives_per_hour=0.1, false_negative_rate=0.01, p95_latency_ms=240, idle_cpu_percent=3.0, rss_mb=120),
            WakeBenchmarkResult("tcn", false_positives_per_hour=0.1, false_negative_rate=0.01, p95_latency_ms=150, idle_cpu_percent=2.5, rss_mb=110),
        ]

        selection = select_wake_architecture(results)

        self.assertEqual(selection.architecture, "tcn")
        self.assertFalse(selection.requires_fallback)
        self.assertIn("tcn", selection.reason)

    def test_requires_fallback_when_no_architecture_meets_thresholds(self):
        results = [
            WakeBenchmarkResult("gru", false_positives_per_hour=2.0, false_negative_rate=0.01, p95_latency_ms=100, idle_cpu_percent=1.0, rss_mb=60),
            WakeBenchmarkResult("lstm", false_positives_per_hour=0.1, false_negative_rate=0.25, p95_latency_ms=100, idle_cpu_percent=1.0, rss_mb=60),
            WakeBenchmarkResult("tcn", false_positives_per_hour=0.1, false_negative_rate=0.01, p95_latency_ms=900, idle_cpu_percent=1.0, rss_mb=60),
        ]

        selection = select_wake_architecture(results)

        self.assertTrue(selection.requires_fallback)
        self.assertIsNone(selection.architecture)
        self.assertIn("No NanoWakeWord architecture", selection.reason)


if __name__ == "__main__":
    unittest.main()
