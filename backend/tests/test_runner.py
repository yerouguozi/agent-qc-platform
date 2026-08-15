from sqlalchemy.orm import Session

from app.eval.datasets import add_case, create_dataset
from app.eval.driver import MockDriver
from app.eval.runner import execute_run
from app.models import EvalResult, EvalRun


def test_execute_run_passes_and_fails(db: Session):
    ds = create_dataset(db, name="d")
    add_case(db, ds.id, input_prompt="p1", checks=[{"type": "contains", "value": "正确"}])
    add_case(db, ds.id, input_prompt="p2", checks=[{"type": "contains", "value": "错误"}])
    run = EvalRun(dataset_id=ds.id, agent_version="v1")
    db.add(run)
    db.commit()
    driver = MockDriver(answer="这是正确结论", tool_calls=["t"])
    execute_run(db, run, driver)
    results = db.query(EvalResult).filter(EvalResult.run_id == run.id).all()
    assert len(results) == 2
    assert results[0].overall_pass is True
    assert results[1].overall_pass is False
    assert db.get(EvalRun, run.id).status == "completed"


def test_execute_run_resume_skips_done(db: Session):
    ds = create_dataset(db, name="d")
    case = add_case(db, ds.id, input_prompt="p1", checks=[{"type": "contains", "value": "正确"}])
    run = EvalRun(dataset_id=ds.id, agent_version="v1")
    db.add(run)
    db.commit()
    db.add(EvalResult(run_id=run.id, case_id=case.id, deterministic_pass=True, overall_pass=True))
    db.commit()
    calls = []

    class CountingDriver(MockDriver):
        def run(self, prompt, run_id):
            calls.append(prompt)
            return super().run(prompt, run_id)

    execute_run(db, run, CountingDriver(answer="这是正确结论"))
    assert calls == []


def test_judge_check_scored(db: Session, monkeypatch):
    ds = create_dataset(db, name="d")
    add_case(db, ds.id, input_prompt="p1", expected_behavior="be", checks=[{"type": "judge"}])
    run = EvalRun(dataset_id=ds.id, agent_version="v1")
    db.add(run)
    db.commit()
    monkeypatch.setattr(
        "app.eval.runner.judge_answer",
        lambda q, a, e: {"score": 5, "reason": "good", "issues": []},
    )
    execute_run(db, run, MockDriver(answer="回答", tool_calls=[]))
    result = db.query(EvalResult).filter(EvalResult.run_id == run.id).first()
    assert result.judge_score == 5
    assert result.overall_pass is True