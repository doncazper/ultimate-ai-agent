from fastapi.testclient import TestClient

from tests.test_kernel_minimum_lovable_happy_path import request

from ultimate_ai_agent.api.app import app

client = TestClient(app)


def test_kernel_task_run_endpoint_runs_local_dev_slice(tmp_path):
    response = client.post("/kernel/tasks/run", json=request(tmp_path).model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["success"] is True
    assert body["data"]["rollback_ref"]
    assert (tmp_path / "notes/m5.md").exists()


def test_kernel_task_run_endpoint_redacts_invalid_secret_payload(tmp_path):
    payload = request(tmp_path).model_dump(mode="json")
    payload["new_content"] = "api_key='abcdefghijklmnop'"

    response = client.post("/kernel/tasks/run", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "abcdefghijklmnop" not in response.text
