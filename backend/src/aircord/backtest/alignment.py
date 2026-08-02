from __future__ import annotations

from collections import defaultdict
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

