# Tasks: Aircord Air-Quality Trust Memory

**Input**: Design documents from `specs/001-air-quality-trust/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Gate, contract, integration, and unit test tasks are included because
the constitution requires testable gates before polish.

**Organization**: Tasks are grouped by setup, foundations, and user story so
each story can be validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the repo structure and tooling without implementing product behavior.

- [ ] T001 Create backend package structure in backend/src/aircord/
- [ ] T002 Create backend project config in backend/pyproject.toml
- [ ] T003 [P] Create backend test directories in backend/tests/
- [ ] T004 [P] Create frontend Vite project skeleton in frontend/package.json and frontend/src/
- [ ] T005 [P] Create infrastructure documentation skeleton in infra/README.md
- [ ] T006 Configure local environment template in .env.example
- [ ] T007 Configure backend lint/test commands in backend/pyproject.toml

---

## Phase 2: Foundational Gates and Data Memory (Blocking)

**Purpose**: Implement the data substrate and Gate A/Gate B proof path before app polish.

**CRITICAL**: No frontend polish, cross-sensor trust propagation, national scope, accounts, forecasting, or health-advice work can begin before this phase is complete.

- [ ] T008 Create CockroachDB migration framework in backend/alembic.ini and backend/alembic/
- [ ] T009 Create initial schema migration for clusters, cells, monitors, sensors, readings, reputation, estimates, resolutions, backtests, and audit log in backend/alembic/versions/
- [ ] T010 [P] Implement database session and retry helpers in backend/src/aircord/db/session.py
- [ ] T011 [P] Implement S3 snapshot reference interface in backend/src/aircord/ingestion/snapshots.py
- [ ] T012 [P] Create domain models matching data-model.md in backend/src/aircord/db/models.py
- [ ] T013 Create repository helpers for versioned cell and sensor reads in backend/src/aircord/db/repositories.py
- [ ] T014 [P] Add unit tests for reputation feature calculations in backend/tests/unit/test_reputation_features.py
- [ ] T015 [P] Add unit tests for static correction baseline in backend/tests/unit/test_static_correction.py
- [ ] T016 Implement AirNow poller/client boundary in backend/src/aircord/ingestion/airnow.py
- [ ] T017 Implement PurpleAir poller/client boundary in backend/src/aircord/ingestion/purpleair.py
- [ ] T018 Implement bounded metro cluster discovery in backend/src/aircord/ingestion/discover_cluster.py
- [ ] T019 Add Gate A integration test with fixture data in backend/tests/integration/test_gate_a_cluster_discovery.py
- [ ] T020 Implement reputation scoring service in backend/src/aircord/reputation/scoring.py
- [ ] T021 Implement hand-crafted behavioral feature vector computation in backend/src/aircord/reputation/fingerprints.py
- [ ] T022 Store sensor_embeddings using CockroachDB vector indexing in backend/src/aircord/reputation/embeddings.py
- [ ] T023 Compute drift via fingerprint self-similarity and feed drift_score into reputation scoring in backend/src/aircord/reputation/scoring.py
- [ ] T024 Implement raw, static-correction, and Aircord method estimators in backend/src/aircord/reconciliation/methods.py
- [ ] T025 Implement paired time-series alignment in backend/src/aircord/backtest/alignment.py
- [ ] T026 Implement Gate B backtest runner in backend/src/aircord/backtest/run.py
- [ ] T027 Add Gate B integration test comparing all three methods on aligned fixtures in backend/tests/integration/test_gate_b_backtest.py
- [ ] T028 Implement audit log writer in backend/src/aircord/audit/log.py
- [ ] T029 Implement reconciliation compute phase outside the transaction in backend/src/aircord/reconciliation/compute.py
- [ ] T030 Implement short serializable reconciliation commit with retry in backend/src/aircord/reconciliation/commit.py
- [ ] T031 Add integration test proving reconciliation commits estimate, resolution, reputation updates, and audit rows atomically in backend/tests/integration/test_reconciliation_commit.py

**Checkpoint**: Gate A and Gate B paths are runnable against fixtures or live scoped data, and the core memory transaction path is test-covered.

---

## Phase 3: User Story 1 - Inspect a reconciled air-quality cell (Priority: P1)

**Goal**: A reviewer can inspect one cell and see estimate, confidence, sensors, weights, and rationale.

**Independent Test**: Select a cell from the API and verify the response traces the estimate to sensors, weights, reasons, confidence factors, caveats, and raw references.

### Tests for User Story 1

- [ ] T032 [P] [US1] Add contract test for GET /clusters/active in backend/tests/contract/test_clusters_contract.py
- [ ] T033 [P] [US1] Add contract test for GET /clusters/active/cells in backend/tests/contract/test_cells_contract.py
- [ ] T034 [P] [US1] Add contract test for GET /cells/{cell_id} in backend/tests/contract/test_cell_detail_contract.py
- [ ] T035 [US1] Add integration test for cell audit inspection in backend/tests/integration/test_cell_audit_inspection.py

### Implementation for User Story 1

- [ ] T036 [US1] Implement FastAPI app bootstrap in backend/src/aircord/main.py
- [ ] T037 [US1] Implement cluster and cell API routes in backend/src/aircord/api/cells.py
- [ ] T038 [US1] Implement cell detail serialization with caveats in backend/src/aircord/api/schemas.py
- [ ] T039 [US1] Implement minimal frontend API client in frontend/src/api/aircord.ts
- [ ] T040 [US1] Implement minimal grid/map view in frontend/src/pages/ClusterView.tsx
- [ ] T041 [US1] Implement cell detail panel in frontend/src/components/CellDetailPanel.tsx
- [ ] T042 [US1] Wire frontend route and app shell in frontend/src/App.tsx

**Checkpoint**: User Story 1 is demoable without any additional stories.

---

## Phase 4: User Story 2 - Prove memory changes an outcome (Priority: P1)

**Goal**: Demonstrate one degraded PurpleAir sensor whose learned reputation changes a cell estimate.

**Independent Test**: Request the degraded-sensor showcase and verify raw/static and Aircord estimates differ because the sensor was downweighted.

### Tests for User Story 2

- [ ] T043 [P] [US2] Add contract test for GET /showcases/degraded-sensor in backend/tests/contract/test_degraded_showcase_contract.py
- [ ] T044 [US2] Add integration test for reputation changing an estimate in backend/tests/integration/test_memory_changes_outcome.py

### Implementation for User Story 2

- [ ] T045 [US2] Implement degraded-sensor selection service in backend/src/aircord/reputation/showcase.py
- [ ] T046 [US2] Implement degraded-sensor API route in backend/src/aircord/api/showcases.py
- [ ] T047 [US2] Implement estimate comparison payload in backend/src/aircord/reconciliation/comparison.py
- [ ] T048 [US2] Add degraded-sensor showcase panel in frontend/src/components/DegradedSensorPanel.tsx
- [ ] T049 [US2] Connect showcase panel to cluster view in frontend/src/pages/ClusterView.tsx

**Checkpoint**: The same input data produces a different outcome because learned memory changes sensor weight.

---

## Phase 5: User Story 3 - Measure the backtest honestly (Priority: P2)

**Goal**: Show measured raw, static, and Aircord error only after aligned time-series comparison succeeds.

**Independent Test**: Run or request a backtest and verify measured summaries appear only when Gate B passes.

### Tests for User Story 3

- [ ] T050 [P] [US3] Add contract test for GET /backtests/latest in backend/tests/contract/test_backtest_latest_contract.py
- [ ] T051 [P] [US3] Add contract test for POST /backtests in backend/tests/contract/test_backtest_create_contract.py
- [ ] T052 [US3] Add integration test preventing measured claims when Gate B is insufficient in backend/tests/integration/test_backtest_claim_status.py

### Implementation for User Story 3

- [ ] T053 [US3] Implement backtest persistence service in backend/src/aircord/backtest/store.py
- [ ] T054 [US3] Implement backtest API routes in backend/src/aircord/api/backtests.py
- [ ] T055 [US3] Implement backtest summary formatter with claim_status in backend/src/aircord/backtest/summary.py
- [ ] T056 [US3] Add backtest summary panel in frontend/src/components/BacktestPanel.tsx
- [ ] T057 [US3] Connect backtest summary to cluster view in frontend/src/pages/ClusterView.tsx

**Checkpoint**: Accuracy claims are either measured by Gate B or explicitly withheld.

---

## Phase 6: User Story 4 - Interrogate sensor reputation memory (Priority: P3)

**Goal**: A reviewer can inspect why a sensor is trusted, downweighted, or ignored.

**Independent Test**: Open a sensor reputation detail and verify reputation factors, evidence window, and affected estimates are shown.

### Tests for User Story 4

- [ ] T058 [P] [US4] Add contract test for GET /sensors/{sensor_id}/reputation in backend/tests/contract/test_sensor_reputation_contract.py
- [ ] T059 [US4] Add integration test for sensor reputation audit trail in backend/tests/integration/test_sensor_reputation_audit.py

### Implementation for User Story 4

- [ ] T060 [US4] Implement sensor reputation API route in backend/src/aircord/api/sensors.py
- [ ] T061 [US4] Implement reputation detail serializer in backend/src/aircord/reputation/detail.py
- [ ] T062 [US4] Add sensor reputation panel in frontend/src/components/SensorReputationPanel.tsx
- [ ] T063 [US4] Link sensor decisions in cell detail to reputation panel in frontend/src/components/CellDetailPanel.tsx

**Checkpoint**: Sensor memory is inspectable and tied to estimate decisions.

---

## Phase 7: Polish and Deferred Enhancements

**Purpose**: Only after gates and the proof loop work, improve demo reliability and optional extensions.

- [ ] T064 [P] Update quickstart validation notes in specs/001-air-quality-trust/quickstart.md
- [ ] T065 Run all backend tests and fix regressions in backend/tests/
- [ ] T066 Run frontend smoke tests and fix regressions in frontend/tests/
- [ ] T067 Add AWS Lambda handler wrappers for pollers in backend/src/aircord/ingestion/lambda_handlers.py
- [ ] T068 Implement cross-sensor trust propagation by nearest-neighbor similarity only if Gate A, Gate B, self-similarity drift detection, and memory beat are already passing in backend/src/aircord/reputation/propagation.py
- [ ] T069 Add deployment notes for S3, Lambda, Bedrock, and CockroachDB in infra/README.md
- [ ] T070 Add Managed MCP Server interrogation examples in infra/cockroach/mcp.md
- [ ] T071 Add optional cross-sensor reputation-by-analogy research note in specs/001-air-quality-trust/research.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational Gates and Data Memory (Phase 2)**: Depends on setup and blocks all user stories.
- **US1 and US2 (Phases 3-4)**: Depend on Phase 2; both are MVP-critical.
- **US3 (Phase 5)**: Depends on Phase 2 and can proceed after backtest persistence is ready.
- **US4 (Phase 6)**: Depends on Phase 2 and can proceed after US1 sensor decisions exist.
- **Polish (Phase 7)**: Depends on Gate A, Gate B, and the memory beat.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2.
- **US2 (P1)**: Starts after Phase 2; integrates with US1 UI if available.
- **US3 (P2)**: Starts after Phase 2; does not require UI polish.
- **US4 (P3)**: Starts after Phase 2 and benefits from US1 cell details.

### Parallel Opportunities

- T003, T004, and T005 can run in parallel.
- T010, T011, T012, T014, and T015 can run in parallel after T008 starts.
- Contract tests T032-T034 can run in parallel.
- US2 contract and integration tests can be prepared before showcase implementation.
- Frontend panels for US2, US3, and US4 can proceed in parallel after the API schemas stabilize.

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup.
2. Complete Phase 2 gates and core memory.
3. Complete US1 cell inspection and US2 degraded-sensor memory beat.
4. Stop and validate quickstart Gate A, Gate B, reconciliation, and audit trail.
5. Add US3 and US4 only if the proof loop is stable.

### Scope Guard

Cut or defer any task that does not support reputation weighting, measured
backtest, auditability, or judge-facing proof. T068 is optional and must not
delay Gate A, Gate B, self-similarity drift detection, or the degraded-sensor
showcase.
