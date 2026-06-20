from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime import ModelRuntimeHealth
from ultimate_ai_agent.core.runtime_readiness import RuntimeHealthStatus, build_runtime_health_status

client = TestClient(app)


def test_model_runtime_health_validation():
    health = ModelRuntimeHealth(
        status="healthy",
        latency_ms=45.2,
        error_count=0,
        uptime_seconds=3600.0,
        last_checked_at="2026-05-31T12:00:00Z"
    )
    assert health.status == "healthy"
    assert health.latency_ms == 45.2
    assert health.error_count == 0


def test_runtime_health_status_builder_preserves_api_shape():
    health = build_runtime_health_status(version="test-version")

    assert isinstance(health, RuntimeHealthStatus)
    assert health.model_dump(mode="json") == {
        "status": "healthy",
        "version": "test-version",
    }


def test_health_route_preserves_response_shape():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "version"}
    assert body["status"] == "healthy"
    assert isinstance(body["version"], str)
    assert body["version"]
