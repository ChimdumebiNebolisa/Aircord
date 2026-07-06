# Aircord (Air Quality) — Concept Spec

*Domain switched from parking to air quality. Air quality strictly dominates parking on the axes that matter: strong stakes, free-to-cheap live data on **both** sides, a **native documented** contradiction (no fabricated crowd reports), a **real per-sensor reputation signal**, and — critically — a **defensible reference (regulatory monitors) that makes a real accuracy number possible**, which parking never had.*

> **Two honest caveats, stated up front (do not bury them):**
> 1. **PurpleAir is points-billed, not free** — but the cost is small (~$0.50/sensor/month at 15-min polling) and you've chosen to pay. Paying is a design win here: pull *full fields* (both channels, all PM sizes, humidity, RSSI, uptime) at higher cadence with history — richer per-sensor data that strengthens both the reputation loop and the behavioral fingerprints (§7). Still scope to one metro cluster and cache; don't poll all of PurpleAir.
> 2. **The incumbent is capable.** AirNow's Fire & Smoke Map + Google Maps already merge these two sources via a *static* EPA correction equation + basic QC. Your edge is *learned, per-sensor, auditable memory* — not "we merge sources," which is done. Position against the static incumbent explicitly.

> **This is the `/speckit.specify` input.** Feed sections 1–8. Keep section 9 (hand-designed core) and section 10 (day-one gates) as your own reference so a coding agent doesn't dilute them.

---

## 1. One sentence (locked claim)

**Aircord is an agentic memory for air quality that learns which crowd sensors to trust — it reconciles a sparse network of accurate regulatory monitors against a dense network of cheap, drifting community sensors, and produces a trust-weighted, explainable estimate that catches degrading sensors a fixed correction still believes.**

Plain-person value: *tells you how safe the air really is — and how much to trust the number — instead of parroting a miscalibrated backyard sensor.*

---

## 2. The problem (why anyone cares)

During wildfire smoke, people make real health decisions — should my kid play outside, should I run, should I keep the windows shut — from apps whose numbers disagree. The disagreement is real and famous: on one August day, AirNow reported AQI 107 for a Berkeley ZIP while nearby PurpleAir sensors read 130s–150s. Regulatory monitors are accurate but sparse and lag ~1–3 hours; community PurpleAir sensors are dense and near-real-time but drift, get mislabeled indoors, and degrade (dust, insects, fan failure). The EPA cared enough to build a nationwide correction equation because raw sensors overestimate most of the time. That gap — dense-but-unreliable vs. sparse-but-trusted — is the entire reason Aircord exists.

---

## 3. What it is

For each location/grid cell, Aircord maintains a **trust-weighted air-quality estimate** with a confidence, updated continuously by two real source types that disagree:

1. **Monitor Agent** — polls AirNow regulatory monitors. Accurate reference, but sparse and hourly.
2. **Sensor Agent** — polls nearby PurpleAir community sensors (~2-min cadence). Dense and fresh, but individually unreliable.

The **Reconciler** weighs each PurpleAir sensor by its **learned reputation** — how well it has tracked the nearest regulatory monitor over time, whether its A/B channels agree, whether it looks indoor/mislabeled — then produces a corrected, trust-weighted estimate plus a plain-English **resolution record**, and updates each sensor's reputation from the latest evidence. Every estimate is inspectable: click a cell → see which sensors were trusted, which were downweighted, and why.

**What Aircord claims:** better-calibrated, *auditable* trust that adapts per sensor over time, and detection of degraded sensors a static correction misses. **What it does NOT claim:** to beat EPA's correction on every sensor, or to know absolute ground truth (regulatory monitors are the accepted *reference*, not perfect truth).

---

## 4. The hero: a real accuracy number + the memory beat

**Hero #1 — the number (honest, measurable):** At locations with both a PurpleAir sensor and a nearby regulatory monitor, measure error against the monitor for three methods: raw crowd average, the static EPA correction, and Aircord's learned trust-weighting. The claim is targeted and true:

> "On real paired LA data, Aircord's trust-weighting tracks the regulatory monitor as well as the static EPA correction on healthy sensors — and materially better on sensors that have drifted or gone bad, because it remembers their track record instead of applying one fixed formula."

This is the strong-but-defensible claim parking could never support, because here you have a real reference.

**Hero #2 — the memory beat (the centerpiece):** Show one PurpleAir sensor that has drifted over weeks. The static approach still trusts it; Aircord has *remembered* its growing disagreement with the reference monitor and downweights it — visibly changing the map's estimate for that neighborhood, with the reasoning shown. Same input, different outcome, because of memory. That is the "agentic memory" proof, and it needs no fabrication.

---

## 5. Why this beats the incumbent (state it precisely)

The incumbent (AirNow F&S / Google Maps) applies: (a) one static US-wide correction equation, and (b) per-reading QC (drop a sensor whose A/B channels disagree that hour). Real, but memoryless.

