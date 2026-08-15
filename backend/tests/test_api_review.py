from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _seed_trace() -> str:
    agent = client.post("/api/v1/agents/register", json={"name": "d", "mcp_url": "http://x"}).json()
    resp = client.post(
        "/api/v1/traces/ingest?agent_id=" + agent["id"],
        json={"session_id": "s", "tool_name": "query_sql", "arguments": {"sql": "select 1"}, "status": "success"},
        headers={"X-Agent-Key": agent["api_key"]},
    )
    return resp.json()["trace_id"]


def test_enqueue_and_decide():
    trace_id = _seed_trace()
    enqueue = client.post("/api/v1/review-queue/items", json={"trace_id": trace_id})
    assert enqueue.status_code == 201
    item = enqueue.json()
    assert item["status"] == "pending"
    decided = client.post(
        f"/api/v1/review-queue/{item['id']}/decide",
        json={"status": "approved", "note": "ok"},
    )
    assert decided.json()["status"] == "approved"


def test_reject_promotes_case():
    trace_id = _seed_trace()
    ds = client.post("/api/v1/datasets", json={"name": "沉淀"}).json()
    item = client.post("/api/v1/review-queue/items", json={"trace_id": trace_id}).json()
    client.post(
        f"/api/v1/review-queue/{item['id']}/decide",
        json={
            "status": "rejected",
            "note": "bad",
            "promote_to_dataset_id": ds["id"],
            "input_prompt": "复现问题",
        },
    )
    cases = client.get(f"/api/v1/datasets/{ds['id']}/cases").json()
    assert len(cases) == 1
    assert cases[0]["source_trace_id"] == trace_id


def test_duplicate_enqueue_conflict():
    trace_id = _seed_trace()
    client.post("/api/v1/review-queue/items", json={"trace_id": trace_id})
    assert client.post("/api/v1/review-queue/items", json={"trace_id": trace_id}).status_code == 409