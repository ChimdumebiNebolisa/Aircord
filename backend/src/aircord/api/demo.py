from __future__ import annotations

from fastapi import APIRouter, Depends

from aircord.api.dependencies import get_repository
from aircord.demo import (
    DEFAULT_SENSOR_ID,
    build_demo_summary,
    section_response,
)
from aircord.db.repositories import Repository


router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/sensors/{sensor_id}/latest")
def latest_sensor(sensor_id: str, repository: Repository = Depends(get_repository)) -> dict:
    summary = build_demo_summary(repository, sensor_id)
    return {
        "status": summary["status"] if summary["latest_sensor_reading"] else "empty",
        "sensor_id": sensor_id,
        "sensor": summary["sensor"],
        "reading": summary["latest_sensor_reading"],
        "airnow_reference": summary["airnow_reference"],
        "message": summary["message"] if summary["latest_sensor_reading"] else "No latest sensor reading is stored.",
    }


@router.get("/sensors/{sensor_id}/memory")
def sensor_memory(sensor_id: str, repository: Repository = Depends(get_repository)) -> dict:
    summary = build_demo_summary(repository, sensor_id)
    return {
        "status": "ok" if summary["sensor_reputation"] or summary["latest_cell_estimate"] else "empty",
        "sensor_id": sensor_id,
        "reputation": summary["sensor_reputation"],
        "estimate": summary["latest_cell_estimate"],
        "resolution": summary["latest_resolution"],
        "message": "Reputation and estimate memory loaded." if summary["sensor_reputation"] or summary["latest_cell_estimate"] else "No reputation or estimate memory is stored.",
    }


@router.get("/sensors/{sensor_id}/resolution")
def sensor_resolution(sensor_id: str, repository: Repository = Depends(get_repository)) -> dict:
    summary = build_demo_summary(repository, sensor_id)
    return section_response(summary, "latest_resolution", sensor_id)


@router.get("/sensors/{sensor_id}/audit")
def sensor_audit(sensor_id: str, repository: Repository = Depends(get_repository)) -> dict:
    summary = build_demo_summary(repository, sensor_id)
    return section_response(summary, "audit_rows", sensor_id)


@router.get("/sensors/{sensor_id}/similar")
def similar_sensors(sensor_id: str, repository: Repository = Depends(get_repository)) -> dict:
    summary = build_demo_summary(repository, sensor_id)
    return {
        "sensor_id": sensor_id,
        **summary["similarity"],
    }


@router.get("/backtests/latest")
def latest_backtest(repository: Repository = Depends(get_repository)) -> dict:
    summary = build_demo_summary(repository, DEFAULT_SENSOR_ID)
    return section_response(summary, "latest_backtest", DEFAULT_SENSOR_ID)


@router.get("/demo-summary")
def demo_summary(repository: Repository = Depends(get_repository)) -> dict:
    return build_demo_summary(repository, DEFAULT_SENSOR_ID)
