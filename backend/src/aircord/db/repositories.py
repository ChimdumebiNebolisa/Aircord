from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aircord.config import DB_PATH
from aircord.db.session import connect


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class Repository:
    def __init__(self, path: Path = DB_PATH):
        self.path = path

    def one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with connect(self.path) as connection:
            return _dict(connection.execute(query, params).fetchone())

    def many(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with connect(self.path) as connection:
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def active_cluster(self) -> dict[str, Any] | None:
        return self.one("SELECT * FROM clusters ORDER BY cluster_id LIMIT 1")

    def cells(self) -> list[dict[str, Any]]:
        return self.many(
            """
            SELECT c.*, e.estimated_aqi, e.confidence, e.claim_status, e.updated_at AS estimate_updated_at
            FROM cells c LEFT JOIN estimates e ON e.estimate_id = (
              SELECT estimate_id FROM estimates e2 WHERE e2.cell_id = c.cell_id ORDER BY updated_at DESC LIMIT 1
            ) ORDER BY c.cell_id
            """
        )

    def cell(self, cell_id: str) -> dict[str, Any] | None:
        return self.one("SELECT * FROM cells WHERE cell_id = ?", (cell_id,))

    def cell_readings(self, cell_id: str) -> list[dict[str, Any]]:
        return self.many(
            """
            SELECT r.*, s.name, s.likely_indoor, rep.reputation_score, rep.features_json
            FROM sensor_readings r
            JOIN sensors s ON s.sensor_id = r.sensor_id
            LEFT JOIN reputations rep ON rep.sensor_id = r.sensor_id
            WHERE r.cell_id = ? AND r.observed_at = (SELECT MAX(r2.observed_at) FROM sensor_readings r2 WHERE r2.cell_id = ?)
            ORDER BY r.sensor_id
            """,
            (cell_id, cell_id),
        )

    def latest_estimate(self, cell_id: str) -> dict[str, Any] | None:
        return self.one(
            "SELECT * FROM estimates WHERE cell_id = ? ORDER BY updated_at DESC LIMIT 1", (cell_id,)
        )

    def latest_resolution(self, cell_id: str) -> dict[str, Any] | None:
        return self.one(
            "SELECT * FROM resolutions WHERE cell_id = ? ORDER BY committed_at DESC LIMIT 1", (cell_id,)
        )

    def resolution_sensors(self, resolution_id: str) -> list[dict[str, Any]]:
        return self.many(
            "SELECT * FROM resolution_sensors WHERE resolution_id = ? ORDER BY weight DESC",
            (resolution_id,),
        )

    def sensor_reputation(self, sensor_id: str) -> dict[str, Any] | None:
        row = self.one(
            """
            SELECT s.sensor_id, s.name, s.cell_id, s.status, s.likely_indoor,
                   rep.reputation_score, rep.features_json, rep.evidence_start, rep.evidence_end
            FROM sensors s LEFT JOIN reputations rep ON rep.sensor_id = s.sensor_id
            WHERE s.sensor_id = ?
            """,
            (sensor_id,),
        )
        if row and row.get("features_json"):
            row["features"] = json.loads(row.pop("features_json"))
        return row

    def affected_estimates(self, sensor_id: str) -> list[str]:
        return [
            row["cell_id"]
            for row in self.many(
                """
                SELECT DISTINCT r.cell_id FROM resolution_sensors rs
                JOIN resolutions r ON r.resolution_id = rs.resolution_id
                WHERE rs.sensor_id = ? ORDER BY r.committed_at DESC
                """,
                (sensor_id,),
            )
        ]

    def readings_for_backtest(self, cluster_id: str) -> list[dict[str, Any]]:
        return self.many(
            """
            SELECT r.*, s.name, s.likely_indoor, rep.reputation_score,
                   m.aqi AS reference_aqi, m.observed_at AS monitor_observed_at
            FROM sensor_readings r
            JOIN sensors s ON s.sensor_id = r.sensor_id
            JOIN monitor_readings m ON m.cell_id = r.cell_id AND m.observed_at = r.observed_at
            LEFT JOIN reputations rep ON rep.sensor_id = r.sensor_id
            JOIN clusters c ON c.cluster_id = s.cluster_id
            WHERE c.cluster_id = ? ORDER BY r.observed_at, r.cell_id, r.sensor_id
            """,
            (cluster_id,),
        )

    def latest_backtest(self) -> dict[str, Any] | None:
        return self.one("SELECT * FROM backtest_runs ORDER BY created_at DESC LIMIT 1")

    def backtest_summaries(self, run_id: str) -> list[dict[str, Any]]:
        return self.many(
            "SELECT * FROM backtest_summaries WHERE backtest_run_id = ? ORDER BY segment, method",
            (run_id,),
        )

