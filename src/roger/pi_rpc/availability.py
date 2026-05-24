from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from typing import Callable, Any
from urllib.error import URLError
from urllib.request import urlopen


class ModelAvailabilityMode(StrEnum):
    ONLINE = "online"
    OFFLINE_FALLBACK = "offline-fallback"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ModelAvailabilityDecision:
    mode: ModelAvailabilityMode
    reason: str


class ModelAvailabilityPolicy:
    def __init__(
        self,
        explicit_offline: bool = False,
        automatic_fallback: bool = True,
        fallback_enabled: bool = True,
        online_probe: Callable[[], bool] | None = None,
    ):
        self.explicit_offline = explicit_offline
        self.automatic_fallback = automatic_fallback
        self.fallback_enabled = fallback_enabled
        self.online_probe = online_probe

    def decide(self) -> ModelAvailabilityDecision:
        if self.explicit_offline:
            if not self.fallback_enabled:
                return ModelAvailabilityDecision(ModelAvailabilityMode.UNAVAILABLE, "explicit offline requested but fallback disabled")
            return ModelAvailabilityDecision(ModelAvailabilityMode.OFFLINE_FALLBACK, "explicit offline mode requested")

        if not self.automatic_fallback:
            return ModelAvailabilityDecision(ModelAvailabilityMode.ONLINE, "automatic fallback disabled; using online default")

        if self.online_probe is not None and not self.online_probe():
            if not self.fallback_enabled:
                return ModelAvailabilityDecision(ModelAvailabilityMode.UNAVAILABLE, "online unavailable and fallback disabled")
            return ModelAvailabilityDecision(ModelAvailabilityMode.OFFLINE_FALLBACK, "online unavailable before dispatch")

        return ModelAvailabilityDecision(ModelAvailabilityMode.ONLINE, "online provider selected")

    def should_retry_offline(self, error: Exception) -> bool:
        return self.automatic_fallback and self.fallback_enabled and is_provider_availability_error(error)


_PROVIDER_AVAILABILITY_MARKERS = (
    "network",
    "provider unavailable",
    "provider error",
    "connection refused",
    "connection reset",
    "timed out",
    "timeout",
    "dns",
    "eai_again",
    "enotfound",
    "fetch failed",
    "authentication failed",
    "api key",
)


def is_provider_availability_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in _PROVIDER_AVAILABILITY_MARKERS)


def make_http_online_probe(url: str, timeout_seconds: float = 2.0, urlopen_fn: Callable[..., Any] = urlopen) -> Callable[[], bool]:
    def probe() -> bool:
        try:
            with urlopen_fn(url, timeout=timeout_seconds) as response:
                return getattr(response, "status", 200) < 500
        except (OSError, URLError):
            return False

    return probe


def probe_llama_cpp_fallback(
    base_url: str | None,
    model: str | None,
    timeout_seconds: float = 2.0,
    urlopen_fn: Callable[..., Any] = urlopen,
) -> str | None:
    if not base_url:
        return None
    url = base_url.rstrip("/") + "/models"
    try:
        with urlopen_fn(url, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                return f"llama.cpp server unavailable at {base_url}: HTTP {status}"
            payload = response.read() if hasattr(response, "read") else b""
    except (OSError, URLError) as error:
        return f"llama.cpp server unavailable at {base_url}: {error}"

    if model and payload:
        try:
            data = json.loads(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        model_ids = _extract_model_names(data)
        if not any(_model_name_matches_configured_alias(name, model) for name in model_ids):
            return f"llama.cpp fallback model not found: {model}"
    return None


def _extract_model_names(data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in ("data", "models"):
        for item in data.get(key, []):
            if not isinstance(item, dict):
                continue
            for field in ("id", "name", "model"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    names.add(value)
    return names


def _model_name_matches_configured_alias(served_name: str, configured_model: str) -> bool:
    served = served_name.lower().removesuffix(".gguf")
    configured = configured_model.lower().removesuffix(".gguf")
    return served == configured or served.startswith(configured + "-") or served.startswith(configured + "_")
