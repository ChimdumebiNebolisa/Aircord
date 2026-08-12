# Aircord Demo Video Script

Target spoken length: 2:30. Hard limit: 2:59. The final ten seconds of the timeline are reserved for the closing line and end card; rehearse once with a timer before recording.

## 0:00-0:20 - Problem

**On screen:** Aircord public demo, starting at the hero and decision packet.

**Narration:**

Cheap community air sensors are dense and fast, but they can drift, disagree across channels, or fail while still returning a fresh timestamp. Regulatory monitors are trusted references, but they are sparse. Aircord adds a persistent memory layer between them so the next decision can use what the system learned before.

## 0:20-0:50 - Concrete case

**On screen:** Conflict card with sensor and monitor evidence.

**Narration:**

Here is the real case in the public demo. PurpleAir sensor 54917, CCA 67th and Myrtle, reported PM2.5 of zero, with channels at zero and 1.9. The nearby AirNow regulatory monitor 060371302 in Compton reported AQI 64. PM2.5 and AQI are different measures, but the disagreement and split channels are useful trust evidence.

## 0:50-1:25 - Memory action

**On screen:** Memory and decision cards; point to reputation, weight, reasons, and estimate.

**Narration:**

Aircord checked the sensor's stored reputation of 0.3973. The transparent rule multiplied that score by the downweighted multiplier of 0.50, producing a sensor weight of 0.1986. It recorded the decision as downweighted because of channel divergence and monitor disagreement, then blended the estimate toward the reference to produce 51.3 with medium confidence.

The key point is that memory changes the answer. Aircord does not just store readings; it retrieves this sensor's reliability history and uses it to reduce the sensor's influence.

## 1:25-1:55 - CockroachDB memory layer

**On screen:** Audit trail, then the architecture diagram or README judge section.

**Narration:**

CockroachDB stores the operational memory: readings, monitor references, sensor reputation, resolutions, audit trail, backtest runs, and VECTOR(8) fingerprints. Aircord retrieves that memory before acting and writes the new estimate, resolution, reputation update, and audit evidence back for the next cycle. The audit rows make the ingestion and decision path inspectable.

## 1:55-2:20 - CockroachDB tools and AWS

**On screen:** Vector similarity card, MCP card, then architecture diagram highlighting AWS.

**Narration:**

Distributed Vector Indexing supports behavioral sensor similarity, and Managed MCP lets Codex ask the database why a sensor was downweighted. AWS Lambda and EventBridge run ingestion, while S3 stores raw sensor evidence. The public Vercel page reads a timestamped, CockroachDB-backed snapshot, so judges see persisted proof without exposing credentials.

## 2:20-2:40 - Honest close

**On screen:** Caveat rail and final Aircord end card. Finish speaking near 2:30 and hold the end card briefly.

**Narration:**

Aircord is not medical advice and does not claim absolute air-quality truth. It is a working proof that an agent can store, retrieve, and act on reliability memory in production infrastructure.
