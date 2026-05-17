from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roger.routing.registry import SessionRegistry


@dataclass(frozen=True)
class PiSessionManager:
    registry: SessionRegistry
    session_dir: Path
    ollama_model: str | None = None

    def build_command(self, session_name: str, offline: bool = False) -> list[str]:
        session_path = self.session_dir / session_name
        return [
            "pi",
            "--mode",
            "rpc",
            "--session-dir",
            str(session_path),
            *select_model_args(offline=offline, ollama_model=self.ollama_model),
        ]

    def cwd_for(self, session_name: str) -> Path:
        return self.registry.get(session_name).cwd


def select_model_args(offline: bool, ollama_model: str | None) -> list[str]:
    if not offline:
        return []
    args = ["--provider", "ollama"]
    if ollama_model:
        args.extend(["--model", ollama_model])
    return args
