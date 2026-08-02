import { useEffect, useState } from "react";
import { api, type Backtest, type CellDetail, type CellSummary, type Cluster, type Showcase } from "./api/aircord";
import { BacktestPanel } from "./components/BacktestPanel";
import { CellDetailPanel } from "./components/CellDetailPanel";
import { DegradedSensorPanel } from "./components/DegradedSensorPanel";
import { ClusterView } from "./pages/ClusterView";

export default function App() {
  const [cluster, setCluster] = useState<Cluster | null>(null);
  const [cells, setCells] = useState<CellSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<CellDetail | null>(null);
  const [showcase, setShowcase] = useState<Showcase | null>(null);
  const [backtest, setBacktest] = useState<Backtest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    Promise.all([api.cluster(), api.cells(), api.showcase(), api.backtest()])
      .then(([clusterData, cellData, showcaseData, backtestData]) => { setCluster(clusterData); setCells(cellData); setShowcase(showcaseData); setBacktest(backtestData); if (cellData[0]) setSelected(cellData[0].cell_id); })
      .catch(() => setError("The API is not reachable. Start the backend with uvicorn aircord.main:app --reload."));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoadingDetail(true);
    api.cell(selected).then(setDetail).catch(() => setError("Could not load that cell." )).finally(() => setLoadingDetail(false));
  }, [selected]);

  return <main className="app-shell"><header className="topbar"><div className="brand-mark"><span>air</span>cord</div><div className="topbar-meta"><span className="live-dot" />{cluster?.name ?? "Air quality trust memory"}</div></header><section className="hero"><div><p className="eyebrow">An agentic memory for air quality</p><h1>Know the number.<br /><em>Know who to trust.</em></h1><p className="lede">Aircord reconciles sparse regulatory references with dense community sensors, then remembers which sensors earn confidence over time.</p>{cluster?.mode === "fixture" && <p className="fixture-note">Fixture evidence · live AirNow/PurpleAir Gate A still requires credentials.</p>}</div><div className="hero-stamp"><span className="stamp-label">Gate A</span><strong>{cluster?.gate_a_status ?? "…"}</strong><small>paired evidence</small></div></section>{error && <div className="error-banner">{error}</div>}<section className="dashboard"><ClusterView cells={cells} selected={selected} onSelect={setSelected} /><CellDetailPanel detail={detail} loading={loadingDetail} /></section><DegradedSensorPanel showcase={showcase} /><BacktestPanel backtest={backtest} /><footer><span>Aircord · learned, auditable trust</span><span>Regulatory monitors are a reference, not absolute truth · not medical advice</span></footer></main>;
}
