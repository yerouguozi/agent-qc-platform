import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.gateway.auth import generate_api_key, hash_key
from app.gateway.proxy import StreamableHttpMCPClient
from app.gateway.ratelimit import RateLimiter
from app.gateway.registry import get_active_agent, register_agent, replace_tools
from app.models import Agent, Tool
from app.schemas import AgentOut, AgentRegisterIn, AgentRegisterOut, ToolOut

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
_limiter = RateLimiter()


@router.post("/register", response_model=AgentRegisterOut)
def register(payload: AgentRegisterIn, db: Session = Depends(get_db)):
    api_key = generate_api_key()
    agent = register_agent(
        db,
        name=payload.name,
        mcp_url=payload.mcp_url,
        api_key_hash=hash_key(api_key),
        rate_limit_qps=payload.rate_limit_qps,
    )
    _limiter.set_limit(agent.id, agent.rate_limit_qps)
    out = AgentOut.model_validate(agent).model_dump()
    return AgentRegisterOut(**out, api_key=api_key)


@router.get("", response_model=list[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).order_by(Agent.created_at.desc()).all()


@router.post("/{agent_id}/tools/sync", response_model=list[ToolOut])
def sync_tools(agent_id: str, db: Session = Depends(get_db)):
    agent = get_active_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    client = StreamableHttpMCPClient(agent.mcp_url)
    tools = asyncio.run(client.list_tools())
    rows = [
        Tool(
            agent_id=agent_id,
            name=t["name"],
            description=t["description"],
            input_schema_json=json.dumps(t["input_schema"], ensure_ascii=False),
        )
        for t in tools
    ]
    replace_tools(db, agent_id, rows)
    return db.query(Tool).filter(Tool.agent_id == agent_id).order_by(Tool.name.asc()).all()