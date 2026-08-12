# Devpost Draft

This is local draft copy only. Nothing has been sent to Devpost.

## 1. Project name

Aircord - Agentic Memory for Sensor Trust

## 2. Tagline

Aircord learns which community air sensors to trust and explains every downweighted reading.

## 3. Public demo URL

https://aircord-demo.vercel.app/

## 4. Repository URL

https://github.com/ChimdumebiNebolisa/Aircord

## 5. License URL

https://github.com/ChimdumebiNebolisa/Aircord/blob/main/LICENSE

## 6. Built with

- CockroachDB Cloud
- CockroachDB Managed MCP Server
- CockroachDB Distributed Vector Indexing
- AWS Lambda
- Amazon EventBridge
- Amazon S3
- PurpleAir API
- AirNow API
- Python
- FastAPI
- React
- TypeScript
- Vite
- Tailwind CSS
- Vercel
- Codex
- Spec Kit
- Design DNA

## 7. Inspiration

Community air sensors are dense, fast, and useful, but a device can drift, disagree across channels, or fail while still producing a fresh timestamp. Regulatory monitors provide a stronger reference but are sparse. We wanted a system that could remember how each inexpensive sensor had behaved, use that memory on the next reading, and explain the result instead of treating every observation as equally trustworthy.

The project became concrete when PurpleAir sensor 54917 reported PM2.5 = 0 while the nearby Compton AirNow monitor reported AQI 64. That is the story Aircord is designed to make inspectable: a community air sensor said the air was clean, and Aircord remembered not to trust it.

## 8. What it does

Aircord is an agentic memory layer for unreliable sensor networks. It ingests community and regulatory observations, stores each sensor’s reliability state, retrieves that state before evaluating a new reading, and uses the remembered reputation to select a trust weight.

In the live demo, sensor 54917 had a stored reputation of 0.3973. Aircord recorded channel divergence and monitor disagreement, classified the reading as `downweighted`, assigned it a 0.1986 weight, blended the estimate toward the AirNow reference, and persisted an adjusted estimate of 51.3 with medium confidence. The page exposes the input evidence, formula, resolution reasoning, audit trail, vector similarity, bounded backtest, and Managed MCP proof.

## 9. How we built it

The backend is Python 3.12 and FastAPI behind a repository boundary that supports CockroachDB Cloud and a deterministic SQLite test fallback. The memory loop computes candidate reputation, weights, estimates, and explanations, then writes the estimate, resolution, reputation update, vector fingerprint, and audit records through the CockroachDB repository.

PurpleAir ingestion runs in AWS Lambda on a 15-minute Amazon EventBridge schedule. Raw PurpleAir and AirNow responses are archived in Amazon S3 before normalized records are persisted. CockroachDB stores the operational memory and `VECTOR(8)` fingerprints. A read-only API and `demo_status.py` produce the same judge-facing summary. For reliable public judging, the Vite/React frontend reads a timestamped CockroachDB-backed snapshot deployed on Vercel; it contains persisted evidence, not fabricated placeholders or credentials.

Codex helped inspect the repository, configure and query CockroachDB Managed MCP, test the memory path, shape the judge-facing frontend, preserve caveats, verify the public deployment, and prepare this submission packet. Spec Kit kept the product scope and architecture aligned; Design DNA guided the final technical visual system.

## 10. How CockroachDB is meaningfully integrated

CockroachDB is not just storage. It is Aircord’s persistent memory layer for sensor state, normalized readings, monitor references, reputation, estimates, resolutions, audit history, vector fingerprints, and backtest runs. Before Aircord acts on a new reading, the agent retrieves that sensor’s stored reliability memory. That memory changes the output: sensor 54917 receives only 0.1986 weight, so the adjusted estimate is blended toward the regulatory reference. The resulting decision, reasons, estimate, and audit trail are written back to CockroachDB for the next cycle. Managed MCP lets Codex interrogate the live memory and explain why the sensor was downweighted, while Distributed Vector Indexing stores and queries `VECTOR(8)` behavioral fingerprints for sensor-similarity diagnostics.

## 11. How AWS is meaningfully integrated

AWS operates the evidence-ingestion path. AWS Lambda executes the PurpleAir ingestion code without a continuously running server. Amazon EventBridge schedules that Lambda every 15 minutes. Amazon S3 stores immutable raw PurpleAir and AirNow response snapshots before normalization, preserving the source evidence linked from CockroachDB readings and audit rows. Together, AWS acquires and preserves observations; CockroachDB turns those observations into persistent decision memory.

