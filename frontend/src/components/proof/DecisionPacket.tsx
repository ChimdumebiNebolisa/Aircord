import type { DemoSummary } from "../../api/aircord";
import {
  confidenceLabel,
  formatNumber,
  formatPercent,
  present,
} from "../../lib/format";
import { Badge } from "../ui/Badge";
import { Metric } from "../ui/Metric";
import { SectionHeader } from "../ui/SectionHeader";
import { StatusDot } from "../ui/StatusDot";
import { MemoryDecision } from "./MemoryDecision";

export function DecisionPacket({ demo }: { demo: DemoSummary }) {
  const reading = demo.latest_sensor_reading;
  const monitor = demo.airnow_reference.monitor;
  const estimate = demo.latest_cell_estimate;
  const resolution = demo.latest_resolution;
  const decision = resolution?.sensors_considered[0];
  const sensorValue = reading?.pm25_cf1;
  const referenceValue = monitor?.latest_aqi;
  const comparisonMax = Math.max(sensorValue ?? 0, referenceValue ?? 0, 1);
  const sensorBar = sensorValue === null || sensorValue === undefined ? null : (sensorValue / comparisonMax) * 100;
  const referenceBar = referenceValue === null || referenceValue === undefined ? null : (referenceValue / comparisonMax) * 100;
  const referenceWeight = decision?.weight === null || decision?.weight === undefined ? null : 1 - decision.weight;
  const hasVector = demo.similarity.status === "ok" && demo.similarity.nearest.length > 0;
  const hasBacktest = Boolean(demo.latest_backtest);
  const hasMcp = demo.mcp.connected_through_codex === true;

  return (
    <section id="decision" className="scroll-mt-6 border-t border-line pt-7">
      <SectionHeader
        eyebrow="Decision packet"
        title="One conflict. One remembered response."
        description="The conclusion and its persisted proof fit in one compact inspection surface."
      />

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <article className="flex min-h-full flex-col rounded-card border border-danger/25 bg-panel p-5 shadow-card">
          <div className="flex items-start justify-between gap-3">
            <span className="font-mono text-[0.625rem] font-medium tracking-[0.13em] text-danger uppercase">
              01 / Conflict
            </span>
            <Badge tone="danger">Signal mismatch</Badge>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-4">
            <Metric
              compact
              label="Community sensor"
              value={formatNumber(sensorValue, 0)}
              unit="PM2.5"
              supporting={`PurpleAir • Channels ${formatNumber(reading?.channel_a, 1)} / ${formatNumber(reading?.channel_b, 1)}`}
            />
            <Metric
              compact
              label="Regulatory reference"
              value={formatNumber(referenceValue, 0)}
              unit="AQI"
              tone="danger"
              supporting={`AirNow • ${present(monitor?.name)} / ${present(monitor?.monitor_id)}`}
            />
          </div>
          <div className="mt-6 space-y-3" aria-label="Side-by-side signal comparison">
            <div>
              <div className="mb-1.5 flex justify-between font-mono text-[0.625rem] text-muted">
                <span>PURPLEAIR</span><span>{formatNumber(sensorValue, 1)}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-canvas">
                {sensorBar !== null ? <div className="h-full min-w-px bg-muted" style={{ width: `${sensorBar}%` }} /> : null}
              </div>
            </div>
            <div>
              <div className="mb-1.5 flex justify-between font-mono text-[0.625rem] text-muted">
                <span>AIRNOW</span><span>{formatNumber(referenceValue, 1)}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-canvas">
                {referenceBar !== null ? <div className="h-full bg-danger" style={{ width: `${referenceBar}%` }} /> : null}
              </div>
            </div>
          </div>
          <p className="mt-auto pt-5 text-[0.6875rem] leading-5 text-muted">
            Shown side by side as conflict evidence; PM2.5 and AQI are different measures.
          </p>
        </article>

        <MemoryDecision formula={demo.weight_formula} decision={decision} />

        <article className="flex min-h-full flex-col rounded-card border border-mint/30 bg-panel p-5 shadow-card">
          <div className="flex items-start justify-between gap-3">
            <span className="font-mono text-[0.625rem] font-medium tracking-[0.13em] text-mint uppercase">
              03 / Decision
            </span>
            <Badge tone="amber">{present(decision?.decision, "Not stored")}</Badge>
          </div>
          <div className="mt-6">
            <Metric
              label="Adjusted estimate"
              value={formatNumber(estimate?.estimate_aqi, 1)}
              unit="AQI proxy"
              tone="mint"
              supporting="Blended toward the evaluation reference"
            />
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 border-y border-line py-4">
            <div>
              <span className="font-mono text-[0.625rem] tracking-[0.08em] text-muted uppercase">Confidence</span>
              <strong className="mt-1 block font-display text-xl font-semibold text-ink">
                {formatPercent(estimate?.confidence)}
              </strong>
              <small className="text-xs text-muted">{confidenceLabel(estimate?.confidence)}</small>
            </div>
            <div>
              <span className="font-mono text-[0.625rem] tracking-[0.08em] text-muted uppercase">Reference share</span>
              <strong className="mt-1 block font-display text-xl font-semibold text-ink">
                {formatPercent(referenceWeight)}
              </strong>
              <small className="text-xs text-muted">Transparent blend</small>
            </div>
          </div>
          <p className="mt-auto pt-5 text-[0.6875rem] leading-5 text-muted">
            The stored estimate is a transparent cross-source proxy, not a validated AQI claim.
          </p>
        </article>

        <article className="flex min-h-full flex-col rounded-card border border-line-strong bg-panel-elevated p-5 shadow-card">
          <div className="flex items-start justify-between gap-3">
            <span className="font-mono text-[0.625rem] font-medium tracking-[0.13em] text-info uppercase">
              04 / Proof
            </span>
            <Badge tone="mint">Persisted</Badge>
          </div>
          <div className="mt-5 divide-y divide-line border-y border-line">
            <ProofStatus
              label="Audit trail"
              value={`${demo.audit_rows.length} rows`}
              ready={demo.audit_rows.length > 0}
            />
            <ProofStatus
              label="Vector memory"
              value={`VECTOR(${demo.similarity.fingerprint_dimensions})`}
              ready={hasVector}
            />
            <ProofStatus
              label="Paired backtest"
              value={present(demo.latest_backtest?.claim_status)}
              ready={hasBacktest}
            />
            <ProofStatus
              label="Managed MCP"
              value={hasMcp ? "Codex connected" : present(demo.mcp.status)}
              ready={hasMcp}
            />
          </div>
          <p className="mt-auto pt-5 text-[0.6875rem] leading-5 text-muted">
            Resolution {present(resolution?.resolution_id)} is linked to inspectable database evidence.
          </p>
        </article>
      </div>
    </section>
  );
}

function ProofStatus({ label, value, ready }: { label: string; value: string; ready: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3.5">
      <span className="flex items-center gap-2 text-xs text-ink-secondary">
        <StatusDot tone={ready ? "mint" : "amber"} /> {label}
      </span>
      <span className="text-right font-mono text-[0.625rem] text-muted uppercase">{value}</span>
    </div>
  );
}