Aircord adds what a fixed formula can't: **persistent per-sensor reputation that accumulates over time**, drift/degradation detection, conflict resolution with an **auditable rationale**, and a single consistent store so the trust model and the estimate never disagree. That's the agentic-memory gap, and it's the right gap for this contest. Do not claim to have invented source-merging.

---

## 6. Why CockroachDB (honest, consolidation + real concurrency)

Two reasons, both stated:

1. **One consistent substrate.** Sensor readings, per-sensor reputation, resolution history, the regulatory reference, and audit all live in one transactional store, read/written atomically — so the trust model can never disagree with the estimate it produced. A split stack (Postgres + separate store) reintroduces exactly that gap.
2. **Genuine concurrency, not staged.** Thousands of PurpleAir sensors reporting every ~2 minutes plus hourly monitor updates produce real concurrent writes on the same geographic cells during reconciliation. Serializable isolation earns its place here for real — no contrived same-millisecond collision needed. (This is a *stronger* concurrency story than parking.)

Say plainly: serializable alone isn't unique (Postgres has it); the win is consolidation + this being the substrate you'd actually run distributed. No node-drop theater.

---

## 7. Architecture

- **Frontend:** a map (grid cells colored by estimate) + a cell-detail panel showing the estimate, confidence, contributing sensors, their reputations, and the resolution reasoning. Do not over-invest.
- **Backend:** API + Monitor Agent + Sensor Agent + Reconciler.
- **Memory:** CockroachDB (§9).
- **AWS (deployed on AWS, several services used meaningfully):**
  - **Amazon Bedrock (Claude)** — the reconciler's reasoning/explanation (given monitor + weighted sensors + reputations → estimate + confidence + human-readable rationale). **Runs OUTSIDE the DB transaction.**
  - **AWS Lambda** — the two polling agents (PurpleAir poller, AirNow poller). Lambda *is* the concurrent writer.
  - **Amazon S3** — immutable raw reading snapshots feeding the audit trail / backtest.
- **CockroachDB tools (≥2 required — be honest about fit):**
  - **Managed MCP Server** — expose the memory as tools so a judge (via Claude) can interrogate it live: "why is sensor 175413 distrusted?" Strong, non-checkbox use.
  - **Distributed Vector Indexing** — used *legitimately*, as the mechanism that **scales the reputation loop**. Direct reputation only works where a regulatory monitor is nearby, but monitors are sparse, so most sensors have no ground truth. Fix: embed each sensor's **behavioral fingerprint** (recent time-series features — diurnal shape, variance, A/B channel-divergence pattern, responsiveness, bias vs. neighbors) and use nearest-neighbor search to (a) **propagate trust by analogy** — infer a far-from-monitor sensor's reliability from behaviorally-similar sensors that *are* anchored to a monitor; (b) **detect drift/faults** when a sensor's current fingerprint diverges from its own recent history; (c) embed sensor **names/labels** ("Living Room", "Bedroom") to flag likely-indoor/mislabeled units. This is real similarity search over numeric embeddings — the job vector indexing exists for — and it serves the reputation centerpiece rather than competing with it. *(Retracting an earlier note: vector indexing is weak only if you naively embed raw readings; behavioral fingerprinting makes it load-bearing.)* Keep it feasible with **hand-crafted feature vectors** (no trained model needed); phase it if time is tight — drift-via-self-similarity first, cross-sensor propagation second. *(ccloud CLI can still appear in provisioning scripts as documented ops, but Vector Indexing is now your genuine second tool.)*

**Reconciliation flow (LLM outside the transaction):**
```
1. Bedrock computes {estimate, confidence, rationale} from monitor + reputation-weighted sensors   ← NO db txn open
2. BEGIN; re-read cell version; if unchanged → write estimate + resolution + per-sensor reputation updates + audit; COMMIT;   ← short, serializable
3. if version changed underneath → retry from step 1
```

---

## 8. Scope guards (what this must NOT become)

