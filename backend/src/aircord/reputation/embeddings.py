from __future__ import annotations

from pathlib import Path

from aircord.db.repositories import Repository
from aircord.reputation.fingerprints import fingerprint_distance


def store_fingerprint(path: Path, sensor_id: str, features: dict[str, float], updated_at: str) -> None:
    Repository(path).store_fingerprint(sensor_id, features, updated_at)


def self_similarity_distance(current: dict[str, float], previous: dict[str, float]) -> float:
    """Local equivalent of the production vector-index distance query."""
    return round(fingerprint_distance(current, previous), 6)

