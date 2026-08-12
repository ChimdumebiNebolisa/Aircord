import { useEffect, useState, type ReactNode } from "react";
import { api, type DemoSummary } from "./api/aircord";

const repositoryDocs = "https://github.com/ChimdumebiNebolisa/Aircord/blob/main/docs";

function number(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toFixed(digits);
}

function label(value: string | null | undefined, fallback = "Unavailable") {
  return value || fallback;
}

function timestamp(value: string | null | undefined) {
  if (!value) return "Unavailable";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(parsed);
}

function Icon({ name }: { name: "arrow" | "database" | "pulse" | "audit" | "external" }) {
  const paths = {
    arrow: <><path d="M5 12h13" /><path d="m13 6 6 6-6 6" /></>,
    database: <><ellipse cx="12" cy="5" rx="7" ry="3" /><path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5" /><path d="M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7" /></>,
    pulse: <><path d="M3 12h4l2.1-6 4.1 12 2.1-6H21" /></>,
    audit: <><path d="M6 3h9l3 3v15H6z" /><path d="M9 12h6M9 16h6M9 8h3" /></>,
    external: <><path d="M14 4h6v6" /><path d="m20 4-9 9" /><path d="M18 13v6H4V5h6" /></>,
  }[name];
  return <svg aria-hidden="true" className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths}</svg>;
}

function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "danger" | "info" }) {
  return <span className={`chip chip-${tone}`}>{children}</span>;
}

function DataRow({ name, value, mono = false }: { name: string; value: ReactNode; mono?: boolean }) {
  return <div className="data-row"><dt>{name}</dt><dd className={mono ? "mono" : ""}>{value}</dd></div>;
}

function Card({ children, className = "", id }: { children: ReactNode; className?: string; id?: string }) {
  return <article id={id} className={`card ${className}`}>{children}</article>;
}

