from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from roger.routing.registry import SessionRegistry


@dataclass(frozen=True)
class RouteDecision:
    session_name: str | None
    needs_clarification: bool = False
    question: str = ""


SYSTEM_KEYWORDS = (
    "instala",
    "instalar",
    "desinstala",
    "desinstalar",
    "actualiza el sistema",
    "actualizar el sistema",
    "mata ",
    "matar ",
    "cierra ",
    "reinicia ",
    "apaga ",
)

PROJECT_KEYWORDS = (
    "corre los tests",
    "correr los tests",
    "ejecuta pruebas",
    "tests",
    "edita",
    "editar",
    "readme",
    "codigo",
    "código",
    "crea un demo",
    "crear un demo",
    "proyecto",
    "inspecciona",
)

AMBIGUOUS_DESTRUCTIVE = (
    "borra",
    "borrar",
    "elimina",
    "eliminar",
    "rm ",
)


class Router:
    def __init__(self, registry: SessionRegistry):
        self.registry = registry

    def route(self, instruction: str) -> RouteDecision:
        text = _normalize(instruction)
        if any(keyword in text for keyword in AMBIGUOUS_DESTRUCTIVE):
            return RouteDecision(
                session_name=None,
                needs_clarification=True,
                question="¿En qué contexto querés ejecutar esa acción: system o current-project?",
            )
        if any(keyword in text for keyword in SYSTEM_KEYWORDS):
            return RouteDecision(session_name="system")
        if any(keyword in text for keyword in PROJECT_KEYWORDS):
            return RouteDecision(session_name="current-project")
        return RouteDecision(
            session_name=None,
            needs_clarification=True,
            question="¿A qué contexto pertenece esta tarea: system o current-project?",
        )


def _normalize(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
