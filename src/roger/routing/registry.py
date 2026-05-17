from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionEntry:
    name: str
    cwd: Path
    description: str = ""


class SessionRegistry:
    def __init__(self, entries: dict[str, SessionEntry]):
        self._entries = dict(entries)

    @classmethod
    def default(cls, project_dir: Path | None = None) -> "SessionRegistry":
        project = Path.cwd() if project_dir is None else project_dir
        return cls(
            {
                "system": SessionEntry("system", Path.home(), "Laptop/system tasks"),
                "current-project": SessionEntry("current-project", project, "Active project tasks"),
            }
        )

    def get(self, name: str) -> SessionEntry:
        return self._entries[name]

    def names(self) -> list[str]:
        return sorted(self._entries)
