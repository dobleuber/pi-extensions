from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path("scripts/nanowakeword/listen_hola_roger.py")


def load_listener_module():
    spec = importlib.util.spec_from_file_location("listen_hola_roger", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NanoWakeWordLiveListenerTests(unittest.TestCase):
    def test_default_arguments_target_lstm_model(self):
        module = load_listener_module()

        args = module.parse_args([])

        self.assertEqual(
            args.model,
            "models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx",
        )
        self.assertEqual(args.threshold, 0.85)
        self.assertEqual(args.cooldown, 1.5)
        self.assertEqual(args.min_print_score, 0.2)

    def test_should_detect_respects_threshold_and_cooldown(self):
        module = load_listener_module()

        self.assertFalse(module.should_detect(score=0.84, threshold=0.85, now=10.0, last_detection=0.0, cooldown=1.5))
        self.assertFalse(module.should_detect(score=0.90, threshold=0.85, now=10.0, last_detection=9.0, cooldown=1.5))
        self.assertTrue(module.should_detect(score=0.90, threshold=0.85, now=10.0, last_detection=8.0, cooldown=1.5))

    def test_should_print_score_uses_minimum_score(self):
        module = load_listener_module()

        self.assertFalse(module.should_print_score(0.19, 0.2))
        self.assertTrue(module.should_print_score(0.2, 0.2))
        self.assertTrue(module.should_print_score(0.95, 0.2))


if __name__ == "__main__":
    unittest.main()
