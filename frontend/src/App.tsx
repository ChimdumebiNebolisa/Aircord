import { useEffect, useState } from "react";
import { api, type DemoSummary } from "./api/aircord";

function number(value: number | null | undefined, digits = 1) {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

function text(value: string | null | undefined) {
  return value || "—";
}

const repositoryDocs = "https://github.com/ChimdumebiNebolisa/Aircord/blob/main/docs";

function App() {
  const [demo, setDemo] = useState<DemoSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.demoSummary().then(setDemo).catch(() => setError("Demo data is unavailable. Start the API or regenerate the static snapshot."));
  }, []);

  const reading = demo?.latest_sensor_reading;
  const monitor = demo?.airnow_reference.monitor;
  const estimate = demo?.latest_cell_estimate;
  const resolution = demo?.latest_resolution;
  const decision = resolution?.sensors_considered[0];
  const formula = demo?.weight_formula;
  const formulaScore = formula?.reputation_score ?? decision?.reputation_score ?? null;
  const formulaWeight = formula?.sensor_weight ?? decision?.weight ?? null;
  const formulaMultiplier = formula?.multiplier ?? (
    decision?.decision === "ignored" ? 0 : decision?.decision === "downweighted" ? 0.5 : 1
  );
  const formulaExpression = formula?.expression ?? (
    formulaScore === null || formulaWeight === null
      ? "Unavailable until a resolution is stored"
      : `${number(formulaScore, 4)} × ${number(formulaMultiplier, 2)} = ${number(formulaWeight, 4)}`
  );
  const mcpConnected = demo?.mcp.connected_through_codex ?? false;
  const mcpAnswer = demo?.mcp.answer_summary ?? "Sensor 54917 was downweighted because channel_divergence and monitor_disagreement were recorded in the live memory decision.";
  const backtest = demo?.latest_backtest;
  const allBacktest = backtest?.summaries.filter((row) => row.segment === "all") ?? [];

  return (
    <main className="demo-shell">
      <header className="demo-header">
        <div>
          <div className="brand-mark"><span>air</span>cord</div>
          <p className="eyebrow">CockroachDB trust-memory demo</p>
        </div>
        <div className={`live-status ${demo?.status ?? "loading"}`}>
          <span className="live-dot" /> {demo?.status === "ok" ? "Live memory loaded" : "Loading memory"}
        </div>
      </header>

      <section className="demo-hero">
        <div>
          <p className="eyebrow">One metro · one remembered decision</p>
          <h1>Aircord</h1>
          <p className="claim">Aircord learns which community air sensors to trust and explains why.</p>
          <p className="lede">A small, inspectable proof surface for live ingestion, reputation, resolution, auditability, vector similarity, and measured backtest evidence.</p>
        </div>
        <div className="proof-stamp"><strong>7</strong><span>proof surfaces</span><small>one CockroachDB memory layer</small></div>
      </section>

      {error && <div className="error-banner">{error}</div>}
      {!demo && !error && <div className="loading-card">Loading the latest CockroachDB-backed demo summary…</div>}
      {demo && (
        <>
          <section className="proof-grid">
            <article className="proof-card sensor-card">
              <div className="card-kicker">01 · live sensor</div>
              <h2>{text(demo.sensor?.name)}</h2>
              <div className="big-id">Sensor {demo.sensor_id}</div>
              <dl>
                <div><dt>Location</dt><dd>{number(demo.sensor?.latitude, 4)}, {number(demo.sensor?.longitude, 4)}</dd></div>
                <div><dt>PM2.5 CF1 / ATM</dt><dd>{number(reading?.pm25_cf1)} / {number(reading?.pm25_atm)} µg/m³</dd></div>
                <div><dt>Channels A / B</dt><dd>{number(reading?.channel_a)} / {number(reading?.channel_b)}</dd></div>
                <div><dt>Raw S3 key</dt><dd className="mono wrap">{text(reading?.raw_s3_key)}</dd></div>
              </dl>
            </article>

            <article className="proof-card reference-card">
              <div className="card-kicker">02 · AirNow reference</div>
              <h2>{text(monitor?.name)}</h2>
              <div className="big-number">{number(monitor?.latest_aqi, 0)}</div>
              <span className="metric-label">AQI reference</span>
              <dl>
                <div><dt>Monitor</dt><dd className="mono">{text(monitor?.monitor_id)}</dd></div>
                <div><dt>Distance</dt><dd>{demo.airnow_reference.distance_km === null ? "—" : `${demo.airnow_reference.distance_km} km`}</dd></div>
                <div><dt>Observed</dt><dd>{text(monitor?.observed_at)}</dd></div>
              </dl>
              <p className="small-note">Regulatory monitors are evaluation references, not absolute truth.</p>
            </article>

            <article className="proof-card memory-card featured-card">
              <div className="card-kicker">03 · memory decision</div>
              <div className="memory-heading"><div><h2>Trust changed the answer</h2><span className={`decision-badge ${decision?.decision ?? "unknown"}`}>{text(decision?.decision)}</span></div><div className="big-number">{number(estimate?.estimate_aqi, 1)}</div></div>
              <dl className="memory-metrics">
                <div><dt>Reputation</dt><dd>{number(Number(demo.sensor_reputation?.reputation_score), 4)}</dd></div>
                <div><dt>Weight</dt><dd>{number(decision?.weight, 4)}</dd></div>
                <div><dt>Confidence</dt><dd>{estimate ? `${number(estimate.confidence * 100, 1)}%` : "—"}</dd></div>
              </dl>
              <div className="formula-box"><span>Weight formula</span><strong>{formulaExpression}</strong><small>{formula?.description ?? "sensor_weight = reputation_score × multiplier; downweighted sensors use 0.50"}</small></div>
              <p className="reasoning">{text(resolution?.reasoning_text)}</p>
            </article>

            <article className="proof-card audit-card">
              <div className="card-kicker">04 · audit trail</div>
              <h2>Every decision leaves evidence</h2>
              <div className="audit-list">{demo.audit_rows.slice(0, 6).map((row) => <div className="audit-row" key={row.audit_id ?? `${row.created_at}-${row.action}`}><span className="audit-dot" /><div><strong>{row.action.replaceAll("_", " ")}</strong><span>{row.actor} · {row.created_at}</span></div></div>)}</div>
            </article>

            <article className="proof-card vector-card">
              <div className="card-kicker">05 · distributed vector index</div>
              <h2>Behavioral similarity</h2>
              <div className="vector-summary"><strong>{demo.similarity.fingerprint_dimensions}</strong><span>handcrafted dimensions<br />not a trained model</span></div>
              <div className="similar-list">{demo.similarity.nearest.length ? demo.similarity.nearest.map((row) => <div className="similar-row" key={row.sensor_id}><div><strong>{row.sensor_id}</strong><span>{row.source}{row.label ? ` · ${row.label}` : ""}</span></div><b>{number(row.cosine_distance, 5)}</b></div>) : <p className="small-note">No other fingerprints are stored yet.</p>}</div>
              <p className="small-note">Lower cosine distance means more similar feature directions, not better accuracy.</p>
            </article>

            <article className="proof-card backtest-card">
              <div className="card-kicker">06 · measured backtest</div>
              <div className="backtest-heading"><div><h2>Reference comparison</h2><span className="status-badge">{text(backtest?.claim_status)}</span></div><span className="sample-count">{backtest?.summaries.find((row) => row.segment === "all")?.observation_count ?? 0} aligned samples</span></div>
              <div className="metric-grid">{["raw_purpleair", "static_correction", "aircord"].map((method) => { const row = allBacktest.find((item) => item.method === method); return <div className={method === "aircord" ? "metric highlight" : "metric"} key={method}><span>{method.replaceAll("_", " ")}</span><strong>{row?.mean_absolute_error === null || row?.mean_absolute_error === undefined ? "—" : number(row.mean_absolute_error, 2)}</strong><small>MAE</small></div>; })}</div>
              <div className="caveat-box">{demo.caveats.map((caveat) => <p key={caveat}>· {caveat}</p>)}</div>
            </article>

            <article className="proof-card mcp-card">
              <div className="card-kicker">07 · MCP judge path</div>
              <h2>Ask the memory layer</h2>
              <div className="mcp-connection"><span className="live-dot" /> {mcpConnected ? "Connected through Codex" : "Read-only path documented"}</div>
              <p className="answer-callout"><strong>Why was sensor 54917 downweighted?</strong> {mcpAnswer}</p>
              <code className="query-path">{demo.mcp.query_path}</code>
              <ul>{demo.mcp.questions.map((question) => <li key={question}>{question}</li>)}</ul>
              <div className="mcp-links"><a href={`${repositoryDocs}/MCP_DEMO.md`} target="_blank" rel="noreferrer">MCP demo notes</a><a href={`${repositoryDocs}/cockroachdb_mcp_queries.sql`} target="_blank" rel="noreferrer">Read-only query pack</a></div>
            </article>
          </section>
          <footer className="demo-footer"><span>Aircord · CockroachDB-backed proof surface</span><span>{demo.reference_caveat} · {demo.medical_directive_caveat}</span></footer>
        </>
      )}
    </main>
  );
}

export default App;
