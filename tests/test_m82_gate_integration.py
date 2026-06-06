from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m82_openapi_route_failures,
)


def test_m82_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m82_command_proposal_contract" in ids
    assert "m82_command_proposal_static_safety" in ids
    assert "m82_command_proposal_route_boundary" in ids
    assert "m82_roadmap_currentness" in ids


def test_m82_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m82_command_proposal_contract",
        "m82_command_proposal_static_safety",
        "m82_command_proposal_route_boundary",
        "m82_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m82_openapi_route_guard_denies_command_execution_routes() -> None:
    failures = m82_openapi_route_failures(
        {
            "/commands/propose": {},
            "/commands/execute": {},
            "/shell/execute": {},
            "/process/spawn": {},
            "/filesystem/write": {},
            "/network/fetch/unrestricted": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/remote/execute": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        }
    )

    for forbidden in [
        "/commands/propose",
        "/commands/execute",
        "/shell/execute",
        "/process/spawn",
        "/filesystem/write",
        "/network/fetch/unrestricted",
        "/browser/click",
        "/plugins/execute",
        "/remote/execute",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m82_openapi_route_failures(app.openapi().get("paths", {}))


def test_m82_static_gate_scans_command_execution_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/m82_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("command_execution_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m82_command_proposal_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("command_execution_enabled=True" in failure for failure in result.failures)
