import { Link } from "react-router-dom";
import type { DemoSummary } from "../api/aircord";
import { Badge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusDot } from "../components/ui/StatusDot";
import { formatNumber, formatTimestamp, humanize, present } from "../lib/format";

const repositoryUrl = "https://github.com/ChimdumebiNebolisa/Aircord";

const memoryRecords = [
  "readings",
  "monitor references",
  "sensor reputation",
  "cell estimates",
  "resolutions",
  "audit log",
  "backtest runs",
  "VECTOR(8) behavioral fingerprints",
];

const steps = [
  {
    number: "01",
    title: "Observe",
    body: "Ingest PurpleAir and AirNow readings, preserving raw evidence in S3.",
  },
  {
    number: "02",
    title: "Remember",
    body: "Store readings, reputation, audit logs, resolutions, and behavioral fingerprints in CockroachDB.",
  },
  {
    number: "03",
    title: "Resolve",
    body: "Use stored reliability memory to decide how much to trust each reading, then write the decision back.",
  },
];

export function LandingPage({
  demo,
  error,
  loading,
}: {
  demo: DemoSummary | null;
  error: string | null;
  loading: boolean;
}) {
  return (
    <main id="top" className="mx-auto w-[min(1440px,calc(100%-2rem))] pb-10 sm:w-[min(1440px,calc(100%-3rem))] lg:w-[min(1440px,calc(100%-4rem))]">
      <LandingHeader />

      <section className="grid min-h-[calc(100vh-4rem)] items-center gap-12 py-14 lg:grid-cols-[minmax(0,1.12fr)_minmax(23rem,0.88fr)] lg:py-20">
        <div>
          <p className="font-mono text-[0.625rem] font-medium tracking-[0.14em] text-mint uppercase">
            Agentic memory for sensor trust
          </p>
          <h1 className="mt-5 max-w-4xl font-display text-[clamp(3.25rem,7.4vw,7.4rem)] leading-[0.88] font-semibold tracking-[-0.075em] text-ink">
            Air sensors disagree. Aircord remembers which ones to trust.
          </h1>
          <p className="mt-7 max-w-2xl text-[clamp(1rem,1.5vw,1.25rem)] leading-8 text-ink-secondary">
            Persistent sensor reliability memory that learns from past behavior, downweights unreliable
            community readings, and explains every decision.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="inline-flex min-h-11 items-center justify-center rounded-control border border-mint bg-mint px-5 font-mono text-xs font-medium tracking-[0.06em] text-canvas uppercase no-underline hover:bg-ink"
              to="/app"
            >
              Try Aircord →
            </Link>
            <a
              className="inline-flex min-h-11 items-center justify-center rounded-control border border-line-strong bg-panel px-5 font-mono text-xs font-medium tracking-[0.06em] text-ink-secondary uppercase no-underline hover:border-mint hover:text-mint"
              href={repositoryUrl}
              rel="noreferrer"
              target="_blank"
            >
              View GitHub ↗
            </a>
          </div>
          <p className="mt-8 flex items-center gap-2 font-mono text-[0.625rem] tracking-[0.08em] text-muted uppercase">
            <StatusDot tone="mint" /> CockroachDB memory · AWS evidence pipeline · public proof
          </p>
        </div>

        <ProductPreview demo={demo} error={error} loading={loading} />
      </section>

      <section id="problem" className="scroll-mt-20 border-t border-line py-20">
        <SectionHeader
          eyebrow="The gap"
          title="Fast coverage needs a memory of trust."
          description="Aircord sits between high-density community observations and sparse regulatory references."
        />
        <div className="grid gap-3 lg:grid-cols-3">
          <ProblemCard
            label="Community sensors"
            title="Dense and fast"
            body="Useful local coverage, but devices can drift, fail, or disagree across channels."
          />
          <ProblemCard
            label="Regulatory monitors"
            title="Trusted and sparse"
            body="A stronger evaluation reference, but too sparse to explain every neighborhood reading alone."
          />
          <ProblemCard
            accent
            label="Aircord"
            title="Memory between them"
            body="Persistent reliability history changes how much influence each new community reading receives."
          />
        </div>
      </section>

      <section id="how-it-works" className="scroll-mt-20 py-20">
        <SectionHeader
          eyebrow="How it works"
          title="Observe. Remember. Resolve."
          description="One inspectable loop retrieves memory before acting and writes the result back afterward."
        />
        <div className="grid gap-px overflow-hidden rounded-panel border border-line bg-line lg:grid-cols-3">
          {steps.map((step) => (
            <article className="bg-panel p-6 lg:min-h-64" key={step.number}>
              <span className="font-mono text-[0.625rem] tracking-[0.14em] text-mint uppercase">
                {step.number} / {step.title}
              </span>
              <h3 className="mt-12 font-display text-3xl font-semibold tracking-[-0.045em] text-ink">
                {step.title}
              </h3>
              <p className="mt-3 max-w-sm text-sm leading-6 text-muted">{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="py-20">
        <SectionHeader
          eyebrow="Memory changes the answer"
          title="The same reading. A different decision."
          description="Stored reliability turns a fresh-looking zero into an explained, downweighted input."
        />
        <div className="grid gap-3 lg:grid-cols-2">
          <article className="rounded-card border border-line bg-panel p-6 shadow-card">
            <Badge tone="neutral">Without memory</Badge>
            <p className="mt-8 font-display text-[clamp(2rem,4vw,3.5rem)] leading-none font-semibold tracking-[-0.055em] text-ink">
              A reading of 0 looks clean.
            </p>
            <p className="mt-4 max-w-lg text-sm leading-6 text-muted">
              A timestamp alone cannot reveal channel disagreement or a sensor&apos;s prior behavior.
            </p>
          </article>
          <article className="rounded-card border border-amber/35 bg-panel-elevated p-6 shadow-card">
            <Badge tone="amber">With Aircord</Badge>
            <p className="mt-8 font-display text-[clamp(2rem,4vw,3.5rem)] leading-none font-semibold tracking-[-0.055em] text-ink">
              The sensor is downweighted.
            </p>
            <p className="mt-4 max-w-xl text-sm leading-6 text-ink-secondary">
              Memory records channel divergence and monitor disagreement, reducing this sensor&apos;s influence
              to {formatNumber(demo?.weight_formula.sensor_weight, 4)}.
            </p>
          </article>
        </div>
      </section>

      <section id="memory" className="scroll-mt-20 py-20">
        <SectionHeader
          eyebrow="CockroachDB memory layer"
          title="CockroachDB is not just storage."
          description="It is Aircord's persistent memory layer—the state retrieved before a decision and updated after it."
        />
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.25fr)_minmax(20rem,0.75fr)]">
          <article className="rounded-card border border-mint/25 bg-panel p-6 shadow-card">
            <div className="grid gap-px overflow-hidden rounded-control border border-line bg-line sm:grid-cols-2">
              {memoryRecords.map((record) => (
                <div className="flex items-center gap-3 bg-panel-elevated px-4 py-3" key={record}>
                  <StatusDot tone="mint" />
                  <span className="font-mono text-[0.6875rem] text-ink-secondary">{record}</span>
                </div>
              ))}
            </div>
          </article>
          <div className="grid gap-3">
            <ToolCard
              label="Distributed Vector Indexing"
              body="Searches explainable VECTOR(8) behavioral fingerprints for similar sensor behavior."
            />
            <ToolCard
              label="Managed MCP Server"
              body="Lets Codex ask the live memory why sensor 54917 was downweighted."
            />
          </div>
        </div>
      </section>

      <section className="py-20">
        <SectionHeader
          eyebrow="AWS evidence path"
          title="Acquire the reading. Preserve the source."
          description="AWS runs the bounded ingestion path while CockroachDB turns observations into persistent decision memory."
        />
        <div className="grid gap-3 lg:grid-cols-3">
          <InfrastructureCard
            label="AWS Lambda"
            body="Serverless PurpleAir ingestion execution."
          />
          <InfrastructureCard
            label="Amazon EventBridge"
            body="A bounded 15-minute ingestion schedule."
          />
          <InfrastructureCard
            label="Amazon S3"
            body="Immutable raw PurpleAir and AirNow evidence snapshots."
          />
        </div>
      </section>

      <section id="architecture" className="scroll-mt-20 py-20">
        <SectionHeader
          eyebrow="Architecture"
          title="Evidence in. Memory updated. Decision explained."
          description="The public demo ships only a generated snapshot; database credentials never reach the browser."
        />
        <div className="grid gap-2 rounded-panel border border-line bg-panel p-4 shadow-card sm:grid-cols-2 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr_auto_1fr] lg:items-center">
          <ArchitectureNode label="Inputs" value="PurpleAir + AirNow" />
          <ArchitectureArrow />
          <ArchitectureNode label="Ingestion" value="AWS Lambda / scripts" />
          <ArchitectureArrow />
          <ArchitectureNode label="Raw evidence" value="Amazon S3" />
          <ArchitectureArrow />
          <ArchitectureNode accent label="Memory" value="CockroachDB" />
          <ArchitectureArrow />
          <ArchitectureNode label="Proof" value="Aircord + Vercel" />
        </div>
      </section>

      <section className="my-16 rounded-panel border border-mint/25 bg-panel-elevated px-6 py-12 shadow-card sm:px-10 lg:flex lg:items-end lg:justify-between lg:gap-10">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.14em] text-mint uppercase">
            Inspect the working memory
          </p>
          <h2 className="mt-4 max-w-3xl font-display text-[clamp(2.5rem,5vw,4.75rem)] leading-[0.95] font-semibold tracking-[-0.065em] text-ink">
            A community sensor said the air was clean. Aircord remembered not to trust it.
          </h2>
        </div>
        <Link
          className="mt-8 inline-flex min-h-12 shrink-0 items-center justify-center rounded-control border border-mint bg-mint px-6 font-mono text-xs font-medium tracking-[0.06em] text-canvas uppercase no-underline hover:bg-ink lg:mt-0"
          to="/app"
        >
          Try Aircord →
        </Link>
      </section>

      <footer className="border-t border-line py-8">
        <div className="flex flex-col gap-5 text-[0.6875rem] leading-5 text-muted lg:flex-row lg:items-start lg:justify-between">
          <span className="font-display text-lg font-semibold tracking-[-0.05em] text-ink">
            air<span className="text-mint">cord</span>
          </span>
          <p className="m-0 max-w-3xl lg:text-right">
            Aircord is not medical advice and does not claim absolute air-quality truth. AirNow is used as
            a regulatory reference, and the backtest is a small reference-based proof, not a broad accuracy
            claim. PM2.5 and AQI are different measures.
          </p>
        </div>
      </footer>
    </main>
  );
}

function LandingHeader() {
  return (
    <header className="flex min-h-16 flex-wrap items-center gap-4 border-b border-line py-4">
      <a
        aria-label="Aircord home"
        className="mr-auto font-display text-xl font-bold tracking-[-0.075em] text-ink no-underline"
        href="#top"
      >
        air<span className="text-mint">cord</span>
      </a>
      <nav
        aria-label="Product sections"
        className="order-3 flex w-full flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[0.625rem] tracking-[0.08em] text-muted uppercase sm:order-none sm:w-auto"
      >
        <a className="no-underline hover:text-mint" href="#how-it-works">How it works</a>
        <a className="no-underline hover:text-mint" href="#memory">Memory layer</a>
        <a className="no-underline hover:text-mint" href="#architecture">Architecture</a>
        <a className="no-underline hover:text-mint" href={repositoryUrl} rel="noreferrer" target="_blank">GitHub</a>
      </nav>
      <Link
        className="inline-flex min-h-9 items-center rounded-control border border-mint/40 bg-mint-dim px-3 font-mono text-[0.625rem] font-medium tracking-[0.08em] text-mint uppercase no-underline hover:border-mint"
        to="/app"
      >
        Try Aircord
      </Link>
    </header>
  );
}

function ProductPreview({
  demo,
  error,
  loading,
}: {
  demo: DemoSummary | null;
  error: string | null;
  loading: boolean;
}) {
  const ready = demo?.status === "ok";
  const decision = demo?.latest_resolution?.sensors_considered[0];
  const reasons = decision?.reason_codes ?? [];

  return (
    <aside className="relative rounded-panel border border-line-strong bg-panel p-3 shadow-card">
      <div className="rounded-card border border-line bg-panel-elevated p-5">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line pb-4">
          <div>
            <p className="font-mono text-[0.625rem] tracking-[0.12em] text-muted uppercase">
              Live decision packet
            </p>
            <h2 className="mt-2 font-display text-2xl font-semibold tracking-[-0.045em] text-ink">
              Sensor {ready ? demo.sensor_id : "memory"}
            </h2>
          </div>
          <Badge tone={ready ? "amber" : error ? "danger" : "info"}>
            {ready ? present(decision?.decision, "Unavailable") : loading ? "Loading snapshot" : "Snapshot unavailable"}
          </Badge>
        </div>

        {ready ? (
          <>
            <div className="grid grid-cols-2 gap-px overflow-hidden rounded-control border border-line bg-line mt-5">
              <PreviewMetric
                label="PurpleAir"
                unit="PM2.5"
                value={formatNumber(demo.latest_sensor_reading?.pm25_cf1, 0)}
              />
              <PreviewMetric
                accent="danger"
                label="AirNow"
                unit="AQI"
                value={formatNumber(demo.airnow_reference.monitor?.latest_aqi, 0)}
              />
            </div>
            <dl className="mt-4 divide-y divide-line border-y border-line">
              <PreviewRow label="Reputation" value={formatNumber(demo.weight_formula.reputation_score, 4)} />
              <PreviewRow label="Trust weight" value={formatNumber(demo.weight_formula.sensor_weight, 4)} tone="amber" />
              <PreviewRow label="Aircord estimate" value={formatNumber(demo.latest_cell_estimate?.estimate_aqi, 1)} tone="mint" />
            </dl>
            <div className="mt-4">
              <span className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">Reasons</span>
              <div className="mt-2 flex flex-wrap gap-2">
                {reasons.map((reason) => <Badge key={reason} tone="amber">{humanize(reason)}</Badge>)}
              </div>
            </div>
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4 font-mono text-[0.625rem] text-muted">
              <span className="flex items-center gap-2"><StatusDot tone="mint" /> CockroachDB-backed snapshot</span>
              <span>{formatTimestamp(demo.generated_at)}</span>
            </div>
          </>
        ) : (
          <div className="grid min-h-80 place-content-center px-4 text-center">
            <p className="font-display text-2xl font-semibold tracking-[-0.04em] text-ink">
              Decision preview unavailable.
            </p>
            <p className="mt-3 max-w-sm text-sm leading-6 text-muted">
              {loading
                ? "Opening the CockroachDB-backed snapshot."
                : error ?? demo?.message ?? "No persisted demo snapshot could be loaded."}
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}

function PreviewMetric({
  label,
  value,
  unit,
  accent = "default",
}: {
  label: string;
  value: string;
  unit: string;
  accent?: "default" | "danger";
}) {
  return (
    <div className="bg-panel px-4 py-5">
      <span className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">{label}</span>
      <div className="mt-2 flex items-baseline gap-2">
        <strong className={`font-display text-4xl font-semibold tracking-[-0.06em] ${accent === "danger" ? "text-danger" : "text-ink"}`}>
          {value}
        </strong>
        <span className="font-mono text-[0.625rem] text-muted uppercase">{unit}</span>
      </div>
    </div>
  );
}

function PreviewRow({ label, value, tone = "default" }: { label: string; value: string; tone?: "default" | "mint" | "amber" }) {
  const toneClass = tone === "mint" ? "text-mint" : tone === "amber" ? "text-amber" : "text-ink-secondary";
  return (
    <div className="flex items-center justify-between gap-5 py-3">
      <dt className="font-mono text-[0.625rem] tracking-[0.1em] text-muted uppercase">{label}</dt>
      <dd className={`m-0 font-mono text-sm font-medium ${toneClass}`}>{value}</dd>
    </div>
  );
}

function ProblemCard({ label, title, body, accent = false }: { label: string; title: string; body: string; accent?: boolean }) {
  return (
    <article className={`rounded-card border p-6 shadow-card ${accent ? "border-mint/30 bg-panel-elevated" : "border-line bg-panel"}`}>
      <p className={`font-mono text-[0.625rem] tracking-[0.12em] uppercase ${accent ? "text-mint" : "text-muted"}`}>{label}</p>
      <h3 className="mt-8 font-display text-3xl font-semibold tracking-[-0.045em] text-ink">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
    </article>
  );
}

function ToolCard({ label, body }: { label: string; body: string }) {
  return (
    <article className="rounded-card border border-line bg-panel-elevated p-5 shadow-card">
      <Badge tone="mint">CockroachDB tool</Badge>
      <h3 className="mt-5 font-display text-xl font-semibold tracking-[-0.035em] text-ink">{label}</h3>
      <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
    </article>
  );
}

function InfrastructureCard({ label, body }: { label: string; body: string }) {
  return (
    <article className="rounded-card border border-line bg-panel p-6 shadow-card">
      <span className="font-mono text-[0.625rem] tracking-[0.12em] text-info uppercase">AWS service</span>
      <h3 className="mt-8 font-display text-2xl font-semibold tracking-[-0.04em] text-ink">{label}</h3>
      <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
    </article>
  );
}

function ArchitectureNode({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`rounded-control border px-3 py-4 text-center ${accent ? "border-mint/35 bg-mint-dim" : "border-line bg-panel-elevated"}`}>
      <span className="block font-mono text-[0.5625rem] tracking-[0.1em] text-muted uppercase">{label}</span>
      <strong className={`mt-2 block font-mono text-[0.6875rem] ${accent ? "text-mint" : "text-ink-secondary"}`}>{value}</strong>
    </div>
  );
}

function ArchitectureArrow() {
  return <span aria-hidden="true" className="hidden font-mono text-sm text-faint lg:block">→</span>;
}
