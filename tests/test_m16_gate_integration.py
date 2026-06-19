from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M16_OPENAPI_PATH_COUNT,
    M16_FORBIDDEN_BACKEND_ROUTES,
    m16_openapi_route_failures,
)


def test_m16_event_timeline_trace_viewer_criterion_exists_and_passes():
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m16_event_timeline_trace_viewer_safe" in criteria_by_id
    assert "redacted timeline" in criteria_by_id["m16_event_timeline_trace_viewer_safe"].pass_condition
    assert "raw payloads" in criteria_by_id["m16_event_timeline_trace_viewer_safe"].pass_condition

    report = FoundationGateEvaluator().evaluate([criteria_by_id["m16_event_timeline_trace_viewer_safe"]])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m16_openapi_route_guard_rejects_backend_timeline_expansion():
    failures = m16_openapi_route_failures(
        {
            "/health",
            "/events/timeline",
            "/trace/export",
        },
        expected_path_count=EXPECTED_M16_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M16_OPENAPI_PATH_COUNT == 75
    assert "/events/timeline" in M16_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/events/timeline" in failure for failure in failures)
    assert any("/trace/export" in failure for failure in failures)
