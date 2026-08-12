# Aircord Submission Narrative Lock

Use this language across the Devpost entry, demo page, video, screenshots, and judge conversations. Do not broaden the claims.

## Project title

Aircord - Agentic Memory for Sensor Trust

## Tagline

Aircord learns which community air sensors to trust and explains every downweighted reading.

## One-sentence explanation

Aircord is an agentic memory layer for unreliable sensor networks: it compares cheap community air sensors against regulatory references, remembers each sensor’s behavior, downweights suspicious readings, and records an auditable decision in CockroachDB.

## Hero hook

A community air sensor said the air was clean. Aircord remembered not to trust it.

## Exact demo case

PurpleAir sensor 54917 reported PM2.5 = 0 while a nearby AirNow monitor reported AQI 64. Aircord retrieved the sensor’s stored reputation, assigned it only 0.1986 weight, blended the estimate toward the reference, and stored the decision with an audit trail.

## What the agent does

For each new reading, the Aircord memory loop retrieves the sensor’s stored reliability state, compares the community reading with the regulatory reference, selects a transparent trust decision, computes a weighted estimate, and atomically records the updated memory, resolution, and audit evidence. The important behavior is retrieval before action: the previous reputation changes how much influence the new reading receives.

## What CockroachDB remembers

CockroachDB is the persistent operational memory for:

- community sensors and normalized readings;
- AirNow monitor references;
- per-sensor reputation and behavioral state;
- trust-weighted cell estimates;
- resolutions with decisions, weights, reason codes, and explanations;
- immutable-style audit records of ingestion and memory updates;
- bounded backtest runs and summaries; and
- `VECTOR(8)` behavioral fingerprints in `sensor_embeddings`.

## What AWS does

- **AWS Lambda** runs the serverless PurpleAir ingestion path.
- **Amazon EventBridge** schedules that Lambda every 15 minutes.
- **Amazon S3** archives the raw PurpleAir and AirNow responses before normalized records are written to CockroachDB, preserving source evidence for later inspection.

## What the two CockroachDB tools do

1. **CockroachDB Cloud Managed MCP Server** gives Codex read-only access to the live CockroachDB memory. It supports the judge question, “Why was sensor 54917 downweighted?” The stored answer is channel divergence and monitor disagreement.
2. **CockroachDB Distributed Vector Indexing** stores and searches `VECTOR(8)` behavioral fingerprints. The similarity query compares reputation, channel difference, recent PM2.5, missingness, freshness, monitor difference, drift, and confidence. Cosine distance is a behavioral-similarity diagnostic, not an accuracy score.

## What the project does not claim

Aircord does not claim absolute air-quality truth or medical guidance. AirNow is used as a regulatory reference, and the current backtest is a small reference-based proof, not a broad accuracy claim. PM2.5 and AQI are different measures, and their comparison is intentionally disclosed.

## 10-second judge explanation

A community sensor reported PM2.5 of zero while the nearby AirNow reference reported AQI 64. Aircord retrieved that sensor’s CockroachDB reputation, reduced its weight to 0.1986, and stored an explained, auditable decision.

## 30-second judge explanation

Aircord is an agentic memory layer for unreliable sensor networks. When PurpleAir sensor 54917 reported PM2.5 of zero but the nearby AirNow reference reported AQI 64, Aircord did not treat the new reading in isolation. It retrieved the sensor’s stored reputation from CockroachDB, downweighted the reading to 0.1986, blended the estimate toward the reference, and wrote the resolution and audit trail back to memory. CockroachDB also supports behavioral similarity through `VECTOR(8)` and live inspection through Managed MCP, while Lambda, EventBridge, and S3 operate the ingestion and raw-evidence pipeline.
