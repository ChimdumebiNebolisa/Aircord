import type { DemoSummary } from "../../api/aircord";
import { formatNumber, present } from "../../lib/format";
import { Badge } from "../ui/Badge";

export function VectorSimilarity({ similarity }: { similarity: DemoSummary["similarity"] }) {
  const maxDistance = Math.max(...similarity.nearest.map((row) => row.cosine_distance), 1);

  return (
    <article className="rounded-card border border-line bg-panel p-5 shadow-card">
      <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.12em] text-info uppercase">Vector memory</p>
          <h3 className="mt-2 font-display text-xl font-semibold tracking-[-0.035em] text-ink">
            Behavioral neighbors
          </h3>
        </div>
        <Badge tone="info">VECTOR({similarity.fingerprint_dimensions})</Badge>
      </div>

      {similarity.nearest.length ? (
        <div className="mt-2">
          {similarity.nearest.map((row) => (
            <div className="border-b border-line py-3.5" key={row.sensor_id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <strong className="block font-mono text-[0.6875rem] font-medium text-ink-secondary">
                    {row.sensor_id}
                  </strong>
                  <span className="mt-1 block text-[0.6875rem] text-muted">
                    {present(row.label)} / {present(row.source)}
                  </span>
                </div>
                <span className="font-mono text-[0.6875rem] text-mint">
                  {formatNumber(row.cosine_distance, 5)}
                </span>
              </div>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-canvas">
                <div
                  className="h-full bg-info"
                  style={{ width: `${Math.max(3, (row.cosine_distance / maxDistance) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted">No similar sensor fingerprints are stored.</p>
      )}

      <p className="mt-4 text-[0.6875rem] leading-5 text-muted">{similarity.message}</p>
    </article>
  );
}
