from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.gateway.registry import verify_agent_key
from app.schemas import TraceIngestIn, TraceOut
from app.trace.store import create_trace, get_trace, list_traces

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])


@router.get("", response_model=list[TraceOut])
def list_traces_api(
    agent_id: str | None = None,
    session_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return list_traces(db, agent_id=agent_id, session_id=session_id, status=status, limit=limit, offset=offset)


@router.get("/{trace_id}", response_model=TraceOut)
def get_trace_api(trace_id: str, db: Session = Depends(get_db)):
    trace = get_trace(db, trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace


@router.post("/ingest", response_model=TraceOut, status_code=201)
def ingest(
    payload: TraceIngestIn,
    agent_id: str = Query(...),
    x_agent_key: str | None = Header(None),
    db: Session = Depends(get_db),
):
    if not verify_agent_key(db, agent_id, x_agent_key or ""):
        raise HTTPException(status_code=401, detail="invalid agent key")
    return create_trace(
        db,
        agent_id=agent_id,
        session_id=payload.session_id,
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        result_summary=payload.result_summary,
        status=payload.status,
        latency_ms=payload.latency_ms,
        token_usage=payload.token_usage,
        cost=payload.cost,
        error_code=payload.error_code,
        error_message=payload.error_message,
    )