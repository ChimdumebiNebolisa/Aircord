import { Badge } from "../ui/Badge";

export function LoadingState() {
  return (
    <main className="grid min-h-screen place-content-center gap-4 px-6 text-center">
      <span className="font-display text-xl font-bold tracking-[-0.075em] text-ink">
        air<span className="text-mint">cord</span>
      </span>
      <Badge tone="info">Loading persisted evidence</Badge>
      <h1 className="font-display text-4xl font-semibold tracking-[-0.055em] text-ink">
        Opening the memory layer.
      </h1>
      <p className="text-sm text-muted">Reading the latest CockroachDB-backed snapshot.</p>
    </main>
  );
}

export function FailureState({ message }: { message?: string }) {
  return (
    <main className="grid min-h-screen place-content-center gap-4 px-6 text-center">
      <span className="font-display text-xl font-bold tracking-[-0.075em] text-ink">
        air<span className="text-mint">cord</span>
      </span>
      <div className="mx-auto">
        <Badge tone="danger">Snapshot load failed</Badge>
      </div>
      <h1 className="font-display text-[clamp(2.25rem,6vw,4rem)] font-semibold tracking-[-0.06em] text-ink">
        Persisted evidence could not be opened.
      </h1>
      <p className="mx-auto max-w-xl text-sm leading-6 text-muted">
        {message ?? "The snapshot contains no persisted Aircord memory."}
      </p>
      <code className="mx-auto max-w-full rounded-control border border-line bg-panel px-4 py-3 font-mono text-[0.6875rem] text-ink-secondary break-all">
        python backend/scripts/demo_status.py --write-frontend-snapshot
      </code>
    </main>
  );
}
