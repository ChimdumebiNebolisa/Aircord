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
