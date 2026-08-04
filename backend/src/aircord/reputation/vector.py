from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


VECTOR_FEATURE_ORDER = (
    "reputation_score",
    "channel_a_b_difference",
    "recent_pm25",
    "missingness_indicator",
    "freshness_score",
    "absolute_difference_from_monitor",
    "drift_score",
    "confidence",
)


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def build_behavioral_fingerprint(
    sensor: Mapping[str, Any],
    reading: Mapping[str, Any] | None,
    monitor: Mapping[str, Any] | None,
    *,
    confidence: float | None = None,
    score_features: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> tuple[list[float], dict[str, float]]:
    """Build a small, explainable vector; this is not a trained embedding."""
    reading = reading or {}
    monitor = monitor or {}
    score_features = score_features or {}
    pm25 = _number(reading.get("pm25_cf1"))
    if pm25 is None:
        pm25 = _number(reading.get("pm25_atm"))
    channel_a = _number(reading.get("channel_a"))
    channel_b = _number(reading.get("channel_b"))
    monitor_aqi = _number(monitor.get("latest_aqi", monitor.get("aqi")))
    observed_at = _parse_time(reading.get("observed_at"))
    captured_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    channel_difference = 0.0 if channel_a is None or channel_b is None else abs(channel_a - channel_b) / max(abs(pm25 or 0.0), 1.0)
    freshness = _number(score_features.get("freshness_score"))
    if freshness is None:
        age_minutes = None if observed_at is None else max(0.0, (captured_at - observed_at).total_seconds() / 60.0)
        freshness = 0.0 if age_minutes is None else _clamp(1.0 - age_minutes / (24.0 * 60.0))
    absolute_difference = 0.0 if pm25 is None or monitor_aqi is None else abs(pm25 - monitor_aqi) / max(abs(monitor_aqi), 50.0)
    missingness = 1.0 if any(value is None for value in (pm25, channel_a, channel_b, observed_at)) else 0.0
    features = {
        "reputation_score": _clamp(_number(sensor.get("reputation_score")) or 0.0),
        "channel_a_b_difference": _clamp(channel_difference),
        "recent_pm25": _clamp((pm25 or 0.0) / 200.0),
        "missingness_indicator": missingness,
        "freshness_score": _clamp(freshness),
        "absolute_difference_from_monitor": _clamp(absolute_difference),
        "drift_score": _clamp(_number(score_features.get("drift_score", sensor.get("drift_score"))) or 0.0),
        "confidence": _clamp(_number(confidence) or 0.0),
    }
    return [features[name] for name in VECTOR_FEATURE_ORDER], features


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.6f}" for value in vector) + "]"
