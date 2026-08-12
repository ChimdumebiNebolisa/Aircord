export function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-5 grid items-end gap-3 border-b border-line pb-4 lg:grid-cols-[minmax(0,1fr)_minmax(16rem,28rem)]">
      <div>
        <p className="font-mono text-[0.625rem] font-medium tracking-[0.14em] text-mint uppercase">
          {eyebrow}
        </p>
        <h2 className="mt-2 font-display text-[clamp(1.65rem,3vw,2.4rem)] leading-none font-semibold tracking-[-0.045em] text-ink">
          {title}
        </h2>
      </div>
      {description ? (
        <p className="m-0 text-sm leading-6 text-muted lg:text-right">{description}</p>
      ) : null}
    </div>
  );
}
