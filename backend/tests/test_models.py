from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.db import engine
from app.models import Agent, Trace, new_id


def test_tables_created(db: Session):
    tables = set(inspect(engine).get_table_names())
    expected = {
        "agents", "tools", "api_keys", "traces", "sessions",
        "eval_datasets", "eval_cases", "eval_runs", "eval_results",
        "audit_logs", "review_queue",
    }
    assert expected.issubset(tables)


def test_new_id_unique():
    assert len(new_id()) == 32
    assert new_id() != new_id()


def test_trace_defaults(db: Session):
    agent = Agent(name="a", mcp_url="http://x", api_key_hash="h")
    db.add(agent)
    db.commit()
    trace = Trace(agent_id=agent.id, tool_name="t", status="success")
    db.add(trace)
    db.commit()
    assert trace.params_masked_json == "{}"
    assert trace.latency_ms == 0
    assert trace.cost == 0.0