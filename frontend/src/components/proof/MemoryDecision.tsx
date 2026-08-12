import type { DemoSummary } from "../../api/aircord";
import { formatNumber, humanize, present } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { Metric } from "../ui/Metric";

type Decision = NonNullable<DemoSummary["latest_resolution"]>["sensors_considered"][number];

export function MemoryDecision({
  formula,
  decision,
}: {
  formula: DemoSummary["weight_formula"];
  decision?: Decision;
}) {
  const weight = formula.sensor_weight ?? decision?.weight ?? null;
  const weightPercent = weight === null ? null : Math.min(100, Math.max(0, weight * 100));
  const reasonCodes = decision?.reason_codes ?? [];

  return (
    <article className="flex min-h-full flex-col rounded-card border border-amber/30 bg-panel p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <span className="font-mono text-[0.625rem] font-medium tracking-[0.13em] text-amber uppercase">
          02 / Memory
        </span>
        <Badge tone="amber">{present(decision?.decision, "Decision not stored")}</Badge>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <Metric
          compact
          label="Reputation"
          value={formatNumber(formula.reputation_score, 4)}
          supporting="Persistent sensor memory"
        />
        <Metric
          compact
          label="Sensor weight"
          value={formatNumber(weight, 4)}
          tone="amber"
          supporting="Influence on this estimate"
        />
      </div>

      <div className="mt-5">
        <div className="mb-2 flex justify-between font-mono text-[0.625rem] text-muted uppercase">
          <span>0 / ignored</span>
          <span>1 / full trust</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full border border-line bg-canvas">
          {weightPercent !== null ? (
            <div className="h-full rounded-full bg-amber" style={{ width: `${weightPercent}%` }} />
          ) : null}
        </div>
      </div>

      <div className="mt-5 border-y border-line py-3">
        <p className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">Weight formula</p>
        <strong className="mt-2 block font-mono text-sm font-medium text-amber">
          {present(formula.expression, "Formula not stored")}
        </strong>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {reasonCodes.length ? (
          reasonCodes.map((reason) => (
            <Badge key={reason} tone="amber">
              {humanize(reason)}
            </Badge>
          ))
        ) : (
          <span className="text-xs text-muted">No reason codes stored.</span>
        )}
      </div>
    </article>
  );
}
