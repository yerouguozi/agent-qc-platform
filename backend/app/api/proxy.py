from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.gateway.proxy import Gateway, ProxyError, RateLimitError
from app.gateway.registry import get_active_agent, verify_agent_key
from app.schemas import ProxyCallIn, ProxyCallOut

router = APIRouter(prefix="/api/v1", tags=["proxy"])
gateway = Gateway()


@router.post("/proxy/call", response_model=ProxyCallOut)
async def proxy_call(
    payload: ProxyCallIn,
    x_agent_key: str | None = Header(None),
    db: Session = Depends(get_db),
):
    agent = get_active_agent(db, payload.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    if not verify_agent_key(db, payload.agent_id, x_agent_key or ""):
        raise HTTPException(status_code=401, detail="invalid agent key")
    try:
        return await gateway.forward(
            db,
            agent,
            payload.tool_name,
            payload.arguments,
            session_id=payload.session_id,
            source="proxy/api",
        )
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=exc.message, headers={"Retry-After": "1"})
    except ProxyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)