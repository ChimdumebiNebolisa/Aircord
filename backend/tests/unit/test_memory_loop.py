from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from aircord.reconciliation.live_memory import run_memory_loop
from aircord.reconciliation.readback import build_memory_readback, format_memory_readback
from aircord.reputation.scoring import score_live_pair


class FakeTransaction:
    def __init__(self):
        self.reputation = None
        self.estimate = None
        self.resolution = None
        self.audits = []

    def update_sensor_reputation(self, sensor_id, reputation_score, features, **kwargs):
        self.reputation = {
            "sensor_id": sensor_id,
            "reputation_score": reputation_score,
            "features": features,
        }
        return self.reputation

    def upsert_cell_estimate(self, cell_id, estimate_aqi, confidence):
        self.estimate = {
            "cell_id": cell_id,
            "estimate_aqi": estimate_aqi,
            "confidence": confidence,
        }
        return self.estimate

    def create_resolution(self, cell_id, estimate_aqi, confidence, reasoning_text, sensors_considered, **kwargs):
        self.resolution = {
            "resolution_id": "resolution-live",
            "cell_id": cell_id,
            "estimate_aqi": estimate_aqi,
            "confidence": confidence,
            "reasoning_text": reasoning_text,
            "sensors_considered": sensors_considered,
        }
        return self.resolution

    def create_audit_log(self, actor, action, entity_type, entity_id, **kwargs):
        audit = {
            "audit_id": f"audit-{len(self.audits) + 1}",
            "actor": actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": kwargs["details"],
        }
        self.audits.append(audit)
        return audit


class FakeRepository:
    def __init__(self):
        self.transaction_value = FakeTransaction()
        self.now = datetime(2026, 8, 4, 21, 5, tzinfo=timezone.utc)
        self.reading = {
            "reading_id": "reading-live",
            "sensor_id": "54917",
            "pm25_cf1": 12.0,
            "pm25_atm": 11.0,
            "channel_a": 12.0,
            "channel_b": 12.2,
            "humidity": 45.0,
            "observed_at": "2026-08-04T21:00:00Z",
        }
        self.monitor = {
            "monitor_id": "060370001",
            "latest_aqi": 12.0,
            "observed_at": "2026-08-04T21:00:00Z",
        }

    def read_sensor(self, sensor_id):
        return {"sensor_id": sensor_id, "name": "CCA", "likely_indoor": False}

    def one(self, query, params=()):
        if "sensor_readings" in query:
            return self.reading
        return self.monitor

    @contextmanager
    def transaction(self):
        yield self.transaction_value


def test_score_live_pair_includes_difference_freshness_and_missingness():
    result = score_live_pair(
        {
            "pm25_cf1": 20.0,
            "channel_a": 20.0,
            "channel_b": 24.0,
            "observed_at": "2026-08-04T21:00:00Z",
        },
        {"latest_aqi": 30.0},
        now=datetime(2026, 8, 4, 21, 5, tzinfo=timezone.utc),
    )

    assert result.features["absolute_difference"] == 10.0
    assert result.features["freshness_score"] > 0.9
    assert result.features["missingness_score"] > 0.5
    assert 0.0 <= result.score <= 1.0


def test_memory_loop_updates_reputation_estimate_resolution_and_audit():
    repository = FakeRepository()

    result = run_memory_loop(
        "54917",
        repository=repository,
        now=repository.now,
    )

    transaction = repository.transaction_value
    assert result.monitor_id == "060370001"
    assert transaction.reputation["sensor_id"] == "54917"
    assert transaction.estimate["cell_id"] == "greater-la-sensor-54917"
    assert transaction.resolution["resolution_id"] == "resolution-live"
    assert [audit["action"] for audit in transaction.audits] == [
        "reputation_updated",
        "resolution_created",
    ]
    assert "not a validated AQI claim" in result.reasoning_text


