from __future__ import annotations

from dataclasses import dataclass, field
import json
import re


DEFAULT_ANGLICISM_PRONUNCIATIONS: dict[str, str] = {
    "GitHub": "/ɡˈɪthʌb/",
    "pull request": "/pˈʊl ɹɪkwˈɛst/",
    "README": "/ɹˈiːdmi/",
    "API": "/ˌeɪ piː ˈaɪ/",
    "JSON": "/ˈdʒeɪsən/",
    "Docker": "/dˈɑkɚ/",
    "commit": "/kəmˈɪt/",
    "branch": "/bɹˈæntʃ/",
    "fork": "/fˈɔɹk/",
    "login": "/lˈɑɡɪn/",
    "token": "/tˈoʊkən/",
    "repo": "/ɹˈiːpoʊ/",
}


@dataclass(frozen=True)
class SpeechScript:
    display_text: str
    speech_text: str
    source: str = "fallback"
    style: str = "neutral"
    degradation_reason: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


def summarize_for_speech(text: str, max_chars: int = 240) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 1:
        return "…"
    return normalized[: max_chars - 1].rstrip() + "…"


def parse_speech_response(text: str) -> SpeechScript:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return prepare_speech_script(text)
    if not isinstance(payload, dict):
        return prepare_speech_script(text)
    display_text = payload.get("display_text")
    speech_text = payload.get("speech_text")
    if not isinstance(display_text, str) or not isinstance(speech_text, str) or not speech_text.strip():
        return prepare_speech_script(text)
    speech_language = payload.get("speech_language", "")
    speech_source = payload.get("speech_source", "pi-router")
    metadata = {}
    if isinstance(speech_language, str) and speech_language:
        metadata["speech_language"] = speech_language
    return SpeechScript(
        display_text=display_text,
        speech_text=_rewrite_anglicisms(speech_text, DEFAULT_ANGLICISM_PRONUNCIATIONS),
        source=speech_source if isinstance(speech_source, str) and speech_source else "pi-router",
        metadata=metadata,
    )


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
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda match: match.group(0) if _is_kokoro_pronunciation_url(match.group(2)) else match.group(1), text)
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


def _rewrite_anglicisms(text: str, pronunciations: dict[str, str]) -> str:
    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"@@ROGER_KOKORO_PRON_{len(protected) - 1}@@"

    result = re.sub(r"\[[^\]]+\]\(/[^)]+/\)", protect, text)
    for term in sorted(pronunciations, key=len, reverse=True):
        pronunciation = pronunciations[term]
        result = re.sub(
            rf"(?<![\w/.[-]){re.escape(term)}(?![\w/\]-])",
            lambda match: _kokoro_pronunciation_markup(match.group(0), pronunciation),
            result,
            flags=re.IGNORECASE,
        )
    for index, original in enumerate(protected):
        result = result.replace(f"@@ROGER_KOKORO_PRON_{index}@@", original)
    return result


def _kokoro_pronunciation_markup(term: str, pronunciation: str) -> str:
    phonemes = pronunciation if _is_kokoro_pronunciation_url(pronunciation) else f"/{pronunciation.strip('/')}/"
    return f"[{term}]({phonemes})"


def _is_kokoro_pronunciation_url(value: str) -> bool:
    return value.startswith("/") and value.endswith("/") and len(value) > 2


def _normalize_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text
