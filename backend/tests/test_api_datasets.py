from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_dataset_and_case():
    ds = client.post("/api/v1/datasets", json={"name": "电商", "description": "口径"}).json()
    assert ds["name"] == "电商"
    case = client.post(
        f"/api/v1/datasets/{ds['id']}/cases",
        json={
            "input_prompt": "退款率怎么算?",
            "expected_behavior": "给出退款口径",
            "checks": [{"type": "contains", "value": "退款"}],
        },
    ).json()
    assert case["checks"] == [{"type": "contains", "value": "退款"}]
    assert len(client.get(f"/api/v1/datasets/{ds['id']}/cases").json()) == 1


def test_case_on_missing_dataset():
    resp = client.post("/api/v1/datasets/nope/cases", json={"input_prompt": "p"})
    assert resp.status_code == 404