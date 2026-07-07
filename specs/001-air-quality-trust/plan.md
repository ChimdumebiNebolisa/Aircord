# Implementation Plan: Aircord Air-Quality Trust Memory

**Branch**: `001-air-quality-trust` | **Date**: 2026-07-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-air-quality-trust/spec.md`

## Summary

Build Aircord as a narrow MVP for one metro cluster: ingest AirNow regulatory
monitor readings and PurpleAir community sensor readings, preserve raw
snapshots, compute learned per-sensor reputation, reconcile cell estimates with
confidence and audit rationale, and run a paired backtest comparing raw
PurpleAir, static correction, and Aircord's trust-weighted method. The app
surface is a minimal grid/map plus cell and sensor detail panels. Gate A and
Gate B are first-class deliverables and must pass before app polish.

## Technical Context

**Language/Version**: Python 3.12 for backend, agents, reconciliation, and
backtesting; TypeScript 5.x for minimal frontend.

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy or SQLModel,
CockroachDB-compatible PostgreSQL driver, Alembic, pandas, numpy, boto3, pytest,
Vite, React, TanStack Query, and a lightweight map/grid library.

**Storage**: CockroachDB for monitors, sensors, readings metadata, reputation,
resolutions, estimates, and audit rows; S3 for immutable raw source snapshots.

**Testing**: pytest for unit/integration/backtest checks; contract tests against
OpenAPI; frontend component/smoke tests only after gates pass.

**Target Platform**: Local development first; deployable backend API and worker
logic on AWS Lambda-compatible Python runtime; frontend as static web app.

**Project Type**: Web service plus lightweight frontend plus poller/backtest
workers.

**Performance Goals**: Reconcile one metro cluster on a cadence suitable for
15-minute PurpleAir polling; display selected cell detail in under 2 seconds on
local/demo data; run a bounded paired backtest in under 5 minutes for the MVP
cluster.

**Constraints**: One metro cluster only; no accounts; no mobile app; no
forecasting; no health-advice engine; Bedrock/LLM reasoning must run before any
database transaction opens; CockroachDB transactions must be short,
serializable, and retryable.

**Scale/Scope**: MVP supports tens to low hundreds of PurpleAir sensors and a
small set of AirNow monitors in one metro cluster, enough paired anchors for
Gate A and one degraded-sensor showcase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec-first: PASS. This plan traces directly to FR-001 through FR-022.
- Honest claims: PASS. Accuracy claims remain pending until Gate B; monitors
  are references, not truth; PurpleAir billing and incumbents stay explicit.
- Memory changes outcomes: PASS. Behavioral-fingerprint self-similarity drift
  detection and the degraded-sensor showcase are required deliverables before
  polish.
- Computed metrics only: PASS. Backtest outputs are required before any measured
  improvement claim.
- Scope discipline: PASS. One metro cluster, no accounts, no mobile, no
  national browsing, no forecasting, no medical advice.
- Auditability: PASS. Resolution and audit records are core entities and API
  outputs.
- Short transactions: PASS. Reconciliation computes candidate estimate,
  confidence, and rationale before opening a serializable transaction.
- Testable gates first: PASS. Gate A and Gate B are setup/foundation tasks and
  quickstart checkpoints.

## Project Structure

### Documentation (this feature)

```text
specs/001-air-quality-trust/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- openapi.yaml
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/
|-- pyproject.toml
|-- alembic.ini
|-- alembic/
|-- src/
|   |-- aircord/
|   |   |-- api/
|   |   |-- backtest/
|   |   |-- db/
|   |   |-- ingestion/
|   |   |-- reconciliation/
|   |   |-- reputation/
|   |   `-- audit/
|   `-- main.py
`-- tests/
    |-- contract/
    |-- integration/
    |-- unit/
    `-- fixtures/

frontend/
|-- package.json
|-- src/
|   |-- api/
|   |-- components/
|   |-- pages/
|   `-- styles/
`-- tests/

infra/
|-- aws/
|-- cockroach/
`-- README.md
```

**Structure Decision**: Use a small Python backend/workers package and a minimal
TypeScript frontend. This keeps the data-heavy reconciliation and backtest in
Python while avoiding a large full-stack framework. AWS and CockroachDB
provisioning are documented, not overbuilt, until Gate A and Gate B pass.

## Phase 0: Research

Research decisions are captured in [research.md](research.md). The key
planning decisions are:

- Python/FastAPI is the fastest reliable stack for data ingestion, backtesting,
  and reconciliation.
- CockroachDB is the single transactional memory store; S3 stores raw snapshots.
- Reconciliation uses a compute-then-short-transaction pattern.
- Distributed Vector Indexing is committed for behavioral fingerprints and
  self-similarity drift detection in core reputation. Cross-sensor
  trust-propagation by nearest-neighbor similarity is stretch only, and naive
  raw-reading embeddings are excluded.

## Phase 1: Design & Contracts

Design artifacts:

- [data-model.md](data-model.md): entities, relationships, and state rules.
- [contracts/openapi.yaml](contracts/openapi.yaml): API contract for cluster,
  cell, sensor, and backtest inspection.
- [quickstart.md](quickstart.md): local validation flow for Gate A, Gate B,
  degraded-sensor showcase, and audit trail.

### Post-Design Constitution Check

- Spec-first: PASS. Design files map to the spec requirements and no unrelated
  features were added.
- Honest claims: PASS. Contracts expose `reference_caveat`,
  `claim_status`, and backtest pass/fail state.
- Memory changes outcomes: PASS. Data model includes sensor embeddings,
  reputation, weights, and comparison outputs needed to prove estimate changes.
- Computed metrics only: PASS. Backtest results include measured rows or an
  explicit failed/pending status.
- Scope discipline: PASS. No accounts, national browsing, mobile app,
  forecasting, or health-advice endpoints.
- Auditability: PASS. `resolution`, `resolution_sensor`, and `audit_log`
  records preserve the estimate decision.
- Short transactions: PASS. Transaction boundary is documented in research and
  quickstart validation.
- Testable gates first: PASS. Tasks must implement Gate A and Gate B before UI
  polish.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | N/A | N/A |
