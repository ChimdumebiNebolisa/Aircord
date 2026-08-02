from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SnapshotReference:
    uri: str
    local_path: Path | None
    immutable: bool = True


def create_snapshot_reference(source: str, identifier: str, base_dir: Path | None = None) -> SnapshotReference:
    if base_dir:
        return SnapshotReference(f"s3://aircord-raw/{source}/{identifier}", base_dir / source / identifier)
    return SnapshotReference(f"s3://aircord-raw/{source}/{identifier}", None)

