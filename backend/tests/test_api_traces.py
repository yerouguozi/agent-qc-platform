from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_and_list():
    agent = client.post("/api/v1/agents/register", json={"name": "demo", "mcp_url": "http://x/mcp"}).json()
    headers = {"X-Agent-Key": agent["api_key"]}
    resp = client.post(
        "/api/v1/traces/ingest?agent_id=" + agent["id"],
        json={
            "session_id": "s9",
            "tool_name": "query_sql",
            "arguments": {"sql": "select 13812345678"},
            "result_summary": "ok",
            "status": "success",
            "latency_ms": 5,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    trace_id = resp.json()["trace_id"]
    assert "13812345678" not in resp.json()["params_masked_json"]
    detail = client.get(f"/api/v1/traces/{trace_id}")
    assert detail.status_code == 200
    listed = client.get("/api/v1/traces?session_id=s9").json()
    assert len(listed) == 1


def test_ingest_requires_valid_key():
    agent = client.post("/api/v1/agents/register", json={"name": "demo", "mcp_url": "http://x/mcp"}).json()
    resp = client.post(
        "/api/v1/traces/ingest?agent_id=" + agent["id"],
        json={"session_id": "s1", "tool_name": "t", "arguments": {}},
        headers={"X-Agent-Key": "bad"},
    )
    assert resp.status_code == 401