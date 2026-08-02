from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SensorReading:
    reading_id: str
    sensor_id: str
    cell_id: str
    observed_at: datetime
    value: float
    channel_a: float
    channel_b: float
    humidity: float
    raw_ref: str | None = None


@dataclass(frozen=True)
class ReputationState:
    sensor_id: str
    reputation_score: float
    features: dict[str, float]
    evidence_window: tuple[str, str]
    version: int


@dataclass(frozen=True)
class SensorDecision:
    sensor_id: str
    reading_id: str
    weight: float
    decision: str
    reason_codes: list[str]
    reputation_score: float


@dataclass(frozen=True)
class CandidateEstimate:
    cell_id: str
    cell_version: int
    estimated_aqi: float
    confidence: float
    claim_status: str
    rationale: str
    confidence_factors: dict[str, Any]
    monitor_context: dict[str, Any]
    decisions: list[SensorDecision]
    reputations: list[ReputationState]

