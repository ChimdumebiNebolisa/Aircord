from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PurpleAirClient:
    api_key: str | None = os.getenv("PURPLEAIR_API_KEY")

    def fetch(self, _bounds: tuple[float, float, float, float]) -> list[dict]:
        if not self.api_key:
            raise RuntimeError("PURPLEAIR_API_KEY is required for live ingestion; use fixture mode locally")
        raise NotImplementedError("Live PurpleAir polling is intentionally scoped for the first adapter")

