import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _wait_completed(run_id: str, timeout: float = 20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        detail = client.get(f"/api/v1/runs/{run_id}").json()
        if detail["status"] in ("completed", "failed"):
            return detail
        time.sleep(0.2)
    raise AssertionError("run 未在超时内完成")


def test_create_and_execute_run():
    ds = client.post("/api/v1/datasets", json={"name": "d"}).json()
    client.post(
        f"/api/v1/datasets/{ds['id']}/cases",
        json={"input_prompt": "p", "checks": [{"type": "contains", "value": "mock"}]},
    )
    run = client.post("/api/v1/runs", json={"dataset_id": ds["id"], "agent_version": "v1"}).json()
    assert run["status"] == "running"
    exec_resp = client.post(f"/api/v1/runs/{run['id']}/execute")
    assert exec_resp.status_code == 200
    done = _wait_completed(run["id"])
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
    _wait_completed(base["id"])
    _wait_completed(cur["id"])
    reg = client.get(f"/api/v1/runs/{cur['id']}/regression?baseline={base['id']}").json()
    assert reg["pass_rate_current"] == 1.0
    assert len(reg["rows"]) == 1


def test_run_with_agent_id():
    agent = client.post("/api/v1/agents/register", json={"name": "a2", "mcp_url": "http://x"}).json()
    ds = client.post("/api/v1/datasets", json={"name": "d"}).json()
    client.post(
        f"/api/v1/datasets/{ds['id']}/cases",
        json={"input_prompt": "p", "checks": [{"type": "contains", "value": "mock"}]},
    )
    run = client.post(
        "/api/v1/runs",
        json={"dataset_id": ds["id"], "agent_version": "v1", "agent_id": agent["id"]},
    ).json()
    assert run["agent_id"] == agent["id"]
    client.post(f"/api/v1/runs/{run['id']}/execute")
    done = _wait_completed(run["id"])
    assert done["status"] == "completed"


def test_list_runs():
    ds = client.post("/api/v1/datasets", json={"name": "d"}).json()
    client.post(
        f"/api/v1/datasets/{ds['id']}/cases",
        json={"input_prompt": "p", "checks": [{"type": "contains", "value": "mock"}]},
    )
    run = client.post("/api/v1/runs", json={"dataset_id": ds["id"], "agent_version": "v1"}).json()
    client.post(f"/api/v1/runs/{run['id']}/execute")
    _wait_completed(run["id"])
    listed = client.get("/api/v1/runs").json()
    assert any(r["id"] == run["id"] for r in listed)