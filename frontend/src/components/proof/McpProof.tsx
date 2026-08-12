import type { DemoSummary } from "../../api/aircord";
import { present } from "../../lib/format";
import { Badge } from "../ui/Badge";

const repositoryDocs = "https://github.com/ChimdumebiNebolisa/Aircord/blob/main/docs";

export function McpProof({ mcp }: { mcp: DemoSummary["mcp"] }) {
  const connected = mcp.connected_through_codex === true;
  const answer =
    mcp.answer_summary ??
    "No live MCP answer summary is stored in this snapshot.";

  return (
    <article className="rounded-card border border-mint/25 bg-panel-elevated p-5 shadow-card xl:col-span-2">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line pb-4">
        <div>
          <p className="font-mono text-[0.625rem] tracking-[0.12em] text-mint uppercase">Managed MCP</p>
          <h3 className="mt-2 font-display text-2xl font-semibold tracking-[-0.04em] text-ink">
            Ask the memory layer directly.
          </h3>
        </div>
        <Badge tone={connected ? "mint" : "amber"}>
          {connected ? "Connected through Codex" : present(mcp.status)}
        </Badge>
      </div>

      <blockquote className="mt-5 border-l-2 border-mint pl-4">
        <p className="font-display text-lg font-medium tracking-[-0.025em] text-ink">
          “Why was sensor 54917 downweighted?”
        </p>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-ink-secondary">{answer}</p>
      </blockquote>

      <div className="mt-5 grid gap-4 border-t border-line pt-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div className="flex flex-wrap gap-2">
          {mcp.questions.slice(0, 4).map((question) => (
            <span
              className="rounded-control border border-line bg-panel px-2.5 py-1.5 text-[0.6875rem] text-muted"
              key={question}
            >
              {question}
            </span>
          ))}
        </div>
        <div className="flex flex-wrap gap-4 font-mono text-[0.625rem] font-medium tracking-[0.06em] text-mint uppercase">
          <a
            className="underline decoration-line-strong underline-offset-4 hover:text-ink"
            href={`${repositoryDocs}/MCP_DEMO.md`}
            rel="noreferrer"
            target="_blank"
          >
            MCP demo notes ↗
          </a>
          <a
            className="underline decoration-line-strong underline-offset-4 hover:text-ink"
            href={`${repositoryDocs}/cockroachdb_mcp_queries.sql`}
            rel="noreferrer"
            target="_blank"
          >
            Read-only queries ↗
          </a>
        </div>
      </div>
    </article>
  );
}
