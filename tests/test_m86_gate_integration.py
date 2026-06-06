from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m86_openapi_route_failures,
)


def test_m86_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m86_shell_approval_gate_contract" in ids
    assert "m86_shell_approval_gate_static_safety" in ids
    assert "m86_shell_approval_gate_route_boundary" in ids
    assert "m86_roadmap_currentness" in ids


def test_m86_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m86_shell_approval_gate_contract",
        "m86_shell_approval_gate_static_safety",
        "m86_shell_approval_gate_route_boundary",
        "m86_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m86_route_boundary_rejects_shell_approval_and_execution_routes() -> None:
    failures = m86_openapi_route_failures(
        {
            "/api/manifest": {},
            "/shell/approval": {},
            "/shell/approval/review": {},
            "/shell/approval/execute": {},
            "/commands/allowlist/execute": {},
            "/sandbox/commands/execute": {},
            "/commands/execute": {},
            "/shell/execute": {},
            "/process/spawn": {},
            "/filesystem/write": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/shell/approval",
        "/shell/approval/review",
        "/shell/approval/execute",
        "/commands/allowlist/execute",
        "/sandbox/commands/execute",
        "/commands/execute",
        "/shell/execute",
        "/process/spawn",
        "/filesystem/write",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m86_openapi_route_failures(app.openapi().get("paths", {}))


def test_m86_static_safety_detects_shell_execution_authority(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/sandbox"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("shell_execution_authorized=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m86_shell_approval_gate_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m86_shell_approval_gate_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("shell_execution_authorized=True" in failure for failure in result.failures)
