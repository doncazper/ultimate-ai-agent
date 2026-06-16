from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m138_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m138_autonomous_error_handling_guardrails_contracts" in ids
    assert "m138_autonomous_error_handling_guardrails_static_safety" in ids
    assert "m138_autonomous_error_handling_guardrails_route_boundary" in ids
    assert "m138_roadmap_currentness" in ids


def test_m138_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m138_autonomous_error_handling_guardrails_contracts",
        "m138_autonomous_error_handling_guardrails_static_safety",
        "m138_autonomous_error_handling_guardrails_route_boundary",
        "m138_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m138_route_boundary_rejects_error_handling_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/autonomy/error-handling-guardrails": {},
        "/autonomy/error-handling-guardrails/start": {},
        "/autonomy/error-handling-guardrails/run": {},
        "/error-handling/run": {},
        "/error-handling/execute": {},
        "/error-guardrails/run": {},
        "/error-guardrails/execute": {},
        "/recovery/retry": {},
        "/recovery/rollback": {},
        "/recovery/resume": {},
        "/recovery/execute": {},
        "/fallback/execute": {},
        "/escalation/execute": {},
        "/loop-recovery/run": {},
    }
    failures = gate_evaluators.m138_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/autonomy/error-handling-guardrails",
        "/autonomy/error-handling-guardrails/start",
        "/error-handling/run",
        "/error-guardrails/run",
        "/recovery/retry",
        "/recovery/rollback",
        "/recovery/resume",
        "/fallback/execute",
        "/escalation/execute",
        "/loop-recovery/run",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m138_openapi_route_failures(app.openapi().get("paths", {}))


def test_m138_static_safety_detects_error_handling_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "error_handling_runtime_enabled=True\n"
        "error_guardrail_runtime_enabled=True\n"
        "autonomous_recovery_execution_enabled=True\n"
        "retry_execution_enabled=True\n"
        "rollback_execution_enabled=True\n"
        "fallback_action_enabled=True\n"
        "escalation_action_enabled=True\n"
        "loop_recovery_enabled=True\n"
        "dependency_execution_enabled=True\n"
        "browser_action_enabled=True\n"
        "connector_action_enabled=True\n"
        "tool_execution_enabled=True\n"
        "execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "network_access_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "error_handling_runtime_authorized=True\n"
        "error_guardrail_runtime_started=True\n"
        "autonomous_recovery_execution_authorized=True\n"
        "retry_execution_performed=True\n"
        "rollback_execution_performed=True\n"
        "resume_execution_performed=True\n"
        "dependency_execution_performed=True\n"
        "browser_action_performed=True\n"
        "connector_action_performed=True\n"
        "tool_execution_performed=True\n"
        "/autonomy/error-handling-guardrails/start\n"
        "/error-handling/run\n"
        "/error-guardrails/run\n"
        "/recovery/retry\n"
        "/recovery/rollback\n"
        "/recovery/resume\n"
        "/fallback/execute\n"
        "/escalation/execute\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m138_autonomous_error_handling_guardrails_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m138_autonomous_error_handling_guardrails_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "error_handling_runtime_enabled=True",
        "error_guardrail_runtime_enabled=True",
        "autonomous_recovery_execution_enabled=True",
        "retry_execution_enabled=True",
        "rollback_execution_enabled=True",
        "fallback_action_enabled=True",
        "loop_recovery_enabled=True",
        "dependency_execution_enabled=True",
        "browser_action_enabled=True",
        "connector_action_enabled=True",
        "tool_execution_enabled=True",
        "backend_route_enabled=True",
        "production_authority_granted=True",
        "error_handling_runtime_authorized=True",
        "error_guardrail_runtime_started=True",
        "retry_execution_performed=True",
        "rollback_execution_performed=True",
        "resume_execution_performed=True",
        "/autonomy/error-handling-guardrails/start",
        "/error-handling/run",
        "/error-guardrails/run",
        "/recovery/retry",
        "/recovery/rollback",
        "/recovery/resume",
        "/fallback/execute",
        "/escalation/execute",
    ]:
        assert any(fragment in failure for failure in result.failures)
