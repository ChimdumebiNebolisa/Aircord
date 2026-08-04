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
from aircord.db.vector_schema import COCKROACH_VECTOR_INDEX, COCKROACH_VECTOR_TABLE, VECTOR_INDEX_NAME
from aircord.reputation.vector import vector_literal


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
        if self.backend == "cockroach":
            return self.one(
                "SELECT * FROM cell_estimates WHERE cell_id = ? ORDER BY updated_at DESC LIMIT 1",
                (cell_id,),
            )
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
        if self.backend == "cockroach":
            return self.one(
                """
                SELECT sensor_id, name, lat AS latitude, lon AS longitude,
                       reputation_score, channel_agreement_score, drift_score,
                       indoor_flag AS likely_indoor, last_seen, updated_at
                FROM sensors WHERE sensor_id = ?
                """,
                (sensor_id,),
            )
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

    def upsert_sensor(
        self,
        sensor_id: str,
        name: str | None,
        latitude: float | None,
        longitude: float | None,
        *,
        likely_indoor: bool = False,
        last_seen: datetime | str | None = None,
        cluster_id: str | None = None,
        cell_id: str | None = None,
        status: str = "active",
    ) -> dict[str, Any]:
        with self.transaction() as transaction:
            return transaction.upsert_sensor(
                sensor_id,
                name,
                latitude,
                longitude,
                likely_indoor=likely_indoor,
                last_seen=last_seen,
                cluster_id=cluster_id,
                cell_id=cell_id,
                status=status,
            )

    def upsert_monitor(
        self,
        monitor_id: str,
        name: str | None,
        latitude: float | None,
        longitude: float | None,
        latest_aqi: float | None,
        observed_at: datetime | str | None,
        *,
        cluster_id: str = "greater-la",
        cell_id: str | None = None,
    ) -> dict[str, Any]:
        with self.transaction() as transaction:
            return transaction.upsert_monitor(
                monitor_id,
                name,
                latitude,
                longitude,
                latest_aqi,
                observed_at,
                cluster_id=cluster_id,
                cell_id=cell_id,
            )

    def update_sensor_reputation(
        self,
        sensor_id: str,
        reputation_score: float,
        features: dict[str, Any],
        *,
        channel_agreement_score: float | None = None,
        drift_score: float | None = None,
        evidence_start: datetime | str | None = None,
        evidence_end: datetime | str | None = None,
    ) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.update_sensor_reputation(
                sensor_id,
                reputation_score,
                features,
                channel_agreement_score=channel_agreement_score,
                drift_score=drift_score,
                evidence_start=evidence_start,
                evidence_end=evidence_end,
            )

    def upsert_cell_estimate(
        self, cell_id: str, estimate_aqi: float, confidence: float
    ) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.upsert_cell_estimate(cell_id, estimate_aqi, confidence)

    def create_resolution(
        self,
        cell_id: str,
        estimate_aqi: float,
        confidence: float,
        reasoning_text: str,
        sensors_considered: list[dict[str, Any]],
        *,
        estimate_id: str | None = None,
    ) -> dict[str, Any] | None:
        with self.transaction() as transaction:
            return transaction.create_resolution(
                cell_id,
                estimate_aqi,
                confidence,
                reasoning_text,
                sensors_considered,
                estimate_id=estimate_id,
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

    def ensure_vector_schema(self) -> None:
        if self.backend != "cockroach":
            return
        with self.transaction() as transaction:
            setting = transaction.one("SHOW CLUSTER SETTING feature.vector_index.enabled")
            if not setting or str(next(iter(setting.values()))).lower() != "true":
                raise RuntimeError(
                    "CockroachDB vector indexes are disabled; enable feature.vector_index.enabled first"
                )
            transaction.execute(COCKROACH_VECTOR_TABLE)
            indexes = transaction.many("SHOW INDEXES FROM sensor_embeddings")
            if not any(row.get("index_name") == VECTOR_INDEX_NAME for row in indexes):
                transaction.execute("SET sql_safe_updates = false")
                transaction.execute(COCKROACH_VECTOR_INDEX)

    def upsert_sensor_embedding(
        self,
        sensor_id: str,
        vector: list[float],
        features: dict[str, float | str],
        updated_at: str,
    ) -> dict[str, Any] | None:
        if self.backend == "cockroach":
            self.ensure_vector_schema()
        with self.transaction() as transaction:
            return transaction.upsert_sensor_embedding(sensor_id, vector, features, updated_at)

    def similar_sensor_embeddings(
        self,
        vector: list[float],
        *,
        exclude_sensor_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if self.backend != "cockroach":
            return []
        self.ensure_vector_schema()
        literal = vector_literal(vector)
        if exclude_sensor_id is None:
            query = """
                SELECT sensor_id, behavioral_fingerprint, feature_json, updated_at,
                       behavioral_fingerprint <=> CAST(? AS VECTOR(8)) AS cosine_distance
                FROM sensor_embeddings
                ORDER BY behavioral_fingerprint <=> CAST(? AS VECTOR(8))
                LIMIT ?
            """
            params = (literal, literal, limit)
        else:
            query = """
                SELECT sensor_id, behavioral_fingerprint, feature_json, updated_at,
                       behavioral_fingerprint <=> CAST(? AS VECTOR(8)) AS cosine_distance
                FROM sensor_embeddings
                WHERE sensor_id <> ?
                ORDER BY behavioral_fingerprint <=> CAST(? AS VECTOR(8))
                LIMIT ?
            """
            params = (literal, exclude_sensor_id, literal, limit)
        return self.many(query, params)


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

    def upsert_sensor(self, *args, **kwargs) -> dict[str, Any]:
        return _upsert_sensor(self.repository, self.connection, *args, **kwargs)

    def upsert_monitor(self, *args, **kwargs) -> dict[str, Any]:
        return _upsert_monitor(self.repository, self.connection, *args, **kwargs)

    def update_sensor_reputation(self, *args, **kwargs) -> dict[str, Any] | None:
        return _update_sensor_reputation(self.repository, self.connection, *args, **kwargs)

    def upsert_cell_estimate(self, *args, **kwargs) -> dict[str, Any] | None:
        return _upsert_cell_estimate(self.repository, self.connection, *args, **kwargs)

    def create_resolution(self, *args, **kwargs) -> dict[str, Any] | None:
        return _create_resolution(self.repository, self.connection, *args, **kwargs)

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

    def upsert_sensor_embedding(self, sensor_id: str, vector, features, updated_at: str) -> dict[str, Any] | None:
        return _upsert_sensor_embedding(self.repository, self.connection, sensor_id, vector, features, updated_at)


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


def _upsert_sensor(repository: Repository, connection, sensor_id, name, latitude, longitude, **kwargs):
    if repository.backend == "cockroach":
        repository._execute(
            connection,
            """
            INSERT INTO sensors (sensor_id, name, lat, lon, indoor_flag, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (sensor_id) DO UPDATE SET
              name = excluded.name,
              lat = excluded.lat,
              lon = excluded.lon,
              indoor_flag = excluded.indoor_flag,
              last_seen = excluded.last_seen,
              updated_at = now()
            """,
            (
                sensor_id,
                name,
                latitude,
                longitude,
                kwargs.get("likely_indoor", False),
                kwargs.get("last_seen"),
            ),
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
            ON CONFLICT (sensor_id) DO UPDATE SET
              name = excluded.name,
              latitude = excluded.latitude,
              longitude = excluded.longitude,
              status = excluded.status,
              likely_indoor = excluded.likely_indoor,
              updated_at = excluded.updated_at
            """,
            (
                sensor_id,
                cluster_id,
                name or sensor_id,
                latitude,
                longitude,
                cell_id,
                kwargs.get("status", "active"),
                int(kwargs.get("likely_indoor", False)),
                _now(),
            ),
        )
    return _read_sensor(repository, connection, sensor_id)


def _upsert_monitor(
    repository: Repository,
    connection,
    monitor_id,
    name,
    latitude,
    longitude,
    latest_aqi,
    observed_at,
    **kwargs,
):
    if repository.backend == "cockroach":
        return repository._execute_returning(
            connection,
            """
            INSERT INTO monitors (monitor_id, name, lat, lon, latest_aqi, observed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (monitor_id) DO UPDATE SET
              name = excluded.name,
              lat = excluded.lat,
              lon = excluded.lon,
              latest_aqi = excluded.latest_aqi,
              observed_at = excluded.observed_at,
              updated_at = now()
            RETURNING *
            """,
            (monitor_id, name, latitude, longitude, latest_aqi, observed_at),
        )

    cluster_id = kwargs.get("cluster_id", "greater-la")
    cell_id = kwargs.get("cell_id") or f"cell-{monitor_id}"
    repository._execute(
        connection,
        """
        INSERT INTO monitors
          (monitor_id, cluster_id, name, latitude, longitude, latest_aqi, observed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (monitor_id) DO UPDATE SET
          name = excluded.name,
          latitude = excluded.latitude,
          longitude = excluded.longitude,
          latest_aqi = excluded.latest_aqi,
          observed_at = excluded.observed_at
        """,
        (monitor_id, cluster_id, name or monitor_id, latitude, longitude, latest_aqi, observed_at),
    )
    return repository._one_on(
        connection,
        "SELECT * FROM monitors WHERE monitor_id = ?",
        (monitor_id,),
    )


def _update_sensor_reputation(
    repository: Repository,
    connection,
    sensor_id,
    reputation_score,
    features,
    **kwargs,
):
    channel_agreement_score = kwargs.get("channel_agreement_score")
    drift_score = kwargs.get("drift_score")
    if repository.backend == "cockroach":
        return repository._execute_returning(
            connection,
            """
            UPDATE sensors
            SET reputation_score = ?,
                channel_agreement_score = COALESCE(?, channel_agreement_score),
                drift_score = COALESCE(?, drift_score),
                updated_at = now()
            WHERE sensor_id = ?
            RETURNING *
            """,
            (reputation_score, channel_agreement_score, drift_score, sensor_id),
        )

    now = _now()
    evidence_start = kwargs.get("evidence_start") or now
    evidence_end = kwargs.get("evidence_end") or now
    repository._execute(
        connection,
        """
        INSERT INTO reputations
          (sensor_id, reputation_score, features_json, evidence_start, evidence_end, version, updated_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
        ON CONFLICT (sensor_id) DO UPDATE SET
          reputation_score = excluded.reputation_score,
          features_json = excluded.features_json,
          evidence_start = excluded.evidence_start,
          evidence_end = excluded.evidence_end,
          version = reputations.version + 1,
          updated_at = excluded.updated_at
        """,
        (sensor_id, reputation_score, json.dumps(features, sort_keys=True), evidence_start, evidence_end, now),
    )
    return repository._one_on(
        connection,
        "SELECT * FROM reputations WHERE sensor_id = ?",
        (sensor_id,),
    )


def _upsert_cell_estimate(repository: Repository, connection, cell_id, estimate_aqi, confidence):
    if repository.backend == "cockroach":
        return repository._execute_returning(
            connection,
            """
            INSERT INTO cell_estimates (cell_id, estimate_aqi, confidence, version, updated_at)
            VALUES (?, ?, ?, 0, now())
            ON CONFLICT (cell_id) DO UPDATE SET
              estimate_aqi = excluded.estimate_aqi,
              confidence = excluded.confidence,
              version = cell_estimates.version + 1,
              updated_at = now()
            RETURNING *
            """,
            (cell_id, estimate_aqi, confidence),
        )

    estimate_id = f"estimate-{uuid4().hex[:12]}"
    now = _now()
    repository._execute(
        connection,
        """
        INSERT INTO estimates (estimate_id, cell_id, estimated_aqi, confidence, claim_status, updated_at)
        VALUES (?, ?, ?, ?, 'pending_backtest', ?)
        """,
        (estimate_id, cell_id, estimate_aqi, confidence, now),
    )
    return repository._one_on(
        connection,
        "SELECT * FROM estimates WHERE estimate_id = ?",
        (estimate_id,),
    )


def _create_resolution(
    repository: Repository,
    connection,
    cell_id,
    estimate_aqi,
    confidence,
    reasoning_text,
    sensors_considered,
    **kwargs,
):
    if repository.backend == "cockroach":
        return repository._execute_returning(
            connection,
            """
            INSERT INTO resolutions
              (cell_id, estimate_aqi, confidence, reasoning_text, sensors_considered)
            VALUES (?, ?, ?, ?, ?)
            RETURNING *
            """,
            (cell_id, estimate_aqi, confidence, reasoning_text, Jsonb(sensors_considered)),
        )

    estimate_id = kwargs.get("estimate_id")
    if not estimate_id:
        raise ValueError("estimate_id is required for the SQLite repository")
    resolution_id = f"resolution-{uuid4().hex[:12]}"
    now = _now()
    repository._execute(
        connection,
        """
        INSERT INTO resolutions
          (resolution_id, estimate_id, cell_id, rationale_text, confidence_factors_json,
           monitor_context_json, reference_caveat, medical_directive_caveat, committed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resolution_id,
            estimate_id,
            cell_id,
            reasoning_text,
            json.dumps({"confidence": confidence}, sort_keys=True),
            json.dumps(sensors_considered, sort_keys=True),
            "Regulatory monitors are references, not absolute truth.",
            "This is an estimate, not medical advice.",
            now,
        ),
    )
    return repository._one_on(
        connection,
        "SELECT * FROM resolutions WHERE resolution_id = ?",
        (resolution_id,),
    )


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


def _upsert_sensor_embedding(repository: Repository, connection, sensor_id, vector, features, updated_at):
    if repository.backend != "cockroach":
        _store_fingerprint(repository, connection, sensor_id, features, updated_at)
        return _read_sensor_embedding(repository, connection, sensor_id)
    return repository._execute_returning(
        connection,
        """
        INSERT INTO sensor_embeddings (sensor_id, behavioral_fingerprint, feature_json, updated_at)
        VALUES (?, CAST(? AS VECTOR(8)), ?, ?)
        ON CONFLICT (sensor_id) DO UPDATE SET
          behavioral_fingerprint = excluded.behavioral_fingerprint,
          feature_json = excluded.feature_json,
          updated_at = excluded.updated_at
        RETURNING *
        """,
        (sensor_id, vector_literal(vector), Jsonb(features), updated_at),
    )


def _read_sensor_embedding(repository: Repository, connection, sensor_id: str):
    return repository._one_on(connection, "SELECT * FROM sensor_embeddings WHERE sensor_id = ?", (sensor_id,))


class SQLiteRepository(Repository):
    backend = "sqlite"


class CockroachRepository(Repository):
    backend = "cockroach"
