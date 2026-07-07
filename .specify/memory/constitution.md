<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles:
- Template principle 1 -> I. Spec-First Development
- Template principle 2 -> II. Honest Air-Quality Claims
- Template principle 3 -> III. Memory Changes Outcomes
- Template principle 4 -> IV. Computed Metrics Only
- Template principle 5 -> V. Scope Discipline
- Added VI. Auditability
- Added VII. Short Serializable Transactions
- Added VIII. Testable Gates First
Added sections:
- Product Constraints
- Development Workflow and Quality Gates
Removed sections:
- Placeholder Section 2
- Placeholder Section 3
Templates requiring updates:
- .specify/templates/plan-template.md - updated
- .specify/templates/spec-template.md - updated
- .specify/templates/tasks-template.md - updated
Follow-up TODOs: none
-->
# Aircord Constitution

## Core Principles

### I. Spec-First Development
Code MUST serve the active Spec Kit artifacts: constitution, spec, plan, and
tasks. Implementation decisions that change product behavior MUST first update
the relevant artifact, then the code. Unrelated refactors, polish, or feature
expansion are prohibited unless the spec calls for them.

Rationale: Aircord is judged on a sharp trust/reconciliation thesis. Drift from
the spec would turn it into a generic AQI map.

### II. Honest Air-Quality Claims
Aircord MUST NOT claim absolute ground truth. Regulatory monitors are the
reference for evaluation, not perfect truth. The product MUST state that
PurpleAir is points-billed, that AirNow Fire & Smoke Map and Google Maps are
capable incumbents, and that Aircord's edge is learned, per-sensor, auditable
memory rather than merely merging sources.

Rationale: Credibility is part of the product. Overclaiming weakens the demo and
the science.

### III. Memory Changes Outcomes
Per-sensor reputation MUST visibly affect estimates, confidence, and rationale.
Reputation cannot be decorative metadata. At least one degraded PurpleAir sensor
MUST be downweighted because of remembered behavior, and the resulting estimate
MUST differ from a raw or static-correction-only estimate.

Rationale: Agentic memory is the core product proof.

### IV. Computed Metrics Only
Aircord MUST NOT present an accuracy, improvement, or backtest number until it
has been computed from aligned PurpleAir and AirNow time series. The system MAY
describe intended metrics before Gate B, but MUST label them as pending.

Rationale: The headline number is valuable only if it is measured.

### V. Scope Discipline
The first build MUST stay within one metro cluster, AirNow regulatory monitors,
PurpleAir community sensors, a minimal map plus cell detail panel, audit trail,
paired-sensor backtest, and degraded-sensor showcase. National coverage, mobile
apps, user accounts, forecasting, and health-advice engines are out of scope.

Rationale: A solo six-week hackathon build needs proof over breadth.

### VI. Auditability
Every committed estimate MUST be explainable from persisted records. The audit
trail MUST show which sensors were trusted, downweighted, or ignored; the reason
for each decision; the confidence; the source readings or raw snapshot
references; and the reputation state used at commit time.

Rationale: Trust reconciliation without inspection is not defensible.

### VII. Short Serializable Transactions
Bedrock or other LLM reasoning MUST run outside CockroachDB transactions. A
reconciliation transaction MUST be short and serializable: re-read relevant
cell/sensor versions, commit estimates, resolutions, reputation updates, and
audit rows, then retry from reasoning if versions changed. Long external calls
inside the transaction are forbidden.

Rationale: The database argument depends on consistent memory under real
concurrent writes, not open transactions waiting on remote reasoning.

### VIII. Testable Gates First
Gate A and Gate B MUST be planned and implemented before app polish. Gate A
proves live paired disagreement and enough labeled anchors in one metro cluster.
Gate B proves the three-method backtest is computable and reports only measured
results.

Rationale: The product's credibility rests on data availability and measurable
comparison before UI polish.

## Product Constraints

- Product identity is Aircord: an agentic memory for air-quality trust and
  reconciliation.
- The domain is air quality, not parking or a generic sensor dashboard.
- Sources are AirNow regulatory monitors and PurpleAir community sensors.
- The core loop is monitor readings plus PurpleAir readings, reputation-weighted
  estimate, confidence, rationale, reputation update, and audit trail.
- CockroachDB is justified by one consistent transactional memory substrate plus
  genuine concurrent writes. Claims that the product is impossible without
  CockroachDB are prohibited.
- AWS services have specific roles: Lambda pollers, S3 raw snapshots, and
  Bedrock explanation/reasoning outside the database transaction.
- CockroachDB Managed MCP Server is valid for live memory interrogation.
  Distributed Vector Indexing is a committed second CockroachDB tool for
  behavioral fingerprinting and self-similarity drift detection. Cross-sensor
  trust propagation by nearest-neighbor similarity is optional stretch work and
  must be validated before use. Claims that the product is impossible without
  CockroachDB are prohibited.

## Development Workflow and Quality Gates

1. Specifications MUST preserve locked product decisions before planning.
2. Plans MUST include research.md, data-model.md, contracts when APIs are
   planned, quickstart.md, and explicit Gate A/Gate B validation steps.
3. Tasks MUST put Gate A and Gate B before frontend polish and before optional
   cross-sensor trust propagation work.
4. Before implementation, spec.md, plan.md, research.md, data-model.md,
   contracts, quickstart.md, and tasks.md MUST be checked for contradictions.
5. Any feature that does not serve the reputation loop, measured backtest,
   auditability, or hackathon judging criteria MUST be cut or deferred.

## Governance

This constitution supersedes all other process guidance for Aircord. Changes
require an explicit constitution update, a Sync Impact Report, and review of
dependent templates and active Spec Kit artifacts.

Versioning follows semantic versioning:
- MAJOR: Removes or redefines a core principle or product constraint.
- MINOR: Adds a principle, quality gate, or materially expands governance.
- PATCH: Clarifies wording without changing obligations.

Compliance review is mandatory during `/speckit-plan`, `/speckit-tasks`, and
pre-implementation analysis. Violations must be resolved in the spec, plan, or
tasks before implementation proceeds.

**Version**: 1.1.0 | **Ratified**: 2026-07-06 | **Last Amended**: 2026-07-07
