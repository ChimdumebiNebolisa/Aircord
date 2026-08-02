import type { Backtest } from "../api/aircord";

export function BacktestPanel({ backtest }: { backtest: Backtest | null }) {
  if (!backtest) return null;
  const rows = backtest.summaries.filter((summary) => summary.segment === "degraded");
  return (
    <section className="panel backtest-panel">
      <div className="panel-kicker">Gate B · measured only</div>
      <div className="backtest-heading"><div><h2>Paired backtest</h2><p>{backtest.claim_status === "measured" ? "Computed from aligned monitor and sensor time series." : "No accuracy claim yet."}</p></div><span className={`status-pill ${backtest.claim_status}`}>{backtest.claim_status}</span></div>
      {backtest.claim_status === "measured" && rows.length > 0 ? <div className="metric-grid">{rows.map((row) => <div className="metric" key={row.method}><span>{row.method.replace("_", " ")}</span><strong>{row.mean_absolute_error}</strong><small>MAE · {row.observation_count} obs</small></div>)}</div> : <p className="muted">The system withholds the headline until Gate B has aligned observations.</p>}
    </section>
  );
}
