from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roger.routing.registry import SessionRegistry


@dataclass(frozen=True)
class PiSessionManager:
    registry: SessionRegistry
    session_dir: Path
    offline_provider: str = "llama-cpp"
    offline_model: str | None = "gemma4"

    def build_command(self, session_name: str, offline: bool = False) -> list[str]:
        session_path = self.session_dir / session_name
        return [
            "pi",
            "--mode",
            "rpc",
            "--session-dir",
            str(session_path),
            *select_model_args(offline=offline, provider=self.offline_provider, model=self.offline_model),
        ]

    def cwd_for(self, session_name: str) -> Path:
        return self.registry.get(session_name).cwd


def select_model_args(offline: bool, provider: str, model: str | None) -> list[str]:
    if not offline:
        return []
    args = ["--provider", provider]
    if model:
        args.extend(["--model", model])
    return args
