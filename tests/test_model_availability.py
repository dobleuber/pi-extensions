import unittest
from urllib.error import URLError

from roger.pi_rpc.availability import (
    ModelAvailabilityPolicy,
    ModelAvailabilityMode,
    is_provider_availability_error,
    probe_llama_cpp_fallback,
)


class ModelAvailabilityPolicyTests(unittest.TestCase):
    def test_explicit_offline_uses_fallback_without_online_probe(self):
        calls = []
        policy = ModelAvailabilityPolicy(
            explicit_offline=True,
            online_probe=lambda: calls.append("online") or True,
        )

        decision = policy.decide()

        self.assertEqual(decision.mode, ModelAvailabilityMode.OFFLINE_FALLBACK)
        self.assertEqual(calls, [])
        self.assertIn("explicit offline", decision.reason)

    def test_available_online_provider_uses_pi_default(self):
        policy = ModelAvailabilityPolicy(online_probe=lambda: True)

        decision = policy.decide()

        self.assertEqual(decision.mode, ModelAvailabilityMode.ONLINE)

    def test_unavailable_online_provider_uses_fallback_when_enabled(self):
        policy = ModelAvailabilityPolicy(online_probe=lambda: False)

        decision = policy.decide()

        self.assertEqual(decision.mode, ModelAvailabilityMode.OFFLINE_FALLBACK)
        self.assertIn("online unavailable", decision.reason)

    def test_disabled_fallback_reports_unavailable_for_explicit_offline(self):
        policy = ModelAvailabilityPolicy(explicit_offline=True, fallback_enabled=False)

        decision = policy.decide()

        self.assertEqual(decision.mode, ModelAvailabilityMode.UNAVAILABLE)
        self.assertIn("fallback disabled", decision.reason)

    def test_disabled_automatic_fallback_skips_probe_and_uses_online(self):
        calls = []
        policy = ModelAvailabilityPolicy(
            automatic_fallback=False,
            online_probe=lambda: calls.append("online") or False,
        )

        decision = policy.decide()

        self.assertEqual(decision.mode, ModelAvailabilityMode.ONLINE)
        self.assertEqual(calls, [])

    def test_recognizes_online_provider_availability_errors(self):
        self.assertTrue(is_provider_availability_error(RuntimeError("network timeout while contacting provider")))
        self.assertTrue(is_provider_availability_error(RuntimeError("provider unavailable: authentication failed")))
        self.assertFalse(is_provider_availability_error(RuntimeError("tool command failed")))

    def test_llama_cpp_probe_accepts_served_gguf_name_matching_configured_alias(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"data":[{"id":"gemma4-latest-Q4_K_M.gguf"}]}'

        error = probe_llama_cpp_fallback(
            "http://127.0.0.1:11434/v1",
            "gemma4",
            urlopen_fn=lambda url, timeout: Response(),
        )

        self.assertIsNone(error)

    def test_llama_cpp_probe_reports_missing_model(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"data":[{"id":"other-model"}]}'

        error = probe_llama_cpp_fallback(
            "http://127.0.0.1:11434/v1",
            "gemma4",
            urlopen_fn=lambda url, timeout: Response(),
        )

        self.assertEqual(error, "llama.cpp fallback model not found: gemma4")

    def test_llama_cpp_probe_reports_server_unavailable(self):
        error = probe_llama_cpp_fallback(
            "http://127.0.0.1:11434/v1",
            "gemma4",
            urlopen_fn=lambda url, timeout: (_ for _ in ()).throw(URLError("connection refused")),
        )

        self.assertIn("llama.cpp server unavailable", error)


if __name__ == "__main__":
    unittest.main()
