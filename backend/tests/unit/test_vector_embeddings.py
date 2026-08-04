from datetime import datetime, timezone

from aircord.reputation.vector import VECTOR_FEATURE_ORDER, build_behavioral_fingerprint, vector_literal


def test_behavioral_fingerprint_has_named_eight_dimension_features():
    vector, features = build_behavioral_fingerprint(
        {"reputation_score": 0.4, "drift_score": 0.1},
        {
            "pm25_cf1": 12.0,
            "channel_a": 12.0,
            "channel_b": 14.0,
            "observed_at": "2026-08-04T22:00:00Z",
        },
        {"latest_aqi": 30.0},
        confidence=0.7,
        now=datetime(2026, 8, 4, 22, 5, tzinfo=timezone.utc),
    )

    assert len(vector) == 8
    assert tuple(features) == VECTOR_FEATURE_ORDER
    assert features["reputation_score"] == 0.4
    assert features["missingness_indicator"] == 0.0
    assert vector_literal(vector).startswith("[")
    assert vector_literal(vector).count(",") == 7


def test_behavioral_fingerprint_marks_missing_values_without_zero_claim():
    vector, features = build_behavioral_fingerprint(
        {"reputation_score": 0.4},
        {"pm25_cf1": None, "channel_a": None, "channel_b": None, "observed_at": None},
        {"latest_aqi": 30.0},
    )

    assert len(vector) == 8
    assert features["missingness_indicator"] == 1.0
    assert features["recent_pm25"] == 0.0
