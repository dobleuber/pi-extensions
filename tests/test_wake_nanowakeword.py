import unittest

from roger.benchmarks.wake_nanowakeword import (
    ARCHITECTURES,
    build_training_config,
    build_training_plan,
)


class NanoWakeWordConfigTests(unittest.TestCase):
    def test_training_plan_is_limited_to_gru_lstm_tcn(self):
        plan = build_training_plan("hola roger")

        self.assertEqual(ARCHITECTURES, ("gru", "lstm", "tcn"))
        self.assertEqual([item["model_type"] for item in plan], ["gru", "lstm", "tcn"])
        self.assertEqual([item["model_name"] for item in plan], [
            "hola_roger_gru",
            "hola_roger_lstm",
            "hola_roger_tcn",
        ])

    def test_training_config_uses_target_phrase_fixed_positives_and_negatives(self):
        config = build_training_config("hola roger", "gru")

        self.assertEqual(config["target_phrase"], "hola roger")
        self.assertEqual(config["model_type"], "gru")
        tasks = config["data_generation_tasks"]

        positive_tasks = [task for task in tasks if task["text_source"]["type"] == "fixed_phrase"]
        self.assertGreaterEqual(len(positive_tasks), 2)
        self.assertTrue(all(task["text_source"]["phrase"] == "hola roger" for task in positive_tasks))

        text_source_types = {task["text_source"]["type"] for task in tasks}
        self.assertIn("auto_adversarial", text_source_types)
        self.assertIn("phoneme_adversarial", text_source_types)
        self.assertIn("from_list", text_source_types)

        manual_negatives = next(task for task in tasks if task["text_source"]["type"] == "from_list")
        self.assertIn("hola", manual_negatives["text_source"]["phrases"])
        self.assertIn("roger", manual_negatives["text_source"]["phrases"])
        self.assertIn("ola roger", manual_negatives["text_source"]["phrases"])

    def test_invalid_architecture_is_rejected(self):
        with self.assertRaises(ValueError):
            build_training_config("hola roger", "cnn")


if __name__ == "__main__":
    unittest.main()
