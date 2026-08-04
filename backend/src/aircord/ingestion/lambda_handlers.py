from __future__ import annotations

from typing import Any

from aircord.db.repositories import Repository
from aircord.ingestion.purpleair import PurpleAirClient
from aircord.ingestion.purpleair_ingest import ingest_sensor
from aircord.ingestion.snapshots import RawSnapshotStore


def purpleair_ingest_handler(
    event: dict[str, Any] | None,
    context: Any | None,
    *,
    client: PurpleAirClient | None = None,
    snapshot_store: RawSnapshotStore | None = None,
    repository: Repository | None = None,
) -> dict[str, str]:
    """Run the existing PurpleAir ingestion path as an AWS Lambda handler."""
    del event, context
    result = ingest_sensor(
        client=client,
        snapshot_store=snapshot_store,
        repository=repository,
    )
    return {
        "sensor_id": result.sensor_id,
        "s3_key": result.snapshot_key,
        "reading_id": result.reading_id,
        "audit_id": result.audit_id,
    }
