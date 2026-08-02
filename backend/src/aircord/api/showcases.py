from fastapi import APIRouter, Depends, HTTPException

from aircord.api.dependencies import get_repository
from aircord.api.schemas import DegradedSensorShowcase
from aircord.db.repositories import Repository
from aircord.reputation.showcase import degraded_showcase


router = APIRouter(tags=["showcase"])


@router.get("/showcases/degraded-sensor", response_model=DegradedSensorShowcase)
def get_degraded_sensor_showcase(repository: Repository = Depends(get_repository)) -> DegradedSensorShowcase:
    result = degraded_showcase(repository.path)
    if not result:
        raise HTTPException(404, "No degraded-sensor showcase available")
    return DegradedSensorShowcase(**{key: result[key] for key in DegradedSensorShowcase.model_fields})

