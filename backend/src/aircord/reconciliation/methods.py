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

