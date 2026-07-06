# Data Model: Aircord Air-Quality Trust Memory

## Entity Overview

```text
MetroCluster 1--* Cell
MetroCluster 1--* Monitor
MetroCluster 1--* Sensor
Sensor 1--* SensorReading
Monitor 1--* MonitorReading
Sensor 1--1 SensorReputation
Cell 1--* Estimate
Estimate 1--1 Resolution
Resolution 1--* ResolutionSensor
BacktestRun 1--* BacktestObservation
BacktestRun 1--* BacktestSummary
AuditLog records writes across all mutable entities
```

## MetroCluster

Represents the bounded MVP geography.

Fields:
- `cluster_id`: stable identifier.
- `name`: display name, such as "greater-la" or "bay-area".
- `bounds`: polygon or bounding box.
- `status`: `candidate`, `gate_a_passed`, `gate_a_failed`.
- `gate_a_notes`: evidence for paired anchors, disagreement, and degraded candidates.
- `created_at`, `updated_at`.

Validation rules:
- Exactly one cluster is active for the MVP.
- A cluster cannot move to `gate_a_passed` without enough paired anchors and at
  least one degraded-sensor candidate or explicit failure notes.

## Cell

Represents a grid or reporting area shown in the minimal map.

Fields:
- `cell_id`: stable identifier.
- `cluster_id`: parent cluster.
- `geometry`: cell boundary or centroid.
- `latest_estimate_id`: nullable reference to the latest estimate.
- `version`: integer used for serializable retry checks.
- `updated_at`.

Validation rules:
- Every estimate references one cell.
- Reconciler must re-read `version` inside the commit transaction.

## Monitor

Represents an AirNow regulatory monitor.

Fields:
- `monitor_id`: AirNow/site identifier.
- `cluster_id`.
- `name`.
- `latitude`, `longitude`.
- `status`: `active`, `inactive`, `unknown`.
- `reference_caveat`: standard text that monitors are references, not absolute truth.
- `created_at`, `updated_at`.

## MonitorReading

Timestamped regulatory reading.

Fields:
- `reading_id`.
- `monitor_id`.
- `observed_at`.
- `aqi`.
- `pm25`: nullable if only AQI is available.
- `source_snapshot_uri`: S3/raw snapshot reference.
- `ingested_at`.

Validation rules:
- Readings used in backtests must align to comparable intervals with PurpleAir
  readings.

## Sensor

Represents a PurpleAir community sensor.

Fields:
- `sensor_id`: PurpleAir identifier.
- `cluster_id`.
- `name`.
- `latitude`, `longitude`.
- `nearest_monitor_id`: nullable.
- `likely_indoor`: nullable boolean.
- `status`: `active`, `stale`, `excluded`, `unknown`.
- `version`: integer used for serializable retry checks.
- `created_at`, `updated_at`.

Validation rules:
- Sensors marked `excluded` cannot receive positive resolution weights unless a
  later reputation update clears the exclusion reason.

## SensorReading

Timestamped PurpleAir reading and health signals.

Fields:
- `reading_id`.
- `sensor_id`.
- `cell_id`.
- `observed_at`.
- `pm25_cf1`, `pm25_atm`: nullable numeric values.
- `channel_a_pm25`, `channel_b_pm25`: nullable numeric values.
- `humidity`, `temperature`, `rssi`: nullable health fields.
- `uptime`: nullable numeric value.
- `last_seen_at`: nullable timestamp from source.
- `source_snapshot_uri`: S3/raw snapshot reference.
- `ingested_at`.

Validation rules:
- A reading with stale `last_seen_at` or missing key fields remains auditable but
  receives lower quality contribution.

## SensorReputation

Learned memory state for a PurpleAir sensor.

Fields:
- `sensor_id`.
- `reputation_score`: numeric score normalized for weighting.
- `agreement_score`: agreement with nearest regulatory monitor over time.
- `channel_agreement_score`: A/B channel consistency.
- `uptime_score`.
- `humidity_sensitivity_score`.
- `volatility_score`.
- `drift_score`.
- `indoor_hint_score`.
- `evidence_window_start`, `evidence_window_end`.
- `last_updated_at`.
- `version`: integer used for serializable retry checks.

