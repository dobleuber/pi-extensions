from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ARCHITECTURES = ("gru", "lstm", "tcn")
MANUAL_NEGATIVES = (
    "hola",
    "roger",
    "oye roger",
    "hola rojo",
    "hola royer",
    "ola roger",
)


def normalize_phrase(phrase: str) -> str:
    return " ".join(phrase.lower().strip().split())


def slugify_phrase(phrase: str) -> str:
    return normalize_phrase(phrase).replace(" ", "_")


def build_training_plan(target_phrase: str) -> list[dict[str, str]]:
    normalized = normalize_phrase(target_phrase)
    slug = slugify_phrase(normalized)
    return [
        {
            "model_type": architecture,
            "model_name": f"{slug}_{architecture}",
            "config_path": f"configs/nanowakeword/{slug}_{architecture}.json",
        }
        for architecture in ARCHITECTURES
    ]


def build_training_config(target_phrase: str, architecture: str) -> dict[str, Any]:
    normalized = normalize_phrase(target_phrase)
    architecture = architecture.lower().strip()
    if architecture not in ARCHITECTURES:
        raise ValueError(f"Unsupported NanoWakeWord architecture: {architecture}")

    slug = slugify_phrase(normalized)
    return {
        "model_name": f"{slug}_{architecture}",
        "output_dir": "./models/wake/nanowakeword",
        "positive_data_path": f"./benchmarks/data/wake/{slug}/positive",
        "negative_data_path": f"./benchmarks/data/wake/{slug}/negative",
        "background_paths": [f"./benchmarks/data/wake/{slug}/background_noise"],
        "rir_paths": [],
        "model_type": architecture,
        "target_phrase": normalized,
        "data_generation_tasks": [
            {
                "name": "positive_train",
                "enabled": True,
                "output_dir": f"benchmarks/data/wake/{slug}/positive",
                "num_samples": 2500,
                "file_prefix": "pos",
                "text_source": {"type": "fixed_phrase", "phrase": normalized},
            },
            {
                "name": "positive_validation",
                "enabled": True,
                "output_dir": f"benchmarks/data/wake/{slug}/positive_val",
                "num_samples": 2000,
                "file_prefix": "pos_val",
                "text_source": {"type": "fixed_phrase", "phrase": normalized},
            },
            {
                "name": "automatic_adversarial_negatives",
                "enabled": True,
                "output_dir": f"benchmarks/data/wake/{slug}/negative",
                "num_samples": 5000,
                "file_prefix": "neg_auto",
                "text_source": {
                    "type": "auto_adversarial",
                    "base_phrase": normalized,
                    "include_input_words": True,
                    "include_partial_phrase": True,
                    "multi_word_prob": 0.5,
                    "max_multi_word_len": 3,
                },
            },
            {
                "name": "phoneme_hard_negatives",
                "enabled": True,
                "output_dir": f"benchmarks/data/wake/{slug}/negative_phoneme",
                "num_samples": 3000,
                "file_prefix": "neg_ph",
                "text_source": {
                    "type": "phoneme_adversarial",
                    "base_phrase": normalized,
                    "min_distance": 0.3,
                },
            },
            {
                "name": "manual_nearby_negatives",
                "enabled": True,
                "output_dir": f"benchmarks/data/wake/{slug}/negative",
                "num_samples": len(MANUAL_NEGATIVES) * 10,
                "file_prefix": "neg_manual",
                "text_source": {
                    "type": "from_list",
                    "phrases": list(MANUAL_NEGATIVES),
                    "repeat_each": 10,
                },
            },
        ],
        "augmentation_settings": {
            "gain_prob": 1.0,
            "min_gain_in_db": -2.0,
            "max_gain_in_db": 2.0,
            "pitch_prob": 0.3,
            "min_pitch_semitones": -1.0,
            "max_pitch_semitones": 1.0,
            "min_snr_in_db": 15.0,
            "max_snr_in_db": 35.0,
            "rir_prob": 0.0,
        },
        "benchmark_metrics": [
            "false_positives",
            "false_negatives",
            "activation_latency_ms",
            "idle_cpu_percent",
            "rss_mb",
            "training_duration_seconds",
        ],
    }


def write_training_configs(target_phrase: str, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for item in build_training_plan(target_phrase):
        config = build_training_config(target_phrase, item["model_type"])
        path = output_dir / Path(item["config_path"]).name
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths.append(path)
    return paths
