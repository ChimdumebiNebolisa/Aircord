import type { DemoSummary } from "../../api/aircord";

export function CaveatRail({ demo }: { demo: DemoSummary }) {
  const caveats = Array.from(
    new Set([
      demo.reference_caveat,
      ...demo.caveats.slice(0, 2),
      demo.medical_directive_caveat,
    ]),
  ).filter(Boolean);

  return (
    <aside className="rounded-card border border-line bg-panel p-5 xl:col-span-2">
      <p className="font-mono text-[0.625rem] tracking-[0.12em] text-amber uppercase">
        Interpretation boundaries
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {caveats.map((caveat) => (
          <p
            className="m-0 border-l border-amber/60 pl-3 text-[0.6875rem] leading-5 text-muted"
            key={caveat}
          >
            {caveat}
          </p>
        ))}
      </div>
    </aside>
  );
}
