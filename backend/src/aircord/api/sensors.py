from fastapi import APIRouter, Depends, HTTPException

from aircord.api.dependencies import get_repository
from aircord.api.schemas import SensorReputation
from aircord.db.repositories import Repository


router = APIRouter(tags=["sensor"])


@router.get("/sensors/{sensor_id}/reputation", response_model=SensorReputation)
def get_sensor_reputation(sensor_id: str, repository: Repository = Depends(get_repository)) -> SensorReputation:
    row = repository.sensor_reputation(sensor_id)
    if not row or row.get("reputation_score") is None:
        raise HTTPException(404, "Sensor reputation not found")
    return SensorReputation(
        sensor_id=sensor_id, reputation_score=row["reputation_score"], features=row["features"],
        evidence_window={"start": row["evidence_start"], "end": row["evidence_end"]},
        affected_estimates=repository.affected_estimates(sensor_id),
    )

