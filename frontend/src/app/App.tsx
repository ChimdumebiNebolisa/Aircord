import { useEffect, useState } from "react";
import { api, type DemoSummary } from "../api/aircord";
import { DemoHeader } from "../components/layout/DemoHeader";
import { FailureState, LoadingState } from "../components/layout/DemoState";
import { Hero } from "../components/layout/Hero";
import { AuditTrail } from "../components/proof/AuditTrail";
import { BacktestProof } from "../components/proof/BacktestProof";
import { CaveatRail } from "../components/proof/CaveatRail";
import { DecisionPacket } from "../components/proof/DecisionPacket";
import { McpProof } from "../components/proof/McpProof";
import { ReferenceEvidence } from "../components/proof/ReferenceEvidence";
import { SensorEvidence } from "../components/proof/SensorEvidence";
import { VectorSimilarity } from "../components/proof/VectorSimilarity";
import { Badge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";

export default function App() {
  const [demo, setDemo] = useState<DemoSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .demoSummary()
      .then((summary) => {
        if (active) setDemo(summary);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        const message = reason instanceof Error ? reason.message : String(reason);
        setError(`The live API and static snapshot could not be loaded. ${message}`);
      });
    return () => {
      active = false;
    };
  }, []);

  if (!demo && !error) return <LoadingState />;
  if (error || !demo || demo.status === "empty") {
    return <FailureState message={error ?? demo?.message} />;
  }

  return (
    <main className="mx-auto w-[min(1440px,calc(100%-2rem))] pb-10 sm:w-[min(1440px,calc(100%-3rem))] lg:w-[min(1440px,calc(100%-4rem))]">
      <DemoHeader generatedAt={demo.generated_at} />
      <Hero
        generatedAt={demo.generated_at}
        monitor={demo.airnow_reference.monitor}
        reading={demo.latest_sensor_reading}
        sensor={demo.sensor}
        sensorId={demo.sensor_id}
      />
      <DecisionPacket demo={demo} />

      <section id="evidence" className="scroll-mt-6 pt-16">
        <SectionHeader
          eyebrow="Source evidence"
          title="The inputs remain inspectable."
          description="Community reading and regulatory reference stay attached to the memory decision."
        />
        <div className="grid gap-3 lg:grid-cols-2">
          <SensorEvidence
            reading={demo.latest_sensor_reading}
            sensor={demo.sensor}
            sensorId={demo.sensor_id}
          />
          <ReferenceEvidence
            caveat={demo.reference_caveat}
            reference={demo.airnow_reference}
          />
        </div>

        <article className="mt-3 rounded-card border border-line bg-panel p-5 shadow-card">
          <div className="grid gap-5 lg:grid-cols-[13rem_minmax(0,1fr)]">
            <div>
              <p className="font-mono text-[0.625rem] tracking-[0.12em] text-amber uppercase">
                Resolution reasoning
              </p>
              <Badge tone="amber">Stored explanation</Badge>
            </div>
            <p className="m-0 text-sm leading-7 text-ink-secondary">
              {demo.latest_resolution?.reasoning_text ?? "No resolution reasoning is stored."}
            </p>
          </div>
        </article>
      </section>

      <section id="proof" className="scroll-mt-6 pt-16">
        <SectionHeader
          eyebrow="Persistent proof"
          title="Memory can be inspected four ways."
          description="Database history, behavioral similarity, paired validation, and managed MCP stay visible without hiding caveats."
        />
        <div className="grid gap-3 xl:grid-cols-4">
          <AuditTrail rows={demo.audit_rows} />
          <VectorSimilarity similarity={demo.similarity} />
          <BacktestProof backtest={demo.latest_backtest} caveats={demo.caveats} />
          <McpProof mcp={demo.mcp} />
          <CaveatRail demo={demo} />
        </div>
      </section>

      <footer className="mt-16 flex flex-col gap-4 border-t border-line py-6 text-[0.6875rem] text-muted sm:flex-row sm:items-center sm:justify-between">
        <span className="font-display font-semibold tracking-[-0.04em] text-ink">
          air<span className="text-mint">cord</span>
        </span>
        <span className="font-mono">Persistent trust memory for one metro.</span>
      </footer>
    </main>
  );
}
