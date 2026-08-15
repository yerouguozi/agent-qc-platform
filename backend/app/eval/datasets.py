import json

from sqlalchemy.orm import Session

from app.models import EvalCase, EvalDataset


def create_dataset(db: Session, name: str, description: str = "") -> EvalDataset:
    ds = EvalDataset(name=name, description=description)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def list_datasets(db: Session) -> list[EvalDataset]:
    return db.query(EvalDataset).order_by(EvalDataset.created_at.desc()).all()


def get_dataset(db: Session, dataset_id: str) -> EvalDataset | None:
    return db.get(EvalDataset, dataset_id)


def add_case(
    db: Session,
    dataset_id: str,
    *,
    input_prompt: str,
    expected_behavior: str = "",
    checks: list[dict] | None = None,
    source_trace_id: str | None = None,
) -> EvalCase:
    case = EvalCase(
        dataset_id=dataset_id,
        input_prompt=input_prompt,
        expected_behavior=expected_behavior,
        checks_json=json.dumps(checks or [], ensure_ascii=False),
        source_trace_id=source_trace_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def list_cases(db: Session, dataset_id: str) -> list[EvalCase]:
    return (
        db.query(EvalCase)
        .filter(EvalCase.dataset_id == dataset_id)
        .order_by(EvalCase.created_at.asc())
        .all()
    )