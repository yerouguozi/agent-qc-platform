from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_list():
    resp = client.post("/api/v1/agents/register", json={"name": "demo", "mcp_url": "http://x/mcp", "rate_limit_qps": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["api_key"].startswith("qc_")
    agent_id = data["id"]
    listed = client.get("/api/v1/agents").json()
    assert any(a["id"] == agent_id for a in listed)


def test_register_missing_field():
    resp = client.post("/api/v1/agents/register", json={"name": "demo"})
    assert resp.status_code == 422