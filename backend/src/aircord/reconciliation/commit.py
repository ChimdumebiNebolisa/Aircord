from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aircord.config import DB_PATH, MEDICAL_DIRECTIVE_CAVEAT, REFERENCE_CAVEAT
from aircord.db.models import CandidateEstimate
from aircord.db.repositories import Repository


class VersionConflict(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def commit_candidate(path: Path, candidate: CandidateEstimate) -> str:
    """Commit estimate, resolution, reputation state, and audit atomically."""
    now = _now()
    estimate_id = f"estimate-{uuid4().hex[:12]}"
    resolution_id = f"resolution-{uuid4().hex[:12]}"
    with Repository(path).transaction() as transaction:
        current = transaction.one("SELECT version FROM cells WHERE cell_id = ?", (candidate.cell_id,))
        if not current or int(current["version"]) != candidate.cell_version:
            raise VersionConflict(f"Cell {candidate.cell_id} changed while reasoning was in progress")
        transaction.execute(
            "INSERT INTO estimates VALUES (?, ?, ?, ?, ?, ?)",
            (estimate_id, candidate.cell_id, candidate.estimated_aqi, candidate.confidence, candidate.claim_status, now),
        )
        transaction.execute(
            "INSERT INTO resolutions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                resolution_id, estimate_id, candidate.cell_id, candidate.rationale,
                json.dumps(candidate.confidence_factors), json.dumps(candidate.monitor_context),
                REFERENCE_CAVEAT, MEDICAL_DIRECTIVE_CAVEAT, now,
            ),
        )
        for decision, reputation in zip(candidate.decisions, candidate.reputations, strict=True):
            transaction.execute(
                "INSERT INTO resolution_sensors VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    resolution_id, decision.sensor_id, decision.reading_id, decision.weight,
                    decision.decision, json.dumps(decision.reason_codes), decision.reputation_score,
                ),
            )
            transaction.execute(
                "UPDATE reputations SET reputation_score = ?, features_json = ?, version = version + 1, updated_at = ? WHERE sensor_id = ?",
                (reputation.reputation_score, json.dumps(reputation.features), now, reputation.sensor_id),
            )
            transaction.store_fingerprint(reputation.sensor_id, reputation.features, now)
            transaction.create_audit_log(
                "reconciler",
                "reputation_updated",
                "sensor",
                reputation.sensor_id,
                reason="Updated from current paired evidence",
                created_at=now,
            )
        transaction.execute(
            "UPDATE cells SET version = version + 1, updated_at = ? WHERE cell_id = ?",
            (now, candidate.cell_id),
        )
        transaction.create_audit_log(
            "reconciler",
            "estimate_committed",
            "cell",
            candidate.cell_id,
            reason=candidate.rationale,
            created_at=now,
        )
    return estimate_id

