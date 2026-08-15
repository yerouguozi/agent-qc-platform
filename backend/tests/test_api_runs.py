from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_execute_run():
    ds = client.post("/api/v1/datasets", json={"name": "d"}).json()
    client.post(
        f"/api/v1/datasets/{ds['id']}/cases",
        json={"input_prompt": "p", "checks": [{"type": "contains", "value": "mock"}]},
    )
    run = client.post("/api/v1/runs", json={"dataset_id": ds["id"], "agent_version": "v1"}).json()
    assert run["status"] == "running"
    done = client.post(f"/api/v1/runs/{run['id']}/execute").json()
    assert done["status"] == "completed"
    detail = client.get(f"/api/v1/runs/{run['id']}").json()
    assert len(detail["results"]) == 1
    assert detail["results"][0]["overall_pass"] is True


def test_regression_api():
    ds = client.post("/api/v1/datasets", json={"name": "d"}).json()
    client.post(
        f"/api/v1/datasets/{ds['id']}/cases",
        json={"input_prompt": "p", "checks": [{"type": "contains", "value": "mock"}]},
    )
    base = client.post("/api/v1/runs", json={"dataset_id": ds["id"], "agent_version": "v1"}).json()
    cur = client.post("/api/v1/runs", json={"dataset_id": ds["id"], "agent_version": "v2"}).json()
    client.post(f"/api/v1/runs/{base['id']}/execute")
    client.post(f"/api/v1/runs/{cur['id']}/execute")
    reg = client.get(f"/api/v1/runs/{cur['id']}/regression?baseline={base['id']}").json()
    assert reg["pass_rate_current"] == 1.0
    assert len(reg["rows"]) == 1