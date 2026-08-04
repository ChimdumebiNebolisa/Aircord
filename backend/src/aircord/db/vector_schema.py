"""CockroachDB schema for handcrafted sensor behavioral fingerprints."""


VECTOR_DIMENSIONS = 8
VECTOR_INDEX_NAME = "sensor_embeddings_behavioral_fingerprint_idx"

COCKROACH_VECTOR_TABLE = """
CREATE TABLE IF NOT EXISTS sensor_embeddings (
  sensor_id STRING PRIMARY KEY,
  behavioral_fingerprint VECTOR(8) NOT NULL,
  feature_json JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
)
"""

COCKROACH_VECTOR_INDEX = f"""
CREATE VECTOR INDEX {VECTOR_INDEX_NAME}
ON sensor_embeddings (behavioral_fingerprint vector_cosine_ops)
"""
