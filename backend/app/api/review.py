from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.eval.datasets import add_case, get_dataset
from app.models import ReviewItem
from app.schemas import ReviewDecideIn, ReviewItemIn, ReviewItemOut
from app.trace.store import get_trace

router = APIRouter(prefix="/api/v1/review-queue", tags=["review"])


@router.get("", response_model=list[ReviewItemOut])
def queue(status: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(ReviewItem)
    if status:
        query = query.filter(ReviewItem.status == status)
    return query.order_by(ReviewItem.id.desc()).limit(limit).all()


@router.post("/items", response_model=ReviewItemOut, status_code=201)
def enqueue(payload: ReviewItemIn, db: Session = Depends(get_db)):
    if get_trace(db, payload.trace_id) is None:
        raise HTTPException(status_code=404, detail="trace not found")
    existing = db.query(ReviewItem).filter(ReviewItem.trace_id == payload.trace_id).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="trace already in review queue")
    item = ReviewItem(trace_id=payload.trace_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/decide", response_model=ReviewItemOut)
def decide(item_id: int, payload: ReviewDecideIn, db: Session = Depends(get_db)):
    item = db.get(ReviewItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="review item not found")
    if payload.status not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="status must be approved/rejected")
    item.status = payload.status
    item.reviewer_note = payload.note
    item.decided_at = datetime.utcnow()
    db.commit()
    if payload.status == "rejected" and payload.promote_to_dataset_id and payload.input_prompt:
        if get_dataset(db, payload.promote_to_dataset_id) is None:
            raise HTTPException(status_code=404, detail="dataset not found")
        trace = get_trace(db, item.trace_id)
        add_case(
            db,
            payload.promote_to_dataset_id,
            input_prompt=payload.input_prompt,
            expected_behavior="应返回正确结果",
            checks=[{"type": "not_tool_called", "tool": trace.tool_name if trace else "unknown"}],
            source_trace_id=item.trace_id,
        )
    db.refresh(item)
    return item