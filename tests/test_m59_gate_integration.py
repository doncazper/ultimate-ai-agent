from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m59_openapi_route_failures,
)


def test_m59_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m59_public_github_readiness_review" in ids
    assert "m59_public_github_readiness_static_safety" in ids
    assert "m59_public_github_readiness_route_boundary" in ids
    assert "m59_roadmap_currentness" in ids


def test_m59_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m59_public_github_readiness_review",
        "m59_public_github_readiness_static_safety",
        "m59_public_github_readiness_route_boundary",
        "m59_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m59_openapi_route_guard_denies_publication_routes() -> None:
    failures = m59_openapi_route_failures(
        {
            "/github/publish": {},
            "/github/release": {},
            "/github/wiki/update": {},
            "/public/artifacts/upload": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        }
    )

    assert any("/github/publish" in failure for failure in failures)
    assert any("/github/release" in failure for failure in failures)
    assert any("/github/wiki/update" in failure for failure in failures)
    assert any("/public/artifacts/upload" in failure for failure in failures)
    assert any("/context/inject" in failure for failure in failures)
    assert not m59_openapi_route_failures(app.openapi().get("paths", {}))
