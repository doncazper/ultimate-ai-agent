from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m114_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m114_account_connector_contracts" in ids
    assert "m114_account_connector_static_safety" in ids
    assert "m114_account_connector_route_boundary" in ids
    assert "m114_roadmap_currentness" in ids


def test_m114_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m114_account_connector_contracts",
        "m114_account_connector_static_safety",
        "m114_account_connector_route_boundary",
        "m114_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m114_route_boundary_rejects_account_connector_runtime_routes() -> None:
    failures = gate_evaluators.m114_openapi_route_failures(
        {
            "/api/manifest": {},
            "/accounts/connect": {},
            "/accounts/oauth/start": {},
            "/accounts/oauth/callback": {},
            "/connectors/accounts/read": {},
            "/connectors/accounts/write": {},
            "/credentials/read": {},
            "/credentials/write": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/accounts/connect",
        "/accounts/oauth/start",
        "/accounts/oauth/callback",
        "/connectors/accounts/read",
        "/connectors/accounts/write",
        "/credentials/read",
        "/credentials/write",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m114_openapi_route_failures(app.openapi().get("paths", {}))


def test_m114_static_safety_detects_account_connector_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "oauth_flow_enabled=True\n"
        "token_exchange_enabled=True\n"
        "account_connector_runtime_enabled=True\n"
        "account_connector_enabled=True\n"
        "account_action_enabled=True\n"
        "network_access_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m114_account_connector_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m114_account_connector_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("oauth_flow_enabled=True" in failure for failure in result.failures)
    assert any("token_exchange_enabled=True" in failure for failure in result.failures)
    assert any(
        "account_connector_runtime_enabled=True" in failure
        for failure in result.failures
    )
    assert any("account_connector_enabled=True" in failure for failure in result.failures)
    assert any("account_action_enabled=True" in failure for failure in result.failures)
    assert any("network_access_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
