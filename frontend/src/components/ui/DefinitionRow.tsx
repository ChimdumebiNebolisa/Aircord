import type { ReactNode } from "react";

export function DefinitionRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="grid gap-1 border-t border-line py-3 sm:grid-cols-[8.5rem_minmax(0,1fr)] sm:gap-5">
      <dt className="font-mono text-[0.625rem] font-medium tracking-[0.1em] text-muted uppercase">
        {label}
      </dt>
      <dd
        className={`m-0 min-w-0 text-left text-xs leading-5 text-ink-secondary sm:text-right ${mono ? "font-mono break-all" : ""}`}
      >
        {value}
      </dd>
    </div>
  );
}
