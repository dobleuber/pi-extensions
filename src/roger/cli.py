from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from roger.config import load_config
from roger.benchmarks.wake_nanowakeword import write_training_configs
from roger.benchmarks.wake_nanowakeword import ARCHITECTURES
from roger.benchmarks.speech import build_stt_plan, build_tts_plan, build_vad_plan


SPIKES = ("wake", "vad", "stt", "tts")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="roger", description="Roger laptop interface")
    subcommands = parser.add_subparsers(dest="command", required=True)

    health = subcommands.add_parser("health", help="Run configuration and environment health checks")
    health.add_argument("--config", type=Path, default=None, help="Path to roger TOML config")
    health.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Current project directory")

    spike = subcommands.add_parser("spike", help="Run or dry-run an implementation spike")
    spike.add_argument("spike", choices=SPIKES)
    spike.add_argument("--dry-run", action="store_true", help="Print spike plan without executing heavy dependencies")
    spike.add_argument("--write-configs", action="store_true", help="Write generated benchmark/training configs when supported")
    spike.add_argument("--output-dir", type=Path, default=Path("configs/nanowakeword"), help="Output directory for generated configs")
    spike.add_argument("--config", type=Path, default=None, help="Path to roger TOML config")
    spike.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Current project directory")

    return parser


def run(argv: Sequence[str] | None = None) -> tuple[int, str]:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.config, project_dir=args.project_dir)

    if args.command == "health":
        return 0, _format_health(config)
    if args.command == "spike":
        if args.spike == "wake" and args.write_configs:
            paths = write_training_configs(config.speech.wake.target_phrase, args.output_dir)
            path_list = "\n".join(f"- {path}" for path in paths)
            return 0, f"wake spike: wrote {len(paths)} NanoWakeWord configs\n{path_list}\n"
        mode = "dry-run" if args.dry_run else "run"
        return 0, _format_spike(args.spike, mode)

    return 2, f"Unsupported command: {args.command}\n"


def main(argv: Sequence[str] | None = None) -> int:
    exit_code, output = run(argv)
    print(output, end="" if output.endswith("\n") else "\n")
    return exit_code


def _format_health(config) -> str:
    sessions = ", ".join(sorted(config.sessions))
    lines = [
        "Roger health",
        f"wake: {config.speech.wake.backend}",
        f"target: {config.speech.wake.target_phrase}",
        f"wake architectures: {', '.join(config.speech.wake.architectures)}",
        f"vad: {config.speech.vad.backend}",
        f"stt: {config.speech.stt.backend}",
        f"tts: {config.speech.tts.backend}",
        f"online model provider: {config.models.online.provider}",
        f"offline model provider: {config.models.offline.provider}",
        f"sessions: {sessions}",
    ]
    return "\n".join(lines) + "\n"


def _format_spike(spike: str, mode: str) -> str:
    candidates: list[str]
    if spike == "wake":
        candidates = list(ARCHITECTURES)
    elif spike == "vad":
        candidates = [candidate["backend"] for candidate in build_vad_plan()["candidates"]]
    elif spike == "stt":
        candidates = [candidate["backend"] for candidate in build_stt_plan()["candidates"]]
    elif spike == "tts":
        candidates = [candidate["backend"] for candidate in build_tts_plan()["candidates"]]
    else:
        candidates = []
    suffix = f"candidates: {', '.join(candidates)}" if candidates else "candidates: none"
    return f"{spike} spike ({mode})\n{suffix}\n"


if __name__ == "__main__":
    raise SystemExit(main())
