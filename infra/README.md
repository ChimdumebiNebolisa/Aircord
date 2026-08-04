# Aircord infrastructure boundary

The bootstrap runs locally in fixture mode so the proof loop is reproducible
without credentials. The production shape keeps CockroachDB as the single
transactional store for estimates, reputations, resolutions, and audit rows;
S3 stores immutable raw AirNow/PurpleAir snapshots; Lambda runs the bounded
pollers; and Bedrock may produce explanation text before the short reconciliation
transaction opens.

The current adapters fail closed when `AIRNOW_API_KEY` or `PURPLEAIR_API_KEY`
is missing. They do not silently substitute fixture data for live data. The
scoped PurpleAir Lambda and 15-minute EventBridge schedule are verified in
`us-east-1`; the AirNow monitor ingest and first reputation/resolution loop
are verified against the live Los Angeles data path. Broader deployment and
multi-metro operation are not claimed.

The Lambda entry point is
`aircord.ingestion.lambda_handlers.purpleair_ingest_handler`. The root README
contains the required environment variables, IAM policy templates, package
commands, manual invoke command, and schedule disable command.

CockroachDB Distributed Vector Indexing is represented locally by persisted
behavioral fingerprints and self-similarity distance. The production migration
should map `sensor_embeddings.fingerprint` to a vector column and query it for
drift detection before enabling cross-sensor trust propagation.

