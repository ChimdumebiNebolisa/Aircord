# Aircord repository instructions

## Purpose and boundaries

Aircord is a one-metro air-quality trust-memory MVP. The core loop is AirNow
regulatory reference data plus PurpleAir community readings, transparent
per-sensor reputation, a trust-weighted estimate, an auditable resolution, and
a paired backtest. Keep work inside the trust/reputation loop, measured
backtest, auditability, or the judge-facing proof surface. Do not add accounts,
national coverage, forecasting, mobile apps, or medical-advice behavior.

## Stack and structure

- `backend/` is Python 3.12, FastAPI, and a local SQLite fallback behind a
  repository boundary. Keep the schema compatible with the planned CockroachDB
  transactional store.
- `frontend/` is a minimal Vite/React/TypeScript inspection surface. The UI is
  a grid/map plus cell detail, degraded-sensor memory beat, and backtest panels.
- `specs/001-air-quality-trust/` contains the authoritative constitution,
  feature spec, plan, data model, API contract, quickstart, and task list.
- `infra/` documents AWS/CockroachDB boundaries; do not claim live deployment
  or live data validation without exercising it.

## Commands

From the repository root:

```powershell
python -m pip install -e 'backend[dev]'
pytest backend/tests
uvicorn aircord.main:app --reload
cd frontend; npm install; npm run build
```

The default local mode uses deterministic fixtures. Set `AIRCORD_DB_PATH` to
an isolated SQLite file for tests or demos. Live AirNow/PurpleAir ingestion
requires `AIRNOW_API_KEY` and `PURPLEAIR_API_KEY`; never commit those values.

## Invariants

- Regulatory monitors are a reference for evaluation, not absolute truth.
- Aircord must not show a measured accuracy claim until aligned backtest data
  has produced it; pending/insufficient results must remain explicit.
- Reputation must change an estimate and rationale for at least one degraded
  sensor. Persist trusted, downweighted, and ignored decisions with reasons.
- Compute explanations and candidate estimates before opening the commit
  transaction. The transaction rechecks versions and atomically writes the
  estimate, resolution, reputation updates, and audit rows.
- Keep the medical-directive caveat visible: this is an estimate, not medical
  advice. PurpleAir is points-billed and the incumbent is capable; Aircord's
  distinction is persistent, per-sensor, auditable memory.

## Project-local skill

The repository includes Spec Kit skills under `.agents/skills/`. Use the
implementation skill when executing `specs/001-air-quality-trust/tasks.md`,
and preserve the constitution/spec/plan/tasks alignment when product behavior
changes.

