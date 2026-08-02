import type { Showcase } from "../api/aircord";

export function DegradedSensorPanel({ showcase }: { showcase: Showcase | null }) {
  if (!showcase) return null;
  const shift = showcase.aircord_estimate - showcase.raw_or_static_estimate;
  return (
    <section className="panel showcase-panel">
      <div className="panel-kicker">The memory beat</div>
      <div className="showcase-heading"><div><h2>{showcase.sensor_id.replace("sensor-", "")} changed the answer</h2><p>{showcase.reputation_reason}</p></div><span className="delta">{shift > 0 ? "+" : ""}{shift.toFixed(1)} AQI</span></div>
      <div className="compare-row"><div><span>Raw / static baseline</span><strong>{showcase.raw_or_static_estimate}</strong></div><div className="arrow">→</div><div className="accent"><span>Aircord, with memory</span><strong>{showcase.aircord_estimate}</strong></div></div>
    </section>
  );
}
