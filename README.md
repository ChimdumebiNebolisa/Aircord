# Aircord

Aircord is a one-metro air-quality trust-memory MVP. The backend uses a local
SQLite fixture database by default and switches to CockroachDB Cloud for real
persistence when `DATABASE_URL` is configured.

## CockroachDB configuration

Copy `.env.example` to `.env` and set:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:26257/aircord?sslmode=verify-full
DATABASE_CA_CERT=.\certs\aircord-ca.crt
```

`DATABASE_CA_CERT` is required when the CockroachDB cluster CA is not trusted by
the local system trust store. Download the CA certificate from the cluster's
Connect dialog and keep it under the ignored `.certs/` directory. Never commit
`.env`, certificates, passwords, or other credentials.

When `DATABASE_URL` is set, the application repository selects the
CockroachDB-backed implementation. Without it, tests and local fixture runs use
the SQLite backend.

## CockroachDB smoke test

With the environment variables set in the current shell, run:

```powershell
python backend/scripts/cockroach_connection_smoke.py
python backend/scripts/cockroach_write_smoke.py
```

The repository smoke test creates and reads one sensor, one sensor reading, and
one audit-log row in a single transaction, then rolls the transaction back.

## Live PurpleAir ingestion smoke

The first live ingestion command requires these environment variables:

```text
DATABASE_URL
PURPLEAIR_API_KEY
PURPLEAIR_SENSOR_ID
AWS_REGION
S3_BUCKET
```

AWS credentials are resolved through the standard AWS SDK credential chain. If
the CockroachDB cluster CA is not trusted by the system, also set
`DATABASE_CA_CERT` to the downloaded certificate path.

After setting the variables in the current shell, run:

```powershell
python backend/scripts/purpleair_ingest_smoke.py
```

Expected success output has this shape (values are generated at runtime):

```text
PurpleAir live ingestion succeeded: sensor=<id>, reading=<uuid>, snapshot=s3://<bucket>/raw/purpleair/sensor_id=<id>/date=<YYYY-MM-DD>/<timestamp>.json, audit=<uuid>
```

The command fetches one sensor, stores the complete raw response in S3 under
`raw/purpleair/sensor_id=<id>/date=<YYYY-MM-DD>/<timestamp>.json`, then upserts
the sensor and writes one normalized `sensor_readings` row plus one
`audit_log` row in CockroachDB. It exits without making a network request when a
required variable is missing.

## Tests

Install the backend in editable mode with development dependencies:

```powershell
python -m pip install -e "backend[dev]"
```

Run the normal test suite:

```powershell
python -m pytest backend/tests
```

The CockroachDB integration test runs when `DATABASE_URL` is configured and is
skipped otherwise:

```powershell
python -m pytest backend/tests/integration/test_cockroach_repository.py
```
