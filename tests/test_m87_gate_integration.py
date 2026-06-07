from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m87_openapi_route_failures,
)


def test_m87_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m87_sandboxed_command_audit_replay_contract" in ids
    assert "m87_sandboxed_command_audit_replay_static_safety" in ids
    assert "m87_sandboxed_command_audit_replay_route_boundary" in ids
    assert "m87_roadmap_currentness" in ids


def test_m87_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m87_sandboxed_command_audit_replay_contract",
        "m87_sandboxed_command_audit_replay_static_safety",
        "m87_sandboxed_command_audit_replay_route_boundary",
        "m87_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m87_route_boundary_rejects_shell_replay_and_execution_routes() -> None:
    failures = m87_openapi_route_failures(
        {
            "/api/manifest": {},
            "/shell/replay": {},
            "/shell/replay/run": {},
            "/shell/replay/execute": {},
            "/commands/audit/replay": {},
            "/commands/audit/replay/run": {},
            "/sandbox/commands/replay": {},
            "/sandbox/commands/execute": {},
            "/commands/execute": {},
            "/shell/execute": {},
            "/process/spawn": {},
            "/filesystem/write": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=15,
    )

    for forbidden in [
        "/shell/replay",
        "/shell/replay/run",
        "/shell/replay/execute",
        "/commands/audit/replay",
        "/commands/audit/replay/run",
        "/sandbox/commands/replay",
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
    assert not m87_openapi_route_failures(app.openapi().get("paths", {}))


def test_m87_static_safety_detects_replay_runner_authority(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/sandbox"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("replay_runner_started=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m87_sandboxed_command_audit_replay_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m87_sandboxed_command_audit_replay_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("replay_runner_started=True" in failure for failure in result.failures)
