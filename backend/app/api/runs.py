from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.eval.datasets import get_dataset
from app.eval.driver import build_driver
from app.eval.regression import compare_runs
from app.eval.runner import execute_run
from app.models import EvalCase, EvalResult, EvalRun
from app.schemas import CaseResultOut, RegressionOut, RunDetailOut, RunIn, RunOut

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.post("", response_model=RunOut, status_code=201)
def create(payload: RunIn, db: Session = Depends(get_db)):
    if get_dataset(db, payload.dataset_id) is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    run = EvalRun(dataset_id=payload.dataset_id, agent_version=payload.agent_version)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/{run_id}/execute", response_model=RunOut)
def execute(run_id: str, db: Session = Depends(get_db)):
    run = db.get(EvalRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    driver = build_driver(db)
    return execute_run(db, run, driver)


@router.get("/{run_id}", response_model=RunDetailOut)
def detail(run_id: str, db: Session = Depends(get_db)):
    run = db.get(EvalRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    results = db.query(EvalResult).filter(EvalResult.run_id == run_id).order_by(EvalResult.id.asc()).all()
    prompts = {}
    for r in results:
        case = db.get(EvalCase, r.case_id)
        prompts[r.case_id] = case.input_prompt if case else ""
    return RunDetailOut(
        **RunOut.model_validate(run).model_dump(),
        results=[
            CaseResultOut(
                case_id=r.case_id,
                input_prompt=prompts.get(r.case_id, ""),
                deterministic_pass=r.deterministic_pass,
                judge_score=r.judge_score,
                judge_reason=r.judge_reason,
                judge_degraded=r.judge_degraded,
                overall_pass=r.overall_pass,
            )
            for r in results
        ],
    )


@router.get("/{run_id}/regression", response_model=RegressionOut)
def regression(run_id: str, baseline: str = Query(...), db: Session = Depends(get_db)):
    if db.get(EvalRun, run_id) is None or db.get(EvalRun, baseline) is None:
        raise HTTPException(status_code=404, detail="run not found")
    return compare_runs(db, baseline, run_id)