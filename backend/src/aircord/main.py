from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aircord.api import backtests, cells, demo, showcases, sensors
from aircord.config import ALLOWED_ORIGINS, DB_PATH
from aircord.db.connection import database_url_configured
from aircord.db.repositories import Repository
from aircord.db.session import ensure_db
from aircord.fixtures import seed_demo
from aircord.reconciliation.run_once import reconcile_cluster


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if database_url_configured():
        yield
        return
    ensure_db(DB_PATH)
    seed_demo(DB_PATH)
    if not Repository(DB_PATH).one("SELECT 1 FROM estimates LIMIT 1"):
        reconcile_cluster(DB_PATH)
    yield


app = FastAPI(title="Aircord MVP API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(cells.router)
app.include_router(showcases.router)
app.include_router(backtests.router)
app.include_router(sensors.router)
app.include_router(demo.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "cockroach" if database_url_configured() else "fixture"}
