# Quickstart: Aircord Air-Quality Trust Memory

This guide defines the validation path the implementation must satisfy. It does
not claim the app is implemented yet.

## Prerequisites

- Python 3.12
- Node.js 20+
- CockroachDB connection string for local or managed cluster
- S3 bucket or local S3-compatible bucket for raw snapshots
- AirNow API access for regulatory monitor data
- PurpleAir API access with enough points for one metro cluster
- Optional Bedrock access for generated explanation text; numeric audit records
  must still work if Bedrock is unavailable

## Setup

```powershell
cd C:\Users\Chimdumebi\Aircord
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e backend[dev]
cd frontend
npm install
```

Expected outcome: backend and frontend dependencies install without creating
any production data.

## Gate A: Live Paired Disagreement

Run the cluster discovery workflow for one candidate metro cluster.

```powershell
python -m aircord.ingestion.discover_cluster --cluster greater-la
```

Expected outcome:

- AirNow monitor candidates are listed.
- PurpleAir sensors near those monitors are listed.
- The report identifies paired anchors and current disagreement.
- The report flags at least one degraded-sensor candidate or fails Gate A with a
  clear reason.
- No national scan is performed.

Pass rule: Gate A passes only if there are enough paired anchors, visible
disagreement, and degraded-sensor candidates for the MVP story.

## Gate B: Computable Backtest

Run the bounded backtest using aligned PurpleAir and AirNow time series.

```powershell
python -m aircord.backtest.run --cluster greater-la --window-days 14
```

Expected outcome:

- The run aligns PurpleAir and AirNow observations to common intervals.
- The output reports raw PurpleAir, static correction, and Aircord errors using
  the same paired observations.
- Results are segmented when healthy/degraded classification is supported.
- If data is insufficient, the command exits with an insufficient-data result
  and no accuracy headline is produced.

Pass rule: Gate B passes only when all three method summaries are computed from
the same aligned observations.

## Reconciliation Transaction Boundary

Run one reconciliation cycle against seeded or live cluster data.

```powershell
python -m aircord.reconciliation.run_once --cluster greater-la
```

Expected outcome:

- Candidate estimate, confidence, rationale, and reputation deltas are computed
  before the commit transaction opens.
- The commit transaction re-reads cell and sensor versions.
- Estimate, resolution, resolution sensors, reputation updates, and audit rows
  commit atomically.
- If a version changed, the cycle retries from candidate computation.

## Degraded-Sensor Memory Beat

Request the showcase endpoint after Gate A and at least one reconciliation run.

```powershell
curl http://localhost:8000/showcases/degraded-sensor
```

Expected outcome:

- Response identifies one degraded sensor.
- Response shows raw/static estimate and Aircord estimate.
- Response explains the remembered behavior that lowered the sensor weight.
- The estimate differs because reputation changed the contribution.

## Cell Audit Inspection

Start the API and frontend.

```powershell
uvicorn aircord.main:app --reload
cd frontend
npm run dev
```

Open the local frontend and select a cell.

Expected outcome:

- The cell detail shows estimate, confidence, and rationale.
- Sensors are grouped or labeled as trusted, downweighted, or ignored.
- Each decision has reason codes and reputation score at commit.
- The UI includes reference and medical-directive caveats.

## Contract Validation

```powershell
pytest backend/tests/contract
```

Expected outcome:

- API responses conform to `contracts/openapi.yaml`.
- Backtest endpoints never return a measured claim when Gate B is pending or
  insufficient.

## Stop Condition Before Polish

Do not spend time on UI polish, national browsing, mobile flows, accounts,
forecasting, vector search, or health advice until:

- Gate A has passed for one metro cluster.
- Gate B has either produced measured results or explicitly failed.
- One degraded-sensor memory beat changes an estimate.
- Resolution and audit rows explain the estimate.
