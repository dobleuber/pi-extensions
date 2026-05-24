from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from roger.routing.registry import SessionRegistry


@dataclass(frozen=True)
class RouteDecision:
    session_name: str | None
    needs_clarification: bool = False
    question: str = ""
    matched_rule: str = ""
    reason: str = ""
    confidence: str = "high"
    reuse_session: bool = True


AMBIGUOUS_DESTRUCTIVE = (
    "borra",
    "borrar",
    "elimina",
    "eliminar",
    "rm",
    "kill",
    "sobrescribe",
    "sobrescribir",
)


class Router:
    def __init__(self, registry: SessionRegistry):
        self.registry = registry

    def route(self, instruction: str) -> RouteDecision:
        text = _normalize(instruction)
        destructive_match = _first_keyword_match(text, AMBIGUOUS_DESTRUCTIVE)
        if destructive_match is not None:
            return RouteDecision(
                session_name=None,
                needs_clarification=True,
                question="¿En qué contexto querés ejecutar esa acción: system o current-project?",
                matched_rule=f"destructive:{destructive_match}",
                reason="destructive action requires explicit target context",
                confidence="low",
            )

        matches: list[tuple[str, str]] = []
        for entry in self.registry.entries():
            keyword = _first_keyword_match(text, entry.routing_keywords)
            if keyword is not None:
                matches.append((entry.name, keyword))

        if len(matches) == 1:
            session_name, keyword = matches[0]
            entry = self.registry.get(session_name)
            return RouteDecision(
                session_name=session_name,
                matched_rule=f"keyword:{keyword}",
                reason=f"matched routing keyword for {session_name}",
                confidence="high",
                reuse_session=entry.reuse_session,
            )
        if len(matches) > 1:
            domains = ", ".join(name for name, _keyword in matches)
            return RouteDecision(
                session_name=None,
                needs_clarification=True,
                question=f"La tarea coincide con varios contextos ({domains}). ¿Cuál uso?",
                matched_rule="ambiguous:multiple-domains",
                reason=f"ambiguous routing match: {domains}",
                confidence="low",
            )

        return RouteDecision(
            session_name=None,
            needs_clarification=True,
            question="¿A qué contexto pertenece esta tarea: system o current-project?",
            matched_rule="ambiguous:no-match",
            reason="ambiguous instruction; no configured routing rule matched",
            confidence="low",
        )


def _first_keyword_match(text: str, keywords) -> str | None:
    if not isinstance(keywords, list | tuple):
        return None
    for keyword in keywords:
        normalized = _normalize(keyword)
        if _contains_keyword(text, normalized):
            return normalized
    return None


def _contains_keyword(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    if " " in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def _normalize(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9ñ ]+", " ", without_accents)
