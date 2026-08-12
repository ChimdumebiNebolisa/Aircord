import type { DemoSummary } from "../../api/aircord";
import { formatNumber, formatTimestamp, present } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { StatusDot } from "../ui/StatusDot";

export function Hero({
  sensorId,
  sensor,
  reading,
  monitor,
  generatedAt,
}: {
  sensorId: string;
  sensor: DemoSummary["sensor"];
  reading: DemoSummary["latest_sensor_reading"];
  monitor: DemoSummary["airnow_reference"]["monitor"];
  generatedAt?: string;
}) {
  return (
    <section id="top" className="grid gap-7 py-10 lg:grid-cols-12 lg:items-end lg:py-14">
      <div className="lg:col-span-9">
        <p className="font-mono text-[0.625rem] font-medium tracking-[0.14em] text-mint uppercase">
          Aircord / Greater Los Angeles / Trust memory
        </p>
        <h1 className="mt-4 max-w-5xl font-display text-[clamp(2.65rem,6.2vw,5.65rem)] leading-[0.94] font-semibold tracking-[-0.07em] text-ink">
          A community air sensor said the air was clean. Aircord remembered not to trust it.
        </h1>
        <p className="mt-5 max-w-4xl text-[clamp(1rem,1.6vw,1.25rem)] leading-7 text-ink-secondary">
          PurpleAir sensor {sensorId} reported PM2.5 = {formatNumber(reading?.pm25_cf1, 0)} while a
          nearby AirNow regulatory monitor reported AQI {formatNumber(monitor?.latest_aqi, 0)}.
          Aircord checked the sensor&apos;s stored reliability, downweighted the reading, blended the
          estimate toward the reference, and wrote the decision to CockroachDB memory.
        </p>
      </div>

      <aside className="border-l border-line pl-5 lg:col-span-3">
        <Badge tone="amber">Active decision packet</Badge>
        <dl className="mt-4 space-y-3">
          <div>
            <dt className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">Subject</dt>
            <dd className="mt-1 text-sm text-ink-secondary">{present(sensor?.name)}</dd>
          </div>
          <div>
            <dt className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">Source</dt>
            <dd className="mt-1 flex items-center gap-2 text-xs text-ink-secondary">
              <StatusDot tone="mint" /> CockroachDB-backed static snapshot
            </dd>
          </div>
          <div>
            <dt className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">Captured</dt>
            <dd className="mt-1 font-mono text-[0.6875rem] text-muted">
              {formatTimestamp(generatedAt)}
            </dd>
          </div>
        </dl>
      </aside>
    </section>
  );
}
