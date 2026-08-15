import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.gateway.masking import mask_arguments
from app.models import Trace, new_id


def create_trace(
    db: Session,
    *,
    agent_id: str,
    session_id: str,
    tool_name: str,
    arguments: dict | None = None,
    result_summary: str = "",
    status: str = "success",
    latency_ms: int = 0,
    token_usage: int = 0,
    cost: float = 0.0,
    error_code: str | None = None,
    error_message: str | None = None,
) -> Trace:
    trace = Trace(
        trace_id=new_id(),
        session_id=session_id,
        agent_id=agent_id,
        tool_name=tool_name,
        params_masked_json=json.dumps(mask_arguments(arguments or {}), ensure_ascii=False),
        result_summary=(result_summary or "")[: settings.trace_result_max_chars],
        status=status,
        latency_ms=latency_ms,
        token_usage=token_usage,
        cost=cost,
        error_code=error_code,
        error_message=error_message,
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)
    return trace


def list_traces(
    db: Session,
    *,
    agent_id: str | None = None,
    session_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Trace]:
    query = db.query(Trace)
    if agent_id:
        query = query.filter(Trace.agent_id == agent_id)
    if session_id:
        query = query.filter(Trace.session_id == session_id)
    if status:
        query = query.filter(Trace.status == status)
    return query.order_by(Trace.id.desc()).offset(offset).limit(limit).all()


def get_trace(db: Session, trace_id: str) -> Trace | None:
    return db.query(Trace).filter(Trace.trace_id == trace_id).first()


def traces_by_session(db: Session, session_id: str) -> list[Trace]:
    return db.query(Trace).filter(Trace.session_id == session_id).order_by(Trace.id.asc()).all()