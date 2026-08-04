-- Read-only judge queries for the CockroachDB Cloud Managed MCP Server.
-- Replace 54917 and 060371302 when interrogating another pair.

-- 1) Why was sensor 54917 downweighted?
SELECT
  s.sensor_id,
  s.name,
  s.reputation_score,
  s.channel_agreement_score,
  s.drift_score,
  r.reading_id,
  r.pm25_cf1,
  r.pm25_atm,
  r.channel_a,
  r.channel_b,
  r.observed_at,
  res.resolution_id,
  res.confidence,
  res.reasoning_text
FROM sensors AS s
LEFT JOIN LATERAL (
  SELECT *
  FROM sensor_readings
  WHERE sensor_id = s.sensor_id
  ORDER BY observed_at DESC
  LIMIT 1
) AS r ON true
LEFT JOIN LATERAL (
  SELECT *
  FROM resolutions
  WHERE cell_id = 'greater-la-sensor-54917'
  ORDER BY committed_at DESC
  LIMIT 1
) AS res ON true
WHERE s.sensor_id = '54917';

-- 2) What evidence did Aircord use?
SELECT
  created_at,
  actor,
  action,
  entity_type,
  entity_id,
  details
FROM audit_log
WHERE entity_id = '54917'
   OR entity_id IN (
     SELECT resolution_id::STRING
     FROM resolutions
     WHERE cell_id = 'greater-la-sensor-54917'
   )
ORDER BY created_at DESC
LIMIT 10;

-- 3) What is the latest reputation score?
SELECT
  sensor_id,
  name,
  reputation_score,
  channel_agreement_score,
  drift_score,
  last_seen,
  updated_at
FROM sensors
WHERE sensor_id = '54917';

-- 4) Show the latest resolution and its sensor decision.
SELECT
  res.resolution_id,
  res.cell_id,
  res.estimate_aqi,
  res.confidence,
  res.reasoning_text,
  res.committed_at,
  res.sensors_considered
FROM resolutions AS res
WHERE res.cell_id = 'greater-la-sensor-54917'
ORDER BY res.committed_at DESC
LIMIT 1;

-- 5a) Show the latest backtest run and caveats.
SELECT
  run.backtest_run_id,
  run.status,
  run.claim_status,
  run.window_start,
  run.window_end,
  run.failure_reason
FROM backtest_runs AS run
ORDER BY run.created_at DESC
LIMIT 1;

-- 5b) Show method summaries for that run.
SELECT
  summary.backtest_run_id,
  summary.segment,
  summary.method,
  summary.observation_count,
  summary.mean_absolute_error,
  summary.median_absolute_error,
  summary.notes
FROM backtest_summaries AS summary
WHERE summary.backtest_run_id = (
  SELECT backtest_run_id
  FROM backtest_runs
  ORDER BY created_at DESC
  LIMIT 1
)
ORDER BY summary.segment, summary.method;

-- 5c) Show the audit details for that run.
SELECT
  created_at,
  actor,
  action,
  details
FROM audit_log
WHERE entity_type = 'backtest'
  AND entity_id = (
    SELECT backtest_run_id
    FROM backtest_runs
    ORDER BY created_at DESC
    LIMIT 1
  )
ORDER BY created_at DESC;

-- 6) Optional: show nearest handcrafted behavioral fingerprints.
SELECT
  sensor_id,
  feature_json,
  updated_at,
  behavioral_fingerprint <=> (
    SELECT behavioral_fingerprint
    FROM sensor_embeddings
    WHERE sensor_id = '54917'
  ) AS cosine_distance
FROM sensor_embeddings
WHERE sensor_id <> '54917'
ORDER BY behavioral_fingerprint <=> (
  SELECT behavioral_fingerprint
  FROM sensor_embeddings
  WHERE sensor_id = '54917'
)
LIMIT 5;
