export function formatNumber(
  value: number | null | undefined,
  digits = 1,
  fallback = "Not stored",
) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return fallback;
  }
  return Number(value).toFixed(digits);
}

export function formatPercent(
  value: number | null | undefined,
  digits = 1,
  fallback = "Not stored",
) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return fallback;
  }
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

export function formatTimestamp(value: string | null | undefined) {
  if (!value) return "Not stored";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export function present(value: string | null | undefined, fallback = "Not stored") {
  return value || fallback;
}

export function humanize(value: string) {
  return value.replaceAll("_", " ");
}

export function confidenceLabel(value: number | null | undefined) {
  if (value === null || value === undefined) return "Not stored";
  if (value >= 0.8) return "High";
  if (value >= 0.6) return "Medium";
  return "Low";
}
