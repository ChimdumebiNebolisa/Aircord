from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
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
        return "ignored", 0.0, reasons or ["insufficient_reputation"]
    if score < 0.85 or features.get("drift_score", 0.0) > 0.25:
        multiplier = 0.25 if features.get("drift_score", 0.0) > 0.25 else 0.5
        return "downweighted", round(score * multiplier, 4), reasons or ["mixed_evidence"]
    return "trusted", round(score, 4), reasons or ["consistent_history"]
