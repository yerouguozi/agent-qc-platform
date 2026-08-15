from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register():
    return client.post("/api/v1/agents/register", json={"name": "demo", "mcp_url": "http://x/mcp"}).json()


def test_proxy_call_requires_key():
    agent = _register()
    resp = client.post(
        "/api/v1/proxy/call",
        json={"agent_id": agent["id"], "tool_name": "query_sql", "arguments": {"sql": "select 1"}, "session_id": "s1"},
    )
    assert resp.status_code == 401


def test_proxy_call_bad_agent_key():
    agent = _register()
    resp = client.post(
        "/api/v1/proxy/call",
        json={"agent_id": agent["id"], "tool_name": "query_sql", "arguments": {}, "session_id": "s1"},
        headers={"X-Agent-Key": "wrong"},
    )
    assert resp.status_code == 401