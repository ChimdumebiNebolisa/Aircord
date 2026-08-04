from __future__ import annotations

import json
from pathlib import Path

from aircord.db.repositories import Repository
from aircord.reconciliation.comparison import compare_cell


def degraded_showcase(path: Path) -> dict | None:
    repository = Repository(path)
    candidates = repository.many(
        """
        SELECT s.sensor_id, s.name, s.cell_id, rep.reputation_score, rep.features_json,
               e.estimated_aqi AS aircord_estimate
        FROM sensors s
        JOIN reputations rep ON rep.sensor_id = s.sensor_id
        LEFT JOIN estimates e ON e.estimate_id = (
          SELECT estimate_id FROM estimates e2 WHERE e2.cell_id = s.cell_id ORDER BY e2.updated_at DESC LIMIT 1
        )
        ORDER BY rep.reputation_score ASC
        """
    )
    row = next(
        (
            candidate
            for candidate in candidates
            if float(candidate.get("reputation_score") or 0.0) < 0.85
            or float(json.loads(candidate.get("features_json") or "{}").get("drift_score") or 0.0) > 0.25
        ),
        None,
    )
    if not row:
        return None
    comparison = compare_cell(path, row["cell_id"])
    return {
        "sensor_id": row["sensor_id"],
        "sensor_name": row["name"],
        "cell_id": row["cell_id"],
        "raw_or_static_estimate": comparison["static_correction_estimate"],
        "aircord_estimate": comparison["aircord_estimate"],
        "reputation_score": row["reputation_score"],
        "reputation_reason": "Remembered monitor disagreement, channel divergence, and drift lowered this sensor's contribution.",
    }
