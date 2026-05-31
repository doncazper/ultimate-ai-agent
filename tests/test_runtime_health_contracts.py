from ultimate_ai_agent.core.runtime import ModelRuntimeHealth

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
