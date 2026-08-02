# Aircord infrastructure boundary

The bootstrap runs locally in fixture mode so the proof loop is reproducible
without credentials. The production shape keeps CockroachDB as the single
transactional store for estimates, reputations, resolutions, and audit rows;
S3 stores immutable raw AirNow/PurpleAir snapshots; Lambda runs the bounded
pollers; and Bedrock may produce explanation text before the short reconciliation
transaction opens.

The current adapters fail closed when `AIRNOW_API_KEY` or `PURPLEAIR_API_KEY`
is missing. They do not silently substitute fixture data for live data. The
SQLite store is a local development fallback; a CockroachDB adapter and
deployment provisioning are intentionally not claimed as verified here.

CockroachDB Distributed Vector Indexing is represented locally by persisted
behavioral fingerprints and self-similarity distance. The production migration
should map `sensor_embeddings.fingerprint` to a vector column and query it for
drift detection before enabling cross-sensor trust propagation.

