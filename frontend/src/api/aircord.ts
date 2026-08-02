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

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

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
};
