import type { DemoSummary } from "../../api/aircord";
import { formatNumber, formatTimestamp, present } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { DefinitionRow } from "../ui/DefinitionRow";
import { Metric } from "../ui/Metric";

export function ReferenceEvidence({
  reference,
  caveat,
}: {
  reference: DemoSummary["airnow_reference"];
  caveat: string;
}) {
  const monitor = reference.monitor;

  return (
    <article className="rounded-card border border-line bg-panel p-5 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.12em] text-muted uppercase">
            AirNow monitor / {present(monitor?.monitor_id)}
          </p>
          <h3 className="mt-2 font-display text-2xl font-semibold tracking-[-0.04em] text-ink">
            {present(monitor?.name)}
          </h3>
        </div>
        <Badge tone="info">Evaluation reference</Badge>
      </div>

      <div className="mt-5 border-y border-line py-4">
        <Metric
          compact
          label="Latest monitor reading"
          value={formatNumber(monitor?.latest_aqi, 0)}
          unit="AQI"
          tone="mint"
        />
      </div>

      <dl className="mt-1">
        <DefinitionRow
          label="Distance"
          value={reference.distance_km === null ? "Not stored" : `${formatNumber(reference.distance_km, 2)} km`}
        />
        <DefinitionRow label="Observed" value={formatTimestamp(monitor?.observed_at)} />
      </dl>

      <p className="mt-4 border-l-2 border-amber bg-amber-dim/50 px-3 py-2.5 text-[0.6875rem] leading-5 text-muted">
        {caveat}
      </p>
    </article>
  );
}
