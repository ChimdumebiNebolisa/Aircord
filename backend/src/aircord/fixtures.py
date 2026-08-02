from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from aircord.config import DB_PATH, REFERENCE_CAVEAT, MEDICAL_DIRECTIVE_CAVEAT
from aircord.db.session import connect, ensure_db
from aircord.reputation.fingerprints import fingerprint_from_features
from aircord.reputation.scoring import score_sensor_from_rows


BASE_TIME = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def seed_demo(path: Path = DB_PATH, *, force: bool = False) -> None:
    ensure_db(path)
    with connect(path) as connection:
        if connection.execute("SELECT 1 FROM clusters LIMIT 1").fetchone() and not force:
            return
        if force:
            for table in (
                "backtest_summaries", "backtest_runs", "resolution_sensors", "resolutions",
                "estimates", "audit_log", "sensor_embeddings", "reputations", "sensor_readings",
                "monitor_readings", "sensors", "monitors", "cells", "clusters",
            ):
                connection.execute(f"DELETE FROM {table}")
        connection.execute(
            "INSERT INTO clusters VALUES (?, ?, ?, ?, ?, ?)",
            (
                "greater-la",
                "Greater Los Angeles (fixture cluster)",
                "passed",
                "Fixture Gate A passed: paired monitor/sensor disagreement and degraded candidates are present. Live Gate A still requires scoped AirNow and PurpleAir credentials.",
                34.05,
                -118.25,
            ),
        )
        cells = [
            ("cell-culver", 34.021, -118.396),
            ("cell-pasadena", 34.148, -118.144),
            ("cell-santa-monica", 34.019, -118.491),
        ]
        for cell_id, lat, lon in cells:
            connection.execute(
                "INSERT INTO cells VALUES (?, ?, ?, ?, 0, ?)",
                (cell_id, "greater-la", lat, lon, _iso(BASE_TIME)),
            )
        monitors = [
            ("monitor-culver", "cell-culver", "Culver City regulatory reference", 121),
            ("monitor-pasadena", "cell-pasadena", "Pasadena regulatory reference", 86),
            ("monitor-santa-monica", "cell-santa-monica", "Santa Monica regulatory reference", 97),
        ]
        for monitor_id, cell_id, name, aqi in monitors:
            cell = next(item for item in cells if item[0] == cell_id)
            connection.execute(
                "INSERT INTO monitors VALUES (?, ?, ?, ?, ?, ?, ?)",
                (monitor_id, "greater-la", name, cell[1], cell[2], aqi, _iso(BASE_TIME)),
            )

        sensors = [
            ("sensor-healthy", "North Culver / healthy", "cell-culver", 103, 104, 102, 42, 0),
            ("sensor-drifted", "South Culver / drifted", "cell-culver", 176, 188, 163, 55, 0),
            ("sensor-indoor", "Living Room / likely indoor", "cell-culver", 211, 215, 207, 82, 1),
            ("sensor-pasadena", "Pasadena community", "cell-pasadena", 91, 92, 90, 46, 0),
            ("sensor-santa", "Santa Monica community", "cell-santa-monica", 101, 100, 102, 49, 0),
        ]
        for sensor_id, name, cell_id, value, channel_a, channel_b, humidity, indoor in sensors:
            cell = next(item for item in cells if item[0] == cell_id)
            connection.execute(
                "INSERT INTO sensors VALUES (?, ?, ?, ?, ?, ?, 'active', ?, 0, ?)",
                (sensor_id, "greater-la", name, cell[1] + 0.004, cell[2] + 0.004, cell_id, indoor, _iso(BASE_TIME)),
            )
            for index in range(12):
                timestamp = BASE_TIME - timedelta(hours=11 - index)
                monitor_aqi = next(item[3] for item in monitors if item[1] == cell_id)
                if sensor_id == "sensor-drifted":
                    historical_value = monitor_aqi + 12 + index * 3
                    historical_a = historical_value + 8
                    historical_b = historical_value - 8
                elif sensor_id == "sensor-indoor":
                    historical_value = monitor_aqi + 38
                    historical_a = historical_value + 4
                    historical_b = historical_value - 4
                else:
                    historical_value = monitor_aqi + ((index % 3) - 1) * 3
                    historical_a = historical_value + 1
                    historical_b = historical_value - 1
                connection.execute(
                    "INSERT INTO sensor_readings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"{sensor_id}-{index}", sensor_id, cell_id, _iso(timestamp),
                        historical_value if index < 11 else value,
                        historical_a if index < 11 else channel_a,
                        historical_b if index < 11 else channel_b,
                        humidity, 24.0, -45.0, f"fixture://purpleair/{sensor_id}/{index}",
                    ),
                )
        for monitor_id, cell_id, _name, current_aqi in monitors:
            for index in range(12):
                timestamp = BASE_TIME - timedelta(hours=11 - index)
                variation = ((index % 4) - 1) * 4
                connection.execute(
                    "INSERT INTO monitor_readings VALUES (?, ?, ?, ?, ?)",
                    (f"{monitor_id}-{index}", monitor_id, cell_id, _iso(timestamp), current_aqi + variation),
                )

        for sensor_id, _name, _cell_id, _value, _a, _b, _humidity, _indoor in sensors:
            rows = [
                dict(row) for row in connection.execute(
                    "SELECT * FROM sensor_readings WHERE sensor_id = ? ORDER BY observed_at", (sensor_id,)
                ).fetchall()
            ]
            cell_id = rows[0]["cell_id"]
            monitor_row = connection.execute(
                "SELECT latest_aqi FROM monitors WHERE monitor_id = (SELECT monitor_id FROM monitor_readings WHERE cell_id = ? LIMIT 1)",
                (cell_id,),
            ).fetchone()
            result = score_sensor_from_rows(rows, float(monitor_row[0]))
            connection.execute(
                "INSERT INTO reputations VALUES (?, ?, ?, ?, ?, 0, ?)",
                (
                    sensor_id, result.score, result.features_json, rows[0]["observed_at"], rows[-1]["observed_at"],
                    _iso(BASE_TIME),
                ),
            )
            connection.execute(
                "INSERT INTO sensor_embeddings VALUES (?, ?, ?)",
                (sensor_id, fingerprint_from_features(result.features), _iso(BASE_TIME)),
            )
        connection.commit()


def reset_demo(path: Path = DB_PATH) -> None:
    seed_demo(path, force=True)

