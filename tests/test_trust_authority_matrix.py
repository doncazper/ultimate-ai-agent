from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    TRUST_AUTHORITY_MATRIX_CONTRACT_REF,
    TRUST_AUTHORITY_MATRIX_ROUTE_REF,
    TrustAuthorityMatrixReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _assert_no_runtime_authority(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    forbidden = [
        'broad_approval_enabled": true',
        'standing_authority_enabled": true',
        'runtime_context_injection_enabled": true',
        'connector_write_enabled": true',
        'provider_model_call_enabled": true',
        'shell_subprocess_execution_enabled": true',
        'browser_execution_enabled": true',
        'background_autonomy_enabled": true',
        'production_authority_enabled": true',
        'control_center_grants_authority": true',
        'raw_content_included": true',
        "/users/",
        "raw prompt",
        "raw response",
        "provider payload",
        "credential",
        "secret",
    ]
    for fragment in forbidden:
        assert fragment not in text


def test_trust_authority_matrix_explains_available_approval_and_blocked(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    matrix = service.trust_authority_matrix()
    parsed = TrustAuthorityMatrixReadModel(**matrix)

    assert parsed.contract_ref == TRUST_AUTHORITY_MATRIX_CONTRACT_REF
    assert parsed.route_ref == TRUST_AUTHORITY_MATRIX_ROUTE_REF
    assert parsed.backend_owned is True
    assert parsed.safe_refs_only is True
    assert parsed.available_now_lane_refs
    assert parsed.approval_required_lane_refs
    assert parsed.blocked_lane_refs
    assert "trust-lane:local-task-commit" in parsed.approval_required_lane_refs
    assert "trust-lane:external-mutations" in parsed.blocked_lane_refs
    assert "trust-lane:local-draft-proposal" in parsed.available_now_lane_refs
    assert "trust-lane:web-evidence-product-slice" in parsed.available_now_lane_refs
    assert "trust-lane:provider-draft-summarize" in parsed.available_now_lane_refs
    assert "trust-lane:connector-draft-only" in parsed.available_now_lane_refs
    assert any(
        lane.tier == 2 and lane.authority_state == "available_now"
        for lane in parsed.lanes
    )
    assert any(
        lane.tier == 3 and lane.requires_exact_approval for lane in parsed.lanes
    )
    assert all(
        lane.authority_state == "blocked" for lane in parsed.lanes if lane.tier >= 4
    )
    assert all(lane.cli_inspection_refs for lane in parsed.lanes)
    assert all(lane.safe_disable_refs for lane in parsed.lanes)
    assert all(lane.rollback_refs for lane in parsed.lanes)
    assert all(lane.promotion_path_refs for lane in parsed.lanes)
    assert set(parsed.cli_inspection_refs) == {
        ref for lane in parsed.lanes for ref in lane.cli_inspection_refs
    }
    assert set(parsed.safe_disable_refs) == {
        ref for lane in parsed.lanes for ref in lane.safe_disable_refs
    }
    assert set(parsed.rollback_refs) == {
        ref for lane in parsed.lanes for ref in lane.rollback_refs
    }
    assert set(parsed.promotion_path_refs) == {
        ref for lane in parsed.lanes for ref in lane.promotion_path_refs
    }
    assert set(parsed.blocked_authority_refs) == {
        ref for lane in parsed.lanes for ref in lane.blocked_authority_refs
    }
    tier_2 = [lane for lane in parsed.lanes if lane.tier == 2]
    assert tier_2
    assert all(lane.operator_posture == "review_only" for lane in tier_2)
    assert all(not lane.rollback_execution_enabled for lane in parsed.lanes)
    tier_3_plus = [lane for lane in parsed.lanes if lane.tier >= 3]
    assert tier_3_plus
    assert all(lane.requires_safe_disable for lane in tier_3_plus)
    assert all(lane.requires_rollback_posture for lane in tier_3_plus)
    assert all(lane.safe_disable_refs for lane in tier_3_plus)
    assert all(lane.rollback_refs for lane in tier_3_plus)
    assert all(
        not any(ref.endswith(":read-model-only") for ref in lane.safe_disable_refs)
        for lane in tier_3_plus
    )
    assert all(
        not any(ref.endswith(":no-mutation") for ref in lane.rollback_refs)
        for lane in tier_3_plus
    )
    _assert_no_runtime_authority(matrix)


def test_trust_authority_route_is_backend_owned() -> None:
    api_client = TestClient(app)
    response = api_client.get("/control-center/trust-authority/matrix")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    matrix = payload["data"]
    TrustAuthorityMatrixReadModel(**matrix)
    assert matrix["route_ref"] == "GET /control-center/trust-authority/matrix"
    assert "read_only_control_center_projection" in payload["redactions_applied"]
    _assert_no_runtime_authority(payload)


def test_trust_authority_cli_outputs_safe_refs_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-trust-authority",
            "--limit",
            "5",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["command_ref"] == "repo-local-command:founder-loop-trust-authority"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    TrustAuthorityMatrixReadModel(**payload["trust_authority_matrix"])
    _assert_no_runtime_authority(payload)
    assert str(state_dir).lower() not in result.stdout.lower()


@pytest.mark.parametrize("flag", [
    "broad_approval_enabled",
    "standing_authority_enabled",
    "runtime_context_injection_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
])
def test_trust_authority_matrix_rejects_authority_creep(
    tmp_path: Path,
    flag: str,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    matrix[flag] = True

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


def test_trust_authority_matrix_rejects_posture_ref_drift(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    matrix["safe_disable_refs"] = []

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


@pytest.mark.parametrize("field,value", [
    ("operator_posture", "enabled_read_only"),
    ("rollback_execution_enabled", True),
    ("cli_inspection_refs", []),
])
def test_trust_authority_matrix_rejects_lane_posture_drift(
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    tier_2_index = next(
        index for index, lane in enumerate(matrix["lanes"]) if lane["tier"] == 2
    )
    matrix["lanes"][tier_2_index][field] = value

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


def test_trust_authority_route_is_in_openapi() -> None:
    schema = app.openapi()
    route = schema["paths"]["/control-center/trust-authority/matrix"]["get"]

    assert route["operationId"] == "get_control_center_trust_authority_matrix"
