from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.eval.datasets import add_case, create_dataset, get_dataset, list_cases, list_datasets
from app.schemas import CaseIn, CaseOut, DatasetIn, DatasetOut

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def create(payload: DatasetIn, db: Session = Depends(get_db)):
    return create_dataset(db, payload.name, payload.description)


@router.get("", response_model=list[DatasetOut])
def list_all(db: Session = Depends(get_db)):
    return list_datasets(db)


@router.post("/{dataset_id}/cases", response_model=CaseOut, status_code=201)
def add(dataset_id: str, payload: CaseIn, db: Session = Depends(get_db)):
    if get_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return add_case(
        db,
        dataset_id,
        input_prompt=payload.input_prompt,
        expected_behavior=payload.expected_behavior,
        checks=payload.checks,
        source_trace_id=payload.source_trace_id,
    )


@router.get("/{dataset_id}/cases", response_model=list[CaseOut])
def cases(dataset_id: str, db: Session = Depends(get_db)):
    return list_cases(db, dataset_id)