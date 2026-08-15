from sqlalchemy.orm import Session

from app.trace.store import create_trace, get_trace, list_traces, traces_by_session


def test_create_and_get(db: Session, sample_agent):
    trace = create_trace(
        db, agent_id=sample_agent.id, session_id="s1", tool_name="query_sql",
        arguments={"sql": "select 13812345678"}, result_summary="ok", status="success", latency_ms=12,
    )
    assert get_trace(db, trace.trace_id).trace_id == trace.trace_id
    assert "13812345678" not in trace.params_masked_json


def test_list_filters(db: Session, sample_agent):
    create_trace(db, agent_id=sample_agent.id, session_id="s1", tool_name="a", status="success")
    create_trace(db, agent_id=sample_agent.id, session_id="s2", tool_name="b", status="failed")
    assert len(list_traces(db, session_id="s1")) == 1
    assert len(list_traces(db, status="failed")) == 1
    assert len(list_traces(db, limit=1)) == 1


def test_by_session_order(db: Session, sample_agent):
    t1 = create_trace(db, agent_id=sample_agent.id, session_id="s1", tool_name="a", status="success")
    t2 = create_trace(db, agent_id=sample_agent.id, session_id="s1", tool_name="b", status="success")
    assert [t.tool_name for t in traces_by_session(db, "s1")] == ["a", "b"]
    assert t1.id < t2.id