# Aircord

Aircord is a one-metro air-quality trust-memory MVP. The backend uses a local
SQLite fixture database by default and switches to CockroachDB Cloud for real
persistence when `DATABASE_URL` is configured.

Project claim: Aircord learns which community air sensors to trust and explains
why. This is a judge-facing proof surface, not a medical-advice product or a
broad accuracy claim.

## Demo surface

The shortest local demo path is a CockroachDB-backed snapshot plus the Vite
frontend. `demo_status` prints the live proof and writes a timestamped JSON
snapshot consumed by the page:

```powershell
# In the backend environment, set DATABASE_URL and DATABASE_CA_CERT if needed.
python backend/scripts/demo_status.py --write-frontend-snapshot

# In a second shell:
cd frontend
npm install
npm run dev
```

The status-only check is:

```powershell
python backend/scripts/demo_status.py
```

The read-only API exposes the same CockroachDB-backed result at:

```text
GET /api/sensors/54917/latest
GET /api/sensors/54917/memory
GET /api/sensors/54917/resolution
GET /api/sensors/54917/audit
GET /api/sensors/54917/similar
GET /api/backtests/latest
GET /api/demo-summary
```

The persisted weight is intentionally simple and inspectable:
`sensor_weight = reputation_score * multiplier`. A trusted sensor uses `1.00`,
an ordinary downweighted sensor uses `0.50`, a drifted downweighted sensor uses
`0.25`, and an ignored sensor uses `0.00`; the result is rounded to four
decimals. The current live readback is `0.3973 * 0.50 = 0.1986`.

The page reads `/demo-summary.json` by default, so the normal local run does
not require a running API. To use the live read-only API instead, start it and
set `VITE_API_BASE`:

```powershell
# Shell 1
uvicorn aircord.main:app --reload --port 8000

# Shell 2
$env:VITE_API_BASE="http://localhost:8000"
cd frontend
npm run dev
```

To regenerate the public-safe static fallback from current CockroachDB state:

```powershell
python backend/scripts/demo_status.py --write-frontend-snapshot
cd frontend
npm run build
```

The generated `frontend/public/demo-summary.json` includes `generated_at` and
only persisted CockroachDB demo data, not credentials. The frontend does not
substitute fake or placeholder values. If the live API is unavailable, it
falls back to this real snapshot rather than inventing data. Regenerate the
snapshot immediately before the final recording or submission so the timestamp
and proof reflect the latest available CockroachDB state.

Frontend verification commands:

```powershell
cd frontend
npm run typecheck
npm run build
```

Architecture proof path:

```text
PurpleAir / AirNow -> S3 raw snapshots -> CockroachDB readings and monitors
                                      -> reputation -> estimate/resolution -> audit trail
                                      -> VECTOR(8) fingerprints -> similarity
                                      -> Managed MCP read-only questions
                                      -> FastAPI /api/demo-summary -> Vite judge surface
```

The demo explicitly shows the CockroachDB Cloud persistent memory layer,
Distributed Vector Indexing, the Managed MCP Server path, AWS S3, Lambda, and
EventBridge. It also keeps the sample-size, unit-mismatch, reference-monitor,
and PurpleAir points-billing caveats visible.

## Public deployment path

