import type { DemoSummary } from "../../api/aircord";
import { formatNumber, formatTimestamp, present } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { DefinitionRow } from "../ui/DefinitionRow";

export function SensorEvidence({
  sensorId,
  sensor,
  reading,
}: {
  sensorId: string;
  sensor: DemoSummary["sensor"];
  reading: DemoSummary["latest_sensor_reading"];
}) {
  return (
    <article className="rounded-card border border-line bg-panel p-5 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.12em] text-muted uppercase">
            Community sensor / {sensorId}
          </p>
          <h3 className="mt-2 font-display text-2xl font-semibold tracking-[-0.04em] text-ink">
            {present(sensor?.name)}
          </h3>
        </div>
        <Badge tone="amber">Downweighted</Badge>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3 border-y border-line py-4">
        <EvidenceMetric label="PM2.5 CF1" value={formatNumber(reading?.pm25_cf1, 1)} />
        <EvidenceMetric label="Channel A" value={formatNumber(reading?.channel_a, 1)} />
        <EvidenceMetric label="Channel B" value={formatNumber(reading?.channel_b, 1)} tone="amber" />
      </div>

      <dl className="mt-1">
        <DefinitionRow
          label="Location"
          value={`${formatNumber(sensor?.latitude, 6)}, ${formatNumber(sensor?.longitude, 6)}`}
          mono
        />
        <DefinitionRow label="Observed" value={formatTimestamp(reading?.observed_at)} />
        <DefinitionRow label="Latest raw S3 key" value={present(reading?.raw_s3_key)} mono />
      </dl>
    </article>
  );
}

function EvidenceMetric({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "amber";
}) {
  return (
    <div className="min-w-0">
      <span className="block font-mono text-[0.5625rem] tracking-[0.08em] text-muted uppercase">
        {label}
      </span>
      <strong
        className={`mt-1 block font-display text-2xl font-semibold tracking-[-0.04em] ${tone === "amber" ? "text-amber" : "text-ink"}`}
      >
        {value}
      </strong>
    </div>
  );
}
