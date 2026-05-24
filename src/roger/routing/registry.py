from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionEntry:
    name: str
    cwd: Path
    description: str = ""
    routing_keywords: list[str] = None
    ambiguity_keywords: list[str] = None
    destructive_keywords: list[str] = None
    reuse_session: bool = True

    def __post_init__(self):
        if self.routing_keywords is None:
            object.__setattr__(self, "routing_keywords", [])
        if self.ambiguity_keywords is None:
            object.__setattr__(self, "ambiguity_keywords", [])
        if self.destructive_keywords is None:
            object.__setattr__(self, "destructive_keywords", [])

    def with_updates(self, **kwargs: Any) -> "SessionEntry":
        return replace(self, **kwargs)


class SessionRegistry:
    def __init__(self, entries: dict[str, SessionEntry]):
        self._entries = dict(entries)

    @classmethod
    def default(cls, project_dir: Path | None = None) -> "SessionRegistry":
        project = Path.cwd() if project_dir is None else project_dir
        return cls(
            {
                "system": SessionEntry(
                    "system",
                    Path.home(),
                    "Laptop/system tasks",
                    routing_keywords=[
                        "instala",
                        "instalar",
                        "desinstala",
                        "desinstalar",
                        "actualiza el sistema",
                        "actualizar el sistema",
                        "mata",
                        "matar",
                        "cierra",
                        "reinicia",
                        "apaga",
                        "hora",
                        "fecha",
                        "calcula",
                        "calcular",
                        "clima",
                    ],
                ),
                "current-project": SessionEntry(
                    "current-project",
                    project,
                    "Active project tasks",
                    routing_keywords=[
                        "tests",
                        "ejecuta pruebas",
                        "edita",
                        "editar",
                        "readme",
                        "codigo",
                        "código",
                        "crea un demo",
                        "crear un demo",
                        "proyecto",
                        "inspecciona",
                    ],
                ),
            }
        )

    def with_entry(
        self,
        name: str,
        cwd: Path,
        description: str = "",
        routing_keywords: list[str] | None = None,
        ambiguity_keywords: list[str] | None = None,
        destructive_keywords: list[str] | None = None,
        reuse_session: bool = True,
    ) -> "SessionRegistry":
        entries = dict(self._entries)
        entries[name] = SessionEntry(
            name=name,
            cwd=cwd,
            description=description,
            routing_keywords=routing_keywords or [],
            ambiguity_keywords=ambiguity_keywords or [],
            destructive_keywords=destructive_keywords or [],
            reuse_session=reuse_session,
        )
        return SessionRegistry(entries)

    def get(self, name: str) -> SessionEntry:
        return self._entries[name]

    def entries(self) -> list[SessionEntry]:
        return [self._entries[name] for name in self.names()]

    def names(self) -> list[str]:
        return sorted(self._entries)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, entry in self._entries.items():
            if entry.name != name:
                errors.append(f"session {name} has mismatched entry name {entry.name}")
            for field_name in ("routing_keywords", "ambiguity_keywords", "destructive_keywords"):
                value = getattr(entry, field_name)
                if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
                    errors.append(f"session {name} has malformed {field_name}")
            if not isinstance(entry.reuse_session, bool):
                errors.append(f"session {name} has malformed reuse_session")
        return errors
