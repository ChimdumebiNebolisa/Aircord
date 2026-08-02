from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AirNowClient:
    api_key: str | None = os.getenv("AIRNOW_API_KEY")

    def fetch(self, _bounds: tuple[float, float, float, float]) -> list[dict]:
        if not self.api_key:
            raise RuntimeError("AIRNOW_API_KEY is required for live ingestion; use fixture mode locally")
        raise NotImplementedError("Live AirNow file-product mapping is intentionally scoped for the first adapter")