The verified public demo is [Aircord on Vercel](https://aircord-demo.vercel.app/).
It is a production deployment of the static Vite artifact; no backend service
or database credential is present in the deployment.

Generate a fresh snapshot from CockroachDB, run the Vite build, then deploy the
`frontend/dist` output directory:

```powershell
python backend/scripts/demo_status.py --write-frontend-snapshot
cd frontend
npm run build
vercel deploy dist --prod -y
```

The build command is `npm run build`, and the output directory is
`frontend/dist`. If the local CLI is not authenticated, run `vercel login` or
use the connected Vercel integration to publish the same static artifact to the
existing `aircord-demo` project. The static deployment reads
`demo-summary.json`; it does not need `DATABASE_URL` and exposes no database
credentials.

After deployment, verify both the page and snapshot:

```text
https://aircord-demo.vercel.app/
https://aircord-demo.vercel.app/demo-summary.json
```

The page must show the persisted sensor decision and must not show the snapshot
failure state.

For a live API deployment, set `VITE_API_BASE` to the public FastAPI origin and
configure `AIRCORD_ALLOWED_ORIGINS` on that API. Never place database URLs,
passwords, certificates, AWS credentials, or API keys in Vite variables or the
frontend repository.

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

The sensor weight formula is intentionally explicit: `sensor_weight =
reputation_score × multiplier`. Trusted sensors use `1.00`, ordinary
downweighted sensors use `0.50`, drifted sensors use `0.25`, and ignored sensors
use `0.00`. For the live sensor `54917`, `0.3973 × 0.50 = 0.19865`, rounded to
the persisted weight `0.1986`. The same explanation appears in
`python backend/scripts/memory_readback.py --sensor-id 54917` and the demo
page.

## Backtest

Run the bounded live comparison for the LA sensor and AirNow monitor:

```powershell
python backend/scripts/backtest_aircord.py --sensor-id 54917 --monitor-id 060371302 --window-days 3
```

The command reads normalized PurpleAir history from CockroachDB and pairs it
with the nearest available AirNow monitor observation. It stores the run and
summaries in `backtest_runs` and `backtest_summaries`, and writes a
`backtest_runner` audit row. At least three valid aligned observations are
required before any MAE is emitted; otherwise the result is explicitly
`insufficient_data` with `claim_status=no_claim`.

Expected output shape:

```text
Aircord backtest
status: passed / claim_status=measured
data source: CockroachDB normalized PurpleAir readings + AirNow monitor snapshot
sample count: <n>
Raw PurpleAir MAE: <value>
Static correction MAE: <value>
Aircord MAE: <value>
degraded sample count: <n>
degraded Aircord MAE: <value or insufficient data>
caveats:
- <data-window and cross-source caveats>
```

The live MVP may have only accumulated snapshots and one current monitor row,
so a passed run is still a limited measured comparison, not a claim that
Aircord is more accurate. PurpleAir PM2.5 and AirNow AQI are different units.
Use the existing SQLite fixture backtest for deterministic development checks:
`python -m aircord.backtest.run --cluster greater-la --window-days 14`.

## CockroachDB tools: persistent memory, vectors, and MCP

CockroachDB is Aircord's persistent memory layer for live sensors, readings,
monitors, reputations, estimates, resolutions, audit rows, and backtest
summaries.

### Distributed Vector Indexing

Aircord stores an explainable, handcrafted 8-dimensional behavioral fingerprint
in `sensor_embeddings`:

1. reputation score
2. channel A/B difference
3. recent PM2.5
4. missingness indicator
5. freshness score
6. absolute difference from the monitor
7. drift score
8. confidence

The values are normalized application features, not a trained embedding model.
CockroachDB stores them in `VECTOR(8)` and uses a cosine vector index. The live
memory loop refreshes the fingerprint after a reputation update. Run the
similarity demo with:

```powershell
python backend/scripts/sensor_similarity.py --sensor-id 54917 --seed-demo-fixtures
```

`--seed-demo-fixtures` creates only rows whose `feature_json.source` is
`demo_fixture`; they are clearly labeled and must not be used as live accuracy
evidence. Without that flag, the command reports only real stored sensors. A
cosine distance is a behavioral-similarity diagnostic, not an accuracy score.
See the [CockroachDB vector documentation](https://www.cockroachlabs.com/docs/stable/vector)
and [vector index documentation](https://www.cockroachlabs.com/docs/stable/vector-indexes).

### Managed MCP Server

CockroachDB Cloud's Managed MCP Server gives an agent read access to the
CockroachDB memory layer. The endpoint is `https://cockroachlabs.cloud/mcp`.
In the CockroachDB Cloud Console, open the organization integrations, choose
the Managed MCP Server, select Codex, prefer OAuth, and scope access to the
`aircord` cluster. The CockroachDB guide also documents the manual Codex
configuration:

```toml
[mcp_servers.cockroachdb-cloud]
url = "https://cockroachlabs.cloud/mcp"
http_headers = { "mcp-cluster-id" = "YOUR_CLUSTER_ID" }
```

After restarting Codex, authenticate with
`codex mcp login cockroachdb-cloud`. API-key authentication is supported by the
provider, but credentials must remain outside the repository. Use the
read-only SQL in [`docs/cockroachdb_mcp_queries.sql`](docs/cockroachdb_mcp_queries.sql)
to back these judge questions:

#### MCP judge questions

- Why was sensor 54917 downweighted?
- What evidence did Aircord use?
- What is its latest reputation score?
- What is the latest resolution and audit trail?
- What is the latest backtest result and its caveats?

See the [Managed MCP Server setup guide](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server)
for the current console, OAuth, and cluster-scope steps.

### MCP demo

See [docs/MCP_DEMO.md](docs/MCP_DEMO.md) for the exact Codex setup, judge
questions, and the actual live answer for why sensor `54917` was downweighted.

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
