from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shlex


START_MARKER = "-- >>> roger voice daemon >>>"
END_MARKER = "-- <<< roger voice daemon <<<"


@dataclass(frozen=True)
class InstallResult:
    changed: bool
    autostart_path: Path
    backup_path: Path | None = None


class AutostartInstaller:
    def __init__(self, home: Path | None = None, project_dir: Path | None = None):
        self.home = Path.home() if home is None else home
        self.project_dir = Path.cwd() if project_dir is None else project_dir
        self.autostart_path = self.home / ".config" / "hypr" / "autostart.lua"

    def install(self) -> InstallResult:
        self.autostart_path.parent.mkdir(parents=True, exist_ok=True)
        original = self._read_autostart()
        if START_MARKER in original:
            return InstallResult(changed=False, autostart_path=self.autostart_path)

        backup = self._backup(original)
        updated = original.rstrip() + "\n\n" + self._managed_block() + "\n"
        self.autostart_path.write_text(updated, encoding="utf-8")
        return InstallResult(changed=True, autostart_path=self.autostart_path, backup_path=backup)

    def uninstall(self) -> InstallResult:
        original = self._read_autostart()
        if START_MARKER not in original:
            return InstallResult(changed=False, autostart_path=self.autostart_path)

        backup = self._backup(original)
        start = original.index(START_MARKER)
        end = original.index(END_MARKER) + len(END_MARKER)
        updated = (original[:start] + original[end:]).replace("\n\n\n", "\n\n").strip() + "\n"
        self.autostart_path.write_text(updated, encoding="utf-8")
        return InstallResult(changed=True, autostart_path=self.autostart_path, backup_path=backup)

    def _read_autostart(self) -> str:
        if not self.autostart_path.exists():
            return "-- Extra autostart processes.\n"
        return self.autostart_path.read_text(encoding="utf-8")

    def _backup(self, content: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.autostart_path.with_suffix(self.autostart_path.suffix + f".bak.roger-{timestamp}")
        backup.write_text(content, encoding="utf-8")
        return backup

    def _managed_block(self) -> str:
        project = shlex.quote(str(self.project_dir))
        command = f"cd {project} && uv run roger daemon"
        lua_command = command.replace('\\', '\\\\').replace('"', '\\"')
        return (
            f"{START_MARKER}\n"
            "-- Roger voice daemon. Managed by `uv run roger install-autostart`.\n"
            f'o.exec_on_start("bash -lc \\\"{lua_command}\\\"")\n'
            f"{END_MARKER}"
        )
