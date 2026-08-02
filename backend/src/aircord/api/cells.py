from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException

from aircord.api.dependencies import get_repository
from aircord.api.schemas import CellDetail, CellSummary, Cluster, EstimateSummary, Point, Resolution, ResolutionSensor
from aircord.config import MEDICAL_DIRECTIVE_CAVEAT, MODE, REFERENCE_CAVEAT
from aircord.db.repositories import Repository


router = APIRouter(tags=["cluster"])


@router.get("/clusters/active", response_model=Cluster)
def get_active_cluster(repository: Repository = Depends(get_repository)) -> Cluster:
    row = repository.active_cluster()
    if not row:
        raise HTTPException(404, "No active cluster")
    return Cluster(cluster_id=row["cluster_id"], name=row["name"], gate_a_status=row["gate_a_status"], gate_a_notes=row["gate_a_notes"], mode=MODE)


@router.get("/clusters/active/cells", response_model=list[CellSummary])
def list_cells(repository: Repository = Depends(get_repository)) -> list[CellSummary]:
    result = []
    for row in repository.cells():
        estimate = None
        if row.get("estimated_aqi") is not None:
            estimate = EstimateSummary(
                estimated_aqi=row["estimated_aqi"], confidence=row["confidence"],
                claim_status=row["claim_status"], updated_at=row["estimate_updated_at"],
            )
        result.append(CellSummary(cell_id=row["cell_id"], centroid=Point(latitude=row["centroid_lat"], longitude=row["centroid_lon"]), latest_estimate=estimate))
    return result


@router.get("/cells/{cell_id}", response_model=CellDetail)
def get_cell_detail(cell_id: str, repository: Repository = Depends(get_repository)) -> CellDetail:
    cell = repository.cell(cell_id)
    if not cell:
        raise HTTPException(404, "Cell not found")
    estimate_row = repository.latest_estimate(cell_id)
    resolution_row = repository.latest_resolution(cell_id)
    estimate = None
    if estimate_row:
        estimate = EstimateSummary(
            estimated_aqi=estimate_row["estimated_aqi"], confidence=estimate_row["confidence"],
            claim_status=estimate_row["claim_status"], updated_at=estimate_row["updated_at"],
        )
    resolution = None
    if resolution_row:
        sensors = []
        for row in repository.resolution_sensors(resolution_row["resolution_id"]):
            sensors.append(ResolutionSensor(
                sensor_id=row["sensor_id"], weight=row["weight"], decision=row["decision"],
                reason_codes=json.loads(row["reason_codes_json"]), reputation_score_at_commit=row["reputation_score_at_commit"],
            ))
        resolution = Resolution(
            rationale_text=resolution_row["rationale_text"],
            confidence_factors=json.loads(resolution_row["confidence_factors_json"]),
            sensors=sensors,
        )
    return CellDetail(
        cell_id=cell_id, estimate=estimate, resolution=resolution,
        reference_caveat=REFERENCE_CAVEAT, medical_directive_caveat=MEDICAL_DIRECTIVE_CAVEAT,
    )
