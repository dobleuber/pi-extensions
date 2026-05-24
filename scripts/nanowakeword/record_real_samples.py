#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path("benchmarks/data/wake/hola_roger")
DEFAULT_BLUETOOTH_SOURCE = "bluez_input.A0:0C:E2:46:9A:98"

NEGATIVE_PROMPTS = [
    "hola",
    "roger",
    "oye roger",
    "hola rojo",
    "hola robert",
    "hola router",
    "habla normal sin decir la frase exacta",
]


def output_dir_for(kind: str) -> Path:
    if kind == "positive":
        return BASE_DIR / "real_positive"
    if kind == "negative":
        return BASE_DIR / "real_negative"
    raise ValueError(f"Unsupported sample kind: {kind}")


def sample_filename(kind: str, index: int) -> str:
    if kind == "positive":
        return f"hola_roger_{index:03d}.wav"
    if kind == "negative":
        return f"negative_{index:03d}.wav"
    raise ValueError(f"Unsupported sample kind: {kind}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record real wake-word samples for Roger.")
    parser.add_argument(
        "kind",
        nargs="?",
        choices=("positive", "negative"),
        default="positive",
        help="Type of samples to record.",
    )
    parser.add_argument("--count", type=int, default=50, help="Number of clips to record.")
    parser.add_argument("--seconds", type=float, default=2.0, help="Seconds per clip.")
    parser.add_argument("--pause", type=float, default=1.0, help="Seconds to wait before each clip.")
    parser.add_argument(
        "--target",
        default=DEFAULT_BLUETOOTH_SOURCE,
        help="PipeWire target source. Defaults to your OpenDots ONE source.",
    )
    parser.add_argument("--rate", type=int, default=16000, help="Sample rate.")
    parser.add_argument("--channels", type=int, default=1, help="Number of channels.")
    parser.add_argument(
        "--start-at",
        type=int,
        default=1,
        help="Starting sample index. Useful to continue a previous session.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing clips instead of skipping them.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def prompt_for(kind: str, index: int) -> str:
    if kind == "positive":
        return "Di: hola roger"
    return f"Di negativo: {NEGATIVE_PROMPTS[(index - 1) % len(NEGATIVE_PROMPTS)]}"


def record_clip(path: Path, args: argparse.Namespace, prompt: str | None = None) -> None:
    cmd = [
        "pw-record",
        "--target",
        args.target,
        "--rate",
        str(args.rate),
        "--channels",
        str(args.channels),
        str(path),
    ]
    proc = subprocess.Popen(cmd)
    try:
        time.sleep(0.2)
        if prompt:
            print(f"  GRABANDO AHORA: {prompt}", flush=True)
        time.sleep(args.seconds)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def run(args: argparse.Namespace) -> int:
    out_dir = output_dir_for(args.kind)
    out_dir.mkdir(parents=True, exist_ok=True)

    end = args.start_at + args.count - 1
    print(f"Guardando clips en: {out_dir}")
    print(f"Fuente PipeWire: {args.target}")
    print("Ctrl+C para detener.\n")

    try:
        for index in range(args.start_at, end + 1):
            path = out_dir / sample_filename(args.kind, index)
            if path.exists() and not args.overwrite:
                print(f"[{index}/{end}] Existe, saltando: {path.name}")
                continue

            prompt = prompt_for(args.kind, index)
            print(f"[{index}/{end}] Prepárate: {prompt}")
            time.sleep(args.pause)
            record_clip(path, args, prompt=prompt)
            print(f"  -> {path}")
    except KeyboardInterrupt:
        print("\nGrabación detenida.")
        return 130

    print("Grabación terminada.")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
