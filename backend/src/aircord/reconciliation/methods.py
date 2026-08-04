from __future__ import annotations

from statistics import mean
from typing import Iterable


def raw_estimate(values: Iterable[float]) -> float:
    values = list(values)
    return round(mean(values), 1) if values else 0.0


def static_correction_estimate(values: Iterable[float]) -> float:
    """A transparent fixed correction baseline, not a claim to reproduce EPA's exact equation."""
    return round(raw_estimate(values) * 0.75, 1)


def trust_weighted_estimate(values_and_weights: Iterable[tuple[float, float]]) -> float:
    pairs = [(value, weight) for value, weight in values_and_weights if weight > 0]
    total_weight = sum(weight for _value, weight in pairs)
    return round(sum(value * weight for value, weight in pairs) / total_weight, 1) if total_weight else 0.0


def reference_blended_estimate(
    sensor_value: float | None,
    reference_value: float | None,
    sensor_weight: float,
) -> tuple[float, str]:
    """Blend a sensor proxy with its reference without silently defaulting to zero."""
    if sensor_value is None and reference_value is None:
        raise ValueError("both sensor and reference values are missing")
    if sensor_value is None:
        return round(reference_value, 1), "sensor value missing; used reference fallback"
    if reference_value is None:
        return round(sensor_value, 1), "reference value missing; used sensor proxy"

    weight = max(0.0, min(1.0, float(sensor_weight)))
    estimate = sensor_value * weight + reference_value * (1.0 - weight)
    return round(estimate, 1), f"sensor weight={weight:.4f}, reference weight={1.0 - weight:.4f}"

