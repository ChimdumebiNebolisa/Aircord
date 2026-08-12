# Aircord Architecture

Aircord separates evidence acquisition, persistent decision memory, and the public judge surface. Raw observations are archived before normalized data is used by the reputation loop.

```mermaid
flowchart LR
    PA["PurpleAir API"] --> LAMBDA["AWS Lambda<br/>15-minute ingestion"]
    LAMBDA --> S3P["Amazon S3<br/>raw PurpleAir snapshot"]
    S3P --> READINGS["CockroachDB<br/>sensor_readings"]

    AN["AirNow API"] --> INGEST["AirNow ingestion script"]
    INGEST --> S3A["Amazon S3<br/>raw AirNow snapshot"]
    S3A --> MONITORS["CockroachDB<br/>monitors"]

    EVENTBRIDGE["Amazon EventBridge<br/>15-minute schedule"] --> LAMBDA

    READINGS --> LOOP["Aircord reputation loop<br/>retrieve → decide → write"]
    MONITORS --> LOOP
    SENSORS["CockroachDB<br/>sensors / reputation"] -->|retrieve memory| LOOP
    LOOP -->|update memory| SENSORS
    LOOP --> ESTIMATES["CockroachDB<br/>cell_estimates"]
    LOOP --> RESOLUTIONS["CockroachDB<br/>resolutions"]
    LOOP --> AUDIT["CockroachDB<br/>audit_log"]
    LOOP --> EMBEDDINGS["CockroachDB<br/>sensor_embeddings VECTOR(8)"]

    EMBEDDINGS --> VINDEX["CockroachDB<br/>vector index"]
    VINDEX --> SIMILARITY["Behavioral similarity query"]

    MEMORY["CockroachDB operational memory"] --> MCP["CockroachDB Cloud<br/>Managed MCP Server"]
    MCP --> CODEX["Codex asks:<br/>Why was sensor 54917 downweighted?"]

    MEMORY --> STATUS["backend/scripts/demo_status.py"]
    STATUS --> SNAPSHOT["frontend/public/demo-summary.json"]
    SNAPSHOT --> VERCEL["Vercel public demo"]

    READINGS -. stored in .-> MEMORY
    MONITORS -. stored in .-> MEMORY
    SENSORS -. stored in .-> MEMORY
    ESTIMATES -. stored in .-> MEMORY
    RESOLUTIONS -. stored in .-> MEMORY
    AUDIT -. stored in .-> MEMORY
    EMBEDDINGS -. stored in .-> MEMORY
```

## Responsibility boundaries

- AWS Lambda and EventBridge acquire PurpleAir observations on a schedule.
- Amazon S3 preserves the raw PurpleAir and AirNow evidence snapshots.
- CockroachDB is the persistent operational memory used before and after each trust decision.
- Distributed Vector Indexing supports an explainable behavioral-similarity diagnostic.
- Managed MCP lets Codex ask read-only questions about the live memory.
- `demo_status.py` exports a timestamped public-safe snapshot for the static Vercel demo; no database credentials are shipped to the browser.
