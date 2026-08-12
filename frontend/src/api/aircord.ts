export type DemoSummary = {
  status: "ok" | "empty";
  generated_at?: string;
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
      reason_codes?: string[];
    }>;
  } | null;
  weight_formula: {
    status: "ok" | "empty";
    description: string;
    reputation_score: number | null;
    decision: string | null;
    multiplier: number | null;
    sensor_weight: number | null;
    expression: string | null;
  };
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
    connected_through_codex?: boolean;
    query_path: string;
    docs_path?: string;
    questions: string[];
    message: string;
    answer_summary?: string;
  };
  reference_caveat: string;
  medical_directive_caveat: string;
};

const API_BASE = import.meta.env.VITE_API_BASE?.replace(/\/$/, "");

async function get<T>(base: string, path: string): Promise<T> {
  const response = await fetch(`${base}${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const api = {
  demoSummary: async () => {
    if (!API_BASE) return get<DemoSummary>("", "/demo-summary.json");
    try {
      return await get<DemoSummary>(API_BASE, "/api/demo-summary");
    } catch (liveError) {
      try {
        return await get<DemoSummary>("", "/demo-summary.json");
      } catch {
        throw liveError;
      }
    }
  },
};
