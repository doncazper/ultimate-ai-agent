from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m107_openapi_route_failures,
)


def test_m107_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m107_mobile_approval_renewal_ux_contracts" in ids
    assert "m107_mobile_approval_renewal_ux_static_safety" in ids
    assert "m107_mobile_approval_renewal_ux_route_boundary" in ids
    assert "m107_roadmap_currentness" in ids


def test_m107_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m107_mobile_approval_renewal_ux_contracts",
        "m107_mobile_approval_renewal_ux_static_safety",
        "m107_mobile_approval_renewal_ux_route_boundary",
        "m107_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m107_route_boundary_rejects_approval_renewal_runtime_routes() -> None:
    failures = m107_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/approvals/renew": {},
            "/mobile/approvals/renew/start": {},
            "/mobile/approvals/renew/capture": {},
            "/mobile/approvals/renew/persist": {},
            "/mobile/approvals/renew/prompt": {},
            "/mobile/approvals/renew/execute": {},
            "/mobile/approvals/kill-switch": {},
            "/mobile/revocation/execute": {},
            "/mobile/notifications/push": {},
            "/mobile/background/workers": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/mobile/approvals/renew",
        "/mobile/approvals/renew/start",
        "/mobile/approvals/renew/capture",
        "/mobile/approvals/renew/persist",
        "/mobile/approvals/renew/prompt",
        "/mobile/approvals/renew/execute",
        "/mobile/approvals/kill-switch",
        "/mobile/revocation/execute",
        "/mobile/notifications/push",
        "/mobile/background/workers",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m107_openapi_route_failures(app.openapi().get("paths", {}))


def test_m107_static_safety_detects_approval_renewal_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "approval_capture_enabled=True\n"
        "approval_persistence_enabled=True\n"
        "approval_renewal_execution_enabled=True\n"
        "raw_approval_payload_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m107_mobile_approval_renewal_ux_static_safety"
    )
    result = (
        FoundationGateEvaluator(tmp_path)
        .check_m107_mobile_approval_renewal_ux_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("approval_capture_enabled=True" in failure for failure in result.failures)
    assert any("approval_persistence_enabled=True" in failure for failure in result.failures)
    assert any("approval_renewal_execution_enabled=True" in failure for failure in result.failures)
    assert any("raw_approval_payload_enabled=True" in failure for failure in result.failures)