## 12. What CockroachDB tools were used

1. **CockroachDB Cloud Managed MCP Server** — Codex connects through OAuth-scoped MCP and asks read-only questions of the live CockroachDB memory. For “Why was sensor 54917 downweighted?”, the stored evidence reports `channel_divergence` and `monitor_disagreement`.
2. **CockroachDB Distributed Vector Indexing** — `sensor_embeddings` stores explainable `VECTOR(8)` fingerprints, and cosine search returns sensors or fixtures with similar behavioral feature directions. This is a similarity diagnostic, not an accuracy score.

## 13. What AWS services were used

- **AWS Lambda** — serverless PurpleAir ingestion.
- **Amazon S3** — raw PurpleAir and AirNow evidence archive.
- **Amazon EventBridge** — scheduled 15-minute Lambda execution.

## 14. Challenges we ran into

- Preserving a reported PM2.5 value of zero without allowing one suspicious sensor to force the entire estimate to zero.
- Keeping the trust formula simple enough to inspect while still making stored reputation materially change the outcome.
- Aligning sparse AirNow observations with a small PurpleAir history without overstating the backtest.
- Making CockroachDB memory, vector similarity, MCP, AWS ingestion, and caveats understandable on one judge-facing page.
- Publishing a dependable demo without exposing database credentials, solved by generating a timestamped public-safe snapshot from CockroachDB.

## 15. Accomplishments

- Built a complete store-retrieve-act-write memory loop in which persisted sensor reputation changes the next estimate.
- Persisted explained resolutions and audit rows atomically with memory updates.
- Demonstrated a real downweighted case using sensor 54917 and monitor 060371302.
- Integrated two CockroachDB tools: Managed MCP Server and Distributed Vector Indexing.
- Deployed an AWS Lambda/EventBridge/S3 ingestion and evidence path.
- Published a public, inspectable demo with the live memory case and honest limitations.

## 16. What we learned

Agentic memory becomes convincing when retrieval changes a visible decision, not merely when records exist. We also learned that operational evidence matters as much as a score: source keys, reason codes, formula readback, resolutions, and audit events make the system defensible. Finally, similarity and backtest outputs need explicit boundaries so judges can distinguish useful diagnostics from broad accuracy claims.

## 17. What’s next

After the hackathon, the next responsible steps would be longer aligned observation windows, more regulatory reference history, careful calibration across additional sensors, and operational monitoring of the deployed ingestion path. Those are future validation steps, not capabilities claimed by the current demo.

## 18. Caveats and honesty notes

Aircord does not claim absolute air-quality truth or medical guidance. AirNow is used as a regulatory reference, and the current backtest is a small reference-based proof, not a broad accuracy claim. PurpleAir PM2.5 and AirNow AQI are different measures. The vector fingerprint is handcrafted and explainable, not a trained accuracy model. Similarity fixtures are clearly labeled and are not used as live accuracy evidence.

## 19. Required Devpost custom answers draft

### CockroachDB tools

- Cloud Managed MCP Server
- Distributed Vector Indexing

### AWS services

- AWS Lambda
- Amazon S3
- Other AWS service: Amazon EventBridge

### Meaningful integration

CockroachDB is not just storage in Aircord. It is the persistent memory layer that stores sensor state, readings, monitor references, reputation, estimates, resolutions, audit history, vector fingerprints, and backtest runs. The agent retrieves a sensor’s stored reliability memory before deciding how much to trust a new reading, and that memory materially changes the result: sensor 54917 was downweighted to 0.1986 before the adjusted estimate and explanation were written back as a resolution and audit trail. CockroachDB Cloud Managed MCP lets Codex interrogate that live memory and answer why the sensor was downweighted. CockroachDB Distributed Vector Indexing stores and queries `VECTOR(8)` behavioral fingerprints. AWS Lambda and Amazon EventBridge ingest readings on a schedule, while Amazon S3 preserves the immutable raw evidence snapshots that support the normalized CockroachDB records.

### Video URL

TODO: Add the final public YouTube or Vimeo URL after recording the under-three-minute demo.

### Final form check

TODO: Compare this draft with the live Devpost form immediately before submission and copy each answer into the matching official field.
