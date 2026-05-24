#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

DEFAULT_MODEL = "models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Listen live for Roger's NanoWakeWord model using the microphone."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Path to the NanoWakeWord ONNX model to test.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Detection threshold. Raise this if false positives are common.",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=1.5,
        help="Seconds to wait between detections.",
    )
    parser.add_argument(
        "--min-print-score",
        type=float,
        default=0.2,
        help="Only print non-detection scores at or above this value.",
    )
    parser.add_argument(
        "--samplerate",
        type=int,
        default=16000,
        help="Microphone sample rate. NanoWakeWord expects 16000 Hz.",
    )
    parser.add_argument(
        "--blocksize",
        type=int,
        default=1280,
        help="Audio frames per inference block. 1280 is 80 ms at 16 kHz.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional sounddevice input device id or name.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Optional max runtime in seconds. 0 means run until Ctrl+C.",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List audio devices and exit.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def should_print_score(score: float, min_print_score: float) -> bool:
    return score >= min_print_score


def should_detect(score: float, threshold: float, now: float, last_detection: float, cooldown: float) -> bool:
    return score >= threshold and now - last_detection > cooldown


def run_listener(args: argparse.Namespace) -> int:
    try:
        import sounddevice as sd
        from nanowakeword import NanoInterpreter
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency. Install speech dependencies first:\n"
            "  uv sync --group speech"
        ) from exc

    if args.list_devices:
        print(sd.query_devices())
        return 0

    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")

    interpreter = NanoInterpreter.load_model(str(model_path))
    last_detection = 0.0
    started = time.monotonic()

    print(f"Model: {model_path}")
    print(f"Threshold: {args.threshold:.3f} | cooldown: {args.cooldown:.1f}s")
    print("Escuchando. Di 'hola roger'. Ctrl+C para salir.")

    try:
        with sd.InputStream(
            samplerate=args.samplerate,
            channels=1,
            dtype="int16",
            blocksize=args.blocksize,
            device=args.device,
        ) as stream:
            while True:
                audio, _ = stream.read(args.blocksize)
                result = interpreter.predict(
                    audio[:, 0],
                    threshold={interpreter.model_name: args.threshold},
                )
                score = result.score

                if should_print_score(score, args.min_print_score):
                    print(f"score={score:.3f}")

                now = time.monotonic()
                if should_detect(score, args.threshold, now, last_detection, args.cooldown):
                    print(f"DETECTADO: {interpreter.model_name} score={score:.3f}")
                    interpreter.reset()
                    last_detection = now

                if args.duration > 0 and now - started >= args.duration:
                    return 0
    except KeyboardInterrupt:
        print("\nDetenido.")
        return 130


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_listener(args)


if __name__ == "__main__":
    raise SystemExit(main())
