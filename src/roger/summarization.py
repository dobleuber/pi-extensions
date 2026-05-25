from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import json
import re
import urllib.error
import urllib.request


DEFAULT_ANGLICISM_PRONUNCIATIONS: dict[str, str] = {
    "GitHub": "guit jab",
    "pull request": "pul ricuest",
    "README": "ridmi",
    "API": "ei pi ai",
    "JSON": "yéison",
    "Docker": "dóker",
    "commit": "cómit",
    "branch": "branch",
    "fork": "fork",
    "login": "login",
    "token": "tóken",
    "repo": "repo",
}


@dataclass(frozen=True)
class SpeechScript:
    display_text: str
    speech_text: str
    source: str = "fallback"
    style: str = "neutral"
    degradation_reason: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


CompleteCallable = Callable[[dict[str, object], float], dict[str, object]]


@dataclass(frozen=True)
class GemmaSpeechNaturalizer:
    base_url: str = "http://127.0.0.1:11434/v1"
    model: str = "gemma4"
    timeout_seconds: float = 2.0
    max_input_chars: int = 4000
    complete: CompleteCallable | None = None
    style: str = "neutral"

    def naturalize(self, display_text: str) -> SpeechScript:
        try:
            response = self._complete(self._payload(display_text), self.timeout_seconds)
            speech_text = self._postprocess_output(self._clean_output(self._extract_text(response)))
            if not self._is_valid(speech_text, display_text):
                raise ValueError("invalid naturalizer output")
            return SpeechScript(
                display_text=display_text,
                speech_text=speech_text,
                source="gemma",
                style=self.style,
            )
        except Exception as error:
            script = prepare_speech_script(
                display_text,
                max_chars=240,
                style=self.style,
                source="fallback",
                degradation_reason=str(error),
            )
            if _looks_like_english_for_tts(script.speech_text):
                return SpeechScript(
                    display_text=display_text,
                    speech_text="No pude preparar una respuesta hablada en español.",
                    source="fallback",
                    style=self.style,
                    degradation_reason=str(error),
                )
            return script

    def _payload(self, display_text: str) -> dict[str, object]:
        clipped = display_text[: self.max_input_chars]
        return {
            "model": self.model,
            "temperature": 0.1,
            "max_tokens": 180,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Convierte texto visual de Roger en un guion natural en español solo para TTS. "
                        "Debes responder en español de forma completa, excepto anglicismos técnicos inevitables. "
                        "No cambies el significado. No expliques. No uses Markdown. "
                        "Mantén comandos, rutas y código como frases legibles o resúmelos sin corromperlos. "
                        "Pronuncia anglicismos técnicos de forma natural para una voz española. "
                        "Cuando una secuencia oral contenga cero solo como separador, como 'nine zero five', no pronuncies el cero: di 'nueve cinco'."
                    ),
                },
                {"role": "user", "content": clipped},
            ],
        }

    def _complete(self, payload: dict[str, object], timeout: float) -> dict[str, object]:
        if self.complete is not None:
            return self.complete(payload, timeout)
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise RuntimeError(str(error)) from error

    def _extract_text(self, response: dict[str, object]) -> str:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            return content.strip() if isinstance(content, str) else ""
        text = first.get("text")
        return text.strip() if isinstance(text, str) else ""

    def _clean_output(self, speech_text: str) -> str:
        cleaned = speech_text.strip()
        for marker in ("<|im_end|>", "<|im_start|>", "<end_of_turn>", "<start_of_turn>"):
            if marker in cleaned:
                cleaned = cleaned.split(marker, 1)[0].strip()
        return cleaned

    def _postprocess_output(self, speech_text: str) -> str:
        speech_text = _rewrite_anglicisms(speech_text, DEFAULT_ANGLICISM_PRONUNCIATIONS)
        return _normalize_spacing(speech_text)

    def _is_valid(self, speech_text: str, display_text: str = "") -> bool:
        if not speech_text.strip():
            return False
        if len(speech_text) > 600:
            return False
        if any(marker in speech_text for marker in ("<|", "im_start", "im_end")):
            return False
        if any(markdown in speech_text for markdown in ("**", "__", "```")):
            return False
        if _looks_like_english_for_tts(speech_text):
            return False
        if _looks_like_unchanged_english(speech_text, display_text):
            return False
        return True


def summarize_for_speech(text: str, max_chars: int = 240) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 1:
        return "…"
    return normalized[: max_chars - 1].rstrip() + "…"


def prepare_speech_script(
    display_text: str,
    *,
    max_chars: int = 240,
    anglicisms: dict[str, str] | None = None,
    style: str = "neutral",
    source: str = "fallback",
    degradation_reason: str = "",
) -> SpeechScript:
    speech_text = fallback_speech_text(display_text, max_chars=max_chars, anglicisms=anglicisms)
    return SpeechScript(
        display_text=display_text,
        speech_text=speech_text,
        source=source,
        style=style,
        degradation_reason=degradation_reason,
    )


