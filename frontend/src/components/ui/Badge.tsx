import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "mint" | "amber" | "danger" | "info";

const toneClasses: Record<BadgeTone, string> = {
  neutral: "border-line text-ink-secondary bg-panel-strong",
  mint: "border-mint/30 text-mint bg-mint-dim",
  amber: "border-amber/35 text-amber bg-amber-dim",
  danger: "border-danger/35 text-danger bg-danger-dim",
  info: "border-info/30 text-info bg-info-dim",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: BadgeTone;
}) {
  return (
    <span
      className={`inline-flex min-h-6 items-center rounded-full border px-2.5 py-1 font-mono text-[0.625rem] leading-none font-medium tracking-[0.08em] uppercase ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}
