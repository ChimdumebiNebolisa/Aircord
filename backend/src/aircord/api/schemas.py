from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Point(BaseModel):
    latitude: float
    longitude: float


class Cluster(BaseModel):
    cluster_id: str
    name: str
    gate_a_status: Literal["candidate", "passed", "failed"]
    gate_a_notes: str
    mode: str = "fixture"


class EstimateSummary(BaseModel):
    estimated_aqi: float
    confidence: float = Field(ge=0, le=1)
    claim_status: Literal["pending_backtest", "measured", "insufficient_data"]
    updated_at: datetime


class CellSummary(BaseModel):
    cell_id: str
    centroid: Point
    latest_estimate: EstimateSummary | None


class ResolutionSensor(BaseModel):
    sensor_id: str
    weight: float
    decision: Literal["trusted", "downweighted", "ignored"]
    reason_codes: list[str]
    reputation_score_at_commit: float


class Resolution(BaseModel):
    rationale_text: str
    confidence_factors: dict[str, Any]
    sensors: list[ResolutionSensor]


class CellDetail(BaseModel):
    cell_id: str
    estimate: EstimateSummary | None
    resolution: Resolution | None
    reference_caveat: str
    medical_directive_caveat: str


class SensorReputation(BaseModel):
    sensor_id: str
    reputation_score: float
    features: dict[str, float]
    evidence_window: dict[str, str]
    affected_estimates: list[str]


class DegradedSensorShowcase(BaseModel):
    sensor_id: str
    cell_id: str
    raw_or_static_estimate: float
    aircord_estimate: float
    reputation_reason: str


class BacktestRequest(BaseModel):
    window_start: datetime
    window_end: datetime


class BacktestSummary(BaseModel):
    segment: Literal["all", "healthy", "degraded"]
    method: Literal["raw_purpleair", "static_correction", "aircord"]
    observation_count: int
    mean_absolute_error: float
    median_absolute_error: float


class BacktestResult(BaseModel):
    backtest_run_id: str
    status: Literal["pending", "passed", "failed", "insufficient_data"]
    claim_status: Literal["pending", "measured", "no_claim"]
    failure_reason: str | None = None
    summaries: list[BacktestSummary]
