from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence


VOICE_COMMANDS = {"daemon", "listen-once"}
CUDA_READY_ENV = "ROGER_CUDA_ENV_READY"


def command_uses_cuda_stt(argv: Sequence[str]) -> bool:
    return any(arg in VOICE_COMMANDS for arg in argv[1:])


def find_cuda_library_dirs(search_roots: Iterable[Path] | None = None) -> list[Path]:
    roots = list(search_roots) if search_roots is not None else _default_search_roots()
    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("libcublas.so.12"):
            if path.is_file() or path.is_symlink():
                found.append(path.parent)
    return _dedupe(found)


def build_cuda_library_path(cuda_dirs: list[Path], existing: str | None = None) -> str:
    parts = [str(path) for path in cuda_dirs]
    if existing:
        parts.append(existing)
    return ":".join(parts)


def cuda_env_for_reexec(argv: Sequence[str], env: dict[str, str] | None = None) -> dict[str, str] | None:
    env = dict(os.environ if env is None else env)
    if env.get(CUDA_READY_ENV) == "1":
        return None
    if not command_uses_cuda_stt(argv):
        return None
    cuda_dirs = find_cuda_library_dirs()
    if not cuda_dirs:
        return None
    env["LD_LIBRARY_PATH"] = build_cuda_library_path(cuda_dirs, env.get("LD_LIBRARY_PATH"))
    env[CUDA_READY_ENV] = "1"
    return env


def _default_search_roots() -> list[Path]:
    roots = [
        Path("/opt/resolve/libs"),
        Path("/usr/local/cuda/lib64"),
        Path(os.sys.prefix) / "lib" / f"python{os.sys.version_info.major}.{os.sys.version_info.minor}" / "site-packages" / "nvidia",
    ]
    return roots


def _dedupe(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result
