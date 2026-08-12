import json

from aircord.db.repositories import Repository
from aircord.reputation.fingerprints import fingerprint_distance
from aircord.reputation.scoring import (
    decision_for_score,
    score_sensor_from_rows,
    sensor_weight_for_decision,
)


def test_drifted_sensor_has_explainable_features(demo_db):
    repository = Repository(demo_db)
    row = repository.one("SELECT * FROM sensor_readings WHERE sensor_id = 'sensor-drifted' ORDER BY observed_at DESC")
    rows = repository.many("SELECT * FROM sensor_readings WHERE sensor_id = 'sensor-drifted' ORDER BY observed_at")
    result = score_sensor_from_rows(rows, 121)
    decision, weight, reasons = decision_for_score(result.score, result.features)
    assert result.features["drift_score"] > 0.25
    assert decision == "downweighted"
    assert weight < result.score
    assert "drift" in reasons
    assert json.loads(result.features_json)["agreement_score"] < 1
    assert row["pm25_cf1"] > 150


def test_fingerprint_distance_is_zero_for_same_behavior():
    features = {"agreement_score": 0.9, "channel_agreement_score": 0.8}
    assert fingerprint_distance(features, features) == 0


def test_downweighted_sensor_weight_formula_is_explicit():
    assert sensor_weight_for_decision(0.3973, "downweighted", {"drift_score": 0.0}) == 0.1986
    assert sensor_weight_for_decision(0.3973, "downweighted", {"drift_score": 0.3}) == 0.0993
    assert sensor_weight_for_decision(0.91, "trusted", {"drift_score": 0.0}) == 0.91
    assert sensor_weight_for_decision(0.91, "ignored", {"drift_score": 0.0}) == 0.0

