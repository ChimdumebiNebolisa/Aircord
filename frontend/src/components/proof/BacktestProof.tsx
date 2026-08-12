import type { DemoSummary } from "../../api/aircord";
import { formatNumber, humanize, present } from "../../lib/format";
import { Badge } from "../ui/Badge";

export function BacktestProof({
  backtest,
  caveats,
}: {
  backtest: DemoSummary["latest_backtest"];
  caveats: string[];
}) {
  const rows = backtest?.summaries.filter((row) => row.segment === "all") ?? [];
  const maxMae = Math.max(...rows.map((row) => row.mean_absolute_error ?? 0), 1);
  const sampleCount = rows[0]?.observation_count ?? 0;

  return (
    <article className="rounded-card border border-line bg-panel p-5 shadow-card">
      <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.12em] text-mint uppercase">Paired backtest</p>
          <h3 className="mt-2 font-display text-xl font-semibold tracking-[-0.035em] text-ink">
            Measured comparison
          </h3>
        </div>
        <Badge tone={backtest?.status === "passed" ? "mint" : "amber"}>
          {present(backtest?.claim_status, "No run")}
        </Badge>
      </div>

      {backtest ? (
        <>
          <div className="mt-4 flex items-center justify-between gap-3 font-mono text-[0.625rem] text-muted">
            <span className="break-all">{backtest.backtest_run_id}</span>
            <span className="shrink-0 text-ink-secondary">n={sampleCount}</span>
          </div>
          <div className="mt-3 space-y-3">
            {rows.map((row) => (
              <div key={row.method}>
                <div className="mb-1.5 flex items-center justify-between gap-3 font-mono text-[0.625rem] uppercase">
                  <span className="text-muted">{humanize(row.method)}</span>
                  <span className={row.method === "aircord" ? "text-mint" : "text-ink-secondary"}>
                    {formatNumber(row.mean_absolute_error, 2)} MAE
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-canvas">
                  <div
                    className={`h-full ${row.method === "aircord" ? "bg-mint" : "bg-faint"}`}
                    style={{ width: `${Math.max(3, ((row.mean_absolute_error ?? 0) / maxMae) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <p className="mt-4 text-sm text-muted">No backtest run is stored.</p>
      )}

      <div className="mt-5 border-l-2 border-amber bg-amber-dim/50 px-3 py-2.5">
        <strong className="font-mono text-[0.625rem] tracking-[0.08em] text-amber uppercase">
          Read with caveats
        </strong>
        {caveats.slice(0, 3).map((caveat) => (
          <p className="mt-1.5 text-[0.6875rem] leading-5 text-muted" key={caveat}>
            {caveat}
          </p>
        ))}
      </div>
    </article>
  );
}
