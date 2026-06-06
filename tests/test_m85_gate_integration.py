from pathlib import Path

from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m85_openapi_route_failures,
)


def test_m85_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m85_read_only_command_allowlist_contract" in ids
    assert "m85_read_only_command_allowlist_static_safety" in ids
    assert "m85_read_only_command_allowlist_route_boundary" in ids
    assert "m85_roadmap_currentness" in ids


def test_m85_route_boundary_rejects_command_allowlist_and_execution_routes() -> None:
    failures = m85_openapi_route_failures(
        {
            "/api/manifest": {},
            "/commands/allowlist": {},
            "/commands/allowlist/execute": {},
            "/shell/execute": {},
            "/process/spawn": {},
            "/filesystem/write": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=9,
    )

    for forbidden in [
        "/commands/allowlist",
        "/commands/allowlist/execute",
        "/shell/execute",
        "/process/spawn",
        "/filesystem/write",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)


def test_m85_static_safety_detects_execution_enablement(tmp_path: Path) -> None:
    root = tmp_path
    src_dir = root / "src/ultimate_ai_agent/core/sandbox"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("command_execution_enabled=True\n", encoding="utf-8")
    (root / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m85_read_only_command_allowlist_static_safety"
    )
    result = FoundationGateEvaluator(root).check_m85_read_only_command_allowlist_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("command_execution_enabled=True" in failure for failure in result.failures)
