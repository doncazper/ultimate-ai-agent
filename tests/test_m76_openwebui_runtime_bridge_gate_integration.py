from pathlib import Path
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m76_openapi_route_failures,
)


def test_m76_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m76_openwebui_runtime_bridge_v1" in ids
    assert "m76_openwebui_runtime_bridge_static_safety" in ids
    assert "m76_openwebui_runtime_bridge_route_boundary" in ids
    assert "m76_roadmap_currentness" in ids


def test_m76_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m76_openwebui_runtime_bridge_v1",
        "m76_openwebui_runtime_bridge_static_safety",
        "m76_openwebui_runtime_bridge_route_boundary",
        "m76_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m76_route_guard_denies_openwebui_runtime_routes() -> None:
    failures = m76_openapi_route_failures(
        {
            "/openwebui/runtime/bridge": {},
            "/openwebui/runtime/handoff": {},
            "/openwebui/runtime/execute": {},
            "/openwebui/chat/send": {},
            "/openwebui/model/call": {},
            "/openwebui/provider/call": {},
            "/openwebui/tools/execute": {},
            "/openwebui/memory/write": {},
            "/openwebui/context/inject": {},
            "/openwebui/raw-payload": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/memory/write": {},
            "/context/inject": {},
        }
    )

    for forbidden in [
        "/openwebui/runtime/bridge",
        "/openwebui/runtime/handoff",
        "/openwebui/runtime/execute",
        "/openwebui/chat/send",
        "/openwebui/model/call",
        "/openwebui/provider/call",
        "/openwebui/tools/execute",
        "/openwebui/memory/write",
        "/openwebui/context/inject",
        "/openwebui/raw-payload",
        "/tools/execute",
        "/tool-runtime/execute",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m76_openapi_route_failures(app.openapi().get("paths", {}))


def test_m76_static_gate_scans_unsafe_openwebui_runtime_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/openwebui_runtime_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("openwebui_runtime_call_performed=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m76_openwebui_runtime_bridge_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("openwebui_runtime_call_performed=True" in failure for failure in result.failures)