- Not a pretty AQI map (that's the incumbent). The product is *learned, auditable trust over unreliable sensors.*
- Not national. One metro cluster (e.g., greater LA / Bay Area) where paired sensors + monitors are dense.
- No accounts, no forecasting, no health-advice engine beyond showing the estimate + confidence, no mobile app.
- **Rule:** before building anything, ask *does this serve the trust/reputation loop or the accuracy number?* If not, defer it.

---

## 9. Hand-designed core (your reference — keep tight)

**Tables**
- `cells` — cell_id (grid or reporting area), estimate, confidence, updated_at, version
- `monitors` — monitor_id, coords, latest_aqi, ts (regulatory reference)
- `sensor_readings` — reading_id, sensor_id, cell_id, pm25_cf1, channel_a, channel_b, ts, raw_ref→S3
- `sensors` — sensor_id, coords, **reputation_score**, drift stats, channel-agreement stats, indoor_flag, agreement-with-nearest-monitor history
- `sensor_embeddings` — sensor_id, **behavioral_fingerprint (vector)**, updated_at — feeds similarity search: trust propagation + drift detection (§7)
- `resolutions` — cell_id, estimate, **reasoning_text**, sensors_considered + weights (json), confidence, committed_at
- `audit_log` — append-only: every write, which agent, when

**The reputation loop is the project.** For each PurpleAir sensor, continuously score: agreement with the nearest regulatory monitor over time, A/B channel divergence, plausibility (indoor/mislabeled), and stability. Weight sensors by reputation in the estimate; update reputation from each new comparison. It must *visibly change outcomes* — a drifted sensor gets downweighted and the neighborhood estimate shifts. If reputation doesn't change outcomes, it's decoration, not memory.

**Reputation by analogy (the coverage fix + your second CockroachDB tool).** Monitors are sparse, so most sensors have no nearby ground truth. Anchor reputation where a monitor *is* nearby (measured agreement), embed every sensor's behavioral fingerprint, and propagate trust to unanchored sensors via vector nearest-neighbor to anchored ones. Honest assumption to state and validate: behaviorally-similar sensors tend to have similar reliability — defensible and *partially validatable* (hold out anchored sensors, predict their reliability from their embedding neighbors, measure the error), not a guarantee.

**Accuracy metric (the hero number — define precisely, compute day-one):** at paired locations, error = |method_estimate − monitor| for {raw, static-EPA-correction, Aircord}. Report on healthy sensors (parity expected) and on degraded/drifted sensors (Aircord should win). Regulatory monitor is the reference; state that.

---

## 10. Day-one gates (BEFORE building anything)

**Gate A — live paired disagreement in one cluster.** Pull AirNow monitors + PurpleAir sensors for one metro area. Confirm: enough PurpleAir sensors near a regulatory monitor (these are your **labeled anchors** for trust propagation — you need a reasonable number); real live disagreement between them right now; and at least a few sensors that look degraded (persistent channel divergence or drift vs. the monitor). **Pass:** you have a cluster with paired data, visible disagreement, some bad sensors to showcase, and enough anchors to propagate from. **Fail:** pick another metro; if no metro has this, reconsider.

**Gate B — the number is computable.** Using PurpleAir history + AirNow, confirm you can reconstruct paired time series and compute the three-method error comparison, and that Aircord beats the static correction on at least some degraded sensors. **Pass:** headline the number. **Fail:** the accuracy hero is at risk — fall back to the memory beat (Hero #2) as the centerpiece; do not fake a number.

---

## 11. How this maps to the five judging criteria

- **Agentic memory design** — memory *is* the product: per-sensor reputation that accumulates, drives weighting, and changes estimates.
- **Technical implementation** — real serializable reconciliation under genuine concurrent sensor writes; consolidated store; MCP inspection.
- **Real-world impact** — real health decisions during smoke; real live data; the problem is documented by the EPA itself.
- **Production readiness** — audit trail, reputation, confidence, drift detection; honest "estimate, not a health directive" disclaimer.
- **Originality** — learned, auditable, memory-driven trust vs. a static correction — a real gap in a domain with a capable incumbent.

---

## 12. Data sources (verified)

- **AirNow API** (regulatory monitors, real-time): free, government, key by signup; ~500 calls/hr; obs hourly, available 10–30 min past the hour; lat/lon + zip endpoints return **peak AQI per reporting area** — use **File Products** for per-monitor/site granularity. (Do NOT use EPA AQS API for real-time — it lags ~6 months.)
- **PurpleAir API** (community sensors, near-real-time): key free (Google account) + starter credits, then points-billed (~$0.50/sensor/mo at 15-min polling) — you've opted to pay, which unlocks full fields + higher cadence + history (better fingerprints). Endpoint `api.purpleair.com/v1/sensors/{id}` with `X-API-Key`. Fields include pm2.5_cf_1, pm2.5_atm, last_seen, per-channel A/B data (health signal), RSSI, humidity, temp. History available for the backtest.
- The AirNow vs PurpleAir disagreement and EPA correction are your justification — cite them.

---

## 13. Honesty guardrails (claims to NEVER make)

- Never: "we beat EPA's correction everywhere." Claim the targeted truth: better on *degraded* sensors, via memory.
- Never: "Aircord knows the true air quality." Regulatory monitors are the reference, not absolute truth.
- Never: "PurpleAir is free." It's free-to-start, then points-billed.
- Never: "impossible without CockroachDB." Argue consolidation + real concurrency.
- Never present the accuracy number before computing it (Gate B).
- Never claim trust-by-analogy is exact: state the assumption (similar behavior → similar reliability) and show your hold-out validation of it.
- Always: "air-quality estimate, not a medical directive."

Stating these up front is what makes a sharp judge trust the rest.
