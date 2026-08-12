from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class ScoreResult:
    score: float
    features: dict[str, float]

    @property
    def features_json(self) -> str:
        return json.dumps(self.features, sort_keys=True)


def _float_or_none(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def score_live_pair(
    sensor_reading: dict[str, Any],
    monitor: dict[str, Any],
    *,
    likely_indoor: bool = False,
    now: datetime | None = None,
) -> ScoreResult:
    """Score one live PurpleAir reading against one AirNow reference.

    The comparison is a transparent heuristic for trust weighting. It is not
    an accuracy claim because PM2.5 concentration and AQI are different units.
    """
    pm25 = _float_or_none(sensor_reading.get("pm25_cf1"))
    if pm25 is None:
        pm25 = _float_or_none(sensor_reading.get("pm25_atm"))
    monitor_aqi = _float_or_none(monitor.get("latest_aqi"))
    channel_a = _float_or_none(sensor_reading.get("channel_a"))
    channel_b = _float_or_none(sensor_reading.get("channel_b"))

    missing_fields = sum(
        value is None
        for value in (pm25, monitor_aqi, channel_a, channel_b, sensor_reading.get("observed_at"))
    )
    missingness_score = _clamp(1.0 - missing_fields / 5.0)
    if pm25 is None or monitor_aqi is None:
        absolute_difference = 0.0
        agreement_score = 0.0
    else:
        absolute_difference = abs(pm25 - monitor_aqi)
        agreement_score = _clamp(1.0 - absolute_difference / max(abs(monitor_aqi), 50.0))

    if pm25 is None or channel_a is None or channel_b is None:
        channel_agreement_score = 0.0
    else:
        channel_agreement_score = _clamp(
            1.0 - abs(channel_a - channel_b) / max(abs(pm25), 1.0)
        )

    observed_at = _parse_time(sensor_reading.get("observed_at"))
    captured_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age_minutes = None if observed_at is None else max(0.0, (captured_at - observed_at).total_seconds() / 60.0)
    freshness_score = 0.0 if age_minutes is None else _clamp(1.0 - age_minutes / (24.0 * 60.0))
    indoor_hint_score = 1.0 if likely_indoor else 0.0
    drift_score = 0.0
    score = (
        agreement_score * 0.40
        + channel_agreement_score * 0.20
        + freshness_score * 0.20
        + missingness_score * 0.15
        + (1.0 - indoor_hint_score) * 0.05
    )
    features = {
        "absolute_difference": round(absolute_difference, 4),
        "agreement_score": round(agreement_score, 4),
        "channel_agreement_score": round(channel_agreement_score, 4),
        "freshness_score": round(freshness_score, 4),
        "missingness_score": round(missingness_score, 4),
        "drift_score": drift_score,
        "indoor_hint_score": indoor_hint_score,
        "age_minutes": round(age_minutes, 2) if age_minutes is not None else -1.0,
    }
    return ScoreResult(round(_clamp(score), 4), features)


def score_sensor_from_rows(rows: list[dict[str, Any]], monitor_aqi: float) -> ScoreResult:
    if not rows:
        return ScoreResult(0.0, {name: 0.0 for name in (
            "agreement_score", "channel_agreement_score", "uptime_score",
            "humidity_sensitivity_score", "volatility_score", "drift_score", "indoor_hint_score"
        )})
    values = [float(row["pm25_cf1"]) for row in rows]
    agreements = [abs(value - monitor_aqi) / max(monitor_aqi, 50.0) for value in values]
    channel_deltas = [abs(float(row["channel_a"]) - float(row["channel_b"])) / max(abs(float(row["pm25_cf1"])), 1.0) for row in rows]
    volatility = statistics.pstdev(values) if len(values) > 1 else 0.0
    latest = values[-1]
    baseline = statistics.mean(values[: max(1, len(values) // 2)])
    drift = abs(latest - baseline) / max(abs(monitor_aqi), 50.0)
    humidity = statistics.mean(float(row["humidity"]) for row in rows)
    likely_indoor = 1.0 if humidity >= 75.0 else 0.0
    features = {
        "agreement_score": _clamp(1.0 - statistics.mean(agreements)),
        "channel_agreement_score": _clamp(1.0 - statistics.mean(channel_deltas) * 2.0),
        "uptime_score": 1.0,
        "humidity_sensitivity_score": _clamp(1.0 - abs(humidity - 50.0) / 60.0),
        "volatility_score": _clamp(1.0 - volatility / 35.0),
        "drift_score": _clamp(drift),
        "indoor_hint_score": likely_indoor,
    }
    score = (
        features["agreement_score"] * 0.35
        + features["channel_agreement_score"] * 0.20
        + features["uptime_score"] * 0.10
        + features["humidity_sensitivity_score"] * 0.10
        + features["volatility_score"] * 0.10
        + (1.0 - features["drift_score"]) * 0.10
        + (1.0 - features["indoor_hint_score"]) * 0.05
    )
    return ScoreResult(round(_clamp(score), 4), {key: round(value, 4) for key, value in features.items()})


def sensor_weight_multiplier(decision: str, features: dict[str, float]) -> float:
    """Return the deliberately small multiplier applied to reputation.

    Trusted sensors keep their reputation as weight, ordinary downweighted
    sensors use half of it, drifted sensors use one quarter, and ignored
    sensors contribute zero.
    """
    if decision == "ignored":
        return 0.0
    if decision == "downweighted":
        return 0.25 if features.get("drift_score", 0.0) > 0.25 else 0.5
    return 1.0


def sensor_weight_for_decision(
    reputation_score: float,
    decision: str,
    features: dict[str, float],
) -> float:
    """Map a reputation score to the persisted sensor weight.

    Formula: ``sensor_weight = reputation_score * multiplier``. The result is
    rounded to four decimals, so reputation ``0.3973`` with an ordinary
    downweighted decision becomes ``0.3973 * 0.5 = 0.1986``.
    """
    return round(float(reputation_score) * sensor_weight_multiplier(decision, features), 4)


def decision_for_score(score: float, features: dict[str, float], likely_indoor: bool = False) -> tuple[str, float, list[str]]:
    reasons: list[str] = []
    if features.get("channel_agreement_score", 1.0) < 0.75:
        reasons.append("channel_divergence")
    if features.get("agreement_score", 1.0) < 0.7:
        reasons.append("monitor_disagreement")
    if features.get("drift_score", 0.0) > 0.25:
        reasons.append("drift")
    if likely_indoor or features.get("indoor_hint_score", 0.0) > 0.8:
        reasons.append("likely_indoor")
    if score < 0.3 or likely_indoor or features.get("indoor_hint_score", 0.0) > 0.8:
        decision = "ignored"
        return decision, sensor_weight_for_decision(score, decision, features), reasons or ["insufficient_reputation"]
    if score < 0.85 or features.get("drift_score", 0.0) > 0.25:
        decision = "downweighted"
        return decision, sensor_weight_for_decision(score, decision, features), reasons or ["mixed_evidence"]
    decision = "trusted"
    return decision, sensor_weight_for_decision(score, decision, features), reasons or ["consistent_history"]
