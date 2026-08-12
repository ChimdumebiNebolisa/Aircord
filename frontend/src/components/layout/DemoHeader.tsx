import { formatTimestamp } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { StatusDot } from "../ui/StatusDot";

export function DemoHeader({ generatedAt }: { generatedAt?: string }) {
  return (
    <header className="flex min-h-16 flex-wrap items-center gap-4 border-b border-line py-4">
      <a
        className="mr-auto font-display text-xl font-bold tracking-[-0.075em] text-ink no-underline"
        href="#top"
      >
        air<span className="text-mint">cord</span>
      </a>

      <nav
        className="order-3 flex w-full items-center gap-5 font-mono text-[0.625rem] tracking-[0.08em] text-muted uppercase sm:order-none sm:w-auto"
        aria-label="Demo sections"
      >
        <a className="no-underline hover:text-mint" href="#decision">
          Decision
        </a>
        <a className="no-underline hover:text-mint" href="#evidence">
          Evidence
        </a>
        <a className="no-underline hover:text-mint" href="#proof">
          Proof
        </a>
      </nav>

      <div className="flex items-center gap-3">
        <Badge tone="mint">
          <StatusDot tone="mint" label="Snapshot ready" />
        </Badge>
        <span className="hidden font-mono text-[0.625rem] tracking-[0.06em] text-muted uppercase lg:inline">
          {formatTimestamp(generatedAt)}
        </span>
      </div>
    </header>
  );
}
