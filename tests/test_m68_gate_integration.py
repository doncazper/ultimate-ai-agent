from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m68_openapi_route_failures,
)


def test_m68_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m68_autonomy_risk_classifier_contract_review" in ids
    assert "m68_autonomy_risk_classifier_static_safety" in ids
    assert "m68_autonomy_risk_classifier_route_boundary" in ids
    assert "m68_roadmap_currentness" in ids


def test_m68_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m68_autonomy_risk_classifier_contract_review",
        "m68_autonomy_risk_classifier_static_safety",
        "m68_autonomy_risk_classifier_route_boundary",
        "m68_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m68_openapi_route_guard_denies_classifier_execution_routes() -> None:
    failures = m68_openapi_route_failures(
        {
            "/autonomy/risk/classify": {},
            "/autonomy/risk/execute": {},
            "/autonomy/risk/activate": {},
            "/autonomy/session/start": {},
            "/autonomy/policy/activate": {},
            "/autonomy/revoke": {},
            "/autonomy/kill-switch/activate": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/browser/click": {},
            "/plugins/execute": {},
        }
    )

    for forbidden in [
        "/autonomy/risk/classify",
        "/autonomy/risk/execute",
        "/autonomy/risk/activate",
        "/autonomy/session/start",
        "/autonomy/policy/activate",
        "/autonomy/revoke",
        "/autonomy/kill-switch/activate",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/shell/execute",
        "/browser/click",
        "/plugins/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m68_openapi_route_failures(app.openapi().get("paths", {}))


def test_m68_static_gate_scans_risk_classifier_authority_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/risk_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("risk_authority_granted=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m68_autonomy_risk_classifier_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("risk_authority_granted=True" in failure for failure in result.failures)
