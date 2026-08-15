from sqlalchemy.orm import Session

from app.eval.datasets import add_case, create_dataset
from app.eval.regression import compare_runs
from app.models import EvalResult, EvalRun


def _run(db: Session, ds_id: str, version: str) -> EvalRun:
    run = EvalRun(dataset_id=ds_id, agent_version=version)
    db.add(run)
    db.commit()
    return run


def test_compare_runs_finds_new_failure(db: Session):
    ds = create_dataset(db, name="d")
    c1 = add_case(db, ds.id, input_prompt="p1")
    c2 = add_case(db, ds.id, input_prompt="p2")
    base = _run(db, ds.id, "v1")
    cur = _run(db, ds.id, "v2")
    db.add(EvalResult(run_id=base.id, case_id=c1.id, deterministic_pass=True, overall_pass=True, judge_score=4))
    db.add(EvalResult(run_id=base.id, case_id=c2.id, deterministic_pass=True, overall_pass=True, judge_score=5))
    db.add(EvalResult(run_id=cur.id, case_id=c1.id, deterministic_pass=True, overall_pass=True, judge_score=4))
    db.add(EvalResult(run_id=cur.id, case_id=c2.id, deterministic_pass=False, overall_pass=False, judge_score=2))
    db.commit()
    out = compare_runs(db, base.id, cur.id)
    assert out["pass_rate_baseline"] == 1.0
    assert out["pass_rate_current"] == 0.5
    assert out["new_failures"] == [c2.id]
    assert len(out["rows"]) == 2