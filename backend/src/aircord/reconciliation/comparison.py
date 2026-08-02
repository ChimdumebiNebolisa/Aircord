from __future__ import annotations

import json
from pathlib import Path

from aircord.db.repositories import Repository
from aircord.reconciliation.methods import raw_estimate, static_correction_estimate, trust_weighted_estimate
from aircord.reputation.scoring import decision_for_score


def compare_cell(path: Path, cell_id: str) -> dict:
    repository = Repository(path)
    readings = repository.cell_readings(cell_id)
    values = [float(row["pm25_cf1"]) for row in readings]
    weighted = []
    for row in readings:
        score = float(row.get("reputation_score") or 0.0)
        _decision, weight, _reasons = decision_for_score(
            score,
            json.loads(row.get("features_json") or "{}"),
            bool(row.get("likely_indoor")),
        )
        weighted.append((float(row["pm25_cf1"]), weight))
    return {
        "raw_estimate": raw_estimate(values),
        "static_correction_estimate": static_correction_estimate(values),
        "aircord_estimate": trust_weighted_estimate(weighted),
    }
