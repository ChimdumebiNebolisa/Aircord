import type { DemoSummary } from "../../api/aircord";
import { formatTimestamp, humanize } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { StatusDot } from "../ui/StatusDot";

export function AuditTrail({ rows }: { rows: DemoSummary["audit_rows"] }) {
  const visibleRows = rows.slice(0, 8);

  return (
    <article className="rounded-card border border-line bg-panel p-5 shadow-card xl:col-span-2">
      <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.12em] text-mint uppercase">Audit trail</p>
          <h3 className="mt-2 font-display text-2xl font-semibold tracking-[-0.04em] text-ink">
            The decision left a trace.
          </h3>
        </div>
        <Badge tone={rows.length ? "mint" : "amber"}>{rows.length} persisted rows</Badge>
      </div>

      {visibleRows.length ? (
        <ol className="mt-1">
          {visibleRows.map((row, index) => (
            <li
              className="relative grid gap-2 border-b border-line py-3.5 pl-6 sm:grid-cols-[minmax(0,1fr)_minmax(10rem,0.55fr)] sm:items-center"
              key={row.audit_id ?? `${row.created_at}-${row.action}`}
            >
              <span className="absolute top-[1.35rem] left-0">
                <StatusDot tone={index < 3 ? "mint" : "neutral"} />
              </span>
              {index < visibleRows.length - 1 ? (
                <span aria-hidden="true" className="absolute top-[1.7rem] bottom-[-1.4rem] left-[0.17rem] w-px bg-line" />
              ) : null}
              <div>
                <strong className="block font-mono text-[0.6875rem] font-medium text-ink-secondary capitalize">
                  {humanize(row.action)}
                </strong>
                <span className="mt-1 block text-[0.6875rem] text-muted">
                  {row.actor} / {formatTimestamp(row.created_at)}
                </span>
              </div>
              <span className="font-mono text-[0.625rem] text-faint break-all sm:text-right">
                {row.entity_type}:{row.entity_id}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-5 text-sm text-muted">No audit rows are stored for this decision.</p>
      )}
    </article>
  );
}
