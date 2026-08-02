from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aircord.db.session import transaction


def write_audit(path: Path, actor: str, action: str, entity_type: str, entity_id: str, reason: str) -> None:
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with transaction(path) as connection:
        connection.execute(
            "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"audit-{uuid4().hex[:12]}", actor, action, entity_type, entity_id, None, reason, created_at),
        )

