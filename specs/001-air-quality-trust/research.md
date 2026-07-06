# Research: Aircord Air-Quality Trust Memory

## Decision: Use Python/FastAPI for backend, ingestion, reconciliation, and backtesting

**Rationale**: Aircord's core risk is time-series ingestion, data alignment,
sensor scoring, and backtest computation. Python has the shortest path for
pandas/numpy-based data work and a simple FastAPI surface for the demo API.

**Alternatives considered**:
- TypeScript/Node backend: good for one-language full stack, weaker for quick
  time-series analysis and backtest iteration.
- Separate notebook-only pipeline: fast for exploration, but too weak for an
  auditable API and repeatable demo.

## Decision: Use a minimal TypeScript/Vite frontend

**Rationale**: The frontend only needs a grid/map, selected cell details,
sensor reputation details, and backtest summary. Vite/React is fast to scaffold
and keeps UI work contained after Gate A and Gate B.

**Alternatives considered**:
- Full Next.js app: unnecessary routing/server complexity for a hackathon demo.
- Backend-rendered templates: simpler, but less ergonomic for map/detail
  interactions.

## Decision: CockroachDB is the single transactional memory store

**Rationale**: Estimates, reputation state, resolution history, monitor
references, and audit rows need to commit consistently. CockroachDB provides a
single serializable substrate for the memory and concurrent poller/reconciler
writes. The claim is consolidation plus real concurrency, not that the product
is impossible without CockroachDB.

**Alternatives considered**:
- PostgreSQL: also supports serializable transactions, but weaker for the
  contest-specific distributed/concurrent memory story.
- Separate analytical store plus operational database: adds consistency gaps and
  scope without improving the MVP proof.

## Decision: Store immutable raw snapshots in S3 and references in CockroachDB

**Rationale**: Raw source payloads must be reproducible for audits and backtests,
but they do not all need to be stored inline with transactional state. S3 keeps
raw snapshots cheap and immutable while CockroachDB stores references and
derived memory.

**Alternatives considered**:
- Store all raw payloads in CockroachDB: simpler query path, but bloats the
  transactional database and is unnecessary for MVP.
- Store only derived readings: fails auditability and backtest reproducibility.

## Decision: Reconciliation runs compute-first, then commits in a short transaction

**Rationale**: Candidate estimate, confidence, rationale, and reputation deltas
can be computed outside the transaction from a versioned read. The transaction
then re-reads cell/sensor versions, commits estimates, resolutions, reputation
updates, and audit rows, and retries if versions changed.

**Alternatives considered**:
- Keep the transaction open during Bedrock/LLM reasoning: violates the
  constitution and risks slow serializable conflicts.
- Commit estimate and reputation separately: risks memory disagreeing with the
  estimate it produced.

## Decision: Gate A selects the cluster before product polish

**Rationale**: Aircord is not viable without enough paired anchors, live
disagreement, and at least one degraded-sensor candidate. The first operational
workflow must prove the chosen metro cluster supports the story.

**Alternatives considered**:
- Build the UI first with sample data: attractive visually, but risks becoming a
  generic AQI map before the trust proof exists.
- Attempt multiple cities in parallel: too broad for a solo six-week build.

## Decision: Gate B computes the backtest before any accuracy headline

**Rationale**: The hero number must compare raw PurpleAir, static correction,
and Aircord on the same paired observations. If the data does not support the
claim, the demo falls back to the memory beat without inventing a number.

**Alternatives considered**:
- Use synthetic drift or fabricated labels: violates honest claims.
- Report anecdotal examples only: acceptable as fallback, but weaker than a
  measured Gate B result.

## Decision: Reputation starts with transparent hand-crafted features

**Rationale**: The MVP needs explainable reputation features: agreement with the
nearest monitor, A/B channel divergence, missingness, last seen, humidity
sensitivity, volatility, drift, and likely indoor/mislabeled hints. These are
auditable and enough to show memory changing outcomes.

**Alternatives considered**:
- Train a model: too broad and harder to explain.
- Use only static EPA correction: does not prove per-sensor memory.

## Decision: Defer behavioral vector similarity until after gates

**Rationale**: CockroachDB Distributed Vector Indexing is valid only if the
project implements real behavioral fingerprints and validates similarity. That
is useful, but Gate A, Gate B, and the degraded-sensor memory beat are higher
priority.

**Alternatives considered**:
- Embed raw readings for vector search: not defensible and not load-bearing.
- Skip vector indexing entirely: acceptable for MVP if the core gates consume
  available time.
