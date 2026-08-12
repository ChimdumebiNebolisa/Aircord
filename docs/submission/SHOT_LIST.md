# Aircord Demo Shot List

Recording target: 2:30. Hard limit: 2:59. Record at 1920x1080 or 1440x900, enlarge the browser to keep values readable, and close notifications before capture.

| Time | Shot | Required visible proof | Narration cue |
| --- | --- | --- | --- |
| 0:00-0:20 | Public demo homepage at `https://aircord-demo.vercel.app/` | Aircord brand, human problem hook, CockroachDB-backed snapshot status and timestamp | Community sensors are dense but unreliable; Aircord adds memory. |
| 0:20-0:50 | Decision packet conflict card | Sensor `54917`, PM2.5 `0`, channels `0 / 1.9`, AirNow monitor `060371302`, Compton, AQI `64` | Introduce the concrete conflict and disclose that PM2.5 and AQI are different measures. |
| 0:50-1:25 | Decision packet memory and decision cards | Stored reputation `0.3973`, formula `0.3973 × 0.50 = 0.1986`, decision `downweighted`, adjusted estimate `51.3`, confidence, reason codes | Explain that retrieved memory changes the sensor's influence. |
| 1:25-1:40 | Audit trail card | Latest ingestion, reputation update, resolution creation, persisted IDs/timestamps | Show that the decision was written back as inspectable memory. |
| 1:40-1:55 | README judge section or `ARCHITECTURE.md` | CockroachDB tables and retrieve-act-write loop | Name the operational memory stored in CockroachDB. |
| 1:55-2:05 | Vector similarity card | `VECTOR(8)`, nearest labeled sensor/fixture, cosine distance, diagnostic caveat | Explain behavioral similarity without presenting it as accuracy. |
| 2:05-2:15 | MCP card or `docs/MCP_DEMO.md` | Judge question and answer: channel divergence plus monitor disagreement | Show that Codex can interrogate live CockroachDB memory. |
| 2:15-2:25 | Architecture diagram | Lambda, EventBridge, S3, CockroachDB, snapshot, Vercel | Explain the AWS ingestion/evidence path and public snapshot. |
| 2:25-2:40 | Caveat rail and final end card | Reference-not-truth, small backtest, unit mismatch, not medical advice | Deliver the honest close, then hold the end card. |

## Optional terminal readback

If the page scroll is faster than planned, substitute a five-second terminal shot after the audit trail:

```powershell
python backend/scripts/demo_status.py
```

Show only the command and public-safe result. Never expose environment variables, connection strings, credentials, certificate paths, or shell history.

## Pre-recording checks

- Regenerate `frontend/public/demo-summary.json` from CockroachDB.
- Refresh the existing Vercel production deployment.
- Open both the page and `/demo-summary.json` in clean browser tabs.
- Confirm the page shows the latest timestamp and does not show the snapshot failure state.
- Rehearse the script once and keep the final cut under three minutes.
