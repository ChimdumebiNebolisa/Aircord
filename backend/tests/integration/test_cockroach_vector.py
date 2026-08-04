from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from aircord.db.repositories import Repository


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_cockroach_vector_round_trip_and_similarity():
    repository = Repository(backend="cockroach")
    repository.ensure_vector_schema()
    suffix = uuid4().hex[:10]
    target = f"test-vector-target-{suffix}"
    neighbor = f"test-vector-neighbor-{suffix}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        repository.upsert_sensor_embedding(
            target,
            [0.4, 0.1, 0.2, 0.0, 0.9, 0.2, 0.0, 0.7],
            {"source": "test", "reputation_score": 0.4},
            now,
        )
        repository.upsert_sensor_embedding(
            neighbor,
            [0.41, 0.1, 0.2, 0.0, 0.9, 0.2, 0.0, 0.7],
            {"source": "test", "reputation_score": 0.41},
            now,
        )

        rows = repository.similar_sensor_embeddings(
            [0.4, 0.1, 0.2, 0.0, 0.9, 0.2, 0.0, 0.7],
            exclude_sensor_id=target,
            limit=1,
        )

        assert rows[0]["sensor_id"] == neighbor
        assert float(rows[0]["cosine_distance"]) >= 0.0
    finally:
        with repository.transaction() as transaction:
            transaction.execute(
                "DELETE FROM sensor_embeddings WHERE sensor_id IN (?, ?)",
                (target, neighbor),
            )
