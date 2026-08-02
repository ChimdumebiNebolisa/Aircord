from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from aircord.config import DB_PATH


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS clusters (
  cluster_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  gate_a_status TEXT NOT NULL,
  gate_a_notes TEXT NOT NULL,
  centroid_lat REAL NOT NULL,
  centroid_lon REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS cells (
  cell_id TEXT PRIMARY KEY,
  cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
  centroid_lat REAL NOT NULL,
  centroid_lon REAL NOT NULL,
  version INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitors (
  monitor_id TEXT PRIMARY KEY,
  cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
  name TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  latest_aqi REAL NOT NULL,
  observed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitor_readings (
  reading_id TEXT PRIMARY KEY,
  monitor_id TEXT NOT NULL REFERENCES monitors(monitor_id),
  cell_id TEXT NOT NULL REFERENCES cells(cell_id),
  observed_at TEXT NOT NULL,
  aqi REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sensors (
  sensor_id TEXT PRIMARY KEY,
  cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
  name TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  cell_id TEXT NOT NULL REFERENCES cells(cell_id),
  status TEXT NOT NULL DEFAULT 'active',
  likely_indoor INTEGER NOT NULL DEFAULT 0,
  version INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sensor_readings (
  reading_id TEXT PRIMARY KEY,
  sensor_id TEXT NOT NULL REFERENCES sensors(sensor_id),
  cell_id TEXT NOT NULL REFERENCES cells(cell_id),
  observed_at TEXT NOT NULL,
  pm25_cf1 REAL NOT NULL,
  channel_a REAL NOT NULL,
  channel_b REAL NOT NULL,
  humidity REAL NOT NULL,
  temperature REAL NOT NULL,
  rssi REAL NOT NULL,
  raw_ref TEXT
);
CREATE TABLE IF NOT EXISTS reputations (
  sensor_id TEXT PRIMARY KEY REFERENCES sensors(sensor_id),
  reputation_score REAL NOT NULL,
  features_json TEXT NOT NULL,
  evidence_start TEXT NOT NULL,
  evidence_end TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sensor_embeddings (
  sensor_id TEXT PRIMARY KEY REFERENCES sensors(sensor_id),
  fingerprint_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estimates (
  estimate_id TEXT PRIMARY KEY,
  cell_id TEXT NOT NULL REFERENCES cells(cell_id),
  estimated_aqi REAL NOT NULL,
  confidence REAL NOT NULL,
  claim_status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resolutions (
  resolution_id TEXT PRIMARY KEY,
  estimate_id TEXT NOT NULL REFERENCES estimates(estimate_id),
  cell_id TEXT NOT NULL REFERENCES cells(cell_id),
  rationale_text TEXT NOT NULL,
  confidence_factors_json TEXT NOT NULL,
  monitor_context_json TEXT NOT NULL,
  reference_caveat TEXT NOT NULL,
  medical_directive_caveat TEXT NOT NULL,
  committed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resolution_sensors (
  resolution_id TEXT NOT NULL REFERENCES resolutions(resolution_id),
  sensor_id TEXT NOT NULL REFERENCES sensors(sensor_id),
  reading_id TEXT NOT NULL REFERENCES sensor_readings(reading_id),
  weight REAL NOT NULL,
  decision TEXT NOT NULL,
  reason_codes_json TEXT NOT NULL,
  reputation_score_at_commit REAL NOT NULL,
  PRIMARY KEY (resolution_id, sensor_id)
);
CREATE TABLE IF NOT EXISTS audit_log (
  audit_id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  source_snapshot_uri TEXT,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS backtest_runs (
  backtest_run_id TEXT PRIMARY KEY,
  cluster_id TEXT NOT NULL REFERENCES clusters(cluster_id),
  window_start TEXT NOT NULL,
  window_end TEXT NOT NULL,
  status TEXT NOT NULL,
  claim_status TEXT NOT NULL,
  failure_reason TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE TABLE IF NOT EXISTS backtest_summaries (
  backtest_run_id TEXT NOT NULL REFERENCES backtest_runs(backtest_run_id),
  segment TEXT NOT NULL,
  method TEXT NOT NULL,
  observation_count INTEGER NOT NULL,
  mean_absolute_error REAL NOT NULL,
  median_absolute_error REAL NOT NULL,
  PRIMARY KEY (backtest_run_id, segment, method)
);
"""


def ensure_db(path: Path = DB_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_db(path)
    connection = sqlite3.connect(path, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


@contextmanager
def transaction(path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    connection = connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()