def test_non_null_purpleair_pm_is_not_replaced_by_zero_and_blends_reference():
    repository = FakeRepository()
    repository.reading["pm25_cf1"] = 12.0
    repository.reading["pm25_atm"] = 11.0
    repository.monitor["latest_aqi"] = 64.0

    result = run_memory_loop("54917", repository=repository, now=repository.now)

    assert result.estimate_aqi > 0.0
    assert result.estimate_aqi < 64.0
    assert "Blended PurpleAir PM2.5 proxy" in result.reasoning_text


def test_downweighted_zero_pm_sensor_moves_estimate_toward_monitor_instead_of_zero():
    repository = FakeRepository()
    repository.reading.update(pm25_cf1=0.0, pm25_atm=0.0, channel_a=0.0, channel_b=0.9)
    repository.monitor["latest_aqi"] = 64.0

    result = run_memory_loop("54917", repository=repository, now=repository.now)

    assert result.decision == "downweighted"
    assert result.estimate_aqi > 0.0
    assert result.estimate_aqi < 64.0
    assert repository.transaction_value.estimate["estimate_aqi"] == result.estimate_aqi


def test_missing_purpleair_pm_uses_explicit_monitor_fallback_and_reasoning():
    repository = FakeRepository()
    repository.reading.update(pm25_cf1=None, pm25_atm=None, channel_a=None, channel_b=None)
    repository.monitor["latest_aqi"] = 64.0

    result = run_memory_loop("54917", repository=repository, now=repository.now)

    assert result.estimate_aqi == 64.0
    assert "PM2.5 was missing" in result.reasoning_text
    assert "explicit fallback" in result.reasoning_text
    assert "PM2.5 was missing" in repository.transaction_value.resolution["reasoning_text"]


def test_missing_purpleair_pm_and_monitor_fail_instead_of_defaulting_to_zero():
    repository = FakeRepository()
    repository.reading.update(pm25_cf1=None, pm25_atm=None)
    repository.monitor["latest_aqi"] = None

    try:
        run_memory_loop("54917", repository=repository, now=repository.now)
    except RuntimeError as exc:
        assert "both PurpleAir PM2.5 and AirNow AQI are missing" in str(exc)
    else:
        raise AssertionError("missing inputs must not silently produce a zero estimate")


class FakeReadbackRepository:
    def read_sensor(self, sensor_id):
        return {"sensor_id": sensor_id, "name": "CCA"}

    def one(self, query, params=()):
        if "sensor_readings" in query:
            return {"reading_id": "reading-live", "pm25_cf1": 12.0, "observed_at": "now"}
        return {"monitor_id": "060370001", "latest_aqi": 12.0, "observed_at": "now"}

    def sensor_reputation(self, sensor_id):
        return {"sensor_id": sensor_id, "reputation_score": 0.97, "channel_agreement_score": 0.99, "drift_score": 0.0}

    def latest_estimate(self, cell_id):
        return {"cell_id": cell_id, "estimate_aqi": 12.0, "confidence": 0.9}

    def latest_resolution(self, cell_id):
        return {
            "resolution_id": "resolution-live",
            "reasoning_text": "trusted recent reading",
            "sensors_considered": [{
                "sensor_id": "54917",
                "decision": "trusted",
                "reputation_score": 0.97,
            }],
        }

    def many(self, query, params=()):
        return [{"created_at": "now", "actor": "aircord_memory", "action": "resolution_created", "entity_type": "resolution", "entity_id": "resolution-live"}]


def test_memory_readback_is_judge_readable():
    output = format_memory_readback(build_memory_readback("54917", repository=FakeReadbackRepository()))

    assert "Aircord memory readback" in output
    assert "sensor reputation: score=0.97" in output
    assert "sensor weight formula: weight = reputation * multiplier; 0.9700 * 1.00 = 0.9700" in output
    assert "trusted recent reading" in output
    assert "resolution_created" in output
