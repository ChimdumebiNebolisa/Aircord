from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import boto3


@dataclass(frozen=True)
class SnapshotReference:
    uri: str
    local_path: Path | None
    immutable: bool = True


class RawSnapshotStore(Protocol):
    def put_json(self, key: str, payload: Any) -> SnapshotReference:
        ...


class S3SnapshotStore:
    def __init__(self, bucket: str, region: str, client: Any | None = None):
        if not bucket:
            raise ValueError("S3_BUCKET is required for raw snapshot storage")
        if not region:
            raise ValueError("AWS_REGION is required for raw snapshot storage")
        self.bucket = bucket
        self.region = region
        self.client = client or boto3.client("s3", region_name=region)

    def put_json(self, key: str, payload: Any) -> SnapshotReference:
        normalized_key = key.lstrip("/")
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.client.put_object(
            Bucket=self.bucket,
            Key=normalized_key,
            Body=body,
            ContentType="application/json",
        )
        return SnapshotReference(f"s3://{self.bucket}/{normalized_key}", None)


def create_snapshot_reference(
    source: str,
    identifier: str,
    base_dir: Path | None = None,
    bucket: str = "aircord-raw",
) -> SnapshotReference:
    if base_dir:
        return SnapshotReference(f"s3://{bucket}/{source}/{identifier}", base_dir / source / identifier)
    return SnapshotReference(f"s3://{bucket}/{source}/{identifier}", None)

