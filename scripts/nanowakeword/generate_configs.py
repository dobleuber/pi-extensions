#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

TARGET_PHRASE = "hola roger"
ARCHITECTURES = ("lstm", "gru", "tcn")
POSITIVE_VARIANTS = [
    "hola roger",
    "ola roger",
    "hola royer",
]

MANUAL_NEGATIVES = [
    "hola",
    "roger",
    "oye roger",
    "hola rojo",
    "hola robert",
    "hola router",
]

FULL_STEPS = 50_000
FULL_STABILIZATION_STEPS = 20_000
PILOT_STEPS = 3_000
PILOT_STABILIZATION_STEPS = 1_000


def sample_count(full: int, pilot: bool) -> int:
    if not pilot:
        return full
    return max(10, full // 10)


def build_config(architecture: str, pilot: bool = False) -> dict[str, Any]:
    architecture = architecture.lower().strip()
    if architecture not in ARCHITECTURES:
        raise ValueError(
            f"Unsupported architecture: {architecture}. "
            f"Expected one of: {', '.join(ARCHITECTURES)}"
        )

    model_name = f"hola_roger_{architecture}"
    if pilot:
        model_name = f"{model_name}_pilot"
    steps = PILOT_STEPS if pilot else FULL_STEPS
    stabilization_steps = PILOT_STABILIZATION_STEPS if pilot else FULL_STABILIZATION_STEPS

    return {
        "model_name": model_name,
        "output_dir": "./models/wake/nanowakeword",
        "positive_data_path": "./benchmarks/data/wake/hola_roger/positive",
        "negative_data_path": "./benchmarks/data/wake/hola_roger/negative",
        "background_paths": ["./benchmarks/data/wake/hola_roger/background_noise"],
        "rir_paths": [],
        "model_type": architecture,
        "tts_settings": {
            "models": [
                "es_ES-sharvard-medium",
                "es_ES-davefx-medium",
                "es_MX-ald-medium",
            ],
            "models_dir": "./NwwResourcesModel/tts_models",
            "length_scales": [0.9, 1.0, 1.1],
            "noise_scales": [0.5, 0.667, 0.8],
            "noise_w_scales": [0.6, 0.8, 1.0],
        },
        "layer_size": 32,
        "n_blocks": 3,
        "embedding_dim": 128,
        "dropout_prob": 0.3,
        "activation_function": "relu",
        "margin_pos": 2.0,
        "margin_neg": -2.0,
        "LOSS_BIAS": 0.65,
        "logit_reg_weight": 0.0005,
        "logit_reg_margin": 4.0,
        "logit_min_margin": 1.5,
        "steps": steps,
        "stabilization_steps": stabilization_steps,
        "optimizer_type": "adamw",
        "learning_rate_max": 0.0008,
        "lr_scheduler_type": "onecycle",
        "weight_decay": 0.01,
        "momentum": 0.9,
        "num_workers": 0,
        "batch_composition": {
            "t": 100,
            "n": 100,
            "b": 90,
            "hn": 20,
            "AE28H_float32": 100,
            "oww": 250,
        },
        "distillation": {
            "enabled": True,
            "steps": 8000 if not pilot else 1000,
            "temperature": 4.0,
            "alpha": 0.7,
            "learning_rate": 0.0005,
            "student_layer_size": 8,
            "student_n_blocks": 1,
            "student_embedding_dim": 8,
        },
        "feature_manifest": {
            "targets": {
                "t": f"./models/wake/nanowakeword/{model_name}/features/positive_features.npy",
            },
            "negatives": {
                "AE28H_float32": "./AE29H_float32.npy",
                "b": "./RACON_11h_v1.npy",
                "n": f"./models/wake/nanowakeword/{model_name}/features/negative_features.npy",
                "hn": f"./models/wake/nanowakeword/{model_name}/features/hard_negative_features.npy",
                "oww": "./openwakeword_features_ACAV100M_2000_hrs_16bit.npy",
            },
            "targets_val": {
                "t_v": f"./models/wake/nanowakeword/{model_name}/features/positive_features_val.npy",
            },
            "negatives_val": {
                "bv": "./RACON_11h_v1.npy",
            },
        },
        "target_phrase": TARGET_PHRASE,
        "data_generation_tasks": [
            {
                "name": "positive_train",
                "enabled": True,
                "output_dir": "benchmarks/data/wake/hola_roger/positive",
                "num_samples": sample_count(2500, pilot),
                "file_prefix": "pos",
                "text_source": {"type": "fixed_phrase", "phrase": TARGET_PHRASE},
            },
            {
                "name": "positive_pronunciation_variants",
                "enabled": True,
                "output_dir": "benchmarks/data/wake/hola_roger/positive_variants",
                "num_samples": sample_count(900, pilot),
                "file_prefix": "pos_variant",
                "text_source": {
                    "type": "from_list",
                    "phrases": POSITIVE_VARIANTS,
                    "repeat_each": 300 if not pilot else 30,
                },
            },
            {
                "name": "positive_validation",
                "enabled": True,
                "output_dir": "benchmarks/data/wake/hola_roger/positive_val",
                "num_samples": sample_count(2000, pilot),
                "file_prefix": "pos_val",
                "text_source": {"type": "fixed_phrase", "phrase": TARGET_PHRASE},
            },
            {
                "name": "automatic_adversarial_negatives",
                "enabled": True,
                "output_dir": "benchmarks/data/wake/hola_roger/negative",
                "num_samples": sample_count(5000, pilot),
                "file_prefix": "neg_auto",
                "text_source": {
                    "type": "auto_adversarial",
                    "base_phrase": TARGET_PHRASE,
                    "include_input_words": True,
                    "include_partial_phrase": True,
                    "multi_word_prob": 0.5,
                    "max_multi_word_len": 3,
                },
            },
            {
                "name": "phoneme_hard_negatives",
                "enabled": True,
                "output_dir": "benchmarks/data/wake/hola_roger/negative_phoneme",
                "num_samples": sample_count(3000, pilot),
                "file_prefix": "neg_ph",
                "text_source": {
                    "type": "phoneme_adversarial",
                    "base_phrase": TARGET_PHRASE,
                    "min_distance": 0.3,
                },
            },
            {
                "name": "manual_nearby_negatives",
                "enabled": True,
                "output_dir": "benchmarks/data/wake/hola_roger/negative",
                "num_samples": len(MANUAL_NEGATIVES) * (2 if pilot else 10),
                "file_prefix": "neg_manual",
                "text_source": {
                    "type": "from_list",
                    "phrases": MANUAL_NEGATIVES,
                    "repeat_each": 2 if pilot else 10,
                },
            },
        ],
        "augmentation_batch_size": 16,
        "feature_gen_cpu_ratio": 1.0,
        "augmentation_settings": {
            "gain_prob": 1.0,
            "max_gain_in_db": 2.0,
            "max_pitch_semitones": 1.0,
            "max_snr_in_db": 35.0,
            "min_gain_in_db": -2.0,
            "min_pitch_semitones": -1.0,
            "min_snr_in_db": 15.0,
            "pitch_prob": 0.3,
            "rir_prob": 0.0,
        },
        "feature_generation_manifest": {
            "positive_features": {
                "input_audio_dirs": [
                    "./benchmarks/data/wake/hola_roger/positive",
                    "./benchmarks/data/wake/hola_roger/positive_variants",
                    "./benchmarks/data/wake/hola_roger/real_positive",
                    "./benchmarks/data/wake/hola_roger/real_positive_variants",
                ],
                "output_filename": "positive_features.npy",
                "use_background_noise": True,
                "use_rir": False,
                "augmentation_rounds": 2 if pilot else 10,
            },
            "positive_val_features": {
                "input_audio_dirs": ["./benchmarks/data/wake/hola_roger/positive_val"],
                "output_filename": "positive_features_val.npy",
                "use_background_noise": True,
                "use_rir": False,
                "augmentation_rounds": 2 if pilot else 10,
            },
            "negative_features": {
                "input_audio_dirs": [
                    "./benchmarks/data/wake/hola_roger/negative",
                    "./benchmarks/data/wake/hola_roger/real_negative",
                ],
                "output_filename": "negative_features.npy",
                "use_background_noise": True,
                "use_rir": False,
                "augmentation_rounds": 2 if pilot else 10,
            },
            "hard_negative_features": {
                "input_audio_dirs": ["./benchmarks/data/wake/hola_roger/negative_phoneme"],
                "output_filename": "hard_negative_features.npy",
                "use_background_noise": True,
                "use_rir": False,
                "augmentation_rounds": 1,
            },
        },
        "clip_length_samples": 32000,
        "background_paths_duplication_rate": [1],
        "val_miss_weight": 4.0,
        "val_fp_weight": 1.0,
        "validation_batch_size": 256,
        "validation_smoothing_window": 3,
        "val_early_stopping_patience": 6000 if not pilot else 1000,
        "hardness_ema_alpha": 0.05,
        "hardness_floor": 0.05,
        "hardness_reset_interval": 5000,
        "hardness_reset_decay": 0.5,
        "checkpoint_averaging_top_k": 5,
        "checkpointing": {
            "enabled": True,
            "interval_steps": 1000 if not pilot else 500,
            "limit": 2,
        },
        "early_stopping_patience": 0,
        "min_delta": 0.0001,
        "ema_alpha": 0.01,
        "onnx_opset_version": 17,
        "show_training_summary": True,
        "debug_mode": True,
        "generate_clips": True,
        "transform_clips": True,
        "train_model": True,
        "overwrite": False,
    }


def write_configs(output_dir: Path, pilot: bool = False) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for architecture in ARCHITECTURES:
        path = output_dir / f"hola_roger_{architecture}.yaml"
        config = build_config(architecture, pilot=pilot)
        path.write_text(
            yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate NanoWakeWord YAML configs for Roger.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("configs/nanowakeword"),
        help="Directory for generated YAML configs.",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Generate reduced configs for a fast local smoke-training run.",
    )
    args = parser.parse_args()

    paths = write_configs(args.output_dir, pilot=args.pilot)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
