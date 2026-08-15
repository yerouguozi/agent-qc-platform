from sqlalchemy.orm import Session

from app.models import EvalCase, EvalResult


def _prompt(db: Session, case_id: str) -> str:
    case = db.get(EvalCase, case_id)
    return case.input_prompt if case else ""


def _pass_rate(results: dict) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results.values() if r.overall_pass) / len(results)


def _avg_score(results: dict) -> float | None:
    scores = [r.judge_score for r in results.values() if r.judge_score is not None]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def compare_runs(db: Session, baseline_run_id: str, current_run_id: str) -> dict:
    baseline = {r.case_id: r for r in db.query(EvalResult).filter(EvalResult.run_id == baseline_run_id).all()}
    current = {r.case_id: r for r in db.query(EvalResult).filter(EvalResult.run_id == current_run_id).all()}
    case_ids = set(baseline) | set(current)
    rows = []
    new_failures = []
    for case_id in sorted(case_ids):
        b = baseline.get(case_id)
        c = current.get(case_id)
        rows.append(
            {
                "case_id": case_id,
                "input_prompt": _prompt(db, case_id),
                "baseline_pass": b.overall_pass if b else None,
                "current_pass": c.overall_pass if c else None,
                "baseline_score": b.judge_score if b else None,
                "current_score": c.judge_score if c else None,
            }
        )
        if (b is None or b.overall_pass) and c is not None and not c.overall_pass:
            new_failures.append(case_id)
    return {
        "baseline_run_id": baseline_run_id,
        "current_run_id": current_run_id,
        "pass_rate_baseline": round(_pass_rate(baseline), 4),
        "pass_rate_current": round(_pass_rate(current), 4),
        "avg_score_baseline": _avg_score(baseline),
        "avg_score_current": _avg_score(current),
        "new_failures": new_failures,
        "rows": rows,
    }