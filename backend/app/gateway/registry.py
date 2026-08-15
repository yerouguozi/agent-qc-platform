from sqlalchemy.orm import Session

from app.gateway.auth import verify_key
from app.models import Agent, Tool


def register_agent(
    db: Session,
    *,
    name: str,
    mcp_url: str,
    api_key_hash: str,
    rate_limit_qps: int = 5,
) -> Agent:
    agent = Agent(name=name, mcp_url=mcp_url, api_key_hash=api_key_hash, rate_limit_qps=rate_limit_qps)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def get_active_agent(db: Session, agent_id: str) -> Agent | None:
    agent = db.get(Agent, agent_id)
    if agent is None or agent.status != "active":
        return None
    return agent


def verify_agent_key(db: Session, agent_id: str, api_key: str) -> bool:
    agent = db.get(Agent, agent_id)
    if agent is None:
        return False
    return verify_key(api_key, agent.api_key_hash)


def replace_tools(db: Session, agent_id: str, tools: list[Tool]) -> None:
    old = db.query(Tool).filter(Tool.agent_id == agent_id).all()
    for tool in old:
        db.delete(tool)
    db.add_all(tools)
    db.commit()