Validation rules:
- Reputation updates must be tied to an audit row and source evidence.
- Reputation score must be explainable from component scores.

## Estimate

Committed cell-level air-quality estimate.

Fields:
- `estimate_id`.
- `cell_id`.
- `estimated_aqi`.
- `estimated_pm25`: nullable.
- `confidence`: numeric value with display band.
- `method`: `aircord_trust_weighted`.
- `claim_status`: `pending_backtest`, `measured`, or `insufficient_data`.
- `created_at`.

Validation rules:
- No estimate can be displayed without a linked resolution.

## Resolution

Auditable explanation for an estimate.

Fields:
- `resolution_id`.
- `estimate_id`.
- `cell_id`.
- `rationale_text`.
- `monitor_context`: summary JSON.
- `confidence_factors`: summary JSON.
- `reference_caveat`.
- `medical_directive_caveat`.
- `created_at`.

Validation rules:
- Rationale must not claim absolute ground truth or unsupported accuracy.
- Rationale must identify trusted, downweighted, and ignored sensors via
  `ResolutionSensor` rows.

## ResolutionSensor

Per-sensor contribution to a resolution.

Fields:
- `resolution_id`.
- `sensor_id`.
- `reading_id`.
- `weight`.
- `decision`: `trusted`, `downweighted`, `ignored`.
- `reason_codes`: list such as `channel_divergence`, `stale`, `drift`,
  `monitor_disagreement`, `likely_indoor`.
- `reputation_score_at_commit`.
- `created_at`.

Validation rules:
- Weight and decision must agree: ignored sensors have zero weight;
  downweighted sensors have lower weight than healthy trusted sensors.

## BacktestRun

Reproducible run comparing methods.

Fields:
- `backtest_run_id`.
- `cluster_id`.
- `window_start`, `window_end`.
- `status`: `pending`, `passed`, `failed`, `insufficient_data`.
- `failure_reason`: nullable.
- `created_at`, `completed_at`.

Validation rules:
- Accuracy claims require `status = passed` and summary rows for all three
  methods.

## BacktestObservation

Aligned observation used in a backtest.

Fields:
- `backtest_run_id`.
- `observed_at`.
- `monitor_id`.
- `sensor_id`.
- `sensor_health_class`: `healthy`, `degraded`, `unknown`.
- `reference_aqi`.
- `raw_purpleair_aqi`.
- `static_corrected_aqi`.
- `aircord_estimated_aqi`.
- `raw_error`.
- `static_error`.
- `aircord_error`.

Validation rules:
- All methods must use the same aligned timestamp/reference observation.

## BacktestSummary

Aggregated measured results.

Fields:
- `backtest_run_id`.
- `segment`: `all`, `healthy`, `degraded`.
- `method`: `raw_purpleair`, `static_correction`, `aircord`.
- `observation_count`.
- `mean_absolute_error`.
- `median_absolute_error`.
- `notes`.

Validation rules:
- Summaries with too few observations must be labeled insufficient rather than
  used as headline claims.

## AuditLog

Append-only write trail.

Fields:
- `audit_id`.
- `actor`: `airnow_poller`, `purpleair_poller`, `reconciler`, `backtest_runner`.
- `action`: write type.
- `entity_type`.
- `entity_id`.
- `source_snapshot_uri`: nullable.
- `before_version`: nullable.
- `after_version`: nullable.
- `reason`.
- `created_at`.

Validation rules:
- Every estimate, resolution, reputation update, and backtest run must produce
  audit rows.

## State Transitions

Cluster:
- `candidate -> gate_a_passed` when paired anchors, disagreement, and degraded
  candidates are documented.
- `candidate -> gate_a_failed` when data is insufficient for the selected metro.

BacktestRun:
- `pending -> passed` when all three method summaries are computed on aligned
  observations.
- `pending -> insufficient_data` when alignment or sample size is inadequate.
- `pending -> failed` when execution errors prevent a valid result.

SensorReputation:
- Scores update only from new evidence windows.
- Updates commit atomically with affected estimate/resolution when produced by
  reconciliation.
