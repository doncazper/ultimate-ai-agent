from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m108_openapi_route_failures,
)


def test_m108_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m108_mobile_kill_switch_revocation_contracts" in ids
    assert "m108_mobile_kill_switch_revocation_static_safety" in ids
    assert "m108_mobile_kill_switch_revocation_route_boundary" in ids
    assert "m108_roadmap_currentness" in ids


def test_m108_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m108_mobile_kill_switch_revocation_contracts",
        "m108_mobile_kill_switch_revocation_static_safety",
        "m108_mobile_kill_switch_revocation_route_boundary",
        "m108_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m108_route_boundary_rejects_runtime_revocation_routes() -> None:
    failures = m108_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/kill-switch": {},
            "/mobile/kill-switch/activate": {},
            "/mobile/kill-switch/execute": {},
            "/mobile/revocation": {},
            "/mobile/revocation/execute": {},
            "/mobile/approvals/revoke": {},
            "/mobile/approvals/kill-switch": {},
            "/mobile/session/stop": {},
            "/mobile/notifications/push": {},
            "/mobile/background/workers": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/mobile/kill-switch",
        "/mobile/kill-switch/activate",
        "/mobile/kill-switch/execute",
        "/mobile/revocation",
        "/mobile/revocation/execute",
        "/mobile/approvals/revoke",
        "/mobile/approvals/kill-switch",
        "/mobile/session/stop",
        "/mobile/notifications/push",
        "/mobile/background/workers",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m108_openapi_route_failures(app.openapi().get("paths", {}))


def test_m108_static_safety_detects_runtime_revocation_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "revocation_execution_enabled=True\n"
        "kill_switch_execution_enabled=True\n"
        "approval_revocation_enabled=True\n"
        "session_stop_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m108_mobile_kill_switch_revocation_static_safety"
    )
    result = (
        FoundationGateEvaluator(tmp_path)
        .check_m108_mobile_kill_switch_revocation_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("revocation_execution_enabled=True" in failure for failure in result.failures)
    assert any("kill_switch_execution_enabled=True" in failure for failure in result.failures)
    assert any("approval_revocation_enabled=True" in failure for failure in result.failures)
    assert any("session_stop_enabled=True" in failure for failure in result.failures)
