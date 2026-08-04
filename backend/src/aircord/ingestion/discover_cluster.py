from __future__ import annotations

import argparse
import math
from typing import Any

from aircord.config import DB_PATH, MODE
from aircord.db.repositories import Repository
from aircord.fixtures import seed_demo
from aircord.ingestion.airnow import AirNowClient
from aircord.ingestion.purpleair import PurpleAirClient


CLUSTER_BOUNDS = {
    # west, south, east, north
    "greater-la": (-118.8, 33.6, -117.6, 34.35),
}


def _number(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _latest_by(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        existing = latest.get(str(value))
        if existing is None or str(row.get("observed_at")) > str(existing.get("observed_at")):
            latest[str(value)] = row
    return list(latest.values())


def _distance_km(first: dict[str, Any], second: dict[str, Any]) -> float | None:
    lat1, lon1 = _number(first.get("latitude")), _number(first.get("longitude"))
    lat2, lon2 = _number(second.get("latitude")), _number(second.get("longitude"))
    if None in (lat1, lon1, lat2, lon2):
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def _discover_live(cluster_id: str) -> dict[str, Any]:
    bounds = CLUSTER_BOUNDS.get(cluster_id)
    if bounds is None:
        raise ValueError(f"No live bounds configured for cluster: {cluster_id}")

    monitors = _latest_by(AirNowClient().fetch(bounds), "monitor_id")
    sensors = PurpleAirClient().fetch(bounds)
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for monitor in monitors:
        nearby = [
            sensor
            for sensor in sensors
            if (_distance_km(monitor, sensor) or float("inf")) <= 5.0
            and _number(sensor.get("pm25_cf1")) is not None
        ]
        pairs.extend((monitor, sensor) for sensor in nearby)

    disagreement_pairs = 0
    degraded_sensor_ids: set[str] = set()
    for monitor, sensor in pairs:
        monitor_pm25 = _number(monitor.get("pm25"))
        sensor_pm25 = _number(sensor.get("pm25_cf1"))
        channel_a = _number(sensor.get("channel_a_pm25"))
        channel_b = _number(sensor.get("channel_b_pm25"))
        if monitor_pm25 is not None and sensor_pm25 is not None and abs(sensor_pm25 - monitor_pm25) >= 5.0:
            disagreement_pairs += 1
        if sensor.get("likely_indoor") or (
            channel_a is not None and channel_b is not None and abs(channel_a - channel_b) >= 5.0
        ):
            degraded_sensor_ids.add(str(sensor["sensor_id"]))

    status = "passed" if len(pairs) >= 3 and disagreement_pairs > 0 and degraded_sensor_ids else "failed"
    return {
        "cluster_id": cluster_id,
        "mode": "live",
        "gate_a_status": status,
        "paired_anchor_count": len(pairs),
        "monitor_count": len(monitors),
        "sensor_count": len(sensors),
        "disagreement_pair_count": disagreement_pairs,
        "degraded_sensor_candidate_count": len(degraded_sensor_ids),
        "notes": (
            f"Live Gate A: {len(monitors)} monitors, {len(sensors)} sensors, "
            f"{len(pairs)} nearby pairs, {disagreement_pairs} disagreement pairs, "
            f"{len(degraded_sensor_ids)} degraded candidates."
        ),
    }


def discover(cluster_id: str = "greater-la") -> dict:
    if MODE == "live":
        return _discover_live(cluster_id)

    seed_demo(DB_PATH)
    repository = Repository(DB_PATH)
    cluster = repository.one("SELECT * FROM clusters WHERE cluster_id = ?", (cluster_id,))
    if not cluster:
        raise ValueError(f"Unknown cluster: {cluster_id}")
    anchors = repository.many(
        "SELECT DISTINCT sensor_id FROM sensor_readings WHERE cell_id IN (SELECT cell_id FROM cells WHERE cluster_id = ?)",
        (cluster_id,),
    )
    return {
        "cluster_id": cluster_id,
        "mode": MODE,
        "gate_a_status": cluster["gate_a_status"],
        "paired_anchor_count": len(anchors),
        "notes": cluster["gate_a_notes"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster", default="greater-la")
    args = parser.parse_args()
    print(discover(args.cluster))


if __name__ == "__main__":
    main()

