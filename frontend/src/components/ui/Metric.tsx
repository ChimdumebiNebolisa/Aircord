import type { ReactNode } from "react";

type MetricTone = "default" | "mint" | "amber" | "danger";

const valueClasses: Record<MetricTone, string> = {
  default: "text-ink",
  mint: "text-mint",
  amber: "text-amber",
  danger: "text-danger",
};

export function Metric({
  label,
  value,
  unit,
  supporting,
  tone = "default",
  compact = false,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  supporting?: ReactNode;
  tone?: MetricTone;
  compact?: boolean;
}) {
  return (
    <div className="min-w-0">
      <p className="font-mono text-[0.625rem] font-medium tracking-[0.12em] text-muted uppercase">
        {label}
      </p>
      <div className="mt-2 flex min-w-0 items-baseline gap-2">
        <strong
          className={`${compact ? "text-3xl" : "text-[clamp(2.5rem,5vw,4.5rem)]"} font-display leading-none font-semibold tracking-[-0.065em] ${valueClasses[tone]}`}
        >
          {value}
        </strong>
        {unit ? (
          <span className="font-mono text-[0.625rem] tracking-[0.08em] text-muted uppercase">
            {unit}
          </span>
        ) : null}
      </div>
      {supporting ? (
        <div className="mt-2 text-xs leading-5 text-muted">{supporting}</div>
      ) : null}
    </div>
  );
}
