import type { BadgeTone } from "./Badge";

const dotClasses: Record<BadgeTone, string> = {
  neutral: "bg-muted",
  mint: "bg-mint shadow-[0_0_0_4px_rgba(120,230,192,0.10)]",
  amber: "bg-amber shadow-[0_0_0_4px_rgba(224,184,103,0.10)]",
  danger: "bg-danger shadow-[0_0_0_4px_rgba(238,141,117,0.10)]",
  info: "bg-info shadow-[0_0_0_4px_rgba(133,184,255,0.10)]",
};

export function StatusDot({
  tone = "neutral",
  label,
}: {
  tone?: BadgeTone;
  label?: string;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <span aria-hidden="true" className={`size-1.5 rounded-full ${dotClasses[tone]}`} />
      {label ? <span>{label}</span> : null}
    </span>
  );
}
