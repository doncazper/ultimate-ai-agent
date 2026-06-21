from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M17_OPENAPI_PATH_COUNT,
    M17_FORBIDDEN_BACKEND_ROUTES,
    m17_openapi_route_failures,
)


def test_m17_evidence_file_memory_viewer_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m17_evidence_file_memory_viewer_safe" in criteria_by_id
    assert "summary-only refs" in criteria_by_id["m17_evidence_file_memory_viewer_safe"].pass_condition
    assert "memory as recall and not authority" in criteria_by_id["m17_evidence_file_memory_viewer_safe"].pass_condition
    assert "raw file" in criteria_by_id["m17_evidence_file_memory_viewer_safe"].pass_condition

    report = FoundationGateEvaluator().evaluate([criteria_by_id["m17_evidence_file_memory_viewer_safe"]])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m17_evidence_file_memory_viewer_hardening_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m17_evidence_file_memory_viewer_hardening_safe" in criteria_by_id
    criterion = criteria_by_id["m17_evidence_file_memory_viewer_hardening_safe"]
    assert "alternate mock refs" in criterion.pass_condition
    assert "selected-card state" in criterion.pass_condition
    assert "OpenAPI path count at 78" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m17_openapi_route_guard_rejects_backend_knowledge_viewer_expansion() -> None:
    failures = m17_openapi_route_failures(
        {
            "/health",
            "/files/write",
            "/memory/raw",
        },
        expected_path_count=EXPECTED_M17_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M17_OPENAPI_PATH_COUNT == 78
    assert "/files/write" in M17_FORBIDDEN_BACKEND_ROUTES
    assert "/memory/raw" in M17_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/files/write" in failure for failure in failures)
    assert any("/memory/raw" in failure for failure in failures)
