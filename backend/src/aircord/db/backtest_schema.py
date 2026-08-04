"""CockroachDB schema additions used by the persisted backtest runner."""


COCKROACH_BACKTEST_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS backtest_runs (
      backtest_run_id STRING PRIMARY KEY,
      cluster_id STRING NOT NULL,
      window_start TIMESTAMPTZ NULL,
      window_end TIMESTAMPTZ NULL,
      status STRING NOT NULL,
      claim_status STRING NOT NULL,
      failure_reason STRING NULL,
      created_at TIMESTAMPTZ NOT NULL,
      completed_at TIMESTAMPTZ NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS backtest_summaries (
      backtest_run_id STRING NOT NULL,
      segment STRING NOT NULL,
      method STRING NOT NULL,
      observation_count INT8 NOT NULL,
      mean_absolute_error FLOAT8 NULL,
      median_absolute_error FLOAT8 NULL,
      notes STRING NULL,
      PRIMARY KEY (backtest_run_id, segment, method)
    )
    """,
)
