# Feature Specification: Aircord Air-Quality Trust Memory

**Feature Branch**: `001-air-quality-trust`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description from `docs/aircord-concept-spec.md`, plus locked product decisions in the request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect a reconciled air-quality cell (Priority: P1)

As a hackathon judge or operator, I can open one metro cluster and inspect a
cell where AirNow monitor readings and PurpleAir sensor readings disagree, then
see Aircord's estimate, confidence, contributing sensors, and rationale.

**Why this priority**: This is the smallest complete product loop: conflicting
sources become a reputation-weighted estimate with an auditable explanation.

**Independent Test**: Use one selected metro cluster with paired AirNow and
PurpleAir data. Select a cell and verify the view shows the estimate,
confidence, sensors considered, each sensor's weight, and reasons for trusting,
downweighting, or ignoring sensors.

**Acceptance Scenarios**:

1. **Given** a metro cluster with current AirNow and PurpleAir readings, **When**
   a user selects a cell, **Then** Aircord presents one estimate, confidence,
   and rationale grounded in the sensors and monitor context for that cell.
2. **Given** a sensor with poor channel agreement or poor historical agreement
   with the reference monitor, **When** it contributes to a selected cell,
   **Then** the rationale identifies the sensor as downweighted or ignored and
   explains why.
3. **Given** no adequate supporting readings for a cell, **When** the user
   selects it, **Then** Aircord withholds overconfident claims and reports low
   confidence or insufficient evidence.

---

### User Story 2 - Prove memory changes an outcome (Priority: P1)

As a judge, I can see one degraded PurpleAir sensor whose remembered track
record causes Aircord to downweight it, visibly changing the neighborhood
estimate compared with raw or static-correction-only treatment.

**Why this priority**: This is the "agentic memory" proof. Reputation must alter
the answer, not decorate the UI.

**Independent Test**: Use a degraded-sensor showcase. Compare the cell estimate
with and without the learned reputation weight and verify the trusted estimate,
confidence, and rationale change.

**Acceptance Scenarios**:

1. **Given** a PurpleAir sensor that has drifted or degraded over time, **When**
   Aircord reconciles a nearby cell, **Then** the sensor receives a lower trust
   weight because of its remembered behavior.
2. **Given** the same current readings, **When** raw/static and Aircord methods
   are compared, **Then** Aircord's estimate differs because reputation changed
   the sensor contribution.
3. **Given** the user opens the sensor detail, **When** the system displays the
   memory beat, **Then** it shows the evidence trail behind the downweighting.

---

### User Story 3 - Measure the backtest honestly (Priority: P2)

As a builder or judge, I can review a paired-sensor backtest that compares raw
PurpleAir, static correction, and Aircord's trust-weighted method against
AirNow regulatory monitor references, with no accuracy number shown before it is
computed.

**Why this priority**: The measurable accuracy claim is the strongest proof, but
it must be computed from aligned time series before being used as a headline.

**Independent Test**: Run the backtest on paired PurpleAir and AirNow history.
Verify each method's error is computed from the same aligned observations and
that the report distinguishes healthy sensors from degraded/drifted sensors.

**Acceptance Scenarios**:

1. **Given** paired PurpleAir and AirNow time series, **When** the backtest is
   run, **Then** it reports error for raw PurpleAir, static correction, and
   Aircord using the same reference intervals.
2. **Given** Gate B has not produced measured results, **When** the product
   describes accuracy, **Then** it labels the number as pending rather than
   claiming improvement.
3. **Given** a degraded-sensor subset exists, **When** the report is generated,
   **Then** it separately shows whether Aircord improves on that subset.

---

### User Story 4 - Interrogate sensor reputation memory (Priority: P3)

As a judge or operator, I can ask why a sensor is trusted, downweighted, or
ignored and receive an auditable explanation backed by reputation history and
recent reading quality.

**Why this priority**: Live interrogation reinforces that memory is persistent,
inspectable, and tied to estimates.

**Independent Test**: Select a sensor from a resolved cell and verify the system
shows reputation score, key reputation features, recent evidence, and estimates
affected by that reputation.

**Acceptance Scenarios**:

1. **Given** a sensor included in a resolution, **When** the user opens its
   reputation details, **Then** Aircord shows the reputation factors used for
   that decision.
