from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from psycopg import sql  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402

from aircord.db.connection import connect_database  # noqa: E402


TABLES = ("sensors", "sensor_readings", "audit_log")
NOW = datetime.now(timezone.utc)


def _columns(cursor, table: str) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT column_name, data_type, udt_name, is_nullable, column_default, is_generated
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    rows = cursor.fetchall()
    if not rows:
        raise RuntimeError(f"Required table not found: {table}")
    return [
        {
            "name": row[0],
            "data_type": row[1],
            "udt_name": row[2],
            "nullable": row[3] == "YES",
            "default": row[4],
            "generated": row[5] == "ALWAYS",
        }
        for row in rows
    ]


def _is_uuid(column: dict[str, Any]) -> bool:
    return column["data_type"] == "uuid" or column["udt_name"] == "uuid"


def _id_value(column: dict[str, Any], logical_id: uuid.UUID, prefix: str) -> Any:
    return logical_id if _is_uuid(column) else f"{prefix}-{logical_id.hex[:12]}"


def _typed_fallback(column: dict[str, Any]) -> Any:
    data_type = column["data_type"]
    if data_type == "boolean":
        return False
    if data_type in {"smallint", "integer", "bigint"}:
        return 0
    if data_type in {"real", "double precision", "numeric", "decimal"}:
        return 0.0
    if data_type in {"json", "jsonb"}:
        return Jsonb({})
    if data_type.startswith("timestamp") or data_type == "date":
        return NOW
    if data_type == "time without time zone":
        return NOW.time()
    return "cockroach-smoke"


def _value_for(
    table: str,
    column: dict[str, Any],
    sensor_id: uuid.UUID,
    reading_id: uuid.UUID,
    audit_id: uuid.UUID,
) -> Any:
    name = column["name"].lower()
    if name in {"sensor_id", "sensorid"}:
        return _id_value(column, sensor_id, "smoke-sensor")
    if name in {"reading_id", "readingid"}:
        return _id_value(column, reading_id, "smoke-reading")
    if name in {"audit_id", "auditid"}:
        return _id_value(column, audit_id, "smoke-audit")
    if name in {"id", f"{table[:-1]}_id"}:
        logical_id = sensor_id if table == "sensors" else reading_id if table == "sensor_readings" else audit_id
        prefix = table[:-1] if table.endswith("s") else table
        return _id_value(column, logical_id, f"smoke-{prefix}")
    if name in {"name", "sensor_name"}:
        return "aircord-cockroach-smoke"
    if name in {"latitude", "lat"}:
        return 34.02
    if name in {"longitude", "lon", "lng"}:
        return -118.40
    if name in {"status", "state"}:
        return "active"
    if name in {"observed_at", "created_at", "updated_at", "ingested_at", "last_seen_at"}:
        return NOW
    if name in {"pm25", "pm25_cf1", "pm25_atm", "value", "reading_value"}:
        return 12.34
    if name in {"channel_a", "channel_a_pm25", "channel_a_value"}:
        return 12.0
    if name in {"channel_b", "channel_b_pm25", "channel_b_value"}:
        return 13.0
    if name in {"humidity", "relative_humidity"}:
        return 45.0
    if name in {"temperature", "temp"}:
        return 72.0
    if name == "rssi":
        return -50.0
    if name in {"raw_ref", "source_snapshot_uri", "source_uri"}:
        return "smoke://cockroachdb/aircord"
    if name in {"actor", "agent"}:
        return "cockroach_smoke"
    if name in {"action", "event_type", "event"}:
        return "smoke_insert"
    if name in {"entity_type", "resource_type"}:
        return "sensor"
    if name in {"entity_id", "resource_id"}:
        return _id_value(column, sensor_id, "smoke-sensor")
    if name in {"reason", "message", "description"}:
        return "CockroachDB write/read smoke test"
    if name in {"before_version", "after_version", "version"}:
        return 0 if name != "after_version" else 1
    return _typed_fallback(column)


def _insert_and_read(cursor, table: str, values: dict[str, Any], key_name: str) -> None:
    names = list(values)
    statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(name) for name in names),
        sql.SQL(", ").join(sql.Placeholder() for _ in names),
    )
    cursor.execute(statement, [values[name] for name in names])
    cursor.execute(
        sql.SQL("SELECT 1 FROM {} WHERE {} = %s").format(
            sql.Identifier(table), sql.Identifier(key_name)
        ),
        (values[key_name],),
    )
    if cursor.fetchone() is None:
        raise RuntimeError(f"Inserted row could not be read back from {table}")


def main() -> None:
    sensor_id = uuid.uuid4()
    reading_id = uuid.uuid4()
    audit_id = uuid.uuid4()
    try:
        with connect_database() as connection:
            with connection.cursor() as cursor:
                table_columns = {table: _columns(cursor, table) for table in TABLES}
                for table, columns in table_columns.items():
                    values = {
                        column["name"]: _value_for(table, column, sensor_id, reading_id, audit_id)
                        for column in columns
                        if not column["generated"]
                        and (
                            column["default"] is None
                            or column["name"].lower()
                            in {"sensor_id", "sensorid", "reading_id", "readingid", "audit_id", "auditid", "id"}
                        )
                    }
                    key_name = next(
                        (
                            name
                            for name in ("sensor_id", "reading_id", "audit_id", "id")
                            if name in values
                        ),
                        None,
                    )
                    if key_name is None:
                        raise RuntimeError(f"No smoke-test identifier column found in {table}")
                    _insert_and_read(cursor, table, values, key_name)
            connection.rollback()
        print("CockroachDB write/read smoke succeeded: sensors=1, sensor_readings=1, audit_log=1 (rolled back)")
    except Exception as exc:
        raise SystemExit(f"CockroachDB write/read smoke failed: {type(exc).__name__}") from exc


if __name__ == "__main__":
    main()
