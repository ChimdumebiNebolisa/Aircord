from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence
from uuid import uuid4

from psycopg.types.json import Jsonb

from aircord.config import DB_PATH
from aircord.db.connection import connect_database, database_url_configured
from aircord.db.session import connect as connect_sqlite


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _adapt_sql(query: str) -> str:
    """Translate the existing qmark SQL used by local fixtures for psycopg."""
    return query.replace("?", "%s")


class Repository:
    """Stable data-access interface with SQLite and CockroachDB backends."""

    backend = "unknown"

    def __new__(cls, path: Path = DB_PATH, *, backend: str | None = None):
        if cls is not Repository:
            return super().__new__(cls)
        selected = backend or ("cockroach" if database_url_configured() else "sqlite")
        concrete = {
            "sqlite": SQLiteRepository,
            "cockroach": CockroachRepository,
        }.get(selected)
        if concrete is None:
            raise ValueError(f"Unsupported repository backend: {selected}")
        return object.__new__(concrete)

    def __init__(self, path: Path = DB_PATH, *, backend: str | None = None):
        self.path = path

    def _new_connection(self):
        if self.backend == "cockroach":
            return connect_database()
        return connect_sqlite(self.path)

    @contextmanager
    def transaction(self, *, rollback: bool = False) -> Iterator[RepositoryTransaction]:
        connection = self._new_connection()
        try:
            if self.backend == "sqlite":
                connection.execute("BEGIN IMMEDIATE")
            yield RepositoryTransaction(self, connection)
            if rollback:
                connection.rollback()
            else:
                connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _fetch(self, connection, query: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        if self.backend == "cockroach":
            with connection.cursor() as cursor:
                cursor.execute(_adapt_sql(query), tuple(params))
                if cursor.description is None:
                    return []
                columns = [getattr(column, "name", column[0]) for column in cursor.description]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        cursor = connection.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def _execute(self, connection, query: str, params: Sequence[Any] = ()) -> None:
        if self.backend == "cockroach":
            with connection.cursor() as cursor:
                cursor.execute(_adapt_sql(query), tuple(params))
            return
        connection.execute(query, tuple(params))

    def _execute_returning(
        self, connection, query: str, params: Sequence[Any] = ()
    ) -> dict[str, Any] | None:
        if self.backend == "cockroach":
            with connection.cursor() as cursor:
                cursor.execute(_adapt_sql(query), tuple(params))
                row = cursor.fetchone()
                if row is None or cursor.description is None:
                    return None
                columns = [getattr(column, "name", column[0]) for column in cursor.description]
                return dict(zip(columns, row, strict=True))
        cursor = connection.execute(query, tuple(params))
        return _dict(cursor.fetchone())

    def _one_on(self, connection, query: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
        rows = self._fetch(connection, query, params)
        return rows[0] if rows else None

    def _many_on(self, connection, query: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return self._fetch(connection, query, params)

    def one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.one(query, params)

    def many(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.transaction() as transaction:
            return transaction.many(query, params)

    def active_cluster(self) -> dict[str, Any] | None:
        return self.one("SELECT * FROM clusters ORDER BY cluster_id LIMIT 1")

    def cells(self) -> list[dict[str, Any]]:
        return self.many(
            """
            SELECT c.*, e.estimated_aqi, e.confidence, e.claim_status, e.updated_at AS estimate_updated_at
            FROM cells c LEFT JOIN estimates e ON e.estimate_id = (
              SELECT estimate_id FROM estimates e2 WHERE e2.cell_id = c.cell_id ORDER BY updated_at DESC LIMIT 1
            ) ORDER BY c.cell_id
            """
        )

    def cell(self, cell_id: str) -> dict[str, Any] | None:
        return self.one("SELECT * FROM cells WHERE cell_id = ?", (cell_id,))

    def cell_readings(self, cell_id: str) -> list[dict[str, Any]]:
        return self.many(
            """
            SELECT r.*, s.name, s.likely_indoor, rep.reputation_score, rep.features_json
            FROM sensor_readings r
            JOIN sensors s ON s.sensor_id = r.sensor_id
            LEFT JOIN reputations rep ON rep.sensor_id = r.sensor_id
            WHERE r.cell_id = ? AND r.observed_at = (SELECT MAX(r2.observed_at) FROM sensor_readings r2 WHERE r2.cell_id = ?)
            ORDER BY r.sensor_id
            """,
            (cell_id, cell_id),
        )

    def latest_estimate(self, cell_id: str) -> dict[str, Any] | None:
        return self.one(
            "SELECT * FROM estimates WHERE cell_id = ? ORDER BY updated_at DESC LIMIT 1", (cell_id,)
        )

    def latest_resolution(self, cell_id: str) -> dict[str, Any] | None:
        return self.one(
            "SELECT * FROM resolutions WHERE cell_id = ? ORDER BY committed_at DESC LIMIT 1", (cell_id,)
        )

    def resolution_sensors(self, resolution_id: str) -> list[dict[str, Any]]:
        return self.many(
            "SELECT * FROM resolution_sensors WHERE resolution_id = ? ORDER BY weight DESC",
            (resolution_id,),
        )

    def sensor_reputation(self, sensor_id: str) -> dict[str, Any] | None:
        row = self.one(
            """
            SELECT s.sensor_id, s.name, s.cell_id, s.status, s.likely_indoor,
                   rep.reputation_score, rep.features_json, rep.evidence_start, rep.evidence_end
            FROM sensors s LEFT JOIN reputations rep ON rep.sensor_id = s.sensor_id
            WHERE s.sensor_id = ?
            """,
            (sensor_id,),
        )
        if row and row.get("features_json"):
            row["features"] = json.loads(row.pop("features_json"))
        return row

    def affected_estimates(self, sensor_id: str) -> list[str]:
        return [
            row["cell_id"]
            for row in self.many(
                """
                SELECT DISTINCT r.cell_id FROM resolution_sensors rs
                JOIN resolutions r ON r.resolution_id = rs.resolution_id
                WHERE rs.sensor_id = ? ORDER BY r.committed_at DESC
                """,
                (sensor_id,),
            )
        ]

    def readings_for_backtest(self, cluster_id: str) -> list[dict[str, Any]]:
        return self.many(
            """
            SELECT r.*, s.name, s.likely_indoor, rep.reputation_score,
                   m.aqi AS reference_aqi, m.observed_at AS monitor_observed_at
            FROM sensor_readings r
            JOIN sensors s ON s.sensor_id = r.sensor_id
            JOIN monitor_readings m ON m.cell_id = r.cell_id AND m.observed_at = r.observed_at
            LEFT JOIN reputations rep ON rep.sensor_id = r.sensor_id
            JOIN clusters c ON c.cluster_id = s.cluster_id
            WHERE c.cluster_id = ? ORDER BY r.observed_at, r.cell_id, r.sensor_id
            """,
            (cluster_id,),
        )

    def latest_backtest(self) -> dict[str, Any] | None:
        return self.one("SELECT * FROM backtest_runs ORDER BY created_at DESC LIMIT 1")

    def backtest_summaries(self, run_id: str) -> list[dict[str, Any]]:
        return self.many(
            "SELECT * FROM backtest_summaries WHERE backtest_run_id = ? ORDER BY segment, method",
            (run_id,),
        )

    def create_sensor(
        self,
        sensor_id: str,
        name: str,
        latitude: float,
        longitude: float,
        *,
        cluster_id: str | None = None,
        cell_id: str | None = None,
        likely_indoor: bool = False,
        status: str = "active",
    ) -> dict[str, Any]:
        with self.transaction() as transaction:
            return transaction.create_sensor(
                sensor_id,
                name,
                latitude,
                longitude,
                cluster_id=cluster_id,
                cell_id=cell_id,
                likely_indoor=likely_indoor,
                status=status,
            )

    def create_sensor_reading(
        self,
        sensor_id: str,
        observed_at: datetime | str,
        pm25_cf1: float,
        channel_a: float,
        channel_b: float,
        humidity: float,
        rssi: float,
        *,
        reading_id: str | None = None,
        cell_id: str | None = None,
        pm25_atm: float | None = None,
        temperature: float = 24.0,
        raw_ref: str | None = None,
        raw_s3_key: str | None = None,
    ) -> dict[str, Any]:
        with self.transaction() as transaction:
            return transaction.create_sensor_reading(
                sensor_id,
                observed_at,
                pm25_cf1,
                channel_a,
                channel_b,
                humidity,
                rssi,
                reading_id=reading_id,
                cell_id=cell_id,
                pm25_atm=pm25_atm,
                temperature=temperature,
                raw_ref=raw_ref,
                raw_s3_key=raw_s3_key,
            )

    def create_audit_log(
        self,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        *,
        details: dict[str, Any] | None = None,
        reason: str | None = None,
        audit_id: str | None = None,
        source_snapshot_uri: str | None = None,
        created_at: datetime | str | None = None,
    ) -> dict[str, Any]:
        with self.transaction() as transaction:
            return transaction.create_audit_log(
                actor,
                action,
                entity_type,
                entity_id,
                details=details,
                reason=reason,
                audit_id=audit_id,
                source_snapshot_uri=source_snapshot_uri,
                created_at=created_at,
            )

    def read_sensor(self, sensor_id: str) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.read_sensor(sensor_id)

    def read_sensor_reading(self, reading_id: str) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.read_sensor_reading(reading_id)

    def read_audit_log(self, audit_id: str) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.read_audit_log(audit_id)

    def store_fingerprint(self, sensor_id: str, features: dict[str, float], updated_at: str) -> None:
        with self.transaction() as transaction:
            transaction.store_fingerprint(sensor_id, features, updated_at)


class RepositoryTransaction:
    def __init__(self, repository: Repository, connection):
        self.repository = repository
        self.connection = connection

    def one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        return self.repository._one_on(self.connection, query, params)

    def many(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        return self.repository._many_on(self.connection, query, params)

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.repository._execute(self.connection, query, params)

    def create_sensor(self, *args, **kwargs) -> dict[str, Any]:
        return _create_sensor(self.repository, self.connection, *args, **kwargs)

    def create_sensor_reading(self, *args, **kwargs) -> dict[str, Any]:
        return _create_sensor_reading(self.repository, self.connection, *args, **kwargs)

    def create_audit_log(self, *args, **kwargs) -> dict[str, Any]:
        return _create_audit_log(self.repository, self.connection, *args, **kwargs)

    def read_sensor(self, sensor_id: str) -> dict[str, Any] | None:
        return _read_sensor(self.repository, self.connection, sensor_id)

    def read_sensor_reading(self, reading_id: str) -> dict[str, Any] | None:
        return _read_sensor_reading(self.repository, self.connection, reading_id)

    def read_audit_log(self, audit_id: str) -> dict[str, Any] | None:
        return _read_audit_log(self.repository, self.connection, audit_id)

    def store_fingerprint(self, sensor_id: str, features: dict[str, float], updated_at: str) -> None:
        _store_fingerprint(self.repository, self.connection, sensor_id, features, updated_at)


def _sensor_read_query(backend: str) -> str:
    if backend == "cockroach":
        return "SELECT sensor_id, name, lat AS latitude, lon AS longitude, reputation_score, channel_agreement_score, drift_score, indoor_flag, last_seen, updated_at FROM sensors WHERE sensor_id = ?"
    return "SELECT sensor_id, name, latitude, longitude, status, likely_indoor, version, updated_at FROM sensors WHERE sensor_id = ?"


def _sensor_reading_read_query(backend: str) -> str:
    if backend == "cockroach":
        return "SELECT * FROM sensor_readings WHERE reading_id = ?"
    return "SELECT * FROM sensor_readings WHERE reading_id = ?"


def _audit_read_query(backend: str) -> str:
    if backend == "cockroach":
        return "SELECT * FROM audit_log WHERE audit_id = ?"
    return "SELECT * FROM audit_log WHERE audit_id = ?"


def _create_sensor(repository: Repository, connection, sensor_id, name, latitude, longitude, **kwargs):
    if repository.backend == "cockroach":
        repository._execute(
            connection,
            "INSERT INTO sensors (sensor_id, name, lat, lon) VALUES (?, ?, ?, ?)",
            (sensor_id, name, latitude, longitude),
        )
    else:
        cluster_id = kwargs.get("cluster_id")
        cell_id = kwargs.get("cell_id")
        if not cluster_id or not cell_id:
            raise ValueError("cluster_id and cell_id are required for the SQLite repository")
        repository._execute(
            connection,
            """
            INSERT INTO sensors (sensor_id, cluster_id, name, latitude, longitude, cell_id, status, likely_indoor, version, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                sensor_id,
                cluster_id,
                name,
                latitude,
                longitude,
                cell_id,
                kwargs.get("status", "active"),
                int(kwargs.get("likely_indoor", False)),
                _now(),
            ),
        )
    return _read_sensor(repository, connection, sensor_id)


def _create_sensor_reading(
    repository: Repository,
    connection,
    sensor_id,
    observed_at,
    pm25_cf1,
    channel_a,
    channel_b,
    humidity,
    rssi,
    **kwargs,
):
    reading_id = kwargs.get("reading_id") or f"reading-{uuid4().hex[:12]}"
    if repository.backend == "cockroach":
        if kwargs.get("reading_id"):
            return repository._execute_returning(
                connection,
                """
                INSERT INTO sensor_readings
                  (reading_id, sensor_id, pm25_cf1, pm25_atm, channel_a, channel_b, humidity, rssi, observed_at, raw_s3_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING *
                """,
                (
                    reading_id,
                    sensor_id,
                    pm25_cf1,
                    kwargs.get("pm25_atm", pm25_cf1),
                    channel_a,
                    channel_b,
                    humidity,
                    rssi,
                    observed_at,
                    kwargs.get("raw_s3_key") or kwargs.get("raw_ref"),
                ),
            )
        else:
            return repository._execute_returning(
                connection,
                """
                INSERT INTO sensor_readings
                  (sensor_id, pm25_cf1, pm25_atm, channel_a, channel_b, humidity, rssi, observed_at, raw_s3_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING *
                """,
                (
                    sensor_id,
                    pm25_cf1,
                    kwargs.get("pm25_atm", pm25_cf1),
                    channel_a,
                    channel_b,
                    humidity,
                    rssi,
                    observed_at,
                    kwargs.get("raw_s3_key") or kwargs.get("raw_ref"),
                ),
            )
    else:
        cell_id = kwargs.get("cell_id")
        if not cell_id:
            raise ValueError("cell_id is required for the SQLite repository")
        repository._execute(
            connection,
            """
            INSERT INTO sensor_readings
              (reading_id, sensor_id, cell_id, observed_at, pm25_cf1, channel_a, channel_b, humidity, temperature, rssi, raw_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reading_id,
                sensor_id,
                cell_id,
                observed_at,
                pm25_cf1,
                channel_a,
                channel_b,
                humidity,
                kwargs.get("temperature", 24.0),
                rssi,
                kwargs.get("raw_ref") or kwargs.get("raw_s3_key"),
            ),
        )
    return _read_sensor_reading(repository, connection, reading_id)


def _create_audit_log(
    repository: Repository,
    connection,
    actor,
    action,
    entity_type,
    entity_id,
    **kwargs,
):
    audit_id = kwargs.get("audit_id") or f"audit-{uuid4().hex[:12]}"
    details = kwargs.get("details")
    created_at = kwargs.get("created_at") or _now()
    if repository.backend == "cockroach":
        columns = ["actor", "action", "entity_type", "entity_id", "details"]
        values: list[Any] = [actor, action, entity_type, entity_id, Jsonb(details) if details is not None else None]
        if kwargs.get("audit_id"):
            columns.insert(0, "audit_id")
            values.insert(0, audit_id)
        if kwargs.get("created_at"):
            columns.append("created_at")
            values.append(created_at)
        placeholders = ", ".join("?" for _ in columns)
        return repository._execute_returning(
            connection,
            f"INSERT INTO audit_log ({', '.join(columns)}) VALUES ({placeholders}) RETURNING *",
            values,
        )
    else:
        repository._execute(
            connection,
            """
            INSERT INTO audit_log
              (audit_id, actor, action, entity_type, entity_id, source_snapshot_uri, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                actor,
                action,
                entity_type,
                entity_id,
                kwargs.get("source_snapshot_uri") or (details or {}).get("source_snapshot_uri"),
                kwargs.get("reason") or action,
                created_at,
            ),
        )
    return _read_audit_log(repository, connection, audit_id)


def _read_sensor(repository: Repository, connection, sensor_id: str) -> dict[str, Any] | None:
    return repository._one_on(connection, _sensor_read_query(repository.backend), (sensor_id,))


def _read_sensor_reading(repository: Repository, connection, reading_id: str) -> dict[str, Any] | None:
    return repository._one_on(connection, _sensor_reading_read_query(repository.backend), (reading_id,))


def _read_audit_log(repository: Repository, connection, audit_id: str) -> dict[str, Any] | None:
    return repository._one_on(connection, _audit_read_query(repository.backend), (audit_id,))


def _store_fingerprint(repository: Repository, connection, sensor_id: str, features: dict[str, float], updated_at: str) -> None:
    repository._execute(
        connection,
        """
        INSERT INTO sensor_embeddings (sensor_id, fingerprint_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT (sensor_id) DO UPDATE SET fingerprint_json = excluded.fingerprint_json, updated_at = excluded.updated_at
        """,
        (sensor_id, json.dumps(features, sort_keys=True), updated_at),
    )


class SQLiteRepository(Repository):
    backend = "sqlite"


class CockroachRepository(Repository):
    backend = "cockroach"
