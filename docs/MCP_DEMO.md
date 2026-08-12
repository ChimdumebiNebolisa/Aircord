# CockroachDB Cloud Managed MCP Demo

This is the live, read-only Codex interrogation of Aircord's CockroachDB
memory layer.

- MCP client: Codex
- MCP server: CockroachDB Cloud Managed MCP
- Endpoint: `https://cockroachlabs.cloud/mcp`
- Cluster ID: `2766ef53-ca8e-4e43-a5c2-5fbb4c49f979`
- Database: `aircord`

## Setup

1. Add the following block to `C:\Users\Chimdumebi\.codex\config.toml`:

   ```toml
   [mcp_servers.cockroachdb-cloud]
   url = "https://cockroachlabs.cloud/mcp"
   http_headers = { "mcp-cluster-id" = "2766ef53-ca8e-4e43-a5c2-5fbb4c49f979" }
   ```

2. Reload Codex, then run:

   ```powershell
   codex mcp login cockroachdb-cloud
   ```

3. Approve the browser OAuth request with read-only access when prompted.
4. Run `/mcp` in Codex and confirm `cockroachdb-cloud` is connected.
5. Ask the judge questions below, or use the read-only query pack in
   [`docs/cockroachdb_mcp_queries.sql`](cockroachdb_mcp_queries.sql). The live
   inspection covered `sensors`, `sensor_readings`, `monitors`, `resolutions`,
   `audit_log`, `backtest_runs`, and `sensor_embeddings`.

## Exact judge questions

- Why was sensor 54917 downweighted?
- What evidence did Aircord use?
- What is the latest reputation score?
- Show the latest resolution and audit trail.
- Show the latest backtest result and caveats.

## Actual live answer: why sensor 54917 was downweighted

Sensor `54917` was downweighted for the two explicit reasons recorded by the
live database: `channel_divergence` and `monitor_disagreement`.

The latest live evidence returned through CockroachDB Cloud Managed MCP was:

| Evidence | Live value |
| --- | --- |
| Latest reading | `94dda429-1c4c-4d89-bb6a-d6200064ba0a`, observed `2026-08-04T22:34:37Z` |
| Reading channels | `channel_a=0`, `channel_b=1.9` |
| Reading PM2.5 values | `pm25_cf1=0`, `pm25_atm=0` |
| Reference monitor | `060371302`, observed `2026-08-04T21:00:00Z`, `latest_aqi=64` |
| Latest resolution | `40a972b5-82d3-421e-b9b3-59874ec4bc6d`, committed `2026-08-04T22:54:18.10157Z` |
| Latest decision | `downweighted`; reputation `0.3973`, sensor weight `0.1986`, reference weight `0.8014` |
| Matching audit row | `d9ada343-b718-4e32-94cc-556fa2e4f4be` |
| Audit evidence | `absolute_difference=64.0`, `agreement_score=0.0`, `channel_agreement_score=0.0`, `drift_score=0.0` |

The decision repeated across four resolutions, with reputation/weight pairs of
`0.3957/0.1978`, `0.4195/0.2097`, `0.3995/0.1998`, and `0.3973/0.1986`.
The latest `sensor_embeddings` row, updated
`2026-08-04T22:54:27.875364Z`, is consistent with the decision: normalized
`channel_a_b_difference=1.0`, `absolute_difference_from_monitor=1.0`,
`recent_pm25=0.0`, and reputation `0.3973`. The related measured backtest
`backtest-f1e5c84e0651` passed, but it is validation context rather than the
recorded cause of this individual downweight.

In plain language, the two sensor channels disagreed with each other, and the
sensor's zero PM2.5 proxy disagreed with the monitor's AQI `64`. The reason
codes are live database facts; interpreting the raw PM2.5 value as the source
of the recorded `64` difference is an inference from the stored values. Aircord
exposes the simple application formula in code and readback output:
`sensor_weight = reputation_score × multiplier`. Trusted sensors use `1.00`,
ordinary downweighted sensors use `0.50`, drifted sensors use `0.25`, and
ignored sensors use `0.00`; therefore `0.3973 × 0.50 = 0.19865`, rounded to
`0.1986`.

## Credential caveat

Secrets and OAuth tokens are not committed. The cluster ID is documented here,
but the OAuth token remains managed by local Codex authentication and the
user-level config is outside this repository. Do not copy credentials into
`.env`, frontend variables, SQL files, or committed documentation.
