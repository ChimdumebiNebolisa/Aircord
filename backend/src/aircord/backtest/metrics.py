from __future__ import annotations

import statistics
from typing import Iterable


MIN_METRIC_SAMPLES = 3


def absolute_errors(predictions: Iterable[float], references: Iterable[float]) -> list[float]:
    prediction_values = list(predictions)
    reference_values = list(references)
    if len(prediction_values) != len(reference_values):
        raise ValueError("predictions and references must have the same length")
    return [abs(prediction - reference) for prediction, reference in zip(prediction_values, reference_values, strict=True)]


def summarize_errors(
    errors: Iterable[float],
    *,
    min_samples: int = MIN_METRIC_SAMPLES,
) -> dict[str, float | int | None]:
    values = list(errors)
    summary: dict[str, float | int | None] = {
        "observation_count": len(values),
        "mean_absolute_error": None,
        "median_absolute_error": None,
    }
    if len(values) < min_samples:
        return summary
    summary["mean_absolute_error"] = round(statistics.mean(values), 2)
    summary["median_absolute_error"] = round(statistics.median(values), 2)
    return summary
