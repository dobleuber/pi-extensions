from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence, Type

from roger.config import load_config
from roger.benchmarks.wake_nanowakeword import write_training_configs
from roger.benchmarks.wake_nanowakeword import ARCHITECTURES
from roger.benchmarks.speech import build_stt_plan, build_tts_plan, build_vad_plan
from roger.backends.factory import create_stt_backend, create_tts_backend, create_vad_backend, create_wake_backend
from roger.config import RogerConfig
from roger.feedback import ConsoleFeedback
from roger.pi_rpc.runner import PiAgentRunner
from roger.pi_rpc.sessions import PiSessionManager
from roger.routing.registry import SessionEntry, SessionRegistry
from roger.tts_speaker import NoopSpeaker, SynthesizingSpeaker
from roger.voice_loop import VoiceLoop


SPIKES = ("wake", "vad", "stt", "tts")


@dataclass(frozen=True)
class RuntimeDependencies:
    create_wake_backend: Callable = create_wake_backend
    create_vad_backend: Callable = create_vad_backend
    create_stt_backend: Callable = create_stt_backend
    create_pi_runner: Callable = None
    create_tts_speaker: Callable = None
    voice_loop_class: Type = VoiceLoop

    def __post_init__(self):
        if self.create_pi_runner is None:
            object.__setattr__(self, "create_pi_runner", _create_pi_runner)
        if self.create_tts_speaker is None:
            object.__setattr__(self, "create_tts_speaker", _create_tts_speaker)


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

    listen_once = subcommands.add_parser("listen-once", help="Run one wake/capture/transcribe/dispatch cycle")
    listen_once.add_argument("--config", type=Path, default=None, help="Path to roger TOML config")
    listen_once.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Current project directory")
    listen_once.add_argument("--manual-wake", action="store_true", help="Use and trigger the manual wake adapter")
    listen_once.add_argument("--preview-action", choices=("accept", "cancel", "timeout"), default="accept")
    listen_once.add_argument("--offline", action="store_true", help="Use offline/Ollama pi-agent mode")
    listen_once.add_argument("--no-tts", action="store_true", help="Do not synthesize spoken output")
    listen_once.add_argument("--quiet", action="store_true", help="Suppress live progress messages")
    listen_once.add_argument("--wake-threshold", type=float, default=None, help="Override wake detection threshold for this run")
    listen_once.add_argument("--wake-debug", action="store_true", help="Print NanoWakeWord scores while waiting")
    listen_once.add_argument("--wake-debug-min-score", type=float, default=0.2, help="Minimum score printed by --wake-debug")

    return parser


def run(argv: Sequence[str] | None = None, dependencies: RuntimeDependencies | None = None) -> tuple[int, str]:
    parser = build_parser()
    args = parser.parse_args(argv)
    dependencies = dependencies or RuntimeDependencies()

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
    if args.command == "listen-once":
        registry = _registry_from_config(config)
        wake = dependencies.create_wake_backend(config, force_manual=args.manual_wake)
        if args.wake_threshold is not None and hasattr(wake, "threshold"):
            wake.threshold = args.wake_threshold
        if args.wake_debug and hasattr(wake, "score_callback"):
            wake.score_callback = _build_wake_score_callback(quiet=args.quiet, min_score=args.wake_debug_min_score)
        if args.manual_wake and hasattr(wake, "trigger"):
            wake.trigger()
        feedback = None if args.quiet else ConsoleFeedback(echo=True)
        if args.manual_wake and feedback is not None:
            feedback.listening_for_wake(manual=True)
        loop = dependencies.voice_loop_class(
            registry,
            wake,
            dependencies.create_vad_backend(config),
            dependencies.create_stt_backend(config),
            dependencies.create_pi_runner(config, registry, offline=args.offline),
            dependencies.create_tts_speaker(config, no_tts=args.no_tts),
            preview_action=args.preview_action,
            feedback=feedback,
        )
        try:
            result = loop.run_once()
        except KeyboardInterrupt:
            return 130, "Roger interrumpido por el usuario\n"
        return 0, _format_listen_once_result(result)

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
        f"wake threshold: {config.speech.wake.threshold}",
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


def _format_listen_once_result(result) -> str:
    dispatched = "yes" if result.dispatched else "no"
    lines = [
        "Roger listen-once result",
        f"status: {result.status}",
        f"dispatched: {dispatched}",
    ]
    if result.message:
        lines.append(f"message: {result.message}")
    return "\n".join(lines) + "\n"


def _registry_from_config(config: RogerConfig) -> SessionRegistry:
    return SessionRegistry(
        {
            name: SessionEntry(name=name, cwd=session.cwd, description=session.description)
            for name, session in config.sessions.items()
        }
    )


def _create_pi_runner(config: RogerConfig, registry: SessionRegistry, offline: bool = False) -> PiAgentRunner:
    session_manager = PiSessionManager(
        registry=registry,
        session_dir=Path(".roger/pi-sessions"),
        ollama_model=config.models.offline.model,
    )
    return PiAgentRunner(session_manager=session_manager, offline=offline)


def _create_tts_speaker(config: RogerConfig, no_tts: bool = False):
    if no_tts:
        return NoopSpeaker()
    return SynthesizingSpeaker(create_tts_backend(config))


def _build_wake_score_callback(quiet: bool = False, min_score: float = 0.2):
    def callback(score: float) -> None:
        if not quiet and score >= min_score:
            print(f"wake score={score:.3f}", flush=True)

    return callback


if __name__ == "__main__":
    raise SystemExit(main())
