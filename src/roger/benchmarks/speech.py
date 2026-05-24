from __future__ import annotations

from typing import Any


def build_vad_plan() -> dict[str, Any]:
    return {
        "sample_format": "16 kHz mono 16-bit PCM",
        "candidates": [
            {
                "backend": "silero",
                "implementation": "silero-vad ONNX/Python",
                "initial_threshold": 0.5,
                "min_speech_duration_ms": 200,
                "min_silence_duration_ms": 700,
                "speech_pad_ms": 200,
            },
            {
                "backend": "webrtc",
                "implementation": "py-webrtcvad",
                "mode": 2,
                "frame_ms": 30,
                "padding_ms": 300,
                "voiced_ratio": 0.9,
            },
        ],
        "metrics": [
            "start_latency_ms",
            "end_latency_p50_ms",
            "end_latency_p95_ms",
            "clipped_start_rate",
            "clipped_end_rate",
            "false_command_windows_per_hour",
            "missed_instruction_rate",
            "cpu_percent",
            "rss_mb",
        ],
        "default_backend": default_vad_backend(),
        "default_thresholds": {
            "silence_timeout_ms": 700,
            "max_capture_seconds": 30,
        },
    }


def build_stt_plan() -> dict[str, Any]:
    return {
        "language": "es",
        "sample_format": "16 kHz mono WAV",
        "candidates": [
            {
                "backend": "faster-whisper",
                "models": ["tiny", "base", "small"],
                "compute_types": ["int8", "float16"],
                "options": {
                    "language": "es",
                    "task": "transcribe",
                    "beam_size": 1,
                    "condition_on_previous_text": False,
                    "temperature": 0.0,
                },
            },
            {
                "backend": "whisper.cpp",
                "models": ["tiny", "base", "small"],
                "quantizations": ["q8_0", "q5_0"],
                "options": {"language": "es", "threads": [2, 4]},
            },
        ],
        "metrics": [
            "model_load_seconds",
            "transcription_seconds",
            "real_time_factor",
            "speech_end_to_text_ms",
            "peak_rss_mb",
            "cpu_percent",
            "wer",
            "cer",
            "intent_accuracy",
            "false_accept_rate",
            "false_reject_rate",
        ],
        "default_backend": default_stt_backend(),
        "default_model": "base",
    }


def build_tts_plan() -> dict[str, Any]:
    return {
        "language": "es",
        "samples": [
            "Hola, ¿cómo estás?",
            "La tarea terminó correctamente. Dejé el resultado en pantalla.",
            "No pude completar la tarea porque pi-agent no está disponible.",
        ],
        "candidates": [
            {
                "backend": "kokoro",
                "implementation": "kokoro Python or kokoro-onnx",
                "voices_to_try": ["ef_dora", "em_alex", "em_santa"],
                "notes": "Higher-quality candidate; validate Spanish quality and runtime dependencies.",
            },
            {
                "backend": "piper",
                "implementation": "piper CLI or PiperVoice Python",
                "voices_to_try": ["es_ES-davefx-medium", "es_MX-ald-medium"],
                "notes": "Low-resource fallback/baseline with broad local voice usage.",
            },
        ],
        "metrics": [
            "cold_start_seconds",
            "warm_synthesis_seconds",
            "time_to_first_audio_ms",
            "output_audio_seconds",
            "real_time_factor",
            "peak_rss_mb",
            "cpu_percent",
            "voice_quality_score",
            "package_status_verified",
            "license_verified",
            "offline_verified",
        ],
        "default_backend": default_tts_backend(),
    }


def default_vad_backend() -> str:
    return "silero"


def default_stt_backend() -> str:
    return "faster-whisper"


def default_tts_backend() -> str:
    return "kokoro"