2. **Given** a sensor has a history of agreement with the nearest reference
   monitor, **When** reputation is inspected, **Then** the system distinguishes
   agreement from other signals such as uptime, channel divergence, humidity
   sensitivity, volatility, and drift.

### Edge Cases

- If no metro cluster has enough paired AirNow/PurpleAir anchors, Gate A fails
  and the project must select another cluster or reduce claims.
- If historical PurpleAir data cannot be aligned with AirNow monitor history,
  Gate B fails and the product must not claim an accuracy improvement.
- If raw PurpleAir, static correction, and Aircord use different time windows or
  sensor subsets, the backtest is invalid until alignment is fixed.
- If a PurpleAir sensor is likely indoor, mislabeled, stale, or missing key
  fields, the estimate must either downweight it or explain why it remains
  trusted.
- If regulatory monitors lag current readings, Aircord must describe them as
  references with latency, not absolute current truth.
- If the explanation generator is unavailable, the system must still preserve
  auditable numeric decisions and avoid unsupported natural-language claims.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aircord MUST ingest or load AirNow regulatory monitor readings for
  one selected metro cluster as the accepted evaluation reference.
- **FR-002**: Aircord MUST ingest or load PurpleAir community sensor readings for
  the same metro cluster, including fields needed to assess sensor health and
  reliability.
- **FR-003**: Aircord MUST preserve raw source snapshots or immutable references
  sufficient to reproduce estimates and backtests.
- **FR-004**: Aircord MUST assign each PurpleAir sensor a learned reputation
  that can change over time.
- **FR-005**: Reputation MUST account for agreement with the nearest regulatory
  monitor when available, A/B channel divergence, missingness or uptime,
  last-seen recency, humidity sensitivity, volatility, drift versus prior
  behavior, and likely indoor or mislabeled hints when available.
- **FR-006**: Aircord MUST compute a per-sensor behavioral fingerprint embedding
  from auditable numeric features and use self-similarity between the current
  fingerprint and recent-history fingerprint as the drift signal feeding
  reputation. This is required for the MVP.
- **FR-007**: Aircord SHOULD extend trust to sensors far from any monitor by
  nearest-neighbor similarity to monitor-anchored sensors
  (reputation-by-analogy), stated as a validated assumption: hold out anchored
  sensors, predict reliability from neighbors, and measure error. This
  cross-sensor propagation MAY be deferred as a stretch.
- **FR-008**: Aircord MUST compute a cell-level air-quality estimate using
  PurpleAir readings weighted by learned reputation and informed by nearby
  regulatory monitor context.
- **FR-009**: Aircord MUST compute and display confidence for each estimate
  based on source quality, agreement, recency, and reputation evidence.
- **FR-010**: Every estimate MUST include a resolution record explaining which
  sensors were trusted, downweighted, or ignored and why.
- **FR-011**: Every reputation update, estimate, resolution, and source snapshot
  reference MUST be auditable after the estimate is produced.
- **FR-012**: Aircord MUST demonstrate one degraded PurpleAir sensor whose
  remembered track record causes downweighting and visibly changes an estimate.
- **FR-013**: Aircord MUST support a paired-location backtest comparing raw
  PurpleAir, static correction, and Aircord's trust-weighted method against
  regulatory monitor references.
- **FR-014**: The backtest MUST report measured results only after aligned time
  series are reconstructed and evaluated.
- **FR-015**: Aircord MUST distinguish healthy-sensor and degraded-sensor
  backtest results when the data supports that split.
- **FR-016**: Aircord MUST explicitly state that regulatory monitors are the
  reference, not absolute ground truth.
- **FR-017**: Aircord MUST explicitly state that PurpleAir is points-billed, not
  fully free.
- **FR-018**: Aircord MUST position AirNow Fire & Smoke Map and Google Maps as
  capable incumbents and identify Aircord's edge as learned, per-sensor,
  auditable memory.
- **FR-019**: Aircord MUST NOT present itself as a health-advice engine or give
  medical directives.
- **FR-020**: Aircord MUST keep the first release scoped to one metro cluster and
  MUST exclude national coverage, mobile apps, user accounts, and forecasting.
