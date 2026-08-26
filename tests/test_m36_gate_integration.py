from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator


def test_m36_foundation_gate_criteria_are_registered() -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}

    assert "m36_ccc_file_review_surface_safe" in criterion_ids
    assert "m36_file_review_openapi_routes_unchanged" in criterion_ids
    assert "m36_m37_m38_remain_future" in criterion_ids


def test_m36_openapi_route_guard_rejects_review_mutation_context_and_execution_routes() -> (
    None
):
    from ultimate_ai_agent.core.gate.evaluators import (
        EXPECTED_M36_OPENAPI_PATH_COUNT,
        m36_openapi_route_failures,
    )

    failures = m36_openapi_route_failures(
        {
            "/files/read/raw": {},
            "/files/review/approve": {},
            "/files/review/submit": {},
            "/files/review/approvals/capture": {},
            "/context/propose": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tool-runtime/execute": {},
        }
    )

    assert any("/files/read/raw" in failure for failure in failures)
    assert any("/files/review/approve" in failure for failure in failures)
    assert any("/files/review/submit" in failure for failure in failures)
    assert any("/files/review/approvals/capture" in failure for failure in failures)
    assert any("/context/propose" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert any("/memory/write" in failure for failure in failures)
    assert any("/tool-runtime/execute" in failure for failure in failures)
    assert any("OpenAPI path count" in failure for failure in failures)
    assert EXPECTED_M36_OPENAPI_PATH_COUNT == 80
    assert m36_openapi_route_failures(app.openapi().get("paths", {})) == []


def test_m36_surface_guard_rejects_unsafe_refs_and_mutating_requests() -> None:
    from ultimate_ai_agent.core.gate.evaluators import m36_file_review_surface_failures

    failures = m36_file_review_surface_failures(
        component_text='fetch("/files/review/approve", { method: "POST" });',
        mock_text='safePathRef: "/Users/local/private.txt"',
    )

    assert any("mutating M36 file review request" in failure for failure in failures)
    assert any("unsafe M36 safe_path_ref" in failure for failure in failures)
    assert any(
        "private path fragment in M36 file review fixture" in failure
        for failure in failures
    )


def test_m36_foundation_gate_evaluator_passes_current_surface() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = [
        criterion
        for criterion in default_foundation_gate_criteria()
        if criterion.criterion_id.startswith("m36_")
    ]

    report = evaluator.evaluate(criteria)

    for result in report.results:
        assert result.status == FoundationGateStatus.passed
