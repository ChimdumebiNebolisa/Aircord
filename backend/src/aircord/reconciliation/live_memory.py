from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aircord.db.repositories import Repository
from aircord.reputation.scoring import decision_for_score, score_live_pair


@dataclass(frozen=True)
class MemoryLoopResult:
    sensor_id: str
    monitor_id: str
    cell_id: str
    reading_id: str
    reputation_score: float
    decision: str
    weight: float
    estimate_aqi: float
    confidence: float
    confidence_label: str
    resolution_id: str
    reputation_audit_id: str
    resolution_audit_id: str
    features: dict[str, Any]
    reasoning_text: str


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _reference_blended_estimate(
    pm25: float | None,
    monitor_aqi: float | None,
    sensor_weight: float,
) -> tuple[float, str]:
    """Build an explicit estimate without turning missing inputs into zero.

    PurpleAir PM2.5 and AirNow AQI are different units, so this remains a
    transparent cross-source proxy rather than a validated AQI claim. The
    monitor is the reference component, and the sensor's reputation weight
    controls how much the PurpleAir value can move the estimate.
    """
    if pm25 is None and monitor_aqi is None:
        raise RuntimeError("Cannot compute an estimate: both PurpleAir PM2.5 and AirNow AQI are missing")
    if pm25 is None:
        return round(monitor_aqi, 1), "PurpleAir PM2.5 was missing; used the AirNow monitor AQI as an explicit fallback"
    if monitor_aqi is None:
        return round(pm25, 1), "AirNow monitor AQI was missing; used the PurpleAir PM2.5 proxy without a reference blend"

    weight = max(0.0, min(1.0, float(sensor_weight)))
    estimate = (pm25 * weight) + (monitor_aqi * (1.0 - weight))
    return round(estimate, 1), (
        f"Blended PurpleAir PM2.5 proxy at weight {weight:.4f} with the AirNow "
        f"monitor AQI at weight {1.0 - weight:.4f}"
    )


def _confidence_label(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def run_memory_loop(
    sensor_id: str | None = None,
    *,
    monitor: dict[str, Any] | None = None,
    repository: Repository | None = None,
    now: datetime | None = None,
) -> MemoryLoopResult:
    sensor_id = sensor_id or os.getenv("PURPLEAIR_SENSOR_ID")
    if not sensor_id:
        raise RuntimeError("PURPLEAIR_SENSOR_ID is required for the memory loop")
    repository = repository or Repository(backend="cockroach")

    sensor = repository.read_sensor(str(sensor_id))
    if not sensor:
        raise RuntimeError(f"Sensor is not present in CockroachDB: {sensor_id}")
    reading = repository.one(
        "SELECT * FROM sensor_readings WHERE sensor_id = ? ORDER BY observed_at DESC LIMIT 1",
        (str(sensor_id),),
    )
    if not reading:
        raise RuntimeError(f"No sensor reading is present in CockroachDB: {sensor_id}")

    if monitor is None:
        monitor = repository.one(
            "SELECT * FROM monitors ORDER BY observed_at DESC NULLS LAST, updated_at DESC LIMIT 1"
        )
    if not monitor:
        raise RuntimeError("No AirNow monitor is present in CockroachDB")
    monitor = dict(monitor)
    if monitor.get("latest_aqi") is None and monitor.get("aqi") is not None:
        monitor["latest_aqi"] = monitor["aqi"]

    captured_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    score = score_live_pair(
        reading,
        monitor,
        likely_indoor=bool(sensor.get("likely_indoor", sensor.get("indoor_flag", False))),
        now=captured_at,
    )
    decision, weight, reasons = decision_for_score(
        score.score,
        score.features,
        likely_indoor=bool(sensor.get("likely_indoor", sensor.get("indoor_flag", False))),
    )
    pm25 = _number(reading.get("pm25_cf1"))
    if pm25 is None:
        pm25 = _number(reading.get("pm25_atm"))
    monitor_aqi = _number(monitor.get("latest_aqi"))
    estimate_aqi, estimate_basis = _reference_blended_estimate(pm25, monitor_aqi, weight)

    confidence = round(
        min(1.0, 0.25 + score.score * 0.5 + score.features["freshness_score"] * 0.15 + score.features["missingness_score"] * 0.1),
        3,
    )
    confidence_label = _confidence_label(confidence)
    cell_id = f"greater-la-sensor-{sensor_id}"
    monitor_id = str(monitor["monitor_id"])
    reading_id = str(reading["reading_id"])
    resolution_sensors = [
        {
            "sensor_id": str(sensor_id),
            "reading_id": reading_id,
            "monitor_id": monitor_id,
            "weight": weight,
            "decision": decision,
            "reputation_score": score.score,
            "reason_codes": reasons,
        }
    ]
    reasoning_text = (
        f"Considered PurpleAir sensor {sensor_id} against AirNow monitor {monitor_id}. "
        f"Assigned reputation {score.score:.4f}, decision={decision}, weight={weight:.4f}, "
        f"and {confidence_label} confidence. "
        f"Estimate basis: {estimate_basis}. "
        "The stored estimate is a transparent cross-source proxy, not a validated AQI claim. "
        f"Reasons: {', '.join(reasons)}."
    )
    with repository.transaction() as transaction:
        updated_sensor = transaction.update_sensor_reputation(
            str(sensor_id),
            score.score,
            score.features,
            channel_agreement_score=score.features["channel_agreement_score"],
            drift_score=score.features["drift_score"],
            evidence_start=reading.get("observed_at"),
            evidence_end=reading.get("observed_at"),
        )
        transaction.upsert_cell_estimate(cell_id, estimate_aqi, confidence)
        resolution = transaction.create_resolution(
            cell_id,
            estimate_aqi,
            confidence,
            reasoning_text,
            resolution_sensors,
        )
        reputation_audit = transaction.create_audit_log(
            "aircord_memory",
            "reputation_updated",
            "sensor",
            str(sensor_id),
            details={
                "sensor_id": str(sensor_id),
                "monitor_id": monitor_id,
                "reputation_score": score.score,
                "features": score.features,
                "decision": decision,
                "weight": weight,
                "reading_id": reading_id,
            },
        )
        resolution_audit = transaction.create_audit_log(
            "aircord_memory",
            "resolution_created",
            "resolution",
            str(resolution["resolution_id"]),
            details={
                "cell_id": cell_id,
                "sensor_id": str(sensor_id),
                "monitor_id": monitor_id,
                "estimate_aqi": estimate_aqi,
                "confidence": confidence,
                "confidence_label": confidence_label,
                "estimate_basis": estimate_basis,
                "reasoning_text": reasoning_text,
            },
        )

    if updated_sensor is None:
        raise RuntimeError(f"Sensor reputation update did not affect sensor: {sensor_id}")
    return MemoryLoopResult(
        sensor_id=str(sensor_id),
        monitor_id=monitor_id,
        cell_id=cell_id,
        reading_id=reading_id,
        reputation_score=score.score,
        decision=decision,
        weight=weight,
        estimate_aqi=estimate_aqi,
        confidence=confidence,
        confidence_label=confidence_label,
        resolution_id=str(resolution["resolution_id"]),
        reputation_audit_id=str(reputation_audit["audit_id"]),
        resolution_audit_id=str(resolution_audit["audit_id"]),
        features=score.features,
        reasoning_text=reasoning_text,
    )
