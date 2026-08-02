from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aircord.db.models import CandidateEstimate, ReputationState, SensorDecision
from aircord.db.repositories import Repository
from aircord.reconciliation.methods import trust_weighted_estimate
from aircord.reputation.scoring import decision_for_score


def compute_cell_candidate(path: Path, cell_id: str) -> CandidateEstimate:
    """Compute the candidate with no open database transaction or remote call."""
    repository = Repository(path)
    cell = repository.cell(cell_id)
    if not cell:
        raise ValueError(f"Unknown cell: {cell_id}")
    readings = repository.cell_readings(cell_id)
    if not readings:
        return CandidateEstimate(
            cell_id, int(cell["version"]), 0.0, 0.0, "insufficient_data",
            "There are no current supporting sensor readings for this cell.",
            {"sensor_count": 0, "monitor_reference_present": False}, {}, [], [],
        )
    decisions: list[SensorDecision] = []
    reputations: list[ReputationState] = []
    for reading in readings:
        score = float(reading.get("reputation_score") or 0.0)
        features = json.loads(reading.get("features_json") or "{}")
        decision, weight, reasons = decision_for_score(score, features, bool(reading["likely_indoor"]))
        decisions.append(SensorDecision(reading["sensor_id"], reading["reading_id"], weight, decision, reasons, score))
        reputations.append(
            ReputationState(
                reading["sensor_id"], score, features,
                ("2026-07-31T01:00:00Z", reading["observed_at"]), 0,
            )
        )
    weighted = trust_weighted_estimate(
        (float(reading["pm25_cf1"]), decision.weight)
        for reading, decision in zip(readings, decisions, strict=True)
    )
    monitor = repository.one(
        "SELECT latest_aqi, name, observed_at FROM monitors WHERE cluster_id = (SELECT cluster_id FROM cells WHERE cell_id = ?) LIMIT 1",
        (cell_id,),
    )
    total_weight = sum(decision.weight for decision in decisions)
    confidence = min(1.0, round(0.45 + min(total_weight / max(len(decisions), 1), 1.0) * 0.45 + (0.1 if monitor else 0.0), 3))
    trusted = sum(1 for decision in decisions if decision.decision == "trusted")
    downweighted = sum(1 for decision in decisions if decision.decision == "downweighted")
    ignored = sum(1 for decision in decisions if decision.decision == "ignored")
    rationale = (
        f"Aircord weighted {trusted} trusted, {downweighted} downweighted, and {ignored} ignored sensor(s). "
        "The estimate reflects persistent per-sensor reputation, including channel agreement and drift evidence. "
        "The nearest regulatory monitor is a reference for comparison, not absolute ground truth."
    )
    return CandidateEstimate(
        cell_id=cell_id,
        cell_version=int(cell["version"]),
        estimated_aqi=weighted,
        confidence=confidence,
        claim_status="pending_backtest",
        rationale=rationale,
        confidence_factors={
            "sensor_count": len(readings),
            "trusted_count": trusted,
            "downweighted_count": downweighted,
            "ignored_count": ignored,
            "total_weight": round(total_weight, 4),
            "monitor_reference_present": bool(monitor),
        },
        monitor_context=monitor or {},
        decisions=decisions,
        reputations=reputations,
    )

