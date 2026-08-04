from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aircord.db.repositories import Repository


def write_audit(path: Path, actor: str, action: str, entity_type: str, entity_id: str, reason: str) -> None:
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    Repository(path).create_audit_log(
        actor,
        action,
        entity_type,
        entity_id,
        reason=reason,
        created_at=created_at,
    )

