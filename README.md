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

## AirNow ingestion and memory readback

The scoped Los Angeles AirNow path uses these variables in addition to the
PurpleAir/Cockroach/S3 settings:

```text
DATABASE_URL
AIRNOW_API_KEY
PURPLEAIR_SENSOR_ID
AWS_REGION
S3_BUCKET
```

Run the monitor ingest, then the first reputation/resolution loop:

```powershell
python backend/scripts/airnow_ingest_smoke.py
python backend/scripts/memory_loop_smoke.py
python backend/scripts/memory_readback.py --sensor-id 54917
```

AirNow stores the raw response under
`raw/airnow/date=<YYYY-MM-DD>/<timestamp>.json`, upserts the nearest current
monitor, and records an `airnow_ingest` audit row. The memory loop updates the
sensor reputation, writes `cell_estimates` and `resolutions`, and records
`aircord_memory` audit rows. Its estimate explicitly blends the PurpleAir PM2.5
proxy with the AirNow monitor AQI using the sensor's reputation weight. This is
a transparent cross-source proxy, not a validated AQI claim; no accuracy
number is implied. If PM2.5 is missing, the resolution says that the monitor
AQI was used as an explicit fallback. If both values are missing, the cycle
fails instead of silently storing `0.0`. A raw PurpleAir PM2.5 value of `0.0`
is preserved as reported, but a downweighted sensor does not make the whole
cell estimate zero while a monitor reference is available.

## AWS Lambda PurpleAir ingestion

The Lambda entry point wraps the same ingestion path as the local smoke:

```text
aircord.ingestion.lambda_handlers.purpleair_ingest_handler
```

Configure these Lambda environment variables:

```text
DATABASE_URL
PURPLEAIR_API_KEY
PURPLEAIR_SENSOR_ID
AWS_REGION
S3_BUCKET
```

`DATABASE_CA_CERT` is optional. If set, package the CockroachDB CA certificate
with the function or a Lambda layer and set the variable to its Lambda runtime
path. The function needs outbound network access to CockroachDB on port 26257.

The execution role needs `s3:PutObject` for the raw snapshot prefix, for
example `arn:aws:s3:::<bucket>/raw/purpleair/*`. Standard CloudWatch Logs
permissions are also required for Lambda execution logging.

The reproducible deployment uses the committed IAM templates and a Linux
Python 3.12 package. Set the real values in the current shell without writing
them to the repository, then run the equivalent commands:

```powershell
aws iam create-role `
  --role-name aircord-purpleair-ingest-role `
  --assume-role-policy-document file://infra/lambda-trust-policy.json
aws iam put-role-policy `
  --role-name aircord-purpleair-ingest-role `
  --policy-name aircord-purpleair-ingest-access `
  --policy-document file://infra/lambda-access-policy.json

python -m pip install --target .lambda-build/package `
  --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 `
  --only-binary=:all: boto3 httpx 'psycopg[binary]'
New-Item -ItemType Directory .lambda-build/package/certs -Force
Copy-Item backend/src/aircord .lambda-build/package/aircord -Recurse
Copy-Item .certs/aircord-ca.crt .lambda-build/package/certs/aircord-ca.crt
tar -a -c -f .lambda-build/aircord-purpleair-ingest.zip -C .lambda-build/package .

aws lambda create-function `
  --function-name aircord-purpleair-ingest `
  --runtime python3.12 `
  --handler aircord.ingestion.lambda_handlers.purpleair_ingest_handler `
  --role <role-arn> `
  --zip-file fileb://.lambda-build/aircord-purpleair-ingest.zip `
  --environment "Variables={DATABASE_URL=$env:DATABASE_URL,PURPLEAIR_API_KEY=$env:PURPLEAIR_API_KEY,PURPLEAIR_SENSOR_ID=$env:PURPLEAIR_SENSOR_ID,S3_BUCKET=$env:S3_BUCKET,DATABASE_CA_CERT=/var/task/certs/aircord-ca.crt}"
```

Lambda supplies the reserved `AWS_REGION` variable from the function's
`us-east-1` deployment region. Keep the CA path inside the artifact or a
Lambda layer; never use a local Windows path.

After deploying the package, invoke it manually with the AWS CLI:

```powershell
aws lambda invoke `
  --function-name <function-name> `
  --invocation-type RequestResponse `
  --cli-binary-format raw-in-base64-out `
  --payload '{}' `
  lambda-response.json
Get-Content lambda-response.json
```

The response contains `sensor_id`, `s3_key`, `reading_id`, and `audit_id`.
Schedule the low-cost 15-minute poller with EventBridge:

```powershell
aws events put-rule --name aircord-purpleair-ingest-15m --schedule-expression "rate(15 minutes)" --state ENABLED
aws lambda add-permission --function-name aircord-purpleair-ingest --statement-id aircord-purpleair-ingest-15m --action lambda:InvokeFunction --principal events.amazonaws.com --source-arn <rule-arn>
aws events put-targets --rule aircord-purpleair-ingest-15m --targets Id=aircord-purpleair-ingest-target,Arn=<function-arn>
```

Disable or re-enable the schedule without deleting it:

```powershell
aws events disable-rule --name aircord-purpleair-ingest-15m
aws events enable-rule --name aircord-purpleair-ingest-15m
```

Keep the local smoke command as the first diagnostic path before
troubleshooting a scheduled invocation.

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