- **FR-021**: Aircord MUST make Gate A pass/fail explicit: enough paired data,
  visible disagreement, degraded candidates, and labeled anchors in the chosen
  metro cluster.
- **FR-022**: Aircord MUST make Gate B pass/fail explicit: computable aligned
  time series and three-method error comparison.

### Scope Boundaries and Claim Discipline *(mandatory for Aircord)*

- This feature serves the reputation loop, the measured backtest, auditability,
  and hackathon judging criteria by making learned per-sensor trust the product
  center.
- Locked product decisions preserved: Aircord name, air-quality domain, AirNow
  and PurpleAir sources, learned per-sensor trust as the hero claim, honest
  PurpleAir billing caveat, capable incumbent caveat, and core loop from
  readings to audit trail.
- Claims requiring Gate A evidence: selected metro cluster, enough paired
  anchors, live disagreement, and at least one degraded-sensor candidate.
- Claims requiring Gate B evidence: any accuracy number or statement that
  Aircord beats static correction on degraded sensors.
- Trust-by-analogy claims must never be described as exact; Aircord must state
  the similar-behavior-implies-similar-reliability assumption and show hold-out
  validation before using cross-sensor propagation as evidence.
- Deferred scope: national app, mobile app, accounts, health advice, forecasting,
  and any feature that does not improve trust weighting, measured comparison, or
  auditability.

### Key Entities *(include if feature involves data)*

- **Metro Cluster**: The bounded geographic area selected for the MVP; contains
  regulatory monitors, PurpleAir sensors, grid cells, and paired anchors.
- **Regulatory Monitor**: AirNow monitor used as the accepted reference for
  evaluation; includes location, reading, timestamp, and reporting latency.
- **Community Sensor**: PurpleAir sensor with location, current and historical
  readings, health fields, reputation, and labeling hints.
- **Sensor Reading**: A timestamped PurpleAir observation including pollutant
  values and health signals such as channels, humidity, uptime, and last-seen
  recency.
- **Grid Cell**: A small location area with an estimate, confidence, contributing
  sensors, and current resolution.
- **Reputation Record**: The learned memory state for a sensor, including score,
  evidence factors, trend, and update history.
- **Resolution Record**: The auditable explanation of one estimate, including
  sensors considered, weights, reasons, confidence, and source references.
- **Backtest Run**: A reproducible comparison of raw PurpleAir, static
  correction, and Aircord against regulatory monitor references.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Gate A identifies one metro cluster with at least one regulatory
  monitor, multiple nearby PurpleAir sensors, visible source disagreement, and
  at least one degraded-sensor candidate.
- **SC-002**: For a selected cell, a reviewer can trace the estimate to every
  contributing sensor, weight, downweighting reason, confidence factor, and raw
  source reference in under 2 minutes.
- **SC-003**: The degraded-sensor showcase demonstrates one sensor whose learned
  reputation changes a cell estimate compared with raw or static-correction-only
  treatment.
- **SC-004**: Gate B produces a reproducible table comparing error for raw
  PurpleAir, static correction, and Aircord on the same aligned paired
  observations, or explicitly fails without an accuracy claim.
- **SC-005**: No public-facing claim states an accuracy improvement unless it is
  backed by the Gate B output.
- **SC-006**: All estimate explanations identify regulatory monitors as
  references rather than absolute truth and include the "estimate, not medical
  directive" caveat.
- **SC-007**: The MVP demo can be completed without user accounts, mobile app
  flows, national browsing, forecasting, or health-advice decisions.

## Assumptions

- The first metro cluster will be chosen from areas with dense PurpleAir and
  AirNow coverage, likely greater Los Angeles or the Bay Area.
- Static correction means the established correction baseline used for
  comparison against raw PurpleAir and Aircord's trust-weighted method.
- Regulatory monitors are treated as the evaluation reference because they are
  accepted and calibrated, while still acknowledged as sparse and lagged.
- PurpleAir data access is available through paid/points-billed usage scoped to
  one metro cluster.
- The first release can use a minimal map and detail panel because the core
  product proof is trust reconciliation and auditability.
- Behavioral fingerprint self-similarity drift detection is required for the
  MVP; cross-sensor trust propagation by nearest-neighbor similarity may be
  deferred as a stretch after hold-out validation.
