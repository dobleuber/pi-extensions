from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


MODULE_PATH = Path("scripts/nanowakeword/generate_configs.py")


def load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_configs", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NanoWakeWordTrainingConfigTests(unittest.TestCase):
    def test_build_config_contains_required_hola_roger_training_sections(self):
        module = load_generator_module()

        config = module.build_config("lstm", pilot=False)

        self.assertEqual(config["model_name"], "hola_roger_lstm")
        self.assertEqual(config["model_type"], "lstm")
        self.assertEqual(config["target_phrase"], "hola roger")
        self.assertEqual(config["output_dir"], "./models/wake/nanowakeword")
        self.assertIs(config["generate_clips"], True)
        self.assertIs(config["transform_clips"], True)
        self.assertIs(config["train_model"], True)

        task_types = {task["text_source"]["type"] for task in config["data_generation_tasks"]}
        self.assertEqual(
            task_types,
            {"fixed_phrase", "auto_adversarial", "phoneme_adversarial", "from_list"},
        )

        manual = next(
            task for task in config["data_generation_tasks"]
            if task["name"] == "manual_nearby_negatives"
        )
        self.assertEqual(
            manual["text_source"]["phrases"],
            ["hola", "roger", "oye roger", "hola rojo", "hola robert", "hola router"],
        )

        variant_task = next(
            task for task in config["data_generation_tasks"]
            if task["name"] == "positive_pronunciation_variants"
        )
        self.assertEqual(
            variant_task["text_source"]["phrases"],
            ["hola roger", "ola roger", "hola royer"],
        )

        self.assertEqual(
            set(config["feature_manifest"]),
            {"targets", "negatives", "targets_val", "negatives_val"},
        )
        self.assertEqual(
            set(config["feature_generation_manifest"]),
            {
                "positive_features",
                "positive_val_features",
                "negative_features",
                "hard_negative_features",
            },
        )
        self.assertIn("batch_composition", config)
        self.assertEqual(
            config["tts_settings"]["models"],
            ["es_ES-sharvard-medium", "es_ES-davefx-medium", "es_MX-ald-medium"],
        )
        self.assertEqual(config["tts_settings"]["models_dir"], "./NwwResourcesModel/tts_models")

    def test_build_config_rejects_architectures_outside_spec_scope(self):
        module = load_generator_module()

        with self.assertRaisesRegex(ValueError, "Unsupported architecture"):
            module.build_config("dnn", pilot=False)

    def test_pilot_config_reduces_training_steps_and_uses_separate_model_name(self):
        module = load_generator_module()

        full = module.build_config("lstm", pilot=False)
        pilot = module.build_config("lstm", pilot=True)

        self.assertEqual(full["model_name"], "hola_roger_lstm")
        self.assertEqual(pilot["model_name"], "hola_roger_lstm_pilot")
        self.assertEqual(pilot["model_type"], full["model_type"])
        self.assertLess(pilot["steps"], full["steps"])
        self.assertLess(pilot["stabilization_steps"], full["stabilization_steps"])
        self.assertLess(
            pilot["data_generation_tasks"][0]["num_samples"],
            full["data_generation_tasks"][0]["num_samples"],
        )

    def test_write_configs_writes_lstm_first_then_gru_and_tcn(self):
        module = load_generator_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = module.write_configs(Path(temp_dir), pilot=False)

            self.assertEqual(
                [path.name for path in paths],
                ["hola_roger_lstm.yaml", "hola_roger_gru.yaml", "hola_roger_tcn.yaml"],
            )
            loaded = yaml.safe_load(paths[0].read_text(encoding="utf-8"))
            self.assertEqual(loaded["model_type"], "lstm")
            self.assertEqual(loaded["target_phrase"], "hola roger")


if __name__ == "__main__":
    unittest.main()
