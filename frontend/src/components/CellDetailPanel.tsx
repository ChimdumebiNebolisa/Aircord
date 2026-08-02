import type { CellDetail } from "../api/aircord";

type Props = { detail: CellDetail | null; loading: boolean };

export function CellDetailPanel({ detail, loading }: Props) {
  if (loading) return <aside className="panel detail-panel"><div className="skeleton" /></aside>;
  if (!detail) return <aside className="panel detail-panel"><p className="muted">Select a cell to inspect its memory.</p></aside>;
  return (
    <aside className="panel detail-panel" aria-label="Cell detail">
      <div className="panel-kicker">Cell inspection</div>
      <h2>{detail.cell_id.replace("cell-", "").replace("-", " ")}</h2>
      {detail.estimate ? (
        <div className="estimate-hero">
          <div><span className="eyebrow">Aircord estimate</span><strong>{Math.round(detail.estimate.estimated_aqi)}</strong><span className="unit">AQI proxy</span></div>
          <div className="confidence"><span>{Math.round(detail.estimate.confidence * 100)}%</span><small>confidence</small></div>
        </div>
      ) : <p className="muted">Insufficient evidence for a current estimate.</p>}
      {detail.resolution && (
        <>
          <p className="rationale">{detail.resolution.rationale_text}</p>
          <div className="sensor-list">
            <div className="section-label">Reputation decisions</div>
            {detail.resolution.sensors.map((sensor) => (
              <div className="sensor-row" key={sensor.sensor_id}>
                <div><strong>{sensor.sensor_id.replace("sensor-", "")}</strong><span>{sensor.reason_codes.join(" · ")}</span></div>
                <div className={`decision ${sensor.decision}`}><b>{sensor.decision}</b><span>{sensor.weight.toFixed(2)} wt</span></div>
              </div>
            ))}
          </div>
        </>
      )}
      <div className="caveats"><p>{detail.reference_caveat}</p><p>{detail.medical_directive_caveat}</p></div>
    </aside>
  );
}
