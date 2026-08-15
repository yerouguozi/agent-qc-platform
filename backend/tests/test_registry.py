from sqlalchemy.orm import Session

from app.gateway.auth import hash_key
from app.gateway.registry import (
    get_active_agent,
    register_agent,
    replace_tools,
    verify_agent_key,
)
from app.models import Tool


def test_register_and_verify(db: Session):
    agent = register_agent(db, name="demo", mcp_url="http://x/mcp", api_key_hash=hash_key("secret"), rate_limit_qps=3)
    assert get_active_agent(db, agent.id).id == agent.id
    assert verify_agent_key(db, agent.id, "secret")
    assert not verify_agent_key(db, agent.id, "wrong")
    assert not verify_agent_key(db, "missing", "secret")


def test_replace_tools(db: Session, sample_agent):
    replace_tools(db, sample_agent.id, [Tool(agent_id=sample_agent.id, name="t1", description="d")])
    replace_tools(db, sample_agent.id, [Tool(agent_id=sample_agent.id, name="t2", description="d")])
    rows = db.query(Tool).filter(Tool.agent_id == sample_agent.id).all()
    assert [r.name for r in rows] == ["t2"]