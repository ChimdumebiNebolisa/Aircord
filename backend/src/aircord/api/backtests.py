from fastapi import APIRouter, Depends, Response, status

from aircord.api.dependencies import get_repository
from aircord.api.schemas import BacktestRequest, BacktestResult, BacktestSummary
from aircord.db.repositories import Repository
from aircord.backtest.run import run_backtest


router = APIRouter(tags=["backtest"])


def _result(repository: Repository, run: dict) -> BacktestResult:
    return BacktestResult(
        backtest_run_id=run["backtest_run_id"], status=run["status"], claim_status=run["claim_status"],
        failure_reason=run.get("failure_reason"), summaries=[BacktestSummary(**summary) for summary in run.get("summaries", [])],
    )


@router.get("/backtests/latest", response_model=BacktestResult)
def latest_backtest(repository: Repository = Depends(get_repository)) -> BacktestResult:
    row = repository.latest_backtest()
    if not row:
        return BacktestResult(backtest_run_id="none", status="pending", claim_status="pending", summaries=[])
    return _result(repository, {**row, "summaries": repository.backtest_summaries(row["backtest_run_id"]), "failure_reason": row["failure_reason"]})


@router.post("/backtests", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
def create_backtest(request: BacktestRequest, response: Response, repository: Repository = Depends(get_repository)) -> dict:
    cluster = repository.active_cluster()
    run = run_backtest(repository.path, cluster["cluster_id"] if cluster else "greater-la")
    response.status_code = status.HTTP_202_ACCEPTED
    return {"backtest_run_id": run["backtest_run_id"], "status": "pending"}

