from __future__ import annotations


def summarize_for_speech(text: str, max_chars: int = 240) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 1:
        return "…"
    return normalized[: max_chars - 1].rstrip() + "…"
