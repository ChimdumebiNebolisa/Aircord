from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


def align_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["cell_id"], row["observed_at"])].append(row)
    return [
        {"cell_id": cell_id, "observed_at": observed_at, "rows": values, "reference_aqi": values[0]["reference_aqi"]}
        for (cell_id, observed_at), values in sorted(grouped.items())
        if values and values[0].get("reference_aqi") is not None
    ]


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def align_sensor_monitor_rows(
    sensor_rows: list[dict[str, Any]],
    monitor_rows: list[dict[str, Any]],
    *,
    max_gap_minutes: float = 180.0,
) -> list[dict[str, Any]]:
    """Pair each sensor reading with the nearest monitor observation.

    Rows without parseable timestamps, a numeric reference, or a monitor
    within the configured gap are excluded rather than assigned a zero.
    Duplicate sensor timestamps are de-duplicated for reproducible samples.
    """
    monitors = []
    for row in monitor_rows:
        observed_at = _parse_time(row.get("observed_at"))
        try:
            reference = None if row.get("latest_aqi") in (None, "") else float(row["latest_aqi"])
        except (TypeError, ValueError):
            reference = None
        if observed_at is not None and reference is not None:
            monitors.append((observed_at, row, reference))

    aligned = []
    seen: set[tuple[str, datetime]] = set()
    max_gap_seconds = max_gap_minutes * 60.0
    for row in sorted(sensor_rows, key=lambda item: str(item.get("observed_at", ""))):
        observed_at = _parse_time(row.get("observed_at"))
        sensor_id = str(row.get("sensor_id", ""))
        if observed_at is None or not sensor_id or (sensor_id, observed_at) in seen or not monitors:
            continue
        nearest = min(monitors, key=lambda item: abs((observed_at - item[0]).total_seconds()))
        gap_seconds = abs((observed_at - nearest[0]).total_seconds())
        if gap_seconds > max_gap_seconds:
            continue
        seen.add((sensor_id, observed_at))
        aligned.append(
            {
                "sensor_id": sensor_id,
                "reading_id": row.get("reading_id"),
                "observed_at": observed_at,
                "sensor": row,
                "monitor": nearest[1],
                "reference_aqi": nearest[2],
                "time_gap_minutes": round(gap_seconds / 60.0, 2),
            }
        )
    return aligned

