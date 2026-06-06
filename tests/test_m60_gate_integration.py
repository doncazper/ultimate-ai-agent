from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m60_openapi_route_failures,
)


def test_m60_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m60_local_developer_beta_freeze_review" in ids
    assert "m60_local_developer_beta_freeze_static_safety" in ids
    assert "m60_local_developer_beta_freeze_route_boundary" in ids
    assert "m60_final_roadmap_currentness" in ids


def test_m60_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m60_local_developer_beta_freeze_review",
        "m60_local_developer_beta_freeze_static_safety",
        "m60_local_developer_beta_freeze_route_boundary",
        "m60_final_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m60_openapi_route_guard_denies_public_and_autonomy_routes() -> None:
    failures = m60_openapi_route_failures(
        {
            "/public/beta/release": {},
            "/github/release": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/shell/execute": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/remote/execute": {},
        }
    )

    for forbidden in [
        "/public/beta/release",
        "/github/release",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/tool-runtime/execute",
        "/shell/execute",
        "/browser/click",
        "/plugins/execute",
        "/remote/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m60_openapi_route_failures(app.openapi().get("paths", {}))