def fallback_speech_text(
    text: str,
    *,
    max_chars: int = 240,
    anglicisms: dict[str, str] | None = None,
) -> str:
    cleaned = _rewrite_markdown(text)
    cleaned = _rewrite_times(cleaned)
    cleaned = _rewrite_anglicisms(cleaned, anglicisms or DEFAULT_ANGLICISM_PRONUNCIATIONS)
    cleaned = _normalize_spacing(cleaned)
    return summarize_for_speech(cleaned, max_chars=max_chars)


def _rewrite_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("*", "").replace("_", "")
    text = re.sub(r"[~#`|]+", " ", text)
    return text


def _rewrite_times(text: str) -> str:
    return re.sub(
        r"\b(\d{1,2}):(\d{2})\s*([AaPp])\.?\s*[Mm]\.?",
        lambda match: _time_to_spanish(match),
        text,
    )


def _time_to_spanish(match: re.Match[str]) -> str:
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3).lower()
    hour_12 = hour % 12 or 12
    period = "de la mañana" if meridiem == "a" else "de la tarde"
    if meridiem == "p" and hour_12 >= 7:
        period = "de la noche"
    hour_words = _SPANISH_NUMBERS.get(hour_12, str(hour_12))
    minute_words = _SPANISH_NUMBERS.get(minute, str(minute))
    if minute == 0:
        return f"{hour_words} en punto {period}"
    return f"{hour_words} y {minute_words} {period}"


_SPANISH_NUMBERS = {
    0: "cero",
    1: "una",
    2: "dos",
    3: "tres",
    4: "cuatro",
    5: "cinco",
    6: "seis",
    7: "siete",
    8: "ocho",
    9: "nueve",
    10: "diez",
    11: "once",
    12: "doce",
    13: "trece",
    14: "catorce",
    15: "quince",
    16: "dieciséis",
    17: "diecisiete",
    18: "dieciocho",
    19: "diecinueve",
    20: "veinte",
    21: "veintiuno",
    22: "veintidós",
    23: "veintitrés",
    24: "veinticuatro",
    25: "veinticinco",
    26: "veintiséis",
    27: "veintisiete",
    28: "veintiocho",
    29: "veintinueve",
    30: "treinta",
    31: "treinta y uno",
    32: "treinta y dos",
    33: "treinta y tres",
    34: "treinta y cuatro",
    35: "treinta y cinco",
    36: "treinta y seis",
    37: "treinta y siete",
    38: "treinta y ocho",
    39: "treinta y nueve",
    40: "cuarenta",
    41: "cuarenta y uno",
    42: "cuarenta y dos",
    43: "cuarenta y tres",
    44: "cuarenta y cuatro",
    45: "cuarenta y cinco",
    46: "cuarenta y seis",
    47: "cuarenta y siete",
    48: "cuarenta y ocho",
    49: "cuarenta y nueve",
    50: "cincuenta",
    51: "cincuenta y uno",
    52: "cincuenta y dos",
    53: "cincuenta y tres",
    54: "cincuenta y cuatro",
    55: "cincuenta y cinco",
    56: "cincuenta y seis",
    57: "cincuenta y siete",
    58: "cincuenta y ocho",
    59: "cincuenta y nueve",
}


def _looks_like_unchanged_english(speech_text: str, display_text: str) -> bool:
    normalized_speech = _normalize_for_language_check(speech_text)
    normalized_display = _normalize_for_language_check(display_text)
    english_markers = {
        "respond",
        "again",
        "it's",
        "it",
        "the",
        "task",
        "complete",
        "updated",
        "created",
        "fixed",
        "ran",
        "eight",
        "thirty",
        "nine",
        "zero",
    }
    if normalized_speech == normalized_display and any(marker in normalized_speech.split() for marker in english_markers):
        return True
    return False


def _normalize_for_language_check(text: str) -> str:
    normalized = text.lower().replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("it's", "it is")
    return re.sub(r"[^a-z0-9']+", " ", normalized).strip()


def _looks_like_english_for_tts(text: str) -> bool:
    words = set(_normalize_for_language_check(text).split())
    english_markers = {
        "respond",
        "again",
        "it's",
        "it",
        "is",
        "the",
        "task",
        "complete",
        "updated",
        "created",
        "fixed",
        "ran",
        "eight",
        "thirty",
        "nine",
        "zero",
    }
    return bool(words & english_markers)


def _rewrite_anglicisms(text: str, pronunciations: dict[str, str]) -> str:
    result = text
    for term in sorted(pronunciations, key=len, reverse=True):
        pronunciation = pronunciations[term]
        result = re.sub(rf"(?<![\w/.-]){re.escape(term)}(?![\w/-])", pronunciation, result, flags=re.IGNORECASE)
    return result


def _normalize_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text
