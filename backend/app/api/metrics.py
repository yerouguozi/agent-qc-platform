from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import EvalResult, EvalRun, Trace
from app.schemas import MetricsOverview, TrendPoint

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/overview", response_model=MetricsOverview)
def overview(db: Session = Depends(get_db)):
    traces = db.query(Trace).all()
    total = len(traces)
    success = sum(1 for t in traces if t.status == "success")
    avg_latency = round(sum(t.latency_ms for t in traces) / total, 1) if total else 0.0
    total_cost = round(sum(t.cost for t in traces), 4)
    last_run = (
        db.query(EvalRun)
        .filter(EvalRun.status == "completed")
        .order_by(EvalRun.started_at.desc())
        .first()
    )
    last_pass = None
    if last_run is not None:
        results = db.query(EvalResult).filter(EvalResult.run_id == last_run.id).all()
        if results:
            last_pass = round(sum(1 for r in results if r.overall_pass) / len(results), 4)
    return MetricsOverview(
        trace_total=total,
        success_rate=round(success / total, 4) if total else 0.0,
        avg_latency_ms=avg_latency,
        total_cost=total_cost,
        last_run_pass_rate=last_pass,
    )


@router.get("/trend", response_model=list[TrendPoint])
def trend(days: int = 7, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    runs = (
        db.query(EvalRun)
        .filter(EvalRun.status == "completed", EvalRun.started_at >= since)
        .order_by(EvalRun.started_at.asc())
        .all()
    )
    points = []
    for run in runs:
        results = db.query(EvalResult).filter(EvalResult.run_id == run.id).all()
        if not results:
            continue
        pass_rate = round(sum(1 for r in results if r.overall_pass) / len(results), 4)
        scores = [r.judge_score for r in results if r.judge_score is not None]
        avg_score = round(sum(scores) / len(scores), 4) if scores else None
        points.append(TrendPoint(day=run.started_at.date().isoformat(), pass_rate=pass_rate, avg_score=avg_score))
    return points