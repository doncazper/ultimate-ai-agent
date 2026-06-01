from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import (
    FoundationGateResult,
    FoundationGateStatus,
    build_foundation_gate_report,
    default_m5_shadow_replay_scenario,
)


client = TestClient(app)


def test_gate_report_validate_endpoint_accepts_safe_report():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[
            FoundationGateResult(
                criterion_id="versioning_consistent",
                status=FoundationGateStatus.passed,
                safe_message="version files agree",
                evidence_refs=["VERSION.md"],
            )
        ],
    )

    response = client.post("/gate/reports/validate", json=report.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "validated"


def test_gate_report_validate_endpoint_blocks_secret_like_report():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[
            FoundationGateResult(
                criterion_id="secret_hygiene_clean",
                status=FoundationGateStatus.failed,
                safe_message="unsafe payload",
                failures=["client_secret=rawvalue123456789"],
            )
        ],
    )

    response = client.post("/gate/reports/validate", json=report.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FOUNDATION_GATE_REPORT_SECRET_EXPOSURE"


def test_shadow_replay_validate_endpoint_does_not_execute_replay():
    scenario = default_m5_shadow_replay_scenario()

    response = client.post("/gate/shadow-replay/validate", json=scenario.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {
        "scenario_id": "m5_minimum_lovable_kernel_replay",
        "status": "validated",
        "executes_replay": False,
    }
