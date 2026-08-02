from __future__ import annotations

import json
import math
from typing import Mapping


FEATURE_ORDER = (
    "agreement_score",
    "channel_agreement_score",
    "uptime_score",
    "humidity_sensitivity_score",
    "volatility_score",
    "drift_score",
    "indoor_hint_score",
)


def fingerprint_from_features(features: Mapping[str, float]) -> str:
    return json.dumps([round(float(features.get(name, 0.0)), 6) for name in FEATURE_ORDER])


def fingerprint_distance(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    values = [float(left.get(name, 0.0)) - float(right.get(name, 0.0)) for name in FEATURE_ORDER]
    return math.sqrt(sum(value * value for value in values) / len(values))

