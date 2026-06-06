from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m69_openapi_route_failures,
)


def test_m69_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m69_low_risk_autonomous_dry_run_contract_review" in ids
    assert "m69_low_risk_autonomous_dry_run_static_safety" in ids
    assert "m69_low_risk_autonomous_dry_run_route_boundary" in ids
    assert "m69_roadmap_currentness" in ids


def test_m69_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m69_low_risk_autonomous_dry_run_contract_review",
        "m69_low_risk_autonomous_dry_run_static_safety",
        "m69_low_risk_autonomous_dry_run_route_boundary",
        "m69_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m69_openapi_route_guard_denies_dry_run_execution_routes() -> None:
    failures = m69_openapi_route_failures(
        {
            "/autonomy/dry-run/start": {},
            "/autonomy/dry-run/execute": {},
            "/autonomy/dry-run/activate": {},
            "/autonomy/session/start": {},
            "/autonomy/policy/activate": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/browser/click": {},
            "/plugins/execute": {},
        }
    )

    for forbidden in [
        "/autonomy/dry-run/start",
        "/autonomy/dry-run/execute",
        "/autonomy/dry-run/activate",
        "/autonomy/session/start",
        "/autonomy/policy/activate",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/shell/execute",
        "/browser/click",
        "/plugins/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m69_openapi_route_failures(app.openapi().get("paths", {}))


def test_m69_static_gate_scans_dry_run_authority_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/dry_run_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("low_risk_dry_run_authority_granted=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m69_low_risk_autonomous_dry_run_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("low_risk_dry_run_authority_granted=True" in failure for failure in result.failures)
