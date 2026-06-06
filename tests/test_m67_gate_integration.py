from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m67_openapi_route_failures,
)


def test_m67_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m67_revocation_kill_switch_contract_review" in ids
    assert "m67_revocation_kill_switch_static_safety" in ids
    assert "m67_revocation_kill_switch_route_boundary" in ids
    assert "m67_roadmap_currentness" in ids


def test_m67_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m67_revocation_kill_switch_contract_review",
        "m67_revocation_kill_switch_static_safety",
        "m67_revocation_kill_switch_route_boundary",
        "m67_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m67_openapi_route_guard_denies_revocation_and_kill_switch_execution_routes() -> None:
    failures = m67_openapi_route_failures(
        {
            "/autonomy/revoke": {},
            "/autonomy/revocation/execute": {},
            "/autonomy/kill-switch": {},
            "/autonomy/kill-switch/activate": {},
            "/autonomy/session/stop": {},
            "/autonomy/session/terminate": {},
            "/process/kill": {},
            "/autonomy/execute": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/background/start": {},
        }
    )

    for forbidden in [
        "/autonomy/revoke",
        "/autonomy/revocation/execute",
        "/autonomy/kill-switch",
        "/autonomy/kill-switch/activate",
        "/autonomy/session/stop",
        "/autonomy/session/terminate",
        "/process/kill",
        "/autonomy/execute",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/shell/execute",
        "/browser/click",
        "/plugins/execute",
        "/background/start",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m67_openapi_route_failures(app.openapi().get("paths", {}))


def test_m67_static_gate_scans_kill_switch_activation_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/revocation_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("kill_switch_activated=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m67_revocation_kill_switch_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("kill_switch_activated=True" in failure for failure in result.failures)