function App() {
  const [demo, setDemo] = useState<DemoSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.demoSummary().then(setDemo).catch((reason: Error) => {
      setError(`The live API and static snapshot could not be loaded. ${reason.message}`);
    });
  }, []);

  if (!demo && !error) {
    return <main className="app-frame"><div className="loading-state"><div className="brand">air<span>cord</span></div><Chip tone="info">Loading evidence</Chip><h1>Opening the memory layer.</h1><p>Reading the latest CockroachDB-backed snapshot.</p></div></main>;
  }

  if (error || !demo || demo.status === "empty") {
    return <main className="app-frame"><div className="empty-state"><div className="brand">air<span>cord</span></div><Chip tone="danger">No demo data</Chip><h1>Evidence is not available.</h1><p>{error || demo?.message || "The snapshot contains no persisted Aircord memory."}</p><code>python backend/scripts/demo_status.py --write-frontend-snapshot</code></div></main>;
  }

  const reading = demo.latest_sensor_reading;
  const sensor = demo.sensor;
  const monitor = demo.airnow_reference.monitor;
  const estimate = demo.latest_cell_estimate;
  const resolution = demo.latest_resolution;
  const decision = resolution?.sensors_considered?.[0];
  const formula = demo.weight_formula;
  const backtest = demo.latest_backtest;
  const backtestRows = backtest?.summaries.filter((row) => row.segment === "all") ?? [];
  const reasonCodes = resolution?.sensors_considered?.[0]?.reason_codes ?? [];
  const mcpAnswer = demo.mcp.answer_summary || "Sensor 54917 was downweighted because channel_divergence and monitor_disagreement were recorded in the live memory decision.";

  return (
    <main className="app-frame">
      <header className="topbar">
        <a className="brand" href="#top">air<span>cord</span></a>
        <nav className="topnav" aria-label="Page sections">
          <a href="#memory">Decision</a>
          <a href="#evidence">Evidence</a>
          <a href="#validation">Validation</a>
        </nav>
        <div className="top-status"><span className="status-dot" /> Live snapshot <span className="top-divider" /> {timestamp(demo.generated_at)}</div>
      </header>

      <div id="top" className="hero-grid">
        <section className="hero-copy">
          <p className="eyebrow">AIRCORD / GREATER LOS ANGELES / SENSOR 54917</p>
          <h1>Trust is a stored decision.</h1>
          <p className="hero-claim">Aircord learns which community air sensors to trust and explains why.</p>
          <p className="hero-body">A compact, inspectable memory layer that compares community readings to a regulatory reference, carries reputation forward, and leaves an audit trail for every estimate.</p>
          <div className="hero-actions"><a className="button button-dark" href="#memory">Inspect decision <Icon name="arrow" /></a><a className="text-link" href={`${repositoryDocs}/MCP_DEMO.md`} target="_blank" rel="noreferrer">Open MCP proof <Icon name="external" /></a></div>
          <div className="source-line"><Icon name="database" /> Source: CockroachDB-backed static snapshot <span>·</span> Captured {timestamp(demo.generated_at)}</div>
        </section>

        <aside className="decision-hero" aria-label="Current memory decision">
          <div className="decision-hero-top"><span className="eyebrow">CURRENT MEMORY DECISION</span><Chip tone="warning">{label(decision?.decision)}</Chip></div>
          <div className="decision-score"><span className="score-label">Trust weight</span><strong>{number(decision?.weight, 4)}</strong><span className="score-context">of the estimate assigned to sensor {demo.sensor_id}</span></div>
          <div className="decision-reasons"><span className="eyebrow">Recorded reasons</span><div className="chip-row">{reasonCodes.map((reason) => <Chip key={reason} tone="warning">{reason.replaceAll("_", " ")}</Chip>)}</div></div>
          <div className="decision-foot"><span>Reputation {number(formula.reputation_score, 4)}</span><span>Estimate {number(estimate?.estimate_aqi, 1)} AQI proxy</span></div>
        </aside>
      </div>

      <section className="stat-strip" aria-label="Live summary">
        <div><span className="stat-label">Sensor</span><strong>{demo.sensor_id}</strong><small>{label(sensor?.name)}</small></div>
        <div><span className="stat-label">AirNow reference</span><strong>{number(monitor?.latest_aqi, 0)}</strong><small>{label(monitor?.name)} · {label(monitor?.monitor_id)}</small></div>
        <div><span className="stat-label">Reputation</span><strong>{number(formula.reputation_score, 4)}</strong><small>Persistent sensor memory</small></div>
        <div><span className="stat-label">Confidence</span><strong>{number((estimate?.confidence ?? 0) * 100, 1)}%</strong><small>{label(backtest?.claim_status, "pending")}</small></div>
      </section>

      <section id="memory" className="section-block">
        <div className="section-heading"><div><p className="eyebrow">01 / MEMORY DECISION</p><h2>One reading. A remembered response.</h2></div><p>Aircord blends the sensor proxy with the reference using the stored reputation weight.</p></div>
        <div className="memory-grid">
          <Card className="estimate-card">
            <div className="card-heading"><div><span className="eyebrow">TRUST-WEIGHTED ESTIMATE</span><h3>{number(estimate?.estimate_aqi, 1)} <span>AQI proxy</span></h3></div><Chip tone="info">{label(backtest?.claim_status, "pending")}</Chip></div>
            <div className="weight-bar"><span style={{ width: `${Math.max(8, (decision?.weight ?? 0) * 100)}%` }} /><i style={{ left: `${Math.max(8, (decision?.weight ?? 0) * 100)}%` }} /></div>
            <div className="bar-labels"><span>Sensor {number(decision?.weight, 4)}</span><span>Reference {number(1 - (decision?.weight ?? 0), 4)}</span></div>
            <div className="formula-line"><span>Formula</span><strong>{formula.expression || "Unavailable until a resolution is stored"}</strong></div>
            <p className="muted">{formula.description}</p>
          </Card>
          <Card className="reason-card">
            <div className="card-heading"><div><span className="eyebrow">RESOLUTION REASONING</span><h3>Why the memory moved the estimate</h3></div><Icon name="pulse" /></div>
            <p className="reason-text">{label(resolution?.reasoning_text)}</p>
            <div className="reason-list">{reasonCodes.map((reason) => <div key={reason}><span className="signal-mark" /><span><strong>{reason.replaceAll("_", " ")}</strong><small>Recorded in the resolution and audit evidence.</small></span></div>)}</div>
          </Card>
        </div>
      </section>

      <section id="evidence" className="section-block">
        <div className="section-heading"><div><p className="eyebrow">02 / SOURCE EVIDENCE</p><h2>Inputs stay visible.</h2></div><p>No hidden normalization. The source reading and its reference remain inspectable beside the decision.</p></div>
        <div className="evidence-grid">
          <Card className="sensor-card"><div className="card-heading"><div><span className="eyebrow">COMMUNITY SENSOR</span><h3>{label(sensor?.name)}</h3></div><Chip tone="warning">Downweighted</Chip></div><div className="entity-id">Sensor {demo.sensor_id}</div><dl><DataRow name="Location" value={`${number(sensor?.latitude, 5)}, ${number(sensor?.longitude, 5)}`} mono /><DataRow name="Latest PM2.5" value={`${number(reading?.pm25_cf1)} ug/m3 CF1 / ${number(reading?.pm25_atm)} ug/m3 ATM`} /><DataRow name="Channels A / B" value={`${number(reading?.channel_a)} / ${number(reading?.channel_b)}`} mono /><DataRow name="Observed" value={timestamp(reading?.observed_at)} /><DataRow name="Raw S3 key" value={label(reading?.raw_s3_key)} mono /></dl></Card>
          <Card className="monitor-card"><div className="card-heading"><div><span className="eyebrow">AIRNOW REFERENCE</span><h3>{label(monitor?.name)}</h3></div><Chip tone="info">Evaluation reference</Chip></div><div className="entity-id">Monitor {label(monitor?.monitor_id)}</div><div className="reference-aqi"><strong>{number(monitor?.latest_aqi, 0)}</strong><span>AQI</span></div><dl><DataRow name="Distance" value={demo.airnow_reference.distance_km === null ? "Unavailable" : `${number(demo.airnow_reference.distance_km, 2)} km`} /><DataRow name="Observed" value={timestamp(monitor?.observed_at)} /></dl><p className="card-note">{demo.reference_caveat}</p></Card>
        </div>
      </section>

      <section className="section-block audit-section">
        <div className="section-heading"><div><p className="eyebrow">03 / AUDIT TRAIL</p><h2>Every change leaves a trace.</h2></div><p>{demo.audit_rows.length} latest persisted events from ingestion, memory, and validation.</p></div>
        <Card className="audit-card"><div className="audit-header"><span className="eyebrow"><Icon name="audit" /> EVENT LOG</span><span className="mono">sensor {demo.sensor_id}</span></div><div className="audit-table">{demo.audit_rows.slice(0, 8).map((row) => <div className="audit-event" key={row.audit_id ?? `${row.created_at}-${row.action}`}><span className="event-line" /><div className="event-main"><strong>{row.action.replaceAll("_", " ")}</strong><span>{row.actor} · {timestamp(row.created_at)}</span></div><span className="event-entity mono">{row.entity_type}:{row.entity_id}</span></div>)}</div></Card>
      </section>

      <section id="validation" className="section-block">
        <div className="section-heading"><div><p className="eyebrow">04 / PROOF SURFACES</p><h2>Memory, similarity, validation.</h2></div><p>The stored decision is surrounded by the context a judge can interrogate.</p></div>
        <div className="proof-grid">
          <Card className="vector-card"><div className="card-heading"><div><span className="eyebrow">VECTOR MEMORY</span><h3>Behavioral similarity</h3></div><span className="dimension-badge">VECTOR({demo.similarity.fingerprint_dimensions})</span></div><p className="card-note">Handcrafted feature directions, not a trained accuracy model.</p><div className="similarity-list">{demo.similarity.nearest.length ? demo.similarity.nearest.map((row) => <div className="similarity-row" key={row.sensor_id}><div><strong>{row.sensor_id}</strong><span>{label(row.source)}{row.label ? ` · ${row.label}` : ""}</span></div><b>{number(row.cosine_distance, 5)}</b></div>) : <p className="muted">No other fingerprints are stored.</p>}</div><div className="feature-line"><span>Latest fingerprint</span><strong>{demo.similarity.fingerprint_dimensions} dimensions</strong></div></Card>
          <Card className="backtest-card"><div className="card-heading"><div><span className="eyebrow">PAIRED BACKTEST</span><h3>Measured comparison</h3></div><Chip tone={backtest?.status === "passed" ? "success" : "warning"}>{label(backtest?.claim_status, "pending")}</Chip></div><div className="backtest-meta"><span>{backtest?.backtest_run_id || "No run stored"}</span><strong>{backtestRows[0]?.observation_count ?? 0} aligned samples</strong></div><div className="metric-table">{["raw_purpleair", "static_correction", "aircord"].map((method) => { const row = backtestRows.find((item) => item.method === method); return <div key={method}><span>{method.replaceAll("_", " ")}</span><strong>{row?.mean_absolute_error === null || row?.mean_absolute_error === undefined ? "—" : number(row.mean_absolute_error, 2)}</strong><small>MAE</small></div>; })}</div><div className="caveat-box"><strong>Read with caveats</strong>{demo.caveats.slice(0, 3).map((caveat) => <p key={caveat}>{caveat}</p>)}</div></Card>
          <Card className="mcp-card"><div className="card-heading"><div><span className="eyebrow">MANAGED MCP</span><h3>Ask the memory layer</h3></div><Chip tone="success">Connected through Codex</Chip></div><p className="mcp-answer"><strong>Why was sensor 54917 downweighted?</strong><br />{mcpAnswer}</p><div className="mcp-links"><a href={`${repositoryDocs}/MCP_DEMO.md`} target="_blank" rel="noreferrer">MCP demo notes <Icon name="external" /></a><a href={`${repositoryDocs}/cockroachdb_mcp_queries.sql`} target="_blank" rel="noreferrer">Read-only query pack <Icon name="external" /></a></div><div className="question-list">{demo.mcp.questions.slice(0, 4).map((question) => <span key={question}>{question}</span>)}</div></Card>
        </div>
      </section>

      <footer className="footer"><div><span className="brand">air<span>cord</span></span><span className="footer-meta">Persistent trust memory for one metro.</span></div><div className="footer-caveats"><span>{demo.reference_caveat}</span><span>{demo.medical_directive_caveat}</span></div></footer>
    </main>
  );
}

export default App;
