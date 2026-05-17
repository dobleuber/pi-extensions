from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path("scripts/nanowakeword/record_real_samples.py")


def load_module():
    spec = importlib.util.spec_from_file_location("record_real_samples", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordRealSamplesTests(unittest.TestCase):
    def test_output_dir_for_positive_samples(self):
        module = load_module()

        path = module.output_dir_for("positive")

        self.assertEqual(path, Path("benchmarks/data/wake/hola_roger/real_positive"))

    def test_output_dir_for_negative_samples(self):
        module = load_module()

        path = module.output_dir_for("negative")

        self.assertEqual(path, Path("benchmarks/data/wake/hola_roger/real_negative"))

    def test_sample_filename_uses_kind_and_zero_padded_index(self):
        module = load_module()

        self.assertEqual(module.sample_filename("positive", 7), "hola_roger_007.wav")
        self.assertEqual(module.sample_filename("negative", 7), "negative_007.wav")

    def test_negative_prompts_do_not_include_target_homophones(self):
        module = load_module()

        self.assertNotIn("hola royer", module.NEGATIVE_PROMPTS)
        self.assertNotIn("ola roger", module.NEGATIVE_PROMPTS)
        self.assertNotIn("hola roger", module.NEGATIVE_PROMPTS)

    def test_default_arguments_record_positive_samples(self):
        module = load_module()

        args = module.parse_args([])

        self.assertEqual(args.kind, "positive")
        self.assertEqual(args.count, 50)
        self.assertEqual(args.seconds, 2.0)
        self.assertEqual(args.target, "bluez_input.A0:0C:E2:46:9A:98")

    def test_prompt_for_positive_tells_user_to_say_wake_phrase(self):
        module = load_module()

        self.assertEqual(module.prompt_for("positive", 1), "Di: hola roger")


if __name__ == "__main__":
    unittest.main()
