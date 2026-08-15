from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_overview_empty():
    data = client.get("/api/v1/metrics/overview").json()
    assert data["trace_total"] == 0
    assert data["success_rate"] == 0.0


def test_overview_after_traces():
    agent = client.post("/api/v1/agents/register", json={"name": "d", "mcp_url": "http://x"}).json()
    headers = {"X-Agent-Key": agent["api_key"]}
    client.post(
        "/api/v1/traces/ingest?agent_id=" + agent["id"],
        json={"session_id": "s", "tool_name": "t", "arguments": {}, "status": "success", "latency_ms": 10, "cost": 0.01},
        headers=headers,
    )
    client.post(
        "/api/v1/traces/ingest?agent_id=" + agent["id"],
        json={"session_id": "s", "tool_name": "t", "arguments": {}, "status": "failed", "latency_ms": 20},
        headers=headers,
    )
    data = client.get("/api/v1/metrics/overview").json()
    assert data["trace_total"] == 2
    assert data["success_rate"] == 0.5
    assert data["avg_latency_ms"] == 15.0
    assert data["total_cost"] == 0.01