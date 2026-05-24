from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WakeBenchmarkResult:
    architecture: str
    false_positives_per_hour: float
    false_negative_rate: float
    p95_latency_ms: float
    idle_cpu_percent: float
    rss_mb: float
    training_duration_seconds: float | None = None


@dataclass(frozen=True)
class WakeArchitectureSelection:
    architecture: str | None
    requires_fallback: bool
    reason: str


@dataclass(frozen=True)
class WakeSelectionThresholds:
    max_false_positives_per_hour: float = 0.25
    max_false_negative_rate: float = 0.05
    max_p95_latency_ms: float = 500.0
    max_idle_cpu_percent: float = 10.0
    max_rss_mb: float = 512.0


def select_wake_architecture(
    results: list[WakeBenchmarkResult],
    thresholds: WakeSelectionThresholds = WakeSelectionThresholds(),
) -> WakeArchitectureSelection:
    passing = [result for result in results if _passes(result, thresholds)]
    if not passing:
        return WakeArchitectureSelection(
            architecture=None,
            requires_fallback=True,
            reason="No NanoWakeWord architecture met false-positive, false-negative, latency, CPU, and memory thresholds.",
        )

    best = min(
        passing,
        key=lambda result: (
            result.false_negative_rate,
            result.false_positives_per_hour,
            result.p95_latency_ms,
            result.idle_cpu_percent,
            result.rss_mb,
        ),
    )
    return WakeArchitectureSelection(
        architecture=best.architecture,
        requires_fallback=False,
        reason=(
            f"Selected {best.architecture}: false_negative_rate={best.false_negative_rate}, "
            f"false_positives_per_hour={best.false_positives_per_hour}, "
            f"p95_latency_ms={best.p95_latency_ms}."
        ),
    )


def _passes(result: WakeBenchmarkResult, thresholds: WakeSelectionThresholds) -> bool:
    return (
        result.false_positives_per_hour <= thresholds.max_false_positives_per_hour
        and result.false_negative_rate <= thresholds.max_false_negative_rate
        and result.p95_latency_ms <= thresholds.max_p95_latency_ms
        and result.idle_cpu_percent <= thresholds.max_idle_cpu_percent
        and result.rss_mb <= thresholds.max_rss_mb
    )
