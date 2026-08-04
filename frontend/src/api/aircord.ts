export type Estimate = {
  estimated_aqi: number;
  confidence: number;
  claim_status: "pending_backtest" | "measured" | "insufficient_data";
  updated_at: string;
};

export type CellSummary = {
  cell_id: string;
  centroid: { latitude: number; longitude: number };
  latest_estimate: Estimate | null;
};

export type Cluster = {
  cluster_id: string;
  name: string;
  gate_a_status: "candidate" | "passed" | "failed";
  gate_a_notes: string;
  mode?: string;
};

export type CellDetail = {
  cell_id: string;
  estimate: Estimate | null;
  resolution: {
    rationale_text: string;
    confidence_factors: Record<string, number | boolean>;
    sensors: Array<{
      sensor_id: string;
      weight: number;
      decision: "trusted" | "downweighted" | "ignored";
      reason_codes: string[];
      reputation_score_at_commit: number;
    }>;
  } | null;
  reference_caveat: string;
  medical_directive_caveat: string;
};

export type Showcase = {
  sensor_id: string;
  cell_id: string;
  raw_or_static_estimate: number;
  aircord_estimate: number;
  reputation_reason: string;
};

export type Backtest = {
  backtest_run_id: string;
  status: "pending" | "passed" | "failed" | "insufficient_data";
  claim_status: "pending" | "measured" | "no_claim";
  failure_reason: string | null;
  summaries: Array<{
    segment: "all" | "healthy" | "degraded";
    method: "raw_purpleair" | "static_correction" | "aircord";
    observation_count: number;
    mean_absolute_error: number;
    median_absolute_error: number;
  }>;
};

export type DemoSummary = {
  status: "ok" | "empty";
  message: string;
  sensor_id: string;
  cell_id: string;
  sensor: {
    sensor_id: string;
    name: string;
    latitude: number;
    longitude: number;
    reputation_score: number | null;
    last_seen: string | null;
  } | null;
  latest_sensor_reading: {
    reading_id: string;
    sensor_id: string;
    pm25_cf1: number | null;
    pm25_atm: number | null;
    channel_a: number | null;
    channel_b: number | null;
    observed_at: string;
    raw_s3_key: string | null;
  } | null;
  airnow_reference: {
    monitor: {
      monitor_id: string;
      name: string;
      latest_aqi: number | null;
      observed_at: string | null;
    } | null;
    distance_km: number | null;
  };
  sensor_reputation: Record<string, unknown> | null;
  latest_cell_estimate: {
    estimate_aqi: number;
    confidence: number;
    updated_at: string;
  } | null;
  latest_resolution: {
    resolution_id: string;
    estimate_aqi: number;
    confidence: number;
    reasoning_text: string;
    sensors_considered: Array<{
      sensor_id: string;
      decision: string;
      weight: number;
      reputation_score: number;
    }>;
  } | null;
  audit_rows: Array<{
    audit_id?: string;
    created_at: string;
    actor: string;
    action: string;
    entity_type: string;
    entity_id: string;
    details?: Record<string, unknown>;
  }>;
  similarity: {
    status: "ok" | "empty";
    message: string;
    fingerprint_dimensions: number;
    fingerprint_features: Record<string, number>;
    nearest: Array<{
      sensor_id: string;
      cosine_distance: number;
      source: string;
      label?: string;
    }>;
  };
  latest_backtest: {
    backtest_run_id: string;
    status: string;
    claim_status: string;
    summaries: Array<{
      segment: string;
      method: string;
      observation_count: number;
      mean_absolute_error: number | null;
    }>;
  } | null;
  caveats: string[];
  mcp: {
    status: string;
    query_path: string;
    questions: string[];
    message: string;
  };
  reference_caveat: string;
  medical_directive_caveat: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const DEMO_PATH = import.meta.env.VITE_API_BASE ? "/api/demo-summary" : "/demo-summary.json";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const api = {
  cluster: () => get<Cluster>("/clusters/active"),
  cells: () => get<CellSummary[]>("/clusters/active/cells"),
  cell: (id: string) => get<CellDetail>(`/cells/${id}`),
  showcase: () => get<Showcase>("/showcases/degraded-sensor"),
  backtest: () => get<Backtest>("/backtests/latest"),
  demoSummary: () => get<DemoSummary>(DEMO_PATH),
};
