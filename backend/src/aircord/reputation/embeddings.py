from __future__ import annotations

import json
from pathlib import Path

from aircord.db.session import connect
from aircord.reputation.fingerprints import fingerprint_distance


def store_fingerprint(path: Path, sensor_id: str, features: dict[str, float], updated_at: str) -> None:
    with connect(path) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO sensor_embeddings VALUES (?, ?, ?)",
            (sensor_id, json.dumps(features, sort_keys=True), updated_at),
        )
        connection.commit()


def self_similarity_distance(current: dict[str, float], previous: dict[str, float]) -> float:
    """Local equivalent of the production vector-index distance query."""
    return round(fingerprint_distance(current, previous), 6)

