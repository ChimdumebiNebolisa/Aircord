import type { CellSummary } from "../api/aircord";

type Props = { cells: CellSummary[]; selected: string | null; onSelect: (id: string) => void };

function tone(aqi: number | undefined) {
  if (aqi === undefined) return "unknown";
  if (aqi <= 50) return "good";
  if (aqi <= 100) return "watch";
  if (aqi <= 150) return "unhealthy";
  return "danger";
}

export function ClusterView({ cells, selected, onSelect }: Props) {
  return <section className="map-card"><div className="map-toolbar"><div><span className="panel-kicker">Metro cluster</span><h2>Live trust surface</h2></div><span className="map-note">One bounded cluster · {cells.length} cells</span></div><div className="grid-map">{cells.map((cell) => <button className={`cell-card ${selected === cell.cell_id ? "selected" : ""}`} key={cell.cell_id} onClick={() => onSelect(cell.cell_id)}><span className={`cell-dot ${tone(cell.latest_estimate?.estimated_aqi)}`} /><strong>{cell.cell_id.replace("cell-", "")}</strong><span>{cell.latest_estimate ? `${Math.round(cell.latest_estimate.estimated_aqi)} AQI` : "No estimate"}</span><small>{cell.latest_estimate ? `${Math.round(cell.latest_estimate.confidence * 100)}% conf.` : "Select to inspect"}</small></button>)}</div><div className="legend"><span><i className="good" />reference-aligned</span><span><i className="unhealthy" />disagreement</span><span><i className="danger" />low trust signal</span></div></section>;
}
