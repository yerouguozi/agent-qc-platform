import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.eval.checks import CaseOutput, run_checks
from app.eval.driver import AgentDriver
from app.eval.judge import JudgeError, judge_answer
from app.models import EvalCase, EvalResult, EvalRun


def execute_run(db: Session, run: EvalRun, driver: AgentDriver) -> EvalRun:
    cases = (
        db.query(EvalCase)
        .filter(EvalCase.dataset_id == run.dataset_id)
        .order_by(EvalCase.created_at.asc())
        .all()
    )
    for case in cases:
        existing = (
            db.query(EvalResult)
            .filter(EvalResult.run_id == run.id, EvalResult.case_id == case.id)
            .first()
        )
        if existing is not None:
            continue
        checks = json.loads(case.checks_json or "[]")
        try:
            output = driver.run(case.input_prompt, run.id)
        except Exception as exc:
            db.add(
                EvalResult(
                    run_id=run.id,
                    case_id=case.id,
                    deterministic_pass=False,
                    judge_reason=f"执行异常:{exc}",
                    overall_pass=False,
                )
            )
            db.commit()
            continue
        deterministic_pass, _details = run_checks(checks, CaseOutput(output.answer, output.tool_calls))
        judge_score = None
        judge_reason = None
        judge_degraded = False
        if any(c.get("type") == "judge" for c in checks):
            try:
                judge = judge_answer(
                    case.input_prompt,
                    output.answer,
                    case.expected_behavior,
                    context="\n".join(output.trace_summaries),
                )
                judge_score = judge["score"]
                judge_reason = judge["reason"]
            except JudgeError:
                judge_degraded = True
        overall = deterministic_pass and (judge_score is None or judge_score >= 4)
        db.add(
            EvalResult(
                run_id=run.id,
                case_id=case.id,
                trace_id=output.trace_id,
                deterministic_pass=deterministic_pass,
                judge_score=judge_score,
                judge_reason=judge_reason,
                judge_degraded=judge_degraded,
                overall_pass=overall,
            )
        )
        db.commit()
        done = db.query(EvalResult).filter(EvalResult.run_id == run.id).count()
        run.summary_json = json.dumps({"cases": len(cases), "done": done}, ensure_ascii=False)
        db.commit()
    run.status = "completed"
    run.finished_at = datetime.utcnow()
    run.summary_json = json.dumps({"cases": len(cases)}, ensure_ascii=False)
    db.commit()
    db.refresh(run)
    return run